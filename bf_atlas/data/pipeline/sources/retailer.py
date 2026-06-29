"""
retailer.py — ingest the retailer price scan (the external market check).

Per-EAN we keep the competitive picture: the min and median observed retail
price (normalized to EUR at scan date), how many retailers list it, and whether
any have it in stock. Brand is resolved for display, but the EAN is the join.
"""

from __future__ import annotations

import pandas as pd

from data.pipeline.config import PATHS
from data.pipeline.normalize.brands import BrandDictionary
from data.pipeline.normalize.clean import clean_ean
from data.pipeline.normalize.currency import CurrencyConverter

COLS = {
    "scan_date": "scan_date", "retailer": "retailer", "country": "country",
    "brand": "brand", "product": "product_name", "ean": "ean",
    "price": "current_price", "currency": "currency", "in_stock": "in_stock",
}


def load_retailer(bd: BrandDictionary, fx: CurrencyConverter | None = None) -> dict:
    fx = fx or CurrencyConverter.load()
    df = pd.read_csv(PATHS.retailer, dtype={COLS["ean"]: "string"})

    df["_ean"] = df[COLS["ean"]].map(clean_ean)
    df["_date"] = df[COLS["scan_date"]].astype("string").str.slice(0, 10)
    df["_price"] = pd.to_numeric(df[COLS["price"]], errors="coerce")
    df["_ccy"] = df[COLS["currency"]].astype("string").str.upper()

    # Vectorized EUR conversion (one ECB lookup per unique currency+date).
    keys = df[["_ccy", "_date"]].drop_duplicates().copy()
    keys["_factor"] = [
        fx.to_eur(1.0, c, d).amount_eur for c, d in keys[["_ccy", "_date"]].itertuples(index=False)
    ]
    df = df.merge(keys, on=["_ccy", "_date"], how="left")
    df["_price_eur"] = (df["_price"] * df["_factor"]).round(2)

    df = df[df["_ean"].notna() & df["_price_eur"].notna()]

    market: dict[str, dict] = {}
    for ean, g in df.groupby("_ean"):
        in_stock = g[COLS["in_stock"]].astype("string").str.upper().eq("Y").any()
        market[ean] = {
            "market_min_eur": round(float(g["_price_eur"].min()), 2),
            "market_median_eur": round(float(g["_price_eur"].median()), 2),
            "retailers": int(g[COLS["retailer"]].nunique()),
            "in_stock": bool(in_stock),
        }

    # Per-scan rows for the retailer_prices table (the Radar screen reads these).
    bmap = {b: bd.resolve(b) for b in df[COLS["brand"]].dropna().unique()}
    in_stock_str = df[COLS["in_stock"]].astype("string").str.upper().eq("Y")
    out = pd.DataFrame({
        "id": [f"ret-{i:06d}" for i in range(len(df))],
        "retailer": df[COLS["retailer"]].astype("string"),
        "brand_id": df[COLS["brand"]].map(bmap),
        "brand_surface": df[COLS["brand"]].astype("string"),
        "product_name": df[COLS["product"]].astype("string"),
        "price": df["_price_eur"],
        "stock_status": in_stock_str.map({True: "in_stock", False: "out"}),
        "scanned_at": df["_date"],
        "is_mock": 0,
    })
    rows = out.where(out.notna(), None).to_dict("records")

    report = {
        "rows": len(df),
        "eans_with_market": len(market),
        "brand_resolved_rate": round(
            df[COLS["brand"]].map(lambda b: bd.resolve(b) is not None).mean(), 4
        ),
    }
    return {"market_by_ean": market, "rows": rows, "report": report}
