"""
Qdrant-based Embedding Store for TraceVision.

Provides a client wrapper for storing and querying 512-dimensional person
appearance embeddings in a Qdrant vector database. Supports:
- Creating and managing collections with cosine similarity distance
- Storing embeddings with rich metadata (video, track, frame info)
- Similarity search for person re-identification queries
- Filtered search within specific video subsets

Qdrant is used as the vector database because it:
- Natively supports cosine similarity distance (ideal for L2-normalized embeddings)
- Provides payload filtering for scoping searches to specific videos
- Scales well for the expected workload of a person search system
- Has a simple Python client API
"""

import logging
import uuid
from typing import Any, Dict, List, Optional

import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models

logger = logging.getLogger(__name__)


class EmbeddingStore:
    """Qdrant client wrapper for storing and querying person embeddings.

    Each stored embedding (point) contains:
    - A 512-dimensional vector (the OSNet appearance embedding)
    - A payload with metadata: video_id, track_id, frame_number,
      timestamp, bbox, confidence, processing_job_id

    Example:
        >>> store = EmbeddingStore(host="localhost", port=6333)
        >>> store.ensure_collection()
        >>> point_id = store.store_embedding(
        ...     embedding=np.random.randn(512).astype(np.float32),
        ...     video_id="vid-001",
        ...     track_id=1,
        ...     frame_number=42,
        ...     timestamp=1.4,
        ...     bbox=[100, 200, 150, 400],
        ...     confidence=0.92,
        ...     processing_job_id="job-001",
        ... )
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        collection_name: str = "person_embeddings",
    ):
        """Initialize the Qdrant client and store configuration.

        Args:
            host: Qdrant server hostname.
            port: Qdrant server HTTP port (default 6333).
            collection_name: Name of the Qdrant collection for person embeddings.
        """
        self.host = host
        self.port = port
        self.collection_name = collection_name
        self._vector_size = 512  # OSNet embedding dimensionality

        self.client = QdrantClient(host=self.host, port=self.port)

        logger.info(
            "EmbeddingStore initialized: host=%s, port=%d, collection=%s",
            self.host,
            self.port,
            self.collection_name,
        )

    def ensure_collection(self) -> None:
        """Create the Qdrant collection if it does not already exist.

        Collection configuration:
        - Vector size: 512 (OSNet embedding dimensionality)
        - Distance metric: Cosine (L2-normalized embeddings → cosine = dot product)
        - Optimized for the person re-identification search workload
        """
        collections = self.client.get_collections().collections
        collection_names = [c.name for c in collections]

        if self.collection_name in collection_names:
            logger.info(
                "Collection '%s' already exists. Skipping creation.",
                self.collection_name,
            )
            return

        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=qdrant_models.VectorParams(
                size=self._vector_size,
                distance=qdrant_models.Distance.COSINE,
            ),
        )

        # Create payload indexes for common filter fields to speed up searches
        self.client.create_payload_index(
            collection_name=self.collection_name,
            field_name="video_id",
            field_schema=qdrant_models.PayloadSchemaType.KEYWORD,
        )
        self.client.create_payload_index(
            collection_name=self.collection_name,
            field_name="track_id",
            field_schema=qdrant_models.PayloadSchemaType.INTEGER,
        )
        self.client.create_payload_index(
            collection_name=self.collection_name,
            field_name="processing_job_id",
            field_schema=qdrant_models.PayloadSchemaType.KEYWORD,
        )

        logger.info(
            "Created collection '%s' with vector_size=%d, distance=Cosine.",
            self.collection_name,
            self._vector_size,
        )

    def store_embedding(
        self,
        embedding: np.ndarray,
        video_id: str,
        track_id: int,
        frame_number: int,
        timestamp: float,
        bbox: List[float],
        confidence: float,
        processing_job_id: str,
    ) -> str:
        """Store a single person embedding with its metadata in Qdrant.

        Args:
            embedding: 512-dimensional feature vector from OSNet.
            video_id: UUID of the source video.
            track_id: ByteTrack tracking ID for this person across frames.
            frame_number: Frame index in the source video.
            timestamp: Time in seconds from the start of the video.
            bbox: Bounding box as [x1, y1, x2, y2] in pixel coordinates.
            confidence: Detection confidence score from YOLOX-Nano.
            processing_job_id: UUID of the processing job that generated this embedding.

        Returns:
            The UUID string of the stored point.

        Raises:
            ValueError: If the embedding has incorrect dimensions.
        """
        if embedding.shape != (self._vector_size,):
            raise ValueError(
                f"Expected embedding of shape ({self._vector_size},), "
                f"got {embedding.shape}."
            )

        point_id = str(uuid.uuid4())

        payload = {
            "video_id": video_id,
            "track_id": track_id,
            "frame_number": frame_number,
            "timestamp": timestamp,
            "bbox": bbox,
            "confidence": confidence,
            "processing_job_id": processing_job_id,
        }

        self.client.upsert(
            collection_name=self.collection_name,
            points=[
                qdrant_models.PointStruct(
                    id=point_id,
                    vector=embedding.tolist(),
                    payload=payload,
                )
            ],
        )

        logger.debug(
            "Stored embedding %s: video=%s, track=%d, frame=%d",
            point_id,
            video_id,
            track_id,
            frame_number,
        )

        return point_id

    def store_batch(
        self,
        embeddings: np.ndarray,
        metadata_list: List[Dict[str, Any]],
    ) -> List[str]:
        """Store a batch of person embeddings with metadata in Qdrant.

        More efficient than calling store_embedding() repeatedly, as it
        performs a single upsert operation for all points.

        Args:
            embeddings: Array of shape (N, 512) containing N embedding vectors.
            metadata_list: List of N dicts, each containing keys:
                video_id, track_id, frame_number, timestamp, bbox,
                confidence, processing_job_id.

        Returns:
            List of UUID strings for the stored points.

        Raises:
            ValueError: If embeddings and metadata_list have mismatched lengths,
                or if embeddings have incorrect dimensions.
        """
        if isinstance(embeddings, list):
            embeddings = np.array(embeddings)

        if len(embeddings) != len(metadata_list):
            raise ValueError(
                f"Mismatch: {len(embeddings)} embeddings vs "
                f"{len(metadata_list)} metadata entries."
            )

        if embeddings.ndim != 2 or embeddings.shape[1] != self._vector_size:
            raise ValueError(
                f"Expected embeddings of shape (N, {self._vector_size}), "
                f"got {embeddings.shape}."
            )

        points = []
        point_ids = []

        for embedding, metadata in zip(embeddings, metadata_list):
            point_id = str(uuid.uuid4())
            point_ids.append(point_id)

            points.append(
                qdrant_models.PointStruct(
                    id=point_id,
                    vector=embedding.tolist(),
                    payload=metadata,
                )
            )

        # Batch upsert — Qdrant handles this more efficiently than individual upserts
        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
        )

        logger.info("Stored batch of %d embeddings.", len(points))

        return point_ids

    def search(
        self,
        query_embedding: np.ndarray,
        limit: int = 20,
        score_threshold: float = 0.6,
    ) -> List[Dict[str, Any]]:
        """Search for similar person embeddings across all stored videos.

        Performs cosine similarity search in Qdrant and returns the top
        matching embeddings with their metadata and similarity scores.

        Args:
            query_embedding: 512-dimensional query vector (from a reference image).
            limit: Maximum number of results to return.
            score_threshold: Minimum cosine similarity score (0.0 to 1.0).
                Only results above this threshold are returned.

        Returns:
            List of match dicts, each containing:
                - id: Point UUID
                - score: Cosine similarity score
                - video_id, track_id, frame_number, timestamp, bbox,
                  confidence, processing_job_id (from stored payload)
        """
        if query_embedding.shape != (self._vector_size,):
            raise ValueError(
                f"Expected query embedding of shape ({self._vector_size},), "
                f"got {query_embedding.shape}."
            )

        if hasattr(self.client, "search"):
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding.tolist(),
                limit=limit,
                score_threshold=score_threshold,
            )
        else:
            response = self.client.query_points(
                collection_name=self.collection_name,
                query=query_embedding.tolist(),
                limit=limit,
                score_threshold=score_threshold,
            )
            results = response.points

        matches = []
        for hit in results:
            match = {
                "id": hit.id,
                "score": hit.score,
                "payload": hit.payload or {},
                **(hit.payload or {}),
            }
            matches.append(match)

        logger.info(
            "Search returned %d matches (threshold=%.2f).",
            len(matches),
            score_threshold,
        )

        return matches

    def search_in_videos(
        self,
        query_embedding: np.ndarray,
        video_ids: List[str],
        limit: int = 20,
        score_threshold: float = 0.6,
    ) -> List[Dict[str, Any]]:
        """Search for similar person embeddings within specific videos only.

        Uses Qdrant's payload filtering to restrict the search to embeddings
        from the specified video_ids, then performs cosine similarity search.

        Args:
            query_embedding: 512-dimensional query vector.
            video_ids: List of video UUIDs to search within.
            limit: Maximum number of results to return.
            score_threshold: Minimum cosine similarity score.

        Returns:
            List of match dicts (same format as search()).
        """
        if query_embedding.shape != (self._vector_size,):
            raise ValueError(
                f"Expected query embedding of shape ({self._vector_size},), "
                f"got {query_embedding.shape}."
            )

        # Build a filter to restrict search to specific videos
        video_filter = qdrant_models.Filter(
            must=[
                qdrant_models.FieldCondition(
                    key="video_id",
                    match=qdrant_models.MatchAny(any=video_ids),
                )
            ]
        )

        if hasattr(self.client, "search"):
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding.tolist(),
                query_filter=video_filter,
                limit=limit,
                score_threshold=score_threshold,
            )
        else:
            response = self.client.query_points(
                collection_name=self.collection_name,
                query=query_embedding.tolist(),
                query_filter=video_filter,
                limit=limit,
                score_threshold=score_threshold,
            )
            results = response.points

        matches = []
        for hit in results:
            match = {
                "id": hit.id,
                "score": hit.score,
                "payload": hit.payload or {},
                **(hit.payload or {}),
            }
            matches.append(match)

        logger.info(
            "Search in %d videos returned %d matches.",
            len(video_ids),
            len(matches),
        )

        return matches
