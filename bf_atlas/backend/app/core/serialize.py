"""JSON-safe conversion of pandas frames (NaN → null, numpy types → native)."""

import json

import pandas as pd


def to_records(df: pd.DataFrame) -> list[dict]:
    """DataFrame → list[dict] that is always JSON-serialisable.

    df.to_json handles NaN→null and numpy int/float→native; json.loads returns
    clean Python objects.
    """
    if df is None or df.empty:
        return []
    return json.loads(df.to_json(orient="records"))


def int_counts(counts: dict) -> dict:
    """Coerce value_counts()-style numpy ints to plain ints."""
    return {str(k): int(v) for k, v in counts.items()}
