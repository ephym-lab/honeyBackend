from sqlalchemy import Column, String, Boolean, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.database import Base


class NewsletterSubscription(Base):
    __tablename__ = "newsletter_subscriptions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    subscribed_at = Column(TIMESTAMP, server_default=func.now())
    active = Column(Boolean, default=True)
