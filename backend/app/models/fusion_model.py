import torch
import torch.nn as nn
import timm
from app.config import settings, CLASS_NAMES

class CNNViTFusion(nn.Module):
    """
    CNN + Vision Transformer Fusion Architecture
    Backbones:
      - CNN: EfficientNet-B0 (feature extractor without head, global avg pool -> 1280)
      - ViT: ViT-Small patch16 224 (feature extractor -> 384)
    Fusion Head:
      - Linear(1280 + 384 -> 256) -> BatchNorm1d(256) -> ReLU -> Dropout(0.3)
      - Classifier: Linear(256 -> 9)
    """
    def __init__(
        self,
        num_classes: int = 9,
        cnn_name: str = "efficientnet_b0",
        vit_name: str = "vit_small_patch16_224",
        fusion_hidden: int = 256,
        dropout: float = 0.3
    ):
        super().__init__()
        self.cnn = timm.create_model(cnn_name, pretrained=False, num_classes=0, global_pool="avg")
        self.vit = timm.create_model(vit_name, pretrained=False, num_classes=0)

        cnn_dim = self.cnn.num_features
        vit_dim = self.vit.num_features

        self.fusion = nn.Sequential(
            nn.Linear(cnn_dim + vit_dim, fusion_hidden),
            nn.BatchNorm1d(fusion_hidden),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout),
        )
        self.classifier = nn.Linear(fusion_hidden, num_classes)

    def forward(self, x, return_embeddings: bool = False):
        cnn_feat = self.cnn(x)
        vit_feat = self.vit(x)
        fused = torch.cat([cnn_feat, vit_feat], dim=1)
        fused = self.fusion(fused)
        logits = self.classifier(fused)
        if return_embeddings:
            return logits, fused
        return logits


def load_fusion_model(weights_path: str = None, device: str = "cpu") -> CNNViTFusion:
    path = weights_path or str(settings.PYTORCH_WEIGHTS_PATH)
    model = CNNViTFusion(num_classes=len(CLASS_NAMES) or 9)
    state_dict = torch.load(path, map_location=device, weights_only=True)
    model.load_state_dict(state_dict)
    model.to(device)
    model.eval()
    return model
