"""
TraceVision — SQLAlchemy ORM Models
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Mirrors the PostgreSQL schema exactly. All primary keys are UUIDs
generated server-side. Relationships are defined for convenient joins.
"""

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Column,
    String,
    Float,
    Integer,
    BigInteger,
    DateTime,
    ForeignKey,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Declarative base for all TraceVision models."""
    pass


# ── Users ─────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    videos: Mapped[List["Video"]] = relationship("Video", back_populates="user", cascade="all, delete-orphan")
    search_requests: Mapped[List["SearchRequest"]] = relationship("SearchRequest", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username})>"


# ── Videos ────────────────────────────────────────────────────────────────────

class Video(Base):
    __tablename__ = "videos"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    fps: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    total_frames: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", back_populates="videos")
    processing_jobs: Mapped[List["ProcessingJob"]] = relationship("ProcessingJob", back_populates="video", cascade="all, delete-orphan")
    detected_persons: Mapped[List["DetectedPerson"]] = relationship("DetectedPerson", back_populates="video", cascade="all, delete-orphan")
    search_results: Mapped[List["SearchResult"]] = relationship("SearchResult", back_populates="video", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Video(id={self.id}, filename={self.original_filename})>"


# ── Processing Jobs ───────────────────────────────────────────────────────────

class ProcessingJob(Base):
    __tablename__ = "processing_jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    video_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )  # pending | processing | completed | failed
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    total_frames_processed: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    persons_detected: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    video: Mapped["Video"] = relationship("Video", back_populates="processing_jobs")
    detected_persons: Mapped[List["DetectedPerson"]] = relationship("DetectedPerson", back_populates="processing_job", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<ProcessingJob(id={self.id}, status={self.status})>"


# ── Detected Persons ──────────────────────────────────────────────────────────

class DetectedPerson(Base):
    __tablename__ = "detected_persons"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    processing_job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("processing_jobs.id", ondelete="CASCADE"), nullable=False
    )
    video_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False
    )
    track_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    first_frame: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    last_frame: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    first_timestamp: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    last_timestamp: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_appearances: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    avg_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    qdrant_point_ids: Mapped[Optional[list]] = mapped_column(
        ARRAY(String), nullable=True
    )  # Array of Qdrant point IDs (stored as strings)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    processing_job: Mapped["ProcessingJob"] = relationship("ProcessingJob", back_populates="detected_persons")
    video: Mapped["Video"] = relationship("Video", back_populates="detected_persons")
    search_results: Mapped[List["SearchResult"]] = relationship("SearchResult", back_populates="detected_person", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<DetectedPerson(id={self.id}, track_id={self.track_id})>"


# ── Search Requests ───────────────────────────────────────────────────────────

class SearchRequest(Base):
    __tablename__ = "search_requests"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )
    reference_image_path: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )  # pending | processing | completed | failed
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", back_populates="search_requests")
    search_results: Mapped[List["SearchResult"]] = relationship("SearchResult", back_populates="search_request", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<SearchRequest(id={self.id}, status={self.status})>"


# ── Search Results ────────────────────────────────────────────────────────────

class SearchResult(Base):
    __tablename__ = "search_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    search_request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("search_requests.id", ondelete="CASCADE"), nullable=False
    )
    detected_person_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("detected_persons.id", ondelete="CASCADE"), nullable=False
    )
    video_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False
    )
    similarity_score: Mapped[float] = mapped_column(Float, nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    matched_frame: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    matched_timestamp: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bbox_x1: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bbox_y1: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bbox_x2: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bbox_y2: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    search_request: Mapped["SearchRequest"] = relationship("SearchRequest", back_populates="search_results")
    detected_person: Mapped["DetectedPerson"] = relationship("DetectedPerson", back_populates="search_results")
    video: Mapped["Video"] = relationship("Video", back_populates="search_results")

    def __repr__(self) -> str:
        return f"<SearchResult(id={self.id}, rank={self.rank}, score={self.similarity_score})>"
