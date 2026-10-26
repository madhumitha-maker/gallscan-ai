import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session
from app.config import settings, DISPLAY_NAMES
from app.db.database import get_db
from app.db import crud
from app.db.models import User
from app.auth.dependencies import get_current_user
from app.inference.preprocess import load_and_preprocess_image
from app.inference.onnx_infer import get_onnx_predictor
from app.inference.gradcam import get_gradcam_explainer
from app.models.schemas import PredictResponse

router = APIRouter(tags=["Inference"])

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}

@router.post("/predict", response_model=PredictResponse)
async def predict_scan(
    file: UploadFile = File(...),
    notes: str = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Validate filename extension
    filename = file.filename or "scan.png"
    ext = "." + filename.split(".")[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS and not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Please upload an ultrasound image (JPG, PNG, WEBP, BMP, TIFF)."
        )

    try:
        contents = await file.read()
        if len(contents) == 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")

        # Preprocess
        numpy_batch, torch_tensor, pil_img = load_and_preprocess_image(contents)

        # 1. Run ONNX Inference
        predictor = get_onnx_predictor()
        pred_result = predictor.predict(numpy_batch)

        predicted_class = pred_result["predicted_class"]
        confidence = pred_result["confidence"]
        top_1_item = pred_result["top_1_item"]
        top_3_items = pred_result["top_3_items"]
        class_probabilities = pred_result["class_probabilities"]

        # 2. Run PyTorch Grad-CAM
        explainer = get_gradcam_explainer()
        uid = f"scan_{uuid.uuid4().hex[:12]}"
        rel_orig_url, rel_gradcam_url = explainer.generate_heatmap(
            input_tensor=torch_tensor,
            target_class_idx=top_1_item.class_id,
            original_pil=pil_img,
            save_prefix=uid
        )

        # 3. Persist in Database
        prediction_record = crud.create_prediction(
            db=db,
            user_id=current_user.id,
            filename=filename,
            predicted_class=predicted_class,
            confidence=confidence,
            class_probabilities=class_probabilities,
            original_image_path=rel_orig_url,
            gradcam_image_path=rel_gradcam_url,
            notes=notes
        )

        # 4. Trigger Notification
        display_label = DISPLAY_NAMES.get(predicted_class, predicted_class)
        conf_pct = f"{confidence * 100:.1f}%"
        crud.create_notification(
            db=db,
            user_id=current_user.id,
            title="Analysis Complete",
            message=f"Ultrasound scan '{filename}' analysis completed: {display_label} ({conf_pct} confidence). Grad-CAM heatmap generated.",
            notif_type="analysis_complete"
        )

        return PredictResponse(
            id=prediction_record.id,
            filename=filename,
            predicted_class=predicted_class,
            predicted_display_name=display_label,
            confidence=confidence,
            top_3_predictions=top_3_items,
            class_probabilities=class_probabilities,
            original_image_url=rel_orig_url,
            gradcam_image_url=rel_gradcam_url,
            disclaimer=settings.CLINICAL_DISCLAIMER,
            created_at=prediction_record.created_at
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference error during scan processing: {str(e)}"
        )
