"""
Jobs Routes
~~~~~~~~~~~
API endpoints for monitoring video processing jobs.
"""

import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.schemas import ProcessingJobResponse, ProcessingJobListResponse
from app.services.processing_service import ProcessingService

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.get("", response_model=ProcessingJobListResponse)
async def list_jobs(
    db: AsyncSession = Depends(get_db),
):
    """List all video processing jobs, newest first."""
    jobs = await ProcessingService.get_all(db=db)
    return ProcessingJobListResponse(
        jobs=jobs,
        total=len(jobs),
    )


@router.get("/{job_id}", response_model=ProcessingJobResponse)
async def get_job(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve status and metrics of a specific processing job by UUID."""
    job = await ProcessingService.get_by_id(job_id=job_id, db=db)
    if not job:
        raise HTTPException(status_code=404, detail="Processing job not found")
    return job
