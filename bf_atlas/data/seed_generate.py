"""
seed_generate.py — self-contained richer dataset generator for BF Atlas.

No external deps (no Faker). Deterministic (seeded). Produces a region-balanced
dataset so every region has a meaningful, *different* dashboard — which is what
the region-based RBAC demo needs.

Output:  data/trading_data.json   (consumed by init_db.py)
Run:     python seed_generate.py
"""

import json
import os
import random
import uuid
from datetime import datetime, timedelta

random.seed(42)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "trading_data.json")
TODAY = datetime(2026, 6, 12)

REGIONS = ["EU-West", "Asia-Pacific", "Americas", "Middle-East", "Southeast-Asia"]

WAREHOUSES = {
    "EU-West": "Rotterdam Warehouse",
    "Asia-Pacific": "Singapore Hub",
    "Americas": "Miami Distribution",
    "Middle-East": "Dubai Logistics",
    "Southeast-Asia": "Bangkok Center",
}

# Regional name pools give the data local flavour per team.
NAMES = {
    "EU-West": (["Sophie", "Marco", "Anna", "James", "Elena", "David", "Lukas", "Marta", "Pieter", "Ingrid"],
                ["Laurent", "Ricci", "Kowalski", "Thornton", "Petrov", "Van Berg", "Müller", "Silva", "De Vries", "Larsson"]),
    "Asia-Pacific": (["Priya", "Hiroshi", "Wei", "Siti", "Mei", "Kenji", "Anjali", "Jin", "Ravi", "Yuki"],
                     ["Nair", "Tanaka", "Zhang", "Rahmat", "Lin", "Sato", "Sharma", "Park", "Kumar", "Watanabe"]),
    "Americas": (["Carlos", "Maria", "Tyler", "Laura", "Diego", "Emily", "Rafael", "Sofia", "Brandon", "Camila"],
                 ["Mendes", "Gonzalez", "Brooks", "Simmons", "Torres", "Carter", "Souza", "Reyes", "Walker", "Rivera"]),
    "Middle-East": (["Fatima", "Omar", "Aisha", "Yusuf", "Layla", "Khalid", "Mariam", "Hassan", "Noor", "Tariq"],
                    ["Al-Rashid", "Khalid", "Mansoor", "Hassan", "Haddad", "Nasser", "Saleh", "Aziz", "Farouk", "Rahman"]),
    "Southeast-Asia": (["Nurul", "Budi", "Malee", "Ravi", "Linh", "Arif", "Sari", "Than", "Dewi", "Kiet"],
                       ["Aziz", "Santoso", "Charoenwong", "Kumar", "Nguyen", "Hassan", "Putri", "Win", "Lestari", "Tran"]),
}

COUNTRIES = {
    "EU-West": ["Netherlands", "France", "Germany", "Belgium", "Spain", "Italy", "Poland"],
    "Asia-Pacific": ["Japan", "China", "India", "South Korea", "Australia", "Singapore"],
    "Americas": ["USA", "Brazil", "Canada", "Mexico", "Argentina", "Chile"],
    "Middle-East": ["UAE", "Saudi Arabia", "Qatar", "Egypt", "Jordan", "Kuwait"],
    "Southeast-Asia": ["Indonesia", "Thailand", "Vietnam", "Malaysia", "Philippines"],
}

COMPANY_PREFIX = ["Aurora", "Lumen", "Vela", "Orient", "Coastal", "Summit", "Maple", "Crescent",
                  "Pioneer", "Atlas", "Nordic", "Azure", "Golden", "Silk", "Pearl", "Cobalt",
                  "Verdant", "Harbor", "Zenith", "Ember"]
COMPANY_SUFFIX = ["Beauty Group", "Distribution", "Retail Co", "Trading", "Cosmetics", "Brands",
                  "Imports", "Partners", "Holdings", "& Co", "Perfumery", "Stores"]

