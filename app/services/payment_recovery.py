"""
Admin help for "I paid but got no email" calls.

check_payment(db, order_id)
    Asks Paystack directly whether this order was paid - even if the customer
    closed the checkout page, the backend restarted, or the order was
    auto-cancelled. If Paystack confirms a successful payment for the right
    amount, the order is marked Paid (re-opened if it had been cancelled), the
    M-Pesa code is saved, and the customer gets the confirmation email with
    the PDF receipt.

resend_confirmation(db, order_id, new_email=None)
    Sends the confirmation email (with PDF receipt) again, optionally to a
    corrected email address.
"""
import json
import urllib.parse
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException

from app.models.order import Order
from app.services import paystack_service, payment_gateway
from app.services.order_service import OrderService

PAID_STATUSES = ("paid", "processing", "shipped", "delivered")


def _order(db, order_id: str) -> Order:
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


def _metadata(tx: dict) -> dict:
    meta = tx.get("metadata")
    if isinstance(meta, str):
        try:
            meta = json.loads(meta)
        except ValueError:
            meta = {}
    return meta if isinstance(meta, dict) else {}


def _belongs_to(tx: dict, order_id: str) -> bool:
    ref = str(tx.get("reference") or "")
    return ref.startswith(order_id + "-") or _metadata(tx).get("order_id") == order_id


def _iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def _paystack_attempts(order: Order) -> list:
    """All Paystack transactions for this order (newest first)."""
    created = order.created_at or datetime.utcnow()
    start = _iso(created - timedelta(days=1))
    end = _iso(created + timedelta(days=4))
    found = []
    for page in range(1, 6):  # up to 500 transactions around the order date
        query = urllib.parse.urlencode({"perPage": 100, "page": page, "from": start, "to": end})
        res = paystack_service._request("GET", "transaction?" + query)
        rows = res.get("data") if isinstance(res, dict) else None
        if not isinstance(rows, list) or not rows:
            break
        found += [tx for tx in rows if isinstance(tx, dict) and _belongs_to(tx, order.id)]
        if len(rows) < 100:
            break
    # The reference remembered by the running backend (if any) is checked too
    remembered = (paystack_service.get_payment(order.id) or {}).get("reference")
    if remembered and not any(tx.get("reference") == remembered for tx in found):
        found.append({"reference": remembered, "status": "unknown"})
    return found


def _mark_paid(db, order: Order, receipt: str | None) -> str:
    """Record the payment. Re-opens a cancelled order (taking the stock out again)."""
    service = OrderService(db)
    previous = str(order.status or "").lower()
    if previous == "cancelled":
        service._change_stock(order, -1)  # raises 400 if the stock has run out
    order.status = "paid"
    if receipt:
        order.mpesa_transaction_id = receipt
    db.commit()
    db.refresh(order)
    # Customer confirmation + PDF receipt, admin email and bell notification
    service._announce_new_order(order)
    paystack_service._set_payment(order.id, state="paid", message="Payment received. Thank you!")
    return previous


