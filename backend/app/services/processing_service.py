"""
Processing Service
~~~~~~~~~~~~~~~~~~~
Manages video processing jobs — creation, status tracking, and
(placeholder) AI pipeline triggering.

NOTE: The actual AI pipeline integration is a PLACEHOLDER. The real
implementation will invoke YOLOX-Nano → ByteTrack → OSNet → Qdrant.
"""

import logging
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.models import ProcessingJob, DetectedPerson
from app.database.session import async_session

# Ensure ai-engine is in sys.path
ROOT_DIR = Path(__file__).resolve().parents[3]
AI_ENGINE_DIR = ROOT_DIR / "ai-engine"
if str(AI_ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(AI_ENGINE_DIR))

from pipeline.video_processor import VideoProcessor

logger = logging.getLogger(__name__)


class ProcessingService:
    """Service for managing video processing jobs and executing AI pipeline."""

    _video_processor: Optional[VideoProcessor] = None

    @classmethod
    def get_video_processor(cls) -> VideoProcessor:
        """Singleton accessor for VideoProcessor."""
        if cls._video_processor is None:
            cls._video_processor = VideoProcessor()
        return cls._video_processor

    @staticmethod
    async def create_job(
        video_id: uuid.UUID, db: AsyncSession
    ) -> ProcessingJob:
        """Create a new processing job for a video."""
        job = ProcessingJob(
            id=uuid.uuid4(),
            video_id=video_id,
            status="pending",
            created_at=datetime.utcnow(),
        )
        db.add(job)
        await db.flush()
        return job

    @classmethod
    async def execute_pipeline_task(cls, video_id: uuid.UUID, video_path: str, job_id: uuid.UUID):
        """Asynchronous background worker executing YOLOX + ByteTrack + OSNet + Qdrant."""
        logger.info("Starting background AI pipeline for video %s (job %s)", video_id, job_id)
        async with async_session() as db:
            try:
                # 1. Update job to processing
                await cls.update_status(job_id=job_id, status="processing", db=db)
                await db.commit()

                # 2. Run video processing
                vp = cls.get_video_processor()
                summary = vp.process_video(
                    video_path=video_path,
                    video_id=str(video_id),
                    processing_job_id=str(job_id),
                )

                # 3. Insert detected persons into PostgreSQL
                for t in summary.get("tracks", []):
                    dp = DetectedPerson(
                        id=uuid.uuid4(),
                        processing_job_id=job_id,
                        video_id=video_id,
                        track_id=t.get("track_id"),
                        first_frame=t.get("first_frame"),
                        last_frame=t.get("last_frame"),
                        first_timestamp=t.get("first_timestamp"),
                        last_timestamp=t.get("last_timestamp"),
                        total_appearances=t.get("total_appearances"),
                        avg_confidence=t.get("avg_confidence"),
                    )
                    db.add(dp)

                # 4. Update job to completed
                await cls.update_status(
                    job_id=job_id,
                    status="completed",
                    db=db,
                    total_frames_processed=summary.get("frames_processed"),
                    persons_detected=summary.get("unique_tracks_identified"),
                )
                await db.commit()
                logger.info("AI pipeline successfully completed for job %s", job_id)

            except Exception as e:
                logger.error("AI pipeline failed for job %s: %s", job_id, str(e), exc_info=True)
                await cls.update_status(
                    job_id=job_id,
                    status="failed",
                    db=db,
                    error_message=str(e),
                )
                await db.commit()

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
