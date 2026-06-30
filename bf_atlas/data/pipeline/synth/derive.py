"""
derive.py — turn real history into the SIGNALS the matching engine needs, and
synthesize only what the Odoo exports don't contain (live stock, team structure).

Data provenance (matches the spec's "reason about the uncertain sources"):
  - DEMAND   — DERIVED from real sales: a client actively buying a brand is
               standing demand at the price they pay. source='derived_sales'.
  - SUPPLY   — REAL: from purchase history (what a vendor sourced us) and from the
               three real supplier offer files. source='purchase_history'|'email_offer'.
  - STOCK    — SYNTHESIZED (exports have no live stock), seeded from real products
               that have both demand and supply so Stock Match can fire. Flagged.
  - TEAMS    — SYNTHESIZED: the 24 real traders deterministically split into 5 teams.

All money is already EUR. "Recent" is measured against a NOW derived from the data.
"""

from __future__ import annotations

import pandas as pd

# Active-signal window: how far back from NOW a transaction still counts as a
# live signal. Generous because the sample spans ~a year.
WINDOW_DAYS = 150


def _with_brand(df: pd.DataFrame, product_by_ean: dict) -> pd.DataFrame:
    df = df.copy()
    df["_brand_id"] = df["_ean"].map(
        lambda e: (product_by_ean.get(e) or {}).get("brand_id") if e else None
    )
    return df


def _cutoff(now: str) -> str:
    return (pd.Timestamp(now) - pd.Timedelta(days=WINDOW_DAYS)).strftime("%Y-%m-%d")


def _mode(s: pd.Series):
    s = s.dropna()
    return s.mode().iat[0] if not s.empty else None


def derive_demand(sales_df, product_by_ean, now: str) -> list[dict]:
    """One demand signal per (active client, brand): they buy it, at their price."""
    df = _with_brand(sales_df, product_by_ean)
    df = df[df["_brand_id"].notna() & df["_partner_id"].notna()]
    cut = _cutoff(now)
    agg = df.groupby(["_partner_id", "_brand_id"]).agg(
        target=("_price_eur", "mean"), qty=("_qty", "mean"),
        last=("_date", "max"), trader=("_trader_id", _mode),
    )
    agg = agg[agg["last"] >= cut]
    rows = []
    for i, ((pid, bid), r) in enumerate(agg.iterrows()):
        rows.append({
            "id": f"dem-{i:06d}", "brand_id": bid, "partner_id": pid,
            "trader_id": r["trader"], "target_price": round(float(r["target"]), 2),
            "wanted_qty": max(int(r["qty"]), 1), "fired_at": r["last"],
            "source": "derived_sales",
        })
    return rows


def supply_from_purchases(purch_df, product_by_ean, now: str) -> list[dict]:
    """Supply signals from real purchase history: a vendor can source this brand."""
    df = _with_brand(purch_df, product_by_ean)
    df = df[df["_brand_id"].notna() & df["_partner_id"].notna()]
    cut = _cutoff(now)
    agg = df.groupby(["_partner_id", "_brand_id"]).agg(
        price=("_price_eur", "mean"), qty=("_qty", "mean"),
        last=("_date", "max"), trader=("_trader_id", _mode),
    )
    agg = agg[agg["last"] >= cut]
    rows = []
    for i, ((pid, bid), r) in enumerate(agg.iterrows()):
        rows.append({
            "id": f"sup-{i:06d}", "brand_id": bid, "partner_id": pid,
            "trader_id": r["trader"], "offer_price": round(float(r["price"]), 2),
            "available_qty": max(int(r["qty"]), 1), "fired_at": r["last"],
            "source": "purchase_history",
        })
    return rows


def supply_from_offers(offers: list[dict], brand_dominant_buyer: dict, roster: list[dict],
                       now: str) -> list[dict]:
    """Supply signals from the three real offer files, routed to the trader who
    most works that brand (so the offer reaches the right person)."""
    fallback = [t["id"] for t in roster]
    rows = []
    for i, o in enumerate(offers):
        bid = o.get("brand_id")
        if not bid or o.get("unit_price_eur") is None:
            continue
        trader = brand_dominant_buyer.get(bid) or (fallback[i % len(fallback)] if fallback else None)
        rows.append({
            "id": f"off-{i:06d}", "brand_id": bid, "partner_id": None,
            "trader_id": trader, "offer_price": round(float(o["unit_price_eur"]), 2),
            "available_qty": int(o.get("qty") or 1),
            # A parsed offer "fires" when we receive it (now), not on its print date.
            "fired_at": now, "source": "email_offer",
        })
    return rows


def synth_inventory(products: list[dict], demand_brands: set, supply_brands: set,
                    target: int = 400) -> list[dict]:
    """Seed live stock for products whose brand has BOTH demand and supply, so
    Stock Match has something to fire on. Deterministic (no RNG)."""
    eligible = [
        p for p in products
        if p.get("brand_id") in demand_brands and p.get("brand_id") in supply_brands
    ]
    eligible.sort(key=lambda p: p["ean"])  # stable order
    rows = []
    for i, p in enumerate(eligible[:target]):
        qty = 120 + (hash(p["ean"]) % 680)  # 120..799, deterministic per EAN
        rows.append({
            "id": f"inv-{i:06d}", "product_id": p["ean"], "warehouse": "SYNTH",
            "qty_on_hand": qty, "qty_reserved": 0, "qty_available": qty,
            "reorder_min": 50,
        })
    return rows


def assign_teams(roster: list[dict], n_teams: int = 5) -> list[dict]:
    """Deterministically split the traders into N teams; all are traders.
    One manager is appointed (sees all) to exercise the masking model."""
    teams = [f"Team {chr(ord('A') + i)}" for i in range(n_teams)]
    out = []
    for i, t in enumerate(sorted(roster, key=lambda r: r["id"])):
        out.append({
            "id": t["id"], "name": t["name"],
            "team": teams[i % n_teams],
            "role": "manager" if i == 0 else "trader",
        })
    return out
