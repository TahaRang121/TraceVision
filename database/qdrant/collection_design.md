# TraceVision — Qdrant Collection Design

## Overview

Qdrant is used as the vector database for storing and searching person appearance embeddings extracted by **OSNet (osnet_x1_0)**. Each embedding represents a person's appearance in a single video frame, enabling cosine-similarity search to find the same person across different videos and timestamps.

---

## Collection: `person_embeddings`

### Vector Configuration

| Parameter | Value | Rationale |
|---|---|---|
| **Collection name** | `person_embeddings` | Descriptive; one collection for all person embeddings |
| **Vector dimension** | `512` | OSNet `osnet_x1_0` output dimension |
| **Distance metric** | `Cosine` | Standard for appearance similarity; normalised comparison |

### Payload Schema

Each point in the collection carries the following payload fields:

| Field | Type | Description |
|---|---|---|
| `video_id` | `keyword` (UUID string) | References `videos.id` in PostgreSQL |
| `track_id` | `integer` | ByteTrack-assigned tracking ID within the video |
| `frame_number` | `integer` | The video frame this embedding was extracted from |
| `timestamp` | `float` | Timestamp in seconds within the video |
| `bbox` | `object` | Bounding box — `{x1, y1, x2, y2}` (integers, pixel coords) |
| `confidence` | `float` | YOLOX detection confidence score |
| `processing_job_id` | `keyword` (UUID string) | References `processing_jobs.id` in PostgreSQL |

### Payload Indexes

Indexes are created on frequently filtered fields to accelerate filtered vector search:

| Field | Index Type | Purpose |
|---|---|---|
| `video_id` | `keyword` | Filter search to a specific video |
| `track_id` | `integer` | Filter search to a specific person track |

---

## Setup: Create Collection & Indexes

```python
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PayloadSchemaType,
)

client = QdrantClient(host="localhost", port=6333)

# Create the collection
client.create_collection(
    collection_name="person_embeddings",
    vectors_config=VectorParams(
        size=512,
        distance=Distance.COSINE,
    ),
)

# Create payload indexes for efficient filtered search
client.create_payload_index(
    collection_name="person_embeddings",
    field_name="video_id",
    field_schema=PayloadSchemaType.KEYWORD,
)

client.create_payload_index(
    collection_name="person_embeddings",
    field_name="track_id",
    field_schema=PayloadSchemaType.INTEGER,
)
```

---

## Example Operations

### Inserting Embeddings

After the AI pipeline processes a video, embeddings are batch-inserted into Qdrant:

```python
import uuid
from qdrant_client.models import PointStruct

# Example: insert embeddings for a detected person track
points = []
for detection in detections:
    point_id = str(uuid.uuid4())
    points.append(
        PointStruct(
            id=point_id,
            vector=detection["embedding"],  # 512-dim float list from OSNet
            payload={
                "video_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "track_id": 3,
                "frame_number": detection["frame"],
                "timestamp": detection["timestamp"],
                "bbox": {
                    "x1": detection["x1"],
                    "y1": detection["y1"],
                    "x2": detection["x2"],
                    "y2": detection["y2"],
                },
                "confidence": detection["confidence"],
                "processing_job_id": "f9e8d7c6-b5a4-3210-fedc-ba0987654321",
            },
        )
    )

# Batch upsert (Qdrant handles batching internally)
client.upsert(
    collection_name="person_embeddings",
    points=points,
)

# Store the point IDs back in PostgreSQL (detected_persons.qdrant_point_ids)
point_ids = [p.id for p in points]
```

### Searching for a Person (Similarity Search)

Given a reference image, generate its embedding with OSNet and query Qdrant:

```python
from qdrant_client.models import Filter, FieldCondition, MatchValue

# query_embedding: 512-dim list extracted from the reference image via OSNet
query_embedding = osnet_model.extract(reference_image)  # [float] × 512

# Search across ALL videos (no filter)
results = client.search(
    collection_name="person_embeddings",
    query_vector=query_embedding,
    limit=20,
    score_threshold=0.6,  # minimum cosine similarity
)

# Search within a SPECIFIC video
results_filtered = client.search(
    collection_name="person_embeddings",
    query_vector=query_embedding,
    query_filter=Filter(
        must=[
            FieldCondition(
                key="video_id",
                match=MatchValue(value="a1b2c3d4-e5f6-7890-abcd-ef1234567890"),
            )
        ]
    ),
    limit=20,
    score_threshold=0.6,
)

# Each result contains:
#   result.id        — Qdrant point UUID
#   result.score     — cosine similarity (0–1)
#   result.payload   — video_id, track_id, frame_number, timestamp, bbox, etc.
```

### Deleting Embeddings (When a Video is Removed)

```python
from qdrant_client.models import Filter, FieldCondition, MatchValue

client.delete(
    collection_name="person_embeddings",
    points_selector=Filter(
        must=[
            FieldCondition(
                key="video_id",
                match=MatchValue(value="a1b2c3d4-e5f6-7890-abcd-ef1234567890"),
            )
        ]
    ),
)
```

---

## How PostgreSQL and Qdrant Work Together

TraceVision uses a **dual-database architecture** where each database handles what it does best:

```
┌──────────────┐                        ┌──────────────┐
│  PostgreSQL  │   video_id + track_id  │    Qdrant    │
│              │◄──────────────────────►│              │
│  Structural  │                        │   Vector     │
│  Metadata    │                        │  Embeddings  │
└──────────────┘                        └──────────────┘
```

### PostgreSQL Responsibilities
- User accounts, authentication
- Video file metadata (paths, dimensions, duration)
- Processing job state machine (pending → processing → completed/failed)
- Detected person track metadata (frame ranges, timestamps, confidence)
- Search request history and ranked results
- Referential integrity via foreign keys and cascading deletes

### Qdrant Responsibilities
- Storing 512-dimensional OSNet appearance embeddings
- High-performance approximate nearest-neighbour (ANN) cosine similarity search
- Filtered vector search (e.g., search within a specific video)
- Payload-based indexing for fast filtering

### The Search Flow (End to End)

1. **User uploads a reference image** → Backend extracts a 512-dim query embedding via OSNet.
2. **Qdrant similarity search** → Returns top-K matching points with `video_id`, `track_id`, `frame_number`, `similarity_score`, and `bbox`.
3. **PostgreSQL join** → Using `video_id` and `track_id` from Qdrant results, the backend queries `detected_persons` to get the full track info (first/last frame, timestamps, total appearances) and `videos` to get the video file path and metadata.
4. **Compose results** → The backend merges Qdrant scores with PostgreSQL metadata and writes ranked rows to `search_results`.
5. **Frontend display** → React renders results with video player, timestamps, bounding box overlays, and similarity scores.

### Data Consistency

- When a **video is deleted** from PostgreSQL (`ON DELETE CASCADE`), the backend must also delete all corresponding points from Qdrant (filtered by `video_id`). This is handled at the application layer since there is no cross-database foreign key.
- The `detected_persons.qdrant_point_ids` array in PostgreSQL stores the Qdrant point UUIDs, providing a bidirectional link between the two databases.
