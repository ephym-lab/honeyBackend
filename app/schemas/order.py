from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Literal
from datetime import date, datetime


class OrderItem(BaseModel):
    productId: str
    quantity: int = Field(gt=0)


class OrderItemResponse(BaseModel):
    productId: str
    productName: str
    quantity: int
    price: int


class OrderCreate(BaseModel):
    customerName: str = Field(min_length=1)
    email: EmailStr
    phone: str = Field(pattern=r"^\+254[0-9]{9}$")
    address: str = Field(min_length=1)
    city: str = Field(min_length=1)
    county: str = Field(min_length=1)
    items: List[OrderItem] = Field(min_length=1)
    paymentMethod: Literal["mpesa", "cash"]
    mpesaPhone: Optional[str] = Field(None, pattern=r"^\+254[0-9]{9}$")
    orderNotes: Optional[str] = None


class Order(BaseModel):
    id: str
    customerName: str
    email: str
    phone: str
    address: str
    city: str
    county: str
    items: List[OrderItemResponse]
    subtotal: int
    shipping: int
    total: int
    paymentMethod: str
    mpesaPhone: Optional[str] = None
    mpesaTransactionId: Optional[str] = None
    status: str
    orderDate: date
    orderNotes: Optional[str] = None
    createdAt: datetime
    updatedAt: datetime
    
    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    success: bool = True
    data: Order
    message: Optional[str] = None


class OrderListResponse(BaseModel):
    success: bool = True
    message: str
    data: List[Order]


class OrderUpdate(BaseModel):
    """Schema for updating order details (only for pending orders)."""
    customerName: Optional[str] = Field(None, min_length=1)
    phone: Optional[str] = Field(None, pattern=r"^\+254[0-9]{9}$")
    address: Optional[str] = Field(None, min_length=1)
    city: Optional[str] = Field(None, min_length=1)
    county: Optional[str] = Field(None, min_length=1)
    orderNotes: Optional[str] = None


class OrderStatusUpdate(BaseModel):
    """Schema for updating order status."""
    status: Literal["pending", "paid", "processing", "shipped", "delivered", "cancelled"]
    mpesaTransactionId: Optional[str] = None


class OrderTrackResponse(BaseModel):
    """Response schema for order tracking."""
    success: bool = True
    message: str
    data: Order


class SuccessResponse(BaseModel):
    """Generic success response."""
    success: bool = True
    message: str
