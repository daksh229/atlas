"""
email_parser.py — turn a raw offer email into structured offers (spec §7 Phase 2).

The AI half: one Claude call with a forced structured-output schema
(`messages.parse` + Pydantic) extracts every offer in the email. One email may
contain several offers (a price list), so it returns a list.

The offline half: if no ANTHROPIC_API_KEY is set (or the call fails), a
deterministic heuristic scans for brand-dictionary names + nearby price/qty so
the POC still runs with zero external dependencies. Each result is labelled
`engine: "ai" | "heuristic"` so we never pretend a heuristic parse was AI.

Brand resolution is NOT done here — it stays deterministic in offers.py via the
brand dictionary, so an extracted name is canonicalised (or flagged) exactly the
same way for both engines.
"""

import re

from app.core.config import settings
from app.services import brands

SYSTEM = (
    "You extract product offers from a wholesale beauty supplier's email. "
    "Return every distinct offer. Use the brand exactly as written in the email "
    "(do not normalise spelling). Price is per unit. If a field is absent, leave "
    "it null. Do not invent offers; if the email contains none, return an empty list."
)


def _ai_extract(text: str) -> list[dict] | None:
    """Return a list of raw offer dicts via Claude, or None if unavailable."""
    if not settings.ANTHROPIC_API_KEY:
        return None
    try:
        import anthropic
        from pydantic import BaseModel

        class Offer(BaseModel):
            brand: str
            product: str | None = None
            offer_price: float | None = None
            currency: str | None = None
            quantity: int | None = None
            valid_until: str | None = None
            supplier: str | None = None
            confidence: float = 0.5

        class Extraction(BaseModel):
            offers: list[Offer]

        client = anthropic.Anthropic()
        resp = client.messages.parse(
            model=settings.EXTRACT_MODEL,
            max_tokens=2048,
            system=SYSTEM,
            messages=[{"role": "user", "content": text}],
            output_format=Extraction,
        )
        return [o.model_dump() for o in resp.parsed_output.offers]
    except Exception:
        # Any failure (no package, network, refusal, schema) → fall back, don't crash.
        return None


_PRICE = re.compile(r"(?:€|eur)\s*([0-9]+(?:[.,][0-9]{1,2})?)|([0-9]+(?:[.,][0-9]{2}))",
                    re.IGNORECASE)
_QTY = re.compile(r"(?:qty|quantity)?\s*([0-9]{2,5})\s*units|qty\s*([0-9]{2,5})",
                  re.IGNORECASE)


def _num(m) -> float | None:
    for g in m.groups():
        if g:
            return float(g.replace(",", "."))
    return None


def _heuristic_extract(text: str) -> list[dict]:
    """Find dictionary brands line-by-line and pull a nearby price/qty."""
    smap = brands.surface_map()  # normalized surface -> (brand_id, canonical)
    # Longer surfaces first so 'christian dior' wins over 'dior'.
    surfaces = sorted(smap.keys(), key=len, reverse=True)
    offers = []
    for line in text.splitlines():
        norm_line = re.sub(r"[^a-z0-9 ]+", " ", line.lower())
        norm_line = re.sub(r"\s+", " ", norm_line)
        for s in surfaces:
            if re.search(rf"\b{re.escape(s)}\b", norm_line):
                price = _PRICE.search(line)
                qty = _QTY.search(line)
                offers.append({
                    "brand": smap[s][1],  # canonical surface for display
                    "product": line.strip(),
                    "offer_price": _num(price) if price else None,
                    "currency": "EUR",
                    "quantity": int(next(g for g in qty.groups() if g)) if qty else None,
                    "valid_until": None, "supplier": None, "confidence": 0.4,
                })
                break  # one brand per line
    return offers


def extract(text: str) -> dict:
    """Extract offers from email text. Returns {engine, offers:[raw offer dicts]}."""
    ai = _ai_extract(text)
    if ai is not None:
        return {"engine": "ai", "offers": ai}
    return {"engine": "heuristic", "offers": _heuristic_extract(text)}
