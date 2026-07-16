from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.schemas.order import (
    OrderCreate, 
    OrderResponse, 
    OrderListResponse, 
    OrderUpdate, 
    OrderStatusUpdate, 
    OrderTrackResponse, 
    SuccessResponse
)
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
    db: Session = Depends(get_db)
):
    """Search orders by order ID, customer name, email, or phone."""
    order_service = OrderService(db)
    return order_service.search_orders(q)


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str,
    db: Session = Depends(get_db)
):
    """Get order by ID."""
    order_service = OrderService(db)
    return order_service.get_order(order_id)


@router.get("", response_model=OrderListResponse)
async def get_orders(
    email: Optional[str] = Query(None, description="Filter orders by customer email"),
    db: Session = Depends(get_db)
):
    """Get all orders or filter by customer email."""
    order_service = OrderService(db)
    
    if email:
        return order_service.get_orders_by_email(email)
    
    return order_service.get_orders()


@router.get("/{order_id}/track", response_model=OrderTrackResponse)
async def track_order(
    order_id: str,
    db: Session = Depends(get_db)
):
    """Track order status and get tracking information."""
    order_service = OrderService(db)
    return order_service.track_order(order_id)


@router.patch("/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: str,
    update_data: OrderUpdate,
    db: Session = Depends(get_db)
):
    """Update order details (only for pending orders)."""
    order_service = OrderService(db)
    return order_service.update_order(order_id, update_data)


@router.patch("/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: str,
    status_data: OrderStatusUpdate,
    db: Session = Depends(get_db)
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
    db: Session = Depends(get_db)
):
    """Cancel an order (only for pending or paid orders)."""
    order_service = OrderService(db)
    return order_service.cancel_order(order_id)
