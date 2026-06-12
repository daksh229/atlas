"""GET /dashboard/* — KPIs and chart data, plus /meta/regions. Region-scoped by RBAC."""

from fastapi import APIRouter, Depends, Query

from app.core.database import regions as list_regions
from app.core.security import Session, get_session, resolve_region
from app.core.serialize import to_records as _recs
from app.services import dashboard as dash

router = APIRouter(tags=["Dashboard"])


@router.get("/meta/regions")
def regions():
    return {"regions": list_regions()}


@router.get("/dashboard/kpis")
def kpis(region: str | None = Query(None), session: Session = Depends(get_session)):
    return dash.kpis(resolve_region(session, region))


@router.get("/dashboard/charts")
def charts(region: str | None = Query(None), session: Session = Depends(get_session)):
    region = resolve_region(session, region)
    return {
        "revenue_by_region": _recs(dash.revenue_by_region(region)),
        "pipeline_by_stage": _recs(dash.pipeline_by_stage(region)),
        "revenue_over_time": _recs(dash.revenue_over_time(region)),
        "low_stock": _recs(dash.low_stock(region)),
        "top_products": _recs(dash.top_products(region, limit=8)),
    }
