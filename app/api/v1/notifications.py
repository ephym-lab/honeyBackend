from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.api.deps import get_current_admin
from app.schemas.notification import NotificationListResponse, NotificationResponse
from app.schemas.common import SuccessResponse
from app.services.notification_service import NotificationService

router = APIRouter()

@router.get("", response_model=NotificationListResponse)
async def get_notifications(
    unread_only: bool = True,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Get all notifications (can be filtered by unread_only)."""
    service = NotificationService(db)
    return service.get_notifications(unread_only=unread_only)

@router.patch("/read-all", response_model=SuccessResponse)
async def mark_all_as_read(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Mark all notifications as read."""
    service = NotificationService(db)
    return service.mark_all_as_read()

@router.patch("/{notification_id}/read", response_model=SuccessResponse)
async def mark_as_read(
    notification_id: str,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Mark a specific notification as read."""
    service = NotificationService(db)
    # The service returns the updated notification in 'data', 
    # but the endpoint schema is SuccessResponse which usually just has success and message.
    # We will return the service output which matches SuccessResponse.
    return service.mark_as_read(notification_id)
