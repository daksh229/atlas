"""
matching.py — the BF Atlas matching engine (spec §6).

For each brand it asks "which signals fired recently?" and detects overlap:
  - demand  : a client wants the brand (demand_signals)
  - supply  : we can source the brand (supply_signals, incl. manual offers)
  - stock   : we hold live inventory of the brand (inventory)
  - retail  : a retailer lists the brand at a price (retailer_prices)

When signals overlap on one brand inside a recency window, that is an opportunity.
This module produces the raw, UN-routed match rows; alerts.py turns them into
typed, quality-controlled, routed alerts.

Everything joins on brand_id (never a string) so the brand dictionary guarantees
"YSL" and "Saint Laurent" land on the same brand.
"""

import pandas as pd

from app.core.database import run_query

# "today" is derived from the real data: the most recent signal we hold. The
# window is wide enough to span the derived-signal horizon (see synth/derive.py).
WINDOW_DAYS = 180  # signals older than this don't count as "recent"
_FALLBACK_NOW = "2026-06-16"


def _now() -> str:
    """The latest signal date in the DB — keeps 'recent' anchored to real data."""
    df = run_query(
        "SELECT MAX(d) AS now FROM ("
        "  SELECT MAX(fired_at) AS d FROM demand_signals"
        "  UNION ALL SELECT MAX(fired_at) FROM supply_signals)"
    )
    val = None if df.empty else df.iloc[0]["now"]
    return str(val)[:10] if val else _FALLBACK_NOW


def demand_supply_matches() -> pd.DataFrame:
    """Every recent demand × recent supply on the same brand with positive margin.

    Returns one row per (demand, supply) pair, carrying both owning traders so the
    router can notify the right people (and mask the counterparty).
    """
    now = _now()
    return run_query(
        f"""
        SELECT b.id AS brand_id, b.canonical_name AS brand,
               d.id AS demand_id, d.trader_id AS demand_trader, d.partner_id AS client_id,
               d.target_price AS sell_price, d.wanted_qty, d.fired_at AS demand_seen,
               s.id AS supply_id, s.trader_id AS supply_trader, s.partner_id AS supplier_id,
               s.offer_price AS buy_price, s.available_qty, s.fired_at AS supply_seen,
               s.source AS supply_source,
               ROUND(d.target_price - s.offer_price, 2) AS margin_per_unit,
               MIN(d.wanted_qty, s.available_qty) AS match_qty,
               ROUND((d.target_price - s.offer_price)
                     * MIN(d.wanted_qty, s.available_qty), 2) AS margin_value
        FROM demand_signals d
        JOIN supply_signals s ON s.brand_id = d.brand_id
        JOIN brands b ON b.id = d.brand_id
        WHERE d.target_price > s.offer_price
          AND d.fired_at >= date('{now}', '-{WINDOW_DAYS} days')
          AND s.fired_at >= date('{now}', '-{WINDOW_DAYS} days')
        ORDER BY margin_value DESC
        """)


def external_market_windows() -> pd.DataFrame:
    """Retailer lists a brand above a price we can supply at → a market window.

    Routed to the trader who can supply (owns the supply signal).
    """
    now = _now()
    return run_query(
        f"""
        SELECT b.id AS brand_id, b.canonical_name AS brand,
               r.retailer, r.product_name, r.price AS retail_price, r.stock_status,
               s.trader_id AS supply_trader, s.offer_price AS our_buy_price,
               ROUND(r.price - s.offer_price, 2) AS headroom_per_unit
        FROM retailer_prices r
        JOIN supply_signals s ON s.brand_id = r.brand_id
        JOIN brands b ON b.id = r.brand_id
        WHERE r.brand_id IS NOT NULL
          AND r.price > s.offer_price
          AND s.fired_at >= date('{now}', '-{WINDOW_DAYS} days')
        ORDER BY headroom_per_unit DESC
        """)


def stock_matches() -> pd.DataFrame:
    """We hold live inventory of a brand that a client wants → fastest deal."""
    now = _now()
    return run_query(
        f"""
        SELECT b.id AS brand_id, b.canonical_name AS brand,
               p.name AS product, SUM(i.qty_available) AS qty_available,
               d.trader_id AS demand_trader, d.partner_id AS client_id,
               d.target_price, d.wanted_qty
        FROM inventory i
        JOIN products p ON p.id = i.product_id
        JOIN brands b ON b.id = p.brand_id
        JOIN demand_signals d ON d.brand_id = b.id
        WHERE i.qty_available > 0
          AND d.fired_at >= date('{now}', '-{WINDOW_DAYS} days')
        GROUP BY p.id, d.id
        HAVING qty_available >= 100
        ORDER BY qty_available DESC
        """)


def reorder_due(cadence_tolerance_days: int = 7) -> pd.DataFrame:
    """Clients overdue for a repeat order, inferred from their own order cadence.

    For each (client, brand) with >= 2 past orders, estimate the typical gap and
    flag it if the time since the last order exceeds that gap.
    """
    orders = run_query(
        """SELECT so.partner_id AS client_id, sol.brand_id, b.canonical_name AS brand,
                  so.trader_id, p.name AS client, so.order_date
           FROM sale_orders so
           JOIN sale_order_lines sol ON sol.order_id = so.id
           JOIN brands b ON b.id = sol.brand_id
           JOIN partners p ON p.id = so.partner_id
           WHERE so.state != 'cancel'""")
    if orders.empty:
        return pd.DataFrame()

    orders["order_date"] = pd.to_datetime(orders["order_date"])
    now = pd.Timestamp(_now())
    rows = []
    for (client_id, brand_id), g in orders.groupby(["client_id", "brand_id"]):
        dates = g["order_date"].sort_values()
        if len(dates) < 2:
            continue
        gaps = dates.diff().dropna().dt.days
        cadence = float(gaps.mean())
        days_since = (now - dates.max()).days
        if cadence > 0 and days_since >= cadence - cadence_tolerance_days:
            r = g.iloc[0]
            rows.append({
                "brand_id": brand_id, "brand": r["brand"], "client_id": client_id,
                "client": r["client"], "demand_trader": r["trader_id"],
                "cadence_days": round(cadence), "days_since_last": int(days_since),
                "last_order": dates.max().strftime("%Y-%m-%d"), "orders": len(dates),
            })
    return pd.DataFrame(rows)
