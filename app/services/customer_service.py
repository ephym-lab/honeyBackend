"""
Customers (CRM step 1): one profile per customer, built from data the shop already has -
orders, customer requests, reviews and newsletter subscriptions. Nothing new is stored.

A customer is identified by email (lower-case). Reviews only count when the
customer bought the reviewed product (see _load). Orders, requests and reviews are only read;
the one thing stored here is the admin's private notes (table customer_notes).
"""
from collections import Counter

from sqlalchemy import text

# Orders that count as real sales
PAID_STATES = {"paid", "processing", "shipped", "delivered"}


def _key(email) -> str:
    return str(email or "").strip().lower()


def _iso(value):
    try:
        return value.isoformat() if value is not None else None
    except AttributeError:
        return str(value)


def _sort_time(value) -> str:
    return _iso(value) or ""


def _load(db):
    """Read everything once and group it by customer email."""
    from app.models.order import Order
    from app.models.customer_request import CustomerRequest

    people = {}

    def person(email):
        k = _key(email)
        if not k:
            return None
        if k not in people:
            people[k] = {"email": k, "orders": [], "requests": [], "reviews": [], "subscriber": False}
        return people[k]

    for o in db.query(Order).all():
        p = person(o.email)
        if p is not None:
            p["orders"].append(o)

    for r in db.query(CustomerRequest).all():
        p = person(r.email)
        if p is not None:
            p["requests"].append(r)

    try:
        from app.models.review import Review
        for rv in db.query(Review).all():
            p = person(getattr(rv, "email", None))
            if p is not None:
                p["reviews"].append(rv)
    except Exception as e:  # reviews are optional for this page
        print(f"[Customers] Could not read reviews: {e}")

    try:
        from app.models.newsletter import NewsletterSubscription
        for s in db.query(NewsletterSubscription).all():
            if getattr(s, "active", True):
                k = _key(s.email)
                if k in people:  # only mark existing customers; subscribers alone are not customers
                    people[k]["subscriber"] = True
    except Exception as e:
        print(f"[Customers] Could not read newsletter subscribers: {e}")

    # The review form's email is optional and not checked, so anyone could type someone else's.
    # Only keep a review on a profile when that customer has a PAID order containing the
    # reviewed product - then it really was a buyer of that product who wrote it.
    for p in people.values():
        if not p["reviews"]:
            continue
        bought = set()
        for o in p["orders"]:
            if str(o.status or "").lower() in PAID_STATES:
                for i in (o.items or []):
                    if isinstance(i, dict) and i.get("productId"):
                        bought.add(str(i["productId"]))
        p["reviews"] = [rv for rv in p["reviews"] if str(rv.product_id) in bought]

    return people


def _summary_row(p):
    orders = sorted(p["orders"], key=lambda o: _sort_time(o.created_at), reverse=True)
    requests = sorted(p["requests"], key=lambda r: _sort_time(r.created_at), reverse=True)
    paid = [o for o in orders if str(o.status or "").lower() in PAID_STATES]
    unpaid = [o for o in orders if str(o.status or "").lower() in ("pending", "cancelled")]

    latest_order = orders[0] if orders else None
    latest_request = requests[0] if requests else None
    name = (latest_order.customer_name if latest_order else None) or \
           (latest_request.name if latest_request else None) or p["email"]
    phone = (latest_order.phone if latest_order else None) or \
            (latest_request.phone if latest_request else None)
    county = latest_order.county if latest_order else None

    times = [_sort_time(o.created_at) for o in orders] + [_sort_time(r.created_at) for r in requests]
    last_activity = max(times) if times else None

    labels = []
    if len(paid) >= 2:
        labels.append("Repeat buyer")
    elif len(paid) == 1:
        labels.append("Customer")
    if requests:
        labels.append("Enquiry")
    if p["subscriber"]:
        labels.append("Subscriber")
    if unpaid and not paid:
        labels.append("Never paid")

    return {
        "email": p["email"],
        "name": name,
        "phone": phone,
        "county": county,
        "paidOrders": len(paid),
        "totalSpent": int(sum(int(o.total or 0) for o in paid)),
        "unpaidOrders": len(unpaid),
        "lastOrderDate": _iso(paid[0].created_at) if paid else None,
        "lastActivity": last_activity,
        "requests": len(requests),
        "openRequests": sum(1 for r in requests if str(r.status or "") != "Completed"),
        "reviews": len(p["reviews"]),
        "subscriber": p["subscriber"],
        "labels": labels,
    }


