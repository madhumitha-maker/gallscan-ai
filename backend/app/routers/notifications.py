from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db import crud
from app.db.models import User
from app.auth.dependencies import get_current_user
from app.models.schemas import NotificationOut, NotificationListResponse

router = APIRouter(prefix="/notifications", tags=["Notifications"])

@router.get("", response_model=NotificationListResponse)
def get_notifications(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    notifs = crud.get_user_notifications(db, user_id=current_user.id, limit=limit)
    unread_count = sum(1 for n in notifs if not n.is_read)
    return NotificationListResponse(
        items=[NotificationOut.from_orm(n) for n in notifs],
        unread_count=unread_count
    )

@router.patch("/{notif_id}/read", response_model=NotificationOut)
def mark_read(
    notif_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    notif = crud.mark_notification_read(db, notif_id=notif_id, user_id=current_user.id)
    if not notif:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found."
        )
    return NotificationOut.from_orm(notif)

@router.patch("/read-all")
def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    count = crud.mark_all_notifications_read(db, user_id=current_user.id)
    return {"message": f"Marked {count} notifications as read."}

@router.delete("/{notif_id}")
def delete_notification(
    notif_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from app.db.models import Notification
    notif = db.query(Notification).filter(Notification.id == notif_id, Notification.user_id == current_user.id).first()
    if not notif:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")
    db.delete(notif)
    db.commit()
    return {"message": "Notification deleted."}
