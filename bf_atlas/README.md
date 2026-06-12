# BF Atlas — AI Data Intelligence Platform (POC)

A showcase POC for **BF Atlas**, B Futurist's internal trader intelligence
platform, on BF's actual required stack: **React 18 + TypeScript + Tailwind**
frontend, **FastAPI** backend, **LangGraph multi-agent** NL layer, with
**JWT + region-based RBAC** (row-level-security story).

> ⚠️ **Directional showcase on mock data.** Built from the public brief, not BF's
> ~30-page spec / ~50-page engineering brief. Mirrors the Phase-1 stack
> (FastAPI + React/TS/Tailwind + AWS EU); this POC uses **SQLite** in place of
> PostgreSQL to demo fast. Alert rules, brand-page layout, and scraping targets
> would conform to BF's spec under NDA.

---

## Architecture

```
┌──────────────────────────────┐    HTTP/JSON + JWT    ┌──────────────────────────────┐
│  React 18 + TS + Tailwind     │  ──────────────────▶  │  FastAPI backend             │
│  • Onboarding (role → region) │   Authorization:      │  • Auth / RBAC (JWT)         │
│  • Region-dynamic dashboard   │   Bearer <token>      │  • REST routers              │
│  • Ask Atlas (agent trace)    │  ◀──────────────────  │  • Services (SQLite)         │
│  • Alerts · Brands · …        │                       │  • LangGraph multi-agent     │
└──────────────────────────────┘                       └──────────────────────────────┘
        (Recharts, axios)                          region isolation enforced server-side
```

All data/AI logic lives in the **backend**; the React frontend
(`frontend-react/`) only renders.

## Region-based RBAC (the isolation story)

Onboarding picks **role → region** and calls `POST /auth/session`, which issues a
**JWT** encoding the user's role + allotted region. Every request carries it, and
the backend derives the *effective* region from the token and **enforces**:

- **Trader** → locked to their allotted region. Any cross-region request → **403**.
- **Manager** → cross-region ("All regions") view, may switch to any single region.

Isolation is enforced **server-side** (`core/security.py`), not in the UI — the
brief's Postgres row-level-security requirement, demonstrated. Auth is
password-less for the POC; production adds Google OAuth.

### The multi-agent system (LangGraph)

`POST /chat` runs a typed graph and returns the full **agent trace** so the UI can
show the routing live:

```
Router ─┬─ data_query  → SQL Generator ─(has SQL?)─→ Retrieval → Insight → END
        │                              └─(no SQL)──────────────────────→ END
        ├─ opportunity → Opportunity Engine ───────────────→ Insight → END
        ├─ brand_intel → Brand-Intel ──────────────────────→ Insight → END
        ├─ knowledge   → RAG agent (embed → retrieve → cite) ──────→ END
        ├─ clarify     → Clarifier ────────────────────────────────→ END
        └─ out_of_scope→ Fallback ─────────────────────────────────→ END
```

| Agent | Role |
|---|---|
| **Router** | Detects intent, selects the route (Claude, with a keyword fallback) |
| **SQL Generator** | NL → a single read-only SQLite SELECT |
| **Retrieval** | Validates with the SQL guard, executes read-only, returns rows |
| **Opportunity** | Cross-match engine for "what can I sell / best matches" |
| **Brand-Intel** | Brand-level "can I buy/sell brand X" |
| **Knowledge (RAG)** | Semantic search over notes/emails/briefs → cited answer |
| **Clarifier** | Asks a follow-up when the question is ambiguous |
| **Insight** | Turns rows/structured data into a business narrative |
| **Fallback** | Handles out-of-scope questions gracefully |

### Hybrid retrieval: SQL for structured, RAG for unstructured

Numbers/aggregations go through **Text-to-SQL** (precise); qualitative questions
("why did a client push back?", "any supplier emails about delays?") go through a
**RAG** path over an unstructured corpus (`data/corpus.json` — deal notes, supplier
emails, brand briefs). Embeddings are **local** (`sentence-transformers`, with a
TF-IDF fallback so it runs offline with no key); production swaps in **pgvector** +
Voyage AI behind the same interface. **RAG retrieval is region-scoped by the same
RBAC** — a trader only ever retrieves their region's notes.

Each agent appends to a shared `trace` (LangGraph add-reducer) → the **Ask Atlas**
page renders `Router → … → Insight` plus a step-by-step breakdown.

---

## Layout

