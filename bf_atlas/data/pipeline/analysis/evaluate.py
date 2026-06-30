"""
evaluate.py — the core judgment: is this offer line good, why, and who should know?

The reasoning is deliberately transparent (every number that drives the verdict
is returned alongside it) so a trader can trust it and audit it.

For one offer line, joined by EAN to BF's own data:
  - COST: how the offered price compares to what BF usually pays
    (product reference avg/min purchase price, cross-checked with real purchase
    history). Below our average buy → attractive; below our best-ever buy → strong.
  - RESALE HEADROOM: margin against the conservative of {our average sale price,
    the live market price}. The market price is the external reality check.
  - WHO SHOULD KNOW: the traders who have bought this product before (potential
    sources) and those who have sold it (potential sell-side / clients).

The margin bands live in config and are surfaced rather than fixed externally.
"""

from __future__ import annotations

from dataclasses import dataclass

from data.pipeline.config import SETTINGS

GOOD, BORDERLINE, SKIP, UNKNOWN = "good", "borderline", "skip", "unknown"


@dataclass
class Refs:
    """Everything we know about an EAN, assembled by the build step."""
    product: dict | None        # product reference row (avg/min pp, avg/max sp, brand, name)
    buy: dict | None            # purchase-history aggregate (by EAN)
    sell: dict | None           # sales-history aggregate (by EAN)
    market: dict | None         # retailer aggregate (by EAN)
    brand: dict | None = None   # brand-level aggregate (context when EAN doesn't match)


def _pct(numer, denom):
    if not denom:
        return None
    return round(numer / denom, 4)


