"""
router.py — intent classifier. Inspects the question and picks one route:

  data_query   general data question  -> SQL Generator → Retrieval
  opportunity  cross-match / "what can I sell/match" -> Opportunity agent
  brand_intel  brand-level "can I buy/sell brand X"   -> Brand-Intel agent
  clarify      too vague to act on    -> Clarifier
  out_of_scope unrelated to Atlas     -> Fallback

Uses Claude when available, else a transparent keyword heuristic so the demo
still routes without an API key.
"""

from app.agents.state import AtlasState, make_step
from app.core import llm

INTENTS = ["data_query", "opportunity", "brand_intel", "knowledge", "clarify", "out_of_scope"]

# Known brands — lets the heuristic spot brand-level questions.
BRANDS = [
    "maison luxe", "floral studio", "arabian essence", "blue ocean", "artisan blend",
    "glow lab", "hydralux", "sunshield", "colour story", "lash queen", "silk & shine",
    "silk and shine", "natura soft",
]

_OPP_WORDS = ("opportunity", "opportunities", "cross-match", "cross match", "match",
              "arbitrage", "margin", "who can i sell", "what can i sell", "best deal",
              "alert", "spread")
# Qualitative / free-text questions → RAG over notes & emails.
_KNOW_WORDS = ("note", "notes", "email", "emails", "said", "saying", "mention",
               "feedback", "comment", "concern", "concerns", "complain", "why did",
               "why are", "summar", "what happened", "delay", "sentiment", "context")
_OOS_WORDS = ("weather", "joke", "who are you", "your name", "hello", "hi ", "thanks",
              "football", "stock market", "bitcoin", "poem", "translate")


def _heuristic(question: str) -> tuple[str, str]:
    q = f" {question.lower().strip()} "
    if any(w in q for w in _OOS_WORDS) and not any(w in q for w in ("sell", "buy", "deal")):
        return "out_of_scope", "Matched out-of-scope keywords."
    if len(question.split()) <= 2:
        return "clarify", "Too few words to act on confidently."
    if any(w in q for w in _KNOW_WORDS):
        return "knowledge", "Matched qualitative/free-text keywords (notes, emails, why)."
    if any(b in q for b in BRANDS) and any(w in q for w in ("buy", "sell", "source", "supplier", "brand")):
        return "brand_intel", "Mentions a known brand with a buy/sell intent."
    if any(w in q for w in _OPP_WORDS):
        return "opportunity", "Matched cross-match/opportunity keywords."
    return "data_query", "Defaulted to a data question."


def _llm_route(question: str) -> tuple[str, str]:
    system = (
        "You are the router for BF Atlas, a perfume/cosmetics trading intelligence "
        "tool. Classify the user's question into exactly one intent:\n"
        "- data_query: metrics/lists over orders, inventory, deals, traders, revenue (numbers).\n"
        "- opportunity: cross-match buy↔sell opportunities, alerts, margins to capture.\n"
        "- brand_intel: questions about a specific brand's supply/demand (can I buy/sell X).\n"
        "- knowledge: qualitative questions answered from notes/emails/briefings — what a "
        "client said, why a deal stalled, supplier email content, sentiment, context.\n"
        "- clarify: too vague/ambiguous to answer without a follow-up.\n"
        "- out_of_scope: unrelated to BF trading data.\n"
    )
    user = (f'Question: "{question}"\n'
            'Return {"intent": "...", "reason": "...", "confidence": 0.0-1.0}.')
    try:
        out = llm.complete_json(system, user, max_tokens=200)
        intent = out.get("intent")
        if intent not in INTENTS:
            return _heuristic(question)
        # Low-confidence non-trivial questions → ask to clarify.
        if out.get("confidence", 1) < 0.45 and intent != "out_of_scope":
            return "clarify", f"Low confidence ({out.get('confidence')}): {out.get('reason','')}"
        return intent, out.get("reason", "")
    except Exception:
        return _heuristic(question)


def run(state: AtlasState) -> dict:
    question = state["question"]
    if llm.has_llm():
        intent, reason = _llm_route(question)
        engine = "Claude"
    else:
        intent, reason = _heuristic(question)
        engine = "heuristic (no API key)"
    step = make_step("Router", f"routed → {intent}", f"{reason} [{engine}]", data={"intent": intent})
    return {"intent": intent, "route_reason": reason, "trace": [step]}
