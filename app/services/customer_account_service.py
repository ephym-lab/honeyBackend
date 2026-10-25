"""
Customer accounts (optional - switched on with CUSTOMER_ACCOUNTS_ENABLED=true in .env).

Kept completely separate from the admin login:
  - customers live in their own table (customer_accounts), not in "users"
  - their login token carries typ="customer"; admin pages never accept it, and
    customer pages never accept an admin token
Guest checkout keeps working whether accounts are on or off.

Tables: customer_accounts, customer_account_tokens (email verification / password reset links),
and orders.customer_account_id (which account placed an order).
"""
import hashlib
import os
import re
import secrets
import time
import uuid
from datetime import datetime, timedelta

from sqlalchemy import text

try:  # make sure .env values (CUSTOMER_ACCOUNTS_ENABLED, FRONTEND_URL) are visible
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

TOKEN_DAYS = 30                 # how long a customer stays logged in
VERIFY_HOURS = 48               # email confirmation link
RESET_MINUTES = 60              # password reset link
MIN_PASSWORD = 8
MAX_FAILED_LOGINS = 5           # then wait LOCK_MINUTES
LOCK_MINUTES = 15

PAID_STATES = ("paid", "processing", "shipped", "delivered")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class AccountError(Exception):
    """A problem to show the customer (status code + message)."""

    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status
        self.message = message


# --------------------------------------------------------------------------- switch

def enabled() -> bool:
    return str(os.getenv("CUSTOMER_ACCOUNTS_ENABLED", "false")).strip().lower() in ("1", "true", "yes", "on")


def require_enabled():
    if not enabled():
        raise AccountError(404, "Customer accounts are not available yet.")


# --------------------------------------------------------------------------- helpers

def _norm_email(email) -> str:
    return str(email or "").strip().lower()


def _iso(value):
    try:
        return value.isoformat() if value is not None else None
    except AttributeError:
        return str(value)


def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _frontend_url() -> str:
    return (os.getenv("FRONTEND_URL") or "http://localhost:5173").rstrip("/")


def _clean(value, limit):
    value = str(value or "").strip()
    return value[:limit] or None


def _check_password(password: str):
    password = str(password or "")
    if len(password) < MIN_PASSWORD:
        raise AccountError(400, f"Your password must be at least {MIN_PASSWORD} characters.")
    if len(password) > 72:
        raise AccountError(400, "Your password is too long (72 characters at most).")
    if password.isdigit() or len(set(password)) < 4:
        raise AccountError(400, "Please choose a stronger password - mix letters and numbers, not just digits.")


_COLUMNS = "id, email, full_name, phone, county, address, email_verified_at, marketing_consent, created_at"


def _account_dict(row) -> dict:
    return {
        "id": str(row[0]),
        "email": row[1],
        "fullName": row[2],
        "phone": row[3],
        "county": row[4],
        "address": row[5],
        "emailVerified": row[6] is not None,
        "marketingConsent": bool(row[7]),
        "createdAt": _iso(row[8]),
    }


def _get_by_id(db, account_id):
    return db.execute(text(f"SELECT {_COLUMNS} FROM customer_accounts WHERE id = :i"), {"i": str(account_id)}).fetchone()


def _get_by_email(db, email):
    return db.execute(text(f"SELECT {_COLUMNS} FROM customer_accounts WHERE email = :e"), {"e": _norm_email(email)}).fetchone()


def _password_hash_for(db, account_id):
    r = db.execute(text("SELECT password_hash FROM customer_accounts WHERE id = :i"), {"i": str(account_id)}).fetchone()
    return r[0] if r else None


def _issue_login_token(account_id) -> str:
    from app.core.security import create_access_token
    return create_access_token({"sub": str(account_id), "typ": "customer"}, expires_delta=timedelta(days=TOKEN_DAYS))


def account_id_from_token(token: str):
    """Customer id from a customer login token, or None (admin tokens and bad tokens give None)."""
    if not token:
        return None
    from app.core.security import decode_access_token
    payload = decode_access_token(token)
    if not payload or payload.get("typ") != "customer" or not payload.get("sub"):
        return None
    return payload["sub"]


# --------------------------------------------------------------------------- failed-login protection

_failed = {}  # email -> [timestamps]


