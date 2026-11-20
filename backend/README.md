# TraceVision — Backend API Service

FastAPI-based REST API backend for **TraceVision**, handling video uploads, job orchestration, person re-identification search queries, and relational metadata persistence.

---

## 1. Overview

The backend service serves as the core coordinator between:
1. **Frontend (React.js)** — Receives user actions (video uploads, reference photo upload, search triggers) and serves results.
2. **PostgreSQL** — Stores persistent relational data: videos, processing jobs, detected person tracks, and search history.
3. **Qdrant Vector Database** — Handles 512-dimensional vector similarity search for Person Re-Identification.
4. **AI Engine** — Coordinates detection (YOLOX-Nano), tracking (ByteTrack), and feature extraction (OSNet).

---

## 2. Directory Structure

```text
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app instance, CORS, lifespan & static mount
│   ├── config.py            # Pydantic settings & env management
│   ├── database/
│   │   ├── __init__.py
│   │   ├── session.py       # Async SQLAlchemy session factory & get_db dependency
│   │   └── init_db.py       # Table creation & upload folder bootstrap
│   ├── models/
│   │   ├── __init__.py
│   │   └── models.py        # SQLAlchemy 2.0 ORM models matching PostgreSQL schema
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── schemas.py       # Pydantic v2 validation & response schemas
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── videos.py        # /api/videos (upload, list, detail)
│   │   ├── search.py        # /api/search (create search, check status, get results)
│   │   └── jobs.py          # /api/jobs (list jobs, job status)
│   └── services/
│       ├── __init__.py
│       ├── video_service.py # OpenCV video metadata extraction & disk storage
│       ├── search_service.py # Qdrant vector search & result assembly
│       └── processing_service.py # Job tracking & AI pipeline trigger
├── requirements.txt
└── README.md
```

---

## 3. API Endpoints

### Videos (`/api/videos`)
- `POST /api/videos/upload` — Multipart form upload. Validates format (`.mp4`, `.avi`, `.mov`, etc.), extracts video properties (FPS, resolution, duration, frames) using OpenCV, saves to `uploads/videos/`, registers in PostgreSQL, and queues a processing job.
- `GET /api/videos` — Returns paginated list of uploaded videos and summary stats.
- `GET /api/videos/{video_id}` — Returns detailed video metadata.

### Search (`/api/search`)
- `POST /api/search` — Accepts a person reference image (multipart). Saves to `uploads/references/`, creates a `search_requests` entry, and triggers similarity search.
- `GET /api/search/{search_id}` — Check status of search request (`pending`, `processing`, `completed`, `failed`).
- `GET /api/search/{search_id}/results` — Retrieves ranked matches with video details, timestamps, bounding boxes, and similarity scores.

### Jobs (`/api/jobs`)
- `GET /api/jobs` — Lists all background processing jobs.
- `GET /api/jobs/{job_id}` — Returns status, frames processed, and detection counts for a specific job.

---

## 4. Setup and Installation

### Prerequisites
- Python 3.10+
- PostgreSQL 14+ (optional for API testing; defaults to `localhost:5432`)
- Qdrant (Docker or standalone on `localhost:6333`)

### Step 1: Create Virtual Environment
```bash
cd F:\TraceVision-POCs\backend
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Configure Environment
Create a `.env` file in the `backend/` directory or rely on defaults in `app/config.py`:
```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/tracevision
QDRANT_HOST=localhost
QDRANT_PORT=6333
UPLOAD_DIR=F:\TraceVision-POCs\uploads
```

### Step 4: Run the Development Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Access the interactive Swagger API documentation at:
`http://localhost:8000/docs`

---

## 5. Current Implementation vs. Planned Pipeline

| Feature | Current State | Target State |
| :--- | :--- | :--- |
| Video Upload & Storage | ✅ Fully Implemented (OpenCV metadata extraction) | Cloud storage / MinIO integration |
| PostgreSQL Models | ✅ Fully Implemented (SQLAlchemy 2.0 async) | Alembic automated migrations |
| REST Endpoints | ✅ Fully Implemented (/videos, /search, /jobs) | Auth / JWT protection |
| AI Pipeline Trigger | 🔲 Hooked via `ProcessingService` (placeholder) | Celery / Redis background worker queue |
| Qdrant Search | 🔲 Architecture ready, mock results returned | Live OSNet vector search query |
