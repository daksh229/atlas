"""
config.py — the single configuration surface for the BF Atlas data pipeline.

Everything tunable lives here: input paths, the DB path, the base currency, the
FX source, and the margin bands that decide whether an offer is "good". Keeping
this in one place keeps the logic transparent and lets the thresholds be
adjusted without hunting through modules.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))


def _p(*parts: str) -> str:
    return os.path.abspath(os.path.join(PROJECT_ROOT, *parts))


# --- Where the source data package lives -----------------------------------
# Source files sit in "New folder/". They are read read-only and never mutated.
RAW_DIR = _p("New folder")


@dataclass(frozen=True)
class Paths:
    products: str = field(default_factory=lambda: os.path.join(RAW_DIR, "Products_Info.xlsx"))
    sales: str = field(default_factory=lambda: os.path.join(RAW_DIR, "Sales_Order_History.xlsx"))
    purchases: str = field(default_factory=lambda: os.path.join(RAW_DIR, "Purchase_Order_History.xlsx"))
    retailer: str = field(default_factory=lambda: os.path.join(RAW_DIR, "retailer_prices (2).csv"))
    offers: tuple[str, ...] = field(default_factory=lambda: (
        os.path.join(RAW_DIR, "offer_1_supplier.csv"),
        os.path.join(RAW_DIR, "offer_2_supplier.csv"),
        os.path.join(RAW_DIR, "offer_3_supplier.csv"),
    ))

    # Pipeline outputs
    processed_dir: str = field(default_factory=lambda: os.path.join(HERE, "processed"))
    reports_dir: str = field(default_factory=lambda: os.path.join(HERE, "reports"))
    cache_dir: str = field(default_factory=lambda: os.path.join(HERE, ".cache"))
    db_path: str = field(default_factory=lambda: _p("data", "atlas.db"))


@dataclass(frozen=True)
class Settings:
    base_currency: str = "EUR"

    # ECB reference rates (daily, 90-day window). Cached locally with an offline
    # fallback so a build never hard-fails on a network blip.
    ecb_rates_url: str = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist-90d.xml"
    fx_cache_file: str = "ecb_rates.json"

    # Read large files in chunks so memory stays bounded on the full corpus.
    read_chunksize: int = 50_000
    insert_batchsize: int = 5_000

    # "Good offer" margin bands (vs. the conservative resale benchmark, in EUR).
    # These thresholds are surfaced and tunable rather than fixed externally.
    margin_good: float = 0.25       # >= 25% headroom → good
    margin_borderline: float = 0.10  # >= 10% → borderline; below → skip

    # 5 teams for the ~24 traders (assignment is deterministic).
    n_teams: int = 5

    paths: Paths = field(default_factory=Paths)


SETTINGS = Settings()
PATHS = SETTINGS.paths
