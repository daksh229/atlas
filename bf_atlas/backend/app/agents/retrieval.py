"""
retrieval.py — validates the generated SQL with the read-only guard and executes
it on a read-only connection. Never trusts the model: bad/unsafe SQL is rejected
before the database is touched.
"""

from app.agents.state import AtlasState, make_step
from app.core.database import run_select_readonly
from app.core.serialize import to_records
from app.core.sql_guard import is_safe_select

ROW_CAP = 200  # cap rows returned to the UI


def run(state: AtlasState) -> dict:
    sql = state.get("sql")
    if not sql:
        return {"trace": [make_step("Retrieval", "skipped", "No SQL to run.")]}

    ok, reason = is_safe_select(sql)
    if not ok:
        step = make_step("Retrieval", "blocked unsafe SQL", reason)
        return {"error": f"Blocked unsafe SQL: {reason}", "rows": [], "columns": [],
                "trace": [step]}

    try:
        df = run_select_readonly(sql)
    except Exception as exc:  # noqa: BLE001
        step = make_step("Retrieval", "execution error", str(exc))
        return {"error": f"SQL execution failed: {exc}", "rows": [], "columns": [],
                "trace": [step]}

    rows = to_records(df.head(ROW_CAP))
    step = make_step("Retrieval", "executed read-only",
                     f"{len(df)} rows ({min(len(df), ROW_CAP)} returned)")
    return {"rows": rows, "columns": list(df.columns), "trace": [step]}
