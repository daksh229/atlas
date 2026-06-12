"""
graph.py — assembles the BF Atlas multi-agent graph with LangGraph.

Flow:
    Router ─┬─ data_query  → SQL Generator ─(has SQL?)─→ Retrieval → Insight → END
            │                              └─(no SQL)──────────────────────→ END
            ├─ opportunity → Opportunity Engine ───────────────→ Insight → END
            ├─ brand_intel → Brand-Intel ──────────────────────→ Insight → END
            ├─ clarify     → Clarifier ────────────────────────────────→ END
            └─ out_of_scope→ Fallback ─────────────────────────────────→ END
"""

from functools import lru_cache

from langgraph.graph import END, StateGraph

from app.agents import (
    brand_intel,
    clarifier,
    fallback,
    insight,
    opportunity,
    rag_agent,
    retrieval,
    router,
    sql_generator,
)
from app.agents.state import AtlasState


def _route_from_router(state: AtlasState) -> str:
    return {
        "data_query": "sql_generator",
        "opportunity": "opportunity",
        "brand_intel": "brand_intel",
        "knowledge": "rag_agent",
        "clarify": "clarifier",
        "out_of_scope": "fallback",
    }.get(state.get("intent", ""), "fallback")


def _after_sql(state: AtlasState) -> str:
    # If SQL was generated, execute it; otherwise we already have an answer.
    return "retrieval" if state.get("sql") else END


@lru_cache(maxsize=1)
def build_graph():
    g = StateGraph(AtlasState)

    g.add_node("router", router.run)
    g.add_node("sql_generator", sql_generator.run)
    g.add_node("retrieval", retrieval.run)
    g.add_node("opportunity", opportunity.run)
    g.add_node("brand_intel", brand_intel.run)
    g.add_node("rag_agent", rag_agent.run)
    g.add_node("clarifier", clarifier.run)
    g.add_node("fallback", fallback.run)
    g.add_node("insight", insight.run)

    g.set_entry_point("router")
    g.add_conditional_edges("router", _route_from_router, {
        "sql_generator": "sql_generator",
        "opportunity": "opportunity",
        "brand_intel": "brand_intel",
        "rag_agent": "rag_agent",
        "clarifier": "clarifier",
        "fallback": "fallback",
    })
    g.add_conditional_edges("sql_generator", _after_sql, {"retrieval": "retrieval", END: END})
    g.add_edge("retrieval", "insight")
    g.add_edge("opportunity", "insight")
    g.add_edge("brand_intel", "insight")
    g.add_edge("insight", END)
    g.add_edge("rag_agent", END)  # self-finalises (synthesises from retrieved docs)
    g.add_edge("clarifier", END)
    g.add_edge("fallback", END)

    return g.compile()


def run_chat(question: str, region: str | None = None) -> AtlasState:
    """Invoke the graph for one question and return the final state."""
    graph = build_graph()
    initial: AtlasState = {"question": question, "region": region, "trace": []}
    return graph.invoke(initial)
