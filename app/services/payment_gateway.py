"""
Chooses which company sends the M-Pesa prompt (STK push).

In ~/honeyBackend/.env :
    PAYMENT_PROVIDER=paystack     (default)  -> Paystack, needs PAYSTACK_SECRET_KEY
    PAYMENT_PROVIDER=payhero                 -> Pay Hero, needs the PAYHERO_* settings

The checkout page does not change: it always calls /orders/{id}/pay and
/orders/{id}/payment-status.
"""
import os

from app.services import payhero_service, paystack_service


class GatewayError(Exception):
    """The payment company could not send the prompt or check the payment."""


def provider() -> str:
    name = (os.getenv("PAYMENT_PROVIDER") or "paystack").strip().lower().replace(" ", "").replace("_", "")
    return "payhero" if name == "payhero" else "paystack"


def start(order) -> dict:
    """Send the M-Pesa PIN prompt for this order."""
    phone = order.mpesa_phone or order.phone
    try:
        if provider() == "payhero":
            return payhero_service.initiate_stk_push(
                order_id=order.id,
                amount=order.total,
                phone=phone,
                customer_name=order.customer_name,
            )
        return paystack_service.initiate_stk_push(
            order_id=order.id,
            amount=order.total,
            phone=phone,
            email=order.email,
            customer_name=order.customer_name,
        )
    except (payhero_service.PayHeroError, paystack_service.PaymentError) as e:
        raise GatewayError(str(e))


def get_payment(order_id: str) -> dict | None:
    service = payhero_service if provider() == "payhero" else paystack_service
    return service.get_payment(order_id)


def refresh(db, order) -> None:
    """Ask the payment company whether a pending order has been paid, and record it."""
    if order.status != "pending":
        return
    try:
        if provider() == "paystack":
            paystack_service.check_and_apply(db, order.id)
            return
        info = payhero_service.get_payment(order.id) or {}
        if info.get("state") == "waiting" and info.get("reference"):
            state, receipt, message = payhero_service.check_transaction_status(info["reference"])
            if state != "waiting":
                payhero_service.apply_payment_result(
                    db, order.id, ok=(state == "paid"), receipt=receipt, message=message
                )
    except Exception as e:  # never break the status check page
        print(f"[Payments] Status check failed for {order.id}: {e}")
