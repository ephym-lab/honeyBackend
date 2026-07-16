from abc import ABC
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import date
from typing import Optional
import uuid

from app.models import order
from app.schemas.order import OrderCreate, OrderItemResponse
from app.models.order import Order
from app.models.product import Products
from app.services.email_service import EmailService
from app.services.email_templates import EmailTemplates


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
                customer_name=order.customer_name,
                order_id=order.id,
                order_date=str(order.order_date),
                items=order.items,
                subtotal=order.subtotal,
                shipping=order.shipping,
                total=order.total,
                payment_method=order.payment_method,
                address=order.address,
                city=order.city,
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
                customer_name=order.customer_name,
                order_id=order.id,
                status=status,
                items=order.items,
                total=order.total,
                message=message
            )
            
            subject = f"Order Status Update - {order.id}"
            self.email_service.send_html_email(order.email, subject, html_body)
            print(f"Order status email sent to {order.email}")
        except Exception as e:
            print(f"Failed to send order status email: {str(e)}")




    
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
        try:
            # Calculate totals and validate products
            items_with_details = []
            subtotal = 0
            
            for item in order_data.items:
                # Get product details
                product = self.db.query(Products).filter(
                    Products.id == item.productId
                ).first()
                
                if not product:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Product {item.productId} not found"
                    )
                
                # Check stock
                if product.stock < item.quantity:
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
            shipping = 500  # KES 500 flat shipping
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
                product.stock -= item.quantity
            
            self.db.commit()
            self.db.refresh(new_order)
            
            # Send confirmation email (non-blocking)
            try:
                self._send_order_confirmation_email(order=new_order)
            except Exception as e:
                print(f"Order created but email failed: {str(e)}")


            
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
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        order.status = status
        if mpesa_transaction_id:
            order.mpesa_transaction_id = mpesa_transaction_id
        
        self.db.commit()
        self.db.refresh(order)
        
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
        try:
            orders = self.db.query(Order).all()
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
            orders = self.db.query(Order).filter(Order.user_id == user_id).all()
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
        if update_data.customerName:
            order.customer_name = update_data.customerName
        if update_data.phone:
            order.phone = update_data.phone
        if update_data.address:
            order.address = update_data.address
        if update_data.city:
            order.city = update_data.city
        if update_data.county:
            order.county = update_data.county
        
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