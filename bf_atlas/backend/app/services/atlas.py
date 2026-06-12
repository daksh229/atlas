"""
atlas.py — BF Atlas Opportunity Engine (cross-match) + brand intelligence.

An opportunity exists when a brand we can SOURCE (brand_offers) is WANTED by a
client (brand_demands) at a higher price — a positive per-unit margin. Alerts and
brand pages are views on top. The 6 alert types are illustrative (the real set is
in BF's spec).
"""

import pandas as pd

from app.core.database import region_clause, run_query

STALE_DAYS = 14
RECENT_DAYS = 3
NOW = "2026-06-11"  # fixed demo "today" (matches data/init_atlas.py)


def opportunities(region=None) -> pd.DataFrame:
    rclause, rparams = region_clause(region, column="d.region")
    return run_query(
        f"""
        SELECT o.brand, o.category, s.name AS supplier,
               o.region AS supply_region, d.region AS demand_region,
               t.name AS trader, cc.company_name AS client,
               o.offer_price AS buy_price, d.target_price AS sell_price,
               ROUND(d.target_price - o.offer_price, 2) AS margin_per_unit,
               MIN(o.available_qty, d.wanted_qty) AS match_qty,
               ROUND((d.target_price - o.offer_price)
                     * MIN(o.available_qty, d.wanted_qty), 2) AS margin_value,
               d.last_activity AS demand_seen, o.updated_at AS offer_seen
        FROM brand_offers o
        JOIN brand_demands d ON d.brand = o.brand
        JOIN suppliers s ON s.id = o.supplier_id
        JOIN crm_contacts cc ON cc.id = d.client_id
        JOIN traders t ON t.id = d.trader_id
        WHERE d.target_price > o.offer_price {rclause}
        ORDER BY margin_value DESC
        """,
        rparams,
    )


def _alert(df, atype, detail_fn, value_col=None):
    rows = []
    for _, r in df.iterrows():
        rows.append({
            "type": atype,
            "brand": r.get("brand"),
            "region": r.get("region") or r.get("demand_region"),
            "detail": detail_fn(r),
            "value": float(r[value_col]) if value_col and pd.notna(r.get(value_col)) else None,
        })
    return rows


def alerts(region=None, limit_per_type=5) -> pd.DataFrame:
    out = []

    opps = opportunities(region).head(limit_per_type)
    out += _alert(
        opps, "Buy↔Sell Match",
        lambda r: (f"Source {r['brand']} from {r['supplier']} @ €{r['buy_price']:.0f} "
                   f"→ {r['client']} wants it @ €{r['sell_price']:.0f} "
                   f"(~{int(r['match_qty'])} units, €{r['margin_value']:,.0f} margin)"),
        "margin_value",
    )

    rclause, rparams = region_clause(region, column="o.region")
    drops = run_query(
        f"""SELECT o.brand, o.region, s.name AS supplier, o.offer_price, o.prev_price,
                   ROUND(o.prev_price - o.offer_price, 2) AS price_drop
            FROM brand_offers o JOIN suppliers s ON s.id = o.supplier_id
            WHERE o.offer_price < o.prev_price {rclause}
            ORDER BY price_drop DESC LIMIT ?""",
        rparams + (limit_per_type,),
    )
    out += _alert(
        drops, "Price Drop",
        lambda r: (f"{r['supplier']} dropped {r['brand']} from €{r['prev_price']:.0f} "
                   f"to €{r['offer_price']:.0f} (−€{r['price_drop']:.0f}/unit)"),
        "price_drop",
    )

    rclause, rparams = region_clause(region, column="d.region")
    new_dem = run_query(
        f"""SELECT d.brand, d.region, cc.company_name AS client, d.last_activity
            FROM brand_demands d JOIN crm_contacts cc ON cc.id = d.client_id
            WHERE d.last_activity >= date('{NOW}', '-{RECENT_DAYS} days')
              AND d.brand IN (SELECT DISTINCT brand FROM brand_offers) {rclause}
            ORDER BY d.last_activity DESC LIMIT ?""",
        rparams + (limit_per_type,),
    )
    out += _alert(
        new_dem, "New Demand",
        lambda r: f"{r['client']} now wants {r['brand']} — we can source it ({r['last_activity']})",
    )

    rclause, rparams = region_clause(region, column="o.region")
    new_sup = run_query(
        f"""SELECT o.brand, o.region, s.name AS supplier, o.offer_price, o.updated_at
            FROM brand_offers o JOIN suppliers s ON s.id = o.supplier_id
            WHERE o.updated_at >= date('{NOW}', '-{RECENT_DAYS} days')
              AND o.brand IN (SELECT DISTINCT brand FROM brand_demands) {rclause}
            ORDER BY o.updated_at DESC LIMIT ?""",
        rparams + (limit_per_type,),
    )
    out += _alert(
        new_sup, "New Supply",
        lambda r: f"{r['supplier']} now offers {r['brand']} @ €{r['offer_price']:.0f} — clients want it",
    )

    rclause, rparams = region_clause(region, column="i.region")
    low = run_query(
        f"""SELECT p.brand, i.region, p.name AS product, i.qty_available, i.low_stock_threshold
            FROM inventory i JOIN products p ON p.id = i.product_id
            WHERE i.qty_available < i.low_stock_threshold
              AND p.brand IN (SELECT DISTINCT brand FROM brand_demands) {rclause}
            ORDER BY i.qty_available ASC LIMIT ?""",
        rparams + (limit_per_type,),
    )
    out += _alert(
        low, "Low Stock + Demand",
        lambda r: (f"{r['product']} ({r['brand']}) at {int(r['qty_available'])} units "
                   f"(< {int(r['low_stock_threshold'])}) — open client demand"),
    )

    rclause, rparams = region_clause(region, column="cd.region")
    stalled = run_query(
        f"""SELECT cd.deal_name, cd.region, cd.stage, cd.value, cd.last_activity, t.name AS trader
            FROM crm_deals cd JOIN traders t ON t.id = cd.trader_id
            WHERE cd.stage NOT IN ('won','lost')
              AND cd.last_activity <= datetime('{NOW}', '-{STALE_DAYS} days') {rclause}
            ORDER BY cd.last_activity ASC LIMIT ?""",
        rparams + (limit_per_type,),
    )
    out += _alert(
        stalled.assign(brand=None), "Stalled Deal",
        lambda r: (f"'{r['deal_name']}' ({r['stage']}, €{r['value']:,.0f}) — "
                   f"no activity since {str(r['last_activity'])[:10]} · {r['trader']}"),
        "value",
    )

    return pd.DataFrame(out)


