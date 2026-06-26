"""GET /brands/* — Brand Maps (sell/buy) + Brand Intelligence detail."""

from fastapi import APIRouter, Depends, HTTPException

from app.core.security import Session, get_session
from app.core.serialize import to_records
from app.services import brands as brand_svc

router = APIRouter(prefix="/brands", tags=["Brand Maps"])


@router.get("/sell")
def can_sell(session: Session = Depends(get_session)):
    return {"items": to_records(brand_svc.brands_i_can_sell(session))}


@router.get("/buy")
def can_buy(session: Session = Depends(get_session)):
    return {"items": to_records(brand_svc.brands_i_can_buy(session))}


@router.get("/{brand_id}")
def detail(brand_id: str, session: Session = Depends(get_session)):
    d = brand_svc.brand_detail(session, brand_id)
    if not d:
        raise HTTPException(status_code=404, detail="Brand not found")
    return {
        "brand_id": d["brand_id"], "brand": d["brand"], "category": d["category"],
        "best_historical_sell_price": d["best_historical_sell_price"],
        "colleagues": to_records(d["colleagues"]),
        "demands": d["demands"], "offers": d["offers"],
        "retailers": to_records(d["retailers"]),
    }
