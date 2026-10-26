from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.db.models import User, Prediction, Notification

# User operations
def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email.ilike(email.strip())).first()

def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()

def create_user(db: Session, name: str, email: str, password_hash: str, role: str = "clinician") -> User:
    user = User(
        name=name.strip(),
        email=email.strip().lower(),
        password_hash=password_hash,
        role=role
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def update_user_profile(db: Session, user: User, name: Optional[str] = None, email: Optional[str] = None) -> User:
    if name is not None:
        user.name = name.strip()
    if email is not None:
        user.email = email.strip().lower()
    db.commit()
    db.refresh(user)
    return user

def update_user_password(db: Session, user: User, password_hash: str) -> User:
    user.password_hash = password_hash
    db.commit()
    db.refresh(user)
    return user

# Prediction operations
def create_prediction(
    db: Session,
    user_id: int,
    filename: str,
    predicted_class: str,
    confidence: float,
    class_probabilities: Dict[str, float],
    original_image_path: Optional[str] = None,
    gradcam_image_path: Optional[str] = None,
    notes: Optional[str] = None
) -> Prediction:
    pred = Prediction(
        user_id=user_id,
        filename=filename,
        predicted_class=predicted_class,
        confidence=confidence,
        class_probabilities=class_probabilities,
        original_image_path=original_image_path,
        gradcam_image_path=gradcam_image_path,
        notes=notes
    )
    db.add(pred)
    db.commit()
    db.refresh(pred)
    return pred

def get_user_predictions(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 20,
    class_filter: Optional[str] = None,
    search: Optional[str] = None
) -> (List[Prediction], int):
    query = db.query(Prediction).filter(Prediction.user_id == user_id)
    if class_filter and class_filter.strip() and class_filter.strip().lower() != "all":
        query = query.filter(Prediction.predicted_class == class_filter.strip())
    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter((Prediction.filename.ilike(term)) | (Prediction.predicted_class.ilike(term)))
    
    total = query.count()
    items = query.order_by(desc(Prediction.created_at)).offset(skip).limit(limit).all()
    return items, total

def get_prediction_by_id(db: Session, prediction_id: int, user_id: int) -> Optional[Prediction]:
    return db.query(Prediction).filter(Prediction.id == prediction_id, Prediction.user_id == user_id).first()

def get_user_prediction_stats(db: Session, user_id: int) -> Dict[str, Any]:
    total_scans = db.query(Prediction).filter(Prediction.user_id == user_id).count()
    latest_scan = db.query(Prediction).filter(Prediction.user_id == user_id).order_by(desc(Prediction.created_at)).first()
    return {
        "total_scans": total_scans,
        "latest_scan_date": latest_scan.created_at.isoformat() if latest_scan else None,
        "latest_scan_class": latest_scan.predicted_class if latest_scan else None
    }

# Notification operations
def create_notification(
    db: Session,
    user_id: int,
    message: str,
    title: str = "Analysis Ready",
    notif_type: str = "analysis_complete"
) -> Notification:
    notif = Notification(
        user_id=user_id,
        title=title,
        message=message,
        type=notif_type,
        is_read=False
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)
    return notif

def get_user_notifications(db: Session, user_id: int, limit: int = 50) -> List[Notification]:
    return db.query(Notification).filter(Notification.user_id == user_id).order_by(desc(Notification.created_at)).limit(limit).all()

def mark_notification_read(db: Session, notif_id: int, user_id: int) -> Optional[Notification]:
    notif = db.query(Notification).filter(Notification.id == notif_id, Notification.user_id == user_id).first()
    if notif:
        notif.is_read = True
        db.commit()
        db.refresh(notif)
    return notif

def mark_all_notifications_read(db: Session, user_id: int) -> int:
    count = db.query(Notification).filter(Notification.user_id == user_id, Notification.is_read == False).update({"is_read": True})
    db.commit()
    return count
