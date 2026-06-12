"""
B Futurist — Sample Trading Data Generator
Generates realistic perfume/cosmetics trading data for POC demo
Run: python seed_data/sample_trading_data.py
"""

import json
import random
from datetime import datetime, timedelta
from faker import Faker
import uuid

fake = Faker()
random.seed(42)

REGIONS = ["EU-West", "Asia-Pacific", "Americas", "Middle-East", "Southeast-Asia"]

TRADERS = [
    {"name": "Sophie Laurent",    "region": "EU-West",        "email": "sophie@bfuturist.com"},
    {"name": "Marco Ricci",       "region": "EU-West",        "email": "marco@bfuturist.com"},
    {"name": "Anna Kowalski",     "region": "EU-West",        "email": "anna@bfuturist.com"},
    {"name": "James Thornton",    "region": "EU-West",        "email": "james@bfuturist.com"},
    {"name": "Priya Nair",        "region": "Asia-Pacific",   "email": "priya@bfuturist.com"},
    {"name": "Hiroshi Tanaka",    "region": "Asia-Pacific",   "email": "hiroshi@bfuturist.com"},
    {"name": "Wei Zhang",         "region": "Asia-Pacific",   "email": "wei@bfuturist.com"},
    {"name": "Siti Rahmat",       "region": "Asia-Pacific",   "email": "siti@bfuturist.com"},
    {"name": "Carlos Mendes",     "region": "Americas",       "email": "carlos@bfuturist.com"},
    {"name": "Maria Gonzalez",    "region": "Americas",       "email": "maria@bfuturist.com"},
    {"name": "Tyler Brooks",      "region": "Americas",       "email": "tyler@bfuturist.com"},
    {"name": "Laura Simmons",     "region": "Americas",       "email": "laura@bfuturist.com"},
    {"name": "Fatima Al-Rashid",  "region": "Middle-East",    "email": "fatima@bfuturist.com"},
    {"name": "Omar Khalid",       "region": "Middle-East",    "email": "omar@bfuturist.com"},
    {"name": "Aisha Mansoor",     "region": "Middle-East",    "email": "aisha@bfuturist.com"},
    {"name": "Yusuf Hassan",      "region": "Middle-East",    "email": "yusuf@bfuturist.com"},
    {"name": "Nurul Aziz",        "region": "Southeast-Asia", "email": "nurul@bfuturist.com"},
    {"name": "Budi Santoso",      "region": "Southeast-Asia", "email": "budi@bfuturist.com"},
    {"name": "Malee Charoenwong", "region": "Southeast-Asia", "email": "malee@bfuturist.com"},
    {"name": "Ravi Kumar",        "region": "Southeast-Asia", "email": "ravi@bfuturist.com"},
    {"name": "David Van Berg",    "region": "EU-West",        "email": "david@bfuturist.com"},  # Davide's team
    {"name": "Elena Petrov",      "region": "EU-West",        "email": "elena@bfuturist.com"},
    {"name": "Kwame Asante",      "region": "Middle-East",    "email": "kwame@bfuturist.com"},
    {"name": "Mei Lin",           "region": "Asia-Pacific",   "email": "meiling@bfuturist.com"},
]

