# BF Atlas — Supplier Offer Evaluator (trial)

A small tool that takes a messy supplier offer and helps a trader judge it
against BF's own data: **is this a good offer, and who internally should know?**

It runs against all three offer formats, joins on **EAN**, normalizes every
price to **EUR using ECB reference rates**, and produces a simple screen showing
which offer lines are worth attention and why.

## How it works

```
Products_Info  ┐
Sales history   ├─▶  ingest + normalize (brand dict, EAN, ECB→EUR, ffill)  ┐
Purchase hist   │                                                          ├─▶  evaluate each
Retailer prices ┘                                                          │    offer line
Supplier offers (×3 formats) ─────────────────────────────────────────────┘    (verdict + why
                                                                                 + who should know)
                                                                                      │
                                                                                      ▼
                                                                          offer_evaluation.json
                                                                                      │
                                                                                      ▼
                                                                            minimal React screen
```

The analysis lives in [`data/pipeline/`](../data/pipeline): `normalize/` (cleaning,
currency, brand dictionary), `sources/` (one adapter per real file),
`analysis/evaluate.py` (the verdict logic), and `build_offers.py` (orchestration).

## Run it

```bash
# 1. from the repo root — build the evaluation JSON (live ECB rates, cached)
python -m data.pipeline.build_offers

# 2. the screen
cd trial/web
npm install
npm run dev          # opens http://localhost:5174
```

`build_offers` publishes the JSON to `trial/web/public/offer_evaluation.json`,
which the page reads directly — no backend, no database, no login.

## The verdict, in one line

An offer line is **good** when the offered price (in EUR) is at or below what BF
usually pays *and* leaves healthy resale headroom against the conservative of
{our average sale price, the live market price}. Unmatched EANs are never
force-matched — they fall back to clearly-flagged brand-level context.

Margin bands and price bases are in [`data/pipeline/config.py`](../data/pipeline/config.py)
— deliberately visible and tunable, since the client gave no target margin.
