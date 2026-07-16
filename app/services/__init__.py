"""Services package."""

from app.services.user_manager import (
    UserManagerService,
    RegisterService,
    LoginService
)
from app.services.order_service import (
    OrderManagerService,
    OrderService
)
from app.services.product_service import (
    ProductManagerService,
    ProductService
)
from app.services.review_service import (
    ReviewManagerService,
    ReviewService
)
from app.services.newsletter_service import (
    NewsletterManagerService,
    NewsletterService
)
from app.services.email_service import EmailService

__all__ = [
    "UserManagerService",
    "RegisterService",
    "LoginService",
    "OrderManagerService",
    "OrderService",
    "ProductManagerService",
    "ProductService",
    "ReviewManagerService",
    "ReviewService",
    "NewsletterManagerService",
    "NewsletterService"
    "EmailService"
]