def _too_many_failures(email: str) -> bool:
    now = time.time()
    recent = [t for t in _failed.get(email, []) if now - t < LOCK_MINUTES * 60]
    _failed[email] = recent
    return len(recent) >= MAX_FAILED_LOGINS


def _record_failure(email: str):
    _failed.setdefault(email, []).append(time.time())


# --------------------------------------------------------------------------- one-time links

def _new_link_token(db, account_id, purpose: str, lifetime: timedelta) -> str:
    raw = secrets.token_urlsafe(32)
    # only the newest link of each kind works
    db.execute(text("UPDATE customer_account_tokens SET used_at = now() "
                    "WHERE account_id = :a AND purpose = :p AND used_at IS NULL"),
               {"a": str(account_id), "p": purpose})
    db.execute(text("INSERT INTO customer_account_tokens (account_id, purpose, token_hash, expires_at) "
                    "VALUES (:a, :p, :h, :x)"),
               {"a": str(account_id), "p": purpose, "h": _hash_token(raw), "x": datetime.utcnow() + lifetime})
    return raw


def _use_link_token(db, raw: str, purpose: str):
    """Returns the account id if the link is valid (and marks it used), else None."""
    row = db.execute(text(
        "UPDATE customer_account_tokens SET used_at = now() "
        "WHERE token_hash = :h AND purpose = :p AND used_at IS NULL AND expires_at > :n "
        "RETURNING account_id"
    ), {"h": _hash_token(str(raw or "")), "p": purpose, "n": datetime.utcnow()}).fetchone()
    return row[0] if row else None


# --------------------------------------------------------------------------- emails

def _send(to: str, subject: str, html: str):
    try:
        from app.services.email_service import EmailService
        EmailService().send_html_email(to, subject, html)
    except Exception as e:  # never block sign-up because of email
        print(f"[Accounts] Email to {to} failed: {e}")


def _email_page(title: str, body_html: str, button_label: str, url: str, preheader: str) -> str:
    try:
        from app.services.email_templates import EmailTemplates as T
        from html import escape
        content = f"""
        <div class="content">
            <h2>{escape(title)}</h2>
            {body_html}
            {T.button(button_label, url)}
            <p class="small">If the button does not work, copy this link into your browser:<br>
            <span style="word-break: break-all;">{escape(url)}</span></p>
        </div>
        """
        return T._base_template(content, preheader)
    except Exception:
        return f"<h2>{title}</h2>{body_html}<p><a href='{url}'>{button_label}</a></p>"


def _send_verification(db, account_id, email, name):
    raw = _new_link_token(db, account_id, "verify", timedelta(hours=VERIFY_HOURS))
    db.commit()
    url = f"{_frontend_url()}/account/verify?token={raw}"
    from html import escape
    html = _email_page(
        "Confirm your email",
        f"<p>Hi <strong>{escape(name or 'there')}</strong>,</p>"
        "<p>Thank you for creating a Pedni Honey account. Please confirm this is your email address. "
        "Once confirmed, all your orders made with this email - including earlier ones - will show in your account.</p>",
        "Confirm my email", url, "Confirm your email to finish setting up your Pedni Honey account.",
    )
    _send(email, "Confirm your email - Pedni Honey", html)


# --------------------------------------------------------------------------- actions

def register(db, payload: dict) -> dict:
    require_enabled()
    email = _norm_email(payload.get("email"))
    if not EMAIL_RE.match(email):
        raise AccountError(400, "Please enter a valid email address.")
    password = str(payload.get("password") or "")
    _check_password(password)
    if _get_by_email(db, email):
        raise AccountError(400, "An account with this email already exists. Log in, or use 'Forgot password'.")

    from app.core.security import get_password_hash
    account_id = str(uuid.uuid4())
    db.execute(text(
        "INSERT INTO customer_accounts (id, email, password_hash, full_name, phone, county, address, marketing_consent) "
        "VALUES (:i, :e, :h, :n, :p, :c, :a, :m)"
    ), {
        "i": account_id, "e": email, "h": get_password_hash(password),
        "n": _clean(payload.get("fullName") or payload.get("full_name"), 255),
        "p": _clean(payload.get("phone"), 30), "c": _clean(payload.get("county"), 100),
        "a": _clean(payload.get("address"), 500), "m": bool(payload.get("marketingConsent")),
    })
    db.commit()
    row = _get_by_id(db, account_id)
    _send_verification(db, account_id, email, row[2])
    return {"token": _issue_login_token(account_id), "account": _account_dict(row)}


