"""
Pay Hero (payhero.co.ke) M-Pesa STK push integration.

Settings come from ~/honeyBackend/.env :
    PAYHERO_API_USERNAME      API username from Pay Hero -> API Keys
    PAYHERO_API_PASSWORD      API password from Pay Hero -> API Keys
      (or PAYHERO_BASIC_AUTH_TOKEN instead of the two above)
    PAYHERO_CHANNEL_ID        Channel ID of your Till/Paybill (Pay Hero -> Payment Channels)
    PAYHERO_CALLBACK_SECRET   Random secret so only Pay Hero can call our callback
    PUBLIC_BACKEND_URL        Public address of this backend, e.g. https://xxxx.ngrok-free.app
                              (optional locally: payment status is also checked by polling)
"""
import base64
import json
import os
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("PAYHERO_BASE_URL", "https://backend.payhero.co.ke/api/v2/")

# Payment attempts we are waiting on: order_id -> {reference, state, message, started}
# Kept in memory (fine for a single backend process). If the backend restarts,
# a paid order is still marked paid by the callback.
PAYMENTS = {}
_lock = threading.Lock()

PAID_STATES = {"SUCCESS", "SUCCESSFUL", "COMPLETED", "PAID"}
FAILED_STATES = {"FAILED", "FAILURE", "CANCELLED", "CANCELED", "TIMEOUT", "REVERSED", "EXPIRED"}


class PayHeroError(Exception):
    """Raised when Pay Hero cannot be reached or rejects a request."""


# --------------------------------------------------------------------------- helpers

def _auth_header() -> str:
    token = (os.getenv("PAYHERO_BASIC_AUTH_TOKEN") or "").strip()
    if token:
        return token if token.lower().startswith("basic ") else f"Basic {token}"
    user = os.getenv("PAYHERO_API_USERNAME")
    password = os.getenv("PAYHERO_API_PASSWORD")
    if not user or not password:
        raise PayHeroError("Pay Hero API credentials are not set in .env")
    return "Basic " + base64.b64encode(f"{user}:{password}".encode()).decode()


def _request(method: str, path: str, body: dict | None = None) -> dict:
    url = BASE_URL.rstrip("/") + "/" + path.lstrip("/")
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": _auth_header(),
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            text = resp.read().decode(errors="replace")
    except urllib.error.HTTPError as e:
        text = e.read().decode(errors="replace")
        print(f"[PayHero] {method} {path} -> HTTP {e.code}: {text[:500]}")
        message = _error_message(text) or f"Pay Hero returned HTTP {e.code}"
        raise PayHeroError(message)
    except urllib.error.URLError as e:
        raise PayHeroError(f"Could not reach Pay Hero: {e.reason}")

    print(f"[PayHero] {method} {path} -> {text[:500]}")
    try:
        return json.loads(text)
    except ValueError:
        raise PayHeroError("Unexpected response from Pay Hero")


def _error_message(text: str) -> str | None:
    try:
        obj = json.loads(text)
    except ValueError:
        return None
    if isinstance(obj, dict):
        for key in ("error_message", "message", "detail", "error"):
            if isinstance(obj.get(key), str):
                return obj[key]
    return None


def normalize_phone(phone: str) -> str:
    """'+254712345678' / '0712345678' / '712345678' -> '254712345678'."""
    digits = "".join(ch for ch in str(phone) if ch.isdigit())
    if digits.startswith("254"):
        return digits
    if digits.startswith("0"):
        return "254" + digits[1:]
    return "254" + digits


def callback_url() -> str | None:
    base = (os.getenv("PUBLIC_BACKEND_URL") or "").strip().rstrip("/")
    secret = os.getenv("PAYHERO_CALLBACK_SECRET") or ""
    if not base:
        return None
    query = urllib.parse.urlencode({"token": secret}) if secret else ""
    return f"{base}/v1/webhooks/payhero/callback" + (f"?{query}" if query else "")


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

