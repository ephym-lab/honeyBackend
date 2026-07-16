"""Pydantic schemas package."""

from app.schemas.product import ProductCreate, ProductUpdate, Product, ProductResponse, ProductListResponse
from app.schemas.order import OrderCreate, Order, OrderResponse
from app.schemas.review import ReviewCreate, Review, ReviewResponse
from app.schemas.auth import LoginRequest, TokenResponse, Register, Login
from app.schemas.newsletter import NewsletterSubscribe, NewsletterResponse

__all__ = [
    "ProductCreate", "ProductUpdate", "Product", "ProductResponse", "ProductListResponse",
    "OrderCreate", "Order", "OrderResponse",
    "ReviewCreate", "Review", "ReviewResponse",
    "LoginRequest", "TokenResponse", "Register", "Login",
    "NewsletterSubscribe", "NewsletterResponse",
]
