# TraceVision — Database & Data Design Document

> **System:** TraceVision  
> **Databases:** PostgreSQL (Relational Metadata) + Qdrant (Vector Embeddings)  
> **Status:** Production Design  

---

## 1. Overview of the Dual-Database Architecture

TraceVision separates relational, structured data from high-dimensional feature vectors:

```mermaid
flowchart LR
    subgraph APP["FastAPI Backend"]
        API["API Services"]
    end

    subgraph RDBMS["PostgreSQL (Relational Storage)"]
        USERS["users"]
        VIDEOS["videos"]
        JOBS["processing_jobs"]
        TRACKS["detected_persons"]
        REQS["search_requests"]
        RESULTS["search_results"]
    end

    subgraph VDB["Qdrant (Vector Database)"]
        COLL["person_embeddings Collection"]
        VEC["512-dim OSNet Vectors"]
        PAYLOAD["Payload: video_id, track_id, bbox, timestamp"]
    end

    subgraph FS["Local Filesystem"]
        FILES["Raw Videos & Query Photos"]
    end

    API -->|"CRUD Metadata"| RDBMS
    API -->|"Cosine Similarity Query"| VDB
    API -->|"Store / Stream Media"| FS
    TRACKS -.->|"track_id & video_id cross-reference"| PAYLOAD
```

### Why Separate PostgreSQL and Qdrant?
1. **Relational Consistency:** User accounts, video metadata, processing job states, and track lifespans require ACID transactions, foreign key constraints (`ON DELETE CASCADE`), and complex relational joins.
2. **Vector Retrieval Efficiency:** Re-identifying people from surveillance footage requires searching across thousands of 512-dimensional floating-point vectors. Traditional relational databases are poorly suited for high-throughput approximate nearest neighbor (ANN) search. Qdrant delivers sub-millisecond cosine similarity search using HNSW graphs with SIMD acceleration.
3. **Storage Decoupling:** Large raw video binaries are kept on the local filesystem (`uploads/videos/`). Storing raw video binaries in either database would lead to storage bloat and slow backup/restore procedures.

---

## 2. PostgreSQL Relational Schema

The complete relational schema is defined in [schema.sql](file:///F:/TraceVision-POCs/database/postgres/schema.sql) and documented via the [ER Diagram](file:///F:/TraceVision-POCs/database/postgres/ER_DIAGRAM.md).

### Table Summary

| Table Name | Primary Key | Foreign Keys | Key Responsibilities |
| :--- | :--- | :--- | :--- |
| `users` | `id` (UUID) | None | System user credentials, emails, and account auditing |
| `videos` | `id` (UUID) | `user_id` → `users.id` | File system path, resolution, FPS, total frames, duration |
| `processing_jobs` | `id` (UUID) | `video_id` → `videos.id` | Pipeline progress tracking (`pending`, `processing`, `completed`, `failed`) |
| `detected_persons` | `id` (UUID) | `video_id`, `processing_job_id` | ByteTrack persistent `track_id`, time intervals, average confidence |
| `search_requests` | `id` (UUID) | `user_id` → `users.id` | Reference photo path, execution timestamp, query status |
| `search_results` | `id` (UUID) | `search_request_id`, `detected_person_id`, `video_id` | Matched frame, timestamp, bounding box, similarity score, rank |

---

## 3. Qdrant Vector Collection Design

The vector database specification is maintained in [collection_design.md](file:///F:/TraceVision-POCs/database/qdrant/collection_design.md).

### Vector Space Configuration
- **Collection:** `person_embeddings`
- **Dimensionality:** `512` (matches output of `osnet_x1_0`)
- **Distance Metric:** `Cosine`

### Vector Payload Schema
```json
{
  "video_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "track_id": 4,
  "frame_number": 412,
  "timestamp": 13.73,
  "bbox": [210, 145, 380, 490],
  "confidence": 0.92,
  "processing_job_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7"
}
```

### Indexed Payload Fields
- `video_id`: Keyword index for scoped filtering within specific cameras.
- `track_id`: Integer index for quick track-level lookups and deduplication.

---

## 4. End-to-End Data Lifecycle

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant Frontend as React Frontend
    participant API as FastAPI Backend
    participant FS as Local Filesystem
    participant PG as PostgreSQL
    participant AI as AI Engine
    participant QD as Qdrant Vector DB

    User->>Frontend: Upload target image + video(s)
    Frontend->>API: POST /api/videos/upload
    API->>FS: Save video binary to uploads/videos/
    API->>PG: INSERT INTO videos & processing_jobs
    
    API->>AI: Trigger video processing
    AI->>FS: Read video frames
    AI->>AI: YOLOX detection + ByteTrack tracking
    AI->>AI: OSNet extracts 512-dim embedding per track
    AI->>QD: Batch insert points (vector + payload)
    AI->>PG: INSERT INTO detected_persons (track metadata)
    AI->>PG: UPDATE processing_jobs (status = completed)

    User->>Frontend: Click "Launch Search Pipeline"
    Frontend->>API: POST /api/search (reference_image)
    API->>FS: Save image to uploads/references/
    API->>PG: INSERT INTO search_requests
    API->>AI: Extract OSNet embedding from reference image
    AI->>QD: Search person_embeddings (query_vector, limit=20, threshold=0.6)
    QD-->>API: Return matching point IDs & scores
    API->>PG: INSERT INTO search_results (rank, score, timestamps)
    API-->>Frontend: Return ranked match results
    Frontend-->>User: Display match cards with timestamps & bounding boxes
```
