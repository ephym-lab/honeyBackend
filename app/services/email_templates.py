"""
HTML Email Templates for HoneyBiz
Beautiful, responsive email templates for all customer communications
"""

from typing import Dict, List, Optional


class EmailTemplates:
    """HTML email templates with modern, responsive design"""
    
    # Brand colors
    PRIMARY_COLOR = "#FF6B6B"
    SECONDARY_COLOR = "#4ECDC4"
    DARK_COLOR = "#2C3E50"
    LIGHT_COLOR = "#F8F9FA"
    SUCCESS_COLOR = "#51CF66"
    WARNING_COLOR = "#FFD93D"
    
    @staticmethod
    def _base_template(content: str, preheader: str = "") -> str:
        """
        Base HTML template with responsive design and brand styling
        
        Args:
            content: Main email content
            preheader: Preview text shown in email clients
            
        Returns:
            Complete HTML email
        """
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <title>HoneyBiz</title>
    <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f4f4f4;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }}
        .email-container {{
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
        }}
        .header {{
            background: linear-gradient(135deg, {EmailTemplates.PRIMARY_COLOR} 0%, {EmailTemplates.SECONDARY_COLOR} 100%);
            padding: 40px 20px;
            text-align: center;
        }}
        .header h1 {{
            color: #ffffff;
            margin: 0;
            font-size: 32px;
            font-weight: 700;
            text-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .header .tagline {{
            color: #ffffff;
            margin: 10px 0 0 0;
            font-size: 14px;
            opacity: 0.9;
        }}
        .content {{
            padding: 40px 30px;
            color: {EmailTemplates.DARK_COLOR};
            line-height: 1.6;
        }}
        .content h2 {{
            color: {EmailTemplates.DARK_COLOR};
            font-size: 24px;
            margin-top: 0;
            margin-bottom: 20px;
        }}
        .content p {{
            margin: 15px 0;
            font-size: 16px;
        }}
        .button {{
            display: inline-block;
            padding: 14px 30px;
            background: linear-gradient(135deg, {EmailTemplates.PRIMARY_COLOR} 0%, {EmailTemplates.SECONDARY_COLOR} 100%);
            color: #ffffff !important;
            text-decoration: none;
            border-radius: 25px;
            font-weight: 600;
            margin: 20px 0;
            box-shadow: 0 4px 15px rgba(255, 107, 107, 0.3);
            transition: transform 0.2s;
        }}
        .button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(255, 107, 107, 0.4);
        }}
        .order-summary {{
            background-color: {EmailTemplates.LIGHT_COLOR};
            border-radius: 10px;
            padding: 25px;
            margin: 25px 0;
        }}
        .order-item {{
            padding: 15px 0;
            border-bottom: 1px solid #dee2e6;
        }}
        .order-item:last-child {{
            border-bottom: none;
        }}
        .order-item-name {{
            font-weight: 600;
            color: {EmailTemplates.DARK_COLOR};
            font-size: 16px;
        }}
        .order-item-details {{
            color: #6c757d;
            font-size: 14px;
            margin-top: 5px;
        }}
        .total-row {{
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            font-size: 16px;
        }}
        .total-row.grand-total {{
            font-weight: 700;
            font-size: 20px;
            color: {EmailTemplates.PRIMARY_COLOR};
            border-top: 2px solid {EmailTemplates.PRIMARY_COLOR};
            margin-top: 15px;
            padding-top: 15px;
        }}
        .info-box {{
            background-color: #e7f5ff;
            border-left: 4px solid {EmailTemplates.SECONDARY_COLOR};
            padding: 15px 20px;
            margin: 20px 0;
            border-radius: 5px;
        }}
        .status-badge {{
            display: inline-block;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .status-pending {{
            background-color: #fff3cd;
            color: #856404;
        }}
        .status-paid {{
            background-color: #d1ecf1;
            color: #0c5460;
        }}
        .status-processing {{
            background-color: #cce5ff;
            color: #004085;
        }}
        .status-shipped {{
            background-color: #d4edda;
            color: #155724;
        }}
        .status-delivered {{
            background-color: #d1f2eb;
            color: #0f5132;
        }}
        .status-cancelled {{
            background-color: #f8d7da;
            color: #721c24;
        }}
        .footer {{
            background-color: {EmailTemplates.DARK_COLOR};
            color: #ffffff;
            padding: 30px 20px;
            text-align: center;
            font-size: 14px;
        }}
        .footer a {{
            color: {EmailTemplates.SECONDARY_COLOR};
            text-decoration: none;
        }}
        .footer .social-links {{
            margin: 20px 0;
        }}
        .footer .social-links a {{
            display: inline-block;
            margin: 0 10px;
            color: #ffffff;
        }}
        .divider {{
            height: 1px;
            background: linear-gradient(to right, transparent, {EmailTemplates.PRIMARY_COLOR}, transparent);
            margin: 30px 0;
        }}
        @media only screen and (max-width: 600px) {{
            .content {{
                padding: 30px 20px;
            }}
            .header h1 {{
                font-size: 26px;
            }}
            .total-row {{
                font-size: 14px;
            }}
            .total-row.grand-total {{
                font-size: 18px;
            }}
        }}
    </style>
</head>
<body>
    <div style="display: none; max-height: 0; overflow: hidden;">{preheader}</div>
    <div class="email-container">
        <div class="header">
            <h1>🍯 HoneyBiz</h1>
            <p class="tagline">Illuminate Your Space with Elegance</p>
        </div>
        {content}
        <div class="footer">
            <p><strong>HoneyBiz - Premium Handcrafted HoneyBiz</strong></p>
            <p>Thank you for choosing us to brighten your space!</p>
            <div class="divider" style="background: linear-gradient(to right, transparent, {EmailTemplates.SECONDARY_COLOR}, transparent);"></div>
            <p style="font-size: 12px; color: #adb5bd; margin-top: 20px;">
                This email was sent to you because you are a valued customer of HoneyBiz.<br>
                If you have any questions, please reply to this email or contact our support team.
            </p>
            <p style="font-size: 12px; color: #adb5bd; margin-top: 10px;">
                © 2026 HoneyBiz. All rights reserved.
            </p>
        </div>
    </div>
</body>
</html>
        """
    
    @staticmethod
    def order_confirmation(
        customer_name: str,
        order_id: str,
        order_date: str,
        items: List[Dict],
        subtotal: float,
        shipping: float,
        total: float,
        payment_method: str,
        address: str,
        city: str,
        county: str
    ) -> str:
        """
        Order confirmation email template
        
        Args:
            customer_name: Customer's name
            order_id: Order ID
            order_date: Order date
            items: List of order items
            subtotal: Subtotal amount
            shipping: Shipping cost
            total: Total amount
            payment_method: Payment method
            address: Delivery address
            city: City
            county: County
            
        Returns:
            HTML email content
        """
        # Build items HTML
        items_html = ""
        for item in items:
            items_html += f"""
            <div class="order-item">
                <div class="order-item-name">{item['productName']}</div>
                <div class="order-item-details">
                    Quantity: {item['quantity']} × KES {item['price']:,.2f} = KES {(item['quantity'] * item['price']):,.2f}
                </div>
            </div>
            """
        
        # Payment method display
        payment_display = payment_method.upper().replace("_", " ")
        
        content = f"""
        <div class="content">
            <h2>🎉 Order Confirmed!</h2>
            <p>Hi <strong>{customer_name}</strong>,</p>
            <p>Thank you for your order! We're excited to prepare your honey and equipment for delivery.</p>
            
            <div class="info-box">
                <strong>Order ID:</strong> {order_id}<br>
                <strong>Order Date:</strong> {order_date}<br>
                <strong>Status:</strong> <span class="status-badge status-pending">Pending</span>
            </div>
            
            <h3 style="color: {EmailTemplates.DARK_COLOR}; margin-top: 30px;">Order Summary</h3>
            <div class="order-summary">
                {items_html}
                
                <div style="margin-top: 20px;">
                    <div class="total-row">
                        <span>Subtotal:</span>
                        <span>KES {subtotal:,.2f}</span>
                    </div>
                    <div class="total-row">
                        <span>Shipping:</span>
                        <span>KES {shipping:,.2f}</span>
                    </div>
                    <div class="total-row grand-total">
                        <span>Total:</span>
                        <span>KES {total:,.2f}</span>
                    </div>
                </div>
            </div>
            
            <h3 style="color: {EmailTemplates.DARK_COLOR}; margin-top: 30px;">Delivery Information</h3>
            <div class="info-box">
                <strong>Address:</strong> {address}<br>
                <strong>City:</strong> {city}<br>
                <strong>County:</strong> {county}<br>
                <strong>Payment Method:</strong> {payment_display}
            </div>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="#" class="button">Track Your Order</a>
            </div>
            
            <div class="divider"></div>
            
            <p style="color: #6c757d; font-size: 14px;">
                <strong>What's Next?</strong><br>
                We'll send you another email once your order has been shipped with tracking information.
                If you have any questions, feel free to reply to this email.
            </p>
        </div>
        """
        
        preheader = f"Your order {order_id} has been confirmed! Thank you for shopping with HoneyBiz."
        return EmailTemplates._base_template(content, preheader)
    
    @staticmethod
    def order_status_update(
        customer_name: str,
        order_id: str,
        status: str,
        items: List[Dict],
        total: float,
        message: Optional[str] = None
    ) -> str:
        """
        Order status update email template
        
        Args:
            customer_name: Customer's name
            order_id: Order ID
            status: New order status
            items: List of order items
            total: Total amount
            message: Optional custom message
            
        Returns:
            HTML email content
        """
        # Status-specific content
        status_messages = {
            "paid": {
                "icon": "💳",
                "title": "Payment Confirmed",
                "message": "Your payment has been successfully processed. We're preparing your order for shipment!"
            },
            "processing": {
                "icon": "📦",
                "title": "Order Being Prepared",
                "message": "Great news! We're carefully preparing your items for shipment."
            },
            "shipped": {
                "icon": "🚚",
                "title": "Order Shipped",
                "message": "Your order is on its way! You should receive it within 2-3 business days."
            },
            "delivered": {
                "icon": "✅",
                "title": "Order Delivered",
                "message": "Your order has been delivered! We hope you love your new items."
            },
            "cancelled": {
                "icon": "❌",
                "title": "Order Cancelled",
                "message": "Your order has been cancelled. If you didn't request this, please contact us immediately."
            }
        }
        
        status_info = status_messages.get(status.lower(), {
            "icon": "📋",
            "title": "Order Status Update",
            "message": f"Your order status has been updated to {status}."
        })
        
        # Build items HTML
        items_html = ""
        for item in items:
            items_html += f"""
            <div class="order-item">
                <div class="order-item-name">{item['productName']}</div>
                <div class="order-item-details">Quantity: {item['quantity']}</div>
            </div>
            """
        
        custom_message = f"<p>{message}</p>" if message else ""
        
        content = f"""
        <div class="content">
            <h2>{status_info['icon']} {status_info['title']}</h2>
            <p>Hi <strong>{customer_name}</strong>,</p>
            <p>{status_info['message']}</p>
            {custom_message}
            
            <div class="info-box">
                <strong>Order ID:</strong> {order_id}<br>
                <strong>Status:</strong> <span class="status-badge status-{status.lower()}">{status.upper()}</span>
            </div>
            
            <h3 style="color: {EmailTemplates.DARK_COLOR}; margin-top: 30px;">Order Items</h3>
            <div class="order-summary">
                {items_html}
                <div class="total-row grand-total" style="margin-top: 20px;">
                    <span>Total:</span>
                    <span>KES {total:,.2f}</span>
                </div>
            </div>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="#" class="button">View Order Details</a>
            </div>
            
            <div class="divider"></div>
            
            <p style="color: #6c757d; font-size: 14px;">
                Need help? Reply to this email or contact our customer support team.
            </p>
        </div>
        """
        
        preheader = f"Order {order_id} - {status_info['title']}"
        return EmailTemplates._base_template(content, preheader)
    
    @staticmethod
    def newsletter_subscription(email: str) -> str:
        """
        Newsletter subscription confirmation email
        
        Args:
            email: Subscriber's email
            
        Returns:
            HTML email content
        """
        content = f"""
        <div class="content">
            <h2>🎉 Welcome to HoneyBiz Newsletter!</h2>
            <p>Hi there,</p>
            <p>Thank you for subscribing to our newsletter! We're thrilled to have you join our community of beekeeping enthusiasts.</p>
            
            <div class="info-box">
                <strong>✨ What to Expect:</strong><br><br>
                • Exclusive discounts and early access to new products<br>
                • Tips for beekeeping and home ambiance<br>
                • Behind-the-scenes looks at our honey harvesting process<br>
                • Special offers just for our subscribers
            </div>
            
            <p>You'll receive our newsletter with the latest updates, special offers, and beekeeping inspiration straight to your inbox.</p>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="#" class="button">Shop Now</a>
            </div>
            
            <div class="divider"></div>
            
            <p style="color: #6c757d; font-size: 14px;">
                <strong>Subscribed Email:</strong> {email}<br><br>
                You can unsubscribe at any time by clicking the unsubscribe link in any of our emails.
            </p>
        </div>
        """
        
        preheader = "Welcome to HoneyBiz! Get ready for exclusive offers and beekeeping inspiration."
        return EmailTemplates._base_template(content, preheader)
    
    @staticmethod
    def newsletter_unsubscription(email: str) -> str:
        """
        Newsletter unsubscription confirmation email
        
        Args:
            email: Subscriber's email
            
        Returns:
            HTML email content
        """
        content = f"""
        <div class="content">
            <h2>😢 We're Sorry to See You Go</h2>
            <p>Hi there,</p>
            <p>You have been successfully unsubscribed from the HoneyBiz newsletter.</p>
            
            <div class="info-box">
                <strong>Unsubscribed Email:</strong> {email}<br><br>
                You will no longer receive promotional emails from us.
            </div>
            
            <p>We're sad to see you go, but we understand. If you change your mind, you're always welcome back!</p>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="#" class="button">Resubscribe</a>
            </div>
            
            <div class="divider"></div>
            
            <p style="color: #6c757d; font-size: 14px;">
                <strong>Note:</strong> You'll still receive important transactional emails about your orders.<br><br>
                If you unsubscribed by mistake or have any questions, please reply to this email.
            </p>
        </div>
        """
        
        preheader = "You've been unsubscribed from HoneyBiz newsletter."
        return EmailTemplates._base_template(content, preheader)
