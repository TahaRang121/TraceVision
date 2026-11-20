# TraceVision — AI Processing Engine

The AI core of **TraceVision**, combining lightweight object detection, multi-target tracking, deep person re-identification, and vector similarity retrieval.

---

## 1. Overview

The AI Engine processes unstructured surveillance and video files into structured, searchable person embeddings. It bridges computer vision models and vector databases:

```text
[ Video Input ]
       │
       ▼
[ OpenCV ] ─── Frame Extraction & Preprocessing
       │
       ▼
[ YOLOX-Nano ] ─── Real-Time Person Detection (COCO Class 0)
       │
       ▼
[ ByteTrack ] ─── Multi-Object Tracking (Persistent Track IDs)
       │
       ▼
[ OSNet (osnet_x1_0) ] ─── 512-dim Appearance Embedding Extraction
       │
       ▼
[ Qdrant Vector DB ] ─── Vector Indexing & Cosine Similarity Search
```

---

## 2. Directory Layout

```text
ai-engine/
├── person_reid/
│   ├── __init__.py
│   ├── feature_extractor.py   # OSNet feature extraction wrapper (512-dim)
│   └── reid_config.py         # Model parameters, input size (256x128), normalizations
├── embeddings/
│   ├── __init__.py
│   └── embedding_store.py     # Qdrant client wrapper (collection creation, indexing, search)
├── pipeline/
│   ├── __init__.py
│   ├── video_processor.py     # End-to-end video ingestion & track embedding generator
│   ├── query_processor.py     # Reference image query embedding & similarity matcher
│   └── pipeline_config.py     # Modular pipeline hyperparameters
├── requirements.txt
└── README.md
```

---

## 3. Models and Technology Details

### A. Detection: YOLOX-Nano
- **Input Resolution:** 416 × 416
- **Confidence Threshold:** 0.25
- **NMS Threshold:** 0.45
- **Class Filter:** Class ID 0 (Person)
- **Role:** Detects bounding boxes for every person in a frame. Developed and verified in `person-detection/`.

### B. Tracking: ByteTrack
- **Matching Mechanism:** Kalman Filter prediction + IoU association
- **Track Threshold:** 0.50
- **Track Buffer:** 30 frames (retains tracks across brief occlusions)
- **Role:** Associates person detections across sequential frames, giving each unique person a persistent `track_id`. Developed in `person-tracking/`.

### C. Person Re-Identification: OSNet (`osnet_x1_0`)
- **Architecture:** Omni-Scale Network (captures multi-scale features with omni-scale residual blocks).
- **Input Dimensions:** 256 × 128 (Height × Width), normalized using ImageNet mean `[0.485, 0.456, 0.406]` and std `[0.229, 0.224, 0.225]`.
- **Output:** 512-dimensional L2-normalized vector embedding.
- **Role:** Generates an identity signature invariant to camera angles, lighting variations, and minor posture changes.

### D. Vector Index: Qdrant
- **Collection Name:** `person_embeddings`
- **Vector Dimension:** 512
- **Distance Metric:** `Cosine`
- **Payload Indexing:** `video_id` (keyword), `track_id` (integer)

---

## 4. Setup and Usage

### Requirements Installation
```bash
cd F:\TraceVision-POCs\ai-engine
pip install -r requirements.txt
```

### Running a Person Search Query
```python
from pipeline.query_processor import QueryProcessor

# Initialize processor (connects to Qdrant on localhost:6333)
qp = QueryProcessor()

# Search using a reference photo
matches = qp.search_person(
    reference_image_path="path/to/target_person.jpg",
    limit=10,
    threshold=0.60
)

for m in matches:
    print(f"Rank {m['rank']}: Video {m['video_id']}, Track {m['track_id']}, Time: {m['timestamp']:.2f}s, Score: {m['similarity_score']}")
```

---

## 5. Implementation Status

| Component | Status | Notes |
| :--- | :--- | :--- |
| **YOLOX-Nano POC** | ✅ Completed | Fully validated in `person-detection/` |
| **ByteTrack POC** | ✅ Completed | Fully validated in `person-tracking/` |
| **OSNet Feature Extractor** | ✅ Implemented | 512-dim extraction with `PersonFeatureExtractor` |
| **Qdrant Embedding Store** | ✅ Implemented | Collection setup, batch payload ingestion, cosine search |
| **Video Processor Pipeline** | ✅ Implemented | Modular pipeline with adapter hooks for POCs |
| **Query Processor** | ✅ Implemented | Reference photo embedding extraction & retrieval |
