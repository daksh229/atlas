"""
radar.py — HONEST Retailer Radar. A real BeautifulSoup parser runs against a
local fixture shaped like a retailer page; other retailers are clearly-labelled
mock data. Same parser code works on a live URL.
"""

import os
import re

import pandas as pd

from app.core.config import settings
from app.core.database import run_query

FIXTURE = os.path.join(settings.DATA_DIR, "samples", "retailer_sample.html")

MOCK_FEED = [
    {"retailer": "ScentWorld (mock)",  "brand": "Maison Luxe",     "product": "Lumière Dorée EDP 100ml",          "price": 124.0, "stock": "In stock"},
    {"retailer": "ScentWorld (mock)",  "brand": "Arabian Essence", "product": "Velvet Oud EDP 50ml",              "price": 159.0, "stock": "In stock"},
    {"retailer": "BeautyHub (mock)",   "brand": "Glow Lab",        "product": "Retinol Night Cream 50ml",         "price": 71.0,  "stock": "Low stock"},
    {"retailer": "BeautyHub (mock)",   "brand": "HydraLux",        "product": "Hyaluronic Acid Moisturiser 50ml", "price": 42.0,  "stock": "In stock"},
    {"retailer": "ParfumDirect (mock)","brand": "Floral Studio",   "product": "Jasmine Soir EDP 75ml",            "price": 92.0,  "stock": "Out of stock"},
    {"retailer": "ParfumDirect (mock)","brand": "Maison Luxe",     "product": "Noir Mystique EDP 75ml",           "price": 99.0,  "stock": "In stock"},
    {"retailer": "GlowMarket (mock)",  "brand": "Colour Story",    "product": "Matte Lipstick Collection (12pc)", "price": 89.0,  "stock": "In stock"},
]


def _price(text: str) -> float | None:
    m = re.search(r"[\d]+[.,]?\d*", text.replace(",", "."))
    return float(m.group(0)) if m else None


def scrape_fixture(path: str = FIXTURE) -> pd.DataFrame:
    from bs4 import BeautifulSoup

    with open(path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")
    rows = []
    for card in soup.select(".product-card"):
        rows.append({
            "retailer": "LuxeScent (live parser)",
            "brand": card.select_one(".brand").get_text(strip=True),
            "product": card.select_one(".title").get_text(strip=True),
            "price": _price(card.select_one(".price").get_text(strip=True)),
            "stock": card.select_one(".stock").get_text(strip=True),
        })
    return pd.DataFrame(rows)


def radar(include_mock: bool = True) -> pd.DataFrame:
    scraped = scrape_fixture()
    if include_mock:
        scraped = pd.concat([scraped, pd.DataFrame(MOCK_FEED)], ignore_index=True)
    return scraped


def compare_to_catalog(feed: pd.DataFrame | None = None) -> pd.DataFrame:
    feed = radar() if feed is None else feed
    cat = run_query("SELECT name, brand, unit_price FROM products")
    cat_by_name = {(r["name"], r["brand"]): r["unit_price"] for _, r in cat.iterrows()}
    rows = []
    for _, r in feed.iterrows():
        our = cat_by_name.get((r["product"], r["brand"]))
        gap = round(r["price"] - our, 2) if our is not None and r["price"] else None
        rows.append({
            "retailer": r["retailer"], "brand": r["brand"], "product": r["product"],
            "retail_price": r["price"], "our_list_price": our, "gap_vs_us": gap, "stock": r["stock"],
            "signal": ("🟢 We undercut" if gap is not None and gap > 0
                       else "🔴 Retailer cheaper" if gap is not None and gap < 0 else "—"),
        })
    return pd.DataFrame(rows)