```
bf_atlas/
├── backend/
│   ├── app/
│   │   ├── main.py                # FastAPI app + routers + /health
│   │   ├── core/                  # config, database, llm, sql_guard, serialize
│   │   ├── services/              # dashboard, atlas, pricelist, radar, sync
│   │   ├── agents/                # router, sql_generator, retrieval, opportunity,
│   │   │                          #   brand_intel, clarifier, insight, fallback, graph
│   │   ├── schemas/               # Pydantic chat models
│   │   └── routers/               # /chat /dashboard /opportunities /brands /pricelist /radar /sync
│   ├── requirements.txt
│   └── .env(.example)
├── frontend-react/                # React 18 + TS + Tailwind (Vite)
│   └── src/
│       ├── auth/                  # AuthContext + JWT/session types
│       ├── api/                   # axios client + typed endpoints
│       ├── components/            # Layout, KpiCard, region switcher, common
│       └── pages/                 # Onboarding, Dashboard, AskAtlas, Alerts,
│                                  #   Brands, PriceList, Radar, Sync
├── data/
│   ├── seed_generate.py           # richer region-balanced seed → trading_data.json
│   ├── generate_corpus.py         # unstructured RAG corpus → corpus.json
│   ├── init_db.py / init_atlas.py / init_all.py
│   ├── samples/                   # messy price list + retailer fixture
│   ├── corpus.json / bfuturist.db # generated
├── run_backend.ps1 / run_frontend_react.ps1
└── README.md
```

---

## Setup & run

```powershell
# 0. (once) build the database + RAG corpus from the seeds
cd bf_atlas/data
python seed_generate.py            # generate trading_data.json (45 traders, 1240 orders, …)
python init_all.py                 # base tables + Atlas cross-match + RAG corpus

# 1. backend  (terminal A)
cd ../backend
pip install -r requirements.txt
copy .env.example .env             # optional: set ANTHROPIC_API_KEY
uvicorn app.main:app --reload --port 8000
#   → API docs at http://localhost:8000/docs

# 2. React frontend (terminal B)  ← primary UI
cd ../frontend-react
npm install
npm run dev                        # Vite dev server proxies /api → :8000
#   → http://localhost:5173
```

Or use the helpers: `./run_backend.ps1` and `./run_frontend_react.ps1`.
If the backend runs on another port: `./run_frontend_react.ps1 -ApiTarget http://localhost:8010`.

### Try the RBAC

- Onboard as **Manager** → switch regions in the top bar (incl. 🌍 All regions); every
  KPI, chart, alert, and brand figure re-scopes.
- Onboard as **Trader / EU-West** → region is **locked**; the API returns **403** for any
  other region (verify in the Network tab).

> **No Claude API key?** Everything still runs. The Router/SQL/Insight agents and
> price-list matcher fall back to deterministic logic; the Opportunity, Brand,
> Dashboard, Radar, Sync, and **RAG retrieval** features are fully functional
> offline. With a key, the NL chat, AI fuzzy-matching, and RAG synthesis light up.
>
> **RAG embeddings** default to a TF-IDF fallback (zero extra install). For local
> *dense* embeddings: `pip install sentence-transformers` then set
> `RAG_EMBEDDER=st` — it downloads a small MiniLM model and runs offline.

---

## Suggested demo flow

1. **Ask Atlas** — type *"What are my best cross-match opportunities?"* → watch the
   agent flow **Router → Opportunity Engine → Insight**. Then *"Can I sell Maison
   Luxe?"* (brand route), *"Why did a client push back on pricing?"* (**Knowledge/RAG**
   → cited sources), *"show me"* (clarifier), *"tell me a joke"* (fallback).
2. **Opportunity Alerts** — 6 alert types + top cross-matches by margin.
3. **Brand Intelligence** — Sell / Buy / closed-loop brand detail.
4. **Price-List Analysis** — messy supplier CSV → AI fuzzy match; the planted
   unknown brand is flagged, not force-matched.
5. **Retailer Radar** — real parser rows vs labelled mock retailers; price gaps.
6. **/docs** — show the OpenAPI surface (the FastAPI layer BF requires).

---

## Honesty / safety notes

- **Retailer Radar** never fakes live scraping: `services/radar.scrape_fixture()`
  is a real BeautifulSoup parser over a local fixture; other retailers are
  labelled `(mock)`.
- **Text-to-SQL**: the Retrieval agent runs only validated read-only SELECT/WITH
  (`core/sql_guard`) on a `mode=ro` connection.
- **Fuzzy matching** flags low-confidence / unknown items instead of forcing a
  match.
- All data is synthetic; the supply/demand cross-match layer is invented from the
  public brief to make the engine demonstrable.

## Phase-1 boundary (not in this POC)
Real Odoo JSON-RPC + NetHunt webhooks (two-way, `last_modified_at` conflicts);
Google OAuth + JWT + Postgres row-level security; production scrapers (robots/ToS,
rate-limiting, scheduling); server-side anonymization; AWS eu-central-1.
