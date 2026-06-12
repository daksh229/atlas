"""
rag_agent.py — the knowledge route. Retrieval-augmented generation over the
unstructured corpus (deal notes, supplier emails, brand briefs).

Flow: embed the question → region-filtered top-k retrieval → Claude synthesises a
cited answer from ONLY the retrieved snippets. Self-finalising (produces the final
answer), so the graph routes it straight to END. Without an API key it returns the
top snippets directly so the demo still works offline.
"""

from app.agents.state import AtlasState, make_step
from app.core import llm
from app.services import rag

TOP_K = 4


def _format_sources(docs: list[dict]) -> list[dict]:
    return [{"id": d.get("id"), "title": d["title"], "type": d["type"],
             "region": d["region"], "score": d["score"],
             "snippet": d["text"][:200]} for d in docs]


def run(state: AtlasState) -> dict:
    question, region = state["question"], state.get("region")
    docs = rag.retrieve(question, region, k=TOP_K)
    sources = _format_sources(docs)
    step = make_step("Knowledge (RAG)", f"retrieved {len(docs)} docs [{rag.engine_name()}]",
                     "; ".join(d["title"] for d in docs[:3]))

    if not docs:
        return {"answer": "I couldn't find anything relevant in the notes for your scope.",
                "structured": {"kind": "rag", "sources": []}, "trace": [step]}

    if not llm.has_llm():
        top = docs[0]
        ans = (f"From {top['title']}: {top['text']}\n\n"
               f"(Offline mode — showing the top match. With a Claude key the answer is "
               f"synthesised across all {len(docs)} retrieved sources.)")
        return {"answer": ans, "structured": {"kind": "rag", "sources": sources},
                "trace": [step]}

    context = "\n\n".join(
        f"[{i+1}] ({d['type']}, {d['region'] or 'global'}) {d['title']}\n{d['text']}"
        for i, d in enumerate(docs)
    )
    try:
        ans = llm.complete(
            "You answer a trader's question using ONLY the provided notes/emails. "
            "Cite sources inline as [1], [2]. If the notes don't contain the answer, say so. "
            "Be concise (2-4 sentences).",
            f"Question: {question}\n\nRetrieved notes:\n{context}",
            max_tokens=400,
        )
    except Exception as exc:  # noqa: BLE001 — fall back to the top snippet
        ans = f"{docs[0]['title']}: {docs[0]['text']}  (synthesis unavailable: {type(exc).__name__})"

    return {"answer": ans, "structured": {"kind": "rag", "sources": sources}, "trace": [step]}
