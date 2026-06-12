"""
sync.py — MOCK Odoo + NetHunt sync. Re-pulls from SQLite and writes a sync_log
row per entity so the dashboard can show a freshness story. Real clients (Odoo
JSON-RPC, NetHunt REST + webhooks) slot in behind run_sync() in Phase 1.
"""

from datetime import datetime

from app.core.database import get_conn

SOURCES = {
    "odoo": ["products", "inventory", "orders"],
    "nethunt": ["crm_contacts", "crm_deals"],
}


def run_sync(source: str) -> list[dict]:
    if source not in SOURCES:
        raise ValueError(f"Unknown source: {source}")
    results = []
    with get_conn() as conn:
        for entity in SOURCES[source]:
            n = conn.execute(f"SELECT COUNT(*) FROM {entity}").fetchone()[0]
            conn.execute(
                """INSERT INTO sync_log (source, entity, records_synced, status, error_msg, synced_at)
                   VALUES (?,?,?,?,?,?)""",
                (source, entity, n, "success", None,
                 datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            )
            results.append({"entity": entity, "records": n, "status": "success"})
        conn.commit()
    return results


def run_all_syncs() -> dict:
    return {src: run_sync(src) for src in SOURCES}


def last_sync_status() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT source, entity, records_synced, status, synced_at
               FROM sync_log s
               WHERE synced_at = (SELECT MAX(synced_at) FROM sync_log
                                  WHERE source=s.source AND entity=s.entity)
               ORDER BY source, entity"""
        ).fetchall()
        return [dict(r) for r in rows]
