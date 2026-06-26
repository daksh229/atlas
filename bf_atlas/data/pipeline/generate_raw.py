"""
generate_raw.py — produce the RAW (intentionally messy) seed for BF Atlas.

"Raw" means it looks like data that just arrived from different systems:
  - brand names appear as RANDOM surface forms (canonical OR an alias), so the
    preprocessing step has real alias-resolution work to do (§9 brand dictionary).
  - entities carry stable string refs (cust-001, prod-001, …), NOT resolved IDs.

It writes one JSON file per source into  data/pipeline/raw/ .
preprocess.py then canonicalises and load_db.py loads the result.

The data is PLANTED: five specific scenarios are hand-built so that every alert
type in Atlas demonstrably fires on a fresh database. Random background data is
layered on top so the lists/screens are never empty.

Scale (POC): 5 traders / 2 teams, 50 brands, ~2 products per brand.
Run:  python generate_raw.py
"""

import json
import os
import random
from datetime import datetime, timedelta

from brands import BRANDS, all_surface_forms

random.seed(42)

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
TODAY = datetime(2026, 6, 16)  # fixed "now" so the demo is stable

# ── Traders: 5 across 2 teams ────────────────────────────────────────────────
TRADERS = [
    {"id": "t1", "name": "Sophie Laurent", "team": "Aurora", "role": "trader"},
    {"id": "t2", "name": "Marco Ricci",    "team": "Aurora", "role": "trader"},
    {"id": "t3", "name": "Anna Kowalski",  "team": "Aurora", "role": "trader"},
    {"id": "t4", "name": "David Chen",     "team": "Zenith", "role": "trader"},
    {"id": "t5", "name": "Layla Hassan",   "team": "Zenith", "role": "trader"},
]
TRADER_IDS = [t["id"] for t in TRADERS]

WAREHOUSE = "Rotterdam Warehouse"

COMPANY_PREFIX = ["Aurora", "Lumen", "Vela", "Orient", "Coastal", "Summit", "Maple",
                  "Crescent", "Pioneer", "Atlas", "Nordic", "Azure", "Golden", "Silk",
                  "Pearl", "Cobalt", "Verdant", "Harbor", "Zenith", "Ember", "Bright",
                  "Royal", "Metro", "Grand", "Prime"]
COMPANY_SUFFIX = ["Beauty Group", "Distribution", "Retail Co", "Trading", "Cosmetics",
                  "Brands", "Imports", "Partners", "Holdings", "Perfumery", "Stores"]
COUNTRIES = ["Netherlands", "France", "Germany", "Belgium", "Spain", "Italy", "UAE",
             "Saudi Arabia", "USA", "Brazil", "Japan", "South Korea", "Singapore"]
RETAILERS = ["ScentWorld", "BeautyHub", "ParfumDirect", "GlowMarket", "LuxeScent"]
STOCK_STATES = ["In stock", "In stock", "In stock", "Low stock", "Out of stock"]


def _d(days_ago: int) -> str:
    return (TODAY - timedelta(days=days_ago)).strftime("%Y-%m-%d")


def _dt(days_ago: int) -> str:
    return (TODAY - timedelta(days=days_ago)).strftime("%Y-%m-%d %H:%M:%S")


def company() -> str:
    return f"{random.choice(COMPANY_PREFIX)} {random.choice(COMPANY_SUFFIX)}"


def surface(canonical: str) -> str:
    """A random spelling of a brand (canonical or an alias) — the messy real world."""
    return random.choice(all_surface_forms(canonical))


# Reference price bands per category (per-unit, EUR) for synthetic costs/prices.
PRICE_BAND = {
    "perfume":   (35, 120),
    "skincare":  (8, 45),
    "cosmetics": (10, 60),
    "haircare":  (9, 40),
    "bodycare":  (6, 30),
}
FORMS = {
    "perfume":   ["EDP 50ml", "EDP 100ml", "EDT 75ml", "EDT 125ml"],
    "skincare":  ["Serum 30ml", "Night Cream 50ml", "Moisturiser 50ml", "Cleanser 200ml"],
    "cosmetics": ["Lipstick", "Foundation 30ml", "Palette 12pc", "Mascara 12ml"],
    "haircare":  ["Shampoo 300ml", "Conditioner 300ml", "Hair Oil 100ml", "Mask 200ml"],
    "bodycare":  ["Body Lotion 250ml", "Body Scrub 300g", "Shower Gel 250ml", "Body Oil 100ml"],
}


