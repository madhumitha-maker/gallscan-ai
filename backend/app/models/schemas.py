from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field

# User Schemas
class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: Optional[str] = "clinician"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None

class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=6)

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=6)

class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut

class UserProfileStatsOut(BaseModel):
    user: UserOut
    total_scans: int
    latest_scan_date: Optional[str] = None
    latest_scan_class: Optional[str] = None

# Prediction Schemas
class ClassProbabilityItem(BaseModel):
    class_id: int
    raw_name: str
    display_name: str
    probability: float
    percentage: float

class PredictionOut(BaseModel):
    id: int
    user_id: int
    filename: str
    predicted_class: str
    predicted_display_name: str
    confidence: float
    class_probabilities: Dict[str, float]
    top_3_predictions: List[ClassProbabilityItem]
    original_image_url: Optional[str] = None
    gradcam_image_url: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class PredictResponse(BaseModel):
    id: int
    filename: str
    predicted_class: str
    predicted_display_name: str
    confidence: float
    top_3_predictions: List[ClassProbabilityItem]
    class_probabilities: Dict[str, float]
    original_image_url: str
    gradcam_image_url: str
    disclaimer: str
    created_at: datetime

class PredictionListResponse(BaseModel):
    items: List[PredictionOut]
    total: int
    page: int
    limit: int
    total_pages: int

# Notification Schemas
class NotificationOut(BaseModel):
    id: int
    title: Optional[str] = "Notification"
    message: str
    type: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True

class NotificationListResponse(BaseModel):
    items: List[NotificationOut]
    unread_count: int

# Health Schema
class HealthResponse(BaseModel):
    status: str
    onnx_loaded: bool
    pytorch_loaded: bool
    device: str
    num_classes: int
    classes: List[str]
    disclaimer: str
