# B Futurist — AI Data Intelligence Platform
## POC Implementation Plan (Phase 0 — 4–5 Day Trial Task)

---

## Overview

**Client:** B Futurist, Rotterdam  
**Stack:** Python 3.12 + FastAPI + PostgreSQL 16 + React 18 + TypeScript + Claude API  
**Integrations:** Odoo ERP (read-only) + NetHunt CRM (two-way)  
**POC Goal:** Demonstrate end-to-end data flow — sync → store → AI query → dashboard

---

## POC Scope (Trial Task — 4–5 Days)

The POC proves three things:
1. We can pull data from Odoo and NetHunt into PostgreSQL cleanly
2. Claude can answer natural language queries over that data
3. A React dashboard can surface it to traders

---

## Day-by-Day Execution Plan

### Day 1 — Project Scaffold + Database
- FastAPI project setup (async, Pydantic v2, Alembic)
- PostgreSQL schema creation
- Sample data seeder (perfume/cosmetics trading data)
- Docker Compose for local dev

### Day 2 — Odoo Integration (Read-Only)
- Odoo JSON-RPC client
- Pull: products, inventory, orders
- Store into PostgreSQL with sync logging
- Scheduled pull via APScheduler

### Day 3 — NetHunt CRM Integration (Two-Way)
- NetHunt REST API client
- Pull: contacts, deals, pipelines
- Webhook listener for real-time updates
- Write-back: update deal stage from platform

### Day 4 — Claude AI Layer (Text-to-SQL + Insights)
- Natural language → SQL pipeline via Claude API
- LangGraph agent for multi-source queries
- Trader insights summarization endpoint
- Query history logging

### Day 5 — React Dashboard + Polish
- Unified trader dashboard (KPIs, charts)
- NL query interface (chat-style)
- Regional filter (5 teams)
- Demo-ready with sample data

---

## Project Structure

```
bfuturist-platform/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── auth.py
│   │   │   └── database.py
│   │   ├── routers/
│   │   │   ├── traders.py
│   │   │   ├── inventory.py
│   │   │   ├── crm.py
│   │   │   ├── ai.py
│   │   │   └── reports.py
│   │   ├── services/
│   │   │   ├── odoo_client.py
│   │   │   ├── nethunt_client.py
│   │   │   ├── claude_service.py
│   │   │   └── text_to_sql.py
│   │   ├── models/
│   │   │   └── all ORM models
│   │   ├── schemas/
│   │   │   └── all Pydantic schemas
│   │   └── tasks/
│   │       └── sync_tasks.py
│   ├── alembic/
│   ├── seed_data/
│   │   └── sample_trading_data.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── api/
│   └── package.json
├── docker-compose.yml
└── README.md
```

---

## Database Schema

