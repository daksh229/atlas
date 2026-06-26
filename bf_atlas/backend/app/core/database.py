"""SQLite access + small query helpers (trader-owned model, no region partition)."""

import sqlite3

import pandas as pd

from app.core.config import settings


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def run_query(sql: str, params: tuple = ()) -> pd.DataFrame:
    """Run a trusted internal query, return a DataFrame."""
    with get_conn() as conn:
        return pd.read_sql_query(sql, conn, params=params)


def scalar(sql: str, params: tuple = ()):
    with get_conn() as conn:
        row = conn.execute(sql, params).fetchone()
        return row[0] if row else None


def traders() -> pd.DataFrame:
    return run_query("SELECT id, name, team, role FROM traders ORDER BY team, name")
