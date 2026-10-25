from sqlalchemy import Column, String, Integer, Text, Date, Boolean, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.database import Base


class Review(Base):
    __tablename__ = "reviews"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    author = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    rating = Column(Integer, nullable=False)
    comment = Column(Text, nullable=False)
    date = Column(Date, nullable=False)
    verified = Column(Boolean, default=False)
    featured = Column(Boolean, default=False)  # shown on the Home page
    created_at = Column(TIMESTAMP, server_default=func.now())
