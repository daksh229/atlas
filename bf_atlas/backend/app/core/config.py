"""Central configuration — reads from environment / backend/.env."""

import os

from dotenv import load_dotenv

# Load backend/.env (two levels up from app/core/).
_BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
load_dotenv(os.path.join(_BACKEND_DIR, ".env"))


class Settings:
    APP_NAME = "BF Atlas API"
    VERSION = "0.1.0"

    # Single Claude model for every agent (per decision: Sonnet only).
    CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

    # JWT signing secret for session/RBAC tokens (set a real one in prod).
    AUTH_SECRET = os.getenv("AUTH_SECRET", "bf-atlas-dev-secret-change-me")

    # SQLite file produced by data/init_db.py + init_atlas.py
    DB_PATH = os.path.abspath(
        os.getenv("DB_PATH", os.path.join(_BACKEND_DIR, "..", "data", "bfuturist.db"))
    )

    # Where sample files (price lists, retailer fixture) live.
    DATA_DIR = os.path.abspath(os.path.join(_BACKEND_DIR, "..", "data"))

    @property
    def has_llm(self) -> bool:
        return bool(self.ANTHROPIC_API_KEY)


settings = Settings()
