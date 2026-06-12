"""POST /pricelist/analyze — fuzzy-match a supplier price list to the catalogue."""

import io

from fastapi import APIRouter, File, Query, UploadFile

from app.core.serialize import to_records
from app.services import pricelist as pl

router = APIRouter(prefix="/pricelist", tags=["Price-List"])


@router.post("/analyze")
async def analyze(
    file: UploadFile | None = File(None),
    use_sample: bool = Query(True),
    prefer_ai: bool = Query(True),
):
    if file is not None:
        content = await file.read()
        items = pl.read_pricelist(io.BytesIO(content))
    elif use_sample:
        items = pl.read_pricelist(pl.SAMPLE_PATH)
    else:
        return {"error": "No file provided and use_sample is false."}

    df, engine = pl.analyze(items, prefer_ai=prefer_ai)
    matched = int(df["sku"].notna().sum())
    return {
        "engine": engine,
        "matched": matched,
        "total": len(df),
        "below_cost": int((df["flag"] == "✅ Cheaper than our cost").sum()),
        "items": to_records(df),
    }