```sql
-- Traders / Users
CREATE TABLE traders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    region VARCHAR(50) NOT NULL,  -- EU-West, Asia, Americas, MEA, APAC
    team_id UUID,
    role VARCHAR(20) DEFAULT 'trader',  -- trader, manager, admin
    created_at TIMESTAMP DEFAULT NOW()
);

-- Products (from Odoo)
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    odoo_id INTEGER UNIQUE,
    name VARCHAR(200) NOT NULL,
    category VARCHAR(100),  -- perfume, cosmetics, skincare
    brand VARCHAR(100),
    sku VARCHAR(50),
    unit_price DECIMAL(10,2),
    cost_price DECIMAL(10,2),
    margin_pct DECIMAL(5,2),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Inventory (from Odoo)
CREATE TABLE inventory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID REFERENCES products(id),
    warehouse VARCHAR(100),
    region VARCHAR(50),
    qty_on_hand INTEGER DEFAULT 0,
    qty_reserved INTEGER DEFAULT 0,
    qty_available INTEGER DEFAULT 0,
    low_stock_threshold INTEGER DEFAULT 50,
    synced_at TIMESTAMP DEFAULT NOW()
);

-- Orders (from Odoo)
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    odoo_id INTEGER UNIQUE,
    trader_id UUID REFERENCES traders(id),
    customer_name VARCHAR(200),
    region VARCHAR(50),
    total_amount DECIMAL(12,2),
    margin_amount DECIMAL(12,2),
    status VARCHAR(50),
    order_date DATE,
    created_at TIMESTAMP DEFAULT NOW()
) PARTITION BY RANGE (order_date);

-- Order Line Items
CREATE TABLE order_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID REFERENCES orders(id),
    product_id UUID REFERENCES products(id),
    qty INTEGER,
    unit_price DECIMAL(10,2),
    line_total DECIMAL(12,2)
);

-- CRM Contacts (from NetHunt)
CREATE TABLE crm_contacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nethunt_id VARCHAR(100) UNIQUE,
    company_name VARCHAR(200),
    contact_name VARCHAR(100),
    email VARCHAR(100),
    country VARCHAR(100),
    region VARCHAR(50),
    trader_id UUID REFERENCES traders(id),
    created_at TIMESTAMP DEFAULT NOW()
);

-- CRM Deals (from NetHunt — two-way)
CREATE TABLE crm_deals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nethunt_id VARCHAR(100) UNIQUE,
    contact_id UUID REFERENCES crm_contacts(id),
    trader_id UUID REFERENCES traders(id),
    deal_name VARCHAR(200),
    stage VARCHAR(50),  -- lead, qualified, proposal, negotiation, won, lost
    value DECIMAL(12,2),
    probability INTEGER,
    expected_close DATE,
    last_activity TIMESTAMP,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Sync Log
CREATE TABLE sync_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source VARCHAR(50),  -- odoo, nethunt
    entity VARCHAR(50),  -- products, inventory, orders, deals
    records_synced INTEGER,
    status VARCHAR(20),  -- success, partial, failed
    error_msg TEXT,
    synced_at TIMESTAMP DEFAULT NOW()
);

-- AI Query Log
CREATE TABLE ai_query_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trader_id UUID REFERENCES traders(id),
    nl_query TEXT,
    generated_sql TEXT,
    result_summary TEXT,
    latency_ms INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## Key Code — Odoo Client

```python
# services/odoo_client.py
import httpx
from typing import Any

class OdooClient:
    def __init__(self, url: str, db: str, username: str, password: str):
        self.url = url
        self.db = db
        self.uid = None
        self._authenticate(username, password)

    def _authenticate(self, username: str, password: str):
        response = httpx.post(f"{self.url}/web/dataset/call_kw", json={
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "service": "common",
                "method": "authenticate",
                "args": [self.db, username, password, {}]
            }
        })
        self.uid = response.json()["result"]

    def search_read(self, model: str, domain: list, fields: list) -> list[dict]:
        response = httpx.post(f"{self.url}/web/dataset/call_kw", json={
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "service": "object",
                "method": "execute_kw",
                "args": [self.db, self.uid, self.password, model,
                         "search_read", [domain], {"fields": fields}]
            }
        })
        return response.json()["result"]

    async def pull_products(self) -> list[dict]:
        return self.search_read(
            "product.template",
            [["active", "=", True]],
            ["id", "name", "categ_id", "list_price", "standard_price"]
        )

    async def pull_inventory(self) -> list[dict]:
        return self.search_read(
            "stock.quant",
            [["location_id.usage", "=", "internal"]],
            ["product_id", "location_id", "quantity", "reserved_quantity"]
        )
```

---

## Key Code — Claude Text-to-SQL

```python
# services/text_to_sql.py
import anthropic
from app.core.database import get_db

SCHEMA_CONTEXT = """
Tables available:
- products (id, name, category, brand, sku, unit_price, cost_price, margin_pct)
- inventory (product_id, warehouse, region, qty_available, low_stock_threshold)
- orders (id, trader_id, customer_name, region, total_amount, margin_amount, status, order_date)
- order_items (order_id, product_id, qty, unit_price, line_total)
- crm_deals (id, trader_id, deal_name, stage, value, probability, expected_close, last_activity)
- traders (id, name, region, team_id)
"""

client = anthropic.Anthropic()

