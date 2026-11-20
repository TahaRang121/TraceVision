"""
Processing Service
~~~~~~~~~~~~~~~~~~~
Manages video processing jobs — creation, status tracking, and
(placeholder) AI pipeline triggering.

NOTE: The actual AI pipeline integration is a PLACEHOLDER. The real
implementation will invoke YOLOX-Nano → ByteTrack → OSNet → Qdrant.
"""

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.models import ProcessingJob


class ProcessingService:
    """Service for managing video processing jobs."""

    @staticmethod
    async def create_job(
        video_id: uuid.UUID, db: AsyncSession
    ) -> ProcessingJob:
        """
        Create a new processing job for a video.

        In the full system, this would kick off the AI pipeline:
        1. Frame extraction via OpenCV
        2. Person detection via YOLOX-Nano
        3. Person tracking via ByteTrack
        4. Appearance embedding via OSNet
        5. Embedding storage in Qdrant

        For now, it just creates a 'pending' job record.
        """
        job = ProcessingJob(
            id=uuid.uuid4(),
            video_id=video_id,
            status="pending",
            created_at=datetime.utcnow(),
        )
        db.add(job)
        await db.flush()

        # ──────────────────────────────────────────────────────────────────
        # TODO: Trigger AI processing pipeline
        # ──────────────────────────────────────────────────────────────────
        # This is where the real processing would happen, either:
        #
        # Option A — Synchronous (simple, for small videos):
        #   await _run_pipeline(job.id, video_id, db)
        #
        # Option B — Background task (recommended for production):
        #   background_tasks.add_task(_run_pipeline, job.id, video_id)
        #
        # Option C — Celery / task queue (best for scalability):
        #   celery_app.send_task("process_video", args=[str(job.id), str(video_id)])
        #
        # The pipeline would:
        #   1. Update job.status → "processing", job.started_at → now()
        #   2. Open video with OpenCV, iterate frames
        #   3. Run YOLOX-Nano detection on each frame → bounding boxes
        #   4. Feed detections to ByteTrack → tracking IDs
        #   5. Crop detected persons, run OSNet → 512-dim embeddings
        #   6. Store embeddings in Qdrant with metadata
        #   7. Create DetectedPerson records in PostgreSQL
        #   8. Update job.status → "completed", set persons_detected, etc.
        # ──────────────────────────────────────────────────────────────────

        return job

    @staticmethod
    async def get_all(db: AsyncSession) -> List[ProcessingJob]:
        """Retrieve all processing jobs, newest first."""
        result = await db.execute(
            select(ProcessingJob).order_by(ProcessingJob.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_by_id(
        job_id: uuid.UUID, db: AsyncSession
    ) -> Optional[ProcessingJob]:
        """Retrieve a single processing job by its UUID."""
        result = await db.execute(
            select(ProcessingJob).where(ProcessingJob.id == job_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update_status(
        job_id: uuid.UUID,
        status: str,
        db: AsyncSession,
        error_message: Optional[str] = None,
        total_frames_processed: Optional[int] = None,
        persons_detected: Optional[int] = None,
    ) -> Optional[ProcessingJob]:
        """
        Update the status of a processing job.

        Used by the AI pipeline to report progress and completion.
        """
        result = await db.execute(
            select(ProcessingJob).where(ProcessingJob.id == job_id)
        )
        job = result.scalar_one_or_none()

        if job is None:
            return None

        job.status = status

        if status == "processing" and job.started_at is None:
            job.started_at = datetime.utcnow()

        if status in ("completed", "failed"):
            job.completed_at = datetime.utcnow()

        if error_message is not None:
            job.error_message = error_message

        if total_frames_processed is not None:
            job.total_frames_processed = total_frames_processed

        if persons_detected is not None:
            job.persons_detected = persons_detected

        await db.flush()
        return job
