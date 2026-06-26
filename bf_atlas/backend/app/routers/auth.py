"""Auth / onboarding — pick a trader identity, issue a session token (spec §9)."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core import security
from app.core.database import traders
from app.core.security import Session, get_session
from app.core.serialize import to_records

router = APIRouter(prefix="/auth", tags=["Auth"])


class SessionRequest(BaseModel):
    trader_id: str


class SessionResponse(BaseModel):
    token: str
    trader_id: str
    name: str
    team: str
    role: str


@router.get("/traders")
def list_traders():
    """Trader identities available at onboarding (the 5 POC traders)."""
    return {"traders": to_records(traders())}


@router.post("/session", response_model=SessionResponse)
def create_session(req: SessionRequest):
    try:
        token = security.create_token(req.trader_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    s = security.decode_token(token)
    return SessionResponse(token=token, trader_id=s.trader_id, name=s.name,
                           team=s.team, role=s.role)


@router.get("/me", response_model=SessionResponse)
def me(session: Session = Depends(get_session)):
    return SessionResponse(token="", trader_id=session.trader_id, name=session.name,
                           team=session.team, role=session.role)
