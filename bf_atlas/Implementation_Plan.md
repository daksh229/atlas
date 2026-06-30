# BF Atlas — Phase 1 Implementation Plan (Real-Data Foundation)

> **Status: implemented.** This is the original planning document and is kept for
> context. Some proposed module names below differ from the final code (e.g. the
> planned `build.py` / `load_db.py` / `sales.py` shipped as `build_db.py` /
> `schema.py` / `sources/orders.py` + `sources/history.py`, and the `synth/` and
> demand-derivation modules were consolidated into `synth/derive.py`). For the
> current structure and behaviour, see [ARCHITECTURE.md](ARCHITECTURE.md) and
> [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md).

> Branch: `Phase1`. This plan supersedes the original synthetic-POC plan. The
> objective of Phase 1 is to **replace the synthetic data flow with the real
> client package**, close the major data gaps, then polish the code so it stays
> correct and fast on a **large corpus** (the real Odoo export is ~20k products,
> ~64k sales lines, ~46k purchase lines — and production will be larger).

---

## 0. Guiding principle: real-first, synthesize-only-the-missing — in Odoo shape

The single rule that governs Phase 1:

1. **If the client package (`New folder/`) contains the data, use the real data.**
   Do not generate it.
2. **If an entity the product needs is *not* in the package, synthesize it — but
   strictly in the client's own schema and flow** (Odoo-shaped, EAN-keyed,
   multi-currency, access-controlled), so that swapping in a live read-only Odoo
   feed later is a near drop-in and the synthetic rows are indistinguishable in
   shape from real ones.

This keeps the app honest (real history drives every price/margin claim) while
still letting every screen and alert type function end-to-end.

### What is real vs. what we synthesize

| Entity | Source in `New folder/` | Decision |
|---|---|---|
| **Products** (name, EAN, brand, category, avg/min purchase, avg/max sale price) | `Products_Info.xlsx` (~20,588 rows, 482 brands) | **REAL** |
| **Sales history** (product, EAN, qty, unit price, currency, salesperson, date, customer) | `Sales_Order_History.xlsx` (~64k lines, EUR/USD/GBP) | **REAL** |
| **Purchase history** (product, EAN, unit price, currency, qty, buyer, date, vendor) | `Purchase_Order_History.xlsx` (~46k lines, EUR/USD/GBP/JPY) | **REAL** |
| **Supplier offers** (3 messy formats) | `offer_1/2/3_supplier.csv` | **REAL** (these are the trial inputs to evaluate) |
| **Retailer market prices** | `retailer_prices (2).csv` (EUR/USD/GBP) | **REAL** |
| **Traders** (roster) | Derived from `Salesperson` + `Buyer` columns (~24 unique) | **REAL (derived)** |
| **Customers / Vendors** (partners) | Derived from `Customer` (~650) + `Vendor` (~428) | **REAL (derived)** |
| **Team assignment** (5 teams) | Not in package | **SYNTHESIZE** — deterministic assignment of the ~24 real traders into 5 teams |
| **Demand signals / leads** (NetHunt forward-looking demand) | Not in package | **SYNTHESIZE** — derive "open demand" from recent real sales cadence + a small planted set, in the demand-signal schema |
| **Live inventory / stock lots** (Lot/Serial) | Not in package | **SYNTHESIZE** — Odoo stock-lot shape, seeded from real products |
| **Trade model + Matched %** | Not in package (exports are PO/SO level, not Trade level) | **SYNTHESIZE/DEFER** — model the schema, populate a representative subset; full Trade feed is a real-Odoo Phase-2 item |
| **FX rates** | Not in package | **REAL (live)** — European Central Bank reference rates, with a cached offline fallback |

> Honesty note for the client call: every margin/verdict shown is computed from
> **real** purchase/sale/retailer history. Only relational scaffolding that the
> export format omits (teams, leads, live stock) is synthetic, and it is clearly
> tagged as such in the data so it is never mistaken for real history.

---

## 1. The internal data contract (target schema)

Canonical, EAN-keyed, currency-normalized tables. All money stored **twice**:
original (`amount`, `currency`) and comparable (`amount_eur`), plus a
`fx_rate`/`fx_date` provenance and an `is_comparable` flag.

