"""
Paystack M-Pesa STK push integration (Kenya).

Settings in ~/honeyBackend/.env :
    PAYSTACK_SECRET_KEY   sk_test_... while testing, sk_live_... for real payments
                          (Paystack dashboard -> Settings -> API Keys & Webhooks)

Webhook (optional locally, needed when live):
    In the Paystack dashboard set the Webhook URL to
    https://<your-backend-address>/v1/webhooks/paystack
"""
import hashlib
import hmac
import json
import os
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("PAYSTACK_BASE_URL", "https://api.paystack.co")

# Payment attempts we are waiting on: order_id -> {reference, state, message, started}
PAYMENTS = {}
_lock = threading.Lock()

FAILED_STATES = {"failed", "reversed"}


class PaymentError(Exception):
    """Raised when Paystack cannot be reached or rejects a request."""


# --------------------------------------------------------------------------- helpers

def _secret_key() -> str:
    key = (os.getenv("PAYSTACK_SECRET_KEY") or "").strip()
    if not key:
        raise PaymentError("PAYSTACK_SECRET_KEY is not set in .env")
    return key


def _request(method: str, path: str, body: dict | None = None) -> dict:
    url = BASE_URL.rstrip("/") + "/" + path.lstrip("/")
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {_secret_key()}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "PedniHoney/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            text = resp.read().decode(errors="replace")
    except urllib.error.HTTPError as e:
        text = e.read().decode(errors="replace")
        print(f"[Paystack] {method} {path} -> HTTP {e.code}: {text[:500]}")
        raise PaymentError(_message(text) or f"Paystack returned HTTP {e.code}")
    except urllib.error.URLError as e:
        raise PaymentError(f"Could not reach Paystack: {e.reason}")

    print(f"[Paystack] {method} {path} -> {text[:500]}")
    try:
        return json.loads(text)
    except ValueError:
        raise PaymentError("Unexpected response from Paystack")


def _message(text: str) -> str | None:
    try:
        obj = json.loads(text)
    except ValueError:
        return None
    if isinstance(obj, dict):
        data = obj.get("data") if isinstance(obj.get("data"), dict) else {}
        for value in (data.get("message"), data.get("gateway_response"), obj.get("message")):
            if isinstance(value, str) and value:
                return value
    return None


def normalize_phone(phone: str) -> str:
    """'0712345678' / '712345678' / '254712345678' -> '+254712345678'."""
    digits = "".join(ch for ch in str(phone) if ch.isdigit())
    if digits.startswith("254"):
        digits = digits[3:]
    elif digits.startswith("0"):
        digits = digits[1:]
    return "+254" + digits


def order_id_from_reference(reference: str | None) -> str | None:
    """References look like ORD-ABC12345-1728720000 -> ORD-ABC12345."""
    if not reference or "-" not in reference:
        return None
    head, tail = reference.rsplit("-", 1)
    return head if tail.isdigit() else None


def get_payment(order_id: str) -> dict | None:
    with _lock:
        info = PAYMENTS.get(order_id)
        return dict(info) if info else None


def _set_payment(order_id: str, **fields) -> dict:
    with _lock:
        info = PAYMENTS.setdefault(order_id, {})
        info.update(fields)
        return dict(info)


# --------------------------------------------------------------------------- API calls

