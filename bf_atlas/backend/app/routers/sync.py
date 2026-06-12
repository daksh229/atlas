"""POST /sync/* and GET /sync/status — mock Odoo/NetHunt sync."""

from fastapi import APIRouter, HTTPException

from app.services import sync as sync_svc

router = APIRouter(prefix="/sync", tags=["Sync"])


@router.post("/all")
def sync_all():
    return sync_svc.run_all_syncs()


@router.post("/{source}")
def sync_one(source: str):
    try:
        return {"source": source, "results": sync_svc.run_sync(source)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/status")
def status():
    return {"items": sync_svc.last_sync_status()}
