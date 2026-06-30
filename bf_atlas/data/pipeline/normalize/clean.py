"""
clean.py — pure data-quality helpers for the messy source package.

Everything here is a small, side-effect-free function so it can be unit-tested
against golden fixtures (decimal commas, doubled brand prefixes, tester EANs,
mixed price tokens) and applied vectorized over large frames.

The mess these handle is real and observed in the source data:
  - prices like "255,00"  (European decimal comma)
  - prices like "€51.39", "12.25 EUR", "59,94"  (mixed symbol/code placement)
  - quantities like "24 units", "60 pcs", "x50"
  - EANs with a trailing tester marker: "5060485381846T"
  - doubled brand prefix in item names: "Electimuss  Electimuss London ..."
  - noise suffixes on retailer brands: "Sisley Paris", "Wella Paris"
"""

from __future__ import annotations

import re
import unicodedata

# Currency tokens we strip out of free-text price cells before parsing.
_CURRENCY_TOKENS = ("EUR", "USD", "GBP", "JPY", "€", "$", "£", "¥")

# Trailing words that are noise on a brand surface form, never the brand itself.
# Conservative on purpose: only stripped when the brand has >1 token.
_BRAND_NOISE_SUFFIX = {
    "paris", "london", "milano", "milan", "newyork", "ny",
    "beauty", "cosmetics", "cosmetic", "skincare", "skin", "haircare",
    "official", "store", "fragrances", "fragrance", "perfumes", "perfume",
    "parfums", "parfum",
}

_NON_DIGIT = re.compile(r"\D")
_WS = re.compile(r"\s+")
_PUNCT = re.compile(r"[^\w\s]", flags=re.UNICODE)


def strip_accents(text: str) -> str:
    """'Hermès' -> 'Hermes' (NFKD decomposition, drop combining marks)."""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def clean_ean(value) -> str | None:
    """
    Normalize a barcode to a canonical digit string, or None if implausible.

    Handles tester markers ('...846T'), floats from Excel ('3346131400192.0'),
    and stray whitespace. Returns the digits as a STRING to preserve any
    leading zeros (critical: an EAN is an identifier, not a number).
    """
    if value is None:
        return None
    s = str(value).strip()
    if not s or s.lower() in {"nan", "none"}:
        return None
    # Excel often hands us '3346131400192.0' — drop a trailing .0 before cleaning.
    if s.endswith(".0"):
        s = s[:-2]
    digits = _NON_DIGIT.sub("", s)  # also removes the tester 'T'
    if len(digits) < 6:  # too short to be a real EAN/UPC
        return None
    return digits


def parse_price(value) -> float | None:
    """
    Parse a price cell into a float, robust to currency symbols/codes and to
    European decimal commas. The LAST separator present is treated as decimal.
    """
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    up = s.upper()
    for tok in _CURRENCY_TOKENS:
        up = up.replace(tok.upper(), "")
    up = up.strip().replace(" ", "")
    if not up:
        return None

    has_comma, has_dot = "," in up, "." in up
    if has_comma and has_dot:
        # Whichever appears last is the decimal separator; the other is grouping.
        if up.rfind(",") > up.rfind("."):
            up = up.replace(".", "").replace(",", ".")
        else:
            up = up.replace(",", "")
    elif has_comma:
        # Only a comma → treat as the decimal separator ("255,00" -> "255.00").
        up = up.replace(",", ".")
    try:
        val = float(up)
    except ValueError:
        return None
    return val if val > 0 else None


def parse_qty(value) -> int | None:
    """'24 units' / '60 pcs' / 'x50' / '150' -> int. None if no number found."""
    if value is None:
        return None
    s = str(value).strip().lower()
    m = re.search(r"\d[\d.,]*", s)
    if not m:
        return None
    num = m.group(0).replace(",", "").split(".")[0]
    try:
        return int(num)
    except ValueError:
        return None


# ml per unit for the volume units we see; used for like-for-like size compare.
_OZ_ML = 29.5735


def parse_size_ml(value) -> float | None:
    """Extract a comparable volume in ml from '100ml' / '1.7 oz' / '50 ml'."""
    if value is None:
        return None
    s = str(value).strip().lower()
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*(ml|oz|g|l)\b", s)
    if not m:
        m = re.search(r"(\d+(?:[.,]\d+)?)\s*(ml|oz|g|l)", s)
    if not m:
        return None
    num = float(m.group(1).replace(",", "."))
    unit = m.group(2)
    if unit == "ml" or unit == "g":
        return num
    if unit == "l":
        return num * 1000
    if unit == "oz":
        return round(num * _OZ_ML, 1)
    return None


def _collapse_doubled(tokens: list[str]) -> list[str]:
    """'electimuss electimuss london' -> 'electimuss london' (drop immediate dup)."""
    out: list[str] = []
    for t in tokens:
        if out and out[-1] == t:
            continue
        out.append(t)
    return out


def _collapse_initialisms(tokens: list[str]) -> list[str]:
    """Merge runs of single-char tokens: ['y','s','l'] -> ['ysl'], keep the rest."""
    out: list[str] = []
    run: list[str] = []
    for t in tokens:
        if len(t) == 1 and t.isalnum():
            run.append(t)
            continue
        if run:
            out.append("".join(run))
            run = []
        out.append(t)
    if run:
        out.append("".join(run))
    return out


def normalize_brand(value) -> str:
    """
    Canonical surface form for matching: lowercase, de-accented, de-punctuated,
    whitespace-collapsed, '&'->'and', immediate-duplicate and trailing-noise
    tokens removed. Returns '' for empty/garbage input.

    Examples:
      'Hermès Paris'        -> 'hermes'
      'Y.S.L.'              -> 'ysl'
      'Dolce & Gabbana'     -> 'dolce and gabbana'
      'Electimuss '         -> 'electimuss'
      'Sisley Paris'        -> 'sisley'
    """
    if value is None:
        return ""
    s = str(value).strip()
    if not s or s.lower() in {"nan", "none"}:
        return ""
    s = strip_accents(s).lower().replace("&", " and ")
    s = _PUNCT.sub(" ", s)
    s = _WS.sub(" ", s).strip()
    if not s:
        return ""
    tokens = _collapse_initialisms(_collapse_doubled(s.split(" ")))
    # Strip trailing noise suffixes, but never reduce to nothing.
    while len(tokens) > 1 and tokens[-1] in _BRAND_NOISE_SUFFIX:
        tokens.pop()
    return " ".join(tokens)


def is_junk_row(*cells) -> bool:
    """A row is junk if it carries a banner/marker instead of data."""
    joined = " ".join(str(c) for c in cells if c is not None).strip().lower()
    if not joined:
        return True
    return joined.startswith("***") or "stock offer" in joined and "valid" in joined
