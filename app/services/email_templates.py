"""
HTML email templates for Pedni Honey.
Colours match the website (src/index.css). No emojis.
Links point to FRONTEND_URL from .env (e.g. http://localhost:5173 or your live site).
"""

import os
from html import escape
from typing import Dict, List, Optional
from urllib.parse import urlencode


def _frontend_url() -> str:
    return (os.getenv("FRONTEND_URL") or "http://localhost:5173").rstrip("/")


def _e(value) -> str:
    """Escape text that came from customers so it can't break the email."""
    return escape(str(value if value is not None else ""))


class EmailTemplates:
    """HTML email templates in the Pedni Honey brand colours."""

    # Brand colours - same as the website
    PRIMARY_COLOR = "#F4C011"      # honey yellow (buttons)
    PRIMARY_TEXT = "#1A1A1A"       # dark text on yellow
    DARK_COLOR = "#1A1A1A"         # headings / body text
    DARK_BG = "#201A0B"            # header / footer background
    DARK_BG_TEXT = "#F4C011"       # text on dark background
    MUTED_TEXT = "#555555"
    LIGHT_COLOR = "#FFFBE0"        # soft honey background
    WARM_COLOR = "#FFF8CC"
    BORDER_COLOR = "#E5E0C0"
    TEAL = "#0F6E6E"
    WARNING_COLOR = "#D66A3B"

    BUSINESS_NAME = "Pedni Honey"
    TAGLINE = "Nurturing Nature's Gift"
    CONTACT_PHONE = "0704 089 414"
    CONTACT_EMAIL = "pedni2021@gmail.com"
    POSTAL_ADDRESS = "P.O Box 157-40301, Kendu Bay"

    # ------------------------------------------------------------------ links

    @staticmethod
    def track_order_url(order_id: str, email: Optional[str] = None) -> str:
        params = {"id": order_id}
        if email:
            params["email"] = email
        return f"{_frontend_url()}/track-order?{urlencode(params)}"

    @staticmethod
    def account_invite(email: Optional[str] = None) -> str:
        """'Create an account' box for order emails. Empty unless CUSTOMER_ACCOUNTS_ENABLED=true."""
        if str(os.getenv("CUSTOMER_ACCOUNTS_ENABLED", "false")).strip().lower() not in ("1", "true", "yes", "on"):
            return ""
        url = f"{_frontend_url()}/account/register"
        if email:
            url += "?" + urlencode({"email": email})
        return f"""
            <div class="info-box" style="text-align: center;">
                <strong>Save your details for next time</strong><br>
                Create a free Pedni Honey account to see all your orders in one place and check out faster.
                Use this same email and your past orders will be added automatically.
                <div style="margin-top: 12px;">
                    <a href="{_e(url)}" style="color: {EmailTemplates.TEAL}; font-weight: 600;">Create my account</a>
                </div>
            </div>
        """

    @staticmethod
    def admin_orders_url(order_id: Optional[str] = None) -> str:
        url = f"{_frontend_url()}/admin/orders"
        return f"{url}?{urlencode({'search': order_id})}" if order_id else url

    @staticmethod
    def button(label: str, url: str) -> str:
        """Bulletproof email button (works in Gmail, Outlook and phones)."""
        return f"""
        <table role="presentation" border="0" cellpadding="0" cellspacing="0" align="center" style="margin: 30px auto;">
          <tr>
            <td align="center" bgcolor="{EmailTemplates.PRIMARY_COLOR}" style="border-radius: 8px;">
              <a href="{_e(url)}" target="_blank"
                 style="display: inline-block; padding: 14px 32px; font-family: 'Poppins', 'Segoe UI', Arial, sans-serif;
                        font-size: 16px; font-weight: 600; color: {EmailTemplates.PRIMARY_TEXT}; text-decoration: none;
                        border-radius: 8px; background-color: {EmailTemplates.PRIMARY_COLOR};">{_e(label)}</a>
            </td>
          </tr>
        </table>
        """

    # ------------------------------------------------------------------ layout

    @staticmethod
    def _base_template(content: str, preheader: str = "") -> str:
        T = EmailTemplates
        site = _frontend_url()
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <title>{T.BUSINESS_NAME}</title>
    <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: 'Poppins', 'Segoe UI', Arial, sans-serif;
            background-color: #f4f1e6;
            -webkit-font-smoothing: antialiased;
        }}
        .email-container {{
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
        }}
        .header {{
            background-color: {T.DARK_BG};
            padding: 32px 20px;
            text-align: center;
            border-bottom: 4px solid {T.PRIMARY_COLOR};
        }}
        .header h1 {{
            color: {T.DARK_BG_TEXT};
            margin: 0;
            font-size: 28px;
            font-weight: 700;
            letter-spacing: 0.5px;
        }}
        .header .tagline {{
            color: #cfc7ad;
            margin: 8px 0 0 0;
            font-size: 14px;
        }}
        .content {{
            padding: 36px 30px;
            color: {T.DARK_COLOR};
            line-height: 1.6;
        }}
        .content h2 {{
            color: {T.DARK_COLOR};
            font-size: 22px;
            margin-top: 0;
            margin-bottom: 18px;
        }}
        .content p {{
            margin: 14px 0;
            font-size: 15px;
        }}
        .order-summary {{
            background-color: {T.LIGHT_COLOR};
            border: 1px solid {T.BORDER_COLOR};
            border-radius: 10px;
            padding: 22px;
            margin: 22px 0;
        }}
        .order-item {{
            padding: 12px 0;
            border-bottom: 1px solid {T.BORDER_COLOR};
        }}
        .order-item:last-child {{
            border-bottom: none;
        }}
        .order-item-name {{
            font-weight: 600;
            font-size: 15px;
        }}
        .order-item-details {{
            color: {T.MUTED_TEXT};
            font-size: 14px;
            margin-top: 4px;
        }}
        .total-table {{
            width: 100%;
            margin-top: 16px;
            font-size: 15px;
        }}
        .total-table td {{
            padding: 6px 0;
        }}
        .grand-total td {{
            font-weight: 700;
            font-size: 18px;
            border-top: 2px solid {T.PRIMARY_COLOR};
            padding-top: 12px;
        }}
        .info-box {{
            background-color: {T.WARM_COLOR};
            border-left: 4px solid {T.PRIMARY_COLOR};
            padding: 14px 18px;
            margin: 20px 0;
            border-radius: 6px;
            font-size: 15px;
        }}
        .status-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .status-pending {{ background-color: #FDEAAD; color: #6b5200; }}
        .status-paid {{ background-color: #E3F2F1; color: #0F6E6E; }}
        .status-processing {{ background-color: #E3F2F1; color: #0F6E6E; }}
        .status-shipped {{ background-color: #EAF3E5; color: #4C7A3D; }}
        .status-delivered {{ background-color: #EAF3E5; color: #4C7A3D; }}
        .status-cancelled {{ background-color: #FBE8E0; color: #D66A3B; }}
        .divider {{
            height: 1px;
            background-color: {T.BORDER_COLOR};
            margin: 28px 0;
        }}
        .small {{
            color: {T.MUTED_TEXT};
            font-size: 14px;
        }}
        .footer {{
            background-color: {T.DARK_BG};
            color: #cfc7ad;
            padding: 28px 20px;
            text-align: center;
            font-size: 13px;
            line-height: 1.7;
        }}
        .footer strong {{
            color: {T.DARK_BG_TEXT};
            font-size: 15px;
        }}
        .footer a {{
            color: {T.DARK_BG_TEXT};
            text-decoration: none;
        }}
        @media only screen and (max-width: 600px) {{
            .content {{ padding: 28px 18px; }}
            .header h1 {{ font-size: 24px; }}
        }}
    </style>
</head>
<body>
    <div style="display: none; max-height: 0; overflow: hidden;">{_e(preheader)}</div>
    <div class="email-container">
        <div class="header">
            <h1>{T.BUSINESS_NAME}</h1>
            <p class="tagline">{T.TAGLINE}</p>
        </div>
        {content}
        <div class="footer">
            <p><strong>Pedni Honey Apiaries Limited</strong></p>
            <p>Pure honey, beekeeping equipment, training and support.</p>
            <p>
                Phone: <a href="tel:+254704089414">{T.CONTACT_PHONE}</a> &nbsp;|&nbsp;
                Email: <a href="mailto:{T.CONTACT_EMAIL}">{T.CONTACT_EMAIL}</a><br>
                {T.POSTAL_ADDRESS}<br>
                <a href="{site}">Visit our shop</a>
            </p>
            <p style="font-size: 12px; color: #9c947c; margin-top: 16px;">
                If you have any questions, simply reply to this email.<br>
                &copy; 2026 Pedni Honey Apiaries Limited. All rights reserved.
            </p>
        </div>
    </div>
</body>
</html>
        """

    # ------------------------------------------------------------------ shared pieces

    @staticmethod
    def _items_html(items: List[Dict], with_prices: bool = True) -> str:
        html = ""
        for item in items or []:
            name = _e(item.get("productName"))
            qty = item.get("quantity", 0)
            if with_prices:
                price = item.get("price", 0)
                details = f"Quantity: {qty} x KES {price:,.2f} = KES {qty * price:,.2f}"
            else:
                details = f"Quantity: {qty}"
            html += f"""
            <div class="order-item">
                <div class="order-item-name">{name}</div>
                <div class="order-item-details">{details}</div>
            </div>
            """
        return html

    @staticmethod
    def _totals_html(subtotal: float, shipping: float, total: float) -> str:
        return f"""
        <table class="total-table" role="presentation" cellpadding="0" cellspacing="0">
            <tr><td>Subtotal</td><td align="right">KES {subtotal:,.2f}</td></tr>
            <tr><td>Delivery</td><td align="right">KES {shipping:,.2f}</td></tr>
            <tr class="grand-total"><td>Total</td><td align="right">KES {total:,.2f}</td></tr>
        </table>
        """

    @staticmethod
    def _payment_display(payment_method: str) -> str:
        return {"mpesa": "M-Pesa", "cash": "Cash on Delivery"}.get(
            str(payment_method).lower(), str(payment_method).replace("_", " ").title()
        )

    # ------------------------------------------------------------------ customer emails

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
        county: str,
        email: Optional[str] = None,
    ) -> str:
        T = EmailTemplates
        content = f"""
        <div class="content">
            <h2>Order Confirmed</h2>
            <p>Hi <strong>{_e(customer_name)}</strong>,</p>
            <p>Thank you for your order. We have received it and will prepare your items for delivery.</p>

            <div class="info-box">
                <strong>Order ID:</strong> {_e(order_id)}<br>
                <strong>Order Date:</strong> {_e(order_date)}<br>
                <strong>Status:</strong> <span class="status-badge status-paid">Paid</span>
            </div>

            <h3 style="margin-top: 28px;">Order Summary</h3>
            <div class="order-summary">
                {T._items_html(items)}
                {T._totals_html(subtotal, shipping, total)}
            </div>

            <h3 style="margin-top: 28px;">Delivery Information</h3>
            <div class="info-box">
                <strong>Address:</strong> {_e(address)}<br>
                {('<strong>City:</strong> ' + _e(city) + '<br>') if city and city != county else ''}
                <strong>County:</strong> {_e(county)}<br>
                <strong>Payment Method:</strong> {T._payment_display(payment_method)}
            </div>

            {T.button("Track Your Order", T.track_order_url(order_id, email))}

            {T.account_invite(email)}

            <div class="divider"></div>

            <p class="small">
                <strong>What happens next?</strong><br>
                We will email you each time your order status changes. You can also check it any time
                with the Track Your Order button above, using your order ID and email address.
            </p>
        </div>
        """
        preheader = f"Your order {order_id} has been confirmed. Thank you for shopping with Pedni Honey."
        return T._base_template(content, preheader)

    @staticmethod
    def order_status_update(
        customer_name: str,
        order_id: str,
        status: str,
        items: List[Dict],
        total: float,
        message: Optional[str] = None,
        email: Optional[str] = None,
    ) -> str:
        T = EmailTemplates
        status_messages = {
            "pending": ("Order Received", "We have received your order and it is waiting to be processed."),
            "paid": ("Payment Confirmed", "Your payment has been received. We are now preparing your order."),
            "processing": ("Order Being Prepared", "We are carefully preparing your items for delivery."),
            "shipped": ("Order On Its Way", "Your order has left our store and is on its way to you."),
            "delivered": ("Order Delivered", "Your order has been delivered. We hope you enjoy your products."),
            "cancelled": ("Order Cancelled",
                          "Your order has been cancelled. If you did not request this, please contact us right away."),
        }
        key = str(status).lower()
        title, text = status_messages.get(key, ("Order Status Update", f"Your order status is now {_e(status)}."))

        extra = ""
        if message and message.strip() and message.strip() != "Your order status has been updated.":
            extra = f"<p>{_e(message)}</p>"

        content = f"""
        <div class="content">
            <h2>{title}</h2>
            <p>Hi <strong>{_e(customer_name)}</strong>,</p>
            <p>{text}</p>
            {extra}

            <div class="info-box">
                <strong>Order ID:</strong> {_e(order_id)}<br>
                <strong>Status:</strong> <span class="status-badge status-{_e(key)}">{_e(key)}</span>
            </div>

            <h3 style="margin-top: 28px;">Order Items</h3>
            <div class="order-summary">
                {T._items_html(items, with_prices=False)}
                <table class="total-table" role="presentation" cellpadding="0" cellspacing="0">
                    <tr class="grand-total"><td>Total</td><td align="right">KES {total:,.2f}</td></tr>
                </table>
            </div>

            {T.button("Track Your Order", T.track_order_url(order_id, email))}

            <div class="divider"></div>

            <p class="small">Need help? Reply to this email or call us on {T.CONTACT_PHONE}.</p>
        </div>
        """
        preheader = f"Order {order_id}: {title}"
        return T._base_template(content, preheader)

    @staticmethod
    def newsletter_subscription(email: str) -> str:
        T = EmailTemplates
        site = _frontend_url()
        unsubscribe = f"{site}/unsubscribe?{urlencode({'email': email})}"
        content = f"""
        <div class="content">
            <h2>Welcome to the Pedni Honey Newsletter</h2>
            <p>Hi there,</p>
            <p>Thank you for subscribing. We are glad to have you in our community of honey lovers and beekeepers.</p>

            <div class="info-box">
                <strong>What to expect:</strong><br>
                &bull; Offers and early access to new products<br>
                &bull; Practical beekeeping tips<br>
                &bull; News from our apiaries and honey harvests<br>
                &bull; Training dates and special events
            </div>

            {T.button("Shop Now", f"{site}/products")}

            <div class="divider"></div>

            <p class="small">
                <strong>Subscribed email:</strong> {_e(email)}<br>
                You can <a href="{_e(unsubscribe)}" style="color: {T.TEAL};">unsubscribe</a> at any time.
            </p>
        </div>
        """
        preheader = "Welcome to Pedni Honey. Offers, beekeeping tips and news from our apiaries."
        return T._base_template(content, preheader)

    @staticmethod
    def newsletter_unsubscription(email: str) -> str:
        T = EmailTemplates
        resubscribe = f"{_frontend_url()}/newsletter/resubscribe?{urlencode({'email': email})}"
        content = f"""
        <div class="content">
            <h2>You Have Been Unsubscribed</h2>
            <p>Hi there,</p>
            <p>You have been unsubscribed from the Pedni Honey newsletter.</p>

            <div class="info-box">
                <strong>Unsubscribed email:</strong> {_e(email)}<br>
                You will no longer receive our newsletter.
            </div>

            <p>If you change your mind, you are always welcome back.</p>

            {T.button("Resubscribe", resubscribe)}

            <div class="divider"></div>

            <p class="small">
                You will still receive emails about any orders you place with us.
                If you unsubscribed by mistake, use the button above or reply to this email.
            </p>
        </div>
        """
        preheader = "You have been unsubscribed from the Pedni Honey newsletter."
        return T._base_template(content, preheader)

    @staticmethod
    def password_reset_otp(customer_name: str, otp: str, expires_in_minutes: int) -> str:
        T = EmailTemplates
        content = f"""
        <div class="content">
            <h2>Password Reset Request</h2>
            <p>Hi {_e(customer_name)},</p>
            <p>We received a request to reset the password for your Pedni Honey account. Your one-time code is:</p>

            <div style="text-align: center; margin: 30px 0;">
                <div style="display: inline-block; padding: 15px 30px; font-size: 26px; font-weight: bold;
                            letter-spacing: 6px; color: {T.DARK_COLOR}; background-color: {T.LIGHT_COLOR};
                            border: 2px dashed {T.PRIMARY_COLOR}; border-radius: 10px;">
                    {_e(otp)}
                </div>
            </div>

            <p>This code will expire in {expires_in_minutes} minutes.</p>

            <div style="margin-top: 28px; padding: 15px; background-color: #FBE8E0;
                        border-left: 4px solid {T.WARNING_COLOR}; border-radius: 6px;">
                <strong>Did not request this?</strong> You can safely ignore this email. Your account is still secure.
            </div>
        </div>
        """
        preheader = "Your Pedni Honey password reset code."
        return T._base_template(content, preheader)

    # ------------------------------------------------------------------ admin emails

    @staticmethod
    def admin_order_notification(
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
        county: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
    ) -> str:
        T = EmailTemplates
        contact = ""
        if email:
            contact += f"<strong>Email:</strong> {_e(email)}<br>"
        if phone:
            contact += f"<strong>Phone:</strong> {_e(phone)}<br>"

        content = f"""
        <div class="content">
            <h2>New Order Received</h2>
            <p>A new order has been placed by <strong>{_e(customer_name)}</strong>.</p>

            <div class="info-box">
                <strong>Order ID:</strong> {_e(order_id)}<br>
                <strong>Order Date:</strong> {_e(order_date)}<br>
                <strong>Status:</strong> <span class="status-badge status-paid">Paid</span>
            </div>

            <h3 style="margin-top: 28px;">Order Summary</h3>
            <div class="order-summary">
                {T._items_html(items)}
                {T._totals_html(subtotal, shipping, total)}
            </div>

            <h3 style="margin-top: 28px;">Customer Details</h3>
            <div class="info-box">
                <strong>Name:</strong> {_e(customer_name)}<br>
                {contact}
                <strong>Address:</strong> {_e(address)}<br>
                {('<strong>City:</strong> ' + _e(city) + '<br>') if city and city != county else ''}
                <strong>County:</strong> {_e(county)}<br>
                <strong>Payment Method:</strong> {T._payment_display(payment_method)}
            </div>

            {T.button("View Order in Dashboard", T.admin_orders_url(order_id))}

            <div class="divider"></div>

            <p class="small">Please process this order promptly.</p>
        </div>
        """
        preheader = f"New order {order_id} received from {customer_name}."
        return T._base_template(content, preheader)

    # ------------------------------------------------------------------ contact page requests

    @staticmethod
    def _request_details_html(req) -> str:
        """Rows for every detail the customer filled in."""
        fields = [
            ("Request type", "reason"),
            ("Training type", "training_type"),
            ("Participants", "participants"),
            ("Preferred date", "preferred_date"),
            ("Location", "location"),
            ("Products", "products"),
            ("Quantity", "quantity"),
            ("Subject", "subject"),
        ]
        rows = ""
        for label, attr in fields:
            value = getattr(req, attr, None)
            if value not in (None, ""):
                rows += f"<strong>{label}:</strong> {_e(value)}<br>"
        return rows

    @staticmethod
    def admin_request_notification(req) -> str:
        T = EmailTemplates
        url = f"{_frontend_url()}/admin/training-requests?{urlencode({'requestId': str(getattr(req, 'id', ''))})}"
        contact = f"<strong>Email:</strong> {_e(req.email)}<br>"
        if getattr(req, "phone", None):
            contact += f"<strong>Phone:</strong> {_e(req.phone)}<br>"
        content = f"""
        <div class="content">
            <h2>New {_e(req.reason)}</h2>
            <p>A new request has been submitted through the Contact page by <strong>{_e(req.name)}</strong>.</p>

            <div class="info-box">
                {('<strong>Reference:</strong> ' + _e(req.reference) + '<br>') if getattr(req, 'reference', None) else ''}
                <strong>Name:</strong> {_e(req.name)}<br>
                {contact}
            </div>

            <h3 style="margin-top: 28px;">Request Details</h3>
            <div class="order-summary">
                {T._request_details_html(req)}
                <div style="margin-top: 14px;"><strong>Message:</strong></div>
                <div style="white-space: pre-line; margin-top: 6px;">{_e(req.message)}</div>
            </div>

            {T.button("Open Request in Dashboard", url)}

            <div class="divider"></div>
            <p class="small">Reply to the customer at {_e(req.email)} or update the request status in your dashboard.</p>
        </div>
        """
        return T._base_template(content, f"New {req.reason} from {req.name}.")

    @staticmethod
    def request_received(req) -> str:
        T = EmailTemplates
        content = f"""
        <div class="content">
            <h2>We Have Received Your Request</h2>
            <p>Hi <strong>{_e(req.name)}</strong>,</p>
            <p>Thank you for contacting Pedni Honey. We have received your request and a member of our team
               will get back to you shortly, usually within one working day.</p>

            {('<div class="info-box"><strong>Your reference: ' + _e(req.reference) + '</strong><br>Please quote it if you call or email us about this request.</div>') if getattr(req, 'reference', None) else ''}

            <h3 style="margin-top: 28px;">Your Request</h3>
            <div class="order-summary">
                {T._request_details_html(req)}
                <div style="margin-top: 14px;"><strong>Your message:</strong></div>
                <div style="white-space: pre-line; margin-top: 6px;">{_e(req.message)}</div>
            </div>

            <p>If you need us sooner, call us on <strong>{T.CONTACT_PHONE}</strong>
               (Monday to Saturday, 8:00 AM to 6:00 PM).</p>

            {T.button("Visit Our Shop", f"{_frontend_url()}/products")}
        </div>
        """
        return T._base_template(content, "Thank you for contacting Pedni Honey. We will get back to you shortly.")
