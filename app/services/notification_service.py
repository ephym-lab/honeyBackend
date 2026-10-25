from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from fastapi import HTTPException, status
from typing import Optional

from app.models.notification import Notification
from app.schemas.notification import NotificationCreate

class NotificationService:
    def __init__(self, db: Session):
        self.db = db

    def create_notification(self, title: str, message: str, notification_type: str, priority: str = "medium", related_entity: Optional[str] = None, related_id: Optional[str] = None):
        """Create a new notification."""
        try:
            new_notification = Notification(
                title=title,
                message=message,
                notification_type=notification_type,
                priority=priority,
                related_entity=related_entity,
                related_id=related_id
            )
            self.db.add(new_notification)
            self.db.commit()
            self.db.refresh(new_notification)
            return new_notification
        except Exception as e:
            self.db.rollback()
            print(f"Failed to create notification: {str(e)}")
            return None

    def get_notifications(self, unread_only: bool = True):
        """Get notifications, optionally filtering by unread."""
        try:
            query = self.db.query(Notification)
            
            total_count = self.db.query(Notification).count()
            unread_count = self.db.query(Notification).filter(Notification.is_read == False).count()
            
            if unread_only:
                query = query.filter(Notification.is_read == False)
            
            notifications = query.order_by(Notification.created_at.desc()).all()
            return {
                "success": True,
                "message": "Notifications retrieved successfully",
                "data": {
                    "notifications": notifications,
                    "total_count": total_count,
                    "unread_count": unread_count
                }
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get notifications: {str(e)}"
            )

    def mark_as_read(self, notification_id: str):
        """Mark a specific notification as read."""
        notification = self.db.query(Notification).filter(Notification.id == notification_id).first()
        
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
            
        notification.is_read = True  # type: ignore
        notification.read_at = func.now()  # type: ignore
        self.db.commit()
        self.db.refresh(notification)
        
        return {
            "success": True,
            "message": "Notification marked as read",
            "data": {
                "id": str(notification.id),
                "is_read": True,
                "unread_count": self.db.query(Notification).filter(Notification.is_read == False).count(),
            }
        }

    def mark_all_as_read(self):
        """Mark all unread notifications as read."""
        try:
            self.db.query(Notification).filter(Notification.is_read == False).update({
                "is_read": True,
                "read_at": func.now()
            })
            self.db.commit()
            return {
                "success": True,
                "message": "All notifications marked as read"
            }
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to mark notifications as read: {str(e)}"
            )

    def mark_related_as_read(self, related_id: str, related_entity: Optional[str] = None):
        """Mark every unread notification about one order/request as read."""
        try:
            query = self.db.query(Notification).filter(
                Notification.is_read == False,
                Notification.related_id == str(related_id),
            )
            if related_entity:
                query = query.filter(func.lower(Notification.related_entity) == related_entity.lower())
            marked = query.update({"is_read": True, "read_at": func.now()}, synchronize_session=False)
            self.db.commit()
            unread = self.db.query(Notification).filter(Notification.is_read == False).count()
            return {
                "success": True,
                "message": f"{marked} notification(s) marked as read",
                "data": {"marked": marked, "unread_count": unread},
            }
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to mark notifications as read: {str(e)}"
            )
