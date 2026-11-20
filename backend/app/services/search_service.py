"""
Search Service
~~~~~~~~~~~~~~~
Handles Qdrant similarity search and result assembly.

NOTE: The actual Qdrant query logic is a PLACEHOLDER. The real implementation
will be added once the AI pipeline (OSNet embedding extraction) is integrated.
For now, the service returns mock results to allow frontend development.
"""

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.models import SearchRequest, SearchResult, DetectedPerson, Video
from app.config import settings


class SearchService:
    """Service for person search via Qdrant similarity search."""

    @staticmethod
    async def create_search_request(
        reference_image_path: str,
        db: AsyncSession,
        user_id: Optional[uuid.UUID] = None,
    ) -> SearchRequest:
        """
        Create a new search request record in the database.

        In the full implementation, this would:
        1. Load the reference image.
        2. Extract an OSNet embedding (512-dim vector).
        3. Query Qdrant for similar embeddings.
        4. Assemble and store search results.

        For now, it creates the request with 'pending' status.
        """
        search_request = SearchRequest(
            id=uuid.uuid4(),
            user_id=user_id,
            reference_image_path=reference_image_path,
            status="pending",
            created_at=datetime.utcnow(),
        )
        db.add(search_request)
        await db.flush()

        # ──────────────────────────────────────────────────────────────────
        # TODO: Trigger AI pipeline here
        # ──────────────────────────────────────────────────────────────────
        # Steps for the real implementation:
        #
        # 1. Load reference image from `reference_image_path`
        #    img = cv2.imread(reference_image_path)
        #
        # 2. Extract OSNet embedding (512-dim) from the reference image
        #    embedding = osnet_extractor.extract(img)  # → np.ndarray shape (512,)
        #
        # 3. Query Qdrant for nearest neighbours
        #    from qdrant_client import QdrantClient
        #    client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
        #    hits = client.search(
        #        collection_name=settings.QDRANT_COLLECTION,
        #        query_vector=embedding.tolist(),
        #        limit=20,
        #        score_threshold=0.6,
        #    )
        #
        # 4. For each hit, look up the DetectedPerson and Video, then create
        #    a SearchResult row with similarity_score, bounding box, etc.
        #
        # 5. Update search_request.status = "completed"
        #    search_request.completed_at = datetime.utcnow()
        # ──────────────────────────────────────────────────────────────────

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
