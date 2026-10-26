import io
from typing import Tuple
import numpy as np
from PIL import Image
import torch
from app.config import PREPROCESSING_CONFIG

def load_and_preprocess_image(image_bytes: bytes) -> Tuple[np.ndarray, torch.Tensor, Image.Image]:
    """
    Preprocess image for both ONNX and PyTorch inference.
    Exact match with preprocessing_config.json:
      - Resize: 224 x 224 (Bilinear)
      - Color mode: RGB
      - Normalize: ImageNet mean [0.485, 0.456, 0.406], std [0.229, 0.224, 0.225]
    
    Returns:
      - numpy_batch: (1, 3, 224, 224) float32 array for ONNX Runtime
      - torch_tensor: (1, 3, 224, 224) float32 PyTorch tensor for Grad-CAM
      - original_pil: PIL.Image of the 224x224 RGB image (for visualization overlay)
    """
    img_size = PREPROCESSING_CONFIG.get("img_size", 224)
    mean = np.array(PREPROCESSING_CONFIG.get("normalize_mean", [0.485, 0.456, 0.406]), dtype=np.float32)
    std = np.array(PREPROCESSING_CONFIG.get("normalize_std", [0.229, 0.224, 0.225]), dtype=np.float32)

    # Open image with PIL and convert to RGB
    pil_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    resized_pil = pil_img.resize((img_size, img_size), Image.Resampling.BILINEAR)

    # Convert to numpy array in range [0, 1]
    img_np = np.array(resized_pil, dtype=np.float32) / 255.0

    # Normalize (H, W, C)
    norm_img = (img_np - mean) / std

    # Transpose to (C, H, W)
    transposed = np.transpose(norm_img, (2, 0, 1)).astype(np.float32)

    # Expand batch dimension (1, C, H, W)
    numpy_batch = np.expand_dims(transposed, axis=0)
    torch_tensor = torch.from_numpy(numpy_batch)

    return numpy_batch, torch_tensor, resized_pil