def initiate_stk_push(order_id: str, amount: int, phone: str, customer_name: str | None = None) -> dict:
    """Ask Pay Hero to send an M-Pesa PIN prompt to the customer's phone."""
    existing = get_payment(order_id)
    if existing and existing.get("state") == "waiting" and time.time() - existing.get("started", 0) < 20:
        # A prompt was just sent; don't send a second one straight away.
        return existing

    channel = (os.getenv("PAYHERO_CHANNEL_ID") or "").strip()
    if not channel:
        raise PayHeroError("PAYHERO_CHANNEL_ID is not set in .env")

    body = {
        "amount": int(amount),
        "phone_number": normalize_phone(phone),
        "channel_id": int(channel) if channel.isdigit() else channel,
        "provider": "m-pesa",
        "external_reference": order_id,
    }
    if customer_name:
        body["customer_name"] = customer_name
    cb = callback_url()
    if cb:
        body["callback_url"] = cb
    else:
        print("[PayHero] PUBLIC_BACKEND_URL not set - no callback; relying on status checks.")

    res = _request("POST", "payments", body)

    if isinstance(res, dict) and res.get("success") is False:
        raise PayHeroError(_error_message(json.dumps(res)) or "Pay Hero could not send the M-Pesa prompt")

    reference = None
    if isinstance(res, dict):
        reference = res.get("reference") or res.get("Reference") or res.get("CheckoutRequestID")

    return _set_payment(
        order_id,
        reference=reference,
        state="waiting",
        message="Check your phone and enter your M-Pesa PIN to complete the payment.",
        started=time.time(),
        receipt=None,
    )


def parse_status(res: dict) -> tuple[str, str | None, str | None]:
    """Turn a Pay Hero transaction-status reply into (state, receipt, message)."""
    if not isinstance(res, dict):
        return "waiting", None, None
    status = str(res.get("status") or res.get("Status") or "").strip().upper()
    receipt = (
        res.get("third_party_reference")
        or res.get("MpesaReceiptNumber")
        or res.get("provider_reference")
    )
    message = res.get("ResultDesc") or res.get("result_desc") or res.get("message")
    if status in PAID_STATES:
        return "paid", receipt, message
    if status in FAILED_STATES:
        return "failed", None, message or "The payment was not completed."
    return "waiting", None, None


def check_transaction_status(reference: str) -> tuple[str, str | None, str | None]:
    res = _request("GET", "transaction-status?" + urllib.parse.urlencode({"reference": reference}))
    return parse_status(res)


def parse_callback(payload: dict) -> dict:
    """Read the result Pay Hero posts to our callback URL."""
    data = payload.get("response") if isinstance(payload.get("response"), dict) else payload
    order_id = data.get("ExternalReference") or data.get("external_reference") or data.get("User_Reference")
    code = data.get("ResultCode", data.get("result_code"))
    status = str(data.get("Status") or data.get("status") or "").strip().upper()
    ok = str(code) == "0" or status in PAID_STATES
    return {
        "order_id": order_id,
        "ok": ok,
        "receipt": data.get("MpesaReceiptNumber") or data.get("third_party_reference"),
        "amount": data.get("Amount") or data.get("amount"),
        "message": data.get("ResultDesc") or data.get("result_desc"),
    }


# --------------------------------------------------------------------------- applying results

def apply_payment_result(db, order_id: str, ok: bool, receipt: str | None = None,
                         message: str | None = None, amount=None) -> None:
    """Mark an order paid (or the attempt failed) after Pay Hero reports back."""
    from app.models.order import Order
    from app.services.order_service import OrderService

    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        print(f"[PayHero] Result for unknown order {order_id} - ignored")
        return

    if not ok:
        if order.status == "pending":
            _set_payment(order_id, state="failed",
                         message=message or "The payment was not completed. You can try again.")
        print(f"[PayHero] Payment FAILED for {order_id}: {message}")
        return

    if order.status != "pending":
        _set_payment(order_id, state="paid", receipt=order.mpesa_transaction_id)
        return

    if amount is not None:
        try:
            if int(float(amount)) != int(order.total):
                print(f"[PayHero] Amount mismatch for {order_id}: paid {amount}, order total {order.total} - NOT marked paid")
                _set_payment(order_id, state="failed",
                             message="The amount paid did not match the order total. Please contact us.")
                return
        except (TypeError, ValueError):
            pass

    OrderService(db).update_order_status(order_id, "paid", receipt)
    _set_payment(order_id, state="paid", receipt=receipt,
                 message="Payment received. Thank you!")
    print(f"[PayHero] Order {order_id} marked PAID (receipt {receipt})")
