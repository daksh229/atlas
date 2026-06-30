"""
brands.py — the BF Atlas BRAND DICTIONARY (canonical brands + known aliases).

This is the single source of truth the spec (§9 "Brand name consistency") calls
"foundational to everything": one canonical record per brand, with aliases, so
that "YSL", "Saint Laurent", and "Yves Saint Laurent" all resolve to ONE brand.

The pipeline uses it two ways:
  - generate_raw.py  picks a RANDOM surface form (canonical OR an alias) when it
                     writes raw data — simulating the messy real world.
  - preprocess.py    resolves every surface form back to a single brand_id.

50 brands; ~20 carry aliases so the dictionary visibly earns its place. brand_id
is derived deterministically from the canonical name in preprocess.py, so it is
stable across rebuilds.
"""

# (canonical_name, category, [aliases])
BRANDS: list[tuple[str, str, list[str]]] = [
    # ── perfume ──────────────────────────────────────────────────────────────
    ("Yves Saint Laurent", "perfume", ["YSL", "Saint Laurent", "Yves Saint-Laurent"]),
    ("Christian Dior",     "perfume", ["Dior", "CD"]),
    ("Chanel",             "perfume", []),
    ("Tom Ford",           "perfume", ["TF"]),
    ("Giorgio Armani",     "perfume", ["Armani"]),
    ("Dolce & Gabbana",    "perfume", ["D&G", "Dolce Gabbana", "Dolce and Gabbana"]),
    ("Versace",            "perfume", []),
    ("Paco Rabanne",       "perfume", ["Rabanne"]),
    ("Jean Paul Gaultier", "perfume", ["JPG", "Gaultier"]),
    ("Carolina Herrera",   "perfume", ["CH"]),
    ("Hugo Boss",          "perfume", ["Boss"]),
    ("Calvin Klein",       "perfume", ["CK"]),
    ("Burberry",           "perfume", []),
    ("Givenchy",           "perfume", []),
    ("Lancôme",            "perfume", ["Lancome"]),
    # ── skincare ─────────────────────────────────────────────────────────────
    ("Estée Lauder",       "skincare", ["Estee Lauder", "EL"]),
    ("Clinique",           "skincare", []),
    ("La Roche-Posay",     "skincare", ["La Roche Posay", "LRP"]),
    ("CeraVe",             "skincare", []),
    ("The Ordinary",       "skincare", []),
    ("Vichy",              "skincare", []),
    ("Eucerin",            "skincare", []),
    ("Neutrogena",         "skincare", []),
    ("Olay",               "skincare", ["Oil of Olay"]),
    ("Nivea",              "skincare", []),
    ("Bioderma",           "skincare", []),
    ("L'Oréal Paris",      "skincare", ["L'Oreal", "Loreal", "LOreal Paris"]),
    ("Garnier",            "skincare", []),
    ("Kiehl's",            "skincare", ["Kiehls"]),
    ("Shiseido",           "skincare", []),
    # ── cosmetics ────────────────────────────────────────────────────────────
    ("MAC",                "cosmetics", ["M.A.C", "MAC Cosmetics"]),
    ("Maybelline",         "cosmetics", ["Maybelline New York"]),
    ("Revlon",             "cosmetics", []),
    ("Urban Decay",        "cosmetics", ["UD"]),
    ("NARS",               "cosmetics", []),
    ("Bobbi Brown",        "cosmetics", []),
    ("Charlotte Tilbury",  "cosmetics", ["CT"]),
    ("Fenty Beauty",       "cosmetics", ["Fenty"]),
    ("Benefit",            "cosmetics", ["Benefit Cosmetics"]),
    ("e.l.f.",             "cosmetics", ["elf", "ELF Cosmetics", "e.l.f"]),
    # ── haircare ─────────────────────────────────────────────────────────────
    ("Kérastase",          "haircare", ["Kerastase"]),
    ("Redken",             "haircare", []),
    ("Olaplex",            "haircare", []),
    ("Moroccanoil",        "haircare", ["Moroccan Oil"]),
    ("Schwarzkopf",        "haircare", []),
    ("Pantene",            "haircare", []),
    # ── bodycare ─────────────────────────────────────────────────────────────
    ("The Body Shop",      "bodycare", []),
    ("Dove",               "bodycare", []),
    ("L'Occitane",         "bodycare", ["L'Occitane en Provence", "LOccitane", "L Occitane"]),
    ("Rituals",            "bodycare", []),
]

assert len(BRANDS) == 50, f"expected 50 brands, got {len(BRANDS)}"

# Convenience lookups -------------------------------------------------------
CANONICAL_BY_NAME = {name: (name, cat, aliases) for name, cat, aliases in BRANDS}


def all_surface_forms(canonical: str) -> list[str]:
    """Canonical name + every alias — the possible 'messy' spellings."""
    name, _cat, aliases = CANONICAL_BY_NAME[canonical]
    return [name, *aliases]
