# BF Atlas Real-Data Implementation Plan

## Goal

Keep the current BF Atlas app shell and replace the synthetic POC data flow with a real import, normalization, and matching pipeline built from the client files in `New folder`.

This approach preserves the strongest parts of the current project:

- frontend navigation and screens
- backend API structure
- trader-scoped access-control concept
- alerting and brand-intelligence product direction

The main remaining work is in the data layer, not the UI layer.

---

## Current Situation

The current POC is strong as a clickable product prototype, but it is not yet aligned with the real BF sample package.

What is already in good shape:

- FastAPI backend with clear business-domain services and routers
- React + TypeScript + Tailwind frontend with the main application screens
- trader-scoped auth and masking model
- offer inbox, retailer radar, brand maps, and brand catalog screens
- synthetic pipeline proving the product concept end-to-end

What is still missing:

- importing the real Excel and CSV files
- handling large real-world datasets
- expanding the brand dictionary beyond the current limited catalog
- barcode/EAN-driven reconciliation
- multi-currency normalization
- rebuilding signals and alerts from imported data instead of planted demo scenarios

---

## Files To Implement Around

### Product Master

- `New folder/Products_Info.xlsx`

Primary fields observed:

- `Name`
- `Product/Barcode`
- `Product Category`
- `Brand`
- `Avg. Purchase Price`
- `Min Purchase Price (mPP)`
- `Avg. Sale Price`
- `Max Selling Price (MSP)`

### Sales History

- `New folder/Sales_Order_History.xlsx`

Primary fields observed:

- `Order Lines/Product`
- `Order Lines/Barcode`
- `Order Lines/Product Qty`
- `Order Lines/Unit Price`
- `Order Lines/Currency`
- `Salesperson`
- `Order Date`
- `Customer`

### Purchase History

- `New folder/Purchase_Order_History.xlsx`

Primary fields observed:

- `Order Lines/Product`
- `Order Lines/Product/Barcode`
- `Order Lines/Unit Price`
- `Order Lines/Currency`
- `Order Lines/Quantity`
- `Buyer`
- `Confirmation Date`
- `Vendor`

### Supplier Offers

- `New folder/offer_1_supplier.csv`
- `New folder/offer_2_supplier.csv`
- `New folder/offer_3_supplier.csv`

Observation:

- these files do not follow one common schema
- at least one of them is highly messy and needs custom parsing

### Retailer Prices

- `New folder/retailer_prices (2).csv`

Primary fields observed:

- `scan_date`
- `retailer`
- `country`
- `brand`
- `product_name`
- `sku_observed`
- `size`
- `ean`
- `current_price`
- `currency`
- `in_stock`

---

## Main Gaps Identified

### 1. Brand Coverage Gap

The current POC brand dictionary is too small for the real package.

Observed overlap:

- `Products_Info.xlsx`: 482 unique brands, only 43 matched by the current dictionary
- `retailer_prices (2).csv`: 151 unique brand values, only 8 matched

This is the biggest implementation gap.

### 2. Product Matching Gap

The real files include barcode/EAN fields, but the current POC is built mostly around a smaller synthetic brand-first dataset.

The real implementation should use:

1. barcode/EAN as the primary product key
2. normalized brand + normalized product name as fallback
3. unresolved reporting when no safe match exists

### 3. Currency Gap

The real package includes multiple currencies:

- `EUR`
- `USD`
- `GBP`
- `JPY`

The current POC price logic assumes a much simpler environment, so normalization is still needed before reliable comparison and alerting.

### 4. Data Quality Gap

The real package contains:

- inconsistent brand spelling
- formatting noise
- incomplete rows
- flattened exports with blank repeated values
- inconsistent size formats
- multiple supplier-offer file layouts

### 5. Signal Generation Gap

The current alerts are driven by planted synthetic scenarios.

The new implementation must derive signals from:

- real product master data
- sales order history
- purchase order history
- supplier offers
- retailer market prices

---

## Implementation Phases

## Phase 1: Define The Internal Data Contract

Goal:
Map each client file into a stable internal schema.

Tasks:

1. Define canonical tables:
   - `brands`
   - `brand_aliases`
   - `products`
   - `sales_history`
   - `purchase_history`
   - `supplier_offers`
   - `retailer_prices`
   - `unresolved_matches`
2. Write field mappings from each input file to the internal schema.
3. Decide key relationships:
   - product identity
   - brand identity
   - customer/vendor ownership
   - currency handling

Deliverable:

- a documented import contract for every BF file

## Phase 2: Replace Synthetic Pipeline Inputs

Goal:
Stop generating fake raw data and build from the real package.

Tasks:

1. Replace `data/pipeline/generate_raw.py` with real import scripts.
2. Add loaders for:
   - products
   - sales history
   - purchase history
   - supplier offers
   - retailer prices
3. Keep the orchestration idea in `build.py`, but change the sequence to:
   - import
   - normalize
   - load database
   - verify coverage and unresolved records

Deliverable:

- reproducible database build from the BF sample files only

## Phase 3: Rebuild Brand And Product Normalization

