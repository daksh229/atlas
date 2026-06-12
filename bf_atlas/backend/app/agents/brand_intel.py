"""
brand_intel.py — answers brand-level questions ("can I buy/sell brand X").
Detects the brand named in the question, then pulls its supply/demand detail from
the Atlas engine. Falls back to a demand overview when no specific brand is named.
"""

from app.agents.state import AtlasState, make_step
from app.core.serialize import to_records
from app.services import atlas

# Canonical brand names as stored in the catalogue.
KNOWN_BRANDS = [
    "Maison Luxe", "Floral Studio", "Arabian Essence", "Blue Ocean Co", "Artisan Blend",
    "Glow Lab", "HydraLux", "SunShield Pro", "Colour Story", "Lash Queen",
    "Silk & Shine", "Natura Soft",
]


def _detect_brand(question: str) -> str | None:
    q = question.lower()
    for b in KNOWN_BRANDS:
        if b.lower() in q or b.lower().replace(" & ", " and ") in q:
            return b
    # token fallback: a distinctive single word (e.g. "hydralux")
    for b in KNOWN_BRANDS:
        first = b.lower().split()[0]
        if len(first) > 4 and first in q:
            return b
    return None


def run(state: AtlasState) -> dict:
    region = state.get("region")
    brand = _detect_brand(state["question"])

    if brand:
        d = atlas.brand_detail(brand, region)
        structured = {
            "kind": "brand_detail",
            "brand": brand,
            "best": d["best"],
            "offers": to_records(d["offers"]),
            "demands": to_records(d["demands"].head(10)),
        }
        detail = (f"{brand}: {len(d['offers'])} supplier offers, {len(d['demands'])} client demands"
                  + (f", best loop €{d['best']['margin_per_unit']:.0f}/unit" if d["best"] else ""))
        rows = structured["offers"]
    else:
        sell = atlas.brands_i_can_sell(region).head(10)
        structured = {"kind": "brand_overview", "brand": None,
                      "sell": to_records(sell)}
        detail = "No specific brand named — returned a demand overview."
        rows = structured["sell"]

    step = make_step("Brand-Intel", "looked up brand supply/demand", detail,
                     data={"brand": brand})
    return {"structured": structured, "rows": rows, "trace": [step]}
