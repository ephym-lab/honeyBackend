from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.newsletter import (
    NewsletterSubscribe, 
    NewsletterResponse,
    NewsletterBroadcast,
    NewsletterBroadcastResponse
)
from app.services.newsletter_service import NewsletterService
from app.api.deps import get_current_admin
from app.models.user import User

router = APIRouter()


@router.post("/subscribe", response_model=NewsletterResponse)
async def subscribe_newsletter(
    data: NewsletterSubscribe,
    db: Session = Depends(get_db)
):
    """Subscribe to newsletter."""
    newsletter_service = NewsletterService(db)
    return newsletter_service.subscribe(data)


@router.post("/unsubscribe", response_model=NewsletterResponse)
async def unsubscribe_newsletter(
    data: NewsletterSubscribe,
    db: Session = Depends(get_db)
):
    """Unsubscribe from newsletter."""
    newsletter_service = NewsletterService(db)
    return newsletter_service.unsubscribe(data.email)


@router.post("/admin/broadcast", response_model=NewsletterBroadcastResponse)
async def send_newsletter_broadcast(
    broadcast_data: NewsletterBroadcast,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """
    Send a newsletter to all active subscribers (Admin only).
    
    Requires admin authentication via Bearer token.
    """
    newsletter_service = NewsletterService(db)
    return newsletter_service.send_newsletter_broadcast(
        subject=broadcast_data.subject,
        html_body=broadcast_data.html_body
    )

@router.get("/admin/stats")
async def get_newsletter_stats(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """Newsletter subscriber statistics (Admin only)."""
    from datetime import datetime, timedelta
    from app.models.newsletter import NewsletterSubscription as NS

    total = db.query(NS).count()
    active = db.query(NS).filter(NS.active == True).count()
    since = datetime.utcnow() - timedelta(days=30)
    new_last_30_days = db.query(NS).filter(NS.subscribed_at >= since).count()

    return {
        "success": True,
        "data": {
            "total": total,
            "active": active,
            "inactive": total - active,
            "new_last_30_days": new_last_30_days,
        },
    }
