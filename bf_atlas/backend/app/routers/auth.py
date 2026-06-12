"""POST /auth/session — onboarding: issue a region-scoped session token."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core import security
from app.core.security import Session, get_session

router = APIRouter(prefix="/auth", tags=["Auth / RBAC"])


class SessionRequest(BaseModel):
    role: str          # "trader" | "manager"
    region: str        # allotted region (required for trader)


class SessionResponse(BaseModel):
    token: str
    role: str
    region: str
    allowed_regions: list[str]


@router.get("/regions")
def regions():
    """Concrete regions available at onboarding."""
    return {"regions": security.valid_regions()}


@router.post("/session", response_model=SessionResponse)
def create_session(req: SessionRequest):
    try:
        token = security.create_token(req.role, req.region)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    s = security.decode_token(token)
    return SessionResponse(token=token, role=s.role, region=s.region,
                           allowed_regions=s.allowed_regions)


@router.get("/me", response_model=SessionResponse)
def me(session: Session = Depends(get_session)):
    return SessionResponse(token="", role=session.role, region=session.region,
                           allowed_regions=session.allowed_regions)
