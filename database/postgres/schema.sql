-- ============================================================================
-- TraceVision — PostgreSQL Database Schema
-- ============================================================================
-- Person search system: finds a target person across video footage using
-- AI-powered detection, tracking, and re-identification.
--
-- Videos are stored on the local filesystem; only paths are stored here.
-- Vector embeddings are stored in Qdrant; only Qdrant point IDs are
-- referenced from the detected_persons table.
-- ============================================================================

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- 1. USERS
-- ============================================================================
-- Registered users who upload videos and perform person searches.
CREATE TABLE users (
    id              UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    username        VARCHAR(50)     UNIQUE NOT NULL,
    email           VARCHAR(100)    UNIQUE NOT NULL,
    password_hash   VARCHAR(255)    NOT NULL,
    created_at      TIMESTAMP       NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP
);

COMMENT ON TABLE  users IS 'Registered users who upload videos and perform person searches.';
COMMENT ON COLUMN users.password_hash IS 'Bcrypt / Argon2 hashed password — never store plaintext.';

-- ============================================================================
-- 2. VIDEOS
-- ============================================================================
-- Video files uploaded by users. Binary data lives on the local filesystem;
-- only the path and metadata are stored here.
CREATE TABLE videos (
    id                  UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id             UUID            NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    filename            VARCHAR(255)    NOT NULL,
    original_filename   VARCHAR(255)    NOT NULL,
    file_path           VARCHAR(500)    NOT NULL,
    file_size_bytes     BIGINT,
    duration_seconds    FLOAT,
    fps                 FLOAT,
    width               INT,
    height              INT,
    total_frames        INT,
    mime_type           VARCHAR(50),
    uploaded_at         TIMESTAMP       NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_videos_user_id ON videos(user_id);

COMMENT ON TABLE  videos IS 'Uploaded video files. Binary data is on the local filesystem; only paths and metadata are stored.';
COMMENT ON COLUMN videos.filename IS 'Server-side filename (may be sanitised / UUID-prefixed).';
COMMENT ON COLUMN videos.original_filename IS 'Original filename as provided by the user at upload time.';
COMMENT ON COLUMN videos.file_path IS 'Absolute path to the video file on the server filesystem.';

-- ============================================================================
-- 3. PROCESSING JOBS
-- ============================================================================
-- One job per video — tracks the detection → tracking → re-id pipeline run.
CREATE TABLE processing_jobs (
    id                      UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    video_id                UUID            NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    status                  VARCHAR(20)     NOT NULL DEFAULT 'pending',
    started_at              TIMESTAMP,
    completed_at            TIMESTAMP,
    total_frames_processed  INT,
    persons_detected        INT,
    error_message           TEXT,
    created_at              TIMESTAMP       NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_processing_jobs_status
        CHECK (status IN ('pending', 'processing', 'completed', 'failed'))
);

CREATE INDEX idx_processing_jobs_video_id ON processing_jobs(video_id);
CREATE INDEX idx_processing_jobs_status   ON processing_jobs(status);

COMMENT ON TABLE  processing_jobs IS 'AI processing pipeline runs (detection → tracking → re-id) for each video.';
COMMENT ON COLUMN processing_jobs.status IS 'Job state: pending → processing → completed | failed.';
COMMENT ON COLUMN processing_jobs.error_message IS 'Populated only when status = failed.';

-- ============================================================================
-- 4. DETECTED PERSONS
-- ============================================================================
-- Each unique person track produced by ByteTrack within a processed video.
-- Links to Qdrant via qdrant_point_ids (array of Qdrant point UUIDs for
-- the appearance embeddings belonging to this track).
CREATE TABLE detected_persons (
    id                  UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    processing_job_id   UUID            NOT NULL REFERENCES processing_jobs(id) ON DELETE CASCADE,
    video_id            UUID            NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    track_id            INT             NOT NULL,
    first_frame         INT             NOT NULL,
    last_frame          INT             NOT NULL,
    first_timestamp     FLOAT           NOT NULL,
    last_timestamp      FLOAT           NOT NULL,
    total_appearances   INT,
    avg_confidence      FLOAT,
    qdrant_point_ids    TEXT[],
    created_at          TIMESTAMP       NOT NULL DEFAULT NOW()
);

-- Composite index: quickly look up a specific track within a video
CREATE UNIQUE INDEX idx_detected_persons_video_track
    ON detected_persons(video_id, track_id);

CREATE INDEX idx_detected_persons_processing_job
    ON detected_persons(processing_job_id);

COMMENT ON TABLE  detected_persons IS 'Unique person tracks detected by ByteTrack in a processed video.';
COMMENT ON COLUMN detected_persons.track_id IS 'ByteTrack-assigned persistent tracking ID within the video.';
COMMENT ON COLUMN detected_persons.qdrant_point_ids IS 'Array of Qdrant point IDs storing the 512-dim OSNet embeddings for this track.';

-- ============================================================================
-- 5. SEARCH REQUESTS
-- ============================================================================
-- A user-initiated search: "find this person across all processed videos."
CREATE TABLE search_requests (
    id                      UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id                 UUID            NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    reference_image_path    VARCHAR(500)    NOT NULL,
    status                  VARCHAR(20)     NOT NULL DEFAULT 'pending',
    created_at              TIMESTAMP       NOT NULL DEFAULT NOW(),
    completed_at            TIMESTAMP,

    CONSTRAINT chk_search_requests_status
        CHECK (status IN ('pending', 'processing', 'completed', 'failed'))
);

CREATE INDEX idx_search_requests_user_id ON search_requests(user_id);
CREATE INDEX idx_search_requests_status  ON search_requests(status);

COMMENT ON TABLE  search_requests IS 'User-initiated person search using a reference image.';
COMMENT ON COLUMN search_requests.reference_image_path IS 'Path to the uploaded reference image on the server filesystem.';

-- ============================================================================
-- 6. SEARCH RESULTS
-- ============================================================================
-- Ranked matches returned by a similarity search against Qdrant, enriched
-- with PostgreSQL metadata.
CREATE TABLE search_results (
    id                  UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    search_request_id   UUID            NOT NULL REFERENCES search_requests(id) ON DELETE CASCADE,
    detected_person_id  UUID            NOT NULL REFERENCES detected_persons(id) ON DELETE CASCADE,
    video_id            UUID            NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    similarity_score    FLOAT           NOT NULL,
    rank                INT             NOT NULL,
    matched_frame       INT,
    matched_timestamp   FLOAT,
    bbox_x1             INT,
    bbox_y1             INT,
    bbox_x2             INT,
    bbox_y2             INT,
    created_at          TIMESTAMP       NOT NULL DEFAULT NOW()
);

-- Index for fetching results in ranked order for a given search
CREATE INDEX idx_search_results_request_rank
    ON search_results(search_request_id, rank);

CREATE INDEX idx_search_results_detected_person
    ON search_results(detected_person_id);

COMMENT ON TABLE  search_results IS 'Ranked person matches from a similarity search, with bounding box and score.';
COMMENT ON COLUMN search_results.similarity_score IS 'Cosine similarity score (0–1) returned by Qdrant.';
COMMENT ON COLUMN search_results.rank IS 'Result rank (1 = best match).';
