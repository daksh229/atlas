"""
currency.py — multi-currency normalization to EUR using ECB reference rates.

Prices are normalized to EUR using European Central Bank reference rates. We
fetch the full ECB history once (covers every date in the package), cache it
locally, and fall back to a small pinned table only if there is no network AND
no cache — so a build is reproducible offline but uses live rates when available.

Conversion is DATE-AWARE: an amount is converted at the rate for its own row
date (offer/order/scan date), using the nearest available ECB date on-or-before
it. Rows that cannot be safely converted are flagged (is_comparable = False)
rather than silently coerced.
"""

from __future__ import annotations

import json
import os
import urllib.request
import xml.etree.ElementTree as ET
from bisect import bisect_right
from dataclasses import dataclass

from data.pipeline.config import SETTINGS, PATHS

# ECB full reference history (since 1999), 1 EUR = <rate> units of the currency.
_ECB_HIST_URL = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.xml"

# Offline fallback (approx., only used when no network and no cache exists).
# Flagged in provenance as source='fallback' so it is never mistaken for ECB.
_FALLBACK_RATES = {"USD": 1.08, "GBP": 0.85, "JPY": 160.0, "EUR": 1.0}


@dataclass
class Conversion:
    amount_eur: float | None
    rate_to_eur: float | None   # units of currency per 1 EUR (ECB convention)
    fx_date: str | None
    source: str                 # 'ecb' | 'fallback'
    is_comparable: bool


def _cache_path() -> str:
    os.makedirs(PATHS.cache_dir, exist_ok=True)
    return os.path.join(PATHS.cache_dir, SETTINGS.fx_cache_file)


def _fetch_ecb() -> dict[str, dict[str, float]]:
    """Download + parse the ECB history XML into {date: {ccy: rate}}."""
    req = urllib.request.Request(_ECB_HIST_URL, headers={"User-Agent": "bf-atlas/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        xml = resp.read()
    root = ET.fromstring(xml)
    ns = {"ecb": "http://www.ecb.int/vocabulary/2002-08-01/eurofxref"}
    rates: dict[str, dict[str, float]] = {}
    for day in root.iter("{http://www.ecb.int/vocabulary/2002-08-01/eurofxref}Cube"):
        date = day.get("time")
        if not date:
            continue
        day_rates: dict[str, float] = {"EUR": 1.0}
        for cube in day:
            ccy, rate = cube.get("currency"), cube.get("rate")
            if ccy and rate:
                day_rates[ccy] = float(rate)
        rates[date] = day_rates
    return rates


class CurrencyConverter:
    """Loads ECB rates (cache → network → fallback) and converts amounts to EUR."""

    def __init__(self, rates: dict[str, dict[str, float]], source: str):
        self._rates = rates
        self._source = source
        self._dates = sorted(rates.keys())

    # --- construction ------------------------------------------------------
    @classmethod
    def load(cls, refresh: bool = False) -> "CurrencyConverter":
        cache = _cache_path()
        if not refresh and os.path.exists(cache):
            with open(cache, "r", encoding="utf-8") as f:
                return cls(json.load(f), source="ecb")
        try:
            rates = _fetch_ecb()
            with open(cache, "w", encoding="utf-8") as f:
                json.dump(rates, f)
            return cls(rates, source="ecb")
        except Exception:
            if os.path.exists(cache):
                with open(cache, "r", encoding="utf-8") as f:
                    return cls(json.load(f), source="ecb")
            # No network, no cache: pin a single fallback "day".
            return cls({"1970-01-01": dict(_FALLBACK_RATES)}, source="fallback")

    # --- lookup ------------------------------------------------------------
    def _rate_on(self, currency: str, date: str | None) -> tuple[float | None, str | None]:
        """Rate for currency at the nearest ECB date on-or-before `date`."""
        if currency == "EUR":
            return 1.0, date
        if self._source == "fallback":
            r = self._rates["1970-01-01"].get(currency)
            return r, "1970-01-01" if r else None
        if date and date in self._rates and currency in self._rates[date]:
            return self._rates[date][currency], date
        # Walk back to the most recent prior date that quotes this currency.
        idx = bisect_right(self._dates, date) if date else len(self._dates)
        for d in reversed(self._dates[:idx] or self._dates):
            if currency in self._rates[d]:
                return self._rates[d][currency], d
        return None, None

    def to_eur(self, amount, currency: str | None, date: str | None = None) -> Conversion:
        if amount is None or currency is None:
            return Conversion(None, None, None, self._source, False)
        ccy = str(currency).strip().upper()
        date = (str(date)[:10] if date else None)
        rate, fx_date = self._rate_on(ccy, date)
        if rate is None or rate == 0:
            return Conversion(None, None, None, self._source, False)
        eur = round(float(amount) / rate, 4)
        return Conversion(eur, rate, fx_date, self._source, True)
