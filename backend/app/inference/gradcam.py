import os
from typing import Tuple, Optional
import numpy as np
from PIL import Image
import cv2
import torch
import torch.nn.functional as F
from app.config import settings
from app.models.fusion_model import CNNViTFusion, load_fusion_model

class GradCAMExplainer:
    def __init__(self, model: Optional[CNNViTFusion] = None, device: str = "cpu"):
        self.device = device
        self.model = model or load_fusion_model(device=device)
        self.model.eval()
        self.target_layer = self.model.cnn.conv_head
        self.gradients = None
        self.activations = None
        self._register_hooks()

    def _register_hooks(self):
        def forward_hook(module, input, output):
            self.activations = output.detach()

        def backward_hook(module, grad_in, grad_out):
            self.gradients = grad_out[0].detach()

        self.target_layer.register_forward_hook(forward_hook)
        self.target_layer.register_full_backward_hook(backward_hook)

    def generate_heatmap(
        self,
        input_tensor: torch.Tensor,
        target_class_idx: int,
        original_pil: Image.Image,
        save_prefix: str
    ) -> Tuple[str, str]:
        """
        Generates Grad-CAM visual heatmap overlay.
        Args:
          - input_tensor: (1, 3, 224, 224) torch Tensor
          - target_class_idx: class index to explain
          - original_pil: 224x224 RGB PIL image
          - save_prefix: unique identifier/filename prefix
        
        Returns:
          - rel_original_path: relative path to saved original image
          - rel_gradcam_path: relative path to saved Grad-CAM overlay image
        """
        self.model.zero_grad()
        tensor_in = input_tensor.clone().to(self.device).requires_grad_(True)

        # Forward pass
        logits = self.model(tensor_in)
        target_score = logits[0, target_class_idx]

        # Backward pass
        target_score.backward()

        # Compute weights: GAP over gradients
        # gradients: (1, C, H, W), activations: (1, C, H, W)
        weights = torch.mean(self.gradients, dim=[2, 3], keepdim=True)
        cam = torch.sum(weights * self.activations, dim=1, keepdim=True)
        cam = F.relu(cam)  # Apply ReLU

        # Normalize to [0, 1]
        cam = cam.squeeze().cpu().numpy()
        cam_min, cam_max = cam.min(), cam.max()
        if cam_max > cam_min:
            cam_norm = (cam - cam_min) / (cam_max - cam_min)
        else:
            cam_norm = np.zeros_like(cam)

        # Resize heatmap to 224x224
        heatmap = cv2.resize(cam_norm, (224, 224), interpolation=cv2.INTER_CUBIC)
        heatmap = np.uint8(255 * heatmap)

        # Apply JET colormap
        colored_heatmap = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)
        colored_heatmap = cv2.cvtColor(colored_heatmap, cv2.COLOR_BGR2RGB)

        # Original image as RGB uint8
        orig_np = np.array(original_pil)

        # Blend original with heatmap: 60% original + 40% heatmap
        overlay = cv2.addWeighted(orig_np, 0.6, colored_heatmap, 0.4, 0)

        # Save images
        orig_filename = f"{save_prefix}_orig.png"
        cam_filename = f"{save_prefix}_gradcam.png"

        orig_full_path = settings.UPLOADS_DIR / orig_filename
        cam_full_path = settings.UPLOADS_DIR / cam_filename

        Image.fromarray(orig_np).save(orig_full_path, format="PNG")
        Image.fromarray(overlay).save(cam_full_path, format="PNG")

        rel_orig = f"/uploads/{orig_filename}"
        rel_cam = f"/uploads/{cam_filename}"

        return rel_orig, rel_cam

# Global singleton instance
gradcam_explainer: Optional[GradCAMExplainer] = None

def get_gradcam_explainer() -> GradCAMExplainer:
    global gradcam_explainer
    if gradcam_explainer is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        gradcam_explainer = GradCAMExplainer(device=device)
    return gradcam_explainer