Goal:
Move from a 50-brand demo dictionary to a real normalization system.

Tasks:

1. Generate the working brand catalog from `Products_Info.xlsx`.
2. Build brand normalization helpers for:
   - case differences
   - punctuation
   - accents
   - suffix noise like `Paris`, `Beauty`, etc.
   - variants like `Y.S.L.` vs `Yves Saint Laurent`
3. Add product reconciliation by barcode/EAN first.
4. Add unresolved brand and unresolved product reports.

Deliverable:

- a robust normalization layer that does not silently lose matches

## Phase 4: Add Currency Normalization

Goal:
Make price comparisons reliable across all input sources.

Tasks:

1. Detect original currency in all imports.
2. Convert to a common comparison currency for analytics.
3. Store both:
   - original price
   - original currency
   - normalized comparable price
4. Flag any row that cannot be safely compared.

Deliverable:

- one trustworthy price basis for alerting and retailer comparison

## Phase 5: Build Real Signals From Imported Data

Goal:
Generate demand, supply, and market signals from the actual files.

Tasks:

1. From `Sales_Order_History.xlsx`:
   - derive customer demand history
   - derive reorder cadence
   - derive best historical sale price
2. From `Purchase_Order_History.xlsx`:
   - derive sourcing history
   - derive historical buy-side behavior
   - derive buyer/vendor relationships
3. From offer files:
   - generate fresh supplier-offer signals
4. From retailer prices:
   - generate external market signals

Deliverable:

- real signal tables replacing synthetic planted scenarios

## Phase 6: Rewrite Matching And Alerts Around Real Data

Goal:
Make the matching engine use imported BF data rather than demo-only data.

Tasks:

1. Demand-supply matching:
   - customer-side demand vs supplier offers
2. External market window:
   - retailer prices vs available or benchmark buy prices
3. Reorder reminders:
   - cadence inferred from real sales history
4. Offer-to-request:
   - supplier offer imports matched against relevant demand indicators
5. Triple-match logic:
   - only if supported cleanly by the imported sources

Deliverable:

- alert generation backed by real imported records

## Phase 7: Refactor Backend Services With Stable API Shapes

Goal:
Preserve the good backend structure while changing the data source logic.

Main files likely to change:

- `backend/app/services/matching.py`
- `backend/app/services/alerts.py`
- `backend/app/services/brands.py`
- `backend/app/services/offers.py`
- `backend/app/services/radar.py`
- `backend/app/services/relationships.py`
- `data/pipeline/*`

Tasks:

1. keep router structure where possible
2. update services to use imported normalized tables
3. add data-quality reporting where helpful

Deliverable:

- the frontend can keep most of its current contract while backend behavior becomes real-data-driven

## Phase 8: Update Frontend For Real-Data Honesty

Goal:
Keep the UI, but make it truthful about imported data quality.

Tasks:

1. add indicators for:
   - unresolved brands
   - unmatched offers
   - unknown products
   - normalized currency basis
2. remove wording that assumes complete or planted coverage
3. keep the current page layout and navigation unless the new data requires a change

Deliverable:

- a production-like interface with honest data-state messaging

## Phase 9: Verification And Trial Readiness

Goal:
Make the implementation defensible and demo-safe.

Tasks:

1. verify import counts by file
2. verify brand match rates
3. verify unresolved counts
4. verify currency conversion coverage
5. verify alert generation is non-empty and reasonable
6. add summary checks for data quality

Deliverable:

- a trial-ready build with measurable confidence, not only a demo flow

---

## Recommended Build Order

1. Define schema and field mappings
2. Import `Products_Info.xlsx`
3. Import sales history
4. Import purchase history
5. Import supplier offers
6. Import retailer prices
7. Build brand and product normalization
8. Add currency normalization
9. Rework matching and alert generation
10. Update frontend wording and reporting
11. Verify results end-to-end

---

## What To Keep vs What To Rewrite

### Keep

- frontend app structure
- page routing
- backend router structure
- authentication/session flow
- trader-scoped access-control direction
- overall BF Atlas product story

### Rewrite Or Heavily Refactor

- `data/pipeline/generate_raw.py`
- much of `data/pipeline/preprocess.py`
- the small hardcoded brand dictionary approach
- synthetic signal generation
- alert logic assumptions tied to planted data
- offer ingestion assumptions based on fixture emails

---

## Honest Progress Estimate

Approximate status after reviewing the real files:

- product/app shell: `70-80% done`
- backend architecture: `65-75% done`
- real-data ingestion readiness: `20-30% done`
- trial-package alignment overall: about `40% done`

Interpretation:

- the visible product foundation is already strong
- the bulk of remaining work is in the data integration and normalization layer
- this is not a frontend rebuild
- this is mainly a data-model, importer, and matching rewrite

---

## Practical Next Step

The best next move is:

1. create the internal schema mapping from the BF files
2. implement the real import pipeline
3. measure unresolved brands/products early
4. only then adjust matching and alerts

That gives the fastest path from a polished POC to a trial-aligned implementation.
