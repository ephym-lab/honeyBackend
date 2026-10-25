from sqlalchemy import Column, String, Integer, Text, DECIMAL, TIMESTAMP, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.database import Base


class Products(Base):
    __tablename__ = "products"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    price = Column(Integer, nullable=False)
    image_cover = Column(String(500), nullable=False)
    images = Column(JSON, nullable=True)
    category = Column(String(50), nullable=False, index=True)
    stock = Column(Integer, nullable=False, default=0, index=True)
    badge = Column(String(50), nullable=True)            # e.g. Bestseller
    delivery_time = Column(String(100), nullable=True)   # e.g. 2-4 Working Days
    return_policy = Column(String(150), nullable=True)   # e.g. 7 days return policy
    weight_kg = Column(DECIMAL(8, 2), nullable=True)  # kg per unit, for delivery pricing
    low_stock_level = Column(Integer, nullable=True)  # alert when stock falls to this (empty = 5)
    rating = Column(DECIMAL(2, 1), default=0)
    tags = Column(JSON, nullable=True)
    features = Column(JSON, nullable=True)
    related_products = Column(JSON, nullable=True)
    bundle_offer = Column(JSON, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())