"""
Enquiry follow-ups (CRM step 3).

For each customer request the admin can record:
  - the outcome: open, Won (with the sale value) or Lost (with a reason)
  - the next follow-up date and what to do on that day
  - a history of what happened (calls, quotes, visits...)

When a follow-up date arrives, a reminder appears in the admin bell.
Stored in two tables: request_followups and request_activity.
"""
import os
import threading
import time
from datetime import date

from sqlalchemy import text

OUTCOMES = {"Won", "Lost"}


def _iso(value):
    try:
        return value.isoformat() if value is not None else None
    except AttributeError:
        return str(value)


def _row(r):
    return {
        "requestId": r[0],
        "outcome": r[1],
        "dealValue": r[2],
        "lostReason": r[3],
        "followUpDate": _iso(r[4]),
        "followUpNote": r[5],
        "updatedAt": _iso(r[6]),
    }


def _activity_row(r):
    return {"id": r[0], "requestId": r[1], "note": r[2], "date": _iso(r[3])}


def _get(db, request_id: str):
    r = db.execute(
        text("SELECT request_id, outcome, deal_value, lost_reason, follow_up_date, follow_up_note, updated_at "
             "FROM request_followups WHERE request_id = :i"),
        {"i": request_id},
    ).fetchone()
    return _row(r) if r else None


def _activity_for(db, request_id: str) -> list:
    rows = db.execute(
        text("SELECT id, request_id, note, created_at FROM request_activity "
             "WHERE request_id = :i ORDER BY created_at DESC, id DESC"),
        {"i": request_id},
    ).fetchall()
    return [_activity_row(r) for r in rows]


def request_exists(db, request_id: str) -> bool:
    return db.execute(
        text("SELECT 1 FROM customer_requests WHERE id::text = :i"), {"i": request_id}
    ).fetchone() is not None


def list_all(db) -> dict:
    """Every saved follow-up and activity, keyed by request id (deleted requests left out)."""
    followups = {}
    for r in db.execute(text(
        "SELECT f.request_id, f.outcome, f.deal_value, f.lost_reason, f.follow_up_date, f.follow_up_note, f.updated_at "
        "FROM request_followups f JOIN customer_requests c ON c.id::text = f.request_id"
    )).fetchall():
        followups[r[0]] = _row(r)

    activity = {}
    for r in db.execute(text(
        "SELECT a.id, a.request_id, a.note, a.created_at FROM request_activity a "
        "JOIN customer_requests c ON c.id::text = a.request_id ORDER BY a.created_at DESC, a.id DESC"
    )).fetchall():
        activity.setdefault(r[1], []).append(_activity_row(r))

    return {"followups": followups, "activity": activity, "today": date.today().isoformat()}


def log(db, request_id: str, note: str, commit: bool = True) -> dict:
    r = db.execute(
        text("INSERT INTO request_activity (request_id, note) VALUES (:i, :n) RETURNING id, request_id, note, created_at"),
        {"i": request_id, "n": note},
    ).fetchone()
    if commit:
        db.commit()
    return _activity_row(r)


def delete_activity(db, activity_id: int) -> bool:
    result = db.execute(text("DELETE FROM request_activity WHERE id = :i"), {"i": activity_id})
    db.commit()
    return (result.rowcount or 0) > 0


def _parse_date(value):
    if value in (None, ""):
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        raise ValueError("The follow-up date is not a valid date")


def _parse_value(value):
    if value in (None, ""):
        return None
    try:
        amount = int(round(float(str(value).replace(",", ""))))
    except ValueError:
        raise ValueError("The sale value must be a number")
    if amount < 0:
        raise ValueError("The sale value cannot be negative")
    return amount


