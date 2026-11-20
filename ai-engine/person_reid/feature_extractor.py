"""
OSNet-based Person Feature Extractor for TraceVision.

Uses the torchreid library (deep-person-reid) to extract 512-dimensional
appearance embeddings from person crops. These embeddings are used for
person re-identification across different camera views and time frames.

Model: OSNet (Omni-Scale Network) — a lightweight CNN designed specifically
for person re-identification. It captures multi-scale features using a
unified aggregation gate, achieving state-of-the-art results on ReID
benchmarks while remaining efficient enough for real-time applications.

Reference:
    Zhou et al., "Omni-Scale Feature Learning for Person Re-Identification",
    ICCV 2019. https://arxiv.org/abs/1905.00953
"""

import logging
from typing import List, Optional

import cv2
import numpy as np
import torch
import torch.nn.functional as F
from torchvision import transforms

from .reid_config import ReIDConfig

logger = logging.getLogger(__name__)


class PersonFeatureExtractor:
    """Extracts 512-dimensional appearance embeddings from person crops
    using a pretrained OSNet model from torchreid.

    The extractor handles:
    - Loading and configuring the OSNet model
    - Preprocessing person crops (resize, normalize)
    - Extracting L2-normalized feature vectors suitable for cosine similarity

    Example:
        >>> extractor = PersonFeatureExtractor()
        >>> crop = cv2.imread("person_crop.jpg")  # BGR image
        >>> embedding = extractor.extract(crop)
        >>> print(embedding.shape)  # (512,)
    """

    def __init__(
        self,
        model_name: str = "osnet_x1_0",
        device: str = "cpu",
        config: Optional[ReIDConfig] = None,
    ):
        """Initialize the feature extractor with a pretrained OSNet model.

        Args:
            model_name: Name of the OSNet variant to load. Default: 'osnet_x1_0'.
            device: Torch device for inference ('cpu' or 'cuda').
            config: Optional ReIDConfig instance. If provided, model_name and
                device are taken from the config instead.
        """
        if config is not None:
            self.config = config
        else:
            self.config = ReIDConfig(model_name=model_name, device=device)

        self.device = torch.device(self.config.device)

        # Build the preprocessing transform pipeline
        # Input: BGR OpenCV image → RGB → resize to 256×128 → normalize
        self._transform = transforms.Compose(
            [
                transforms.ToPILImage(),
                transforms.Resize(self.config.input_size),  # (256, 128) = (H, W)
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=self.config.pixel_mean,
                    std=self.config.pixel_std,
                ),
            ]
        )

        # Load the pretrained model
        self.model = self._load_model()

        logger.info(
            "PersonFeatureExtractor initialized: model=%s, device=%s, "
            "embedding_dim=%d",
            self.config.model_name,
            self.config.device,
            self.config.embedding_dim,
        )

    def _load_model(self) -> torch.nn.Module:
        """Load a pretrained OSNet model from torchreid and configure it
        for feature extraction (inference mode).

        Returns:
            The loaded model in eval mode on the configured device.
        """
        try:
            import torchreid

            model = torchreid.models.build_model(
                name=self.config.model_name,
                num_classes=1000,  # Pretrained on ImageNet
                loss="softmax",
                pretrained=True,
            )

            model = model.to(self.device)
            model.eval()

            logger.info(
                "Loaded pretrained %s model successfully.", self.config.model_name
            )
            return model

        except ImportError:
            logger.error(
                "torchreid is not installed. Install it with: "
                "pip install torchreid  OR  "
                "pip install git+https://github.com/KaiyangZhou/deep-person-reid.git"
            )
            raise
        except Exception as e:
            logger.error("Failed to load OSNet model: %s", str(e))
            raise

    def _preprocess(self, person_crop: np.ndarray) -> torch.Tensor:
        """Preprocess a single BGR person crop for the model.

        Steps:
            1. Convert BGR (OpenCV) → RGB
            2. Resize to 256×128 (height × width)
            3. Convert to float tensor and normalize with ImageNet mean/std

        Args:
            person_crop: BGR image as a numpy array (H, W, 3).

        Returns:
            Preprocessed tensor of shape (3, 256, 128).
        """
        # OpenCV loads images in BGR; convert to RGB for the model
        rgb_crop = cv2.cvtColor(person_crop, cv2.COLOR_BGR2RGB)

        # Apply the transform pipeline
        tensor = self._transform(rgb_crop)

        return tensor

    def extract(self, person_crop: np.ndarray) -> np.ndarray:
        """Extract a 512-dimensional feature embedding from a single person crop.

        Args:
            person_crop: BGR image of a detected person as a numpy array (H, W, 3).
                This is typically a crop from a full video frame using the
                bounding box coordinates from the YOLOX-Nano detector.

        Returns:
            L2-normalized 512-dimensional feature vector as a numpy array
            of shape (512,).

        Raises:
            ValueError: If the input crop is empty or has invalid dimensions.
        """
        if person_crop is None or person_crop.size == 0:
            raise ValueError("Input person crop is empty or None.")

        if person_crop.ndim != 3 or person_crop.shape[2] != 3:
            raise ValueError(
                f"Expected a 3-channel image (H, W, 3), got shape {person_crop.shape}."
            )

        # Preprocess and add batch dimension
        input_tensor = self._preprocess(person_crop).unsqueeze(0)  # (1, 3, 256, 128)
        input_tensor = input_tensor.to(self.device)

        # Extract features (no gradient computation needed for inference)
        with torch.no_grad():
            features = self.model(input_tensor)  # (1, 512)

        # L2-normalize the embedding for cosine similarity
        if self.config.normalize_embeddings:
            features = F.normalize(features, p=2, dim=1)

        # Convert to numpy and flatten
        embedding = features.cpu().numpy().flatten()

        return embedding

    def extract_batch(self, crops: List[np.ndarray]) -> np.ndarray:
        """Extract feature embeddings from a batch of person crops.

        Processes multiple person crops efficiently in batches. If the number
        of crops exceeds the configured batch_size, they are processed in
        multiple forward passes.

        Args:
            crops: List of BGR person crop images, each as a numpy array (H, W, 3).
                Crops can have different sizes; they will all be resized to 256×128.

        Returns:
            Array of L2-normalized 512-dimensional feature vectors with shape
            (N, 512), where N is the number of input crops.

        Raises:
            ValueError: If the crops list is empty.
        """
        if not crops:
            raise ValueError("Input crops list is empty.")

        all_embeddings = []

        # Process in batches to manage GPU memory
        for batch_start in range(0, len(crops), self.config.batch_size):
            batch_crops = crops[batch_start : batch_start + self.config.batch_size]

            # Preprocess all crops in this batch
            tensors = []
            for crop in batch_crops:
                if crop is None or crop.size == 0:
                    logger.warning(
                        "Skipping empty crop at index %d",
                        batch_start + len(tensors),
                    )
                    continue
                tensors.append(self._preprocess(crop))

            if not tensors:
                continue

            # Stack into a batch tensor: (batch_size, 3, 256, 128)
            batch_tensor = torch.stack(tensors).to(self.device)

            # Extract features
            with torch.no_grad():
                features = self.model(batch_tensor)  # (batch_size, 512)

            # L2-normalize
            if self.config.normalize_embeddings:
                features = F.normalize(features, p=2, dim=1)

            all_embeddings.append(features.cpu().numpy())

        if not all_embeddings:
            return np.empty((0, self.config.embedding_dim))

        # Concatenate all batch results
        return np.concatenate(all_embeddings, axis=0)
