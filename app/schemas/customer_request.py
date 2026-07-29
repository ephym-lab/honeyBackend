from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
import uuid

class CustomerRequestBase(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    reason: str
    training_type: Optional[str] = None
    participants: Optional[int] = None
    preferred_date: Optional[str] = None
    location: Optional[str] = None
    message: str

class CustomerRequestCreate(CustomerRequestBase):
    pass

class CustomerRequestUpdateStatus(BaseModel):
    status: str

class CustomerRequestResponse(CustomerRequestBase):
    id: uuid.UUID
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CustomerRequestStats(BaseModel):
    total: int
    training_requests: int
    general_inquiries: int
    bulk_order_quotes: int
    product_support: int
    other_inquiries: int
    new: int
    contacted: int
    in_progress: int
    completed: int
