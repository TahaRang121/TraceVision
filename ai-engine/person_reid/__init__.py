"""
Person Re-Identification module for TraceVision.

Provides OSNet-based feature extraction for generating 512-dimensional
appearance embeddings from person crops detected in video frames.
"""

from .feature_extractor import PersonFeatureExtractor
from .reid_config import ReIDConfig

__all__ = ["PersonFeatureExtractor", "ReIDConfig"]
