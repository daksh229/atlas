"""Read-only SQL guard. We never trust model-generated SQL — this validates it."""

import re

_FORBIDDEN = re.compile(
    r"\b(insert|update|delete|drop|alter|create|replace|truncate|"
    r"attach|detach|pragma|vacuum|reindex|grant|revoke)\b",
    re.IGNORECASE,
)


def strip_sql(text: str) -> str:
    """Pull SQL out of a possible ```sql fence and drop a trailing ';'."""
    fenced = re.search(r"```(?:sql)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    sql = fenced.group(1) if fenced else text
    return sql.strip().rstrip(";").strip()


def is_safe_select(sql: str) -> tuple[bool, str]:
    """Allow exactly one read-only SELECT/WITH statement."""
    s = sql.strip()
    if not s:
        return False, "Empty query."
    if ";" in s.rstrip(";"):
        return False, "Multiple SQL statements are not allowed."
    if not re.match(r"(?is)^\s*(select|with)\b", s):
        return False, "Only SELECT queries are allowed."
    if _FORBIDDEN.search(s):
        return False, "Query contains a non-read-only keyword."
    return True, ""
