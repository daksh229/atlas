"""Dashboard data: KPIs + chart frames (region-scoped)."""

import pandas as pd

from app.core.database import ALL_REGIONS, region_clause, run_query


def kpis(region=None) -> dict:
    rclause, rparams = region_clause(region)

    rev = run_query(
        f"""SELECT COALESCE(SUM(total_amount), 0) AS revenue FROM orders
            WHERE status != 'cancelled'
              AND strftime('%Y-%m', order_date) = strftime('%Y-%m', 'now') {rclause}""",
        rparams,
    )["revenue"].iloc[0]

    open_deals = run_query(
        f"""SELECT COUNT(*) AS n, COALESCE(SUM(value),0) AS pipeline FROM crm_deals
            WHERE stage NOT IN ('won','lost') {rclause}""",
        rparams,
    )

    low_stock = run_query(
        f"""SELECT COUNT(*) AS n FROM inventory
            WHERE qty_available < low_stock_threshold {rclause}""",
        rparams,
    )["n"].iloc[0]

    closed = run_query(
        f"""SELECT SUM(CASE WHEN stage='won' THEN 1 ELSE 0 END) AS won,
                   SUM(CASE WHEN stage IN ('won','lost') THEN 1 ELSE 0 END) AS closed
            FROM crm_deals WHERE 1=1 {rclause}""",
        rparams,
    )
    won, total = closed["won"].iloc[0] or 0, closed["closed"].iloc[0] or 0
    win_rate = round(float(won / total * 100), 1) if total else 0.0

    return {
        "revenue_mtd": float(rev),
        "open_deals": int(open_deals["n"].iloc[0]),
        "open_pipeline": float(open_deals["pipeline"].iloc[0]),
        "low_stock": int(low_stock),
        "win_rate": win_rate,
    }


def revenue_by_region(region=None) -> pd.DataFrame:
    # Region-scoped for RBAC: a trader sees only their own region's bar.
    rclause, rparams = region_clause(region)
    return run_query(
        f"""SELECT region, SUM(total_amount) AS revenue, SUM(margin_amount) AS margin
            FROM orders WHERE status != 'cancelled' {rclause}
            GROUP BY region ORDER BY revenue DESC""",
        rparams,
    )


def pipeline_by_stage(region=None) -> pd.DataFrame:
    rclause, rparams = region_clause(region)
    df = run_query(
        f"""SELECT stage, COUNT(*) AS deals, SUM(value) AS value
            FROM crm_deals WHERE 1=1 {rclause} GROUP BY stage""",
        rparams,
    )
    order = ["lead", "qualified", "proposal", "negotiation", "won", "lost"]
    df["stage"] = pd.Categorical(df["stage"], categories=order, ordered=True)
    return df.sort_values("stage")


def low_stock(region=None) -> pd.DataFrame:
    rclause, rparams = region_clause(region, column="i.region")
    return run_query(
        f"""SELECT p.name AS product, p.sku, p.category, i.warehouse, i.region,
                   i.qty_available, i.low_stock_threshold
            FROM inventory i JOIN products p ON p.id = i.product_id
            WHERE i.qty_available < i.low_stock_threshold {rclause}
            ORDER BY i.qty_available ASC""",
        rparams,
    )


def revenue_over_time(region=None) -> pd.DataFrame:
    rclause, rparams = region_clause(region)
    return run_query(
        f"""SELECT strftime('%Y-%m', order_date) AS month, SUM(total_amount) AS revenue
            FROM orders WHERE status != 'cancelled' {rclause}
            GROUP BY month ORDER BY month""",
        rparams,
    )


def top_products(region=None, limit=10) -> pd.DataFrame:
    rclause, rparams = region_clause(region, column="o.region")
    return run_query(
        f"""SELECT p.name AS product, p.category,
                   SUM(oi.qty) AS units, SUM(oi.line_total) AS revenue
            FROM order_items oi
            JOIN orders o ON o.id = oi.order_id
            JOIN products p ON p.id = oi.product_id
            WHERE o.status != 'cancelled' {rclause}
            GROUP BY p.id ORDER BY revenue DESC LIMIT ?""",
        rparams + (limit,),
    )
