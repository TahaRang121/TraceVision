"""
Processing pipeline module for TraceVision.

Provides end-to-end video processing (detection → tracking → re-id → storage)
and query processing (reference image → embedding → similarity search).
"""

from .video_processor import VideoProcessor
from .query_processor import QueryProcessor
from .pipeline_config import PipelineConfig

__all__ = ["VideoProcessor", "QueryProcessor", "PipelineConfig"]