def login(db, payload: dict) -> dict:
    require_enabled()
    email = _norm_email(payload.get("email"))
    if _too_many_failures(email):
        raise AccountError(429, f"Too many wrong passwords. Please wait {LOCK_MINUTES} minutes or reset your password.")
    row = _get_by_email(db, email)
    from app.core.security import verify_password
    ok = False
    if row:
        try:
            ok = verify_password(str(payload.get("password") or ""), _password_hash_for(db, row[0]))
        except Exception:
            ok = False
    if not ok:
        _record_failure(email)
        raise AccountError(401, "Wrong email or password.")
    _failed.pop(email, None)
    db.execute(text("UPDATE customer_accounts SET last_login_at = now() WHERE id = :i"), {"i": str(row[0])})
    db.commit()
    return {"token": _issue_login_token(row[0]), "account": _account_dict(row)}


def _link_orders(db, account_id, email):
    db.execute(text("UPDATE orders SET customer_account_id = :a "
                    "WHERE lower(email) = :e AND customer_account_id IS NULL"),
               {"a": str(account_id), "e": _norm_email(email)})


def verify_email(db, raw_token: str) -> dict:
    require_enabled()
    account_id = _use_link_token(db, raw_token, "verify")
    if not account_id:
        db.rollback()
        raise AccountError(400, "This confirmation link has expired or was already used. Log in and ask for a new one.")
    db.execute(text("UPDATE customer_accounts SET email_verified_at = COALESCE(email_verified_at, now()) WHERE id = :i"),
               {"i": str(account_id)})
    row = _get_by_id(db, account_id)
    _link_orders(db, account_id, row[1])
    db.commit()
    return {"account": _account_dict(_get_by_id(db, account_id))}


def resend_verification(db, account_id) -> dict:
    require_enabled()
    row = _get_by_id(db, account_id)
    if not row:
        raise AccountError(401, "Please log in again.")
    if row[6] is not None:
        return {"message": "Your email is already confirmed."}
    _send_verification(db, account_id, row[1], row[2])
    return {"message": f"We have sent a new confirmation link to {row[1]}."}


def forgot_password(db, email) -> dict:
    require_enabled()
    row = _get_by_email(db, email)
    if row:
        raw = _new_link_token(db, row[0], "reset", timedelta(minutes=RESET_MINUTES))
        db.commit()
        url = f"{_frontend_url()}/account/reset-password?token={raw}"
        from html import escape
        html = _email_page(
            "Reset your password",
            f"<p>Hi <strong>{escape(row[2] or 'there')}</strong>,</p>"
            f"<p>We received a request to reset your Pedni Honey password. The link works for {RESET_MINUTES} minutes.</p>"
            "<p>If you did not ask for this, you can ignore this email - your password will not change.</p>",
            "Choose a new password", url, "Reset your Pedni Honey password.",
        )
        _send(row[1], "Reset your password - Pedni Honey", html)
    # same answer either way, so nobody can find out which emails have accounts
    return {"message": "If an account exists for that email, we have sent a link to reset the password."}


def reset_password(db, raw_token: str, new_password: str) -> dict:
    require_enabled()
    _check_password(new_password)
    account_id = _use_link_token(db, raw_token, "reset")
    if not account_id:
        db.rollback()
        raise AccountError(400, "This reset link has expired or was already used. Please ask for a new one.")
    from app.core.security import get_password_hash
    # opening the link proves they own the inbox, so the email counts as confirmed too
    db.execute(text("UPDATE customer_accounts SET password_hash = :h, updated_at = now(), "
                    "email_verified_at = COALESCE(email_verified_at, now()) WHERE id = :i"),
               {"h": get_password_hash(new_password), "i": str(account_id)})
    row = _get_by_id(db, account_id)
    _link_orders(db, account_id, row[1])
    db.commit()
    _failed.pop(row[1], None)
    return {"token": _issue_login_token(account_id), "account": _account_dict(row)}


def me(db, account_id) -> dict:
    require_enabled()
    row = _get_by_id(db, account_id)
    if not row:
        raise AccountError(401, "Please log in again.")
    return {"account": _account_dict(row)}


