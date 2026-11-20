"""
Video Routes
~~~~~~~~~~~~
API endpoints for video uploading, listing, and metadata retrieval.
"""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.session import get_db
from app.models.models import Video
from app.schemas.schemas import VideoResponse, VideoListResponse
from app.services.video_service import VideoService
from app.services.processing_service import ProcessingService

router = APIRouter(prefix="/videos", tags=["Videos"])


@router.post("/upload", response_model=VideoResponse, status_code=status.HTTP_201_CREATED)
async def upload_video(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a video file to TraceVision.

    - Stores the video in `uploads/videos/`
    - Extracts metadata via OpenCV (fps, resolution, duration, total frames)
    - Records video metadata in PostgreSQL
    - Automatically queues a processing job for the video
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file selected")

    valid_extensions = (".mp4", ".avi", ".mov", ".mkv", ".webm")
    if not file.filename.lower().endswith(valid_extensions):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format. Supported: {', '.join(valid_extensions)}"
        )

    try:
        video = await VideoService.save_upload(file=file, db=db)
        # Automatically create processing job
        await ProcessingService.create_job(video_id=video.id, db=db)
        return video
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process video upload: {str(e)}")


@router.get("", response_model=VideoListResponse)
async def list_videos(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """List all registered videos in the system."""
    query = select(Video).offset(skip).limit(limit).order_by(Video.uploaded_at.desc())
    result = await db.execute(query)
    videos = list(result.scalars().all())

    # Count total
    count_query = select(Video)
    total_result = await db.execute(count_query)
    total = len(list(total_result.scalars().all()))

    return VideoListResponse(videos=videos, total=total)


@router.get("/{video_id}", response_model=VideoResponse)
async def get_video(
    video_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve details and metadata for a specific video by UUID."""
    video = await VideoService.get_video_by_id(video_id=video_id, db=db)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return video
