from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db import crud
from app.auth.security import verify_password, get_password_hash, create_access_token, decode_access_token
from app.models.schemas import (
    UserCreate,
    UserLogin,
    UserOut,
    TokenResponse,
    ForgotPasswordRequest,
    ResetPasswordRequest
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(user_in: UserCreate, db: Session = Depends(get_db)):
    existing = crud.get_user_by_email(db, email=user_in.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists."
        )
    password_hash = get_password_hash(user_in.password)
    user = crud.create_user(
        db,
        name=user_in.name,
        email=user_in.email,
        password_hash=password_hash,
        role=user_in.role or "clinician"
    )
    
    # Create welcome notification
    crud.create_notification(
        db,
        user_id=user.id,
        title="Welcome to GallScan AI",
        message="Your account has been configured. You can now upload gallbladder ultrasound scans for real-time AI classification and Grad-CAM explainability.",
        notif_type="system"
    )

    access_token = create_access_token(subject=user.id)
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserOut.from_orm(user)
    )

@router.post("/login", response_model=TokenResponse)
def login(login_in: UserLogin, db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, email=login_in.email)
    if not user or not verify_password(login_in.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )
    access_token = create_access_token(subject=user.id)
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserOut.from_orm(user)
    )

@router.post("/forgot-password")
def forgot_password(req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, email=req.email)
    # Always return 200 to prevent email enumeration
    if not user:
        return {
            "message": "If that email is registered, a password reset link has been dispatched.",
            "demo_reset_token": None
        }
    
    reset_token = create_access_token(subject=f"reset_{user.id}")
    return {
        "message": "If that email is registered, a password reset link has been dispatched.",
        "demo_reset_token": reset_token  # For demo convenience
    }

@router.post("/reset-password")
def reset_password(req: ResetPasswordRequest, db: Session = Depends(get_db)):
    payload = decode_access_token(req.token)
    if not payload or not str(payload.get("sub", "")).startswith("reset_"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token."
        )
    user_id_str = payload["sub"].replace("reset_", "")
    try:
        user_id = int(user_id_str)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Corrupted token data.")
    
    user = crud.get_user_by_id(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    
    new_hash = get_password_hash(req.new_password)
    crud.update_user_password(db, user=user, password_hash=new_hash)
    
    # Notify user
    crud.create_notification(
        db,
        user_id=user.id,
        title="Security Notice",
        message="Your account password was recently updated.",
        notif_type="system"
    )

    return {"message": "Password has been successfully updated. You may now log in."}
