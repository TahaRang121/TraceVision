"""
TraceVision Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~
Application settings loaded from environment variables via pydantic-settings.
Create a .env file in the backend/ directory to override defaults.
"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings with sensible defaults for local development."""

    # ── Database ──────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/tracevision"

    # ── Qdrant Vector Database ────────────────────────────────────────────
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION: str = "person_embeddings"

    # ── File Storage ──────────────────────────────────────────────────────
    UPLOAD_DIR: str = r"F:\TraceVision-POCs\uploads"

    # ── CORS ──────────────────────────────────────────────────────────────
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # ── App Metadata ──────────────────────────────────────────────────────
    APP_TITLE: str = "TraceVision API"
    APP_VERSION: str = "0.1.0"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


# Singleton settings instance
settings = Settings()