def save(db, request_id: str, payload: dict) -> dict:
    """
    Save the follow-up for one request. Only the keys sent are changed:
      outcome ("Won" | "Lost" | "" for open), dealValue, lostReason,
      followUpDate ("YYYY-MM-DD" or "" to clear), followUpNote
    Marking Won or Lost also sets the request status to Completed and clears the follow-up date.
    Returns {"followup": ..., "activity": [...], "status": new status or None}
    """
    current = _get(db, request_id) or {
        "outcome": None, "dealValue": None, "lostReason": None, "followUpDate": None, "followUpNote": None,
    }
    new = dict(current)
    history = []

    if "followUpDate" in payload:
        d = _parse_date(payload.get("followUpDate"))
        new["followUpDate"] = d.isoformat() if d else None
    if "followUpNote" in payload:
        new["followUpNote"] = (str(payload.get("followUpNote") or "").strip()[:300]) or None
    if "dealValue" in payload:
        new["dealValue"] = _parse_value(payload.get("dealValue"))
    if "lostReason" in payload:
        new["lostReason"] = (str(payload.get("lostReason") or "").strip()[:300]) or None
    if "outcome" in payload:
        outcome = str(payload.get("outcome") or "").strip().title() or None
        if outcome and outcome not in OUTCOMES:
            raise ValueError("Outcome must be Won, Lost or open")
        new["outcome"] = outcome

    if new["outcome"] != "Won":
        new["dealValue"] = None
    if new["outcome"] != "Lost":
        new["lostReason"] = None
    if new["outcome"] in OUTCOMES:
        new["followUpDate"] = None  # a closed enquiry needs no more follow-ups

    # what to write in the history
    if new["outcome"] != current["outcome"]:
        if new["outcome"] == "Won":
            history.append("Marked as Won" + (f" - KSh {new['dealValue']:,}" if new["dealValue"] else ""))
        elif new["outcome"] == "Lost":
            history.append("Marked as Lost" + (f" - {new['lostReason']}" if new["lostReason"] else ""))
        else:
            history.append("Re-opened")
    elif new["outcome"] == "Won" and new["dealValue"] != current["dealValue"] and new["dealValue"]:
        history.append(f"Sale value changed to KSh {new['dealValue']:,}")
    if new["followUpDate"] != current["followUpDate"]:
        if new["followUpDate"]:
            when = date.fromisoformat(new["followUpDate"]).strftime("%d %b %Y")
            history.append(f"Follow-up set for {when}" + (f": {new['followUpNote']}" if new["followUpNote"] else ""))
        elif new["outcome"] is None:
            history.append("Follow-up cleared")

    db.execute(text(
        "INSERT INTO request_followups (request_id, outcome, deal_value, lost_reason, follow_up_date, follow_up_note, updated_at) "
        "VALUES (:i, :o, :v, :l, :d, :n, now()) "
        "ON CONFLICT (request_id) DO UPDATE SET outcome = :o, deal_value = :v, lost_reason = :l, "
        "follow_up_date = :d, follow_up_note = :n, updated_at = now()"
    ), {
        "i": request_id, "o": new["outcome"], "v": new["dealValue"], "l": new["lostReason"],
        "d": new["followUpDate"], "n": new["followUpNote"],
    })

    new_status = None
    if new["outcome"] in OUTCOMES and new["outcome"] != current["outcome"]:
        db.execute(text("UPDATE customer_requests SET status = 'Completed', updated_at = now() WHERE id::text = :i"),
                   {"i": request_id})
        new_status = "Completed"
    elif new["outcome"] is None and current["outcome"] in OUTCOMES:
        db.execute(text("UPDATE customer_requests SET status = 'In Progress', updated_at = now() WHERE id::text = :i"),
                   {"i": request_id})
        new_status = "In Progress"

    for line in history:
        log(db, request_id, line, commit=False)
    db.commit()

    return {"followup": _get(db, request_id), "activity": _activity_for(db, request_id), "status": new_status}


# --------------------------------------------------------------------------- bell reminders

def send_due_reminders(db) -> int:
    """Put a reminder in the admin bell for every follow-up due today or earlier (once per date)."""
    due = db.execute(text(
        "UPDATE request_followups f SET reminded_for = f.follow_up_date "
        "FROM customer_requests c "
        "WHERE c.id::text = f.request_id AND f.outcome IS NULL AND f.follow_up_date IS NOT NULL "
        "AND f.follow_up_date <= CURRENT_DATE "
        "AND (f.reminded_for IS NULL OR f.reminded_for <> f.follow_up_date) "
        "RETURNING f.request_id, c.name, c.reason, f.follow_up_note, f.follow_up_date"
    )).fetchall()
    db.commit()
    if not due:
        return 0

    from app.services.notification_service import NotificationService
    service = NotificationService(db)
    for request_id, name, reason, note, when in due:
        late = "" if when == date.today() else f" (was due {when.strftime('%d %b')})"
        try:
            service.create_notification(
                title=f"Follow up: {name}",
                message=f"{reason}{late}" + (f" - {note}" if note else ""),
                notification_type="customer_request",
                priority="high",
                related_entity="customer_request",
                related_id=str(request_id),
            )
        except Exception as e:
            db.rollback()
            print(f"[Follow-ups] Could not create reminder for {request_id}: {e}")
    return len(due)


def _reminder_loop():
    from app.database import get_db
    minutes = float(os.getenv("FOLLOWUP_CHECK_MINUTES", "15") or 15)
    time.sleep(20)  # let the app finish starting
    while True:
        gen = get_db()
        try:
            db = next(gen)
            count = send_due_reminders(db)
            if count:
                print(f"[Follow-ups] {count} reminder(s) added to the bell")
        except Exception as e:
            print(f"[Follow-ups] Reminder check failed: {e}")
        finally:
            try:
                gen.close()
            except Exception:
                pass
        time.sleep(max(1.0, minutes) * 60)


_started = False


def start_reminder_loop():
    global _started
    if _started:
        return
    _started = True
    threading.Thread(target=_reminder_loop, name="followup-reminders", daemon=True).start()
