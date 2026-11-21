"""
Search Service
~~~~~~~~~~~~~~~
Handles Qdrant similarity search and result assembly.

NOTE: The actual Qdrant query logic is a PLACEHOLDER. The real implementation
will be added once the AI pipeline (OSNet embedding extraction) is integrated.
For now, the service returns mock results to allow frontend development.
"""

import logging
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.models import SearchRequest, SearchResult, DetectedPerson, Video
from app.config import settings

# Ensure ai-engine is in sys.path
ROOT_DIR = Path(__file__).resolve().parents[3]
AI_ENGINE_DIR = ROOT_DIR / "ai-engine"
if str(AI_ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(AI_ENGINE_DIR))

from pipeline.query_processor import QueryProcessor

logger = logging.getLogger(__name__)


class SearchService:
    """Service for person search via OSNet query processing and Qdrant similarity search."""

    _query_processor: Optional[QueryProcessor] = None

    @classmethod
    def get_query_processor(cls) -> QueryProcessor:
        """Singleton accessor for QueryProcessor."""
        if cls._query_processor is None:
            cls._query_processor = QueryProcessor()
        return cls._query_processor

    @classmethod
    async def create_search_request(
        cls,
        reference_image_path: str,
        db: AsyncSession,
        user_id: Optional[uuid.UUID] = None,
    ) -> SearchRequest:
        """
        Create a new search request, execute OSNet feature extraction and Qdrant similarity search,
        and persist ranked match rows into PostgreSQL.
        """
        search_request = SearchRequest(
            id=uuid.uuid4(),
            user_id=user_id,
            reference_image_path=reference_image_path,
            status="processing",
            created_at=datetime.utcnow(),
        )
        db.add(search_request)
        await db.flush()

        try:
            qp = cls.get_query_processor()
            matches = qp.search_person(
                reference_image_path=reference_image_path,
                limit=20,
                threshold=0.30,
            )

            for match in matches:
                bbox = match.get("bbox", [0, 0, 0, 0])
                vid_raw = match.get("video_id")
                try:
                    video_uuid = uuid.UUID(str(vid_raw)) if vid_raw else None
                except (ValueError, TypeError):
                    video_uuid = None

                # Verify video_uuid exists in PostgreSQL videos table before referencing
                if video_uuid is not None:
                    vid_stmt = select(Video.id).where(Video.id == video_uuid)
                    vid_exists = (await db.execute(vid_stmt)).scalar_one_or_none()
                    if not vid_exists:
                        video_uuid = None

                dp_uuid = None
                track_id = match.get("track_id")
                if video_uuid and track_id is not None:
                    dp_stmt = select(DetectedPerson).where(
                        DetectedPerson.video_id == video_uuid,
                        DetectedPerson.track_id == track_id,
                    )
                    dp_res = await db.execute(dp_stmt)
                    dp_obj = dp_res.scalar_one_or_none()
                    if dp_obj:
                        dp_uuid = dp_obj.id

                result_row = SearchResult(
                    id=uuid.uuid4(),
                    search_request_id=search_request.id,
                    detected_person_id=dp_uuid,
                    video_id=video_uuid,
                    similarity_score=float(match.get("similarity_score", 0.0)),
                    rank=int(match.get("rank", 1)),
                    matched_frame=int(match.get("frame_number", 0)),
                    matched_timestamp=float(match.get("timestamp", 0.0)),
                    bbox_x1=float(bbox[0]),
                    bbox_y1=float(bbox[1]),
                    bbox_x2=float(bbox[2]),
                    bbox_y2=float(bbox[3]),
                )
                db.add(result_row)

            search_request.status = "completed"
            search_request.completed_at = datetime.utcnow()
            await db.flush()

        except Exception as e:
            logger.error("Failed to execute search for %s: %s", search_request.id, str(e), exc_info=True)
            search_request.status = "failed"
            await db.flush()
            raise e

        return search_request

    @staticmethod
    async def get_search_request(
        search_id: uuid.UUID, db: AsyncSession
    ) -> Optional[SearchRequest]:
        """Get a search request by ID."""
        result = await db.execute(
            select(SearchRequest).where(SearchRequest.id == search_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_search_results(
        search_id: uuid.UUID, db: AsyncSession
    ) -> tuple[Optional[SearchRequest], List[SearchResult]]:
        """
        Get search results for a given search request.

        Returns the SearchRequest and its associated SearchResult rows,
        each eagerly loaded with the detected_person and video relationships
        so the response can include enriched details.
        """
        # Fetch the search request
        req_result = await db.execute(
            select(SearchRequest).where(SearchRequest.id == search_id)
        )
        search_request = req_result.scalar_one_or_none()

        if search_request is None:
            return None, []

        # Fetch results with eager-loaded relationships
        results_query = (
            select(SearchResult)
            .where(SearchResult.search_request_id == search_id)
            .options(
                selectinload(SearchResult.detected_person),
                selectinload(SearchResult.video),
            )
            .order_by(SearchResult.rank)
        )
        results_result = await db.execute(results_query)
        results = list(results_result.scalars().all())

        return search_request, results