def check_payment(db, order_id: str) -> dict:
    order = _order(db, order_id)

    if payment_gateway.provider() != "paystack":
        raise HTTPException(status_code=400,
                            detail="This check only works with Paystack (PAYMENT_PROVIDER in .env).")
    if order.payment_method != "mpesa":
        raise HTTPException(status_code=400, detail="This order was not paid with M-Pesa.")

    try:
        attempts = _paystack_attempts(order)
    except paystack_service.PaymentError as e:
        raise HTTPException(status_code=502, detail=f"Could not check with Paystack: {e}")

    if not attempts:
        return {
            "result": "not_found",
            "message": "Paystack has no payment attempt for this order. The customer's money did not "
                       "reach your Paystack account through this order. Ask for the M-Pesa SMS - she may "
                       "have paid to a different number or till.",
        }

    # Confirm each attempt directly with Paystack (never trust the list alone)
    confirmed = None
    last_problem = None
    for tx in attempts:
        try:
            result = paystack_service.verify(tx["reference"])
        except paystack_service.PaymentError as e:
            last_problem = str(e)
            continue
        if result["state"] == "paid":
            confirmed = result
            break
        last_problem = result.get("message") or result["state"]

    if not confirmed:
        return {
            "result": "not_paid",
            "message": f"Paystack shows {len(attempts)} payment attempt(s) for this order, but none was "
                       f"successful (last: {last_problem or 'not completed'}). The customer was not charged "
                       "through this order.",
        }

    receipt = confirmed.get("receipt")
    expected = int(order.total) * 100
    if confirmed.get("amount") is not None and int(confirmed["amount"]) != expected:
        return {
            "result": "amount_mismatch",
            "message": f"Paystack shows a successful payment of KSh {int(confirmed['amount']) // 100:,} "
                       f"(code {receipt}), but the order total is KSh {int(order.total):,}. "
                       "The order was NOT marked paid - please sort this out with the customer.",
            "receipt": receipt,
        }
    if confirmed.get("currency") and str(confirmed["currency"]).upper() != "KES":
        return {"result": "amount_mismatch",
                "message": f"Paystack shows a payment in {confirmed['currency']}, not KES. Not marked paid."}

    status = str(order.status or "").lower()
    if status in PAID_STATUSES:
        if receipt and not order.mpesa_transaction_id:
            order.mpesa_transaction_id = receipt
            db.commit()
        return {
            "result": "already_paid",
            "message": f"Confirmed: Paystack received this payment (M-Pesa code {receipt}). The order is "
                       f"already marked {status}. If the customer has no email, use Resend email below.",
            "receipt": receipt,
        }

    try:
        previous = _mark_paid(db, order, receipt)
    except HTTPException as e:
        db.rollback()
        return {
            "result": "paid_no_stock",
            "message": f"Paystack confirms the customer PAID (M-Pesa code {receipt}), but the order could "
                       f"not be re-opened: {e.detail}. Contact the customer to agree a replacement or "
                       "refund her through Paystack.",
            "receipt": receipt,
        }

    reopened = " It had been cancelled, so it was re-opened and the stock taken out again." \
        if previous == "cancelled" else ""
    print(f"[Payments] Admin check: order {order.id} confirmed PAID by Paystack ({receipt}), was {previous}")
    return {
        "result": "marked_paid",
        "message": f"Payment confirmed by Paystack (M-Pesa code {receipt}). The order is now marked Paid."
                   f"{reopened} The customer has been sent her confirmation email with the receipt.",
        "receipt": receipt,
    }


def resend_confirmation(db, order_id: str, new_email: str | None = None) -> dict:
    order = _order(db, order_id)
    status = str(order.status or "").lower()
    if status not in PAID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail="This order is not paid, so there is no confirmation to send. "
                   "Use 'Check payment with Paystack' first.",
        )

    changed = ""
    if new_email and new_email.strip().lower() != (order.email or "").strip().lower():
        old = order.email
        order.email = new_email.strip()
        db.commit()
        db.refresh(order)
        changed = f" Email changed from {old}."
        print(f"[Orders] Admin changed email on {order.id}: {old} -> {order.email}")

    # Same email the customer gets when she pays (with the PDF receipt), but we
    # need to know whether it actually went out.
    from app.services.email_templates import EmailTemplates
    service = OrderService(db)
    html_body = EmailTemplates.order_confirmation(
        email=order.email, customer_name=order.customer_name, order_id=order.id,
        order_date=str(order.order_date), items=order.items, subtotal=order.subtotal,
        shipping=order.shipping, total=order.total, payment_method=order.payment_method,
        address=order.address, city=order.city, county=order.county,
    )
    subject = f"Order Confirmation - {order.id}"
    attachments = []
    try:
        from app.services.receipt_pdf import build_receipt, receipt_number
        attachments.append((f"Pedni-Honey-Receipt-{receipt_number(order.id)}.pdf", build_receipt(order), "pdf"))
        subject = f"Payment Receipt & Order Confirmation - {order.id}"
    except Exception as e:
        print(f"[Receipts] Could not create receipt for {order.id}: {e}")

    sent = service.email_service.send_html_email(order.email, subject, html_body, attachments=attachments)
    if not sent:
        raise HTTPException(
            status_code=502,
            detail="The email could not be sent (check the email settings and the backend log).",
        )
    receipt_note = " with the PDF receipt" if attachments else ""
    return {
        "result": "sent",
        "email": order.email,
        "message": f"Confirmation email{receipt_note} sent to {order.email}.{changed} "
                   "Ask the customer to also check her Spam and Promotions folders.",
    }
