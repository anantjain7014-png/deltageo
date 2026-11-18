import io
import numpy as np
from PIL import Image, ImageOps
from typing import Tuple, List, Optional
import scipy.ndimage as ndi

class ImagePreprocessor:
    """
    Satellite Imagery Preprocessing Service for Bi-temporal Change Detection (Sentinel-2, LISS-4, Optical).
    Handles format decoding, radiometric alignment, spatial tiling, and tensor normalization.
    """

    def __init__(self, target_size: Tuple[int, int] = (256, 256)):
        self.target_size = target_size

    def decode_image_bytes(self, image_bytes: bytes) -> np.ndarray:
        """Decodes raw byte stream into an RGB uint8 NumPy array."""
        try:
            image = Image.open(io.BytesIO(image_bytes))
            image = ImageOps.exif_transpose(image)
            image = image.convert("RGB")
            return np.array(image, dtype=np.uint8)
        except Exception as e:
            raise ValueError(f"Failed to decode image bytes: {str(e)}")

    def align_radiometry(self, img_t1: np.ndarray, img_t2: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Applies radiometric normalization to balance atmospheric and illumination 
        variations between bi-temporal acquisition dates without altering structural differences.
        """
        norm_t1 = img_t1.astype(np.float32)
        norm_t2 = img_t2.astype(np.float32)

        # Match mean and standard deviation per channel of T2 to T1 for background baseline
        for c in range(3):
            mean1, std1 = np.mean(norm_t1[..., c]), np.std(norm_t1[..., c]) + 1e-5
            mean2, std2 = np.mean(norm_t2[..., c]), np.std(norm_t2[..., c]) + 1e-5
            # Gentle histogram matching / shift
            norm_t2[..., c] = np.clip((norm_t2[..., c] - mean2) * (std1 / std2) * 0.3 + (norm_t2[..., c] * 0.7) + (mean1 - mean2) * 0.2, 0, 255)

        return img_t1, norm_t2.astype(np.uint8)

    def prepare_input_tensors(
        self, 
        img_t1: np.ndarray, 
        img_t2: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, Tuple[int, int]]:
        """
        Prepares normalized float32 tensors [1, H, W, 3] scaled to [0.0, 1.0].
        Returns (tensor_t1, tensor_t2, original_dimensions).
        """
        orig_h, orig_w = img_t1.shape[:2]

        # Resize to target input shape (e.g. 256x256)
        pil_t1 = Image.fromarray(img_t1).resize(self.target_size, Image.Resampling.BILINEAR)
        pil_t2 = Image.fromarray(img_t2).resize(self.target_size, Image.Resampling.BILINEAR)

        arr_t1 = np.array(pil_t1, dtype=np.float32) / 255.0
        arr_t2 = np.array(pil_t2, dtype=np.float32) / 255.0

        tensor_t1 = np.expand_dims(arr_t1, axis=0)
        tensor_t2 = np.expand_dims(arr_t2, axis=0)

        return tensor_t1, tensor_t2, (orig_h, orig_w)

    def extract_spectral_indices(self, rgb_image: np.ndarray) -> dict:
        """
        Calculates remote sensing optical indices from RGB channels:
        - Visible Atmospherically Resistant Index (VARI) for vegetation: (G - R) / (G + R - B + eps)
        - Red-Green Ratio Index (RGRI): R / (G + eps)
        - Brightness / Built-up Index proxy: (R + G + B) / 3
        """
        img_f = rgb_image.astype(np.float32) / 255.0
        r, g, b = img_f[..., 0], img_f[..., 1], img_f[..., 2]
        eps = 1e-5

        vari = (g - r) / (g + r - b + eps)
        brightness = (r + g + b) / 3.0
        structural_gradient = np.abs(r - g) + np.abs(g - b)

        return {
            "vari": np.clip(vari, -1.0, 1.0),
            "brightness": brightness,
            "structural_gradient": structural_gradient
        }
