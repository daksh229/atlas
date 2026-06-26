# BF Atlas — Trader Intelligence Platform (POC)

A spec-aligned POC of **BF Atlas**, B Futurist's internal trader-intelligence
platform, on BF's required stack: **React 18 + TypeScript + Tailwind** frontend,
**FastAPI** backend, **SQLite** (POC stand-in for PostgreSQL 16).

This POC implements the load-bearing requirements of the BF Atlas spec:

| Spec § | Requirement | Where |
|---|---|---|
| §4 | **A web application, not a chatbot** — navigable screens, no chat | the whole UI; the agent/chat layer was removed |
| §5 | Data sources, brand-dictionary canonicalisation | `data/pipeline/` (Odoo-shaped, preprocessing pipeline) |
| §6 | **Matching engine** — per-brand signal convergence | `services/matching.py` |
| §7 | The **4 core alerts** + Offer-to-Request + Triple Match | `services/alerts.py` |
| §7 | Brand Intelligence view + shareable **Brand Catalog (PDF)** | `services/brands.py`, `services/catalog.py` |
| §8 | **Navigation** in the spec's menu sections | `components/Layout.tsx` |
| §9 | **Trader-based access control** + counterparty masking | `core/security.py` |
| §9 | **Alert quality control** (dedup, bundle-by-brand, daily cap, priority) | `services/alerts.py` |
| §9 | **Right-person routing** | every alert carries a `target_trader_id` |
| §9 | **Brand dictionary** (canonical + aliases) | `data/pipeline/brands.py`, `brand_aliases` table |

> POC scope: **5 traders / 2 teams / 50 brands** on planted mock data, SQLite not
> Postgres, no AWS, no real Odoo. The data is **Odoo-shaped** so a future read-only
> Odoo integration is a near drop-in.

---

## Architecture

```
React 18 + TS + Tailwind  ──HTTP/JSON + JWT──▶  FastAPI
  • Opportunity Alerts (landing)                • Auth (trader identity, JWT)
  • Brand Maps (Sell / Buy)                     • Matching engine (brand_id joins)
  • My Clients / My Suppliers                   • Alert engine (route + dedup + cap)
  • Offers Inbox · Retailer Radar               • Access control (trader-owned + mask)
  • Brand Catalog (+ PDF)                       • SQLite (atlas.db)
```

Access control is enforced **server-side** in `core/security.py`: each trader sees
only their own clients/suppliers; other traders' accounts appear only as aggregate
signals + the responsible colleague ("via …"), never by name.

### The matching engine

For each brand it asks *which signals fired recently* (demand, supply, live stock,
retail price) and detects overlap inside a recency window. Overlaps become typed,
routed, quality-controlled alerts:

- **Demand–Supply Match** — a client wants a brand a colleague can supply (notifies both)
- **External Market Window** — a retailer lists a brand above a price we can supply at
- **Stock Match** — we hold live inventory a client wants
- **Reorder Reminder** — a client is overdue for a repeat order (cadence-inferred)
- **Offer-to-Request** — a manual offer matches an existing client request (Offers Inbox)
- **Triple Match** — demand + supply + retail align (highest priority)

Everything joins on **brand_id**, never a raw string, so the brand dictionary
guarantees "YSL" and "Saint Laurent" land on one brand.

---

## Layout

```
bf_atlas/
├── backend/app/
│   ├── main.py                  # FastAPI app (routers = spec nav sections)
│   ├── core/                    # config, database, security (trader RBAC + masking), serialize
│   ├── services/                # matching, alerts, brands, relationships, offers, radar, catalog, dashboard
│   └── routers/                 # auth, alerts, brands, relationships, offers, radar, catalog, dashboard
├── frontend-react/src/
│   ├── auth/                    # trader-identity session
│   ├── api/                     # axios client + typed endpoints
│   └── pages/                   # OpportunityAlerts, BrandMaps, BrandDetail, MyClients,
│                                #   MySuppliers, OffersInbox, RetailerRadar, BrandCatalog, Overview
└── data/
    ├── pipeline/                # raw seed → preprocess (brand canonicalisation) → load atlas.db
    │   ├── brands.py            # THE brand dictionary (50 brands + aliases)
    │   ├── generate_raw.py      # messy raw seed + 5 planted alert scenarios
    │   ├── preprocess.py        # alias resolution + normalisation
    │   ├── load_db.py           # schema + load
    │   └── build.py             # orchestrate + verify all alerts fire
    └── atlas.db                 # generated SQLite DB
```

---

## Setup & run

```powershell
# 0. (once) build the database from the pipeline
cd bf_atlas/data/pipeline
python build.py                 # raw → preprocess → atlas.db, then verifies all alert types fire

# 1. backend (terminal A)
cd ../../backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000      # docs at http://localhost:8000/docs

# 2. frontend (terminal B)
cd ../frontend-react
npm install
npm run dev                     # http://localhost:5173  (proxies /api → :8000)
```

Or use the helpers: `./run_backend.ps1` and `./run_frontend_react.ps1`.

### Try the access control
- Onboard as **Sophie Laurent** (Team Aurora) vs **David Chen** (Team Zenith): each
  sees a different alert feed, different clients/suppliers, and counterparties on
  shared matches show as **"(via <colleague>)"** — never by name.

### Suggested demo flow
1. **Opportunity Alerts** — routed, ranked, bundled-by-brand, capped (note "suppressed" count).
2. **Brand Maps → click a brand** — full Brand Intelligence with masked vs. owned rows.
3. **Offers Inbox** — submit *Chanel @ 30 × 200* → an Offer-to-Request Match fires.
4. **Retailer Radar** — market windows + the flagged unknown brand (not force-matched).
5. **Brand Catalog → Export PDF** — anonymised, no internal data.

---

## Honesty / safety notes
- The brand dictionary resolves 41 aliases; one retailer row is a genuinely unknown
  brand that is **flagged, never force-matched**.
- All access control is enforced server-side, not hidden in the UI.
- All data is synthetic and deliberately planted so every alert type demonstrably fires.

## Out of scope for this POC (real Phase 1)
Real read-only Odoo (JSON-RPC) + NetHunt; Google OAuth; PostgreSQL row-level
security; production scrapers (robots/ToS, scheduling); AWS eu-central-1; the
email/offers parsing infrastructure (the Offers Inbox here is a structural stand-in).
