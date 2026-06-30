"""
orders.py — reconstruct Orders, Order Lines, and Partners from the flattened
Odoo exports (the real Sales/Purchase history).

The exports are line-level: each order's header (Salesperson/Customer/Date, or
Buyer/Vendor/Date) appears only on the FIRST line of the order and is blank on
continuation lines. We:
  1. detect order boundaries from those header rows (before ffilling),
  2. forward-fill the header down each block,
  3. reconstruct one order per block with real dates + EUR totals,
  4. derive partners (customers from sales, suppliers from purchases) and assign
     each an owner trader = the trader who handled it most.

Output feeds the existing atlas.db schema unchanged, so the application's
services and screens run on real data.
"""

from __future__ import annotations

import re
import warnings

import pandas as pd

from data.pipeline.config import PATHS
from data.pipeline.normalize.clean import clean_ean
from data.pipeline.normalize.currency import CurrencyConverter
from data.pipeline.sources.history import SALES_COLS, PURCH_COLS, trader_id_for, _add_eur

_SLUG = re.compile(r"[^a-z0-9]+")


def partner_id_for(name: str) -> str:
    return "p-" + _SLUG.sub("-", str(name).strip().lower()).strip("-")


def _read_lines(path: str, cols: dict, fx: CurrencyConverter) -> pd.DataFrame:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        df = pd.read_excel(path, dtype={cols["ean"]: "string"})

    # Order boundary = a row that still carries its header (before ffill).
    header = df[cols["trader"]].notna()
    order_seq = header.cumsum()

    out = pd.DataFrame({
        "_order_seq": order_seq.to_numpy(),
        "_ean": df[cols["ean"]].map(clean_ean),
        "_qty": pd.to_numeric(df[cols["qty"]], errors="coerce"),
        "_price": pd.to_numeric(df[cols["price"]], errors="coerce"),
        "_currency": df[cols["currency"]].astype("string").str.upper(),
        # ffill the header columns down each order block
        "_trader": df[cols["trader"]].ffill().astype("string"),
        "_date": df[cols["date"]].ffill().astype("string").str.slice(0, 10),
        "_account": df[cols["account"]].ffill().astype("string"),
    })
    out = out[out["_price"].notna()].copy()
    out["_price_eur"] = _add_eur(out, fx)
    out["_qty"] = out["_qty"].fillna(0)
    out["_subtotal_eur"] = (out["_price_eur"] * out["_qty"]).round(2)
    out["_trader_id"] = out["_trader"].map(lambda n: trader_id_for(n) if pd.notna(n) else None)
    out["_partner_id"] = out["_account"].map(lambda n: partner_id_for(n) if pd.notna(n) else None)
    return out


def _orders_and_lines(df: pd.DataFrame, kind: str, product_by_ean: dict) -> tuple[list, list]:
    """kind = 'sale' | 'purchase'. Returns (orders, lines) row dicts."""
    prefix = "SO" if kind == "sale" else "PO"
    orders, lines = [], []
    grouped = df.groupby("_order_seq", sort=True)
    for seq, g in grouped:
        first = g.iloc[0]
        oid = f"{prefix}-{int(seq):06d}"
        orders.append({
            "id": oid,
            "ref": oid,
            "partner_id": first["_partner_id"],
            "trader_id": first["_trader_id"],
            "order_date": first["_date"],
            "state": "done",
            "amount_total": round(float(g["_subtotal_eur"].sum()), 2),
            "margin_amount": None,
        })
        eans = g["_ean"].tolist()
        qtys = g["_qty"].tolist()
        prices = g["_price_eur"].tolist()
        subs = g["_subtotal_eur"].tolist()
        for j, (ean, qty, price, sub) in enumerate(zip(eans, qtys, prices, subs)):
            brand_id = (product_by_ean.get(ean) or {}).get("brand_id") if ean else None
            lines.append({
                "id": f"{oid}-{j}",
                "order_id": oid,
                "product_id": ean,
                "brand_id": brand_id,
                "qty": int(qty) if pd.notna(qty) else 0,
                "unit_price": None if pd.isna(price) else float(price),
                "subtotal": None if pd.isna(sub) else float(sub),
            })
    return orders, lines


def _derive_partners(sales: pd.DataFrame, purch: pd.DataFrame) -> list[dict]:
    """Customers from sales, suppliers from purchases; owner = dominant trader."""
    partners: dict[str, dict] = {}

    def ingest(df: pd.DataFrame, is_customer: int, is_supplier: int):
        sub = df[df["_partner_id"].notna()]
        # owner trader = the trader who handled this partner on the most lines
        owner = (
            sub.groupby("_partner_id")["_trader_id"]
            .agg(lambda s: s.dropna().mode().iat[0] if not s.dropna().empty else None)
        )
        names = sub.groupby("_partner_id")["_account"].first()
        for pid in sub["_partner_id"].unique():
            rec = partners.setdefault(pid, {
                "id": pid, "name": names.get(pid), "is_customer": 0, "is_supplier": 0,
                "owner_trader_id": owner.get(pid), "country": None, "ref": None, "email": None,
            })
            rec["is_customer"] |= is_customer
            rec["is_supplier"] |= is_supplier
            if rec["owner_trader_id"] is None:
                rec["owner_trader_id"] = owner.get(pid)

    ingest(sales, 1, 0)
    ingest(purch, 0, 1)
    return list(partners.values())


def load_orders(fx: CurrencyConverter, product_by_ean: dict) -> dict:
    """Reconstruct everything order/partner/trader from the real exports."""
    sales = _read_lines(PATHS.sales, SALES_COLS, fx)
    purch = _read_lines(PATHS.purchases, PURCH_COLS, fx)

    so, sol = _orders_and_lines(sales, "sale", product_by_ean)
    po, pol = _orders_and_lines(purch, "purchase", product_by_ean)
    partners = _derive_partners(sales, purch)

    names = sorted(set(sales["_trader"].dropna().unique()) | set(purch["_trader"].dropna().unique()))
    roster = [{"id": trader_id_for(n), "name": n} for n in names]

    report = {
        "sale_orders": len(so), "sale_order_lines": len(sol),
        "purchase_orders": len(po), "purchase_order_lines": len(pol),
        "partners": len(partners),
        "customers": sum(1 for p in partners if p["is_customer"]),
        "suppliers": sum(1 for p in partners if p["is_supplier"]),
        "traders": len(roster),
    }
    return {
        "sale_orders": so, "sale_order_lines": sol,
        "purchase_orders": po, "purchase_order_lines": pol,
        "partners": partners, "roster": roster,
        "_sales_df": sales, "_purch_df": purch,  # reused for signal derivation
        "report": report,
    }
