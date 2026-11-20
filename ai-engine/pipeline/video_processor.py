"""
Video Processor Pipeline for TraceVision.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Integrates the full video ingestion pipeline:
1. Frame extraction via OpenCV
2. Person detection via YOLOX-Nano
3. Multi-object tracking via ByteTrack
4. Appearance feature extraction via OSNet (512-dim embeddings)
5. Vector storage into Qdrant vector database
"""

import logging
import os
import sys
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List, Optional

import cv2
import numpy as np
import torch

# ── Dynamic Path Setup for ByteTrack ──────────────────────────────────────────
ROOT_DIR = Path(__file__).resolve().parents[2]
BYTETRACK_DIR = ROOT_DIR / "person-tracking" / "third_party" / "ByteTrack"
if str(BYTETRACK_DIR) not in sys.path:
    sys.path.insert(0, str(BYTETRACK_DIR))

from yolox.exp import get_exp
from yolox.tracker.byte_tracker import BYTETracker
from yolox.tracking_utils.timer import Timer
from tools.demo_track import Predictor

from person_reid.feature_extractor import PersonFeatureExtractor
from embeddings.embedding_store import EmbeddingStore
from pipeline.pipeline_config import PipelineConfig

logger = logging.getLogger(__name__)


class VideoProcessor:
    """End-to-end video processing pipeline for TraceVision.

    Orchestrates video decoding, YOLOX-Nano detection, ByteTrack ID association,
    OSNet re-ID embedding extraction, and Qdrant vector persistence.
    """

    def __init__(
        self,
        feature_extractor: Optional[PersonFeatureExtractor] = None,
        embedding_store: Optional[EmbeddingStore] = None,
        config: Optional[PipelineConfig] = None,
    ):
        self.config = config or PipelineConfig()
        self.device = self.config.reid.device

        # 1. Initialize OSNet Re-ID Extractor & Qdrant Store
        self.feature_extractor = feature_extractor or PersonFeatureExtractor(
            model_name=self.config.reid.model_name,
            device=self.device,
            config=self.config.reid,
        )
        self.embedding_store = embedding_store or EmbeddingStore(
            host=self.config.embedding_store.host,
            port=self.config.embedding_store.port,
            collection_name=self.config.embedding_store.collection_name,
        )

        # 2. Load YOLOX-Nano Model & Pretrained Weights
        exp_path = BYTETRACK_DIR / "exps" / "default" / "nano.py"
        self.exp = get_exp(str(exp_path), None)
        self.exp.test_conf = self.config.detection.confidence_threshold  # 0.25
        self.exp.nmsthre = self.config.detection.nms_threshold          # 0.45
        self.exp.test_size = (416, 416)

        model = self.exp.get_model()
        model.eval()

        weights_path = ROOT_DIR / "person-tracking" / "models" / "yolox_nano.pth"
        if not weights_path.exists():
            weights_path = ROOT_DIR / "person-detection" / "models" / "yolox_nano.pth"

        logger.info("Loading YOLOX-Nano checkpoint from: %s", weights_path)
        checkpoint = torch.load(str(weights_path), map_location=self.device)
        model.load_state_dict(checkpoint["model"])

        # 3. Initialize Predictor & Timer
        self.predictor = Predictor(model, self.exp, device=self.device, fp16=False)
        self.timer = Timer()

        # 4. ByteTrack Default Arguments
        self.tracker_args = SimpleNamespace(
            track_thresh=self.config.tracking.track_thresh if hasattr(self.config, 'tracking') else 0.5,
            track_buffer=self.config.tracking.track_buffer if hasattr(self.config, 'tracking') else 30,
            match_thresh=self.config.tracking.match_thresh if hasattr(self.config, 'tracking') else 0.8,
            mot20=False,
            min_box_area=10,
            aspect_ratio_thresh=1.6,
        )

        logger.info("VideoProcessor successfully initialized on device: %s", self.device)

    def process_video(
        self,
        video_path: str,
        video_id: str,
        processing_job_id: str,
    ) -> Dict[str, Any]:
        """Process a video file end-to-end with YOLOX + ByteTrack + OSNet + Qdrant.

        Args:
            video_path: Absolute path to the video file on disk.
            video_id: UUID string identifying the video.
            processing_job_id: UUID string identifying the processing job.

        Returns:
            Dictionary containing processing summary statistics.
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found at: {video_path}")

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Failed to open video file: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        logger.info(
            "Processing video %s: %dx%d @ %.1f FPS (%d total frames)",
            video_id, frame_width, frame_height, fps, total_frames
        )

        # Ensure Qdrant collection exists before inserting points
        self.embedding_store.ensure_collection()

        # Initialize fresh ByteTrack tracker for this video stream
        tracker = BYTETracker(self.tracker_args, frame_rate=int(fps))

        frame_idx = 0
        frames_processed = 0
        unique_tracks = set()
        embeddings_stored = 0

        embeddings_batch = []
        metadata_batch = []
        batch_size = 32
        start_time = time.time()

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_idx += 1

            # Frame sampling for throughput optimization
            if frame_idx % self.config.frame_sample_rate != 0:
                continue

            frames_processed += 1
            timestamp = frame_idx / fps

            # Step 1: Detect persons using YOLOX-Nano
            outputs, img_info = self.predictor.inference(frame, self.timer)

            # Step 2: Track persons using ByteTrack
            if outputs[0] is not None:
                online_targets = tracker.update(
                    outputs[0],
                    [img_info["height"], img_info["width"]],
                    self.exp.test_size,
                )

                # Step 3: Extract OSNet embeddings for each tracked person
                for target in online_targets:
                    tlbr = target.tlbr
                    track_id = int(target.track_id)
                    score = float(target.score)
                    unique_tracks.add(track_id)

                    x1 = max(0, int(tlbr[0]))
                    y1 = max(0, int(tlbr[1]))
                    x2 = min(frame_width, int(tlbr[2]))
                    y2 = min(frame_height, int(tlbr[3]))

                    # Filter out degenerated or tiny boxes
                    if (x2 - x1) < 15 or (y2 - y1) < 25:
                        continue

                    # Crop person appearance patch
                    crop = frame[y1:y2, x1:x2]
                    embedding = self.feature_extractor.extract(crop)

                    embeddings_batch.append(embedding)
                    metadata_batch.append({
                        "video_id": video_id,
                        "track_id": track_id,
                        "frame_number": frame_idx,
                        "timestamp": round(timestamp, 2),
                        "bbox": [x1, y1, x2, y2],
                        "confidence": round(score, 4),
                        "processing_job_id": processing_job_id,
                    })

                    # Flush batch to Qdrant
                    if len(embeddings_batch) >= batch_size:
                        self.embedding_store.store_batch(np.array(embeddings_batch), metadata_batch)
                        embeddings_stored += len(embeddings_batch)
                        embeddings_batch.clear()
                        metadata_batch.clear()

        # Flush any remaining items in the buffer
        if embeddings_batch:
            self.embedding_store.store_batch(np.array(embeddings_batch), metadata_batch)
            embeddings_stored += len(embeddings_batch)
            embeddings_batch.clear()
            metadata_batch.clear()

        cap.release()
        elapsed_time = time.time() - start_time

        summary = {
            "video_id": video_id,
            "processing_job_id": processing_job_id,
            "total_frames_in_video": total_frames,
            "frames_processed": frames_processed,
            "unique_tracks_identified": len(unique_tracks),
            "embeddings_stored": embeddings_stored,
            "processing_time_seconds": round(elapsed_time, 2),
            "fps_achieved": round(frames_processed / max(1e-5, elapsed_time), 2),
        }

        logger.info("Video processing complete for %s: %s", video_id, summary)
        return summary