def update_me(db, account_id, payload: dict) -> dict:
    require_enabled()
    fields = {"fullName": ("full_name", 255), "phone": ("phone", 30), "county": ("county", 100), "address": ("address", 500)}
    sets, params = [], {"i": str(account_id)}
    for key, (column, limit) in fields.items():
        if key in payload:
            sets.append(f"{column} = :{column}")
            params[column] = _clean(payload.get(key), limit)
    if "marketingConsent" in payload:
        sets.append("marketing_consent = :m")
        params["m"] = bool(payload.get("marketingConsent"))
    if sets:
        db.execute(text(f"UPDATE customer_accounts SET {', '.join(sets)}, updated_at = now() WHERE id = :i"), params)
        db.commit()
    return me(db, account_id)


def change_password(db, account_id, current: str, new: str) -> dict:
    require_enabled()
    from app.core.security import get_password_hash, verify_password
    stored = _password_hash_for(db, account_id)
    if not stored or not verify_password(str(current or ""), stored):
        raise AccountError(400, "Your current password is not correct.")
    _check_password(new)
    db.execute(text("UPDATE customer_accounts SET password_hash = :h, updated_at = now() WHERE id = :i"),
               {"h": get_password_hash(new), "i": str(account_id)})
    db.commit()
    return {"message": "Your password has been changed."}


def my_orders(db, account_id) -> dict:
    require_enabled()
    row = _get_by_id(db, account_id)
    if not row:
        raise AccountError(401, "Please log in again.")
    verified = row[6] is not None
    # Orders placed while logged in always show. Orders made as a guest with the same email
    # only show once the email is confirmed, so nobody can see another person's orders.
    if verified:
        _link_orders(db, account_id, row[1])
        db.commit()
    rows = db.execute(text(
        "SELECT id, created_at, status, total, items, county, mpesa_transaction_id, shipping "
        "FROM orders WHERE customer_account_id = :a ORDER BY created_at DESC"
    ), {"a": str(account_id)}).fetchall()
    orders = []
    for r in rows:
        items = r[4]
        if isinstance(items, str):
            try:
                import json
                items = json.loads(items)
            except ValueError:
                items = []
        items = items if isinstance(items, list) else []
        orders.append({
            "id": r[0], "date": _iso(r[1]), "status": r[2], "total": int(r[3] or 0),
            "items": [{"name": i.get("productName"), "quantity": i.get("quantity"), "price": i.get("price")}
                      for i in items if isinstance(i, dict)],
            "county": r[5], "mpesaReceipt": r[6], "shipping": int(r[7] or 0),
            "paid": str(r[2] or "").lower() in PAID_STATES,
        })
    return {"orders": orders, "emailVerified": verified}


def delete_me(db, account_id, password: str) -> dict:
    require_enabled()
    from app.core.security import verify_password
    stored = _password_hash_for(db, account_id)
    if not stored or not verify_password(str(password or ""), stored):
        raise AccountError(400, "Your password is not correct.")
    # Orders stay (the shop needs them for its records) but are no longer linked to a login.
    db.execute(text("UPDATE orders SET customer_account_id = NULL WHERE customer_account_id = :a"), {"a": str(account_id)})
    db.execute(text("DELETE FROM customer_account_tokens WHERE account_id = :a"), {"a": str(account_id)})
    db.execute(text("DELETE FROM customer_accounts WHERE id = :a"), {"a": str(account_id)})
    db.commit()
    return {"message": "Your account has been deleted."}


# --------------------------------------------------------------------------- checkout

def link_new_order(db, authorization_header, order_result):
    """If a logged-in customer placed this order, remember it on their account."""
    if not enabled() or not authorization_header:
        return
    parts = str(authorization_header).split(" ", 1)
    account_id = account_id_from_token(parts[1].strip() if len(parts) == 2 else "")
    if not account_id:
        return
    order_id = None
    data = order_result.get("data") if isinstance(order_result, dict) else getattr(order_result, "data", None)
    if isinstance(data, dict):
        order_id = data.get("id")
    else:
        order_id = getattr(data, "id", None)
    if not order_id:
        return
    db.execute(text("UPDATE orders SET customer_account_id = :a WHERE id = :o AND customer_account_id IS NULL"),
               {"a": str(account_id), "o": str(order_id)})
    db.commit()
