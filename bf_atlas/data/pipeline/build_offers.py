"""
build_offers.py — end-to-end run of the offer evaluator (the trial deliverable).

    products + history + retailer + ECB  ──▶  evaluate each offer line  ──▶  JSON

Produces `reports/offer_evaluation.json`: per-offer-file results a trader can act
on (verdict, the numbers behind it, and who internally should know), plus a
coverage report. The minimal React screen reads this JSON directly.

Run:  python -m data.pipeline.build_offers
"""

from __future__ import annotations

import json
import os
from collections import defaultdict

from data.pipeline.config import PATHS
from data.pipeline.normalize.currency import CurrencyConverter
from data.pipeline.sources.products import load_products
from data.pipeline.sources.history import load_history
from data.pipeline.sources.retailer import load_retailer
from data.pipeline.sources.offers import load_offers
from data.pipeline.analysis.evaluate import evaluate_all, Refs


def _brand_aggregates(products, hist, product_by_ean) -> dict:
    """Per-brand context: typical buy/sell EUR + which traders work the brand.
    Used only when an offer line has no exact EAN match (flagged context)."""
    price: dict[str, dict] = defaultdict(lambda: {"buys": [], "sales": [], "n": 0})
    for p in products:
        bid = p.get("brand_id")
        if not bid:
            continue
        price[bid]["n"] += 1
        if p.get("avg_purchase_price_eur"):
            price[bid]["buys"].append(p["avg_purchase_price_eur"])
        if p.get("avg_sale_price_eur"):
            price[bid]["sales"].append(p["avg_sale_price_eur"])

    routing: dict[str, dict] = defaultdict(lambda: {"buy": set(), "sell": set()})
    for ean, agg in hist["buy_by_ean"].items():
        bid = (product_by_ean.get(ean) or {}).get("brand_id")
        if bid:
            routing[bid]["buy"].update(agg.get("buy_traders", []))
    for ean, agg in hist["sell_by_ean"].items():
        bid = (product_by_ean.get(ean) or {}).get("brand_id")
        if bid:
            routing[bid]["sell"].update(agg.get("sell_traders", []))

    out: dict[str, dict] = {}
    for bid, pr in price.items():
        out[bid] = {
            "avg_buy_eur": round(sum(pr["buys"]) / len(pr["buys"]), 2) if pr["buys"] else None,
            "avg_sale_eur": round(sum(pr["sales"]) / len(pr["sales"]), 2) if pr["sales"] else None,
            "n_products": pr["n"],
            "buy_traders": sorted(routing[bid]["buy"]),
            "sell_traders": sorted(routing[bid]["sell"]),
        }
    return out


def main() -> dict:
    fx = CurrencyConverter.load()

    print("· loading product master + brand dictionary …")
    prod = load_products()
    bd = prod["brand_dict"]
    product_by_ean = {p["ean"]: p for p in prod["products"]}

    print("· loading purchase + sales history (ffill + EUR) …")
    hist = load_history(fx)

    print("· loading retailer market scan …")
    retail = load_retailer(bd, fx)

    print("· parsing the three supplier offers …")
    off = load_offers(bd, fx)

    print("· rolling up brand-level context …")
    brand_ref = _brand_aggregates(prod["products"], hist, product_by_ean)

    def get_refs(offer):
        ean = offer.get("ean")
        return Refs(
            product=product_by_ean.get(ean),
            buy=hist["buy_by_ean"].get(ean),
            sell=hist["sell_by_ean"].get(ean),
            market=retail["market_by_ean"].get(ean),
            brand=brand_ref.get(offer.get("brand_id")),
        )

    results = evaluate_all(off["offers"], get_refs)

    by_file: dict[str, list] = defaultdict(list)
    for r in results:
        by_file[r["source_file"]].append(r)

    verdict_counts: dict[str, dict] = {}
    for f, rows in by_file.items():
        c = defaultdict(int)
        for r in rows:
            c[r["verdict"]] += 1
        verdict_counts[f] = dict(c)

    payload = {
        "offers": {f: rows for f, rows in by_file.items()},
        "report": {
            "products": prod["report"],
            "history": hist["report"],
            "retailer": retail["report"],
            "offers": off["report"],
            "verdicts": verdict_counts,
            "fx_source": fx._source,
        },
    }

    os.makedirs(PATHS.reports_dir, exist_ok=True)
    out_path = os.path.join(PATHS.reports_dir, "offer_evaluation.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False, default=str)

    # Publish a copy where the minimal React page reads it.
    web_public = os.path.join(PATHS.processed_dir, "..", "..", "..", "trial", "web", "public")
    web_public = os.path.abspath(web_public)
    if os.path.isdir(web_public):
        with open(os.path.join(web_public, "offer_evaluation.json"), "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, default=str)

    print(f"\n=== offer evaluation written → {out_path} ===")
    for f, c in verdict_counts.items():
        print(f"  {f:10s} {dict(c)}")
    return payload


if __name__ == "__main__":
    main()
