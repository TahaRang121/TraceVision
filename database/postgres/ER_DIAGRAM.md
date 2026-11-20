# TraceVision — Entity-Relationship Diagram

> [!NOTE]
> This diagram covers the PostgreSQL relational schema. Vector embeddings live in Qdrant and are referenced from `detected_persons.qdrant_point_ids`.

```mermaid
erDiagram
    users {
        UUID id PK
        VARCHAR username UK
        VARCHAR email UK
        VARCHAR password_hash
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }

    videos {
        UUID id PK
        UUID user_id FK
        VARCHAR filename
        VARCHAR original_filename
        VARCHAR file_path
        BIGINT file_size_bytes
        FLOAT duration_seconds
        FLOAT fps
        INT width
        INT height
        INT total_frames
        VARCHAR mime_type
        TIMESTAMP uploaded_at
    }

    processing_jobs {
        UUID id PK
        UUID video_id FK
        VARCHAR status
        TIMESTAMP started_at
        TIMESTAMP completed_at
        INT total_frames_processed
        INT persons_detected
        TEXT error_message
        TIMESTAMP created_at
    }

    detected_persons {
        UUID id PK
        UUID processing_job_id FK
        UUID video_id FK
        INT track_id
        INT first_frame
        INT last_frame
        FLOAT first_timestamp
        FLOAT last_timestamp
        INT total_appearances
        FLOAT avg_confidence
        TEXT_ARRAY qdrant_point_ids
        TIMESTAMP created_at
    }

    search_requests {
        UUID id PK
        UUID user_id FK
        VARCHAR reference_image_path
        VARCHAR status
        TIMESTAMP created_at
        TIMESTAMP completed_at
    }

    search_results {
        UUID id PK
        UUID search_request_id FK
        UUID detected_person_id FK
        UUID video_id FK
        FLOAT similarity_score
        INT rank
        INT matched_frame
        FLOAT matched_timestamp
        INT bbox_x1
        INT bbox_y1
        INT bbox_x2
        INT bbox_y2
        TIMESTAMP created_at
    }

    users          ||--o{ videos            : "uploads"
    users          ||--o{ search_requests   : "initiates"
    videos         ||--o{ processing_jobs   : "processed by"
    videos         ||--o{ detected_persons  : "contains"
    processing_jobs||--o{ detected_persons  : "produces"
    search_requests||--o{ search_results    : "returns"
    detected_persons||--o{ search_results   : "matched in"
    videos         ||--o{ search_results    : "referenced by"
```

## Relationship Summary

| Relationship | Cardinality | Description |
|---|---|---|
| `users` → `videos` | One-to-Many | A user can upload many videos |
| `users` → `search_requests` | One-to-Many | A user can create many search requests |
| `videos` → `processing_jobs` | One-to-Many | A video can have multiple processing runs |
| `videos` → `detected_persons` | One-to-Many | A video contains many detected person tracks |
| `processing_jobs` → `detected_persons` | One-to-Many | A single job produces many person tracks |
| `search_requests` → `search_results` | One-to-Many | A search returns multiple ranked results |
| `detected_persons` → `search_results` | One-to-Many | A detected person can appear in many search results |
| `videos` → `search_results` | One-to-Many | Search results reference the source video |

## Cross-Database Link

`detected_persons.qdrant_point_ids` stores an array of Qdrant point UUIDs, linking each PostgreSQL track to its vector embeddings in the `person_embeddings` Qdrant collection. This is the bridge between relational metadata and vector similarity search.
