"""
relationships.py — My Clients / My Suppliers (spec §8 "My Relationships").

Strictly scoped to the session trader's OWN accounts (§9). A trader never sees
another trader's partners here.
"""

import pandas as pd

from app.core.database import run_query
from app.core.security import Session


def my_clients(session: Session) -> pd.DataFrame:
    return run_query(
        """SELECT p.id, p.name AS client, p.country, p.email,
                  COUNT(DISTINCT so.id) AS orders,
                  COALESCE(SUM(CASE WHEN so.state!='cancel' THEN so.amount_total END),0) AS lifetime_value,
                  MAX(so.order_date) AS last_order,
                  COUNT(DISTINCT d.id) AS open_demands
           FROM partners p
           LEFT JOIN sale_orders so ON so.partner_id = p.id
           LEFT JOIN demand_signals d ON d.partner_id = p.id
           WHERE p.is_customer = 1 AND p.owner_trader_id = ?
           GROUP BY p.id ORDER BY lifetime_value DESC""",
        (session.trader_id,))


def my_suppliers(session: Session) -> pd.DataFrame:
    return run_query(
        """SELECT p.id, p.name AS supplier, p.country, p.email,
                  COUNT(DISTINCT po.id) AS purchase_orders,
                  COALESCE(SUM(po.amount_total),0) AS total_purchased,
                  COUNT(DISTINCT s.id) AS active_offers,
                  MIN(s.offer_price) AS best_offer
           FROM partners p
           LEFT JOIN purchase_orders po ON po.partner_id = p.id
           LEFT JOIN supply_signals s ON s.partner_id = p.id
           WHERE p.is_supplier = 1 AND p.owner_trader_id = ?
           GROUP BY p.id ORDER BY total_purchased DESC""",
        (session.trader_id,))
