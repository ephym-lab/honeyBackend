from sqlalchemy import Column, String, Integer, Text, Date, TIMESTAMP, JSON
from sqlalchemy.sql import func
from app.database import Base


class Order(Base):
    __tablename__ = "orders"
    
    id = Column(String(50), primary_key=True)
    customer_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    phone = Column(String(20), nullable=False)
    address = Column(Text, nullable=False)
    city = Column(String(100), nullable=False)
    county = Column(String(100), nullable=False)
    items = Column(JSON, nullable=False)
    subtotal = Column(Integer, nullable=False)
    shipping = Column(Integer, nullable=False)
    total = Column(Integer, nullable=False)
    payment_method = Column(String(10), nullable=False)
    mpesa_phone = Column(String(20), nullable=True)
    mpesa_transaction_id = Column(String(100), nullable=True)
    status = Column(String(20), nullable=False, default="pending", index=True)
    order_date = Column(Date, nullable=False, index=True)
    order_notes = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
