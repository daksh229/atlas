"""
offers.py — the Offers Inbox (spec §7 Phase 2, structural).

Two ways an offer becomes a supply signal that the matcher checks against client
demand:

  1. Manual quick-add: a trader types brand/price/qty (submit_offer).
  2. Email parse: a trader opens a mock supplier email, the AI/heuristic parser
     extracts structured offers (email_parser), the trader reviews/edits them,
     and accepts (accept_offers).

Either way the result is a supply_signal(source ∈ manual_offer | email_offer) and
the SAME matching engine produces Offer-to-Request alerts. No real email
integration — the inbox is a folder of fixture .txt files.

Brand resolution stays deterministic here (via the brand dictionary): an unknown
brand is FLAGGED, never force-matched.
"""

import os
import re
import uuid

from app.core.config import settings
from app.core.database import get_conn, run_query
from app.services import brands, email_parser, matching

EMAIL_DIR = os.path.join(settings.DATA_DIR, "samples", "emails")

# Pre-computed supplier-offer evaluation (built by `python -m data.pipeline.build_offers`).
_EVAL_PATH = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", "..", "..",
    "data", "pipeline", "reports", "offer_evaluation.json",
))


def evaluation() -> dict:
    """The three real supplier offers, judged against BF's own data (verdict +
    reasoning + who-should-know). Read from the pipeline's pre-built JSON so the
    screen is fast and the heavy analysis runs at build time, not per request."""
    import json
    if not os.path.exists(_EVAL_PATH):
        return {"offers": {}, "report": {}, "error": "not_built"}
    with open(_EVAL_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# ── manual quick-add ────────────────────────────────────────────────────────

def list_offers(session=None):
    """Recorded offers (manual + email), newest first; scoped to the trader."""
    where, params = "WHERE s.source IN ('manual_offer','email_offer')", ()
    if session is not None and not session.is_manager:
        where += " AND s.trader_id = ?"
        params = (session.trader_id,)
    return run_query(
        f"""SELECT s.id, b.canonical_name AS brand, s.offer_price, s.available_qty,
                   s.fired_at, s.source, t.name AS submitted_by
            FROM supply_signals s JOIN brands b ON b.id = s.brand_id
            JOIN traders t ON t.id = s.trader_id
            {where} ORDER BY s.fired_at DESC""",
        params)


def _persist_offer(session, brand_id, offer_price, qty, source) -> str:
    sid = f"sup-{source}-{uuid.uuid4().hex[:8]}"
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO supply_signals
               (id, brand_id, partner_id, trader_id, offer_price, available_qty,
                fired_at, source)
               VALUES (?,?,?,?,?,?,?,?)""",
            (sid, brand_id, None, session.trader_id, offer_price, qty, matching._now(), source))
        conn.commit()
    return sid


def _matches_for(brand_id, supply_id) -> list[dict]:
    ds = matching.demand_supply_matches()
    hits = ds[(ds["brand_id"] == brand_id) & (ds["supply_id"] == supply_id)]
    return [
        {"client_owner": r["demand_trader"], "sell_price": float(r["sell_price"]),
         "match_qty": int(r["match_qty"]), "margin_value": float(r["margin_value"])}
        for _, r in hits.iterrows()
    ]


def submit_offer(session, brand_surface: str, offer_price: float, qty: int) -> dict:
    brand_id = brands.resolve(brand_surface)
    if brand_id is None:
        return {"ok": False, "error": f"Unknown brand: {brand_surface!r} "
                "(not in the brand dictionary — not force-matched)."}
    sid = _persist_offer(session, brand_id, offer_price, qty, "manual_offer")
    matches = _matches_for(brand_id, sid)
    return {"ok": True, "offer_id": sid, "brand": brand_surface,
            "match_count": len(matches), "matches": matches}


# ── email inbox ─────────────────────────────────────────────────────────────

def _read_email(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        raw = f.read()
    frm = subject = ""
    body_lines, in_body = [], False
    for line in raw.splitlines():
        if not in_body and line.lower().startswith("from:"):
            frm = line.split(":", 1)[1].strip()
        elif not in_body and line.lower().startswith("subject:"):
            subject = line.split(":", 1)[1].strip()
        elif not in_body and line.strip() == "":
            in_body = True
        elif in_body:
            body_lines.append(line)
    return {"from": frm, "subject": subject, "body": "\n".join(body_lines).strip(),
            "raw": raw}


def inbox() -> list[dict]:
    if not os.path.isdir(EMAIL_DIR):
        return []
    out = []
    for name in sorted(os.listdir(EMAIL_DIR)):
        if not name.endswith(".txt"):
            continue
        e = _read_email(os.path.join(EMAIL_DIR, name))
        preview = re.sub(r"\s+", " ", e["body"])[:90]
        out.append({"id": name, "from": e["from"], "subject": e["subject"],
                    "preview": preview})
    return out


def email_body(email_id: str) -> dict | None:
    path = os.path.join(EMAIL_DIR, os.path.basename(email_id))
    if not os.path.isfile(path):
        return None
    e = _read_email(path)
    return {"id": email_id, "from": e["from"], "subject": e["subject"], "body": e["body"]}


def parse(email_id: str | None = None, text: str | None = None) -> dict:
    """Extract + brand-resolve offers from an email (or pasted text). Not persisted."""
    if email_id:
        e = email_body(email_id)
        if e is None:
            return {"engine": None, "offers": [], "error": "Email not found"}
        text = e["body"]
    text = text or ""
    result = email_parser.extract(text)
    offers = []
    for o in result["offers"]:
        bid = brands.resolve(o.get("brand", ""))
        canonical = None
        if bid is not None:
            row = run_query("SELECT canonical_name FROM brands WHERE id = ?", (bid,))
            canonical = row.iloc[0]["canonical_name"] if not row.empty else None
        offers.append({
            "brand_surface": o.get("brand"), "brand": canonical, "brand_id": bid,
            "unknown_brand": bid is None,
            "product": o.get("product"), "offer_price": o.get("offer_price"),
            "currency": o.get("currency") or "EUR", "quantity": o.get("quantity"),
            "valid_until": o.get("valid_until"), "supplier": o.get("supplier"),
            "confidence": o.get("confidence", 0.5),
        })
    return {"engine": result["engine"], "offers": offers}


def accept_offers(session, offers: list[dict]) -> dict:
    """Persist accepted offers (resolved brands only) and run the matcher."""
    accepted, all_matches, skipped = 0, [], 0
    for o in offers:
        bid = o.get("brand_id") or brands.resolve(o.get("brand_surface") or o.get("brand") or "")
        price, qty = o.get("offer_price"), o.get("quantity")
        if bid is None or price is None or qty is None:
            skipped += 1
            continue
        sid = _persist_offer(session, bid, float(price), int(qty), "email_offer")
        for m in _matches_for(bid, sid):
            all_matches.append({**m, "brand": o.get("brand")})
        accepted += 1
    return {"accepted": accepted, "skipped": skipped,
            "match_count": len(all_matches), "matches": all_matches}
