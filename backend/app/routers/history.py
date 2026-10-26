from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db import crud
from app.db.models import User
from app.auth.dependencies import get_current_user
from app.config import DISPLAY_NAMES, LABEL_TO_IDX
from app.models.schemas import PredictionOut, PredictionListResponse, ClassProbabilityItem

router = APIRouter(prefix="/history", tags=["History"])

def format_prediction_out(pred) -> PredictionOut:
    raw_name = pred.predicted_class
    display_name = DISPLAY_NAMES.get(raw_name, raw_name)

    # Reconstruct sorted probability items
    all_items: List[ClassProbabilityItem] = []
    if isinstance(pred.class_probabilities, dict):
        for k, v in pred.class_probabilities.items():
            prob_val = float(v)
            c_id = LABEL_TO_IDX.get(k, 0)
            d_name = DISPLAY_NAMES.get(k, k)
            all_items.append(
                ClassProbabilityItem(
                    class_id=c_id,
                    raw_name=k,
                    display_name=d_name,
                    probability=round(prob_val, 4),
                    percentage=round(prob_val * 100.0, 2)
                )
            )
    all_sorted = sorted(all_items, key=lambda x: x.probability, reverse=True)
    top_3 = all_sorted[:3]

    return PredictionOut(
        id=pred.id,
        user_id=pred.user_id,
        filename=pred.filename,
        predicted_class=raw_name,
        predicted_display_name=display_name,
        confidence=pred.confidence,
        class_probabilities=pred.class_probabilities or {},
        top_3_predictions=top_3,
        original_image_url=pred.original_image_path,
        gradcam_image_url=pred.gradcam_image_path,
        notes=pred.notes,
        created_at=pred.created_at
    )

@router.get("", response_model=PredictionListResponse)
def list_history(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    class_filter: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    skip = (page - 1) * limit
    items, total = crud.get_user_predictions(
        db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        class_filter=class_filter,
        search=search
    )
    total_pages = (total + limit - 1) // limit if total > 0 else 1

    formatted_items = [format_prediction_out(p) for p in items]
    return PredictionListResponse(
        items=formatted_items,
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages
    )

@router.get("/{prediction_id}", response_model=PredictionOut)
def get_prediction(
    prediction_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    pred = crud.get_prediction_by_id(db, prediction_id=prediction_id, user_id=current_user.id)
    if not pred:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prediction record not found."
        )
    return format_prediction_out(pred)

@router.delete("/{prediction_id}")
def delete_prediction(
    prediction_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    pred = crud.get_prediction_by_id(db, prediction_id=prediction_id, user_id=current_user.id)
    if not pred:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found.")
    db.delete(pred)
    db.commit()
    return {"message": "Record deleted successfully."}
