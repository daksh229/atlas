"""GET /radar — Retailer Radar competitor price comparison."""

from fastapi import APIRouter

from app.core.serialize import to_records
from app.services import radar as rr

router = APIRouter(prefix="/radar", tags=["Retailer Radar"])


@router.get("")
def scan():
    df = rr.compare_to_catalog()
    return {
        "count": len(df),
        "retailers": int(df["retailer"].nunique()),
        "items": to_records(df),
    }
