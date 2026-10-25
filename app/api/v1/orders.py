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
from fastapi import Request as _AccountRequest

router = APIRouter()


@router.post("", response_model=OrderResponse)
async def create_order(
    order_data: OrderCreate,
    request: _AccountRequest,
    db: Session = Depends(get_db)
):
    """Create a new order."""
    order_service = OrderService(db)
    result = order_service.create_order(order_data)
    # If a logged-in customer placed it, link it to their account (guests are unaffected)
    try:
        from app.services import customer_account_service
        customer_account_service.link_new_order(db, request.headers.get("authorization"), result)
    except Exception as e:
        print(f"[Accounts] Could not link order to account: {e}")
    return result


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
    # An unpaid M-Pesa order cannot be processed, shipped or delivered.
    # (It can still be marked Paid by hand after checking the M-Pesa statement.)
    from app.models.order import Order as _GuardOrder
    _order = db.query(_GuardOrder).filter(_GuardOrder.id == order_id).first()
    if (
        _order
        and _order.payment_method == "mpesa"
        and str(_order.status).lower() == "pending"
        and status_data.status in ("processing", "shipped", "delivered")
    ):
        raise HTTPException(
            status_code=400,
            detail="This M-Pesa order has not been paid yet. Only mark it Paid after the money "
                   "has reached your M-Pesa, then you can process and ship it.",
        )
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


# ---------------------------------------------------------------------------
# M-Pesa STK push via Pay Hero
# ---------------------------------------------------------------------------
from app.models.order import Order as OrderModel
from app.services import payhero_service
from app.services import payment_gateway  # Paystack or Pay Hero (PAYMENT_PROVIDER in .env)


