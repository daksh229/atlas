"""Offers Inbox — quick-add an offer, or parse a supplier email → Offer-to-Request."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.security import Session, get_session
from app.core.serialize import to_records
from app.services import offers as offers_svc

router = APIRouter(prefix="/offers", tags=["Offers Inbox"])


class OfferIn(BaseModel):
    brand: str
    offer_price: float
    qty: int


class ParseIn(BaseModel):
    email_id: str | None = None
    text: str | None = None


class AcceptIn(BaseModel):
    offers: list[dict]


@router.get("")
def list_offers(session: Session = Depends(get_session)):
    return {"items": to_records(offers_svc.list_offers(session))}


@router.post("")
def submit(body: OfferIn, session: Session = Depends(get_session)):
    return offers_svc.submit_offer(session, body.brand, body.offer_price, body.qty)


@router.get("/evaluation")
def evaluation(session: Session = Depends(get_session)):
    """Supplier-offer evaluation: the 3 real offers judged against BF's data."""
    return offers_svc.evaluation()


@router.get("/inbox")
def inbox(session: Session = Depends(get_session)):
    return {"items": offers_svc.inbox()}


@router.get("/inbox/{email_id}")
def inbox_email(email_id: str, session: Session = Depends(get_session)):
    e = offers_svc.email_body(email_id)
    if e is None:
        raise HTTPException(status_code=404, detail="Email not found")
    return e


@router.post("/parse")
def parse(body: ParseIn, session: Session = Depends(get_session)):
    return offers_svc.parse(email_id=body.email_id, text=body.text)


@router.post("/accept")
def accept(body: AcceptIn, session: Session = Depends(get_session)):
    return offers_svc.accept_offers(session, body.offers)
