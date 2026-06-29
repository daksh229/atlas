# BF Atlas — Spec Coverage Map

How our current work maps to the BF Atlas specification. Two complementary builds:

- **Demo POC** — the navigable FastAPI + React app (the walkthrough video). Proves
  *breadth*: every screen, all six alert types, masking, brand intelligence — on
  **synthetic/mock data**.
- **Real-data build** (branch `Phase1`, `data/pipeline/` + `trial/`) — the paid-trial
  offer-evaluator. Proves *depth*: the messy-data engineering (real 482-brand
  dictionary, EAN matching, ECB multi-currency, 3 offer formats) on the **real client
  files** — on the offer-judgment slice only.

**Legend:** ✅ Done · 🟡 Partial / prototype · ⛔ Not started · ➖ Out of Phase-1 scope (per spec phasing)

---

## §4 — A web application, not a chatbot

| Requirement | Demo POC | Real-data build | Notes |
|---|:--:|:--:|---|
| Navigable app, left-side menu, structured screens (no chat) | ✅ | 🟡 | POC has the full nav; real-data build is a single offer screen by design (trial = "keep it small") |
| Clickable detail views | ✅ | 🟡 | POC: brand detail modal. Real-data: click-a-row reasoning |

## §5 — Data sources

| Source | Phase | Demo POC | Real-data build | Notes |
|---|:--:|:--:|:--:|---|
| **Odoo ERP** (read-only) | 1 | 🟡 | 🟡 | POC uses **Odoo-shaped mock** tables; real-data build ingests the **real Odoo exports** (Products/Sales/Purchase) — but neither is a *live* JSON-RPC Odoo connection yet |
| Retailer websites (scraping) | 1/3 | 🟡 | 🟡 | POC: radar on mock rows. Real-data: ingests the **provided** retailer file. **No live scraper built** (infra deferred per spec) |
| Email offers (parsing) | 2 | 🟡 | ✅ | POC: AI offer-inbox prototype. Real-data: parses **3 real messy offer formats** incl. currency/qty/EAN cleaning |
| NetHunt CRM | TBD | ⛔ | ⛔ | "To be defined", not live — correctly untouched |

## §6 — Matching engine

| Requirement | Demo POC | Real-data build | Notes |
|---|:--:|:--:|---|
| Per-brand signal convergence (demand/supply/stock/retail) | ✅ | 🟡 | POC: full engine on mock data. Real-data: offer-vs-history judgment (the demand/supply economics), not yet the full multi-signal engine |
| Joins on a canonical **brand_id**, never a raw string | ✅ | ✅ | Both. Real-data resolves 482 brands from `Products_Info` |
| Margin / "is this a good deal" logic | ✅ | ✅ | Real-data: transparent cost-vs-buy + resale-headroom verdict on real EUR figures |
| Nightly schedule + live-event reaction | 🟡 | ⛔ | POC computes on request; no scheduler yet |

## §7 — Alerts & supporting outputs

| Output | Phase | Demo POC | Real-data build | Notes |
|---|:--:|:--:|:--:|---|
| Demand–Supply Match (central) | 1 | ✅ | 🟡 | Real-data surfaces the same economics per offer line + routing |
| External Market Window | 1 | ✅ | 🟡 | Real-data computes market headroom from the retailer file |
| Stock Match | 1 | ✅ | ⛔ | Needs live stock (Odoo Lot/Serial) — mock only |
| Reorder Reminder | 1 | ✅ | ⛔ | Needs order-date cadence on real data (history is ingested; alert not built) |
| Offer-to-Request Match | 2 | ✅ | 🟡 | The trial evaluator is essentially this, on real offers |
| Triple Match | 2 | ✅ | ⛔ | Phase 2 |
| Brand intelligence view (access-masked) | 1 | ✅ | 🟡 | POC: full modal. Real-data: per-EAN routing + brand-level context |
| Brand Catalog + shareable **PDF** | 1 | ✅ | ⛔ | POC: reportlab PDF export, no internal data |

## §8 — Navigation (5 menu sections)