PRODUCTS = [
    {"name": "Lumière Dorée EDP 100ml",        "category": "perfume",   "brand": "Maison Luxe",     "sku": "PF-001", "cost": 45.00, "price": 120.00},
    {"name": "Noir Mystique EDP 75ml",          "category": "perfume",   "brand": "Maison Luxe",     "sku": "PF-002", "cost": 38.00, "price": 95.00},
    {"name": "Rose Eternelle EDP 50ml",         "category": "perfume",   "brand": "Floral Studio",   "sku": "PF-003", "cost": 28.00, "price": 75.00},
    {"name": "Oud Royale EDP 100ml",            "category": "perfume",   "brand": "Arabian Essence", "sku": "PF-004", "cost": 65.00, "price": 180.00},
    {"name": "Citrus Bloom EDT 125ml",          "category": "perfume",   "brand": "Floral Studio",   "sku": "PF-005", "cost": 22.00, "price": 58.00},
    {"name": "Velvet Oud EDP 50ml",             "category": "perfume",   "brand": "Arabian Essence", "sku": "PF-006", "cost": 55.00, "price": 145.00},
    {"name": "Aqua Marine EDT 100ml",           "category": "perfume",   "brand": "Blue Ocean Co",   "sku": "PF-007", "cost": 18.00, "price": 48.00},
    {"name": "Jasmine Soir EDP 75ml",           "category": "perfume",   "brand": "Floral Studio",   "sku": "PF-008", "cost": 32.00, "price": 88.00},
    {"name": "Amber Nights EDP 100ml",          "category": "perfume",   "brand": "Maison Luxe",     "sku": "PF-009", "cost": 50.00, "price": 135.00},
    {"name": "Cedar & Smoke EDP 50ml",          "category": "perfume",   "brand": "Artisan Blend",   "sku": "PF-010", "cost": 42.00, "price": 110.00},
    {"name": "Vitamin C Brightening Serum 30ml","category": "skincare",  "brand": "Glow Lab",        "sku": "SK-001", "cost": 12.00, "price": 45.00},
    {"name": "Retinol Night Cream 50ml",        "category": "skincare",  "brand": "Glow Lab",        "sku": "SK-002", "cost": 18.00, "price": 65.00},
    {"name": "Hyaluronic Acid Moisturiser 50ml","category": "skincare",  "brand": "HydraLux",        "sku": "SK-003", "cost": 10.00, "price": 38.00},
    {"name": "SPF50 Sunscreen 100ml",           "category": "skincare",  "brand": "SunShield Pro",   "sku": "SK-004", "cost": 8.00,  "price": 28.00},
    {"name": "Collagen Eye Cream 15ml",         "category": "skincare",  "brand": "HydraLux",        "sku": "SK-005", "cost": 15.00, "price": 55.00},
    {"name": "AHA Exfoliating Toner 200ml",     "category": "skincare",  "brand": "Glow Lab",        "sku": "SK-006", "cost": 9.00,  "price": 32.00},
    {"name": "Niacinamide Serum 30ml",          "category": "skincare",  "brand": "HydraLux",        "sku": "SK-007", "cost": 7.00,  "price": 25.00},
    {"name": "Matte Lipstick Collection (12pc)","category": "cosmetics", "brand": "Colour Story",    "sku": "CM-001", "cost": 35.00, "price": 85.00},
    {"name": "HD Foundation SPF15 30ml",        "category": "cosmetics", "brand": "Colour Story",    "sku": "CM-002", "cost": 14.00, "price": 42.00},
    {"name": "Volumising Mascara 12ml",         "category": "cosmetics", "brand": "Lash Queen",      "sku": "CM-003", "cost": 8.00,  "price": 28.00},
    {"name": "Contour Palette Pro",             "category": "cosmetics", "brand": "Colour Story",    "sku": "CM-004", "cost": 22.00, "price": 65.00},
    {"name": "Eyeshadow Palette 18 Shades",     "category": "cosmetics", "brand": "Colour Story",    "sku": "CM-005", "cost": 28.00, "price": 72.00},
    {"name": "Setting Powder Translucent 20g",  "category": "cosmetics", "brand": "Lash Queen",      "sku": "CM-006", "cost": 10.00, "price": 35.00},
    {"name": "Argan Oil Hair Serum 100ml",      "category": "haircare",  "brand": "Silk & Shine",    "sku": "HC-001", "cost": 11.00, "price": 38.00},
    {"name": "Keratin Shampoo 300ml",           "category": "haircare",  "brand": "Silk & Shine",    "sku": "HC-002", "cost": 9.00,  "price": 28.00},
    {"name": "Deep Conditioning Mask 200ml",    "category": "haircare",  "brand": "Silk & Shine",    "sku": "HC-003", "cost": 8.00,  "price": 25.00},
    {"name": "Shea Body Butter 250ml",          "category": "bodycare",  "brand": "Natura Soft",     "sku": "BC-001", "cost": 7.00,  "price": 22.00},
    {"name": "Coffee Body Scrub 300g",          "category": "bodycare",  "brand": "Natura Soft",     "sku": "BC-002", "cost": 6.00,  "price": 20.00},
    {"name": "Rose Hip Body Oil 100ml",         "category": "bodycare",  "brand": "Natura Soft",     "sku": "BC-003", "cost": 9.00,  "price": 30.00},
    {"name": "Luxury Bath Salts 500g",          "category": "bodycare",  "brand": "Natura Soft",     "sku": "BC-004", "cost": 5.00,  "price": 18.00},
]