async def nl_to_sql(query: str, trader_region: str) -> dict:
    """Convert natural language to SQL, execute, return results + summary."""

    # Step 1: Generate SQL
    sql_response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        system=f"""You are a SQL expert for a perfume/cosmetics trading platform.
        {SCHEMA_CONTEXT}
        Rules:
        - Always filter by region = '{trader_region}' unless user asks for global view
        - Return ONLY the SQL query, no explanation
        - Use parameterized-style queries
        - Never use DELETE, UPDATE, DROP
        """,
        messages=[{"role": "user", "content": f"Convert to SQL: {query}"}]
    )

    sql = sql_response.content[0].text.strip()

    # Step 2: Execute SQL
    async with get_db() as db:
        result = await db.execute(sql)
        rows = result.fetchall()

    # Step 3: Summarize results
    summary_response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=500,
        messages=[{
            "role": "user",
            "content": f"Query: {query}\nResults: {rows}\nGive a 2-3 sentence business insight."
        }]
    )

    return {
        "sql": sql,
        "rows": rows,
        "summary": summary_response.content[0].text,
        "count": len(rows)
    }
```

---

## Key Code — FastAPI AI Router

```python
# routers/ai.py
from fastapi import APIRouter, Depends
from app.services.text_to_sql import nl_to_sql
from app.core.auth import get_current_trader

router = APIRouter(prefix="/ai", tags=["AI"])

@router.post("/query")
async def natural_language_query(
    query: str,
    current_trader = Depends(get_current_trader)
):
    """Accept NL query, return SQL + results + insight summary."""
    result = await nl_to_sql(query, current_trader.region)
    return {
        "query": query,
        "sql": result["sql"],
        "data": result["rows"],
        "insight": result["summary"],
        "count": result["count"]
    }

@router.get("/insights/daily")
async def daily_trader_insights(
    current_trader = Depends(get_current_trader)
):
    """Claude-generated daily briefing for the trader."""
    # Pull today's data, generate narrative summary
    ...
```

---

## NetHunt Webhook Handler

```python
# routers/webhooks.py
from fastapi import APIRouter, Request
import hmac, hashlib

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

@router.post("/nethunt")
async def nethunt_webhook(request: Request):
    """Handle real-time NetHunt CRM updates."""
    payload = await request.json()

    event_type = payload.get("event")  # deal.updated, contact.created, etc.
    record_id = payload.get("recordId")

    if event_type == "deal.updated":
        await sync_deal_from_nethunt(record_id)
    elif event_type == "contact.created":
        await sync_contact_from_nethunt(record_id)

    return {"status": "ok"}
```

---

## Sample Data Available

Since Odoo/NetHunt won't be accessible during POC, we generate realistic sample data:

- **50 perfume/cosmetics SKUs** across 5 categories
- **5 regional warehouses** with inventory levels
- **200 orders** over last 6 months
- **24 trader profiles** across 5 regions
- **150 CRM deals** at various pipeline stages
- **100 contacts** across Europe, Asia, Americas

Run: `python seed_data/sample_trading_data.py`

---

## POC Demo Flow

1. Trader logs in → sees their regional dashboard
2. KPI cards: Revenue MTD, Open Deals, Low Stock Alerts, Win Rate
3. Types: *"Which fragrances are low stock AND have open deals?"*
4. Claude returns: table of SKUs + natural language insight
5. Manager view: cross-region comparison chart

---

## Environment Variables

```env
# Backend
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/bfuturist
ANTHROPIC_API_KEY=sk-ant-...
ODOO_URL=https://client.odoo.com
ODOO_DB=bfuturist
ODOO_USER=api@bfuturist.com
ODOO_PASSWORD=...
NETHUNT_API_KEY=...
NETHUNT_WEBHOOK_SECRET=...

# AWS (Production)
AWS_REGION=eu-central-1
AWS_S3_BUCKET=bfuturist-platform
```

---

## Docker Compose (Local Dev)

```yaml
version: "3.9"
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_DB: bfuturist
      POSTGRES_USER: dev
      POSTGRES_PASSWORD: dev
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  backend:
    build: ./backend
    command: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    environment:
      DATABASE_URL: postgresql+asyncpg://dev:dev@db/bfuturist
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
```

---

## What We Deliver at POC End

| Deliverable | Status |
|---|---|
| Working FastAPI backend | ✅ |
| PostgreSQL schema + migrations | ✅ |
| Odoo mock client + real client scaffold | ✅ |
| NetHunt mock client + webhook handler | ✅ |
| Claude Text-to-SQL endpoint | ✅ |
| Sample data seeder (perfume/trading) | ✅ |
| React dashboard (regional KPIs) | ✅ |
| NL query interface | ✅ |
| Docker Compose local setup | ✅ |
| README with setup instructions | ✅ |