| Section | Demo POC | Real-data build |
|---|:--:|:--:|
| My View (Opportunity Alerts) | ✅ | ⛔ |
| Brand Maps (Sell / Buy) | ✅ | ⛔ |
| My Relationships (Clients / Suppliers) | ✅ | ⛔ |
| Market Activity (Offers Inbox / Retailer Radar) | ✅ | 🟡 |
| System (Brand Catalog) | ✅ | ⛔ |

## §9 — Cross-cutting rules (the make-or-break four)

| Rule | Demo POC | Real-data build | Notes |
|---|:--:|:--:|---|
| **Access control — server-side masking** | ✅ | ✅ | POC: `mask_partner()`/`owns()` enforce in service queries (genuinely server-side, **not** frontend-only). Real-data: client names never leave Python — only a masked count reaches the screen |
| **Alert quality** (prioritize, bundle-by-brand, dedup, daily cap) | ✅ | ➖ | POC: dedup + bundle + 15/day cap. N/A to the single-offer tool |
| **Right-person routing** | ✅ | ✅ | POC: `target_trader_id` per alert. Real-data: routes to real traders from buy/sell history |
| **Brand dictionary** (YSL = Saint Laurent = …) — *client's #1 risk* | 🟡 | ✅ | POC: 50 curated brands. Real-data: **482 brands from the master** + alias/accent/punctuation/noise-suffix resolution, genuine unknowns flagged |

## §11–12 — Odoo Trade model & fields

| Item | Demo POC | Real-data build | Notes |
|---|:--:|:--:|---|
| Products / EAN / brand / category / price fields | 🟡 | ✅ | Real-data uses the actual `Products_Info` fields (avg/min purchase, avg/max sale) |
| Sales & Purchase history (buyer/salesperson/customer/vendor/dates) | 🟡 | ✅ | Real-data ingests both, incl. the **flattened-export ffill** fix (attribution 10%→100%) |
| **Multi-currency → EUR** (ECB rates) | ⛔ | ✅ | Real-data: date-aware ECB conversion (EUR/USD/GBP/JPY), cached + offline fallback |
| Trade model + Matched % | ⛔ | ⛔ | Not in the exports; a live-Odoo item |
| Live stock (Lot/Serial) | 🟡 | ⛔ | POC mock only |

## §13 — Stack & deployment

| Requirement | Status | Notes |
|---|:--:|---|
| Python 3.12 + FastAPI | ✅ | POC backend |
| React 18 + TypeScript + Tailwind | ✅ | POC frontend (trial screen is React+TS, plain CSS) |
| PostgreSQL 16 | ⛔ | POC uses **SQLite** as a Postgres stand-in |
| AWS EU (GDPR) deployment | ⛔ | Not deployed |
| Read-only Odoo integration (JSON-RPC) | ⛔ | Mock/file-based; no live connection |
| Google OAuth | ⛔ | Password-less JWT in POC |
| Claude / OpenAI for AI parts | ✅ | POC offer-inbox uses Claude Haiku; real-data parser has AI + heuristic paths |

---

## Honest caveats (say these plainly — they reward it)

- **Both builds run on data, not on live Odoo.** The POC is Odoo-*shaped* mock; the
  real-data build ingests the real Odoo *exports*. A live read-only JSON-RPC
  integration (and the Trade/Matched% model) is a real Phase-1 work item, not done.
- **No production scraper.** Retailer data is a provided file. The scraping subsystem
  (10 sites, anti-bot, change-detection) is genuinely unbuilt — and is the riskiest
  external dependency.
- **SQLite, not Postgres; no AWS; no OAuth.** Deliberate POC simplifications; all are
  straightforward to swap for the production stack the spec mandates.
- **The two builds are complementary, not redundant:** the POC shows we can build the
  *whole product surface*; the real-data build shows we can survive the *real mess*
  (482 brands, 4 currencies, 3 offer formats, flattened exports) — which is where the
  spec says the real risk lives.

## One-line summary

> The product surface (screens, 6 alerts, masking, catalog) is proven on mock data in
> the POC; the hard data layer (brand dictionary, EAN matching, multi-currency, messy
> offer parsing) is proven on the **real** client files in the Phase-1 build. What
> remains for production Phase 1 is the live Odoo integration, the retailer scraper, and
> the Postgres/AWS/OAuth stack — none of which change the logic already demonstrated.
