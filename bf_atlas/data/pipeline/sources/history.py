"""
history.py — ingest Sales and Purchase order history (the big Odoo exports).

Two jobs:
  1. Data-quality fix (the highest-impact one): these are FLATTENED exports —
     Salesperson/Customer/Order Date (sales) and Buyer/Vendor/Confirmation Date
     (purchases) appear ONLY on the first line of each order and are blank on
     every continuation line. We forward-fill them; without this ~90% of the
     trader/account attribution is silently lost.
  2. Per-EAN intelligence for the offer evaluator and brand views:
       - who bought it (buyer traders + vendors)        → potential SOURCES
       - who sold it (salesperson traders + customers)  → potential SELL-SIDE
       - EUR price stats (min/avg buy, avg/max sell) from real lines
       - recency (last buy/sell date)

Currency is normalized to EUR per line at the row's own date, vectorized by
unique (currency, date) so it stays fast on ~110k rows.
"""

from __future__ import annotations

import re
import warnings

import pandas as pd

from data.pipeline.config import PATHS
from data.pipeline.normalize.clean import clean_ean
from data.pipeline.normalize.currency import CurrencyConverter

_SLUG = re.compile(r"[^a-z0-9]+")

SALES_COLS = {
    "product": "Order Lines/Product",
    "ean": "Order Lines/Barcode",
    "qty": "Order Lines/Product Qty",
    "price": "Order Lines/Unit Price",
    "currency": "Order Lines/Currency",
    "trader": "Salesperson",
    "date": "Order Date",
    "account": "Customer",
}
PURCH_COLS = {
    "product": "Order Lines/Product",
    "ean": "Order Lines/Product/Barcode",
    "qty": "Order Lines/Quantity",
    "price": "Order Lines/Unit Price",
    "currency": "Order Lines/Currency",
    "trader": "Buyer",
    "date": "Confirmation Date",
    "account": "Vendor",
}


def trader_id_for(name: str) -> str:
    return "t-" + _SLUG.sub("-", str(name).strip().lower()).strip("-")


def _add_eur(df: pd.DataFrame, fx: CurrencyConverter) -> pd.Series:
    """Vectorized EUR unit price: one ECB lookup per unique (currency, date)."""
    keys = df[["_currency", "_date"]].drop_duplicates().copy()
    keys["_factor"] = [
        fx.to_eur(1.0, ccy, date).amount_eur          # EUR per 1 unit of currency
        for ccy, date in keys[["_currency", "_date"]].itertuples(index=False)
    ]
    merged = df.merge(keys, on=["_currency", "_date"], how="left")
    return (merged["_price"].to_numpy() * merged["_factor"].to_numpy()).round(4)


def _read(path: str, cols: dict, fx: CurrencyConverter) -> pd.DataFrame:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        df = pd.read_excel(path, dtype={cols["ean"]: "string"})

    # (1) THE FIX: forward-fill the flattened header columns down each order block.
    for k in ("trader", "date", "account"):
        df[cols[k]] = df[cols[k]].ffill()

    out = pd.DataFrame({
        "_ean": df[cols["ean"]].map(clean_ean),
        "_qty": pd.to_numeric(df[cols["qty"]], errors="coerce"),
        "_price": pd.to_numeric(df[cols["price"]], errors="coerce"),
        "_currency": df[cols["currency"]].astype("string").str.upper(),
        "_trader": df[cols["trader"]].astype("string"),
        "_date": df[cols["date"]].astype("string").str.slice(0, 10),
        "_account": df[cols["account"]].astype("string"),
    })
    out = out[out["_ean"].notna() & out["_price"].notna()].copy()
    out["_price_eur"] = _add_eur(out, fx)
    out["_trader_id"] = out["_trader"].map(lambda n: trader_id_for(n) if pd.notna(n) else None)
    return out


def _uniq_sorted(s: pd.Series) -> list:
    return sorted({v for v in s.dropna().tolist()})


def _per_ean(df: pd.DataFrame, side: str) -> dict[str, dict]:
    """Aggregate to per-EAN in a single groupby pass (no per-group rescans)."""
    stats = df.groupby("_ean").agg(
        _min=("_price_eur", "min"),
        _mean=("_price_eur", "mean"),
        _max=("_price_eur", "max"),
        _count=("_price_eur", "count"),
        _last=("_date", "max"),
        _traders=("_trader", _uniq_sorted),
        _accounts=("_account", _uniq_sorted),
    )
    agg: dict[str, dict] = {}
    for ean, row in stats.iterrows():
        agg[ean] = {
            f"{side}_min_eur": round(float(row["_min"]), 2),
            f"{side}_avg_eur": round(float(row["_mean"]), 2),
            f"{side}_max_eur": round(float(row["_max"]), 2),
            f"{side}_lines": int(row["_count"]),
            f"{side}_traders": row["_traders"],
            f"{side}_accounts": row["_accounts"],
            f"{side}_last_date": row["_last"],
        }
    return agg


def load_history(fx: CurrencyConverter | None = None) -> dict:
    fx = fx or CurrencyConverter.load()
    sales = _read(PATHS.sales, SALES_COLS, fx)
    purch = _read(PATHS.purchases, PURCH_COLS, fx)

    sell = _per_ean(sales, "sell")
    buy = _per_ean(purch, "buy")

    # Trader roster = union of everyone who bought or sold (the ~24 real traders).
    names = sorted(set(sales["_trader"].dropna().unique()) | set(purch["_trader"].dropna().unique()))
    roster = [{"id": trader_id_for(n), "name": n} for n in names]

    report = {
        "sales_lines": len(sales),
        "purchase_lines": len(purch),
        "sales_attribution_rate": round(sales["_trader"].notna().mean(), 4),
        "purchase_attribution_rate": round(purch["_trader"].notna().mean(), 4),
        "eans_with_sell_history": len(sell),
        "eans_with_buy_history": len(buy),
        "traders": len(roster),
    }
    return {"sell_by_ean": sell, "buy_by_ean": buy, "roster": roster, "report": report}
