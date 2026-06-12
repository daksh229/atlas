"""SQLite access: pooled-ish connections, region filter helper, read-only executor."""

import sqlite3

import pandas as pd

from app.core.config import settings

ALL_REGIONS = "All regions"


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def run_query(sql: str, params: tuple = ()) -> pd.DataFrame:
    """Run a trusted internal query, return a DataFrame."""
    with get_conn() as conn:
        return pd.read_sql_query(sql, conn, params=params)


def run_select_readonly(sql: str) -> pd.DataFrame:
    """Execute agent-generated SQL on a read-only connection (defence in depth)."""
    uri = f"file:{settings.DB_PATH}?mode=ro"
    with sqlite3.connect(uri, uri=True) as conn:
        return pd.read_sql_query(sql, conn)


def region_clause(region, column: str = "region") -> tuple[str, tuple]:
    """(sql_fragment, params) for an optional region filter. None/All = no filter."""
    if not region or region == ALL_REGIONS:
        return "", ()
    return f" AND {column} = ?", (region,)


def regions() -> list[str]:
    df = run_query("SELECT DISTINCT region FROM traders ORDER BY region")
    return [ALL_REGIONS] + df["region"].tolist()
