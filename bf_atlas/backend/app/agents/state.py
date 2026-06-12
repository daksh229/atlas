"""Shared LangGraph state + a trace step helper so the UI can show the flow."""

import operator
from typing import Annotated, Any, Optional, TypedDict


def make_step(agent: str, action: str, detail: str = "", data: Any = None) -> dict:
    step = {"agent": agent, "action": action, "detail": detail}
    if data is not None:
        step["data"] = data
    return step


class AtlasState(TypedDict, total=False):
    # inputs
    question: str
    region: Optional[str]

    # router output
    intent: str          # data_query | opportunity | brand_intel | clarify | out_of_scope
    route_reason: str

    # sql path
    sql: Optional[str]
    columns: list
    rows: list           # list[dict], capped for transport

    # opportunity / brand path
    structured: Any      # service payload (opportunities, brand detail, …)

    # final / control
    answer: str
    clarification: Optional[str]
    error: Optional[str]

    # trace uses an add-reducer: each node returns {"trace": [step]} and they concat.
    trace: Annotated[list, operator.add]
