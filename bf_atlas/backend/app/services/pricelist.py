"""
pricelist.py — supplier price-list analysis with AI fuzzy matching.

BF's stated AI use case. Claude maps messy supplier lines to our catalogue; an
offline difflib matcher runs when no key is present so the demo never breaks.
"""

import difflib
import os
import re

import pandas as pd

from app.core import llm
from app.core.config import settings
from app.core.database import run_query

MATCH_THRESHOLD = 0.45
SAMPLE_PATH = os.path.join(settings.DATA_DIR, "samples", "supplier_pricelist_messy.csv")


def catalog() -> pd.DataFrame:
    return run_query("SELECT sku, name, brand, category, cost_price, unit_price FROM products")


def read_pricelist(file_or_buffer) -> pd.DataFrame:
    df = pd.read_csv(file_or_buffer)
    cols = {c.lower().strip(): c for c in df.columns}
    item = cols.get("supplier_item") or cols.get("item") or list(df.columns)[0]
    price = cols.get("offered_price") or cols.get("price") or list(df.columns)[1]
    qty = cols.get("qty") or cols.get("quantity")
    out = pd.DataFrame({"supplier_item": df[item], "offered_price": df[price]})
    out["qty"] = df[qty] if qty else None
    return out


def _norm(s: str) -> str:
    s = str(s).lower()
    s = re.sub(r"\bedp\b", "eau de parfum", s)
    s = re.sub(r"\bedt\b", "eau de toilette", s)
    s = re.sub(r"\bcrm\b", "cream", s)
    s = re.sub(r"\bess\.?\b", "essence", s)
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _fallback_match(items: pd.DataFrame, cat: pd.DataFrame) -> list[dict]:
    cat_norm = [(_norm(f"{r.brand} {r['name']}"), r) for _, r in cat.iterrows()]
    results = []
    for raw in items["supplier_item"]:
        q = _norm(raw)
        best, best_score = None, 0.0
        for cnorm, row in cat_norm:
            score = difflib.SequenceMatcher(None, q, cnorm).ratio()
            shared = set(q.split()) & set(cnorm.split())
            score = 0.7 * score + 0.3 * (len(shared) / max(len(set(cnorm.split())), 1))
            if score > best_score:
                best, best_score = row, score
        results.append({"sku": best["sku"] if best is not None and best_score >= MATCH_THRESHOLD else None,
                        "confidence": round(best_score, 2)})
    return results


def _claude_match(items: pd.DataFrame, cat: pd.DataFrame) -> list[dict] | None:
    if not llm.has_llm():
        return None
    catalogue = "\n".join(f"{r.sku}: {r.brand} — {r['name']}" for _, r in cat.iterrows())
    lines = "\n".join(f"{i}: {v}" for i, v in enumerate(items["supplier_item"]))
    system = ("You match messy supplier price-list lines to catalogue SKUs. "
              "Items have abbreviations, typos, reordered words.")
    user = (f"CATALOGUE:\n{catalogue}\n\nSUPPLIER ITEMS (index: text):\n{lines}\n\n"
            'Return a JSON array: [{"index":0,"sku":"PF-001","confidence":0.0-1.0}]. '
            "Use null for sku when no credible match.")
    try:
        arr = llm.complete_json(system, user, max_tokens=1500)
    except Exception:
        return None
    by_idx = {d.get("index"): d for d in arr}
    return [{"sku": by_idx.get(i, {}).get("sku"),
             "confidence": by_idx.get(i, {}).get("confidence", 0.0)} for i in range(len(items))]


def analyze(items: pd.DataFrame, prefer_ai: bool = True) -> tuple[pd.DataFrame, str]:
    cat = catalog()
    matches, engine = None, "difflib (offline fallback)"
    if prefer_ai:
        matches = _claude_match(items, cat)
        engine = "AI (Claude)"
    if matches is None:
        matches = _fallback_match(items, cat)
        engine = "difflib (offline fallback)"

    cat_by_sku = {r.sku: r for _, r in cat.iterrows()}
    rows = []
    for (_, item), m in zip(items.iterrows(), matches):
        sku = m.get("sku")
        cr = cat_by_sku.get(sku) if sku else None
        offered = float(item["offered_price"])
        if cr is not None:
            our_cost, our_price = float(cr["cost_price"]), float(cr["unit_price"])
            resale_margin = round(our_price - offered, 2)
            flag = ("✅ Cheaper than our cost" if offered < our_cost
                    else "💰 Resale margin" if resale_margin > 0 else "⚠️ Above resale price")
            rows.append({"supplier_item": item["supplier_item"], "matched": cr["name"], "sku": sku,
                         "brand": cr["brand"], "confidence": m.get("confidence"), "offered": offered,
                         "our_cost": our_cost, "our_price": our_price,
                         "vs_cost": round(offered - our_cost, 2), "resale_margin": resale_margin, "flag": flag})
        else:
            rows.append({"supplier_item": item["supplier_item"], "matched": None, "sku": None,
                         "brand": None, "confidence": m.get("confidence"), "offered": offered,
                         "our_cost": None, "our_price": None, "vs_cost": None,
                         "resale_margin": None, "flag": "❓ No catalogue match"})
    return pd.DataFrame(rows), engine