def list_customers(db) -> dict:
    rows = [_summary_row(p) for p in _load(db).values()]
    rows.sort(key=lambda r: (r["lastActivity"] or ""), reverse=True)

    buyers = [r for r in rows if r["paidOrders"] > 0]
    repeat = [r for r in buyers if r["paidOrders"] >= 2]
    counties = Counter(r["county"] for r in buyers if r["county"])
    top_county = counties.most_common(1)[0] if counties else None

    return {
        "success": True,
        "data": {
            "customers": rows,
            "summary": {
                "totalCustomers": len(rows),
                "buyers": len(buyers),
                "repeatBuyers": len(repeat),
                "repeatRate": round(100 * len(repeat) / len(buyers)) if buyers else 0,
                "topCounty": top_county[0] if top_county else None,
                "topCountyBuyers": top_county[1] if top_county else 0,
                "totalSpent": sum(r["totalSpent"] for r in buyers),
            },
        },
    }


def customer_profile(db, email: str) -> dict | None:
    people = _load(db)
    p = people.get(_key(email))
    if not p:
        return None

    product_names = {}
    if p["reviews"]:
        try:
            from app.models.product import Products
            ids = {rv.product_id for rv in p["reviews"]}
            for pid, name in db.query(Products.id, Products.name).filter(Products.id.in_(ids)).all():
                product_names[pid] = name
        except Exception as e:
            print(f"[Customers] Could not read product names: {e}")

    orders = sorted(p["orders"], key=lambda o: _sort_time(o.created_at), reverse=True)
    requests = sorted(p["requests"], key=lambda r: _sort_time(r.created_at), reverse=True)
    reviews = sorted(p["reviews"], key=lambda r: _sort_time(r.created_at), reverse=True)

    return {
        "success": True,
        "data": {
            **_summary_row(p),
            "notes": get_notes(db, p["email"]),
            "address": orders[0].address if orders else None,
            "orders": [
                {
                    "id": o.id,
                    "date": _iso(o.created_at) or _iso(o.order_date),
                    "status": o.status,
                    "total": int(o.total or 0),
                    "items": [
                        {"name": i.get("productName"), "quantity": i.get("quantity")}
                        for i in (o.items or []) if isinstance(i, dict)
                    ],
                    "county": o.county,
                    "mpesaReceipt": o.mpesa_transaction_id,
                }
                for o in orders
            ],
            "requestsList": [
                {
                    "id": str(r.id),
                    "reference": getattr(r, "reference", None),
                    "date": _iso(r.created_at),
                    "reason": r.reason,
                    "status": r.status,
                    "message": (r.message or "")[:300],
                }
                for r in requests
            ],
            "reviewsList": [
                {
                    "id": str(rv.id),
                    "date": _iso(rv.created_at),
                    "product": product_names.get(rv.product_id, "Deleted product"),
                    "rating": rv.rating,
                    "comment": rv.comment,
                    "verified": bool(rv.verified),
                }
                for rv in reviews
            ],
        },
    }


# --------------------------------------------------------------------------- notes (step 2)

def get_notes(db, email: str) -> list:
    try:
        rows = db.execute(
            text("SELECT id, note, created_at FROM customer_notes WHERE lower(email) = :e ORDER BY created_at DESC, id DESC"),
            {"e": _key(email)},
        ).fetchall()
    except Exception as e:  # table missing - show the profile anyway
        db.rollback()
        print(f"[Customers] Could not read notes: {e}")
        return []
    return [{"id": r[0], "note": r[1], "date": _iso(r[2])} for r in rows]


def add_note(db, email: str, note: str) -> dict:
    row = db.execute(
        text("INSERT INTO customer_notes (email, note) VALUES (:e, :n) RETURNING id, note, created_at"),
        {"e": _key(email), "n": note},
    ).fetchone()
    db.commit()
    return {"id": row[0], "note": row[1], "date": _iso(row[2])}


def delete_note(db, note_id: int) -> bool:
    result = db.execute(text("DELETE FROM customer_notes WHERE id = :i"), {"i": note_id})
    db.commit()
    return (result.rowcount or 0) > 0
