"""
Pipeline configuration for TraceVision.

Centralizes all configuration for the video processing pipeline, including
detection, tracking, feature extraction, and embedding storage settings.
"""

from dataclasses import dataclass, field
from typing import List, Optional

from person_reid.reid_config import ReIDConfig


@dataclass
class DetectionConfig:
    """Configuration for the YOLOX-Nano person detector.

    These values match the existing person-detection POC:
    - Input size: 416×416
    - Confidence threshold: 0.25
    - NMS threshold: 0.45
    - Person class ID: 0 (COCO dataset)

    When integrating the real YOLOX-Nano detector from person-detection/,
    these values should be passed to the detector's initialization.
    """

    model_path: str = ""  # Path to YOLOX-Nano ONNX or checkpoint
    input_size: int = 416  # Input resolution (416×416)
    confidence_threshold: float = 0.25
    nms_threshold: float = 0.45
    person_class_id: int = 0  # COCO class ID for 'person'


@dataclass
class TrackingConfig:
    """Configuration for the ByteTrack person tracker.

    These values match the existing person-tracking POC:
    - track_thresh: 0.5 (minimum detection score for tracking)
    - track_buffer: 30 (frames to keep lost tracks alive)
    - match_thresh: 0.8 (IoU threshold for matching detections to tracks)

    When integrating the real ByteTrack tracker from person-tracking/,
    these values should be passed to the BYTETracker initialization.
    """

    track_thresh: float = 0.5
    track_buffer: int = 30
    match_thresh: float = 0.8
    frame_rate: int = 30  # Used for track buffer calculation


@dataclass
class EmbeddingStoreConfig:
    """Configuration for the Qdrant embedding store."""

    host: str = "localhost"
    port: int = 6333
    collection_name: str = "person_embeddings"


@dataclass
class PipelineConfig:
    """Top-level configuration for the entire TraceVision processing pipeline.

    Aggregates configurations for all pipeline stages:
    1. Frame extraction (OpenCV)
    2. Person detection (YOLOX-Nano)
    3. Person tracking (ByteTrack)
    4. Feature extraction (OSNet)
    5. Embedding storage (Qdrant)

    Attributes:
        detection: YOLOX-Nano detector configuration.
        tracking: ByteTrack tracker configuration.
        reid: OSNet feature extractor configuration.
        embedding_store: Qdrant connection and collection settings.
        frame_sample_rate: Process every Nth frame for efficiency. Set to 1
            to process every frame; higher values skip frames to reduce
            processing time at the cost of potentially missing some detections.
        min_crop_size: Minimum bounding box size (pixels) to extract features
            from. Very small crops produce unreliable embeddings.
        max_persons_per_frame: Maximum number of detected persons to process
            per frame. Limits processing for crowded scenes.
    """

    detection: DetectionConfig = field(default_factory=DetectionConfig)
    tracking: TrackingConfig = field(default_factory=TrackingConfig)
    reid: ReIDConfig = field(default_factory=ReIDConfig)
    embedding_store: EmbeddingStoreConfig = field(
        default_factory=EmbeddingStoreConfig
    )
    frame_sample_rate: int = 5  # Process every 5th frame
    min_crop_size: int = 50  # Minimum bbox width or height in pixels
    max_persons_per_frame: int = 50

    def __post_init__(self):
        """Validate pipeline configuration."""
        if self.frame_sample_rate < 1:
            raise ValueError("frame_sample_rate must be >= 1.")
        if self.min_crop_size < 1:
            raise ValueError("min_crop_size must be >= 1.")
        if self.max_persons_per_frame < 1:
            raise ValueError("max_persons_per_frame must be >= 1.")
