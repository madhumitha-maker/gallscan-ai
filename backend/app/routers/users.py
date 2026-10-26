from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db import crud
from app.db.models import User
from app.auth.dependencies import get_current_user
from app.auth.security import verify_password, get_password_hash
from app.models.schemas import (
    UserOut,
    UserUpdate,
    PasswordChange,
    UserProfileStatsOut
)

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me", response_model=UserProfileStatsOut)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    stats = crud.get_user_prediction_stats(db, user_id=current_user.id)
    return UserProfileStatsOut(
        user=UserOut.from_orm(current_user),
        total_scans=stats["total_scans"],
        latest_scan_date=stats["latest_scan_date"],
        latest_scan_class=stats["latest_scan_class"]
    )

@router.patch("/me", response_model=UserOut)
def update_profile(
    update_in: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if update_in.email and update_in.email != current_user.email:
        existing = crud.get_user_by_email(db, email=update_in.email)
        if existing and existing.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This email address is already in use by another account."
            )
    
    updated_user = crud.update_user_profile(
        db,
        user=current_user,
        name=update_in.name,
        email=update_in.email
    )
    return UserOut.from_orm(updated_user)

@router.post("/me/change-password")
def change_password(
    pwd_in: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not verify_password(pwd_in.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password."
        )
    
    new_hash = get_password_hash(pwd_in.new_password)
    crud.update_user_password(db, user=current_user, password_hash=new_hash)

    # Add notification
    crud.create_notification(
        db,
        user_id=current_user.id,
        title="Security Alert",
        message="Your account password was updated successfully.",
        notif_type="system"
    )

    return {"message": "Password changed successfully."}
