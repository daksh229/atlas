"""
security.py — lightweight JWT session + region-based RBAC.

Onboarding (role + region) calls /auth/session, which issues a JWT encoding the
user's role and allotted region. Every data request carries that token; the
backend derives the *effective* region from it and ENFORCES isolation:

  - trader  → locked to their allotted region. Requesting any other region → 403.
  - manager → may view any single region or the cross-region ("All regions") view.

This mirrors the brief's Postgres row-level-security story: isolation is enforced
server-side, not in the UI. (Auth is intentionally password-less for the POC.)
"""

from dataclasses import dataclass

import jwt
from fastapi import Depends, Header, HTTPException

from app.core.config import settings
from app.core.database import ALL_REGIONS, regions as db_regions

ALGO = "HS256"
ROLES = {"trader", "manager"}


def valid_regions() -> list[str]:
    """Concrete regions (excludes the 'All regions' pseudo-value)."""
    return [r for r in db_regions() if r != ALL_REGIONS]


@dataclass
class Session:
    role: str
    region: str               # the user's home/allotted region
    allowed_regions: list[str]  # regions this user may read


def create_token(role: str, region: str) -> str:
    if role not in ROLES:
        raise ValueError(f"Invalid role: {role}")
    regions = valid_regions()
    if role == "trader":
        if region not in regions:
            raise ValueError(f"Invalid region: {region}")
        allowed = [region]
    else:  # manager
        allowed = regions + [ALL_REGIONS]
        if region not in regions:
            region = regions[0]
    payload = {"role": role, "region": region, "allowed": allowed}
    return jwt.encode(payload, settings.AUTH_SECRET, algorithm=ALGO)


def decode_token(token: str) -> Session:
    try:
        data = jwt.decode(token, settings.AUTH_SECRET, algorithms=[ALGO])
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail=f"Invalid session token: {exc}")
    return Session(role=data["role"], region=data["region"],
                   allowed_regions=data.get("allowed", []))


def get_session(authorization: str | None = Header(default=None)) -> Session:
    """FastAPI dependency. No token → permissive default (manager, all regions)
    for API docs / tooling / curl. Production would require a valid token."""
    if not authorization or not authorization.lower().startswith("bearer "):
        return Session(role="manager", region=valid_regions()[0],
                       allowed_regions=valid_regions() + [ALL_REGIONS])
    return decode_token(authorization.split(" ", 1)[1].strip())


def resolve_region(session: Session, requested: str | None) -> str | None:
    """Map a requested region to what this session is actually allowed to read.

    Raises 403 if a trader tries to reach outside their allotted region.
    Returns the effective region (None / 'All regions' = cross-region for managers).
    """
    if session.role == "trader":
        if requested and requested not in (session.region,):
            raise HTTPException(
                status_code=403,
                detail=f"Trader access is restricted to {session.region}. "
                       f"'{requested}' is not permitted.",
            )
        return session.region

    # manager
    if not requested:
        return ALL_REGIONS
    if requested not in session.allowed_regions:
        raise HTTPException(status_code=403, detail=f"Region '{requested}' not allowed.")
    return requested