```
brands(brand_id, canonical_name, category, source)          -- built from Products_Info
brand_aliases(brand_id, alias_norm)                          -- generated normalisation map
products(ean, name, brand_id, category,
         avg_purchase_price_eur, min_purchase_price_eur,
         avg_sale_price_eur, max_sale_price_eur)             -- Products_Info (prices already EUR)
traders(trader_id, name, team_id, role)                      -- derived roster + synthetic teams
teams(team_id, name)                                         -- synthetic (5)
partners(partner_id, name, kind[customer|vendor], owner_trader_id)  -- derived from SO/PO
sales_history(ean, qty, unit_price, currency, unit_price_eur,
              salesperson_trader_id, customer_id, order_date)  -- Sales_Order_History (ffill'd)
purchase_history(ean, qty, unit_price, currency, unit_price_eur,
                 buyer_trader_id, vendor_id, confirmation_date) -- Purchase_Order_History (ffill'd)
supplier_offers(offer_id, source_file, supplier_name, brand_id, ean,
                product_name, size, qty, unit_price, currency,
                unit_price_eur, offer_date, match_status)     -- 3 offer adapters
retailer_prices(scan_date, retailer, country, brand_id, ean,
                product_name, price, currency, price_eur, in_stock)  -- retailer file
demand_signals(...)        -- SYNTHESIZED in schema (leads/open demand)
inventory(ean, lot, qty_available, ...)  -- SYNTHESIZED in Odoo stock shape
unresolved(source, raw_brand, raw_name, ean, reason)         -- everything we refused to force-match
fx_rates(date, currency, rate_to_eur, source)                -- ECB
build_report(metric, value)                                  -- coverage/quality metrics per build
```

**Join policy (non-negotiable):** EAN is the primary key linking offers ↔
products ↔ history ↔ retailer. Normalized brand+name is **fallback only**, used
when EAN is missing/unmatched, and any fallback match is recorded with lower
confidence. Unmatched rows go to `unresolved` — **never force-matched.**

---

## 2. The build pipeline (replaces the synthetic generator)

Reshape `data/pipeline/` so `build.py` orchestrates **ingest → normalize → load →
verify** over the real package, generating only the missing entities:

```
data/pipeline/
├── sources/
│   ├── products.py        # read Products_Info.xlsx → products + seed brand dictionary
│   ├── sales.py           # read Sales_Order_History.xlsx (ffill flattened cols)
│   ├── purchases.py       # read Purchase_Order_History.xlsx (ffill flattened cols)
│   ├── offers.py          # 3 format adapters → common offer schema
│   └── retailer.py        # read retailer_prices.csv
├── normalize/
│   ├── brands.py          # canonicalisation + alias generation (REWRITTEN, 482 brands)
│   ├── currency.py        # ECB rates + to_eur(amount, currency, date)
│   └── clean.py           # decimal commas, units (x50/pcs), tester-EAN, doubled-prefix, size parsing
├── synth/
│   ├── teams.py           # assign 24 real traders → 5 teams (deterministic)
│   ├── demand.py          # derive/plant demand signals in schema
│   └── inventory.py       # seed live stock lots in Odoo shape
├── load_db.py             # schema + bulk load (indexed, batched)
├── build.py               # orchestrate + emit build_report (coverage, unresolved, fx)
└── reports/_build_report.json
```

The **Trade/Matched% model** is schema-modeled here but populated as a
representative subset (full live Trade feed is a real-Odoo integration item).

---

## 3. Major gaps to close (do these first, in order)

These are the load-bearing gaps. Each must land with a measurable check.

### Gap 1 — Brand coverage (50 → 482)
- Build the working brand dictionary **from `Products_Info.xlsx`** (482 unique
  brands), not a hardcoded list.
- Normalisation must absorb: case, accents (`Hermès`→`hermes`), punctuation
  (`Y.S.L.`→`ysl`), doubled prefixes (`Electimuss Electimuss…`), and **noise
  suffixes** seen in retailer data (`" Paris"`, `" Beauty"`, `" London"`,
  truncations like `The`/`La`/`AS`).
