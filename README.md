# BF Atlas — AI Data Intelligence Platform (POC)

An internal **trader intelligence platform** for a perfume/cosmetics trading
business, built as a proof of concept on the target production stack:
**React 18 + TypeScript + Tailwind** · **FastAPI** · **LangGraph multi-agent AI** ·
**JWT + region-based RBAC**.

> ⚠️ **Directional POC on synthetic data.** Built from a public brief, not a
> production spec. Uses **SQLite** in place of PostgreSQL to demo fast; all data
> is mock and generated locally.

The full application lives in **[`bf_atlas/`](bf_atlas/)** — see
**[bf_atlas/README.md](bf_atlas/README.md)** for architecture, the agent graph,
and detailed setup.

---

## What it does

| Capability | Summary |
|---|---|
| **Unified dashboard** | KPIs + interactive charts over combined ERP + CRM data, region-scoped |
| **Ask Atlas** | Natural-language interface backed by a **LangGraph multi-agent** system |
| **Opportunity Alerts** | Cross-match engine (supplier offers ↔ client demand), 6 alert types |
| **Brand Intelligence** | "Brands I can sell / buy" + closed-loop brand detail |
| **Price-List Analysis** | Messy supplier list → AI fuzzy-match to catalogue |
| **Retailer Radar** | Competitor price scan (real parser + honest mock feed) |
| **RAG** | Semantic search over notes/emails/briefs with cited sources |
| **RBAC** | JWT sessions; traders are locked to one region (server-enforced), managers see all |

### The multi-agent brain (LangGraph)

```
Router ─┬─ data_query  → SQL Generator → Retrieval → Insight
        ├─ opportunity → Opportunity Engine → Insight
        ├─ brand_intel → Brand-Intel → Insight
        ├─ knowledge   → RAG agent (embed → retrieve → cite)
        ├─ clarify     → Clarifier
        └─ out_of_scope→ Fallback
```

Structured questions go through **Text-to-SQL** (precise); qualitative ones go
through **RAG**. Region isolation is enforced server-side on every path.

---

## Quickstart

**Prerequisites:** Python 3.11+, Node 18+.

```bash
# 1. Build the database + RAG corpus (one-time)
cd bf_atlas/data
python seed_generate.py        # → trading_data.json
python init_all.py             # → SQLite DB + cross-match layer + RAG corpus

# 2. Backend (terminal A)
cd ../backend
python -m venv .venv && .venv/Scripts/activate    # Windows
pip install -r requirements.txt
cp .env.example .env           # optional: add ANTHROPIC_API_KEY
uvicorn app.main:app --reload --port 8000

# 3. Frontend (terminal B)
cd ../frontend-react
npm install
npm run dev                    # → http://localhost:5173
```

> Runs **fully offline without an API key** (deterministic fallbacks for the AI
> agents). With a Claude key, NL chat, AI matching, and RAG synthesis light up.

---

## Repository layout

```
.
├── bf_atlas/                  # the application
│   ├── backend/               # FastAPI + LangGraph agents + services
│   ├── frontend-react/        # React 18 + TS + Tailwind (Vite)
│   ├── data/                  # generators + samples
│   └── README.md              # full docs
├── implementation.md          # original technical design notes
├── sample_trading_data.py     # original seed generator (legacy)
└── README.md                  # you are here
```

## Tech stack

Python 3.12 · FastAPI · LangGraph · SQLite · PyJWT · scikit-learn ·
React 18 · TypeScript · Tailwind · Vite · Recharts · axios · Claude (Sonnet 4.6)

---

*Built with Claude Code. Synthetic data only — no real customer information.*