PRODUCTS = [
    # Perfumes
    {"name": "Lumière Dorée EDP 100ml",       "category": "perfume",   "brand": "Maison Luxe",    "sku": "PF-001", "cost": 45.00,  "price": 120.00},
    {"name": "Noir Mystique EDP 75ml",         "category": "perfume",   "brand": "Maison Luxe",    "sku": "PF-002", "cost": 38.00,  "price": 95.00},
    {"name": "Rose Eternelle EDP 50ml",        "category": "perfume",   "brand": "Floral Studio",  "sku": "PF-003", "cost": 28.00,  "price": 75.00},
    {"name": "Oud Royale EDP 100ml",           "category": "perfume",   "brand": "Arabian Essence","sku": "PF-004", "cost": 65.00,  "price": 180.00},
    {"name": "Citrus Bloom EDT 125ml",         "category": "perfume",   "brand": "Floral Studio",  "sku": "PF-005", "cost": 22.00,  "price": 58.00},
    {"name": "Velvet Oud EDP 50ml",            "category": "perfume",   "brand": "Arabian Essence","sku": "PF-006", "cost": 55.00,  "price": 145.00},
    {"name": "Aqua Marine EDT 100ml",          "category": "perfume",   "brand": "Blue Ocean Co",  "sku": "PF-007", "cost": 18.00,  "price": 48.00},
    {"name": "Jasmine Soir EDP 75ml",          "category": "perfume",   "brand": "Floral Studio",  "sku": "PF-008", "cost": 32.00,  "price": 88.00},
    {"name": "Amber Nights EDP 100ml",         "category": "perfume",   "brand": "Maison Luxe",    "sku": "PF-009", "cost": 50.00,  "price": 135.00},
    {"name": "Cedar & Smoke EDP 50ml",         "category": "perfume",   "brand": "Artisan Blend",  "sku": "PF-010", "cost": 42.00,  "price": 110.00},
    # Skincare
    {"name": "Vitamin C Brightening Serum 30ml","category": "skincare", "brand": "Glow Lab",       "sku": "SK-001", "cost": 12.00,  "price": 45.00},
    {"name": "Retinol Night Cream 50ml",        "category": "skincare", "brand": "Glow Lab",       "sku": "SK-002", "cost": 18.00,  "price": 65.00},
    {"name": "Hyaluronic Acid Moisturiser 50ml","category": "skincare", "brand": "HydraLux",       "sku": "SK-003", "cost": 10.00,  "price": 38.00},
    {"name": "SPF50 Sunscreen 100ml",           "category": "skincare", "brand": "SunShield Pro",  "sku": "SK-004", "cost": 8.00,   "price": 28.00},
    {"name": "Collagen Eye Cream 15ml",         "category": "skincare", "brand": "HydraLux",       "sku": "SK-005", "cost": 15.00,  "price": 55.00},
    {"name": "AHA Exfoliating Toner 200ml",     "category": "skincare", "brand": "Glow Lab",       "sku": "SK-006", "cost": 9.00,   "price": 32.00},
    {"name": "Niacinamide Serum 30ml",          "category": "skincare", "brand": "HydraLux",       "sku": "SK-007", "cost": 7.00,   "price": 25.00},
    # Cosmetics
    {"name": "Matte Lipstick Collection (12pc)","category": "cosmetics","brand": "Colour Story",   "sku": "CM-001", "cost": 35.00,  "price": 85.00},
    {"name": "HD Foundation SPF15 30ml",        "category": "cosmetics","brand": "Colour Story",   "sku": "CM-002", "cost": 14.00,  "price": 42.00},
    {"name": "Volumising Mascara 12ml",         "category": "cosmetics","brand": "Lash Queen",     "sku": "CM-003", "cost": 8.00,   "price": 28.00},
    {"name": "Contour Palette Pro",             "category": "cosmetics","brand": "Colour Story",   "sku": "CM-004", "cost": 22.00,  "price": 65.00},
    {"name": "Eyeshadow Palette 18 Shades",     "category": "cosmetics","brand": "Colour Story",   "sku": "CM-005", "cost": 28.00,  "price": 72.00},
    {"name": "Setting Powder Translucent 20g",  "category": "cosmetics","brand": "Lash Queen",     "sku": "CM-006", "cost": 10.00,  "price": 35.00},
    # Hair Care
    {"name": "Argan Oil Hair Serum 100ml",      "category": "haircare", "brand": "Silk & Shine",   "sku": "HC-001", "cost": 11.00,  "price": 38.00},
    {"name": "Keratin Shampoo 300ml",           "category": "haircare", "brand": "Silk & Shine",   "sku": "HC-002", "cost": 9.00,   "price": 28.00},
    {"name": "Deep Conditioning Mask 200ml",    "category": "haircare", "brand": "Silk & Shine",   "sku": "HC-003", "cost": 8.00,   "price": 25.00},
    # Body Care
    {"name": "Shea Body Butter 250ml",          "category": "bodycare", "brand": "Natura Soft",    "sku": "BC-001", "cost": 7.00,   "price": 22.00},
    {"name": "Coffee Body Scrub 300g",          "category": "bodycare", "brand": "Natura Soft",    "sku": "BC-002", "cost": 6.00,   "price": 20.00},
    {"name": "Rose Hip Body Oil 100ml",         "category": "bodycare", "brand": "Natura Soft",    "sku": "BC-003", "cost": 9.00,   "price": 30.00},
    {"name": "Luxury Bath Salts 500g",          "category": "bodycare", "brand": "Natura Soft",    "sku": "BC-004", "cost": 5.00,   "price": 18.00},
]

DEAL_STAGES = ["lead", "qualified", "proposal", "negotiation", "won", "lost"]
DEAL_PROBABILITIES = {"lead": 10, "qualified": 25, "proposal": 50, "negotiation": 75, "won": 100, "lost": 0}

WAREHOUSES = {
    "EU-West":        "Rotterdam Warehouse",
    "Asia-Pacific":   "Singapore Hub",
    "Americas":       "Miami Distribution",
    "Middle-East":    "Dubai Logistics",
    "Southeast-Asia": "Bangkok Center",
}


