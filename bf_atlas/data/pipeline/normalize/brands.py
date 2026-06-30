"""
brands.py — the brand dictionary, built FROM the real product master.

Spec §9 ("Brand name consistency") calls one-canonical-record-per-brand
"foundational to everything". The brand dictionary is derived from the product
master (`Products_Info.xlsx`), with a small curated alias set layered on top for
the cross-name brands that matching would otherwise split (YSL / Saint Laurent /
Yves Saint Laurent, Dior / Christian Dior, ...).

resolve() is the only entry point the rest of the pipeline uses: a surface form
(however messy) → a stable brand_id, or None (then it goes to `unresolved`,
never force-matched).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from data.pipeline.normalize.clean import normalize_brand

# Curated aliases for known multi-name beauty brands: alias surface -> canonical
# surface as it appears in Products_Info. Only applied when the canonical brand
# actually exists in the data, so this never invents brands.
# Targets are the EXACT canonical spelling as it appears in Products_Info; both
# alias and target are normalized before lookup, so an alias only binds when its
# target brand is really in the data.
_CURATED_ALIASES: dict[str, str] = {
    "ysl": "Yves Saint Laurent",
    "saint laurent": "Yves Saint Laurent",
    "yves saint-laurent": "Yves Saint Laurent",
    "ysl beauty": "Yves Saint Laurent",
    "cd": "Dior",
    "christian dior": "Dior",
    "tomford": "Tom Ford",
    "t ford": "Tom Ford",
    "t. ford": "Tom Ford",
    "tf": "Tom Ford",
    "d&g": "Dolce & Gabbana",
    "armani": "Giorgio Armani",
    "ck": "Calvin Klein",
    "bulgari": "Bvlgari",
    "ck calvin klein": "Calvin Klein",
}

_SLUG = re.compile(r"[^a-z0-9]+")


def brand_id_for(canonical: str) -> str:
    """Stable id derived from the canonical name: 'Tom Ford' -> 'brand-tom-ford'."""
    slug = _SLUG.sub("-", normalize_brand(canonical)).strip("-")
    return f"brand-{slug or 'unknown'}"


@dataclass
class BrandDictionary:
    # brand_id -> (canonical_name, category)
    brands: dict[str, tuple[str, str | None]] = field(default_factory=dict)
    # normalized surface -> brand_id
    _index: dict[str, str] = field(default_factory=dict)
    # brand_id -> set of alias surfaces (for export/inspection)
    _aliases: dict[str, set[str]] = field(default_factory=dict)

    # --- construction ------------------------------------------------------
    @classmethod
    def from_records(cls, records: list[tuple[str, str | None]]) -> "BrandDictionary":
        """records = [(raw_brand_name, category), ...] from the product master."""
        d = cls()
        # 1) one canonical record per distinct normalized brand (first spelling wins)
        norm_to_canonical: dict[str, str] = {}
        for raw, category in records:
            norm = normalize_brand(raw)
            if not norm:
                continue
            if norm not in norm_to_canonical:
                canonical = str(raw).strip()
                norm_to_canonical[norm] = canonical
                bid = brand_id_for(canonical)
                d.brands[bid] = (canonical, category)
                d._index[norm] = bid
                d._aliases.setdefault(bid, set())
        # 2) layer curated aliases, but only onto brands that exist in the data
        for alias_surface, canonical_target in _CURATED_ALIASES.items():
            target_norm = normalize_brand(canonical_target)
            bid = d._index.get(target_norm)
            if not bid:
                continue
            alias_norm = normalize_brand(alias_surface)
            if alias_norm and alias_norm not in d._index:
                d._index[alias_norm] = bid
                d._aliases[bid].add(alias_norm)
        return d

    # --- lookup ------------------------------------------------------------
    def resolve(self, surface) -> str | None:
        """Surface form → brand_id, or None if genuinely unknown."""
        return self._index.get(normalize_brand(surface))

    def canonical(self, brand_id: str) -> str | None:
        rec = self.brands.get(brand_id)
        return rec[0] if rec else None

    # --- export for load_db -----------------------------------------------
    def to_brand_rows(self) -> list[dict]:
        return [
            {"id": bid, "canonical_name": name, "category": cat}
            for bid, (name, cat) in sorted(self.brands.items())
        ]

    def to_alias_rows(self) -> list[dict]:
        rows: list[dict] = []
        for bid, aliases in self._aliases.items():
            for i, alias in enumerate(sorted(aliases)):
                rows.append({"id": f"{bid}-a{i}", "brand_id": bid, "alias": alias})
        return rows

    def __len__(self) -> int:
        return len(self.brands)
