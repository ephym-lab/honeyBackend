from abc import ABC
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import date, timedelta
from sqlalchemy import func
from typing import Optional
import uuid
import os

from app.models import order
from app.schemas.order import OrderCreate, OrderItemResponse
from app.models.order import Order
from app.models.product import Products
from app.services.email_service import EmailService
from app.services.email_templates import EmailTemplates
from app.services.notification_service import NotificationService


class OrderManagerService(ABC):
    """Abstract base class for order management services."""
    
    def __init__(self, db: Session):
        self.db = db


class OrderService(OrderManagerService):
    """Service for handling order operations."""
    
    def __init__(self, db: Session):
        super().__init__(db)
        self.email_service = EmailService()
        
    def _send_order_confirmation_email(self, order: Order):
        """
        Send HTML order confirmation email
        
        Args:
            order: Order object
        """
        try:
            html_body = EmailTemplates.order_confirmation(
                email=order.email,
                # pyrefly: ignore [bad-argument-type]
                customer_name=order.customer_name,
                # pyrefly: ignore [bad-argument-type]
                order_id=order.id,
                order_date=str(order.order_date),
                # pyrefly: ignore [bad-argument-type]
                items=order.items,
                # pyrefly: ignore [bad-argument-type]
                subtotal=order.subtotal,
                # pyrefly: ignore [bad-argument-type]
                shipping=order.shipping,
                # pyrefly: ignore [bad-argument-type]
                total=order.total,
                # pyrefly: ignore [bad-argument-type]
                payment_method=order.payment_method,
                # pyrefly: ignore [bad-argument-type]
                address=order.address,
                # pyrefly: ignore [bad-argument-type]
                city=order.city,
                # pyrefly: ignore [bad-argument-type]
                county=order.county
            )
            
            subject = f"Order Confirmation - {order.id}"
            self.email_service.send_html_email(order.email, subject, html_body)
            print(f"Order confirmation email sent to {order.email}")
        except Exception as e:
            print(f"Failed to send order confirmation email: {str(e)}")
    
    def _send_order_status_email(self, order: Order, status: str, message: Optional[str] = None):
        """
        Send HTML order status update email
        
        Args:
            order: Order object
            status: New order status
            message: Optional custom message
        """
        try:
            html_body = EmailTemplates.order_status_update(
                email=order.email,
                # pyrefly: ignore [bad-argument-type]
                customer_name=order.customer_name,
                # pyrefly: ignore [bad-argument-type]
                order_id=order.id,
                status=status,
                # pyrefly: ignore [bad-argument-type]
                items=order.items,
                # pyrefly: ignore [bad-argument-type]
                total=order.total,
                message=message
            )
            
            subject = f"Order Status Update - {order.id}"
            self.email_service.send_html_email(order.email, subject, html_body)
            print(f"Order status email sent to {order.email}")
        except Exception as e:
            print(f"Failed to send order status email: {str(e)}")

    def _send_admin_order_notification(self, order: Order):
        """
        Send HTML order notification email to admin
        """
        try:
            html_body = EmailTemplates.admin_order_notification(
                email=order.email,
                phone=order.phone,
                # pyrefly: ignore [bad-argument-type]
                customer_name=order.customer_name,
                # pyrefly: ignore [bad-argument-type]
                order_id=order.id,
                order_date=str(order.order_date),
                # pyrefly: ignore [bad-argument-type]
                items=order.items,
                # pyrefly: ignore [bad-argument-type]
                subtotal=order.subtotal,
                # pyrefly: ignore [bad-argument-type]
                shipping=order.shipping,
                # pyrefly: ignore [bad-argument-type]
                total=order.total,
                # pyrefly: ignore [bad-argument-type]
                payment_method=order.payment_method,
                # pyrefly: ignore [bad-argument-type]
                address=order.address,
                # pyrefly: ignore [bad-argument-type]
                city=order.city,
                # pyrefly: ignore [bad-argument-type]
                county=order.county
            )
            
            admin_email = os.getenv("ADMIN_EMAIL", self.email_service.from_email)
            subject = f"New Order Received - {order.id}"
            self.email_service.send_html_email(admin_email, subject, html_body)
            print(f"Admin order notification email sent to {admin_email}")
        except Exception as e:
            print(f"Failed to send admin order notification email: {str(e)}")

    
    def create_order(self, order_data: OrderCreate):
        """
        Create a new order.
        
        Args:
            order_data: Order creation data
            
        Returns:
            dict: Success response with order data
            
        Raises:
            HTTPException: If order creation fails or products not found
        """
        # Free up stock held by M-Pesa orders that were never paid
        self.expire_unpaid_mpesa_orders()

        try:
            # Calculate totals and validate products
            items_with_details = []
            subtotal = 0
            
            # Lock each product while this order is saved, so two customers cannot
            # both buy the last item at the same moment. Products are locked in a fixed
            # order (by id) so two orders can never wait for each other forever.
            for item in sorted(order_data.items, key=lambda i: str(i.productId)):
                # Get product details (locked until this order is saved)
                product = self.db.query(Products).filter(
                    Products.id == item.productId
                ).with_for_update().first()
                
                if not product:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Product {item.productId} not found"
                    )
                
                # Check stock (adding up the same product listed twice in one order)
                wanted = sum(i.quantity for i in order_data.items if str(i.productId) == str(item.productId))
                if product.stock < wanted:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Insufficient stock for {product.name}. Available: {product.stock}"
                    )
                
                # Calculate item total
                item_total = product.price * item.quantity
                subtotal += item_total
                
                # Add item with details
                items_with_details.append({
                    "productId": str(product.id),
                    "productName": product.name,
                    "quantity": item.quantity,
                    "price": product.price
                })
            
            # Calculate shipping (flat rate for now)
            # Delivery fee by zone + weight (Admin > Delivery)
            from app.services import delivery_service
            shipping = delivery_service.quote_for_items(
                self.db,
                [(item.productId, item.quantity) for item in order_data.items],
                order_data.county,
            )["shipping"]
            total = subtotal + shipping
            
            # Generate order ID
            order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"
            
            # Create order
            new_order = Order(
                id=order_id,
                customer_name=order_data.customerName,
                email=order_data.email,
                phone=order_data.phone,
                address=order_data.address,
                city=order_data.city,
                county=order_data.county,
                order_notes=order_data.orderNotes,
                items=items_with_details,
                subtotal=subtotal,
                shipping=shipping,
                total=total,
                payment_method=order_data.paymentMethod,
                mpesa_phone=order_data.mpesaPhone if order_data.paymentMethod == "mpesa" else None,
                status="pending",
                order_date=date.today()
            )
            
            self.db.add(new_order)
            
            # Update product stock
            for item in order_data.items:
                product = self.db.query(Products).filter(
                    Products.id == item.productId
                ).first()
                # pyrefly: ignore [missing-attribute]
                product.stock -= item.quantity
            
            self.db.commit()
            self.db.refresh(new_order)
            
            # M-Pesa orders are announced (customer email, admin email, bell) only once
            # they are PAID - see update_order_status. Other orders: straight away.
            if new_order.payment_method != "mpesa":
                self._announce_new_order(new_order)
            
            return {
                "success": True,
                "data": {
                    "id": new_order.id,
                    "customerName": new_order.customer_name,
                    "email": new_order.email,
                    "phone": new_order.phone,
                    "address": new_order.address,
                    "city": new_order.city,
                    "county": new_order.county,
                    "orderNotes": new_order.order_notes,
                    "items": new_order.items,
                    "subtotal": new_order.subtotal,
                    "shipping": new_order.shipping,
                    "total": new_order.total,
                    "paymentMethod": new_order.payment_method,
                    "mpesaPhone": new_order.mpesa_phone,
                    "status": new_order.status,
                    "orderDate": new_order.order_date,
                    "createdAt": new_order.created_at,
                    "updatedAt": new_order.updated_at
                },
                "message": "Order created successfully"
            }
            
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create order: {str(e)}"
            )
    
    def get_order(self, order_id: str):
        """
        Get order by ID.
        
        Args:
            order_id: Order ID
            
        Returns:
            dict: Success response with order data
            
        Raises:
            HTTPException: If order not found
        """
        order = self.db.query(Order).filter(Order.id == order_id).first()
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        return {
            "success": True,
            "data": {
                "id": order.id,
                "customerName": order.customer_name,
                "email": order.email,
                "phone": order.phone,
                "address": order.address,
                "city": order.city,
                "county": order.county,
                "orderNotes": order.order_notes,
                "items": order.items,
                "subtotal": order.subtotal,
                "shipping": order.shipping,
                "total": order.total,
                "paymentMethod": order.payment_method,
                "mpesaPhone": order.mpesa_phone,
                "mpesaTransactionId": order.mpesa_transaction_id,
                "status": order.status,
                "orderDate": order.order_date,
                "createdAt": order.created_at,
                "updatedAt": order.updated_at
            }
        }
    
    def update_order_status(self, order_id: str, status: str, mpesa_transaction_id: Optional[str] = None):
        """
        Update order status (for webhooks/admin).
        
        Args:
            order_id: Order ID
            status: New status
            mpesa_transaction_id: M-Pesa transaction ID if applicable
            
        Returns:
            dict: Success response
            
        Raises:
            HTTPException: If order not found
        """
        order = self.db.query(Order).filter(Order.id == order_id).first()
        
        if not order:
            raise HTTPException(
                # pyrefly: ignore [missing-attribute]
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        previous_status = str(order.status or "").lower()

        # Return stock when cancelling (or take it out again when re-opening)
        self._adjust_stock_for_status_change(order, order.status, status)

        # pyrefly: ignore [bad-assignment]
        order.status = status
        if mpesa_transaction_id:
            # pyrefly: ignore [bad-assignment]
            order.mpesa_transaction_id = mpesa_transaction_id
        
        self.db.commit()
        self.db.refresh(order)
        
        just_paid = (
            previous_status == "pending"
            and str(status).lower() == "paid"
            and order.payment_method == "mpesa"
        )
        if just_paid:
            # First news of this order: full confirmation to the customer,
            # new-order email to the admin and the bell notification
            self._announce_new_order(order)
        else:
            #send email notification about status update 
            try:
                self._send_order_status_email(
                    order=order,
                    status=status,
                    message=f"Your order status has been updated."
                )
                print(f"Status update email sent to {order.email} successfully.")
            except Exception as e:
                print(f"Status update email failed: {str(e)}")

        
        return {
            "success": True,
            "data": {
                "id": order.id,
                "customerName": order.customer_name,
                "email": order.email,
                "phone": order.phone,
                "address": order.address,
                "city": order.city,
                "county": order.county,
                "orderNotes": order.order_notes,
                "items": order.items,
                "subtotal": order.subtotal,
                "shipping": order.shipping,
                "total": order.total,
                "paymentMethod": order.payment_method,
                "mpesaPhone": order.mpesa_phone,
                "mpesaTransactionId": order.mpesa_transaction_id,
                "status": order.status,
                "orderDate": order.order_date,
                "createdAt": order.created_at,
                "updatedAt": order.updated_at
            },
            "message": f"Order status updated to {status}"
        }

    def get_orders(self):
        """
        Get all orders.
        
        Returns:
            dict: Response with message and list of orders
        """
        self.expire_unpaid_mpesa_orders()

        try:
            orders = self.db.query(Order).order_by(Order.created_at.desc()).all()
            return {
                "success": True,
                "message": "Orders retrieved successfully",
                "data": [
                    {
                        "id": order.id,
                        "customerName": order.customer_name,
                        "email": order.email,
                        "phone": order.phone,
                        "address": order.address,
                        "city": order.city,
                        "county": order.county,
                        "orderNotes": order.order_notes,
                        "items": order.items,
                        "subtotal": order.subtotal,
                        "shipping": order.shipping,
                        "total": order.total,
                        "paymentMethod": order.payment_method,
                        "mpesaPhone": order.mpesa_phone,
                        "mpesaTransactionId": order.mpesa_transaction_id,
                        "status": order.status,
                        "orderDate": order.order_date,
                        "createdAt": order.created_at,
                        "updatedAt": order.updated_at
                    }
                    for order in orders
                ]
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get orders: {str(e)}"
            )
        
    def get_user_orders(self, user_id: str):
        """
        Get all orders for a specific user.
        
        Args:
            user_id: User ID
            
        Returns:
            list: List of orders for the user
        """
        try:
            orders = self.db.query(Order).filter(Order.user_id == user_id).order_by(Order.created_at.desc()).all()
            return {
                "message": "Orders retrieved successfully",
                "success": True,
                "data": orders
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get orders: {str(e)}"
            )
    
    def get_orders_by_email(self, email: str):
        """
        Get all orders for a specific customer email.
        
        Args:
            email: Customer email address
            
        Returns:
            dict: Response with message and list of orders
        """
        try:
            orders = self.db.query(Order).filter(Order.email == email).order_by(Order.created_at.desc()).all()
            return {
                "success": True,
                "message": f"Orders retrieved successfully for {email}",
                "data": [
                    {
                        "id": order.id,
                        "customerName": order.customer_name,
                        "email": order.email,
                        "phone": order.phone,
                        "address": order.address,
                        "city": order.city,
                        "county": order.county,
                        "orderNotes": order.order_notes,
                        "items": order.items,
                        "subtotal": order.subtotal,
                        "shipping": order.shipping,
                        "total": order.total,
                        "paymentMethod": order.payment_method,
                        "mpesaPhone": order.mpesa_phone,
                        "mpesaTransactionId": order.mpesa_transaction_id,
                        "status": order.status,
                        "orderDate": order.order_date,
                        "createdAt": order.created_at,
                        "updatedAt": order.updated_at
                    }
                    for order in orders
                ]
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get orders: {str(e)}"
            )
    
    def track_order(self, order_id: str):
        """
        Track order status.
        
        Args:
            order_id: Order ID
            
        Returns:
            dict: Success response with order tracking data
        """
        order = self.db.query(Order).filter(Order.id == order_id).first()
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        return {
            "success": True,
            "message": f"Order tracking information for {order_id}",
            "data": {
                "id": order.id,
                "customerName": order.customer_name,
                "email": order.email,
                "phone": order.phone,
                "address": order.address,
                "city": order.city,
                "county": order.county,
                "orderNotes": order.order_notes,
                "items": order.items,
                "subtotal": order.subtotal,
                "shipping": order.shipping,
                "total": order.total,
                "paymentMethod": order.payment_method,
                "mpesaPhone": order.mpesa_phone,
                "mpesaTransactionId": order.mpesa_transaction_id,
                "status": order.status,
                "orderDate": order.order_date,
                "createdAt": order.created_at,
                "updatedAt": order.updated_at
            }
        }
    
    def update_order(self, order_id: str, update_data: dict):
        """
        Update order details (only for pending orders).
        
        Args:
            order_id: Order ID
            update_data: Order update data
            
        Returns:
            dict: Success response with updated order
        """
        order = self.db.query(Order).filter(Order.id == order_id).first()
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        # Only allow updates for pending orders
        if order.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot update order with status '{order.status}'. Only pending orders can be updated."
            )
        
        # Update fields if provided
        if "customerName" in update_data:
            order.customer_name = update_data["customerName"]
        if "phone" in update_data:
            order.phone = update_data["phone"]
        if "address" in update_data:
            order.address = update_data["address"]
        if "city" in update_data:
            order.city = update_data["city"]
        if "county" in update_data:
            order.county = update_data["county"]
        if "orderNotes" in update_data:
            order.order_notes = update_data["orderNotes"]
        
        try:
            self.db.commit()
            self.db.refresh(order)
            
            return {
                "success": True,
                "message": "Order updated successfully",
                "data": {
                    "id": order.id,
                    "customerName": order.customer_name,
                    "email": order.email,
                    "phone": order.phone,
                    "address": order.address,
                    "city": order.city,
                    "county": order.county,
                    "orderNotes": order.order_notes,
                    "items": order.items,
                    "subtotal": order.subtotal,
                    "shipping": order.shipping,
                    "total": order.total,
                    "paymentMethod": order.payment_method,
                    "mpesaPhone": order.mpesa_phone,
                    "mpesaTransactionId": order.mpesa_transaction_id,
                    "status": order.status,
                    "orderDate": order.order_date,
                    "createdAt": order.created_at,
                    "updatedAt": order.updated_at
                }
            }
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update order: {str(e)}"
            )
    
    
    def cancel_order(self, order_id: str):
        """
        Cancel an order (only for pending or paid orders).
        
        Args:
            order_id: Order ID
            
        Returns:
            dict: Success response
        """
        order = self.db.query(Order).filter(Order.id == order_id).first()
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        # Only allow cancellation for pending or paid orders
        if order.status not in ["pending", "paid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel order with status '{order.status}'. Only pending or paid orders can be cancelled."
            )
        
        # Update status to cancelled
        # pyrefly: ignore [bad-assignment]
        order.status = "cancelled"
        
        # Restore product stock
        try:
            for item in order.items:
                product = self.db.query(Products).filter(
                    Products.id == item["productId"]
                ).first()
                if product:
                    product.stock += item["quantity"]
            
            self.db.commit()
            
            # Let the customer know (never blocks the cancellation)
            
            try:
            
                self._send_order_status_email(order=order, status="cancelled")
            
            except Exception as e:
            
                print(f"Cancellation email failed: {e}")
            
            return {
                "success": True,
                "message": f"Order {order_id} has been cancelled successfully"
            }
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to cancel order: {str(e)}"
            )
    
    def search_orders(self, query: str):
        """
        Search orders by order ID, customer name, email, or phone.
        
        Args:
            query: Search query string
            
        Returns:
            dict: Response with search results
        """
        try:
            # Case-insensitive search across multiple fields
            search_filter = f"%{query}%"
            orders = self.db.query(Order).filter(
                (Order.id.ilike(search_filter)) |
                (Order.customer_name.ilike(search_filter)) |
                (Order.email.ilike(search_filter)) |
                (Order.phone.ilike(search_filter))
            ).order_by(Order.created_at.desc()).all()
            
            return {
                "success": True,
                "message": f"Found {len(orders)} orders matching '{query}'",
                "data": [
                    {
                        "id": order.id,
                        "customerName": order.customer_name,
                        "email": order.email,
                        "phone": order.phone,
                        "address": order.address,
                        "city": order.city,
                        "county": order.county,
                        "orderNotes": order.order_notes,
                        "items": order.items,
                        "subtotal": order.subtotal,
                        "shipping": order.shipping,
                        "total": order.total,
                        "paymentMethod": order.payment_method,
                        "mpesaPhone": order.mpesa_phone,
                        "mpesaTransactionId": order.mpesa_transaction_id,
                        "status": order.status,
                        "orderDate": order.order_date,
                        "createdAt": order.created_at,
                        "updatedAt": order.updated_at
                    }
                    for order in orders
                ]
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to search orders: {str(e)}"
            )   

    def delete_order(self, order_id: str):
        """
        Delete order by ID.
        
        Args:
            order_id: Order ID
            
        Returns:
            dict: Success response
            
        Raises:
            HTTPException: If order not found
        """
        order = self.db.query(Order).filter(Order.id == order_id).first()
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        self.db.delete(order)
        self.db.commit()
        
        return {
            "success": True,
            "message": "Order deleted successfully"
        }

    def bulk_delete_orders(self, order_ids: list[str]):
        """
        Delete multiple orders by ID.
        
        Args:
            order_ids: List of Order IDs
            
        Returns:
            dict: Success response
            
        Raises:
            HTTPException: If an error occurs
        """
        try:
            # Delete orders that match the IDs
            deleted_count = self.db.query(Order).filter(Order.id.in_(order_ids)).delete(synchronize_session=False)
            self.db.commit()
            
            return {
                "success": True,
                "message": f"Successfully deleted {deleted_count} orders"
            }
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to bulk delete orders: {str(e)}"
            )


    # ------------------------------------------------------------------ stock helpers

    def _change_stock(self, order, direction: int):
        """direction=+1 puts the order's items back in stock, -1 takes them out again."""
        for item in order.items or []:
            product = self.db.query(Products).filter(
                Products.id == item["productId"]
            ).first()
            if not product:
                continue
            if direction < 0 and product.stock < item["quantity"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Not enough stock to re-open this order: {product.name} has {product.stock} left"
                )
            product.stock += direction * item["quantity"]

    def _adjust_stock_for_status_change(self, order, previous_status, new_status):
        """Cancelling returns stock; re-opening a cancelled order takes it out again."""
        was_cancelled = str(previous_status or "").lower() == "cancelled"
        now_cancelled = str(new_status or "").lower() == "cancelled"
        if now_cancelled and not was_cancelled:
            self._change_stock(order, +1)
        elif was_cancelled and not now_cancelled:
            self._change_stock(order, -1)

    def expire_unpaid_mpesa_orders(self):
        """
        Cancel M-Pesa orders still unpaid after UNPAID_ORDER_TIMEOUT_HOURS (from .env)
        and return their stock. 0 (the default) switches this off.
        """
        try:
            hours = float(os.getenv("UNPAID_ORDER_TIMEOUT_HOURS", "0") or 0)
        except ValueError:
            hours = 0
        if hours <= 0:
            return 0

        try:
            stale = self.db.query(Order).filter(
                Order.status == "pending",
                Order.payment_method == "mpesa",
                Order.created_at < func.now() - timedelta(hours=hours),
            ).all()
            if not stale:
                return 0

            for order in stale:
                self._change_stock(order, +1)
                order.status = "cancelled"
            self.db.commit()

            shown = int(hours) if hours == int(hours) else hours
            for order in stale:
                print(f"[Orders] Auto-cancelled unpaid M-Pesa order {order.id}")
                try:
                    from app.services.notification_service import NotificationService
                    NotificationService(self.db).create_notification(
                        title=f"Order {order.id} cancelled - not paid",
                        message=(f"{order.customer_name} did not pay order {order.id} "
                                 f"(KSh {int(order.total or 0):,}) within {shown} hours, so it was "
                                 "cancelled automatically. The items are back in stock."),
                        notification_type="order_cancelled",
                        priority="low",
                        related_entity="Order",
                        related_id=str(order.id),
                    )
                except Exception as e:
                    print(f"[Orders] Could not create auto-cancel notification for {order.id}: {e}")
                try:
                    self._send_order_status_email(
                        order=order,
                        status="cancelled",
                        message=(
                            f"We did not receive your M-Pesa payment within {shown} hours, "
                            "so this order has been cancelled and the items released. "
                            "You are welcome to place the order again at any time."
                        ),
                    )
                except Exception as e:
                    print(f"Auto-cancel email failed for {order.id}: {e}")
            return len(stale)
        except Exception as e:
            self.db.rollback()
            print(f"[Orders] Could not expire unpaid orders: {e}")
            return 0


    def _announce_new_order(self, order):
        """Customer confirmation email, admin new-order email and the admin bell notification."""
        try:
            self._send_order_confirmation_email(order=order)
        except Exception as e:
            print(f"Order confirmation email failed: {str(e)}")
        try:
            self._send_admin_order_notification(order=order)
        except Exception as e:
            print(f"Admin new-order email failed: {str(e)}")
        try:
            paid = str(order.status or "").lower() == "paid"
            NotificationService(self.db).create_notification(
                title="New Paid Order" if paid else "New Order Received",
                message=f"Customer {order.customer_name} "
                        f"{'paid' if paid else 'placed an order'} KES {order.total:,.2f}"
                        f"{' by M-Pesa' if paid else ''}",
                notification_type="new_order",
                related_entity="Order",
                related_id=order.id,
            )
        except Exception as e:
            print(f"Failed to create in-app notification: {str(e)}")
