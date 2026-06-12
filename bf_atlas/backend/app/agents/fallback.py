"""
fallback.py — terminal node for out-of-scope questions. Explains what Atlas can
do rather than attempting an answer it shouldn't.
"""

from app.agents.state import AtlasState, make_step

MESSAGE = (
    "That's outside what BF Atlas covers. I work with your trading data — try asking "
    "about revenue and deals, low stock, cross-match opportunities (what to buy/sell "
    "for margin), or a specific brand's supply and demand."
)


def run(state: AtlasState) -> dict:
    step = make_step("Fallback", "out-of-scope response", "Returned capability guidance.")
    return {"answer": MESSAGE, "trace": [step]}
