from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Literal
from datetime import date, datetime
from typing_extensions import Annotated


# Define shared constrained types to avoid duplicating validation logic
CustomerNameType = Annotated[str, Field(min_length=1)]
PhoneType = Annotated[str, Field(pattern=r"^\+254[0-9]{9}$")]
AddressType = Annotated[str, Field(min_length=1)]
CityType = Annotated[str, Field(min_length=1)]
CountyType = Annotated[str, Field(min_length=1)]


class OrderItem(BaseModel):
    productId: str
    quantity: int = Field(gt=0)


class OrderItemResponse(BaseModel):
    productId: str
    productName: str
    quantity: int
    price: int


class OrderBase(BaseModel):
    customerName: CustomerNameType
    phone: PhoneType
    address: AddressType
    city: CityType
    county: CountyType
    orderNotes: Optional[str] = None


class OrderCreate(OrderBase):
    email: EmailStr
    items: List[OrderItem] = Field(min_length=1)
    paymentMethod: Literal["mpesa"] = "mpesa"  # cash on delivery removed - M-Pesa only
    mpesaPhone: Optional[PhoneType] = None


class Order(OrderBase):
    id: str
    email: str
    items: List[OrderItemResponse]
    subtotal: int
    shipping: int
    total: int
    paymentMethod: str
    mpesaPhone: Optional[str] = None
    mpesaTransactionId: Optional[str] = None
    status: str
    orderDate: date
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
    customerName: Optional[CustomerNameType] = None
    phone: Optional[PhoneType] = None
    address: Optional[AddressType] = None
    city: Optional[CityType] = None
    county: Optional[CountyType] = None
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

class BulkDeleteRequest(BaseModel):
    """Schema for bulk deleting orders."""
    order_ids: List[str] = Field(..., min_length=1)
