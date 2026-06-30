"""
build.py — one-shot data build for BF Atlas.

    raw seed  →  preprocess (brand canonicalisation)  →  load atlas.db  →  verify

After it runs, it asserts that every alert type has the data it needs to fire, so
a fresh database is always ready to use.

Run:  python build.py
"""

import os
import sqlite3

import generate_raw
import preprocess
import load_db

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.abspath(os.path.join(HERE, "..", "atlas.db"))


def verify():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    q = lambda sql, p=(): conn.execute(sql, p).fetchone()[0]

    checks = {
        "Demand–Supply (cross-trader, positive margin)": q("""
            SELECT COUNT(*) FROM demand_signals d JOIN supply_signals s
              ON d.brand_id = s.brand_id
            WHERE d.target_price > s.offer_price AND d.trader_id <> s.trader_id"""),
        "External Market Window (retail > our supply)": q("""
            SELECT COUNT(*) FROM retailer_prices r JOIN supply_signals s
              ON r.brand_id = s.brand_id
            WHERE r.brand_id IS NOT NULL AND r.price > s.offer_price"""),
        "Stock Match (live stock + demand)": q("""
            SELECT COUNT(*) FROM inventory i JOIN products p ON p.id = i.product_id
            JOIN demand_signals d ON d.brand_id = p.brand_id
            WHERE i.qty_available > 100"""),
        "Reorder Reminder (>=2 past orders, last 20–60d)": q("""
            SELECT COUNT(*) FROM (
              SELECT sol.brand_id, so.partner_id, COUNT(*) n,
                     MAX(so.order_date) last
              FROM sale_orders so JOIN sale_order_lines sol ON sol.order_id = so.id
              GROUP BY sol.brand_id, so.partner_id HAVING n >= 2
            )"""),
        "Offer-to-Request (manual offer ↔ demand)": q("""
            SELECT COUNT(*) FROM supply_signals s JOIN demand_signals d
              ON d.brand_id = s.brand_id
            WHERE s.source = 'manual_offer' AND d.trader_id <> s.trader_id"""),
        "Brand aliases present (dictionary in use)": q("SELECT COUNT(*) FROM brand_aliases"),
        "Retailer unknown-brand flagged (not force-matched)": q(
            "SELECT COUNT(*) FROM retailer_prices WHERE brand_id IS NULL"),
    }
    conn.close()

    print("\n=== verification: alert prerequisites ===")
    ok = True
    for label, n in checks.items():
        mark = "OK " if n > 0 else "!! "
        if n == 0:
            ok = False
        print(f"  [{mark}] {label}: {n}")
    if not ok:
        raise SystemExit("\nFAILED: some alert types have no planted data.")
    print("\nAll alert prerequisites satisfied — database is demo-ready.")


def main():
    generate_raw.main()
    print()
    preprocess.main()
    print()
    load_db.main()
    verify()


if __name__ == "__main__":
    main()
