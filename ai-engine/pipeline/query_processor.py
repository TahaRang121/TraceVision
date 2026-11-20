"""
Query Processor for TraceVision.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Handles user search requests:
1. Loads the reference image of the target person
2. Extracts a 512-dimensional appearance embedding via OSNet
3. Executes vector similarity search in Qdrant
4. Ranks and deduplicates matches across video tracks
"""

import logging
import os
from typing import Any, Dict, List, Optional
import cv2
import numpy as np

from person_reid.feature_extractor import PersonFeatureExtractor
from embeddings.embedding_store import EmbeddingStore

logger = logging.getLogger(__name__)


class QueryProcessor:
    """Processes person search queries against indexed video footage."""

    def __init__(
        self,
        feature_extractor: Optional[PersonFeatureExtractor] = None,
        embedding_store: Optional[EmbeddingStore] = None,
    ):
        """Initialize the query processor.

        Args:
            feature_extractor: OSNet feature extractor instance.
            embedding_store: Qdrant vector store client wrapper.
        """
        self.feature_extractor = feature_extractor or PersonFeatureExtractor()
        self.embedding_store = embedding_store or EmbeddingStore()

    def search_person(
        self,
        reference_image_path: str,
        video_ids: Optional[List[str]] = None,
        limit: int = 20,
        threshold: float = 0.60,
    ) -> List[Dict[str, Any]]:
        """Find occurrences of a person from a reference photo across indexed videos.

        Args:
            reference_image_path: Path to the query image of the person.
            video_ids: Optional list of specific video IDs to restrict search to.
            limit: Maximum number of matches to return.
            threshold: Minimum cosine similarity score (0.0 to 1.0).

        Returns:
            Ranked list of match dictionaries containing:
                - rank (int)
                - similarity_score (float)
                - video_id (str)
                - track_id (int)
                - frame_number (int)
                - timestamp (float in seconds)
                - bbox ([x1, y1, x2, y2])
        """
        if not os.path.exists(reference_image_path):
            raise FileNotFoundError(f"Reference image not found: {reference_image_path}")

        image = cv2.imread(reference_image_path)
        if image is None:
            raise ValueError(f"Could not decode reference image: {reference_image_path}")

        logger.info("Extracting query embedding for reference image: %s", reference_image_path)

        # Step 1: Extract 512-dim embedding using OSNet
        query_embedding = self.feature_extractor.extract(image)

        # Step 2: Query Qdrant
        if video_ids:
            raw_results = self.embedding_store.search_in_videos(
                query_embedding=query_embedding,
                video_ids=video_ids,
                limit=limit,
                score_threshold=threshold,
            )
        else:
            raw_results = self.embedding_store.search(
                query_embedding=query_embedding,
                limit=limit,
                score_threshold=threshold,
            )

        # Step 3: Format and rank results
        ranked_results = []
        for rank, hit in enumerate(raw_results, 1):
            payload = hit.get("payload", {})
            ranked_results.append({
                "rank": rank,
                "similarity_score": round(float(hit.get("score", 0.0)), 4),
                "point_id": hit.get("id"),
                "video_id": payload.get("video_id"),
                "track_id": payload.get("track_id"),
                "frame_number": payload.get("frame_number"),
                "timestamp": payload.get("timestamp"),
                "bbox": payload.get("bbox"),
                "confidence": payload.get("confidence"),
                "processing_job_id": payload.get("processing_job_id"),
            })

        logger.info(
            "Person search completed: found %d matches above threshold %.2f",
            len(ranked_results), threshold
        )
        return ranked_results