def generate_data():
    data = {
        "traders": [],
        "products": [],
        "inventory": [],
        "orders": [],
        "order_items": [],
        "crm_contacts": [],
        "crm_deals": [],
    }

    # Traders
    trader_ids = {}
    for t in TRADERS:
        tid = str(uuid.uuid4())
        trader_ids[t["email"]] = tid
        data["traders"].append({
            "id": tid,
            "name": t["name"],
            "email": t["email"],
            "region": t["region"],
            "role": "manager" if t["name"] in ["Sophie Laurent", "Carlos Mendes"] else "trader",
        })

    # Products
    product_ids = {}
    for p in PRODUCTS:
        pid = str(uuid.uuid4())
        product_ids[p["sku"]] = pid
        margin = round(((p["price"] - p["cost"]) / p["price"]) * 100, 2)
        data["products"].append({
            "id": pid,
            "odoo_id": random.randint(1000, 9999),
            "name": p["name"],
            "category": p["category"],
            "brand": p["brand"],
            "sku": p["sku"],
            "unit_price": p["price"],
            "cost_price": p["cost"],
            "margin_pct": margin,
        })

    # Inventory per region
    for p in PRODUCTS:
        pid = product_ids[p["sku"]]
        for region, warehouse in WAREHOUSES.items():
            qty = random.randint(10, 500)
            reserved = random.randint(0, min(50, qty))
            data["inventory"].append({
                "id": str(uuid.uuid4()),
                "product_id": pid,
                "warehouse": warehouse,
                "region": region,
                "qty_on_hand": qty,
                "qty_reserved": reserved,
                "qty_available": qty - reserved,
                "low_stock_threshold": 50,
            })

    # Orders (200 over last 6 months)
    order_ids = []
    for i in range(200):
        trader = random.choice(TRADERS)
        tid = trader_ids[trader["email"]]
        order_date = datetime.now() - timedelta(days=random.randint(1, 180))
        status = random.choices(
            ["confirmed", "shipped", "delivered", "cancelled"],
            weights=[15, 25, 55, 5]
        )[0]

        num_items = random.randint(1, 5)
        selected_products = random.sample(PRODUCTS, num_items)

        total = 0
        margin_total = 0
        items = []
        for prod in selected_products:
            qty = random.randint(10, 200)
            line = qty * prod["price"]
            line_margin = qty * (prod["price"] - prod["cost"])
            total += line
            margin_total += line_margin
            items.append({
                "product_sku": prod["sku"],
                "qty": qty,
                "unit_price": prod["price"],
                "line_total": round(line, 2)
            })

        oid = str(uuid.uuid4())
        order_ids.append(oid)
        data["orders"].append({
            "id": oid,
            "odoo_id": 10000 + i,
            "trader_id": tid,
            "trader_region": trader["region"],
            "customer_name": fake.company(),
            "region": trader["region"],
            "total_amount": round(total, 2),
            "margin_amount": round(margin_total, 2),
            "status": status,
            "order_date": order_date.strftime("%Y-%m-%d"),
        })

        for item in items:
            data["order_items"].append({
                "id": str(uuid.uuid4()),
                "order_id": oid,
                "product_id": product_ids[item["product_sku"]],
                "qty": item["qty"],
                "unit_price": item["unit_price"],
                "line_total": item["line_total"],
            })

    # CRM Contacts (100)
    contact_ids = []
    for i in range(100):
        trader = random.choice(TRADERS)
        cid = str(uuid.uuid4())
        contact_ids.append({"id": cid, "region": trader["region"], "trader_id": trader_ids[trader["email"]]})
        data["crm_contacts"].append({
            "id": cid,
            "nethunt_id": f"nh-contact-{1000+i}",
            "company_name": fake.company(),
            "contact_name": fake.name(),
            "email": fake.company_email(),
            "country": fake.country(),
            "region": trader["region"],
            "trader_id": trader_ids[trader["email"]],
        })

    # CRM Deals (150)
    for i in range(150):
        contact = random.choice(contact_ids)
        stage = random.choices(DEAL_STAGES, weights=[15, 20, 25, 15, 15, 10])[0]
        expected_close = datetime.now() + timedelta(days=random.randint(-30, 90))
        last_activity = datetime.now() - timedelta(days=random.randint(0, 30))

        data["crm_deals"].append({
            "id": str(uuid.uuid4()),
            "nethunt_id": f"nh-deal-{2000+i}",
            "contact_id": contact["id"],
            "trader_id": contact["trader_id"],
            "deal_name": f"{fake.company()} — {random.choice(['Q3 Restock', 'Annual Supply', 'Launch Order', 'Trial Order', 'Bulk Purchase'])}",
            "stage": stage,
            "value": round(random.uniform(5000, 150000), 2),
            "probability": DEAL_PROBABILITIES[stage],
            "expected_close": expected_close.strftime("%Y-%m-%d"),
            "last_activity": last_activity.strftime("%Y-%m-%d %H:%M:%S"),
            "region": contact["region"],
        })

    return data


if __name__ == "__main__":
    data = generate_data()
    with open("seed_data/trading_data.json", "w") as f:
        json.dump(data, f, indent=2)

    print("=== B Futurist Sample Data Generated ===")
    print(f"  Traders:      {len(data['traders'])}")
    print(f"  Products:     {len(data['products'])}")
    print(f"  Inventory:    {len(data['inventory'])} records ({len(PRODUCTS)} SKUs x {len(WAREHOUSES)} regions)")
    print(f"  Orders:       {len(data['orders'])}")
    print(f"  Order Items:  {len(data['order_items'])}")
    print(f"  CRM Contacts: {len(data['crm_contacts'])}")
    print(f"  CRM Deals:    {len(data['crm_deals'])}")
    print("\nSaved to: seed_data/trading_data.json")
