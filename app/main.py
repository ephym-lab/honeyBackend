from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.config import settings
from app.api.v1 import products, orders, reviews, auth, analytics, newsletter, webhooks, notifications, customer_requests, customers
from app.api.v1 import customer_accounts
from app.api.v1 import request_followups

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(products.router, prefix=f"{settings.API_V1_PREFIX}/products", tags=["products"])
app.include_router(orders.router, prefix=f"{settings.API_V1_PREFIX}/orders", tags=["orders"])
app.include_router(reviews.router, prefix=f"{settings.API_V1_PREFIX}", tags=["reviews"])
app.include_router(auth.router, prefix=f"{settings.API_V1_PREFIX}/auth", tags=["auth"])
app.include_router(analytics.router, prefix=f"{settings.API_V1_PREFIX}/analytics", tags=["analytics"])
app.include_router(newsletter.router, prefix=f"{settings.API_V1_PREFIX}/newsletter", tags=["newsletter"])
app.include_router(webhooks.router, prefix=f"{settings.API_V1_PREFIX}/webhooks", tags=["webhooks"])
app.include_router(notifications.router, prefix=f"{settings.API_V1_PREFIX}/notifications", tags=["notifications"])
app.include_router(customer_requests.router, prefix=f"{settings.API_V1_PREFIX}/requests", tags=["requests"])
app.include_router(customers.router, prefix=f"{settings.API_V1_PREFIX}/customers", tags=["customers"])
app.include_router(customer_accounts.router, prefix=f"{settings.API_V1_PREFIX}/account", tags=["customer accounts"])
app.include_router(request_followups.router, prefix=f"{settings.API_V1_PREFIX}/request-followups", tags=["follow-ups"])

# Ensure uploads directory exists and mount it
uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0"
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Premium Honey API",
        "docs": f"{settings.API_V1_PREFIX}/docs"
    }


# CRM step 3: follow-up reminders in the admin bell
@app.on_event("startup")
def _start_followup_reminders():
    from app.services import followup_service
    followup_service.start_reminder_loop()


# Low-stock alerts in the admin bell (checked every few minutes)
@app.on_event("startup")
def _start_stock_alerts():
    from app.services import stock_alerts
    stock_alerts.start_loop()
