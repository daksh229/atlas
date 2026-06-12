"""
main.py — BF Atlas FastAPI application.

Run (from backend/):  uvicorn app.main:app --reload --port 8000
Docs:                 http://localhost:8000/docs
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import (
    auth,
    brands,
    chat,
    dashboard,
    opportunities,
    pricelist,
    radar,
    sync,
)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Internal trading intelligence API — dashboard, cross-match "
                "opportunity engine, brand intelligence, price-list AI matching, "
                "retailer radar, and a LangGraph multi-agent NL interface.",
)

# The React frontend (and any local client) can call the API in dev.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in (auth, chat, dashboard, opportunities, brands, pricelist, radar, sync):
    app.include_router(r.router)


@app.get("/health", tags=["Meta"])
def health():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.VERSION,
        "llm_configured": settings.has_llm,
        "model": settings.CLAUDE_MODEL,
    }


@app.get("/", tags=["Meta"])
def root():
    return {"service": settings.APP_NAME, "docs": "/docs", "health": "/health"}