@router.post("/{order_id}/pay")
def start_mpesa_payment(
    order_id: str,
    db: Session = Depends(get_db)
):
    """Send an M-Pesa PIN prompt (STK push) for a pending M-Pesa order."""
    order = db.query(OrderModel).filter(OrderModel.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.payment_method != "mpesa":
        raise HTTPException(status_code=400, detail="This order is not set to be paid with M-Pesa")
    if order.status != "pending":
        raise HTTPException(status_code=400, detail=f"This order is already {order.status}")

    try:
        info = payment_gateway.start(order)
    except payment_gateway.GatewayError as e:
        print(f"[Payments] Could not start payment for {order.id}: {e}")
        raise HTTPException(status_code=502, detail=f"Could not send the M-Pesa prompt: {e}")

    return {
        "success": True,
        "data": {
            "orderId": order.id,
            "state": info.get("state", "waiting"),
            "message": info.get("message"),
            "amount": order.total,
        },
    }


@router.get("/{order_id}/payment-status")
def mpesa_payment_status(
    order_id: str,
    db: Session = Depends(get_db)
):
    """Tell the checkout page whether an M-Pesa payment has gone through."""
    order = db.query(OrderModel).filter(OrderModel.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Ask the payment company (Paystack or Pay Hero) whether it has been paid
    payment_gateway.refresh(db, order)
    db.refresh(order)
    info = payment_gateway.get_payment(order_id) or {}

    if order.status not in ("pending", "cancelled"):
        state = "paid"
    elif order.status == "cancelled":
        state = "cancelled"
    else:
        state = info.get("state", "not_started")

    return {
        "success": True,
        "data": {
            "orderId": order.id,
            "orderStatus": order.status,
            "state": state,
            "message": info.get("message"),
            "receipt": order.mpesa_transaction_id,
        },
    }


# ---------------------------------------------------------------------------
# Public order tracking (customer enters order ID + email)
# ---------------------------------------------------------------------------
from app.models.order import Order as _TrackOrderModel


@router.get("/{order_id}/public-status")
def public_order_status(
    order_id: str,
    email: str = Query(..., description="Email used when placing the order"),
    db: Session = Depends(get_db)
):
    """Let a customer see their own order's status (order ID and email must both match)."""
    order = db.query(_TrackOrderModel).filter(
        _TrackOrderModel.id == order_id.strip().upper()
    ).first()

    if not order or (order.email or "").strip().lower() != email.strip().lower():
        # Same message either way, so nobody can guess which order IDs exist
        raise HTTPException(
            status_code=404,
            detail="We could not find an order with that order ID and email address."
        )

    return {
        "success": True,
        "data": {
            "id": order.id,
            "customerName": order.customer_name,
            "status": order.status,
            "orderDate": order.order_date,
            "updatedAt": order.updated_at,
            "items": [
                {
                    "productName": item.get("productName"),
                    "quantity": item.get("quantity"),
                    "price": item.get("price"),
                }
                for item in (order.items or [])
            ],
            "subtotal": order.subtotal,
            "shipping": order.shipping,
            "total": order.total,
            "paymentMethod": order.payment_method,
            "city": order.city,
            "county": order.county,
        },
    }


# ---------------------------------------------------------------------------
# Delivery pricing (zone + weight). Settings are edited in Admin > Delivery.
# ---------------------------------------------------------------------------
from typing import List as _DList
from pydantic import BaseModel as _DModel
from app.services import delivery_service


class _QuoteItem(_DModel):
    productId: str
    quantity: int = 1


class _QuoteRequest(_DModel):
    county: Optional[str] = None
    items: _DList[_QuoteItem] = []


@router.get("/delivery/settings")
def get_delivery_settings(db: Session = Depends(get_db)):
    """Delivery zones and charges (public, so checkout can show them)."""
    return {"success": True, "data": delivery_service.get_settings(db)}


@router.put("/delivery/settings")
def update_delivery_settings(
    settings: dict,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Save delivery zones and charges (Admin only)."""
    try:
        saved = delivery_service.save_settings(db, settings)
    except Exception as e:
        db.rollback()
        print(f"[Delivery] Could not save settings: {e}")
        raise HTTPException(status_code=500, detail="Could not save the delivery settings")
    return {"success": True, "message": "Delivery settings saved", "data": saved}


@router.post("/delivery/quote")
def delivery_quote(request: _QuoteRequest, db: Session = Depends(get_db)):
    """Delivery fee for a cart - the same calculation used when the order is placed."""
    items = [(i.productId, i.quantity) for i in request.items if i.quantity > 0]
    return {"success": True, "data": delivery_service.quote_for_items(db, items, request.county)}


# ---------------------------------------------------------------------------
# Customer cancels an unpaid M-Pesa order from the payment screen
# ---------------------------------------------------------------------------
from fastapi import Body as _CancelBody


@router.post("/{order_id}/cancel-unpaid")
def cancel_unpaid_order(
    order_id: str,
    payload: dict = _CancelBody(...),
    db: Session = Depends(get_db)
):
    """Cancel a pending M-Pesa order (email must match). Stock goes back on sale."""
    from app.models.order import Order as _CancelOrder

    order = db.query(_CancelOrder).filter(_CancelOrder.id == order_id).first()
    email = str((payload or {}).get("email") or "").strip().lower()
    if not order or not email or (order.email or "").strip().lower() != email:
        raise HTTPException(status_code=404, detail="Order not found")

    # The customer may have paid a moment ago - check before cancelling
    try:
        payment_gateway.refresh(db, order)
        db.refresh(order)
    except Exception as e:
        print(f"[Orders] Payment check before cancelling {order_id} failed: {e}")

    if order.status != "pending":
        return {
            "success": True,
            "data": {"orderId": order.id, "state": "paid" if order.status != "cancelled" else "cancelled",
                     "receipt": order.mpesa_transaction_id},
        }

    OrderService(db).update_order_status(order_id, "cancelled")
    print(f"[Orders] Customer cancelled unpaid order {order_id}")
    try:
        from app.services.notification_service import NotificationService
        NotificationService(db).create_notification(
            title=f"Order {order_id} cancelled by customer",
            message=(f"{order.customer_name} cancelled order {order_id} "
                     f"(KSh {int(order.total or 0):,}) before paying. The items are back in stock."),
            notification_type="order_cancelled",
            priority="medium",
            related_entity="Order",
            related_id=order_id,
        )
    except Exception as e:
        print(f"[Orders] Could not create cancel notification for {order_id}: {e}")
    return {"success": True, "data": {"orderId": order_id, "state": "cancelled"}}