def brands_i_can_buy(region=None) -> pd.DataFrame:
    # Region-scoped for RBAC: a trader sees offers from suppliers in their region;
    # a manager on "All regions" sees every supplier.
    rclause, rparams = region_clause(region, column="o.region")
    return run_query(
        f"""SELECT o.brand, o.category, COUNT(DISTINCT o.supplier_id) AS suppliers,
                   MIN(o.offer_price) AS best_buy_price, SUM(o.available_qty) AS total_available
            FROM brand_offers o WHERE 1=1 {rclause}
            GROUP BY o.brand ORDER BY o.brand""",
        rparams,
    )


def brands_i_can_sell(region=None) -> pd.DataFrame:
    rclause, rparams = region_clause(region, column="d.region")
    return run_query(
        f"""SELECT d.brand, d.category, COUNT(DISTINCT d.client_id) AS clients,
                   ROUND(AVG(d.target_price),2) AS avg_target_price, SUM(d.wanted_qty) AS total_wanted
            FROM brand_demands d WHERE 1=1 {rclause}
            GROUP BY d.brand ORDER BY total_wanted DESC""",
        rparams,
    )


def brand_detail(brand: str, region=None) -> dict:
    oclause, oparams = region_clause(region, column="o.region")
    offers = run_query(
        f"""SELECT s.name AS supplier, o.region, o.offer_price, o.available_qty, o.min_qty, o.valid_until
            FROM brand_offers o JOIN suppliers s ON s.id = o.supplier_id
            WHERE o.brand = ? {oclause} ORDER BY o.offer_price ASC""",
        (brand, *oparams),
    )
    rclause, rparams = region_clause(region, column="d.region")
    demands = run_query(
        f"""SELECT cc.company_name AS client, d.region, t.name AS trader,
                   d.target_price, d.wanted_qty, d.last_activity
            FROM brand_demands d
            JOIN crm_contacts cc ON cc.id = d.client_id
            JOIN traders t ON t.id = d.trader_id
            WHERE d.brand = ? {rclause} ORDER BY d.target_price DESC""",
        (brand, *rparams),
    )
    best = None
    if not offers.empty and not demands.empty:
        buy, sell = offers["offer_price"].min(), demands["target_price"].max()
        if sell > buy:
            best = {"buy": float(buy), "sell": float(sell),
                    "margin_per_unit": round(float(sell - buy), 2)}
    return {"offers": offers, "demands": demands, "best": best}
