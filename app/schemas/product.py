from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class BundleOffer(BaseModel):
    quantity: int
    discount: int
    description: str


class ProductBase(BaseModel):
    name: str
    description: str
    price: int
    image_cover: str
    category: str
    stock: int
    tags: Optional[List[str]] = None
    images: Optional[List[str]] = None
    features: Optional[List[str]] = None
    related_products: Optional[List[str]] = None
    bundle_offer: Optional[BundleOffer] = None



class ProductCreate(ProductBase):
    pass




class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[int] = None
    image_cover: Optional[str] = None
    category: Optional[str] = None
    stock: Optional[int] = None
    tags: Optional[List[str]] = None
    images: Optional[List[str]] = None
    features: Optional[List[str]] = None
    related_products: Optional[List[str]] = None
    bundle_offer: Optional[BundleOffer] = None


class Product(ProductBase):
    id: UUID
    rating: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # REQUIRED for ORM


class Pagination(BaseModel):
    page: int
    limit: int
    total: int
    totalPages: int


class ProductListItem(BaseModel):
    id: UUID
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[int] = None
    image_cover: Optional[str] = None
    category: Optional[str] = None
    stock: Optional[int] = None

    class Config:
        from_attributes = True


class ProductListData(BaseModel):
    products: List[ProductListItem]
    pagination: Pagination


class ProductResponse(BaseModel):
    success: bool = True
    data: Product
    message: Optional[str] = None


class ProductListResponse(BaseModel):
    success: bool = True
    data: ProductListData


class ProductBundleListResponse(BaseModel):
    """Response schema for products with bundle offers (no pagination)."""
    success: bool = True
    message: str
    data: List[Product]


class StockUpdate(BaseModel):
    """Schema for updating product stock."""
    stock: int = Field(ge=0, description="New stock quantity")


class AvailabilityResponse(BaseModel):
    """Response schema for product availability check."""
    success: bool = True
    message: str
    data: dict


class TopSellingProduct(BaseModel):
    """Schema for top-selling product with sales data."""
    id: UUID
    name: str
    description: str
    price: int
    image_cover: str
    category: str
    stock: int
    rating: float
    total_sold: int
    revenue: int
    
    class Config:
        from_attributes = True


class TopSellingResponse(BaseModel):
    """Response schema for top-selling products."""
    success: bool = True
    message: str
    data: List[TopSellingProduct]


class BundleResponse(BaseModel):
    """Response schema for bundle offers."""
    success: bool = True
    message: str
    data: Optional[BundleOffer] = None

