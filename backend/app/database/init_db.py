"""
Database Initialization
~~~~~~~~~~~~~~~~~~~~~~~~
Creates all tables on startup if they don't already exist.
"""

import os
from app.database.session import engine
from app.models.models import Base
from app.config import settings


async def init_db() -> None:
    """Initialize the database: create tables and ensure upload directories exist."""

    # Create all tables from ORM models
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Ensure upload directories exist
    videos_dir = os.path.join(settings.UPLOAD_DIR, "videos")
    references_dir = os.path.join(settings.UPLOAD_DIR, "references")
    os.makedirs(videos_dir, exist_ok=True)
    os.makedirs(references_dir, exist_ok=True)

    print("✅ Database tables created and upload directories ensured.")
