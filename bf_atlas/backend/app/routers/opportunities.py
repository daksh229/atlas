"""GET /opportunities and /alerts — the cross-match engine outputs."""

from fastapi import APIRouter, Depends, Query

from app.core.security import Session, get_session, resolve_region
from app.core.serialize import int_counts, to_records
from app.services import atlas

router = APIRouter(tags=["Opportunities"])


@router.get("/opportunities")
def opportunities(region: str | None = Query(None), limit: int = 50,
                  session: Session = Depends(get_session)):
    df = atlas.opportunities(resolve_region(session, region)).head(limit)
    return {"count": len(df), "items": to_records(df)}


@router.get("/alerts")
def alerts(region: str | None = Query(None), session: Session = Depends(get_session)):
    df = atlas.alerts(resolve_region(session, region))
    counts = int_counts(df["type"].value_counts().to_dict()) if not df.empty else {}
    return {"counts": counts, "items": to_records(df)}
