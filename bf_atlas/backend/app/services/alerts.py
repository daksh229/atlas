"""
alerts.py — turn matches into routed, quality-controlled alerts (spec §7 + §9).

Alert types
  Phase 1 core:
    demand_supply    — a client needs a brand and a (colleague's) supply exists
    external_market  — a retailer lists a brand above a price we can supply at
    stock_match      — we hold live inventory of a brand a client wants
    reorder          — a client is overdue for a repeat order
  Phase 2 (demonstrated on planted data):
    offer_to_request — a manual offer matches an existing client request
    triple_match     — demand + supply + retail all align on one brand (top priority)

Right-person routing (§9): every alert targets a specific trader — the account
owner / stock owner / matching-client owner — not the whole team. Demand–Supply,
Offer-to-Request and Triple alerts notify BOTH sides; each side sees the
counterparty masked via core.security.mask_partner.

Alert quality control (§9): for each recipient we de-duplicate, BUNDLE by brand,
rank by priority then value, and CAP per day — so the feed stays useful, not spam.
"""

from app.core.security import Session, mask_partner, owns
from app.services import matching


def _counterparty(session: Session, owner) -> str:
    """How to name the other side of a match for this session (access-masked)."""
    return "(your own account)" if owns(session, owner) else mask_partner(session, owner, None)

PRIORITY = {
    "triple_match": 100, "offer_to_request": 90, "demand_supply": 80,
    "stock_match": 70, "external_market": 60, "reorder": 50,
}
LABEL = {
    "triple_match": "Triple Match", "offer_to_request": "Offer-to-Request Match",
    "demand_supply": "Demand–Supply Match", "stock_match": "Stock Match",
    "external_market": "External Market Window", "reorder": "Reorder Reminder",
}
DAILY_CAP = 15  # max alerts surfaced per trader per run


def _candidates() -> list[dict]:
    """All alert candidates across all traders (un-filtered, un-masked).

    Each carries `recipient` (the routed trader) plus enough raw context to mask
    and render per-session later.
    """
    out: list[dict] = []
    ds = matching.demand_supply_matches()
    triple_brands = set(matching.external_market_windows()["brand_id"]) & set(ds["brand_id"])

    for _, r in ds.iterrows():
        is_offer = r["supply_source"] == "manual_offer"
        is_triple = r["brand_id"] in triple_brands
        atype = "triple_match" if is_triple else ("offer_to_request" if is_offer else "demand_supply")
        base = {
            "type": atype, "brand_id": r["brand_id"], "brand": r["brand"],
            "value": float(r["margin_value"]), "match_qty": int(r["match_qty"]),
            "buy_price": float(r["buy_price"]), "sell_price": float(r["sell_price"]),
        }
        if r["demand_trader"] == r["supply_trader"]:
            # one trader owns BOTH sides → a single buy→sell loop, not two notices
            out.append({**base, "recipient": r["demand_trader"],
                        "cp_owner": r["demand_trader"], "cp_kind": "loop",
                        "cp_id": r["client_id"], "side": "loop"})
        else:
            # notify the demand owner (counterparty = supply side)
            out.append({**base, "recipient": r["demand_trader"],
                        "cp_owner": r["supply_trader"], "cp_kind": "supply",
                        "cp_id": r["supplier_id"], "side": "demand"})
            # notify the supply owner (counterparty = demand side)
            out.append({**base, "recipient": r["supply_trader"],
                        "cp_owner": r["demand_trader"], "cp_kind": "demand",
                        "cp_id": r["client_id"], "side": "supply"})

    for _, r in matching.external_market_windows().iterrows():
        out.append({
            "type": "external_market", "brand_id": r["brand_id"], "brand": r["brand"],
            "recipient": r["supply_trader"], "cp_owner": None, "cp_kind": "retail",
            "value": float(r["headroom_per_unit"]),
            "retailer": r["retailer"], "retail_price": float(r["retail_price"]),
            "our_buy_price": float(r["our_buy_price"]), "stock_status": r["stock_status"],
        })

    for _, r in matching.stock_matches().iterrows():
        out.append({
            "type": "stock_match", "brand_id": r["brand_id"], "brand": r["brand"],
            "recipient": r["demand_trader"], "cp_owner": r["demand_trader"],
            "cp_kind": "client", "cp_id": r["client_id"],
            "value": float(r["qty_available"]), "product": r["product"],
            "qty_available": int(r["qty_available"]), "wanted_qty": int(r["wanted_qty"]),
        })

    rdf = matching.reorder_due()
    for _, r in (rdf.iterrows() if not rdf.empty else []):
        out.append({
            "type": "reorder", "brand_id": r["brand_id"], "brand": r["brand"],
            "recipient": r["demand_trader"], "cp_owner": r["demand_trader"],
            "cp_kind": "client", "cp_id": r["client_id"],
            "value": float(r["days_since_last"]), "client": r["client"],
            "cadence_days": int(r["cadence_days"]), "days_since_last": int(r["days_since_last"]),
            "last_order": r["last_order"],
        })
    return out


