"""
offers.py — parse the three deliberately-different supplier offer formats into
one common offer-line schema.

The three files mirror a trader's reality:
  - offer_1: a fairly clean table (has explicit brand/ean/currency/date columns),
             but with messy brand spellings and one USD row hidden among EUR.
  - offer_2: a messy broker list — junk banner row, brand doubled inside the
             ITEM text, no brand/currency columns, prices as '€51.39'/'12.25 EUR'
             /'59,94', quantities as '24 units'/'x50'/'60 pcs'. Currency = EUR.
  - offer_3: a formal price list with MOQ/warehouse; currency is USD (the column
             is literally 'Unit Price USD').

EAN is the primary join, so brand extraction is best-effort (mainly for display
and as a fallback). Each line is currency-normalized to EUR.
"""

from __future__ import annotations

import os

import pandas as pd

from data.pipeline.config import PATHS
from data.pipeline.normalize.brands import BrandDictionary
from data.pipeline.normalize.clean import (
    clean_ean, is_junk_row, normalize_brand, parse_price, parse_qty,
)
from data.pipeline.normalize.currency import CurrencyConverter


def _line(source, supplier, brand_surface, brand_id, ean, product, size,
          qty, price, currency, date, fx) -> dict:
    conv = fx.to_eur(price, currency, date)
    return {
        "source_file": source,
        "supplier_name": supplier,
        "brand_surface": brand_surface,
        "brand_id": brand_id,
        "ean": ean,
        "product_name": product,
        "size": size,
        "qty": qty,
        "unit_price": price,
        "currency": currency,
        "unit_price_eur": conv.amount_eur,
        "offer_date": date,
        "is_comparable": conv.is_comparable,
    }


def _extract_brand_from_item(item: str, bd: BrandDictionary) -> tuple[str, str | None]:
    """offer_2 has no brand column; the brand is the (often doubled) ITEM prefix.
    Try the longest leading prefix (1..4 tokens) that resolves in the dictionary."""
    tokens = str(item).split()
    best: tuple[str, str | None] = (tokens[0] if tokens else "", None)
    for n in range(min(4, len(tokens)), 0, -1):
        surface = " ".join(tokens[:n])
        bid = bd.resolve(surface)
        if bid:
            return surface, bid
    return best


def _adapter_offer_1(path, bd, fx) -> list[dict]:
    df = pd.read_csv(path, dtype={"ean": "string"})
    rows = []
    for r in df.itertuples(index=False):
        ean = clean_ean(r.ean)
        brand_surface = str(r.brand)
        rows.append(_line(
            "offer_1", str(r.supplier_name), brand_surface, bd.resolve(brand_surface),
            ean, str(r.product_name), str(r.size),
            parse_qty(r.qty_available), parse_price(r.price_per_unit),
            str(r.currency).strip().upper(), str(r.offer_date)[:10], fx,
        ))
    return rows


def _adapter_offer_2(path, bd, fx) -> list[dict]:
    df = pd.read_csv(path, dtype={"EAN CODE": "string"})
    df = df.rename(columns={"ITEM": "item", "EAN CODE": "ean", "PCS": "pcs", "PRICE (EUR)": "price"})
    rows = []
    for r in df.itertuples(index=False):
        if is_junk_row(r.item, r.ean, r.pcs, r.price):
            continue
        brand_surface, bid = _extract_brand_from_item(r.item, bd)
        rows.append(_line(
            "offer_2", "(broker list)", brand_surface, bid,
            clean_ean(r.ean), str(r.item), None,
            parse_qty(r.pcs), parse_price(r.price), "EUR", None, fx,
        ))
    return rows


def _adapter_offer_3(path, bd, fx) -> list[dict]:
    df = pd.read_csv(path, dtype={"Barcode": "string"})
    df = df.rename(columns={
        "Supplier": "supplier", "Brand": "brand", "Description": "description",
        "Barcode": "ean", "Volume": "volume", "Stock": "stock", "Unit Price USD": "price",
    })
    rows = []
    for r in df.itertuples(index=False):
        brand_surface = str(r.brand)
        rows.append(_line(
            "offer_3", str(r.supplier), brand_surface, bd.resolve(brand_surface),
            clean_ean(r.ean), str(r.description),
            str(r.volume), parse_qty(r.stock), parse_price(r.price), "USD", None, fx,
        ))
    return rows


_ADAPTERS = {
    "offer_1_supplier.csv": _adapter_offer_1,
    "offer_2_supplier.csv": _adapter_offer_2,
    "offer_3_supplier.csv": _adapter_offer_3,
}


def load_offers(bd: BrandDictionary, fx: CurrencyConverter | None = None) -> dict:
    """Parse all three offers → {'offers': [...], 'report': {per-file counts}}."""
    fx = fx or CurrencyConverter.load()
    all_rows: list[dict] = []
    report: dict[str, dict] = {}
    for path in PATHS.offers:
        name = os.path.basename(path)
        rows = _ADAPTERS[name](path, bd, fx)
        all_rows.extend(rows)
        report[name] = {
            "lines": len(rows),
            "ean_present": sum(1 for x in rows if x["ean"]),
            "brand_resolved": sum(1 for x in rows if x["brand_id"]),
            "eur_comparable": sum(1 for x in rows if x["is_comparable"]),
        }
    return {"offers": all_rows, "report": report}
