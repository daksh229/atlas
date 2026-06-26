"""
security.py — trader-based session + access control (spec §9).

The spec is explicit and non-negotiable: each trader logs in and sees ONLY their
own clients, suppliers and data. Other traders' accounts are NEVER shown by name —
only aggregate signals (brand, quantity, price) plus which colleague is
responsible. This is enforced SERVER-SIDE, in every data response.

Model:
  - Onboarding picks a trader identity → /auth/session issues a JWT encoding the
    trader_id (+ name, team, role).
  - Every request carries the token; the backend derives the trader from it.
  - `owns()` / `mask_partner()` are the primitives every service uses so the rule
    holds uniformly, not per-endpoint.

Auth is intentionally password-less for the POC (production adds Google OAuth).
"""

from dataclasses import dataclass

import jwt
from fastapi import Depends, Header, HTTPException

from app.core.config import settings
from app.core.database import run_query

ALGO = "HS256"


@dataclass
class Session:
    trader_id: str
    name: str
    team: str
    role: str  # 'trader' | 'manager'

    @property
    def is_manager(self) -> bool:
        return self.role == "manager"


def _trader_row(trader_id: str):
    df = run_query("SELECT id, name, team, role FROM traders WHERE id = ?", (trader_id,))
    return None if df.empty else df.iloc[0]


def create_token(trader_id: str) -> str:
    row = _trader_row(trader_id)
    if row is None:
        raise ValueError(f"Unknown trader: {trader_id}")
    payload = {"trader_id": row["id"], "name": row["name"],
               "team": row["team"], "role": row["role"]}
    return jwt.encode(payload, settings.AUTH_SECRET, algorithm=ALGO)


def decode_token(token: str) -> Session:
    try:
        data = jwt.decode(token, settings.AUTH_SECRET, algorithms=[ALGO])
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail=f"Invalid session token: {exc}")
    return Session(trader_id=data["trader_id"], name=data.get("name", ""),
                   team=data.get("team", ""), role=data.get("role", "trader"))


def get_session(authorization: str | None = Header(default=None)) -> Session:
    """FastAPI dependency. No token → first trader as a convenience default for
    API docs / curl. Production would reject anonymous requests."""
    if not authorization or not authorization.lower().startswith("bearer "):
        df = run_query("SELECT id FROM traders ORDER BY id LIMIT 1")
        if df.empty:
            raise HTTPException(status_code=500, detail="No traders in database.")
        return decode_token(create_token(df.iloc[0]["id"]))
    return decode_token(authorization.split(" ", 1)[1].strip())


# ── access-control primitives every service shares ──────────────────────────

def owns(session: Session, owner_trader_id: str | None) -> bool:
    """True if this session may see the named account. Managers see all."""
    return session.is_manager or owner_trader_id == session.trader_id


def colleague_name(owner_trader_id: str | None) -> str:
    row = _trader_row(owner_trader_id) if owner_trader_id else None
    return row["name"] if row is not None else "another trader"


def mask_partner(session: Session, owner_trader_id: str | None,
                 partner_name: str | None) -> str:
    """Return the partner name if owned, else the responsible colleague instead.

    Implements "other traders' clients/suppliers are never shown by name — only …
    which colleague is responsible". Used everywhere a counterparty is rendered.
    """
    if owns(session, owner_trader_id):
        return partner_name or "—"
    return f"(via {colleague_name(owner_trader_id)})"
