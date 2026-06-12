"""
opportunity.py — answers cross-match / "what can I sell" questions using the
Atlas Opportunity Engine directly (no SQL). Returns the top opportunities and a
few live alerts as structured data for the Insight agent to narrate.
"""

from app.agents.state import AtlasState, make_step
from app.core.serialize import int_counts, to_records
from app.services import atlas

TOP_N = 8


def run(state: AtlasState) -> dict:
    region = state.get("region")
    opps = atlas.opportunities(region).head(TOP_N)
    alerts = atlas.alerts(region)

    rows = to_records(opps[["brand", "supplier", "client", "buy_price", "sell_price",
                            "match_qty", "margin_value"]]) if not opps.empty else []
    total = float(opps["margin_value"].sum()) if not opps.empty else 0.0

    structured = {
        "kind": "opportunities",
        "top": rows,
        "total_margin": total,
        "alert_counts": int_counts(alerts["type"].value_counts().to_dict()) if not alerts.empty else {},
    }
    step = make_step(
        "Opportunity Engine", "cross-matched offers ↔ demand",
        f"{len(rows)} top matches, €{total:,.0f} margin in scope",
        data={"count": len(rows)},
    )
    return {"structured": structured, "rows": rows, "trace": [step]}
