"""
brands.py — brand dictionary + brand intelligence (spec §7 / §9).

All brand logic joins on brand_id (never a raw string), so aliases can never
split one brand into many. `resolve()` maps any surface form to a canonical brand
using the brands + brand_aliases tables — the same dictionary the data pipeline
built.

Brand Maps:
  - brands_i_can_sell : brands the trader's CLIENTS want (their demand signals)
  - brands_i_can_buy  : brands the trader's SUPPLIERS offer (their supply signals)

Brand Intelligence view: the full picture for one brand — which colleagues buy /
sell it, which clients want it (access-masked), which retailers carry it, and the
best historical selling price.
"""

import re
import unicodedata

import pandas as pd

from app.core.database import run_query
from app.core.security import Session, mask_partner


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(c for c in text if not unicodedata.combining(c)).lower()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", text)).strip()


def surface_map() -> dict[str, tuple[str, str]]:
    """normalized surface form → (brand_id, canonical_name) for every name + alias."""
    out: dict[str, tuple[str, str]] = {}
    canon = run_query("SELECT id AS brand_id, canonical_name FROM brands")
    for _, r in canon.iterrows():
        out[_norm(r["canonical_name"])] = (r["brand_id"], r["canonical_name"])
    al = run_query(
        """SELECT a.brand_id, a.alias, b.canonical_name
           FROM brand_aliases a JOIN brands b ON b.id = a.brand_id""")
    for _, r in al.iterrows():
        out[_norm(r["alias"])] = (r["brand_id"], r["canonical_name"])
    return out


def resolve(surface: str) -> str | None:
    """Surface form (canonical or alias) → brand_id, or None if unknown."""
    hit = surface_map().get(_norm(surface))
    return hit[0] if hit else None


def catalog() -> pd.DataFrame:
    """Company-wide brand list (no internal data) — backs the Brand Catalog."""
    return run_query(
        """SELECT b.canonical_name AS brand, b.category,
                  COUNT(DISTINCT p.id) AS products,
                  GROUP_CONCAT(DISTINCT a.alias) AS aliases
           FROM brands b
           LEFT JOIN products p ON p.brand_id = b.id
           LEFT JOIN brand_aliases a ON a.brand_id = b.id
           GROUP BY b.id ORDER BY b.canonical_name""")


def brands_i_can_sell(session: Session) -> pd.DataFrame:
    """Brands where THIS trader's clients show demand."""
    return run_query(
        """SELECT b.id AS brand_id, b.canonical_name AS brand, b.category,
                  COUNT(DISTINCT d.partner_id) AS clients,
                  ROUND(AVG(d.target_price), 2) AS avg_target_price,
                  SUM(d.wanted_qty) AS total_wanted
           FROM demand_signals d JOIN brands b ON b.id = d.brand_id
           WHERE d.trader_id = ?
           GROUP BY b.id ORDER BY total_wanted DESC""",
        (session.trader_id,))


def brands_i_can_buy(session: Session) -> pd.DataFrame:
    """Brands THIS trader's suppliers can source."""
    return run_query(
        """SELECT b.id AS brand_id, b.canonical_name AS brand, b.category,
                  COUNT(DISTINCT s.id) AS offers,
                  MIN(s.offer_price) AS best_buy_price,
                  SUM(s.available_qty) AS total_available
           FROM supply_signals s JOIN brands b ON b.id = s.brand_id
           WHERE s.trader_id = ?
           GROUP BY b.id ORDER BY b.canonical_name""",
        (session.trader_id,))


def brand_detail(session: Session, brand_id: str) -> dict:
    """Full intelligence for one brand, with access masking applied server-side."""
    head = run_query("SELECT id, canonical_name, category FROM brands WHERE id = ?",
                     (brand_id,))
    if head.empty:
        return {}
    name = head.iloc[0]["canonical_name"]

    # Colleagues active on this brand (trader identities are allowed to show).
    colleagues = run_query(
        """SELECT t.name AS colleague, t.team,
                  SUM(CASE WHEN x.kind='demand' THEN 1 ELSE 0 END) AS demand_signals,
                  SUM(CASE WHEN x.kind='supply' THEN 1 ELSE 0 END) AS supply_signals
           FROM (
             SELECT trader_id, 'demand' AS kind FROM demand_signals WHERE brand_id = ?
             UNION ALL
             SELECT trader_id, 'supply' AS kind FROM supply_signals WHERE brand_id = ?
           ) x JOIN traders t ON t.id = x.trader_id
           GROUP BY t.id ORDER BY t.name""",
        (brand_id, brand_id))

    # Clients wanting it — names masked unless owned by the session trader.
    dem = run_query(
        """SELECT p.name AS client, d.trader_id AS owner, d.target_price,
                  d.wanted_qty, d.fired_at
           FROM demand_signals d JOIN partners p ON p.id = d.partner_id
           WHERE d.brand_id = ? ORDER BY d.target_price DESC""",
        (brand_id,))
    demands = [
        {"client": mask_partner(session, r["owner"], r["client"]),
         "target_price": r["target_price"], "wanted_qty": int(r["wanted_qty"]),
         "fired_at": r["fired_at"], "mine": r["owner"] == session.trader_id}
        for _, r in dem.iterrows()
    ]

    # Suppliers offering it — names masked unless owned.
    sup = run_query(
        """SELECT p.name AS supplier, s.trader_id AS owner, s.offer_price,
                  s.available_qty, s.fired_at, s.source
           FROM supply_signals s LEFT JOIN partners p ON p.id = s.partner_id
           WHERE s.brand_id = ? ORDER BY s.offer_price ASC""",
        (brand_id,))
    offers = [
        {"supplier": mask_partner(session, r["owner"],
                                  r["supplier"] if r["source"] != "manual_offer"
                                  else "Manual offer"),
         "offer_price": r["offer_price"], "available_qty": int(r["available_qty"]),
         "fired_at": r["fired_at"], "mine": r["owner"] == session.trader_id}
        for _, r in sup.iterrows()
    ]

    retailers = run_query(
        """SELECT retailer, product_name, price, stock_status, scanned_at
           FROM retailer_prices WHERE brand_id = ? ORDER BY price ASC""",
        (brand_id,))

    best_hist = run_query(
        """SELECT MAX(sol.unit_price) AS best_sell_price
           FROM sale_order_lines sol JOIN sale_orders so ON so.id = sol.order_id
           WHERE sol.brand_id = ? AND so.state != 'cancel'""",
        (brand_id,))
    best_price = best_hist.iloc[0]["best_sell_price"] if not best_hist.empty else None

    return {
        "brand_id": brand_id, "brand": name, "category": head.iloc[0]["category"],
        "best_historical_sell_price": float(best_price) if pd.notna(best_price) else None,
        "colleagues": colleagues, "demands": demands, "offers": offers,
        "retailers": retailers,
    }
