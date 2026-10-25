"""
Customer account endpoints - /v1/account/...
All of them (except /status) answer 404 while CUSTOMER_ACCOUNTS_ENABLED is not true.
"""
from fastapi import APIRouter, Body, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import customer_account_service as accounts

router = APIRouter()


def _run(fn, *args):
    try:
        return {"success": True, "data": fn(*args)}
    except accounts.AccountError as e:
        raise HTTPException(status_code=e.status, detail=e.message)


def current_customer(authorization: str = Header(default="")):
    """The logged-in customer's id. Admin tokens are refused here."""
    accounts_on = accounts.enabled()
    if not accounts_on:
        raise HTTPException(status_code=404, detail="Customer accounts are not available yet.")
    parts = authorization.split(" ", 1)
    account_id = accounts.account_id_from_token(parts[1].strip() if len(parts) == 2 else "")
    if not account_id:
        raise HTTPException(status_code=401, detail="Please log in to continue.")
    return account_id


@router.get("/status")
def account_status():
    """Lets the website know whether to show login / sign up."""
    return {"success": True, "data": {"enabled": accounts.enabled()}}


@router.post("/register")
def register(payload: dict = Body(...), db: Session = Depends(get_db)):
    return _run(accounts.register, db, payload or {})


@router.post("/login")
def login(payload: dict = Body(...), db: Session = Depends(get_db)):
    return _run(accounts.login, db, payload or {})


@router.post("/verify-email")
def verify_email(payload: dict = Body(...), db: Session = Depends(get_db)):
    return _run(accounts.verify_email, db, (payload or {}).get("token"))


@router.post("/forgot-password")
def forgot_password(payload: dict = Body(...), db: Session = Depends(get_db)):
    return _run(accounts.forgot_password, db, (payload or {}).get("email"))


@router.post("/reset-password")
def reset_password(payload: dict = Body(...), db: Session = Depends(get_db)):
    payload = payload or {}
    return _run(accounts.reset_password, db, payload.get("token"), payload.get("password"))


@router.get("/me")
def get_me(account_id=Depends(current_customer), db: Session = Depends(get_db)):
    return _run(accounts.me, db, account_id)


@router.patch("/me")
def update_me(payload: dict = Body(...), account_id=Depends(current_customer), db: Session = Depends(get_db)):
    return _run(accounts.update_me, db, account_id, payload or {})


@router.post("/me/password")
def change_password(payload: dict = Body(...), account_id=Depends(current_customer), db: Session = Depends(get_db)):
    payload = payload or {}
    return _run(accounts.change_password, db, account_id, payload.get("currentPassword"), payload.get("newPassword"))


@router.post("/me/resend-verification")
def resend_verification(account_id=Depends(current_customer), db: Session = Depends(get_db)):
    return _run(accounts.resend_verification, db, account_id)


@router.get("/me/orders")
def my_orders(account_id=Depends(current_customer), db: Session = Depends(get_db)):
    return _run(accounts.my_orders, db, account_id)


@router.post("/me/delete")
def delete_me(payload: dict = Body(...), account_id=Depends(current_customer), db: Session = Depends(get_db)):
    return _run(accounts.delete_me, db, account_id, (payload or {}).get("password"))
