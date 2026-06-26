"""GET /relationships/* — My Clients / My Suppliers (own accounts only)."""

from fastapi import APIRouter, Depends

from app.core.security import Session, get_session
from app.core.serialize import to_records
from app.services import relationships as rel

router = APIRouter(prefix="/relationships", tags=["My Relationships"])


@router.get("/clients")
def clients(session: Session = Depends(get_session)):
    return {"items": to_records(rel.my_clients(session))}


@router.get("/suppliers")
def suppliers(session: Session = Depends(get_session)):
    return {"items": to_records(rel.my_suppliers(session))}
