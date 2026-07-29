from sqlalchemy import Column, String, Text, Integer, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.database import Base

class CustomerRequest(Base):
    __tablename__ = "customer_requests"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    reason = Column(String(100), nullable=False, index=True)
    training_type = Column(String(100), nullable=True)
    participants = Column(Integer, nullable=True)
    preferred_date = Column(String(50), nullable=True)
    location = Column(String(255), nullable=True)
    message = Column(Text, nullable=False)
    status = Column(String(50), nullable=False, default="New", index=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
