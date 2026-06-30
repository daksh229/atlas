# BF Atlas — Project Structure

A directory-by-directory guide to the repository. For how the pieces work together see
[ARCHITECTURE.md](ARCHITECTURE.md); for setup and run steps see [README.md](README.md).

```
bf_atlas/
├── backend/                     FastAPI backend (the API + engine)
├── frontend-react/              React + TypeScript + Tailwind UI
├── data/                        data pipeline, generated DB, sample emails
├── trial/                       standalone offer evaluator + written notes
├── New folder/                  confidential source data (gitignored)
└── *.md                         documentation
```

---

## backend/

```
backend/
├── app/
│   ├── main.py                  FastAPI app; mounts the routers, CORS
│   ├── core/
│   │   ├── config.py            settings (DB path, secrets, data dir)
│   │   ├── database.py          SQLite helpers (queries → pandas DataFrames)
│   │   ├── security.py          session (JWT) + access control: owns(), mask_partner()
│   │   └── serialize.py         JSON-safe conversion of DataFrames
│   ├── routers/                 thin HTTP layer, one module per nav area
│   │   ├── auth.py              trader onboarding + session token
│   │   ├── alerts.py            GET /alerts — the opportunity feed
│   │   ├── brands.py            brand maps + brand detail
│   │   ├── relationships.py     my clients / my suppliers
│   │   ├── offers.py            offers inbox, parse, evaluation
│   │   ├── radar.py             retailer radar
│   │   ├── catalog.py           brand catalog + PDF
│   │   └── dashboard.py         overview KPIs + chart data
│   ├── services/                business logic (read the DB, return records)
│   │   ├── matching.py          signal-overlap detection per brand
│   │   ├── alerts.py            matches → routed, bundled, diversified, capped alerts
│   │   ├── brands.py            brand resolution + brand intelligence (masked)
│   │   ├── email_parser.py      offer-email extraction (AI + heuristic fallback)
│   │   ├── offers.py            offers inbox + supplier-offer evaluation
│   │   ├── radar.py             retailer prices vs our supply
│   │   ├── catalog.py           catalog rows + PDF generation
│   │   ├── dashboard.py         per-trader KPIs and top brands
│   │   └── relationships.py     per-trader clients/suppliers with metrics
│   └── schemas/                 shared response models
├── requirements.txt
└── .env.example                 copy to .env (AUTH_SECRET, ANTHROPIC_API_KEY, …)
```

Routers depend on services; services depend on `core`. Access control is applied in the
service layer so it holds uniformly across every endpoint.

---

## frontend-react/

```
frontend-react/
├── index.html
├── vite.config.ts               dev server + /api proxy to the backend
├── tailwind.config.js
└── src/
    ├── main.tsx                 app entry
    ├── App.tsx                  routes (auth-gated) + layout
    ├── index.css                Tailwind layers
    ├── api/
    │   ├── client.ts            axios instance + JWT header
    │   └── endpoints.ts         typed API calls (one per backend endpoint)
    ├── auth/
    │   ├── AuthContext.tsx       session state (localStorage) + login/logout
    │   └── types.ts
    ├── components/
    │   ├── Layout.tsx           sidebar navigation + header
    │   ├── KpiCard.tsx          metric card
    │   └── common.tsx           Loading, ErrorMsg, PageHeader, Pill, formatters
    ├── hooks/
    │   └── useApi.ts            async data-fetch hook (loading/error/refetch)
    └── pages/
        ├── Onboarding.tsx        pick a trader → sign in
        ├── OpportunityAlerts.tsx the alert feed (landing)
        ├── Overview.tsx          KPIs + provenance badges + chart
        ├── BrandMaps.tsx         Brands I Can Sell / Buy
        ├── BrandDetail.tsx       full brand intelligence (masked)
        ├── MyClients.tsx
        ├── MySuppliers.tsx
        ├── OffersInbox.tsx       email parse → review → match
        ├── OfferEvaluation.tsx   the 3 supplier offers, judged
        ├── RetailerRadar.tsx     market windows
        └── BrandCatalog.tsx      shareable brand list + PDF export
```

---

## data/

```
data/
├── pipeline/                    source files → atlas.db / offer evaluation
│   ├── config.py                single config surface (paths, margin bands, FX)
│   ├── schema.py                canonical SQLite schema + per-table columns
│   ├── build_db.py              entry point: build atlas.db from the source data
│   ├── build_offers.py          entry point: build the offer-evaluation JSON
│   ├── normalize/               shared, deterministic data layer
│   │   ├── clean.py             EAN / price / quantity / brand-string helpers
│   │   ├── currency.py          ECB rates → EUR (date-aware, cached, fallback)
│   │   └── brands.py            brand dictionary (canonical + curated aliases)
│   ├── sources/                 one ingester per source file
│   │   ├── products.py          product master → products + seeds brand dictionary
│   │   ├── orders.py            flattened histories → orders + partners (ffill)
│   │   ├── history.py          per-EAN price/trader aggregates
│   │   ├── retailer.py          retailer price scan
│   │   └── offers.py            three supplier-offer formats → one schema
│   ├── synth/
│   │   └── derive.py            demand/supply signals + synthetic stock + teams
│   └── analysis/
│       └── evaluate.py          offer-line verdict (good / borderline / skip / unknown)
├── samples/
│   └── emails/                  sample supplier emails read by the Offers Inbox
└── atlas.db                     generated SQLite database (gitignored)
```

Generated artifacts (`atlas.db`, the FX cache, pipeline reports) are gitignored and
rebuilt from the source files by the two `build_*` entry points.

---

## trial/

A self-contained version of the supplier-offer evaluator, plus the written notes.

```
trial/
├── README.md                    how to run the standalone evaluator
├── NOTE.md                      design choices and reasoning
├── BRIDGES.md                   platform architecture / change-management notes
└── web/                         minimal Vite + React page reading the offer JSON
```

The shared analysis it uses lives in `data/pipeline/` (the same modules the main app
uses), so the two builds stay consistent.

---

## Documentation (root)

| File | Purpose |
|---|---|
| `README.md` | overview, stack, setup and run |
| `ARCHITECTURE.md` | how the system works end to end |
| `PROJECT_STRUCTURE.md` | this file — the repository layout |

---

## Generated / ignored paths

Not committed (see `.gitignore`): `New folder/` (confidential source data),
`data/atlas.db`, `data/pipeline/.cache/`, `data/pipeline/reports/`, `backend/.env`,
`**/node_modules`, build output, and the dev-only screenshot tooling.