- Keep a curated alias set for known multi-name brands (YSL / Saint Laurent /
  Yves Saint Laurent; Dior / Christian Dior; D&G / Dolce & Gabbana).
- **Check:** brand match-rate report on offers + retailer file; unresolved list
  is short and genuinely unknown (e.g. `LuxeNiche`, `MysticOud`, `Aurelia`).

### Gap 2 — EAN-first product matching
- Match every offer/retailer/history line to `products` on **EAN first**.
- Strip tester markers (trailing `T`), normalize leading-zero/length issues.
- Fallback to normalized brand+name only when EAN is absent/unmatched; flag it.
- **Check:** % of offer lines matched by EAN vs. fallback vs. unresolved.

### Gap 3 — Multi-currency normalization (ECB)
- Fetch **ECB reference rates**; convert every monetary value to EUR.
- Convert **at the row's own date** (offer/order/scan date), not "today"; fall
  back to nearest available rate; flag rows that can't be safely converted.
- Store original + EUR + rate + date. Products_Info prices are already EUR.
- **Check:** every EUR figure has a rate provenance; `is_comparable` coverage %.

### Gap 4 — Data quality (treat the mess as the problem)
- **Flattened-export ffill:** `Salesperson`/`Customer`/`Order Date` (sales) and
  `Buyer`/`Vendor`/`Confirmation Date` (purchases) appear only on the first line
  of each order — forward-fill before aggregating or ~90% of trader attribution
  is lost. *(This is the single highest-impact data fix.)*
- Decimal commas (`"255,00"` → `255.00`), mixed price tokens (`€51.39`,
  `12.25 EUR`), quantity tokens (`x50`, `60 pcs`, `24 units`), junk header rows
  (`*** STOCK OFFER ***`), missing EANs, inconsistent sizes.
- **Check:** per-file row-in/row-out counts; dropped-row reasons logged.

### Gap 5 — Real signal generation
- **Demand** from sales cadence (who reorders what, how often) + synthesized
  leads in schema. **Supply** from purchase history + offers. **Reorder** from
  real per-(customer, brand) cadence. **Market** from retailer prices.
- **Check:** each signal table is non-empty and traces back to real rows.

### Gap 6 — Trader mapping + access control on real partners
- Map real `Salesperson`/`Buyer` → `traders`; assign `partners.owner_trader_id`
  from who actually traded the account.
- Re-assert the spec's hard rule: a trader sees only their own accounts; others
  appear masked (`via <colleague>`), enforced server-side.
- **Check:** two traders get disjoint client/supplier sets; masking holds.

---

## 4. Then: partial improvements (after the gaps close)

Smaller, high-value refinements once the foundation is real:

- Size/volume parsing into a comparable unit (ml) for like-for-like pricing.
- Per-EAN price bands (p25/median/p75) instead of single avg, for robust verdicts.
- Retailer spread/outlier handling (drop obviously broken scrapes before using as market).
- Offer-date staleness flag (offers from 2024 vs. retail scans from 2025).
- Confidence scoring on every match (EAN-exact > brand+name > brand-only).
- Coverage dashboard surfaced in the UI (honest "X% matched, Y unresolved").

---

## 5. Code polishing (quality pass)

After behavior is correct, raise the code quality bar across `data/pipeline/`,
`backend/app/services/`, and the trial offer-evaluator:

- **Single responsibility:** one module per source/normalizer; no god-functions.
- **Pure, testable core:** parsing/normalization/verdict logic as pure functions
  taking DataFrames/dicts and returning DataFrames/dicts — no hidden I/O.
- **Typed boundaries:** type hints + small dataclasses/`TypedDict` for the
  internal record shapes (offer line, product ref, verdict).
- **One config surface:** thresholds (margin bands), paths, currency base, FX
  source live in one `config`/`settings` object — tunable and explainable on the call.
- **Deterministic builds:** fixed seeds for any synthesis; same inputs → same DB.
- **Tests:** unit tests for each adapter against the 3 real offer files + golden
  fixtures for the messy cases (decimal comma, doubled prefix, tester EAN, USD row).
- **Logging not prints:** structured logs with per-stage counts; a build summary.
- **Docstrings that explain *why*** (especially every data-quality decision), so
  the "walk us through your code" call is easy.

