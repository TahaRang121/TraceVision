"""
TraceVision — Pydantic Schemas
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Request and response schemas for the REST API.
"""

import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


# ── Video Schemas ─────────────────────────────────────────────────────────────

class VideoResponse(BaseModel):
    """Response schema for a single video."""
    id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    filename: str
    original_filename: str
    file_path: str
    file_size_bytes: Optional[int] = None
    duration_seconds: Optional[float] = None
    fps: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None
    total_frames: Optional[int] = None
    mime_type: Optional[str] = None
    uploaded_at: datetime

    model_config = {"from_attributes": True}


class VideoListResponse(BaseModel):
    """Response schema for a list of videos."""
    videos: List[VideoResponse]
    total: int


# ── Processing Job Schemas ────────────────────────────────────────────────────

class ProcessingJobResponse(BaseModel):
    """Response schema for a single processing job."""
    id: uuid.UUID
    video_id: uuid.UUID
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_frames_processed: Optional[int] = None
    persons_detected: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ProcessingJobListResponse(BaseModel):
    """Response schema for a list of processing jobs."""
    jobs: List[ProcessingJobResponse]
    total: int


# ── Search Schemas ────────────────────────────────────────────────────────────

class SearchRequestResponse(BaseModel):
    """Response schema for a search request."""
    id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    reference_image_path: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class DetectedPersonInfo(BaseModel):
    """Nested schema for detected person details within search results."""
    id: uuid.UUID
    track_id: Optional[int] = None
    first_frame: Optional[int] = None
    last_frame: Optional[int] = None
    first_timestamp: Optional[float] = None
    last_timestamp: Optional[float] = None
    total_appearances: Optional[int] = None
    avg_confidence: Optional[float] = None

    model_config = {"from_attributes": True}


class VideoInfo(BaseModel):
    """Nested schema for video details within search results."""
    id: uuid.UUID
    original_filename: str
    duration_seconds: Optional[float] = None
    fps: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None

    model_config = {"from_attributes": True}


class SearchResultResponse(BaseModel):
    """Response schema for a single search result with enriched details."""
    id: uuid.UUID
    search_request_id: uuid.UUID
    detected_person_id: uuid.UUID
    video_id: uuid.UUID
    similarity_score: float
    rank: int
    matched_frame: Optional[int] = None
    matched_timestamp: Optional[float] = None
    bbox_x1: Optional[float] = None
    bbox_y1: Optional[float] = None
    bbox_x2: Optional[float] = None
    bbox_y2: Optional[float] = None
    created_at: datetime

    # Enriched nested objects (populated by the search service)
    detected_person: Optional[DetectedPersonInfo] = None
    video: Optional[VideoInfo] = None

    model_config = {"from_attributes": True}


class SearchResultsListResponse(BaseModel):
    """Response schema for search results list."""
    search_request: SearchRequestResponse
    results: List[SearchResultResponse]
    total: int


# ── Error Schema ──────────────────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    """Standard error response."""
    detail: str
