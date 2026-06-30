"""
build_db.py — build atlas.db from the source data package.

Populates the schema (so the FastAPI services and React screens run unchanged)
from the Odoo exports + offers + retailer file, deriving demand from sales and
synthesizing only what the exports omit (live stock, teams).

    products + orders + partners + signals + retailer  ──▶  atlas.db (SQLite)

Run:  python -m data.pipeline.build_db
"""

from __future__ import annotations

import os
import sqlite3

import pandas as pd

from data.pipeline.config import PATHS
from data.pipeline.load_db import SCHEMA, COLUMNS
from data.pipeline.normalize.currency import CurrencyConverter
from data.pipeline.sources.products import load_products
from data.pipeline.sources.orders import load_orders
from data.pipeline.sources.retailer import load_retailer
from data.pipeline.sources.offers import load_offers
from data.pipeline.synth.derive import (
    derive_demand, supply_from_purchases, supply_from_offers,
    synth_inventory, assign_teams,
)


def _brand_dominant_buyer(purch_df: pd.DataFrame, product_by_ean: dict) -> dict:
    df = purch_df.copy()
    df["_brand_id"] = df["_ean"].map(lambda e: (product_by_ean.get(e) or {}).get("brand_id") if e else None)
    df = df[df["_brand_id"].notna() & df["_trader_id"].notna()]
    return (
        df.groupby("_brand_id")["_trader_id"]
        .agg(lambda s: s.mode().iat[0] if not s.mode().empty else None)
        .to_dict()
    )


def _products_rows(products: list[dict]) -> list[dict]:
    return [{
        "id": p["ean"], "brand_id": p["brand_id"], "name": p["name"], "sku": None,
        "category": p["category"], "list_price": p["avg_sale_price_eur"],
        "cost_price": p["avg_purchase_price_eur"], "ref": p["ean"],
    } for p in products]


def main() -> dict:
    fx = CurrencyConverter.load()

    print("· products + brand dictionary …")
    prod = load_products()
    bd = prod["brand_dict"]
    products = prod["products"]
    product_by_ean = {p["ean"]: p for p in products}

    print("· reconstructing orders + partners …")
    od = load_orders(fx, product_by_ean)
    sales_df, purch_df = od["_sales_df"], od["_purch_df"]

    now = max(o["order_date"] for o in od["sale_orders"] if o["order_date"])
    print(f"  data 'now' = {now}")

    print("· retailer scan + offers …")
    retail = load_retailer(bd, fx)
    offers = load_offers(bd, fx)["offers"]

    print("· deriving signals + synthesizing stock/teams …")
    demand = derive_demand(sales_df, product_by_ean, now)
    supply = (
        supply_from_purchases(purch_df, product_by_ean, now)
        + supply_from_offers(offers, _brand_dominant_buyer(purch_df, product_by_ean), od["roster"], now)
    )
    demand_brands = {d["brand_id"] for d in demand}
    supply_brands = {s["brand_id"] for s in supply}
    inventory = synth_inventory(products, demand_brands, supply_brands)
    traders = assign_teams(od["roster"])

    tables = {
        "traders": traders,
        "brands": bd.to_brand_rows(),
        "brand_aliases": bd.to_alias_rows(),
        "partners": od["partners"],
        "products": _products_rows(products),
        "inventory": inventory,
        "sale_orders": od["sale_orders"],
        "sale_order_lines": od["sale_order_lines"],
        "purchase_orders": od["purchase_orders"],
        "purchase_order_lines": od["purchase_order_lines"],
        "demand_signals": demand,
        "supply_signals": supply,
        "retailer_prices": retail["rows"],
    }

    print("· writing atlas.db …")
    conn = sqlite3.connect(PATHS.db_path)
    try:
        conn.executescript(SCHEMA)
        counts = {}
        for table, cols in COLUMNS.items():
            rows = tables.get(table, [])
            ph = ", ".join("?" for _ in cols)
            conn.executemany(
                f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({ph})",
                [[r.get(c) for c in cols] for r in rows],
            )
            counts[table] = len(rows)
        conn.commit()
    finally:
        conn.close()

    print(f"\n=== atlas.db built (real data) → {PATHS.db_path} ===")
    for t, n in counts.items():
        print(f"  {t:22s} {n}")
    return counts


if __name__ == "__main__":
    main()