def _render(session: Session, c: dict) -> str:
    """Human-readable detail line with access masking applied for this session."""
    b = c["brand"]
    t = c["type"]
    if t in ("demand_supply", "offer_to_request", "triple_match"):
        if c["side"] == "loop":
            return (f"Your own buy→sell loop: source {b} @ €{c['buy_price']:.0f} → "
                    f"your client @ €{c['sell_price']:.0f} — ~{c['match_qty']} units, "
                    f"€{c['value']:,.0f} margin")
        who = _counterparty(session, c["cp_owner"])  # counterparty trader, masked
        if c["side"] == "demand":
            return (f"Your client wants {b} @ €{c['sell_price']:.0f}; supply available "
                    f"{who} @ €{c['buy_price']:.0f} — ~{c['match_qty']} units, "
                    f"€{c['value']:,.0f} margin")
        return (f"You can supply {b} @ €{c['buy_price']:.0f}; a client wants it "
                f"{who} @ €{c['sell_price']:.0f} — ~{c['match_qty']} units, "
                f"€{c['value']:,.0f} margin")
    if t == "external_market":
        return (f"{c['retailer']} lists {b} @ €{c['retail_price']:.0f}; you can supply "
                f"from €{c['our_buy_price']:.0f} (+€{c['value']:.0f}/unit headroom)")
    if t == "stock_match":
        return (f"{c['qty_available']} units of {b} in stock — your client wants "
                f"~{c['wanted_qty']}. Fastest deal, no sourcing needed.")
    if t == "reorder":
        return (f"{c['client']} reorders {b} every ~{c['cadence_days']}d; "
                f"{c['days_since_last']}d since last order ({c['last_order']}) — follow up.")
    return b


def for_trader(session: Session) -> dict:
    """Routed, masked, de-duplicated, bundled, capped alert feed for the session."""
    mine = [c for c in _candidates()
            if session.is_manager or c["recipient"] == session.trader_id]

    # de-duplicate identical (type, brand, counterparty) candidates
    seen, deduped = set(), []
    for c in mine:
        key = (c["type"], c["brand_id"], c.get("cp_id"), c.get("retailer"), c.get("side"))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(c)

    # bundle by (recipient, type, brand): one alert per brand+type, items inside
    bundles: dict[tuple, dict] = {}
    for c in deduped:
        bkey = (c["recipient"], c["type"], c["brand_id"])
        line = _render(session, c)
        if bkey not in bundles:
            bundles[bkey] = {
                "id": f"{c['type']}:{c['brand_id']}:{c['recipient']}",
                "type": c["type"], "label": LABEL[c["type"]], "brand": c["brand"],
                "brand_id": c["brand_id"], "priority": PRIORITY[c["type"]],
                "value": 0.0, "items": [],
            }
        bundles[bkey]["items"].append(line)
        bundles[bkey]["value"] += c["value"] if c["type"] not in ("reorder", "stock_match") else 0

    feed = sorted(bundles.values(), key=lambda a: (a["priority"], a["value"]), reverse=True)

    # daily cap (right-sized so the feed stays useful, not spam)
    capped = feed[:DAILY_CAP]
    counts: dict[str, int] = {}
    for a in capped:
        counts[a["label"]] = counts.get(a["label"], 0) + 1

    return {
        "trader": session.name, "total": len(capped),
        "suppressed": max(0, len(feed) - DAILY_CAP),
        "counts": counts, "items": capped,
    }
