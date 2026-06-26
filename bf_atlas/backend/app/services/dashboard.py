"""Dashboard — a slim 'My View' overview, scoped to the session trader (§9)."""

from app.core.database import run_query, scalar
from app.core.security import Session


def kpis(session: Session) -> dict:
    tid = session.trader_id
    clients = scalar("SELECT COUNT(*) FROM partners WHERE is_customer=1 AND owner_trader_id=?", (tid,))
    suppliers = scalar("SELECT COUNT(*) FROM partners WHERE is_supplier=1 AND owner_trader_id=?", (tid,))
    open_demand = scalar("SELECT COUNT(*) FROM demand_signals WHERE trader_id=?", (tid,))
    revenue = scalar(
        """SELECT COALESCE(SUM(amount_total),0) FROM sale_orders
           WHERE trader_id=? AND state!='cancel'""", (tid,))
    return {
        "clients": int(clients or 0), "suppliers": int(suppliers or 0),
        "open_demand_signals": int(open_demand or 0), "revenue_total": float(revenue or 0),
    }


def my_brands(session: Session):
    """Top brands the trader is active on (by combined demand+supply signal count)."""
    return run_query(
        """SELECT b.canonical_name AS brand, b.category,
                  COUNT(DISTINCT d.id) AS demand, COUNT(DISTINCT s.id) AS supply
           FROM brands b
           LEFT JOIN demand_signals d ON d.brand_id=b.id AND d.trader_id=?
           LEFT JOIN supply_signals s ON s.brand_id=b.id AND s.trader_id=?
           GROUP BY b.id
           HAVING demand>0 OR supply>0
           ORDER BY (demand+supply) DESC LIMIT 10""",
        (session.trader_id, session.trader_id))
