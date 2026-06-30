# BF Atlas — Architecture

This document explains what the system does and how the pieces fit together. For the
directory-by-directory layout see [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md); for
setup and run steps see [README.md](README.md).

---

## 1. What the system does

B Futurist is a wholesale distributor of branded beauty products: it buys and resells,
linking a purchase (a buy) to a sale (a sell). The valuable knowledge — who wants a
brand, who can source it, at what price, and what the market charges — is scattered
across traders, emails, and spreadsheets.

BF Atlas brings that knowledge together. For each brand it asks *which signals fired
recently?* — a client wants it (demand), we can source it (supply), we hold live stock,
a retailer prices it where we can compete. When signals align within a recency window,
that is an opportunity, routed to the right trader. Separately, it evaluates incoming
supplier offers against the company's own history and the market.

The application is a navigable web product (menus, tables, detail views), not a chat
interface. AI runs underneath (offer email parsing); traders interact with structured
screens.

---

## 2. High-level shape

```
   Source data (Odoo exports, offers, retailer prices)
                      │
                      ▼
        ┌─────────────────────────────┐
        │  Data pipeline (Python)      │   ingest → normalize → derive → load
        │  data/pipeline/              │
        └──────────────┬──────────────┘
                       ▼
                 data/atlas.db   (SQLite, Odoo-shaped)
                       │
                      ▼
        ┌─────────────────────────────┐
        │  Backend API (FastAPI)       │   matching engine, alert engine,
        │  backend/app/                │   access control, brand intelligence
        └──────────────┬──────────────┘
                       │ HTTP / JSON (+ JWT)
                      ▼
        ┌─────────────────────────────┐
        │  Frontend (React + TS)       │   navigable screens, per-trader views
        │  frontend-react/             │
        └─────────────────────────────┘
```

The data pipeline and the API are decoupled by the database: the pipeline produces
`atlas.db`; the API only reads it.

---

## 3. The data pipeline (`data/pipeline/`)

Transforms the source files into `atlas.db`. Four stages:

1. **Ingest** (`sources/`) — read each source file into internal records:
   - `products.py` — the product master (one row per EAN: brand, category, average/min
     purchase price, average/max sale price, all in EUR). Seeds the brand dictionary.
   - `orders.py` — reconstruct sale/purchase orders and partners from the flattened
     order-history exports (see "flattened export" below).
   - `history.py` — per-EAN price and trader/account aggregates from the histories.
   - `retailer.py` — retailer price scan rows.
   - `offers.py` — three supplier-offer formats, normalized to one schema.

2. **Normalize** (`normalize/`) — the shared, deterministic data layer:
   - `clean.py` — pure helpers for messy values (EAN cleaning, price/quantity parsing,
     brand-string normalization).
   - `currency.py` — convert every amount to EUR using ECB reference rates, date-aware,
     cached, with an offline fallback.
   - `brands.py` — the brand dictionary: resolve any brand spelling to one canonical
     `brand_id` (see §6).

3. **Derive / synthesize** (`synth/derive.py`) — produce the signals the matching
   engine needs: demand derived from sales history, supply from purchase history and
   offers, plus synthesized live stock and team assignment (the exports omit these).

4. **Load** (`build_db.py` + `schema.py`) — create the schema and bulk-load every table
   into `atlas.db`.

`build_offers.py` is a separate entry point that runs the offer evaluator end-to-end and
writes a JSON the UI reads.

### The "flattened export" detail

The order-history exports carry the order header (salesperson/customer/date, or
buyer/vendor/date) only on the *first* line of each order; continuation lines are blank.
`orders.py` forward-fills these before aggregating — without it, the great majority of
trader/account attribution would be lost.

---

## 4. The backend (`backend/app/`)

A FastAPI application. Routers are thin and delegate to services; services hold the
logic and read the database.

- **`core/`** — `config` (settings), `database` (SQLite query helpers returning
  DataFrames), `security` (session + access control), `serialize` (JSON-safe output).
- **`routers/`** — one per navigation area: `auth`, `alerts`, `brands`, `relationships`,
  `offers`, `radar`, `catalog`, `dashboard`.
- **`services/`** — the engine:
  - `matching.py` — for each signal type, find recent overlaps on the same `brand_id`
    within a window anchored to the latest data date.
  - `alerts.py` — turn matches into typed, routed, de-duplicated, brand-bundled,
    type-diversified, capped alerts.
  - `brands.py` — brand resolution + brand intelligence (access-masked).
  - `offers.py` / `email_parser.py` — the Offers Inbox and supplier-offer evaluation.
  - `radar.py`, `catalog.py`, `dashboard.py`, `relationships.py` — the remaining screens.

### The matching engine and alert types

Phase 1 core alerts:

| Alert | Fires when |
|---|---|
| Demand–Supply Match | a client wants a brand and a (colleague's) supply exists |
| External Market Window | a retailer lists a brand above a price we can supply at |
| Stock Match | we hold live stock of a brand a client wants |
| Reorder Reminder | a client is overdue for a repeat order (from real order cadence) |

Two further alerts build on the offers capability: Offer-to-Request Match and Triple
Match (demand + supply + retail aligned).

---

## 5. The frontend (`frontend-react/`)

React + TypeScript + Tailwind (Vite). A typed API client (`src/api/`) calls the backend;
an auth context holds the selected trader's session (JWT). Pages map to the navigation
sections: Opportunity Alerts, Overview, Brand Maps (Sell/Buy), Brand Detail, My Clients,
My Suppliers, Offers Inbox, Offer Evaluation, Retailer Radar, Brand Catalog.

---

## 6. Cross-cutting rules

These hold across the whole system and are where most of the engineering care goes.

**Access control.** Each trader sees only their own clients and suppliers. Other
traders' accounts never appear by name — only as aggregate signals plus the responsible
colleague. Enforced server-side in the service layer (`core/security.py`), not hidden in
the UI.

**Alert quality.** The feed is de-duplicated, bundled by brand, diversified across alert
types, ranked, and capped per trader, so it stays a short action list rather than noise.

**Right-person routing.** Every alert targets a specific trader — the account owner,
stock owner, or matching-client owner.

**Brand dictionary.** "YSL", "Saint Laurent", and "Yves Saint Laurent" are one brand.
Resolution is **deterministic**: a fixed normalization pipeline (accents, punctuation,
initialisms, noise suffixes) plus a small curated alias table, built from the product
master. No model is involved in matching, so it is reproducible and auditable; unknown
brands are flagged, never force-matched. (AI is used only to *read* free-text offer
emails, not to *decide* brand matches.)

---

## 7. Data provenance

The system is explicit about where each piece of data comes from, and the UI labels it:

- **Real** — products, partners, sale/purchase orders (from the Odoo exports), supplier
  offers, retailer prices.
- **Derived** — demand signals, inferred from sales history.
- **Synthetic** — live stock and team assignment (not present in the exports).

---

## 8. Key design decisions

- **EAN as the join key.** Product names are inconsistent; the barcode is the reliable
  link across offers, the product master, history, and retailer prices. Brand-name
  matching is a fallback only.
- **Currency normalized to EUR at the row's own date** using ECB rates, with original
  amount and currency retained.
- **Database as the contract** between pipeline and API: the API is unaware of how the
  data was produced, so the source can evolve (e.g. a live Odoo feed) without touching
  the API.
- **Deterministic core, AI at the edge.** Matching and canonicalization are
  rule-based; the LLM is confined to parsing unstructured email text.
