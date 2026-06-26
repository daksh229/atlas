"""
main.py — BF Atlas FastAPI application.

A navigable trader-intelligence API (spec §4: a web application, NOT a chatbot).
Routers map 1:1 to the spec's navigation sections.

Run (from backend/):  uvicorn app.main:app --reload --port 8000
Docs:                 http://localhost:8000/docs
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import (
    alerts,
    auth,
    brands,
    catalog,
    dashboard,
    offers,
    radar,
    relationships,
)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Internal trader intelligence — trader-scoped opportunity alerts, "
                "brand maps, relationships, retailer radar and a shareable brand "
                "catalog. Matching runs on a brand dictionary with server-side "
                "trader access control.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in (auth, alerts, brands, relationships, offers, radar, catalog, dashboard):
    app.include_router(r.router)


@app.get("/health", tags=["Meta"])
def health():
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.VERSION}


@app.get("/", tags=["Meta"])
def root():
    return {"service": settings.APP_NAME, "docs": "/docs", "health": "/health"}
