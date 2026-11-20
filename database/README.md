# TraceVision — Database Layer

## Overview

TraceVision uses a **dual-database architecture** optimised for person search across video footage:

| Database | Role | Stores |
|---|---|---|
| **PostgreSQL** | Relational metadata | Users, video metadata, processing jobs, detected person tracks, search history & results |
| **Qdrant** | Vector similarity search | 512-dim OSNet appearance embeddings for every detected person crop |

> [!IMPORTANT]
> Video files are **never** stored in either database. They live on the local filesystem; only file paths are recorded in PostgreSQL.

---

## Directory Structure

```
database/
├── README.md                          ← You are here
├── postgres/
│   ├── schema.sql                     ← Full PostgreSQL schema (tables, indexes, constraints)
│   └── ER_DIAGRAM.md                  ← Mermaid ER diagram with relationship descriptions
└── qdrant/
    └── collection_design.md           ← Qdrant collection config, payload schema, example code
```

---

## How the Two Databases Complement Each Other

```
User uploads video
        │
        ▼
┌──────────────────┐    file path    ┌────────────────┐
│   Local Storage   │◄──────────────│   PostgreSQL    │
│   (video files)   │               │   (metadata)    │
└──────────────────┘               └───────┬────────┘
                                           │ video_id
                                           │ track_id
                                           ▼
                                   ┌────────────────┐
                                   │     Qdrant      │
                                   │  (embeddings)   │
                                   └────────────────┘
```

- **PostgreSQL** handles everything relational: user auth, video metadata, job state tracking, person track metadata, and search result history. Foreign keys and cascading deletes ensure referential integrity.
- **Qdrant** handles the computationally expensive part: storing 512-dimensional appearance vectors and performing fast approximate nearest-neighbour (ANN) cosine similarity search.
- The two are linked by `video_id` and `track_id` fields present in both Qdrant payloads and PostgreSQL tables. The `detected_persons.qdrant_point_ids` column stores the Qdrant point UUIDs for bidirectional lookup.

---

## Setup Instructions

### Prerequisites

- **PostgreSQL 14+** — [Download](https://www.postgresql.org/download/)
- **Qdrant 1.7+** — [Download](https://qdrant.tech/documentation/guides/installation/)
- **Python 3.9+** with `psycopg2` / `asyncpg` and `qdrant-client`

### 1. PostgreSQL Setup

```bash
# Create the database
createdb tracevision

# Apply the schema
psql -d tracevision -f database/postgres/schema.sql
```

**Environment variables** (configure in `.env`):

```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=tracevision
POSTGRES_USER=tracevision_user
POSTGRES_PASSWORD=<your-secure-password>
```

### 2. Qdrant Setup

**Option A — Docker (recommended):**

```bash
docker run -p 6333:6333 -p 6334:6334 \
    -v $(pwd)/qdrant_storage:/qdrant/storage \
    qdrant/qdrant
```

**Option B — Binary:**

```bash
# Download from https://github.com/qdrant/qdrant/releases
./qdrant
```

**Create the collection** (run once):

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PayloadSchemaType

client = QdrantClient(host="localhost", port=6333)

client.create_collection(
    collection_name="person_embeddings",
    vectors_config=VectorParams(size=512, distance=Distance.COSINE),
)

client.create_payload_index("person_embeddings", "video_id", PayloadSchemaType.KEYWORD)
client.create_payload_index("person_embeddings", "track_id", PayloadSchemaType.INTEGER)
```

**Environment variables:**

```env
QDRANT_HOST=localhost
QDRANT_PORT=6333
```

### 3. Verify Setup

```python
# Quick check — PostgreSQL
import psycopg2
conn = psycopg2.connect(dbname="tracevision", user="tracevision_user", password="...")
cur = conn.cursor()
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public';")
print(cur.fetchall())
# Expected: [('users',), ('videos',), ('processing_jobs',), ('detected_persons',),
#            ('search_requests',), ('search_results',)]

# Quick check — Qdrant
from qdrant_client import QdrantClient
client = QdrantClient(host="localhost", port=6333)
info = client.get_collection("person_embeddings")
print(f"Vectors: {info.vectors_count}, Dimension: {info.config.params.vectors.size}")
# Expected: Vectors: 0, Dimension: 512
```

---

## Key Design Decisions

| Decision | Rationale |
|---|---|
| UUID primary keys | Globally unique, safe for distributed systems, no sequential guessing |
| `ON DELETE CASCADE` on all FKs | Deleting a user/video cleanly removes all dependent data |
| CHECK constraints on status fields | Enforces valid state machine transitions at the DB level |
| `qdrant_point_ids TEXT[]` in `detected_persons` | Bidirectional link between PostgreSQL and Qdrant without tight coupling |
| Composite unique index on `(video_id, track_id)` | Prevents duplicate tracks; enables fast lookups |
| Cosine distance in Qdrant | Standard for normalised appearance embeddings; values in [0, 1] |
| Videos on filesystem, not in DB | Avoids bloating the database; enables direct file serving |

---

## Further Reading

- [PostgreSQL Schema](postgres/schema.sql) — Full DDL with indexes, constraints, and comments
- [ER Diagram](postgres/ER_DIAGRAM.md) — Visual entity-relationship diagram (Mermaid)
- [Qdrant Collection Design](qdrant/collection_design.md) — Vector config, payload schema, example Python code
