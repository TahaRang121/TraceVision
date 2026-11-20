# TraceVision — Presentation Talking Points

> **Occasion:** College Major Project Review (Tuesday Presentation)  
> **Topic:** TraceVision — AI-Powered Person Search Across Video Footage  
> **Presenter Guide:** Structured notes with time allocations and anticipated Q&A.  

---

## 1. Project Motivation & Problem Statement (Time: 1.5 mins)

- **The Real-World Problem:** Security teams and forensic investigators frequently need to find a missing child, a suspect, or a specific VIP across hours of CCTV surveillance from multiple camera feeds.
- **Current Limitation:** Manual human review is slow, prone to fatigue, and virtually impossible across dozens of concurrent camera streams.
- **Our Solution — TraceVision:** An automated AI platform where an operator supplies a single reference image of a person and video recordings. TraceVision automatically detects all people, tracks their movements, computes deep visual embeddings, and retrieves every appearance of the target individual with exact timestamps in seconds.

---

## 2. Technical Architecture & Stack (Time: 2 mins)

- **Frontend:** React.js Single Page Application built on modern component architecture (interactive drag-and-drop file ingestion, real-time progress banners, and ranked match visualization).
- **Backend:** Python FastAPI asynchronous REST API handling multipart uploads, video metadata extraction (OpenCV), and background job orchestration.
- **Relational Metadata:** PostgreSQL storing users, videos, processing jobs, and detected person tracks with full referential integrity.
- **Vector Search Engine:** Qdrant Vector Database executing sub-millisecond approximate nearest neighbor (ANN) search over 512-dimensional appearance vectors.
- **AI/CV Pipeline:**
  1. **Detection:** YOLOX-Nano (lightweight anchor-free detector, 416×416 input, 25+ FPS on GPU).
  2. **Tracking:** ByteTrack (associates detections across frames using Kalman filters and low-confidence box recovery to maintain persistent IDs across occlusions).
  3. **Re-Identification:** OSNet (`osnet_x1_0`, Omni-Scale Network extracting 512-dimensional appearance embeddings invariant to camera viewpoint and slight illumination changes).

---

## 3. What We Have Built vs. Roadmap (Time: 2 mins)

### ✅ Completed Proofs of Concept (POCs)
1. **Person Detection POC (`person-detection/`):**
   - Successfully validated YOLOX-Nano on both local CPU and NVIDIA Tesla T4 GPU (Google Colab).
   - Achieved 25.88 FPS inference on 341 video frames with zero dropped detections.
2. **Person Tracking POC (`person-tracking/`):**
   - Successfully integrated ByteTrack tracking with persistent ID assignments across frames.
   - Bounding boxes and track IDs persisted across brief camera occlusions.

### 🔲 Draft System Architecture & Design
- **FastAPI Backend:** Complete API models, schemas, and routes for videos, search, and job monitoring.
- **React Frontend:** Production-grade dark mode UI with interactive search workflow and demonstration mode.
- **Database Architecture:** Complete PostgreSQL `schema.sql`, ER diagram, and Qdrant collection design (`512` dims, `Cosine` distance).
- **AI Integration Engine:** End-to-end `VideoProcessor` pipeline and `QueryProcessor` search engine connecting detection, tracking, OSNet, and Qdrant.

---

## 4. Key Technical Decisions & Justifications (Time: 1.5 mins)

| Decision | Why We Chose It | Alternative Considered & Why Rejected |
| :--- | :--- | :--- |
| **YOLOX-Nano** | Extremely lightweight (0.91M params), fast on edge/CPU, high recall on small targets. | YOLOv5/v8 large (too compute heavy for multi-stream CCTV). |
| **ByteTrack** | Recovers low-confidence boxes, drastically reducing track fragmentation during occlusions. | SORT / DeepSORT (DeepSORT is slower due to per-box CNN calls during tracking). |
| **OSNet ReID** | Omni-Scale residual blocks capture fine-grained and coarse features simultaneously; produces compact 512-dim vectors. | ResNet-50 (2048 dims, 4x larger memory footprint in vector DB). |
| **Dual DB (Postgres + Qdrant)** | Keeps relational metadata separate from vector indexing; optimal performance for both paradigms. | Single DB with pgvector (pgvector is less optimized for large-scale multi-camera ANN queries compared to dedicated Qdrant). |

---

## 5. Live Demonstration Flow for the Panel (Time: 2 mins)

1. **Step 1: Open TraceVision Web Interface (`http://localhost:5173/`)**
   - Point out the clean dark-mode interface and responsive architecture.
2. **Step 2: Navigate to "Search Person"**
   - Demonstrate drag-and-drop of the target individual's reference photograph.
   - Show multi-video selection and upload validation.
3. **Step 3: Trigger Search Pipeline**
   - Explain what is happening under the hood (Frame decoding → YOLOX detection → ByteTrack tracking → OSNet ReID embedding → Qdrant vector index).
4. **Step 4: Review Ranked Match Cards**
   - Show how matches are ordered by similarity score (e.g. 94.2% at 13.7s, 88.7% at 24.0s).
   - Highlight track IDs, video names, and exact bounding box coordinates.

---

## 6. Likely Panel Questions & Sample Answers

**Q: Why don't you do tracking directly with the ReID model?**  
*A:* Calling a deep ReID network on every single bounding box in every single frame would bottleneck the system down to 2-4 FPS. Instead, we use ByteTrack with lightweight Kalman filtering for real-time tracking, and sample representative crops per track for OSNet feature extraction. This gives us 25+ FPS real-time speed.

**Q: Where are the large video files stored?**  
*A:* They are stored on the dedicated local filesystem or object storage (MinIO/S3). Neither PostgreSQL nor Qdrant stores video binaries; they only store paths and metadata, preventing database bloat.

**Q: What if the person changes their clothes?**  
*A:* Person ReID models like OSNet rely on appearance, color, and silhouette. If a subject completely changes clothing, appearance-based ReID faces an inherent challenge; future scope includes multi-modal biometrics (gait analysis and facial recognition fusion).
