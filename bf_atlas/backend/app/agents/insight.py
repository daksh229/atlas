"""
insight.py — shared finalizer for the data-bearing routes (data_query,
opportunity, brand_intel). Turns rows/structured payloads into a concise business
answer. Uses Claude when available; otherwise a deterministic template so the
demo still produces a sensible answer.
"""

import pandas as pd

from app.agents.state import AtlasState, make_step
from app.core import llm


def _template(state: AtlasState) -> str:
    if state.get("error"):
        return f"I couldn't complete that: {state['error']}"
    rows = state.get("rows") or []
    structured = state.get("structured") or {}
    kind = structured.get("kind")

    if kind == "opportunities":
        n, total = len(structured.get("top", [])), structured.get("total_margin", 0)
        if not n:
            return "No profitable cross-match opportunities in this scope right now."
        top = structured["top"][0]
        return (f"{n} cross-match opportunities worth ~€{total:,.0f} in margin. "
                f"Best: {top['brand']} — buy @ €{top['buy_price']:.0f}, "
                f"sell @ €{top['sell_price']:.0f} (~€{top['margin_value']:,.0f}).")
    if kind == "brand_detail":
        b, best = structured["brand"], structured.get("best")
        if best:
            return (f"{b}: source @ €{best['buy']:.0f}, place @ €{best['sell']:.0f} — "
                    f"€{best['margin_per_unit']:.0f}/unit margin available.")
        return f"{b}: offers and demand exist, but no profitable buy→sell loop in scope."
    if kind == "brand_overview":
        sell = structured.get("sell", [])
        if sell:
            return (f"Top brand by client demand: {sell[0]['brand']} "
                    f"({int(sell[0]['total_wanted'])} units wanted).")
        return "No active brand demand in this scope."

    # generic data_query
    if not rows:
        return "The query ran but returned no rows for this scope."
    return f"Found {len(rows)} result(s). Top row: {rows[0]}"


def run(state: AtlasState) -> dict:
    # If a node already produced a final answer (e.g. no-key SQL skip), keep it.
    if state.get("answer") and not state.get("rows") and not state.get("structured"):
        return {"trace": [make_step("Insight", "passed through", "Used upstream answer.")]}

    if not llm.has_llm():
        ans = _template(state)
        return {"answer": ans, "trace": [make_step("Insight", "summarised (template)", "")]}

    rows = state.get("rows") or []
    preview = pd.DataFrame(rows).head(25).to_markdown(index=False) if rows else "(no rows)"
    context = ""
    if state.get("structured", {}).get("kind"):
        context = f"\nContext kind: {state['structured']['kind']}."
    if state.get("error"):
        context += f"\nNote: an error occurred: {state['error']}"

    try:
        ans = llm.complete(
            "You are BF Atlas. Give a trader a concise 2-3 sentence business insight. "
            "Lead with the number that matters. No preamble, no SQL.",
            f"Question: {state['question']}{context}\nResult (first 25 rows):\n{preview}",
            max_tokens=300,
        )
    except Exception:
        ans = _template(state)

    return {"answer": ans, "trace": [make_step("Insight", "summarised (Claude)", "")]}
