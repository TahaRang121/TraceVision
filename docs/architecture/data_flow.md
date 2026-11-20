# TraceVision — Data Flow

> **Project:** TraceVision — Person Search Across Video Footage  
> **Version:** 1.0  
> **Last Updated:** November 2026

---

## 1. Overview

This document maps the flow of data through TraceVision — what data moves between components, in what format, and where it is stored. TraceVision uses three distinct storage systems, each optimized for a different kind of data.

| Storage System | Purpose | Data Type |
|---|---|---|
| **Local Filesystem** | Raw media files | Video files (MP4/AVI), reference images (JPG/PNG) |
| **PostgreSQL** | Structured metadata | Video metadata, job status, track records, search history |
| **Qdrant** | Vector embeddings | 512-dim appearance vectors for similarity search |

---

## 2. End-to-End Data Flow Diagram

```mermaid
flowchart TD
    subgraph USER["👤 User"]
        IMG["Reference Image\n(JPG/PNG)"]
        VID["Video File(s)\n(MP4/AVI)"]
    end

    subgraph FRONTEND["🖥️ React Frontend"]
        UPLOAD_FORM["Upload Form"]
        SEARCH_FORM["Search Form"]
        RESULTS_VIEW["Results View"]
    end

    subgraph BACKEND["⚙️ FastAPI Backend"]
        UPLOAD_EP["POST /api/upload"]
        SEARCH_EP["POST /api/search"]
        RESULTS_EP["GET /api/results"]
        JOB_MANAGER["Job Manager"]
    end

    subgraph AI_ENGINE["🤖 AI Engine"]
        FRAME_EXT["Frame Extractor"]
        DETECTOR["Person Detector"]
        TRACKER["Person Tracker"]
        CROPPER["Person Cropper"]
        EMBEDDING_GEN["Embedding Generator"]
    end

    subgraph STORAGE["🗄️ Storage"]
        FS["📂 Filesystem\nuploads/videos/\nuploads/images/"]
        PG["🐘 PostgreSQL\nvideos, jobs,\ntracks tables"]
        QD["🔷 Qdrant\nperson_embeddings\ncollection"]
    end

    %% Upload flow
    VID -->|"multipart/form-data"| UPLOAD_FORM
    IMG -->|"multipart/form-data"| UPLOAD_FORM
    UPLOAD_FORM -->|"HTTP POST\nmultipart/form-data"| UPLOAD_EP
    UPLOAD_EP -->|"Binary file write"| FS
    UPLOAD_EP -->|"SQL INSERT\n{filename, path, size, duration}"| PG
    UPLOAD_EP -->|"Trigger async"| JOB_MANAGER

    %% Processing flow
    JOB_MANAGER -->|"video_path"| FRAME_EXT
    FRAME_EXT -->|"np.ndarray\n(H×W×3) per frame"| DETECTOR
    DETECTOR -->|"List[bbox]\n[x1,y1,x2,y2,conf]"| TRACKER
    TRACKER -->|"List[tracked_bbox]\n[x1,y1,x2,y2,track_id]"| CROPPER
    CROPPER -->|"np.ndarray\n(256×128×3)"| EMBEDDING_GEN
    EMBEDDING_GEN -->|"np.ndarray\n(512,) float32"| QD
    EMBEDDING_GEN -->|"SQL INSERT\n{video_id, track_id,\nstart_time, end_time, bboxes}"| PG

    %% Search flow
    SEARCH_FORM -->|"HTTP POST\nreference image"| SEARCH_EP
    SEARCH_EP -->|"image_path"| EMBEDDING_GEN
    EMBEDDING_GEN -->|"query vector\n(512,) float32"| SEARCH_EP
    SEARCH_EP -->|"Vector search\n{query, top_k, threshold}"| QD
    QD -->|"matched IDs +\nsimilarity scores"| SEARCH_EP
    SEARCH_EP -->|"SQL SELECT\nWHERE track_id IN (...)"| PG
    PG -->|"track metadata\n{video_id, timestamps, bboxes}"| SEARCH_EP

    %% Results flow
    SEARCH_EP -->|"JSON response"| RESULTS_VIEW
    RESULTS_VIEW -->|"HTTP GET\n/api/video/{id}"| FS

    style USER fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    style FRONTEND fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    style BACKEND fill:#fff3e0,stroke:#e65100,stroke-width:2px
    style AI_ENGINE fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    style STORAGE fill:#f3e5f5,stroke:#6a1b9a,stroke-width:2px
```

---

## 3. Data Format Between Components

### 3.1 User → Frontend

| Data | Format | Description |
|---|---|---|
| Video file(s) | MP4, AVI, MOV | Raw video footage to search through |
| Reference image | JPG, PNG | Photo of the target person |

### 3.2 Frontend → Backend

| Endpoint | Direction | Format | Payload |
|---|---|---|---|
| `POST /api/upload` | Request | `multipart/form-data` | `video: File`, `reference_image: File` |
| `POST /api/upload` | Response | `application/json` | `{"job_id": "uuid", "status": "queued"}` |
| `GET /api/jobs/{id}` | Response | `application/json` | `{"job_id": "uuid", "status": "processing", "progress": 0.45}` |
| `POST /api/search` | Request | `multipart/form-data` | `reference_image: File` |
| `POST /api/search` | Response | `application/json` | `{"search_id": "uuid", "matches": [...]}` |
| `GET /api/video/{id}` | Response | `video/mp4` | Binary video stream |

### 3.3 Backend → Filesystem

| Operation | Data Written | Location |
|---|---|---|
| Save uploaded video | Raw video bytes | `uploads/videos/{uuid}.mp4` |
| Save reference image | Raw image bytes | `uploads/images/{uuid}.jpg` |

