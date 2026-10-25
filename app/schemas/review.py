from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import date, datetime
from uuid import UUID


class ReviewBase(BaseModel):
    author: str = Field(min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    rating: int = Field(ge=1, le=5)
    comment: str = Field(min_length=1)


class ReviewCreate(ReviewBase):
    pass


class Review(ReviewBase):
    id: UUID
    product_id: UUID
    date: date
    verified: bool
    featured: Optional[bool] = False
    created_at: datetime
    
    class Config:
        from_attributes = True


class ReviewResponse(BaseModel):
    success: bool = True
    data: Review
    message: Optional[str] = None