def evaluate_line(offer: dict, refs: Refs) -> dict:
    offer_eur = offer.get("unit_price_eur")
    out = {
        **offer,
        "matched": False,
        "verdict": UNKNOWN,
        "cost_ref_eur": None, "cost_basis": None, "cost_delta_pct": None,
        "resale_ref_eur": None, "resale_basis": None, "margin_pct": None,
        "market_min_eur": None, "market_margin_pct": None,
        "potential_value_eur": None,
        "sources": [], "sell_side": [], "n_clients": 0,
        "brand_context": None,
        "why": "", "flags": [],
    }

    if not offer.get("ean"):
        out["flags"].append("no_ean")
    if offer_eur is None:
        out["flags"].append("not_comparable")
        out["why"] = "Offer price could not be converted to EUR — cannot judge."
        return out

    p, buy, sell, market, brand = refs.product, refs.buy, refs.sell, refs.market, refs.brand
    if not any([p, buy, sell, market]):
        # No exact product match by EAN. Fall back to brand-level CONTEXT only —
        # clearly flagged, never presented as a per-product verdict.
        out["flags"].append("no_exact_ean_match")
        if brand and (brand.get("avg_buy_eur") or brand.get("avg_sale_eur")):
            out["brand_context"] = {
                "brand": offer.get("brand_surface"),
                "typical_buy_eur": brand.get("avg_buy_eur"),
                "typical_sale_eur": brand.get("avg_sale_eur"),
                "n_products": brand.get("n_products"),
            }
            out["sources"] = brand.get("buy_traders", [])[:5]
            out["sell_side"] = brand.get("sell_traders", [])[:5]
            tb = brand.get("typical_buy_eur") or brand.get("avg_buy_eur")
            ts = brand.get("avg_sale_eur")
            ctx = []
            if tb:
                ctx.append(f"buys ~€{tb:.0f}")
            if ts:
                ctx.append(f"sells ~€{ts:.0f}")
            out["why"] = (
                f"No exact product match by EAN. At brand level BF "
                f"{' / '.join(ctx)} across {brand.get('n_products')} {offer.get('brand_surface')} "
                f"products — context only, not a per-product verdict."
            )
        else:
            out["flags"].append("unknown_product")
            out["why"] = "Product not found in our data (by EAN or brand) — flagged, not force-matched."
        return out
    out["matched"] = True

    # --- COST: vs what BF usually pays ------------------------------------
    cost_ref = (p or {}).get("avg_purchase_price_eur") or (buy or {}).get("buy_avg_eur")
    min_pp = (p or {}).get("min_purchase_price_eur") or (buy or {}).get("buy_min_eur")
    if cost_ref:
        out["cost_ref_eur"] = round(cost_ref, 2)
        out["cost_basis"] = "avg_purchase_price" if (p or {}).get("avg_purchase_price_eur") else "purchase_history_avg"
        out["cost_delta_pct"] = _pct(cost_ref - offer_eur, cost_ref)  # +ve = cheaper than usual

    # --- RESALE: conservative of our sale price and the market ------------
    our_sale = (p or {}).get("avg_sale_price_eur") or (sell or {}).get("sell_avg_eur")
    mkt = (market or {}).get("market_min_eur")
    out["market_min_eur"] = mkt
    candidates = [c for c in (our_sale, mkt) if c]
    resale_ref = min(candidates) if candidates else None
    if resale_ref:
        out["resale_ref_eur"] = round(resale_ref, 2)
        out["resale_basis"] = "min(our_avg_sale, market)" if len(candidates) == 2 else (
            "our_avg_sale" if our_sale else "market")
        out["margin_pct"] = _pct(resale_ref - offer_eur, offer_eur)
    if mkt:
        out["market_margin_pct"] = _pct(mkt - offer_eur, offer_eur)

    # --- VERDICT ----------------------------------------------------------
    margin = out["margin_pct"]
    below_avg_buy = out["cost_delta_pct"] is not None and out["cost_delta_pct"] >= 0
    below_best_buy = min_pp is not None and offer_eur <= min_pp

    if margin is None:
        out["verdict"] = UNKNOWN
    elif (below_avg_buy and margin >= SETTINGS.margin_good) or (below_best_buy and margin >= SETTINGS.margin_borderline):
        out["verdict"] = GOOD
    elif margin >= SETTINGS.margin_borderline:
        out["verdict"] = BORDERLINE
    else:
        out["verdict"] = SKIP

    # potential €value of the line (margin per unit × qty) for ranking
    if margin is not None and offer.get("qty"):
        out["potential_value_eur"] = round((resale_ref - offer_eur) * offer["qty"], 2)

    # --- WHO SHOULD KNOW --------------------------------------------------
    # Route to the responsible TRADERS (spec §9). Client/vendor account names are
    # access-controlled, so we expose only a count, never the names themselves.
    out["sources"] = (buy or {}).get("buy_traders", [])[:5]
    out["sell_side"] = (sell or {}).get("sell_traders", [])[:5]
    out["n_clients"] = len((sell or {}).get("sell_accounts", []))

    out["why"] = _explain(out)
    return out


def _explain(o: dict) -> str:
    bits = []
    price = f"€{o['unit_price_eur']:.2f}"
    if o["currency"] != "EUR":
        price += f" ({o['unit_price']:.2f} {o['currency']})"
    if o["cost_delta_pct"] is not None:
        d = o["cost_delta_pct"]
        rel = f"{abs(d)*100:.0f}% {'below' if d >= 0 else 'above'} our avg buy €{o['cost_ref_eur']:.2f}"
        bits.append(f"{price} — {rel}")
    else:
        bits.append(price)
    if o["margin_pct"] is not None:
        bits.append(f"~{o['margin_pct']*100:.0f}% resale headroom (vs {o['resale_basis']} €{o['resale_ref_eur']:.2f})")
    if o["sell_side"]:
        bits.append("sold before by " + ", ".join(o["sell_side"][:2]))
    elif o["sources"]:
        bits.append("sourced before by " + ", ".join(o["sources"][:2]))
    return "; ".join(bits) + "."


def evaluate_all(offers: list[dict], get_refs) -> list[dict]:
    """get_refs(offer) -> Refs. Pure orchestration over the offer lines."""
    results = [evaluate_line(o, get_refs(o)) for o in offers]
    rank = {GOOD: 0, BORDERLINE: 1, SKIP: 2, UNKNOWN: 3}
    results.sort(key=lambda r: (rank[r["verdict"]], -(r["potential_value_eur"] or 0)))
    return results
