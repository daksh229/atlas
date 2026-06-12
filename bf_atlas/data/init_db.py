"""
init_db.py — Load the generated sample trading data into a SQLite file.

Adapts the PostgreSQL schema from implementation.md to SQLite:
  - UUID columns  -> TEXT
  - DECIMAL       -> REAL
  - no partitioning / no extensions

Run:  python init_db.py
Produces:  bfuturist.db  in the same folder.
"""

import json
import os
import sqlite3

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, "bfuturist.db")

# trading_data.json lives one level up (project root), with a local fallback.
DATA_CANDIDATES = [
    os.path.join(HERE, "trading_data.json"),               # local (richer) seed — preferred
    os.path.join(HERE, "..", "..", "trading_data.json"),   # project root (legacy)
    os.path.join(HERE, "..", "trading_data.json"),
]

SCHEMA = """
DROP TABLE IF EXISTS traders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS inventory;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS crm_contacts;
DROP TABLE IF EXISTS crm_deals;
DROP TABLE IF EXISTS sync_log;

CREATE TABLE traders (
    id      TEXT PRIMARY KEY,
    name    TEXT NOT NULL,
    email   TEXT UNIQUE NOT NULL,
    region  TEXT NOT NULL,
    role    TEXT DEFAULT 'trader'
);

CREATE TABLE products (
    id          TEXT PRIMARY KEY,
    odoo_id     INTEGER,
    name        TEXT NOT NULL,
    category    TEXT,
    brand       TEXT,
    sku         TEXT,
    unit_price  REAL,
    cost_price  REAL,
    margin_pct  REAL
);

CREATE TABLE inventory (
    id                  TEXT PRIMARY KEY,
    product_id          TEXT REFERENCES products(id),
    warehouse           TEXT,
    region              TEXT,
    qty_on_hand         INTEGER DEFAULT 0,
    qty_reserved        INTEGER DEFAULT 0,
    qty_available       INTEGER DEFAULT 0,
    low_stock_threshold INTEGER DEFAULT 50
);

CREATE TABLE orders (
    id              TEXT PRIMARY KEY,
    odoo_id         INTEGER,
    trader_id       TEXT REFERENCES traders(id),
    trader_region   TEXT,
    customer_name   TEXT,
    region          TEXT,
    total_amount    REAL,
    margin_amount   REAL,
    status          TEXT,
    order_date      TEXT
);

CREATE TABLE order_items (
    id          TEXT PRIMARY KEY,
    order_id    TEXT REFERENCES orders(id),
    product_id  TEXT REFERENCES products(id),
    qty         INTEGER,
    unit_price  REAL,
    line_total  REAL
);

CREATE TABLE crm_contacts (
    id           TEXT PRIMARY KEY,
    nethunt_id   TEXT UNIQUE,
    company_name TEXT,
    contact_name TEXT,
    email        TEXT,
    country      TEXT,
    region       TEXT,
    trader_id    TEXT REFERENCES traders(id)
);

CREATE TABLE crm_deals (
    id            TEXT PRIMARY KEY,
    nethunt_id    TEXT UNIQUE,
    contact_id    TEXT REFERENCES crm_contacts(id),
    trader_id     TEXT REFERENCES traders(id),
    deal_name     TEXT,
    stage         TEXT,
    value         REAL,
    probability   INTEGER,
    expected_close TEXT,
    last_activity TEXT,
    region        TEXT
);

-- Populated by the mock Odoo/NetHunt clients to demonstrate the sync story.
CREATE TABLE sync_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    source          TEXT,
    entity          TEXT,
    records_synced  INTEGER,
    status          TEXT,
    error_msg       TEXT,
    synced_at       TEXT
);

CREATE INDEX idx_orders_region ON orders(region);
CREATE INDEX idx_orders_date   ON orders(order_date);
CREATE INDEX idx_inv_region    ON inventory(region);
CREATE INDEX idx_deals_region  ON crm_deals(region);
CREATE INDEX idx_deals_stage   ON crm_deals(stage);
"""

# Columns we insert per table (order matters for the executemany binding).
COLUMNS = {
    "traders": ["id", "name", "email", "region", "role"],
    "products": ["id", "odoo_id", "name", "category", "brand", "sku",
                 "unit_price", "cost_price", "margin_pct"],
    "inventory": ["id", "product_id", "warehouse", "region", "qty_on_hand",
                  "qty_reserved", "qty_available", "low_stock_threshold"],
    "orders": ["id", "odoo_id", "trader_id", "trader_region", "customer_name",
               "region", "total_amount", "margin_amount", "status", "order_date"],
    "order_items": ["id", "order_id", "product_id", "qty", "unit_price", "line_total"],
    "crm_contacts": ["id", "nethunt_id", "company_name", "contact_name", "email",
                     "country", "region", "trader_id"],
    "crm_deals": ["id", "nethunt_id", "contact_id", "trader_id", "deal_name",
                  "stage", "value", "probability", "expected_close",
                  "last_activity", "region"],
}


def find_data_file() -> str:
    for path in DATA_CANDIDATES:
        if os.path.exists(path):
            return os.path.abspath(path)
    raise FileNotFoundError(
        "trading_data.json not found. Looked in: "
        + ", ".join(os.path.abspath(p) for p in DATA_CANDIDATES)
    )


def load(conn: sqlite3.Connection, data: dict) -> dict:
    counts = {}
    for table, cols in COLUMNS.items():
        rows = data.get(table, [])
        placeholders = ", ".join("?" for _ in cols)
        sql = f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({placeholders})"
        conn.executemany(sql, [[r.get(c) for c in cols] for r in rows])
        counts[table] = len(rows)
    conn.commit()
    return counts


def main() -> None:
    data_path = find_data_file()
    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    conn = sqlite3.connect(DB_PATH)
    try:
        conn.executescript(SCHEMA)
        counts = load(conn, data)
    finally:
        conn.close()

    print("=== B Futurist SQLite DB initialised ===")
    print(f"  source: {data_path}")
    print(f"  db:     {DB_PATH}")
    for table, n in counts.items():
        print(f"  {table:14s} {n}")


if __name__ == "__main__":
    main()