### 3.4 Backend ↔ PostgreSQL

**Tables and their fields:**

```mermaid
erDiagram
    VIDEOS {
        uuid id PK
        string filename
        string file_path
        int file_size_bytes
        float duration_seconds
        int width
        int height
        int fps
        timestamp uploaded_at
    }

    JOBS {
        uuid id PK
        uuid video_id FK
        string status
        float progress
        timestamp created_at
        timestamp completed_at
    }

    TRACKS {
        uuid id PK
        uuid video_id FK
        int track_id
        int start_frame
        int end_frame
        float start_time
        float end_time
        json bounding_boxes
        timestamp created_at
    }

    SEARCHES {
        uuid id PK
        string reference_image_path
        json results
        timestamp searched_at
    }

    VIDEOS ||--o{ JOBS : "has"
    VIDEOS ||--o{ TRACKS : "contains"
```

### 3.5 AI Engine Internal Data Flow

| From | To | Data Format | Shape / Type |
|---|---|---|---|
| Frame Extractor | Detector | NumPy array (BGR→RGB) | `(H, W, 3)` uint8 |
| Detector | Tracker | Detection list | `List[[x1, y1, x2, y2, confidence]]` float32 |
| Tracker | Cropper | Tracked detection list | `List[[x1, y1, x2, y2, track_id]]` |
| Cropper | OSNet | Normalized person crop | `(256, 128, 3)` float32, ImageNet normalized |
| OSNet | Aggregator | Embedding vector | `(512,)` float32, L2-normalized |
| Aggregator | Qdrant | Mean embedding + metadata | `(512,)` float32 + payload dict |
| Aggregator | PostgreSQL | Track record | Dict: `{video_id, track_id, start_time, end_time, bboxes}` |

### 3.6 Backend ↔ Qdrant

| Operation | Data Sent | Data Received |
|---|---|---|
| **Upsert** (indexing) | `point_id`, `vector` (512 floats), `payload` (video_id, track_id, timestamps) | Ack |
| **Search** (querying) | `query_vector` (512 floats), `limit`, `score_threshold` | `List[{id, score, payload}]` |

---

## 4. Data Storage Locations Summary

```mermaid
flowchart LR
    subgraph FS["📂 Local Filesystem"]
        V["uploads/videos/\n*.mp4, *.avi"]
        I["uploads/images/\n*.jpg, *.png"]
    end

    subgraph PG["🐘 PostgreSQL"]
        T1["videos table\n(metadata)"]
        T2["jobs table\n(processing status)"]
        T3["tracks table\n(detections & timestamps)"]
        T4["searches table\n(search history)"]
    end

    subgraph QD["🔷 Qdrant"]
        C1["person_embeddings\ncollection"]
        C1_D["512-dim vectors\n+ payload metadata"]
    end

    C1 --- C1_D

    style FS fill:#f5f5f5,stroke:#616161,stroke-width:2px
    style PG fill:#e8eaf6,stroke:#283593,stroke-width:2px
    style QD fill:#fce4ec,stroke:#c62828,stroke-width:2px
```

| Storage | What It Holds | Why This Storage |
|---|---|---|
| **Filesystem** | Raw video files, reference images | Large binary blobs; not suitable for databases; direct read access needed by AI Engine |
| **PostgreSQL** | Video metadata, job status, track records with timestamps and bounding boxes, search history | Structured relational data requiring ACID transactions, complex queries, and joins |
| **Qdrant** | 512-dim appearance embedding vectors with track/video metadata payload | Purpose-built for high-dimensional vector similarity search; efficient cosine distance computation |

---

## 5. Data Lifecycle

```mermaid
flowchart TD
    A["1. User uploads video + image"] --> B["2. Files saved to disk"]
    B --> C["3. Metadata written to PostgreSQL"]
    C --> D["4. AI Engine reads video from disk"]
    D --> E["5. Frames extracted, persons detected & tracked"]
    E --> F["6. Person crops → OSNet → 512-dim embeddings"]
    F --> G["7. Embeddings stored in Qdrant"]
    F --> H["8. Track metadata stored in PostgreSQL"]
    
    I["9. User initiates search"] --> J["10. Reference image → OSNet → query embedding"]
    J --> K["11. Qdrant cosine similarity search"]
    K --> L["12. Matching track IDs returned"]
    L --> M["13. PostgreSQL lookup for track details"]
    M --> N["14. Results sent to frontend"]
    N --> O["15. Frontend streams matched video from disk"]

    style A fill:#e3f2fd,stroke:#1565c0
    style I fill:#e3f2fd,stroke:#1565c0
    style G fill:#fce4ec,stroke:#c62828
    style H fill:#e8eaf6,stroke:#283593
    style K fill:#fce4ec,stroke:#c62828
    style M fill:#e8eaf6,stroke:#283593
    style O fill:#f5f5f5,stroke:#616161
```

---

## 6. Data Volume Estimates

| Data Point | Estimate | Notes |
|---|---|---|
| Uploaded video size | 50–500 MB per file | Typical surveillance / smartphone video |
| Frames per minute (at 5 FPS sampling) | 300 frames | From 30 FPS source video |
| Detections per frame | 0–20 persons | Depends on scene |
| Tracks per video | 10–100+ | Depends on duration and crowd density |
| Embedding size per track | 512 × 4 bytes = 2 KB | Single float32 vector |
| PostgreSQL row per track | ~500 bytes | Metadata + serialized bbox list |
| Qdrant storage per 10K tracks | ~20 MB vectors + payload | Grows linearly with tracks |
