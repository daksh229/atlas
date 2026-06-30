# BF Atlas — Trader Intelligence Platform

BF Atlas is an internal intelligence application for B Futurist's wholesale traders.
It reads the company's ERP data (products, sales, purchases), supplier offers, and
retailer market prices, and surfaces — per brand — where supply, demand, live stock,
and market prices align, so a trader can act on an opportunity *before* it reaches the
ERP. It also evaluates incoming supplier offers ("is this a good deal, and who should
know?").

The application runs on the actual exported B Futurist data, normalized through a
data pipeline into a single SQLite database that the API and UI read.

- **Architecture & how it works:** [ARCHITECTURE.md](ARCHITECTURE.md)
- **Repository layout:** [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)

---

## Stack

| Layer | Technology |
|---|---|
| Frontend | React 18 + TypeScript + Tailwind (Vite) |
| Backend | Python 3.12 + FastAPI |
| Database | SQLite (Odoo-shaped schema; a PostgreSQL drop-in for production) |
| AI | Anthropic Claude (offer email parsing) with a deterministic heuristic fallback |
| FX | European Central Bank reference rates (cached) |

## Repository at a glance

```
bf_atlas/
├── backend/          FastAPI API (core, routers, services)
├── frontend-react/   React + TS + Tailwind UI
├── data/
│   ├── pipeline/     ingest → normalize → build atlas.db / offer evaluation
│   ├── samples/      sample supplier emails (Offers Inbox)
│   └── atlas.db      generated SQLite database (gitignored)
└── trial/            standalone supplier-offer evaluator + written notes
```

Full breakdown in [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md).

---

## Setup

Prerequisites: **Python 3.12+**, **Node 18+**, and the source data package present at
`New folder/` (the Odoo exports, supplier offers, and retailer prices). Internet is
required on the first run to fetch ECB rates (cached afterwards).

```bash
# 1. Python dependencies
pip install pandas openpyxl                                   # pipeline
python -m pip install -r backend/requirements.txt             # backend (use backend/.venv)

# 2. Frontend dependencies
cd frontend-react && npm install && cd ..
```

## Build the data

Run from the **repository root** (the pipeline uses package imports):

```bash
python -m data.pipeline.build_db        # builds data/atlas.db from the source files
python -m data.pipeline.build_offers    # builds the supplier-offer evaluation JSON
```

`build_db` prints per-table row counts; `build_offers` prints a verdict summary per
offer file.

## Run the application

Two terminals:

```bash
# Terminal A — backend (http://localhost:8000, docs at /docs)
cd backend
python -m uvicorn app.main:app --reload --port 8000

# Terminal B — frontend (http://localhost:5173, proxies /api → :8000)
cd frontend-react
npm run dev
```

Open **http://localhost:5173** and select a trader to sign in. Each trader sees only
their own accounts; counterparties on shared opportunities are shown as the
responsible colleague, never by account name (enforced server-side).

### Standalone offer evaluator (optional)

A minimal, self-contained version of the offer evaluator lives in `trial/`:

```bash
python -m data.pipeline.build_offers
cd trial/web && npm install && npm run dev    # http://localhost:5174
```

---

## Data sources & confidentiality

The source data under `New folder/` is confidential and **gitignored** — it is never
committed. The generated database (`data/atlas.db`), the FX cache, and pipeline
reports are also gitignored and rebuilt from the source files.

Data provenance is explicit throughout the UI:

- **Real** — products, partners, sales and purchase history (from the Odoo exports),
  supplier offers, and retailer prices.
- **Derived** — demand signals (inferred from sales history).
- **Synthetic** — live stock and team assignment (not present in the exports).

## Notes

- Run the `python -m data.pipeline.*` commands from the repository root.
- `build_db` overwrites `data/atlas.db`; run it before starting the backend.
- If the Offer Evaluation screen reports "not built", run `build_offers` first.
