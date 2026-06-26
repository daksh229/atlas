"""GET /alerts — the trader's routed, quality-controlled Opportunity Alerts."""

from fastapi import APIRouter, Depends

from app.core.security import Session, get_session
from app.services import alerts as alerts_svc

router = APIRouter(tags=["Opportunity Alerts"])


@router.get("/alerts")
def alerts(session: Session = Depends(get_session)):
    return alerts_svc.for_trader(session)
