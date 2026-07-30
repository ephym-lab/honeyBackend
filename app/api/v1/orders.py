from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.api.deps import get_current_admin
from app.schemas.order import (
    OrderCreate, 
    OrderResponse, 
    OrderListResponse, 
    OrderUpdate, 
    OrderStatusUpdate, 
    OrderTrackResponse,
    BulkDeleteRequest
)
from app.schemas.common import SuccessResponse
from app.services.order_service import OrderService

router = APIRouter()


@router.post("", response_model=OrderResponse)
async def create_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db)
):
    """Create a new order."""
    order_service = OrderService(db)
    return order_service.create_order(order_data)


@router.get("/search", response_model=OrderListResponse)
async def search_orders(
    q: str = Query(..., description="Search query for order ID, customer name, email, or phone"),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Search orders by order ID, customer name, email, or phone."""
    order_service = OrderService(db)
    return order_service.search_orders(q)


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Get order by ID."""
    order_service = OrderService(db)
    return order_service.get_order(order_id)


@router.get("", response_model=OrderListResponse)
async def get_orders(
    email: Optional[str] = Query(None, description="Filter orders by customer email"),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Get all orders or filter by customer email."""
    order_service = OrderService(db)
    
    if email:
        return order_service.get_orders_by_email(email)
    
    return order_service.get_orders()


@router.get("/{order_id}/track", response_model=OrderTrackResponse)
async def track_order(
    order_id: str,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Track order status and get tracking information."""
    order_service = OrderService(db)
    return order_service.track_order(order_id)


@router.patch("/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: str,
    update_data: OrderUpdate,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Update order details (only for pending orders)."""
    order_service = OrderService(db)
    return order_service.update_order(order_id, update_data.model_dump(exclude_unset=True))


@router.patch("/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: str,
    status_data: OrderStatusUpdate,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Update order status."""
    order_service = OrderService(db)
    return order_service.update_order_status(
        order_id, 
        status_data.status, 
        status_data.mpesaTransactionId
    )


@router.patch("/{order_id}/cancel", response_model=SuccessResponse)
async def cancel_order(
    order_id: str,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Cancel an order (only for pending or paid orders)."""
    order_service = OrderService(db)
    return order_service.cancel_order(order_id)


@router.delete("/{order_id}", response_model=SuccessResponse)
async def delete_order(
    order_id: str,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Delete order by ID."""
    order_service = OrderService(db)
    return order_service.delete_order(order_id)


@router.post("/bulk-delete", response_model=SuccessResponse)
async def bulk_delete_orders(
    request: BulkDeleteRequest,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Bulk delete orders by ID."""
    order_service = OrderService(db)
    return order_service.bulk_delete_orders(request.order_ids)