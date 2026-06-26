"""GET /catalog + /catalog/pdf — company-wide Brand Catalog (anonymised, shareable)."""

from fastapi import APIRouter, Depends
from fastapi.responses import Response

from app.core.security import Session, get_session
from app.services import catalog as catalog_svc

router = APIRouter(prefix="/catalog", tags=["Brand Catalog"])


@router.get("")
def catalog(session: Session = Depends(get_session)):
    rows = catalog_svc.catalog_rows()
    return {"count": len(rows), "items": rows}


@router.get("/pdf")
def catalog_pdf(session: Session = Depends(get_session)):
    data, media = catalog_svc.build_pdf()
    ext = "pdf" if media == "application/pdf" else "txt"
    return Response(content=data, media_type=media, headers={
        "Content-Disposition": f'attachment; filename="bf_brand_catalogue.{ext}"'})
