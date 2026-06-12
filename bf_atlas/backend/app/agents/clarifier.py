"""
clarifier.py — when the router judges the question too vague, ask a focused
follow-up instead of guessing or failing. Terminal node (no data is fetched).
"""

from app.agents.state import AtlasState, make_step
from app.core import llm

_CAPABILITIES = (
    "I can help with: trading metrics (revenue, deals, inventory, win rate), "
    "cross-match opportunities (what to buy/sell for margin), and brand supply/demand."
)


def run(state: AtlasState) -> dict:
    question = state["question"]
    if llm.has_llm():
        try:
            q = llm.complete(
                "You are BF Atlas. The user's question is too vague to answer. Ask ONE "
                "short, specific clarifying question to narrow it down. " + _CAPABILITIES,
                f'User said: "{question}"', max_tokens=120,
            )
        except Exception:
            q = f"Could you be more specific? {_CAPABILITIES}"
    else:
        q = f"Could you be more specific? {_CAPABILITIES}"

    step = make_step("Clarifier", "asked for clarification", q)
    return {"clarification": q, "answer": q, "trace": [step]}
