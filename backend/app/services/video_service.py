"""
Video Service
~~~~~~~~~~~~~~
Handles video file uploads and metadata extraction using OpenCV.
"""

import os
import uuid
import mimetypes
from datetime import datetime
from typing import Optional

import cv2
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.models.models import Video


class VideoService:
    """Service for video upload handling and metadata extraction."""

    @staticmethod
    def _get_videos_dir() -> str:
        """Return the videos upload directory path."""
        return os.path.join(settings.UPLOAD_DIR, "videos")

    @staticmethod
    async def save_upload(file: UploadFile, db: AsyncSession) -> Video:
        """
        Save an uploaded video file to disk and extract metadata with OpenCV.

        Steps:
        1. Generate a unique filename to prevent collisions.
        2. Write the file to the uploads/videos/ directory.
        3. Use OpenCV to extract: fps, resolution (width × height),
           duration, and total frame count.
        4. Create a Video record in the database.
        5. Return the Video ORM object.
        """
        videos_dir = VideoService._get_videos_dir()
        os.makedirs(videos_dir, exist_ok=True)

        # Generate unique filename
        file_ext = os.path.splitext(file.filename)[1] if file.filename else ".mp4"
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = os.path.join(videos_dir, unique_filename)

        # Write file to disk
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        file_size = len(content)

        # Detect MIME type
        mime_type, _ = mimetypes.guess_type(file.filename or unique_filename)
        if mime_type is None:
            mime_type = "video/mp4"

        # Extract video metadata with OpenCV
        fps, width, height, total_frames, duration = VideoService._extract_metadata(file_path)

        # Create database record
        video = Video(
            id=uuid.uuid4(),
            filename=unique_filename,
            original_filename=file.filename or unique_filename,
            file_path=file_path,
            file_size_bytes=file_size,
            duration_seconds=duration,
            fps=fps,
            width=width,
            height=height,
            total_frames=total_frames,
            mime_type=mime_type,
            uploaded_at=datetime.utcnow(),
        )

        db.add(video)
        await db.flush()  # Flush to populate the ID
        return video

    @staticmethod
    def _extract_metadata(file_path: str) -> tuple:
        """
        Extract video metadata using OpenCV.

        Returns:
            (fps, width, height, total_frames, duration_seconds)
        """
        fps: Optional[float] = None
        width: Optional[int] = None
        height: Optional[int] = None
        total_frames: Optional[int] = None
        duration: Optional[float] = None

        try:
            cap = cv2.VideoCapture(file_path)
            if cap.isOpened():
                fps = cap.get(cv2.CAP_PROP_FPS)
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

                if fps and fps > 0 and total_frames and total_frames > 0:
                    duration = total_frames / fps

                cap.release()
        except Exception as e:
            print(f"⚠️  OpenCV metadata extraction failed for {file_path}: {e}")

        return fps, width, height, total_frames, duration

    @staticmethod
    async def get_all(db: AsyncSession) -> list[Video]:
        """Retrieve all uploaded videos, ordered by upload time (newest first)."""
        result = await db.execute(
            select(Video).order_by(Video.uploaded_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_by_id(video_id: uuid.UUID, db: AsyncSession) -> Optional[Video]:
        """Retrieve a single video by its UUID."""
        result = await db.execute(
            select(Video).where(Video.id == video_id)
        )
        return result.scalar_one_or_none()

    get_video_by_id = get_by_id
