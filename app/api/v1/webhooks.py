import hmac
import os

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import payhero_service

router = APIRouter()


@router.post("/mpesa/callback")
async def mpesa_callback():
    """Handle direct Safaricom (Daraja) M-Pesa callback. Not used with Pay Hero."""
    return {"ResultCode": 0, "ResultDesc": "Accepted"}


@router.post("/payhero/callback")
def payhero_callback(
    payload: dict = Body(...),
    token: str = Query(""),
    db: Session = Depends(get_db),
):
    """
    Pay Hero calls this when an STK push payment finishes.
    The secret token in the URL makes sure the call really comes from the
    callback address we gave Pay Hero.
    """
    secret = os.getenv("PAYHERO_CALLBACK_SECRET") or ""
    if not secret or not hmac.compare_digest(token, secret):
        raise HTTPException(status_code=403, detail="Invalid callback token")

    print(f"[PayHero] Callback received: {str(payload)[:500]}")
    result = payhero_service.parse_callback(payload)

    if result["order_id"]:
        payhero_service.apply_payment_result(
            db,
            result["order_id"],
            ok=result["ok"],
            receipt=result["receipt"],
            message=result["message"],
            amount=result["amount"],
        )

    return {"status": "received"}


# ---------------------------------------------------------------------------
# Paystack webhook: Paystack -> Settings -> API Keys & Webhooks -> Webhook URL
#   https://<public backend address>/v1/webhooks/paystack
# (optional while testing locally - the checkout page also checks with Paystack)
# ---------------------------------------------------------------------------
import json as _ps_json

from fastapi import Request as _PsRequest
from fastapi.concurrency import run_in_threadpool as _ps_threadpool

from app.services import paystack_service


def _process_paystack_event(event: dict) -> None:
    if event.get("event") != "charge.success":
        return
    data = event.get("data") or {}
    reference = data.get("reference")
    metadata = data.get("metadata") if isinstance(data.get("metadata"), dict) else {}
    order_id = metadata.get("order_id") or paystack_service.order_id_from_reference(reference)
    if not reference or not order_id:
        return
    # Never trust the webhook body alone - confirm with Paystack first.
    result = paystack_service.verify(reference)
    db_gen = get_db()
    db = next(db_gen)
    try:
        paystack_service.apply_verified_result(db, order_id, result)
    finally:
        db_gen.close()


@router.post("/paystack")
async def paystack_webhook(request: _PsRequest):
    """Paystack calls this when a payment succeeds. Signed with your secret key."""
    raw = await request.body()
    if not paystack_service.valid_signature(raw, request.headers.get("x-paystack-signature")):
        raise HTTPException(status_code=401, detail="Invalid signature")
    try:
        event = _ps_json.loads(raw)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    print(f"[Paystack] Webhook: {event.get('event')} {str((event.get('data') or {}).get('reference'))}")
    try:
        await _ps_threadpool(_process_paystack_event, event)
    except paystack_service.PaymentError as e:
        print(f"[Paystack] Webhook processing failed: {e}")
    return {"status": "received"}
