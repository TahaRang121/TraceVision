"""
TraceVision Backend API
~~~~~~~~~~~~~~~~~~~~~~~
FastAPI application entry point. Provides REST endpoints for video uploads,
person search, job monitoring, and similarity search result retrieval.
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database.init_db import init_db
from app.routes.videos import router as videos_router
from app.routes.search import router as search_router
from app.routes.jobs import router as jobs_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager for startup and shutdown events."""
    # Ensure upload directories exist
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "videos"), exist_ok=True)
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "references"), exist_ok=True)
    print("📁 Upload directories initialized.")

    # Try initializing database tables
    try:
        await init_db()
        print(" Connected to PostgreSQL and initialized tables.")
    except Exception as e:
        print(f"⚠️ Warning: Could not connect to PostgreSQL on startup ({e}).")
        print("   Make sure PostgreSQL is running if you intend to perform database operations.")

    yield

    print("🛑 TraceVision Backend shutting down.")


app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    description="Backend REST API for TraceVision — AI-Powered Person Search Across Video Footage",
    lifespan=lifespan,
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers under /api prefix
app.include_router(videos_router, prefix="/api")
app.include_router(search_router, prefix="/api")
app.include_router(jobs_router, prefix="/api")

# Mount uploads directory for static file access (video playback / thumbnail viewing)
if os.path.exists(settings.UPLOAD_DIR):
    app.mount("/static/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")


@app.get("/", tags=["Health"])
async def root():
    """Root health check endpoint."""
    return {
        "status": "online",
        "app": settings.APP_TITLE,
        "version": settings.APP_VERSION,
        "docs_url": "/docs",
    }


@app.get("/api/health", tags=["Health"])
async def health_check():
    """Detailed health check endpoint."""
    return {
        "status": "healthy",
        "database": "configured",
        "qdrant": f"{settings.QDRANT_HOST}:{settings.QDRANT_PORT}",
        "upload_dir": settings.UPLOAD_DIR,
    }
