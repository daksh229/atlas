"""GET /brands/* — brand intelligence (sell, buy, detail)."""

from fastapi import APIRouter, Depends, Query

from app.core.security import Session, get_session, resolve_region
from app.core.serialize import to_records
from app.services import atlas

router = APIRouter(prefix="/brands", tags=["Brand Intelligence"])


@router.get("/sell")
def can_sell(region: str | None = Query(None), session: Session = Depends(get_session)):
    return {"items": to_records(atlas.brands_i_can_sell(resolve_region(session, region)))}


@router.get("/buy")
def can_buy(region: str | None = Query(None), session: Session = Depends(get_session)):
    return {"items": to_records(atlas.brands_i_can_buy(resolve_region(session, region)))}


@router.get("/{brand}")
def detail(brand: str, region: str | None = Query(None),
           session: Session = Depends(get_session)):
    d = atlas.brand_detail(brand, resolve_region(session, region))
    return {
        "brand": brand,
        "best": d["best"],
        "offers": to_records(d["offers"]),
        "demands": to_records(d["demands"]),
    }
