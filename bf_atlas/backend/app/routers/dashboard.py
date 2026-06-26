"""GET /dashboard — slim 'My View' overview, scoped to the session trader."""

from fastapi import APIRouter, Depends

from app.core.security import Session, get_session
from app.core.serialize import to_records
from app.services import dashboard as dash

router = APIRouter(prefix="/dashboard", tags=["My View"])


@router.get("")
def dashboard(session: Session = Depends(get_session)):
    return {"kpis": dash.kpis(session), "my_brands": to_records(dash.my_brands(session))}