---

## 6. Large-corpus engineering standards (build for future scale)

> **Instruction for all Phase-1 code:** assume the real corpus is large and
> growing (today ~130k rows across files; production Odoo is far bigger). Write
> every data-path component so it scales without a rewrite.

Concrete rules:

1. **Vectorize, never iterate rows.** Use pandas/SQL set operations; ban
   `df.iterrows()`/Python loops over rows in hot paths. Merges on indexed keys (EAN).
2. **Stream/chunk large reads.** Read Excel/CSV in chunks where feasible; process
   and release. Don't hold multiple full copies of a 64k-row frame in memory.
3. **Push work into SQLite/SQL.** Do joins/aggregations in the database with
   proper **indexes** (`ean`, `brand_id`, `owner_trader_id`, `order_date`),
   not in Python. Batch inserts via `executemany`/`to_sql(method='multi')`.
4. **Idempotent, incremental builds.** Builds are re-runnable; design so a future
   version can ingest only new/changed rows (date-watermarked) rather than full reload.
5. **Bounded memory + explicit dtypes.** Set column dtypes on read (category for
   brand, string for EAN to preserve leading zeros); downcast numerics.
6. **Pagination & limits at the API/UI.** Never return an unbounded result set;
   server-side filter/paginate. Precompute heavy aggregates at build time.
7. **Cache the stable, recompute the volatile.** FX rates and brand dictionary
   cached; only signals/alerts recomputed per run.
8. **Profile the hot path.** Keep a timing log per pipeline stage; flag any stage
   that grows worse than linearly with input size.
9. **Fail loud on data scale issues.** Assert expected row-count ranges; surface
   coverage drops in the build report instead of silently shrinking.

These standards are requirements, not suggestions — every PR on `Phase1` should
be checkable against them.

---

## 7. Build order (recommended sequence)

1. Internal schema + `load_db.py` (indexed) + `config`.
2. `currency.py` (ECB + cache) — needed by every money column.
3. `products.py` + brand dictionary from Products_Info (Gap 1).
4. `sales.py` + `purchases.py` with ffill + EUR (Gaps 3, 4).
5. EAN matcher + `unresolved` reporting (Gap 2).
6. Offer adapters (3) → common schema (Gaps 2, 4) — also powers the trial tool.
7. `retailer.py` + market join (Gap 3, 5).
8. `synth/` teams, demand, inventory — in client schema (Section 0).
9. Trader mapping + access control on real partners (Gap 6).
10. Signals + matching/alerts rebuilt on real tables (Gap 5).
11. Partial improvements (Section 4).
12. Code polish + tests + large-corpus pass (Sections 5, 6).
13. Verification (below).

The **trial offer-evaluator** (small React page + EAN-join + EUR + verdict) sits
on top of steps 1–7 and stays deliberately small for submission; the rest of the
sequence builds the real-data foundation the full Atlas needs.

---

## 8. Verification & acceptance (per build)

`build.py` must emit a `_build_report.json` with:

- Import counts per file (rows in / rows loaded / rows dropped + reasons).
- Brand match-rate (offers, retailer) + unresolved brand list.
- EAN match-rate (exact / fallback / unresolved) per source.
- FX coverage (% of monetary rows with a comparable EUR value).
- Trader/partner attribution coverage (% of history lines with an owner).
- Signal counts (demand/supply/reorder/market) — all non-empty.
- A sanity run of all 3 offers through the evaluator returning verdicts.

Acceptance = real data loaded, gaps closed with measurable coverage, no silent
data loss, and all checks green on the large corpus within a sensible runtime.

---

## 9. Keep vs. rewrite

**Keep:** frontend app shell & routing, backend router structure, trader-scoped
access-control concept, brand-dictionary + EAN-join concept, the overall BF Atlas
product story, the matching/alerts *interfaces*.

**Rewrite/heavily refactor:** `data/pipeline/generate_raw.py` (→ real `sources/`),
`preprocess.py` (→ `normalize/`), the 50-brand hardcoded dictionary (→ 482 from
Products_Info), synthetic signal planting (→ derived from real history), currency
assumptions (→ ECB normalization), and any row-by-row logic (→ vectorized/SQL).