def build():
    partners, products, inventory = [], [], []
    sale_orders, purchase_orders = [], []
    demand_signals, supply_signals, retailer_prices = [], [], []

    # ── Partners: clients + suppliers, each owned by a trader ─────────────────
    clients, suppliers = [], []
    for i in range(1, 41):  # 40 clients
        cid = f"cust-{i:03d}"
        clients.append(cid)
        partners.append({
            "id": cid, "name": company(), "is_customer": 1, "is_supplier": 0,
            "owner_trader_id": random.choice(TRADER_IDS),
            "country": random.choice(COUNTRIES), "ref": f"odoo-partner-{2000+i}",
            "email": f"buyer{i}@example.com",
        })
    for i in range(1, 21):  # 20 suppliers
        sid = f"supp-{i:03d}"
        suppliers.append(sid)
        partners.append({
            "id": sid, "name": company(), "is_customer": 0, "is_supplier": 1,
            "owner_trader_id": random.choice(TRADER_IDS),
            "country": random.choice(COUNTRIES), "ref": f"odoo-partner-{4000+i}",
            "email": f"supplier{i}@example.com",
        })

    # ── Products: ~2 per brand, with synthetic cost/list price ───────────────
    brand_products: dict[str, list[str]] = {}
    pc = 0
    for canonical, category, _aliases in BRANDS:
        brand_products[canonical] = []
        for _ in range(random.randint(1, 3)):
            pc += 1
            pid = f"prod-{pc:03d}"
            lo, hi = PRICE_BAND[category]
            cost = round(random.uniform(lo, hi), 2)
            price = round(cost * random.uniform(1.8, 3.0), 2)
            products.append({
                "id": pid, "brand_surface": surface(canonical), "category": category,
                "name": f"{canonical.split()[0]} {random.choice(FORMS[category])}",
                "sku": f"{category[:2].upper()}-{pc:04d}",
                "list_price": price, "cost_price": cost, "ref": f"odoo-prod-{1000+pc}",
            })
            brand_products[canonical].append(pid)
            # inventory: most products in stock, some low/zero
            on_hand = random.choice([0, 0, 40, 120, 300, 600])
            reserved = random.randint(0, min(50, on_hand)) if on_hand else 0
            inventory.append({
                "id": f"inv-{pc:03d}", "product_id": pid, "warehouse": WAREHOUSE,
                "qty_on_hand": on_hand, "qty_reserved": reserved,
                "qty_available": on_hand - reserved, "reorder_min": 50,
            })

    product_brand = {}  # pid -> canonical (for order lines)
    for canonical, pids in brand_products.items():
        for pid in pids:
            product_brand[pid] = canonical
    prod_by_id = {p["id"]: p for p in products}

    # ── Background sale & purchase orders ────────────────────────────────────
    soc = poc = 0

    def add_sale_order(partner_id, trader_id, picks, days_ago, ref=None):
        nonlocal soc
        soc += 1
        oid = ref or f"so-{soc:04d}"
        lines, total, margin = [], 0.0, 0.0
        for pid in picks:
            p = prod_by_id[pid]
            qty = random.randint(20, 200)
            sub = round(qty * p["list_price"], 2)
            total += sub
            margin += qty * (p["list_price"] - p["cost_price"])
            lines.append({"product_id": pid, "brand_surface": surface(product_brand[pid]),
                          "qty": qty, "unit_price": p["list_price"], "subtotal": sub})
        sale_orders.append({
            "id": oid, "ref": f"S{10000+soc}", "partner_id": partner_id,
            "trader_id": trader_id, "order_date": _d(days_ago),
            "state": random.choices(["done", "confirmed", "cancel"], weights=[70, 25, 5])[0],
            "amount_total": round(total, 2), "margin_amount": round(margin, 2),
            "lines": lines,
        })
        return oid

    def add_purchase_order(partner_id, trader_id, picks, days_ago):
        nonlocal poc
        poc += 1
        oid = f"po-{poc:04d}"
        lines, total = [], 0.0
        for pid in picks:
            p = prod_by_id[pid]
            qty = random.randint(50, 400)
            unit = round(p["cost_price"] * random.uniform(1.0, 1.15), 2)
            sub = round(qty * unit, 2)
            total += sub
            lines.append({"product_id": pid, "brand_surface": surface(product_brand[pid]),
                          "qty": qty, "unit_price": unit, "subtotal": sub})
        purchase_orders.append({
            "id": oid, "ref": f"P{20000+poc}", "partner_id": partner_id,
            "trader_id": trader_id, "order_date": _d(days_ago),
            "state": "done", "amount_total": round(total, 2), "lines": lines,
        })
        return oid

    all_pids = list(product_brand)
    for _ in range(150):
        cid = random.choice(clients)
        owner = next(p for p in partners if p["id"] == cid)["owner_trader_id"]
        add_sale_order(cid, owner, random.sample(all_pids, random.randint(1, 4)),
                       random.randint(1, 300))
    for _ in range(60):
        sid = random.choice(suppliers)
        owner = next(p for p in partners if p["id"] == sid)["owner_trader_id"]
        add_purchase_order(sid, owner, random.sample(all_pids, random.randint(1, 4)),
                           random.randint(1, 300))

    # ── Background demand & supply signals ───────────────────────────────────
    canon_names = [b[0] for b in BRANDS]
    for _ in range(70):
        cid = random.choice(clients)
        owner = next(p for p in partners if p["id"] == cid)["owner_trader_id"]
        canonical = random.choice(canon_names)
        pid = random.choice(brand_products[canonical])
        ref_price = prod_by_id[pid]["list_price"]
        demand_signals.append({
            "brand_surface": surface(canonical), "partner_id": cid, "trader_id": owner,
            "target_price": round(ref_price * random.uniform(0.8, 1.1), 2),
            "wanted_qty": random.choice([50, 100, 150, 300]),
            "fired_at": _d(random.randint(0, 40)), "source": "crm",
        })
    for _ in range(50):
        sid = random.choice(suppliers)
        owner = next(p for p in partners if p["id"] == sid)["owner_trader_id"]
        canonical = random.choice(canon_names)
        pid = random.choice(brand_products[canonical])
        ref_cost = prod_by_id[pid]["cost_price"]
        supply_signals.append({
            "brand_surface": surface(canonical), "partner_id": sid, "trader_id": owner,
            "offer_price": round(ref_cost * random.uniform(1.0, 1.3), 2),
            "available_qty": random.randint(100, 2000),
            "fired_at": _d(random.randint(0, 40)), "source": "supplier",
        })

    # ── Background retailer scan rows ────────────────────────────────────────
    for _ in range(28):
        canonical = random.choice(canon_names)
        pid = random.choice(brand_products[canonical])
        retailer_prices.append({
            "retailer": random.choice(RETAILERS), "brand_surface": surface(canonical),
            "product_name": prod_by_id[pid]["name"],
            "price": round(prod_by_id[pid]["list_price"] * random.uniform(1.0, 1.6), 2),
            "stock_status": random.choice(STOCK_STATES),
            "scanned_at": _d(random.randint(0, 5)), "is_mock": 1,
        })
    # one deliberately UNKNOWN brand → must be flagged, never force-matched
    retailer_prices.append({
        "retailer": "ScentWorld", "brand_surface": "Mystère de Paris",
        "product_name": "Mystère de Paris EDP 100ml", "price": 88.0,
        "stock_status": "In stock", "scanned_at": _d(1), "is_mock": 1,
    })

    # ════════════════════════════════════════════════════════════════════════
    #  PLANTED SCENARIOS — one per alert type (deterministic, demonstrable)
    # ════════════════════════════════════════════════════════════════════════

    # 1) DEMAND–SUPPLY MATCH (cross-trader): t1's client wants YSL; t4's supplier
    #    offers Saint Laurent (same brand via alias) cheaper → margin → both notified.
    partners.append({"id": "cust-ds", "name": "Aurora Beauty Group", "is_customer": 1,
                     "is_supplier": 0, "owner_trader_id": "t1", "country": "Netherlands",
                     "ref": "odoo-partner-9001", "email": "buyer@aurorabeauty.com"})
    partners.append({"id": "supp-ds", "name": "Étoile Distribution", "is_customer": 0,
                     "is_supplier": 1, "owner_trader_id": "t4", "country": "France",
                     "ref": "odoo-partner-9002", "email": "sales@etoile.fr"})
    demand_signals.append({"brand_surface": "YSL", "partner_id": "cust-ds", "trader_id": "t1",
                           "target_price": 95.0, "wanted_qty": 200, "fired_at": _d(1),
                           "source": "crm"})
    supply_signals.append({"brand_surface": "Saint Laurent", "partner_id": "supp-ds",
                           "trader_id": "t4", "offer_price": 62.0, "available_qty": 500,
                           "fired_at": _d(2), "source": "supplier"})

    # 2) EXTERNAL MARKET WINDOW: a retailer lists Dior high; t2 can supply Dior
    #    (has a supplier offer) below that retail price → t2 notified with numbers.
    partners.append({"id": "supp-emw", "name": "Iberia Fragrance House", "is_customer": 0,
                     "is_supplier": 1, "owner_trader_id": "t2", "country": "Spain",
                     "ref": "odoo-partner-9003", "email": "trade@iberiafragrance.es"})
    supply_signals.append({"brand_surface": "Dior", "partner_id": "supp-emw", "trader_id": "t2",
                           "offer_price": 70.0, "available_qty": 400, "fired_at": _d(3),
                           "source": "supplier"})
    retailer_prices.append({"retailer": "LuxeScent", "brand_surface": "Christian Dior",
                            "product_name": "Dior Sauvage EDP 100ml", "price": 132.0,
                            "stock_status": "In stock", "scanned_at": _d(1), "is_mock": 0})

    # 3) STOCK MATCH: we hold live inventory of Olaplex; t3's client wants it →
    #    fastest deal (no sourcing). High qty_available on an Olaplex product.
    olaplex_pid = brand_products["Olaplex"][0]
    for inv in inventory:
        if inv["product_id"] == olaplex_pid:
            inv.update({"qty_on_hand": 900, "qty_reserved": 100, "qty_available": 800})
    partners.append({"id": "cust-stock", "name": "Coastal Retail Co", "is_customer": 1,
                     "is_supplier": 0, "owner_trader_id": "t3", "country": "Germany",
                     "ref": "odoo-partner-9004", "email": "orders@coastalretail.de"})
    demand_signals.append({"brand_surface": "Olaplex", "partner_id": "cust-stock",
                           "trader_id": "t3", "target_price": round(prod_by_id[olaplex_pid]["list_price"], 2),
                           "wanted_qty": 250, "fired_at": _d(1), "source": "crm"})

    # 4) REORDER REMINDER: t5's client reorders La Roche-Posay ~every 30 days;
    #    last order was 32 days ago → due now. Plant a 3-order cadence.
    partners.append({"id": "cust-reorder", "name": "Summit Perfumery", "is_customer": 1,
                     "is_supplier": 0, "owner_trader_id": "t5", "country": "Belgium",
                     "ref": "odoo-partner-9005", "email": "buying@summitperf.be"})
    lrp_pid = brand_products["La Roche-Posay"][0]
    for days_ago in (92, 62, 32):  # every ~30 days, last 32 days ago → overdue
        add_sale_order("cust-reorder", "t5", [lrp_pid], days_ago)

    # 5) OFFER-TO-REQUEST (the dummy "Offers Inbox"): t2 submits a manual offer
    #    for Chanel; t3's client already requested Chanel → both notified.
    partners.append({"id": "cust-offer", "name": "Pioneer Imports", "is_customer": 1,
                     "is_supplier": 0, "owner_trader_id": "t3", "country": "Italy",
                     "ref": "odoo-partner-9006", "email": "purchasing@pioneerimports.it"})
    chanel_pid = brand_products["Chanel"][0]
    demand_signals.append({"brand_surface": "Chanel", "partner_id": "cust-offer",
                           "trader_id": "t3", "target_price": round(prod_by_id[chanel_pid]["list_price"] * 0.95, 2),
                           "wanted_qty": 180, "fired_at": _d(4), "source": "crm"})
    supply_signals.append({"brand_surface": "Chanel", "partner_id": None, "trader_id": "t2",
                           "offer_price": round(prod_by_id[chanel_pid]["cost_price"] * 1.1, 2),
                           "available_qty": 300, "fired_at": _d(0), "source": "manual_offer"})

    return {
        "traders": TRADERS, "partners": partners, "products": products,
        "inventory": inventory, "sale_orders": sale_orders,
        "purchase_orders": purchase_orders, "demand_signals": demand_signals,
        "supply_signals": supply_signals, "retailer_prices": retailer_prices,
    }


def main():
    os.makedirs(RAW, exist_ok=True)
    data = build()
    for name, rows in data.items():
        with open(os.path.join(RAW, f"{name}.json"), "w", encoding="utf-8") as f:
            json.dump(rows, f, indent=2, ensure_ascii=False)
    print("=== raw seed generated → data/pipeline/raw/ ===")
    for name, rows in data.items():
        print(f"  {name:18s} {len(rows)}")


if __name__ == "__main__":
    main()
