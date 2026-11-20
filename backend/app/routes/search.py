"""
Search Routes
~~~~~~~~~~~~~
API endpoints for creating person search requests and retrieving similarity search results.
"""

import os
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.session import get_db
from app.schemas.schemas import SearchRequestResponse, SearchResultsListResponse
from app.services.search_service import SearchService

router = APIRouter(prefix="/search", tags=["Search"])


@router.post("", response_model=SearchRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_search(
    reference_image: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Initiate a person search using a reference image.

    - Stores reference image in `uploads/references/`
    - Creates a search request record in PostgreSQL
    - In full pipeline: Extracts 512-dim embedding with OSNet and searches Qdrant
    - Returns SearchRequest with UUID and status
    """
    if not reference_image.filename:
        raise HTTPException(status_code=400, detail="No reference image provided")

    valid_extensions = (".jpg", ".jpeg", ".png", ".webp", ".bmp")
    if not reference_image.filename.lower().endswith(valid_extensions):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported image format. Supported: {', '.join(valid_extensions)}"
        )

    # Save reference image to disk
    references_dir = os.path.join(settings.UPLOAD_DIR, "references")
    os.makedirs(references_dir, exist_ok=True)

    file_ext = os.path.splitext(reference_image.filename)[1]
    unique_filename = f"ref_{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(references_dir, unique_filename)

    content = await reference_image.read()
    with open(file_path, "wb") as f:
        f.write(content)

    # Create search request in DB
    search_req = await SearchService.create_search_request(
        reference_image_path=file_path,
        db=db,
    )

    return search_req


@router.get("/{search_id}", response_model=SearchRequestResponse)
async def get_search_request(
    search_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get the status of a specific search request."""
    search_req = await SearchService.get_search_request(search_id=search_id, db=db)
    if not search_req:
        raise HTTPException(status_code=404, detail="Search request not found")
    return search_req


@router.get("/{search_id}/results", response_model=SearchResultsListResponse)
async def get_search_results(
    search_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve ranked similarity search results for a given search request.
    Includes matched timestamps, bounding boxes, video details, and similarity scores.
    """
    search_req, results = await SearchService.get_search_results(search_id=search_id, db=db)
    if not search_req:
        raise HTTPException(status_code=404, detail="Search request not found")

    return SearchResultsListResponse(
        search_request=search_req,
        results=results,
        total=len(results),
    )
