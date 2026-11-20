from .videos import router as videos_router
from .search import router as search_router
from .jobs import router as jobs_router

__all__ = ["videos_router", "search_router", "jobs_router"]
