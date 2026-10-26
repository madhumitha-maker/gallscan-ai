import torch
from fastapi import APIRouter
from app.config import settings, CLASS_NAMES
from app.models.schemas import HealthResponse

router = APIRouter(tags=["Health"])

@router.get("/health", response_model=HealthResponse)
def health_check():
    onnx_exists = settings.ONNX_MODEL_PATH.exists()
    pytorch_exists = settings.PYTORCH_WEIGHTS_PATH.exists()
    device = "cuda" if torch.cuda.is_available() else "cpu"

    return HealthResponse(
        status="healthy" if (onnx_exists and pytorch_exists) else "degraded",
        onnx_loaded=onnx_exists,
        pytorch_loaded=pytorch_exists,
        device=device,
        num_classes=len(CLASS_NAMES),
        classes=CLASS_NAMES,
        disclaimer=settings.CLINICAL_DISCLAIMER
    )
