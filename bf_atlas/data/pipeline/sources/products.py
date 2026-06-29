"""
products.py — ingest the product master (`Products_Info.xlsx`).

This file is the spine of the whole system: one row per product (EAN) with the
brand, category, and BF's own average/min purchase and average/max sale prices
(already in EUR). It also seeds the brand dictionary.

Output:
  - product rows keyed by EAN (the join key for every other source)
  - a populated BrandDictionary
  - a coverage report (rows in / kept / dropped, brand count)
"""

from __future__ import annotations

import warnings

import pandas as pd

from data.pipeline.config import PATHS
from data.pipeline.normalize.brands import BrandDictionary
from data.pipeline.normalize.clean import clean_ean

# Source column → meaning. Kept explicit so a schema change is a one-line fix.
COLS = {
    "name": "Name",
    "barcode": "Product/Barcode",
    "category": "Product Category",
    "brand": "Brand",
    "avg_pp": "Avg. Purchase Price",
    "min_pp": "Min Purchase Price (mPP)",
    "avg_sp": "Avg. Sale Price",
    "max_sp": "Max Selling Price (MSP)",
}


def _num(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def load_products() -> dict:
    """Returns {'products': [...], 'brand_dict': BrandDictionary, 'report': {...}}."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        # Barcode forced to string so leading zeros and big ints survive intact.
        df = pd.read_excel(PATHS.products, dtype={COLS["barcode"]: "string"})

    rows_in = len(df)

    # Build the brand dictionary from the (raw brand, category) pairs.
    brand_records = list(
        df[[COLS["brand"], COLS["category"]]]
        .dropna(subset=[COLS["brand"]])
        .itertuples(index=False, name=None)
    )
    brand_dict = BrandDictionary.from_records(brand_records)

    # Vectorized cleaning of the join key + prices.
    df["_ean"] = df[COLS["barcode"]].map(clean_ean)
    for key in ("avg_pp", "min_pp", "avg_sp", "max_sp"):
        df[f"_{key}"] = _num(df[COLS[key]])

    kept = df[df["_ean"].notna()].copy()
    dropped_no_ean = rows_in - len(kept)

    # Resolve brand per row (fast: map over the small set of distinct brands).
    distinct = kept[COLS["brand"]].dropna().unique()
    brand_map = {b: brand_dict.resolve(b) for b in distinct}
    kept["_brand_id"] = kept[COLS["brand"]].map(brand_map)

    # Collapse to one record per EAN (first wins) — EAN is the primary key.
    kept = kept.drop_duplicates(subset="_ean", keep="first")

    # Build a clean, renamed frame and emit records (vectorized, no row loops).
    out = pd.DataFrame({
        "ean": kept["_ean"],
        "id": kept["_ean"],                     # EAN is the product id
        "name": kept[COLS["name"]].astype("string"),
        "brand_id": kept["_brand_id"],
        "category": kept[COLS["category"]].astype("string"),
        "avg_purchase_price_eur": kept["_avg_pp"],
        "min_purchase_price_eur": kept["_min_pp"],
        "avg_sale_price_eur": kept["_avg_sp"],
        "max_sale_price_eur": kept["_max_sp"],
    })
    products = out.where(out.notna(), None).to_dict("records")

    report = {
        "rows_in": rows_in,
        "products_kept": len(products),
        "dropped_no_ean": int(dropped_no_ean),
        "brands": len(brand_dict),
        "brand_resolved_rate": round(
            kept["_brand_id"].notna().mean() if len(kept) else 0.0, 4
        ),
    }
    return {"products": products, "brand_dict": brand_dict, "report": report}


def _none(v):
    return None if pd.isna(v) else float(v)
