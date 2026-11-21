"""
TraceVision Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~
Application settings loaded from environment variables via pydantic-settings.
Create a .env file in the backend/ directory to override defaults.
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import List

_BACKEND_DIR = Path(__file__).resolve().parents[1]
_ROOT_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Application settings with sensible defaults for local development."""

    # ── Database ──────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgrespassword@localhost:5433/tracevision"

    # ── Qdrant Vector Database ────────────────────────────────────────────
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION: str = "person_embeddings"

    # ── File Storage ──────────────────────────────────────────────────────
    UPLOAD_DIR: str = str(_ROOT_DIR / "uploads")

    # ── CORS ──────────────────────────────────────────────────────────────
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # ── App Metadata ──────────────────────────────────────────────────────
    APP_TITLE: str = "TraceVision API"
    APP_VERSION: str = "0.1.0"

    model_config = {
        "env_file": [str(_BACKEND_DIR / ".env"), str(_ROOT_DIR / ".env"), ".env"],
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore",
    }


# Singleton settings instance
settings = Settings()
