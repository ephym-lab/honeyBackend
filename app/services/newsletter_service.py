from abc import ABC
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from app.schemas.newsletter import NewsletterSubscribe
from app.models.newsletter import NewsletterSubscription
from app.services.email_service import EmailService
from app.services.email_templates import EmailTemplates


class NewsletterManagerService(ABC):
    """Abstract base class for newsletter management services."""
    
    def __init__(self, db: Session):
        self.db = db


class NewsletterService(NewsletterManagerService):
    """Service for handling newsletter subscription operations."""
    
    def __init__(self, db: Session):
        super().__init__(db)
        self.email_service = EmailService()
    
    def subscribe(self, subscription_data: NewsletterSubscribe):
        """
        Subscribe an email to the newsletter.
        
        Args:
            subscription_data: Subscription data with email
            
        Returns:
            dict: Success response
            
        Raises:
            HTTPException: If subscription fails
        """
        try:
            # Check if email already exists
            existing = self.db.query(NewsletterSubscription).filter(
                NewsletterSubscription.email == subscription_data.email
            ).first()
            
            if existing:
                if existing.active:
                    return {
                        "success": True,
                        "message": "You are already subscribed to our newsletter"
                    }
                else:
                    # Reactivate subscription
                    existing.active = True
                    self.db.commit()
                    return {
                        "success": True,
                        "message": "Your subscription has been reactivated"
                    }
            
            # Create new subscription
            subscription = NewsletterSubscription(
                email=subscription_data.email,
                active=True
            )
            
            self.db.add(subscription)
            self.db.commit()
            
            # Send welcome email (non-blocking)
            try:
                html_body = EmailTemplates.newsletter_subscription(
                    email=subscription_data.email
                )
                subject = "Welcome to HoneyBiz Newsletter! 🍯"
                self.email_service.send_html_email(
                    subscription_data.email,
                    subject,
                    html_body
                )
                print(f"Newsletter welcome email sent to {subscription_data.email}")
            except Exception as e:
                print(f"Subscription successful but email failed: {str(e)}")
            
            return {
                "success": True,
                "message": "Successfully subscribed to newsletter"
            }
            
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already subscribed"
            )


        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to subscribe: {str(e)}"
            )
    
    def unsubscribe(self, email: str):
        """
        Unsubscribe an email from the newsletter.
        
        Args:
            email: Email address to unsubscribe
            
        Returns:
            dict: Success response
            
        Raises:
            HTTPException: If email not found
        """
        subscription = self.db.query(NewsletterSubscription).filter(
            NewsletterSubscription.email == email
        ).first()
        
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email not found in newsletter"
            )
        
        subscription.active = False
        self.db.commit()
        
        # Send unsubscribe confirmation email (non-blocking)
        try:
            html_body = EmailTemplates.newsletter_unsubscription(email=email)
            subject = "You've been unsubscribed from HoneyBiz Newsletter"
            self.email_service.send_html_email(email, subject, html_body)
            print(f"Newsletter unsubscribe confirmation sent to {email}")
        except Exception as e:
            print(f"Unsubscription successful but email failed: {str(e)}")
        
        return {
            "success": True,
            "message": "Successfully unsubscribed from newsletter"
        }
    
    def get_all_subscribers(self, active_only: bool = True):
        """
        Get all newsletter subscribers (admin only).
        
        Args:
            active_only: Only return active subscriptions
            
        Returns:
            dict: Success response with subscribers list
        """
        query = self.db.query(NewsletterSubscription)
        
        if active_only:
            query = query.filter(NewsletterSubscription.active == True)
        
        subscribers = query.order_by(NewsletterSubscription.subscribed_at.desc()).all()
        
        return {
            "success": True,
            "data": {
                "subscribers": [
                    {
                        "id": str(sub.id),
                        "email": sub.email,
                        "subscribedAt": sub.subscribed_at,
                        "active": sub.active
                    }
                    for sub in subscribers
                ],
                "count": len(subscribers)
            }
        }
    
    def send_newsletter_broadcast(self, subject: str, html_body: str):
        """
        Send a newsletter to all active subscribers (admin only).
        
        Args:
            subject: Email subject line
            html_body: HTML content of the newsletter
            
        Returns:
            dict: Success response with count of emails sent
        """
        # Get all active subscribers
        subscribers = self.db.query(NewsletterSubscription).filter(
            NewsletterSubscription.active == True
        ).all()
        
        if not subscribers:
            return {
                "success": True,
                "message": "No active subscribers to send newsletter to",
                "emails_sent": 0,
                "failed_emails": []
            }
        
        emails_sent = 0
        failed_emails = []
        
        # Send email to each subscriber
        for subscriber in subscribers:
            try:
                success = self.email_service.send_html_email(
                    to_email=subscriber.email,
                    subject=subject,
                    html_body=html_body
                )
                
                if success:
                    emails_sent += 1
                    print(f"Newsletter sent to {subscriber.email}")
                else:
                    failed_emails.append(subscriber.email)
                    print(f"Failed to send newsletter to {subscriber.email}")
                    
            except Exception as e:
                failed_emails.append(subscriber.email)
                print(f"Error sending newsletter to {subscriber.email}: {str(e)}")
        
        return {
            "success": True,
            "message": f"Newsletter sent to {emails_sent} out of {len(subscribers)} subscribers",
            "emails_sent": emails_sent,
            "failed_emails": failed_emails
        }
