"""
radar.py — Retailer Radar (spec §5 / §8 Market Activity).

Reads PERSISTED retailer_prices (populated by the data pipeline; in production a
scheduled scraper writes here). Every row is matched to our catalogue via brand_id
through the brand dictionary — so retailer spellings can't fragment a brand. Rows
whose brand is unknown are FLAGGED, never force-matched.
"""

import pandas as pd

from app.core.database import run_query


def radar() -> pd.DataFrame:
    """Retailer rows joined to our best supply price for the same brand."""
    return run_query(
        """SELECT r.retailer, r.brand_surface,
                  b.canonical_name AS brand, r.product_name, r.price AS retail_price,
                  r.stock_status, r.scanned_at, r.is_mock,
                  (SELECT MIN(s.offer_price) FROM supply_signals s
                   WHERE s.brand_id = r.brand_id) AS our_buy_price,
                  (r.brand_id IS NULL) AS unknown_brand
           FROM retailer_prices r
           LEFT JOIN brands b ON b.id = r.brand_id
           ORDER BY r.scanned_at DESC, r.retailer""")


def compare_to_catalog() -> pd.DataFrame:
    df = radar()
    rows = []
    for _, r in df.iterrows():
        our = r["our_buy_price"]
        headroom = round(r["retail_price"] - our, 2) if pd.notna(our) else None
        rows.append({
            "retailer": r["retailer"],
            "brand": r["brand"] if pd.notna(r["brand"]) else f"⚠ {r['brand_surface']} (unknown)",
            "product": r["product_name"], "retail_price": r["retail_price"],
            "our_buy_price": float(our) if pd.notna(our) else None,
            "headroom_per_unit": headroom, "stock": r["stock_status"],
            "scanned_at": r["scanned_at"], "is_mock": bool(r["is_mock"]),
            "signal": ("🟢 Market window" if headroom is not None and headroom > 0
                       else "🔴 No headroom" if headroom is not None
                       else "—"),
        })
    return pd.DataFrame(rows)
