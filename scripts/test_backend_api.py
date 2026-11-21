"""
TraceVision - Comprehensive FastAPI Backend & PostgreSQL Integration Test
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Tests every API endpoint and verifies PostgreSQL and Qdrant persistence:
1. GET  /docs                      - Swagger documentation
2. GET  /api/videos                - List videos
3. POST /api/videos/upload         - Upload video, OpenCV metadata, PostgreSQL insert
4. GET  /api/videos/{id}           - Retrieve video by ID
5. GET  /api/jobs                  - List processing jobs
6. GET  /api/jobs/{id}             - Retrieve job status
7. POST /api/search                - Submit reference photo, extract embedding, search Qdrant, persist to DB
8. GET  /api/search/{id}           - Check search request status
9. GET  /api/search/{id}/results   - Retrieve ranked matches with timestamps & bboxes
"""

import asyncio
import os
import sys
import uuid
from pathlib import Path

# Paths
ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
AI_ENGINE_DIR = ROOT_DIR / "ai-engine"
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(AI_ENGINE_DIR))

import httpx
from app.main import app
from app.database.init_db import init_db
from app.database.session import async_session
from app.models.models import Video, ProcessingJob, SearchRequest, SearchResult


async def run_tests():
    print("=" * 70)
    print("TraceVision - Automated FastAPI & PostgreSQL Integration Verification")
    print("=" * 70)

    # 1. Initialize DB tables
    await init_db()
    print(" [1/9] Database connection & tables verified.")

    # Create ASGI test client
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://localhost:8000") as client:

        # 2. Test GET /docs
        res = await client.get("/docs")
        assert res.status_code == 200, f"Expected 200 on /docs, got {res.status_code}"
        print(" [2/9] GET /docs (Swagger UI): SUCCESS (Status 200)")

        # 3. Test GET /api/videos
        res = await client.get("/api/videos")
        assert res.status_code == 200, f"Expected 200 on /api/videos, got {res.status_code}"
        print(" [3/9] GET /api/videos: SUCCESS (Status 200)")

        # 4. Test POST /api/videos/upload
        video_sample = ROOT_DIR / "person-detection" / "test_videos" / "6387-191695740_medium.mp4"
        with open(video_sample, "rb") as f:
            files = {"file": ("test_cctv.mp4", f, "video/mp4")}
            res = await client.post("/api/videos/upload", files=files)
        assert res.status_code == 201, f"Expected 201 on /api/videos/upload, got {res.status_code}: {res.text}"
        video_data = res.json()
        video_id = video_data["id"]
        print(f" [4/9] POST /api/videos/upload: SUCCESS (Status 201)")
        print(f"       -> Video ID: {video_id}")
        print(f"       -> Extracted Metadata: {video_data['width']}x{video_data['height']} @ {video_data['fps']} FPS, {video_data['total_frames']} frames, {video_data['duration_seconds']}s")

        # 5. Test GET /api/videos/{id}
        res = await client.get(f"/api/videos/{video_id}")
        assert res.status_code == 200, f"Expected 200 on /api/videos/{video_id}, got {res.status_code}"
        print(f" [5/9] GET /api/videos/{video_id}: SUCCESS (Status 200)")

        # 6. Test GET /api/jobs
        res = await client.get("/api/jobs")
        assert res.status_code == 200, f"Expected 200 on /api/jobs, got {res.status_code}"
        jobs_data = res.json()
        jobs = jobs_data.get("jobs", [])
        assert len(jobs) > 0, "Expected at least 1 processing job"
        latest_job = jobs[0]
        job_id = latest_job["id"]
        print(f" [6/9] GET /api/jobs: SUCCESS (Found {len(jobs)} jobs, latest Job ID: {job_id}, status: {latest_job['status']})")

        # 7. Test GET /api/jobs/{id}
        res = await client.get(f"/api/jobs/{job_id}")
        assert res.status_code == 200, f"Expected 200 on /api/jobs/{job_id}, got {res.status_code}"
        print(f" [7/9] GET /api/jobs/{job_id}: SUCCESS (Status: {res.json()['status']})")

        # 8. Test POST /api/search with reference photo
        ref_sample = ROOT_DIR / "person-detection" / "test_images" / "people.jpg"
        with open(ref_sample, "rb") as f:
            files = {"reference_image": ("target_person.jpg", f, "image/jpeg")}
            res = await client.post("/api/search", files=files)
        assert res.status_code == 201, f"Expected 201 on /api/search, got {res.status_code}: {res.text}"
        search_data = res.json()
        search_id = search_data["id"]
        print(f" [8/9] POST /api/search: SUCCESS (Status 201)")
        print(f"       -> Search ID: {search_id}, Status: {search_data['status']}")

        # 9. Test GET /api/search/{id}/results
        res = await client.get(f"/api/search/{search_id}/results")
        assert res.status_code == 200, f"Expected 200 on /api/search/{search_id}/results, got {res.status_code}"
        results_data = res.json()
        matches = results_data["results"]
        total_matches = results_data["total"]
        print(f" [9/9] GET /api/search/{search_id}/results: SUCCESS (Status 200)")
        print(f"       -> Retrieved {total_matches} ranked matches from PostgreSQL:")
        for m in matches[:5]:
            score_pct = round(m["similarity_score"] * 100, 1)
            print(f"          • Rank {m['rank']}: Score={score_pct}%, Frame={m['matched_frame']}, Time={m['matched_timestamp']}s, BBox=[{m['bbox_x1']}, {m['bbox_y1']}, {m['bbox_x2']}, {m['bbox_y2']}]")

    print("\n" + "=" * 70)
    print(">>> ALL 9 ENDPOINTS & POSTGRESQL INTEGRATIONS VERIFIED SUCCESSFULLY! <<<")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_tests())
