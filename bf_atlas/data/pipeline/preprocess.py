"""
preprocess.py — canonicalise the raw seed into load-ready records.

This is where the §9 brand dictionary does its job. Raw data refers to brands by
arbitrary surface forms ("YSL", "Saint Laurent", "Yves Saint-Laurent"); this step
resolves every one of them to a single canonical brand_id, so the downstream
matching engine can join on brand_id and never miss a match.

Steps:
  1. Build the dictionary tables (brands + brand_aliases) and a resolver index.
  2. Resolve brand_surface → brand_id on products, order lines, signals, retailer
     rows. Our own data MUST resolve (anything that doesn't is a seed bug).
  3. Retailer rows may contain genuinely unknown brands → keep them with
     brand_id=None and record them in an "unresolved" report. They are FLAGGED,
     never force-matched (data-provenance requirement).
  4. Emit processed/*.json for load_db.py.

Run (after generate_raw.py):  python preprocess.py
"""

import json
import os
import re
import unicodedata

from brands import BRANDS

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
PROCESSED = os.path.join(HERE, "processed")


def normalize(text: str) -> str:
    """Fold case, accents and punctuation so 'L'Oréal' == 'loreal'."""
    if text is None:
        return ""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)  # drop &, ., -, ' etc.
    return re.sub(r"\s+", " ", text).strip()


def build_dictionary():
    """Return (brands_rows, alias_rows, resolver) from the canonical BRANDS list."""
    brands_rows, alias_rows, resolver = [], [], {}
    for idx, (canonical, category, aliases) in enumerate(BRANDS, start=1):
        bid = f"brand-{idx:03d}"
        brands_rows.append({"id": bid, "canonical_name": canonical, "category": category})
        # canonical name resolves to itself
        resolver[normalize(canonical)] = bid
        for alias in aliases:
            alias_rows.append({"id": f"alias-{len(alias_rows)+1:03d}", "brand_id": bid,
                               "alias": alias})
            resolver[normalize(alias)] = bid
    return brands_rows, alias_rows, resolver


def load_raw(name: str):
    with open(os.path.join(RAW, f"{name}.json"), "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    os.makedirs(PROCESSED, exist_ok=True)
    brands_rows, alias_rows, resolver = build_dictionary()
    unresolved = []  # surface forms we could not map (for the report)

    def resolve(surface: str, *, required: bool, context: str):
        bid = resolver.get(normalize(surface))
        if bid is None and required:
            # our own internal data should never contain an unknown brand
            raise ValueError(f"[{context}] unresolved internal brand: {surface!r}")
        if bid is None:
            unresolved.append({"surface": surface, "context": context})
        return bid

    out = {"brands": brands_rows, "brand_aliases": alias_rows}
    out["traders"] = load_raw("traders")
    out["partners"] = load_raw("partners")

    # products: resolve brand_surface → brand_id
    products = []
    for p in load_raw("products"):
        bid = resolve(p["brand_surface"], required=True, context="product")
        products.append({k: v for k, v in p.items() if k != "brand_surface"} | {"brand_id": bid})
    out["products"] = products

    out["inventory"] = load_raw("inventory")

    # orders: flatten embedded lines into separate line tables, resolve brands
    def split_orders(name, line_table):
        headers, lines = [], []
        for o in load_raw(name):
            order_lines = o.pop("lines")
            headers.append(o)
            for ln in order_lines:
                bid = resolve(ln["brand_surface"], required=True, context=name)
                lines.append({"id": f"{line_table}-{len(lines)+1:05d}", "order_id": o["id"],
                              "product_id": ln["product_id"], "brand_id": bid,
                              "qty": ln["qty"], "unit_price": ln["unit_price"],
                              "subtotal": ln["subtotal"]})
        return headers, lines

    out["sale_orders"], out["sale_order_lines"] = split_orders("sale_orders", "sol")
    out["purchase_orders"], out["purchase_order_lines"] = split_orders("purchase_orders", "pol")

    # signals: resolve brand, assign ids
    def with_brand(name, prefix, required=True):
        rows = []
        for i, r in enumerate(load_raw(name), start=1):
            bid = resolve(r["brand_surface"], required=required, context=name)
            rows.append({"id": f"{prefix}-{i:04d}",
                         **{k: v for k, v in r.items() if k != "brand_surface"},
                         "brand_id": bid})
        return rows

    out["demand_signals"] = with_brand("demand_signals", "dem")
    out["supply_signals"] = with_brand("supply_signals", "sup")
    # retailer rows: unknown brands allowed → flagged, not force-matched
    retailer = []
    for i, r in enumerate(load_raw("retailer_prices"), start=1):
        bid = resolve(r["brand_surface"], required=False, context="retailer")
        retailer.append({"id": f"ret-{i:04d}", **r, "brand_id": bid})
    out["retailer_prices"] = retailer

    # write processed
    for name, rows in out.items():
        with open(os.path.join(PROCESSED, f"{name}.json"), "w", encoding="utf-8") as f:
            json.dump(rows, f, indent=2, ensure_ascii=False)
    with open(os.path.join(PROCESSED, "_unresolved_report.json"), "w", encoding="utf-8") as f:
        json.dump(unresolved, f, indent=2, ensure_ascii=False)

    print("=== preprocess → data/pipeline/processed/ ===")
    print(f"  brands {len(brands_rows)}  aliases {len(alias_rows)}")
    for name in ("products", "sale_order_lines", "purchase_order_lines",
                 "demand_signals", "supply_signals", "retailer_prices"):
        print(f"  {name:22s} {len(out[name])}")
    print(f"  unresolved (retailer-only, flagged): {len(unresolved)} "
          f"→ {[u['surface'] for u in unresolved]}")


if __name__ == "__main__":
    main()
