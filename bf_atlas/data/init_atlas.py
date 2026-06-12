"""
init_atlas.py — adds the BF Atlas "cross-match" layer to bfuturist.db.

The base sample data (trading_data.json) has products/orders/CRM but NO model of
*who can supply* vs *who wants to buy* a brand — which is what the Atlas
Opportunity Engine matches on. This script synthesises that layer:

  suppliers       companies that offer us brands (the BUY / sourcing side)
  brand_offers    a supplier's offer for a brand: price, qty, recency
  brand_demands   a client's demand for a brand: target price, qty, recency
                  (derived from existing crm_contacts = clients)

An "opportunity" is a brand where some supplier's offer_price is below some
client's target_price (positive margin) — computed live in lib/atlas.py.

NOTE: This is DIRECTIONAL mock data built from the public brief, not BF's real
spec. Run init_db.py first, then this.   Run:  python init_atlas.py
"""

import os
import random
import sqlite3
from datetime import datetime, timedelta

random.seed(7)  # reproducible

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, "bfuturist.db")
TODAY = datetime(2026, 6, 11)  # fixed "now" so the demo is stable

SUPPLIERS = [
    ("Étoile Distribution", "France", "EU-West"),
    ("Maghreb Aromatics", "Morocco", "Middle-East"),
    ("Pearl River Beauty", "China", "Asia-Pacific"),
    ("Nordic Skin Labs", "Sweden", "EU-West"),
    ("Gulf Scent Trading", "UAE", "Middle-East"),
    ("Lima Naturals", "Peru", "Americas"),
    ("Saigon Cosmetics Co", "Vietnam", "Southeast-Asia"),
    ("Iberia Fragrance House", "Spain", "EU-West"),
    ("Tokyo Glow Import", "Japan", "Asia-Pacific"),
    ("Cape Botanicals", "South Africa", "Middle-East"),
    ("Andes Organics", "Chile", "Americas"),
    ("Mekong Beauty Supply", "Thailand", "Southeast-Asia"),
    ("Rhine Cosmetics GmbH", "Germany", "EU-West"),
    ("Seoul Skin Co", "South Korea", "Asia-Pacific"),
    ("Levant Perfumers", "Jordan", "Middle-East"),
]

SCHEMA = """
DROP TABLE IF EXISTS suppliers;
DROP TABLE IF EXISTS brand_offers;
DROP TABLE IF EXISTS brand_demands;

CREATE TABLE suppliers (
    id          TEXT PRIMARY KEY,
    name        TEXT,
    country     TEXT,
    region      TEXT,
    reliability INTEGER          -- 1..100
);

CREATE TABLE brand_offers (
    id            TEXT PRIMARY KEY,
    supplier_id   TEXT REFERENCES suppliers(id),
    brand         TEXT,
    category      TEXT,
    offer_price   REAL,          -- per-unit price the supplier sells to us
    prev_price    REAL,          -- previous offer price (for price-drop alerts)
    min_qty       INTEGER,
    available_qty INTEGER,
    region        TEXT,
    valid_until   TEXT,
    updated_at    TEXT
);

CREATE TABLE brand_demands (
    id            TEXT PRIMARY KEY,
    client_id     TEXT REFERENCES crm_contacts(id),
    trader_id     TEXT REFERENCES traders(id),
    brand         TEXT,
    category      TEXT,
    target_price  REAL,          -- per-unit price the client is willing to pay
    wanted_qty    INTEGER,
    region        TEXT,
    last_activity TEXT
);

CREATE INDEX idx_offers_brand  ON brand_offers(brand);
CREATE INDEX idx_demands_brand ON brand_demands(brand);
"""


def _d(days_ago: int) -> str:
    return (TODAY - timedelta(days=days_ago)).strftime("%Y-%m-%d")


def main() -> None:
    import uuid

    random.seed(7)  # re-seed here so import order (e.g. via init_all) can't shift it

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)

    # Brand reference prices from the existing catalogue.
    brands = conn.execute(
        """SELECT brand, category,
                  AVG(cost_price) AS avg_cost, AVG(unit_price) AS avg_price
           FROM products GROUP BY brand"""
    ).fetchall()
    brand_info = {b["brand"]: b for b in brands}
    brand_names = list(brand_info)

    # --- suppliers + their offers (BUY side) -------------------------------
    supplier_ids = []
    for name, country, region in SUPPLIERS:
        sid = str(uuid.uuid4())
        supplier_ids.append((sid, region))
        conn.execute(
            "INSERT INTO suppliers VALUES (?,?,?,?,?)",
            (sid, name, country, region, random.randint(60, 99)),
        )

    for sid, sregion in supplier_ids:
        for brand in random.sample(brand_names, random.randint(2, 4)):
            info = brand_info[brand]
            base = info["avg_cost"]
            offer = round(base * random.uniform(1.02, 1.30), 2)
            # ~25% of offers had a recent price drop.
            if random.random() < 0.25:
                prev, updated = round(offer * random.uniform(1.08, 1.25), 2), _d(random.randint(0, 3))
            else:
                prev, updated = offer, _d(random.randint(4, 60))
            conn.execute(
                "INSERT INTO brand_offers VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (str(uuid.uuid4()), sid, brand, info["category"], offer, prev,
                 random.choice([50, 100, 200]), random.randint(200, 3000),
                 sregion, _d(-random.randint(20, 120)), updated),
            )

    # --- demands from existing clients (SELL side) -------------------------
    clients = conn.execute(
        "SELECT id, region, trader_id FROM crm_contacts"
    ).fetchall()
    for c in random.sample(clients, min(180, len(clients))):  # clients with active demand
        for brand in random.sample(brand_names, random.randint(1, 3)):
            info = brand_info[brand]
            target = round(info["avg_price"] * random.uniform(0.72, 1.05), 2)
            conn.execute(
                "INSERT INTO brand_demands VALUES (?,?,?,?,?,?,?,?,?)",
                (str(uuid.uuid4()), c["id"], c["trader_id"], brand, info["category"],
                 target, random.choice([50, 100, 150, 300]),
                 c["region"], _d(random.randint(0, 40))),
            )

    conn.commit()
    n_sup = conn.execute("SELECT COUNT(*) FROM suppliers").fetchone()[0]
    n_off = conn.execute("SELECT COUNT(*) FROM brand_offers").fetchone()[0]
    n_dem = conn.execute("SELECT COUNT(*) FROM brand_demands").fetchone()[0]
    conn.close()

    print("=== BF Atlas cross-match layer added ===")
    print(f"  suppliers      {n_sup}")
    print(f"  brand_offers   {n_off}")
    print(f"  brand_demands  {n_dem}")


if __name__ == "__main__":
    main()