def initiate_stk_push(order_id: str, amount: int, phone: str, email: str,
                      customer_name: str | None = None) -> dict:
    """Ask Paystack to send an M-Pesa PIN prompt to the customer's phone."""
    existing = get_payment(order_id)
    if existing and existing.get("state") == "waiting" and time.time() - existing.get("started", 0) < 20:
        return existing  # a prompt was just sent; don't send another straight away

    reference = f"{order_id}-{int(time.time())}"  # Paystack needs a new reference per attempt
    body = {
        "email": email,
        "amount": int(amount) * 100,  # KES -> cents
        "currency": "KES",
        "reference": reference,
        "mobile_money": {"phone": normalize_phone(phone), "provider": "mpesa"},
        "metadata": {"order_id": order_id, "customer_name": customer_name or ""},
    }
    res = _request("POST", "charge", body)

    data = res.get("data") if isinstance(res, dict) and isinstance(res.get("data"), dict) else {}
    status = str(data.get("status") or "").lower()

    if res.get("status") is False or status in FAILED_STATES:
        raise PaymentError(_message(json.dumps(res)) or "Paystack could not send the M-Pesa prompt")

    if status == "success":  # can happen instantly in test mode
        return _set_payment(order_id, reference=data.get("reference") or reference,
                            state="paid_pending_record", started=time.time(),
                            message="Payment received.")

    return _set_payment(
        order_id,
        reference=data.get("reference") or reference,
        state="waiting",
        message=data.get("display_text")
        or "Check your phone and enter your M-Pesa PIN to complete the payment.",
        started=time.time(),
    )


def verify(reference: str) -> dict:
    """Ask Paystack for the final state of a transaction."""
    res = _request("GET", "transaction/verify/" + urllib.parse.quote(reference, safe=""))
    data = res.get("data") if isinstance(res, dict) and isinstance(res.get("data"), dict) else {}
    status = str(data.get("status") or "").lower()
    if status == "success":
        state = "paid"
    elif status in FAILED_STATES:
        state = "failed"
    else:
        state = "waiting"
    return {
        "state": state,
        "amount": data.get("amount"),  # in cents
        "currency": data.get("currency"),
        "receipt": data.get("receipt_number") or data.get("reference"),
        "message": data.get("gateway_response") or data.get("message"),
        "reference": data.get("reference") or reference,
        "order_id": (data.get("metadata") or {}).get("order_id") if isinstance(data.get("metadata"), dict)
        else None,
    }


def valid_signature(raw_body: bytes, signature: str | None) -> bool:
    """Paystack signs webhooks with HMAC-SHA512 of the raw body using the secret key."""
    if not signature:
        return False
    try:
        key = _secret_key().encode()
    except PaymentError:
        return False
    expected = hmac.new(key, raw_body, hashlib.sha512).hexdigest()
    return hmac.compare_digest(expected, signature)


# --------------------------------------------------------------------------- applying results

def apply_verified_result(db, order_id: str, result: dict) -> None:
    """Update the order from a verify() result (only trusted, verified data)."""
    from app.models.order import Order
    from app.services.order_service import OrderService

    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        print(f"[Paystack] Result for unknown order {order_id} - ignored")
        return

    if result["state"] == "waiting":
        return

    if result["state"] == "failed":
        if order.status == "pending":
            _set_payment(order_id, state="failed",
                         message=result.get("message") or "The payment was not completed. You can try again.")
        print(f"[Paystack] Payment FAILED for {order_id}: {result.get('message')}")
        return

    # paid
    if order.status != "pending":
        _set_payment(order_id, state="paid")
        return

    expected = int(order.total) * 100
    if result.get("amount") is not None and int(result["amount"]) != expected:
        print(f"[Paystack] Amount mismatch for {order_id}: paid {result['amount']} cents, expected {expected} - NOT marked paid")
        _set_payment(order_id, state="failed",
                     message="The amount paid did not match the order total. Please contact us.")
        return
    if result.get("currency") and str(result["currency"]).upper() != "KES":
        print(f"[Paystack] Currency mismatch for {order_id}: {result['currency']} - NOT marked paid")
        return

    receipt = result.get("receipt")
    OrderService(db).update_order_status(order_id, "paid", receipt)
    _set_payment(order_id, state="paid", message="Payment received. Thank you!")
    print(f"[Paystack] Order {order_id} marked PAID (ref {receipt})")


def check_and_apply(db, order_id: str) -> None:
    """Used by the checkout page's status checks: verify with Paystack and update."""
    info = get_payment(order_id) or {}
    reference = info.get("reference")
    if not reference or info.get("state") not in ("waiting", "paid_pending_record"):
        return
    result = verify(reference)
    apply_verified_result(db, order_id, result)
