"""
Configuration for the Person Re-Identification module.

Defines model parameters, preprocessing settings, and default thresholds
for the OSNet feature extractor used in TraceVision.
"""

from dataclasses import dataclass, field
from typing import Tuple, List


@dataclass
class ReIDConfig:
    """Configuration for OSNet-based Person Re-Identification.

    Attributes:
        model_name: Name of the torchreid model to use. Default is 'osnet_x1_0',
            which provides a good balance between accuracy and speed.
            Other options: 'osnet_x0_75', 'osnet_x0_5', 'osnet_x0_25',
            'osnet_ain_x1_0', 'osnet_ibn_x1_0'.
        input_size: (height, width) expected by the model. OSNet uses 256×128.
        embedding_dim: Dimensionality of the output feature vector. OSNet produces
            512-dimensional embeddings.
        device: Torch device to run inference on ('cpu', 'cuda', 'cuda:0', etc.).
        pixel_mean: Per-channel mean for ImageNet normalization (RGB order).
        pixel_std: Per-channel std for ImageNet normalization (RGB order).
        batch_size: Maximum number of crops to process in a single forward pass.
        normalize_embeddings: Whether to L2-normalize output embeddings.
            Normalization is required for cosine similarity search in Qdrant.
    """

    model_name: str = "osnet_x1_0"
    input_size: Tuple[int, int] = (256, 128)  # (height, width)
    embedding_dim: int = 512
    device: str = "cpu"
    pixel_mean: List[float] = field(
        default_factory=lambda: [0.485, 0.456, 0.406]
    )
    pixel_std: List[float] = field(
        default_factory=lambda: [0.229, 0.224, 0.225]
    )
    batch_size: int = 32
    normalize_embeddings: bool = True

    def __post_init__(self):
        """Validate configuration values."""
        valid_models = [
            "osnet_x1_0",
            "osnet_x0_75",
            "osnet_x0_5",
            "osnet_x0_25",
            "osnet_ain_x1_0",
            "osnet_ibn_x1_0",
        ]
        if self.model_name not in valid_models:
            raise ValueError(
                f"Invalid model_name '{self.model_name}'. "
                f"Must be one of: {valid_models}"
            )

        if self.embedding_dim <= 0:
            raise ValueError("embedding_dim must be a positive integer.")

        if self.batch_size <= 0:
            raise ValueError("batch_size must be a positive integer.")

        h, w = self.input_size
        if h <= 0 or w <= 0:
            raise ValueError("input_size dimensions must be positive integers.")
