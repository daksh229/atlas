"""
sql_generator.py — turns a natural-language data question into a single SQLite
SELECT, scoped to the trader's region. Generation only; execution is a separate
agent (retrieval) so the two concerns stay isolated.
"""

from app.agents.state import AtlasState, make_step
from app.core import llm
from app.core.sql_guard import strip_sql

SCHEMA_CONTEXT = """
SQLite tables for a perfume/cosmetics trading platform:
- traders(id, name, email, region, role)
- products(id, odoo_id, name, category, brand, sku, unit_price, cost_price, margin_pct)
- inventory(id, product_id, warehouse, region, qty_on_hand, qty_reserved, qty_available, low_stock_threshold)
- orders(id, odoo_id, trader_id, trader_region, customer_name, region, total_amount, margin_amount, status, order_date)
- order_items(id, order_id, product_id, qty, unit_price, line_total)
- crm_contacts(id, nethunt_id, company_name, contact_name, email, country, region, trader_id)
- crm_deals(id, nethunt_id, contact_id, trader_id, deal_name, stage, value, probability, expected_close, last_activity, region)
- suppliers(id, name, country, region, reliability)
- brand_offers(id, supplier_id, brand, category, offer_price, prev_price, min_qty, available_qty, region, valid_until, updated_at)
- brand_demands(id, client_id, trader_id, brand, category, target_price, wanted_qty, region, last_activity)
Notes: dates are 'YYYY-MM-DD' TEXT; use strftime(). Deal stages: lead, qualified,
proposal, negotiation, won, lost. Regions: EU-West, Asia-Pacific, Americas,
Middle-East, Southeast-Asia.
"""


def run(state: AtlasState) -> dict:
    question, region = state["question"], state.get("region")

    if not llm.has_llm():
        msg = ("I need the Claude API key to translate that into SQL. Meanwhile the "
               "Opportunity Alerts and Brand Intelligence views answer the most common "
               "trading questions directly.")
        step = make_step("SQL Generator", "skipped", "No API key — cannot generate SQL.")
        return {"answer": msg, "sql": None, "trace": [step]}

    region_rule = (
        f"- Unless the user asks for a global/all-region view, filter to region = '{region}'.\n"
        if region and region != "All regions" else ""
    )
    system = (f"{SCHEMA_CONTEXT}\nReturn ONLY one read-only SQLite SELECT query, no prose, "
              f"no markdown. Never write/update/delete.\n{region_rule}")
    try:
        sql = strip_sql(llm.complete(system, question, max_tokens=600))
    except Exception as exc:  # noqa: BLE001
        step = make_step("SQL Generator", "error", str(exc))
        return {"error": f"SQL generation failed: {exc}", "sql": None,
                "answer": "I couldn't generate a query for that right now "
                          f"({type(exc).__name__}). Please try again or rephrase.",
                "trace": [step]}

    step = make_step("SQL Generator", "generated SQL", sql, data={"sql": sql})
    return {"sql": sql, "trace": [step]}
