"""GET /radar — Retailer Radar (persisted scan vs our supply, brand-dictionary joined)."""

from fastapi import APIRouter, Depends

from app.core.security import Session, get_session
from app.core.serialize import to_records
from app.services import radar as radar_svc

router = APIRouter(prefix="/radar", tags=["Retailer Radar"])


@router.get("")
def radar(session: Session = Depends(get_session)):
    df = radar_svc.compare_to_catalog()
    windows = int((df["signal"] == "🟢 Market window").sum()) if not df.empty else 0
    unknown = int(df["brand"].str.startswith("⚠").sum()) if not df.empty else 0
    return {"count": len(df), "market_windows": windows, "unknown_brands": unknown,
            "items": to_records(df)}