DEAL_STAGES = ["lead", "qualified", "proposal", "negotiation", "won", "lost"]
DEAL_PROB = {"lead": 10, "qualified": 25, "proposal": 50, "negotiation": 75, "won": 100, "lost": 0}

# Per-region scale knobs (deliberately uneven so dashboards differ).
TRADERS_PER_REGION = 9          # 1 manager + 8 traders each → 45 total
ORDERS_PER_REGION = {"EU-West": 320, "Asia-Pacific": 280, "Americas": 300,
                     "Middle-East": 180, "Southeast-Asia": 160}     # 1240 total
CONTACTS_PER_REGION = {"EU-West": 70, "Asia-Pacific": 55, "Americas": 60,
                       "Middle-East": 40, "Southeast-Asia": 35}     # 260 total
DEALS_PER_REGION = {"EU-West": 130, "Asia-Pacific": 110, "Americas": 120,
                    "Middle-East": 75, "Southeast-Asia": 65}        # 500 total


def company_name() -> str:
    return f"{random.choice(COMPANY_PREFIX)} {random.choice(COMPANY_SUFFIX)}"


def generate():
    data = {k: [] for k in ["traders", "products", "inventory", "orders",
                            "order_items", "crm_contacts", "crm_deals"]}

    # Traders — balanced per region, first one per region is the manager.
    region_traders: dict[str, list[str]] = {r: [] for r in REGIONS}
    used_emails = set()
    for region in REGIONS:
        firsts, lasts = NAMES[region]
        for i in range(TRADERS_PER_REGION):
            name = f"{firsts[i % len(firsts)]} {lasts[(i * 3) % len(lasts)]}"
            base = name.lower().replace(" ", ".").replace("-", "")
            email = f"{base}@bfuturist.com"
            n = 1
            while email in used_emails:
                n += 1
                email = f"{base}{n}@bfuturist.com"
            used_emails.add(email)
            tid = str(uuid.uuid4())
            region_traders[region].append(tid)
            data["traders"].append({
                "id": tid, "name": name, "email": email, "region": region,
                "role": "manager" if i == 0 else "trader",
            })

    # Products + per-region inventory (varied so low-stock differs by region).
    product_ids = {}
    for p in PRODUCTS:
        pid = str(uuid.uuid4())
        product_ids[p["sku"]] = pid
        margin = round((p["price"] - p["cost"]) / p["price"] * 100, 2)
        data["products"].append({
            "id": pid, "odoo_id": random.randint(1000, 9999), "name": p["name"],
            "category": p["category"], "brand": p["brand"], "sku": p["sku"],
            "unit_price": p["price"], "cost_price": p["cost"], "margin_pct": margin,
        })
        for region, warehouse in WAREHOUSES.items():
            qty = random.randint(0, 480)
            reserved = random.randint(0, min(60, qty)) if qty else 0
            data["inventory"].append({
                "id": str(uuid.uuid4()), "product_id": pid, "warehouse": warehouse,
                "region": region, "qty_on_hand": qty, "qty_reserved": reserved,
                "qty_available": qty - reserved, "low_stock_threshold": 50,
            })

    # Orders + line items, per region.
    order_counter = 10000
    for region in REGIONS:
        for _ in range(ORDERS_PER_REGION[region]):
            tid = random.choice(region_traders[region])
            order_date = TODAY - timedelta(days=random.randint(0, 365))
            status = random.choices(["confirmed", "shipped", "delivered", "cancelled"],
                                    weights=[15, 25, 55, 5])[0]
            picks = random.sample(PRODUCTS, random.randint(1, 6))
            total = margin_total = 0
            oid = str(uuid.uuid4())
            for prod in picks:
                qty = random.randint(10, 220)
                line = qty * prod["price"]
                total += line
                margin_total += qty * (prod["price"] - prod["cost"])
                data["order_items"].append({
                    "id": str(uuid.uuid4()), "order_id": oid,
                    "product_id": product_ids[prod["sku"]], "qty": qty,
                    "unit_price": prod["price"], "line_total": round(line, 2),
                })
            data["orders"].append({
                "id": oid, "odoo_id": order_counter, "trader_id": tid,
                "trader_region": region, "customer_name": company_name(),
                "region": region, "total_amount": round(total, 2),
                "margin_amount": round(margin_total, 2), "status": status,
                "order_date": order_date.strftime("%Y-%m-%d"),
            })
            order_counter += 1

    # CRM contacts, per region.
    region_contacts: dict[str, list[str]] = {r: [] for r in REGIONS}
    nh = 1000
    for region in REGIONS:
        for _ in range(CONTACTS_PER_REGION[region]):
            cid = str(uuid.uuid4())
            region_contacts[region].append(cid)
            tid = random.choice(region_traders[region])
            comp = company_name()
            data["crm_contacts"].append({
                "id": cid, "nethunt_id": f"nh-contact-{nh}", "company_name": comp,
                "contact_name": f"{random.choice(NAMES[region][0])} {random.choice(NAMES[region][1])}",
                "email": f"contact@{comp.split()[0].lower()}.com",
                "country": random.choice(COUNTRIES[region]), "region": region, "trader_id": tid,
            })
            nh += 1

    # CRM deals, per region.
    nd = 2000
    for region in REGIONS:
        for _ in range(DEALS_PER_REGION[region]):
            cid = random.choice(region_contacts[region])
            tid = random.choice(region_traders[region])
            stage = random.choices(DEAL_STAGES, weights=[15, 20, 25, 15, 15, 10])[0]
            data["crm_deals"].append({
                "id": str(uuid.uuid4()), "nethunt_id": f"nh-deal-{nd}", "contact_id": cid,
                "trader_id": tid,
                "deal_name": f"{company_name()} — {random.choice(['Q3 Restock', 'Annual Supply', 'Launch Order', 'Trial Order', 'Bulk Purchase'])}",
                "stage": stage, "value": round(random.uniform(5000, 150000), 2),
                "probability": DEAL_PROB[stage],
                "expected_close": (TODAY + timedelta(days=random.randint(-30, 90))).strftime("%Y-%m-%d"),
                "last_activity": (TODAY - timedelta(days=random.randint(0, 45))).strftime("%Y-%m-%d %H:%M:%S"),
                "region": region,
            })
            nd += 1

    return data


if __name__ == "__main__":
    data = generate()
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print("=== BF Atlas richer dataset generated ===")
    for k, v in data.items():
        print(f"  {k:14s} {len(v)}")
    # Per-region order spread (sanity check).
    from collections import Counter
    print("  orders/region:", dict(Counter(o["region"] for o in data["orders"])))
    print(f"\nSaved to: {OUT}")
