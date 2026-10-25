"""
Low-stock alerts in the admin bell.

Each product can have its own low-stock level (products.low_stock_level, empty = DEFAULT_LEVEL).
Every few minutes the stock is checked:
  - a product that has dropped to its level gets one "Low stock" notification
  - a product that has run out gets one "Out of stock" notification
  - restocking clears the alert, so it will warn again next time
products.stock_alert remembers the last alert ('low' / 'out') so the bell is not flooded.
"""
import os
import threading
import time

from sqlalchemy import text

DEFAULT_LEVEL = 5
_RANK = {None: 0, "low": 1, "out": 2}


def level_for(product_level) -> int:
    try:
        level = int(product_level)
        return level if level >= 0 else DEFAULT_LEVEL
    except (TypeError, ValueError):
        return DEFAULT_LEVEL


def state_for(stock, product_level):
    stock = int(stock or 0)
    if stock <= 0:
        return "out"
    if stock <= level_for(product_level):
        return "low"
    return None


def check(db) -> int:
    """Send alerts for products that just became low or out of stock. Returns how many were sent."""
    rows = db.execute(text("SELECT id, name, stock, low_stock_level, stock_alert FROM products")).fetchall()
    to_alert = []
    for pid, name, stock, level, old in rows:
        new = state_for(stock, level)
        if new == old:
            continue
        db.execute(text("UPDATE products SET stock_alert = :s WHERE id = :i"), {"s": new, "i": pid})
        if _RANK[new] > _RANK.get(old, 0):
            to_alert.append((pid, name, int(stock or 0), level_for(level), new))
    db.commit()
    if not to_alert:
        return 0

    from app.services.notification_service import NotificationService
    service = NotificationService(db)
    for pid, name, stock, level, state in to_alert:
        try:
            service.create_notification(
                title=f"Out of stock: {name}" if state == "out" else f"Low stock: {name}",
                message="None left - customers cannot order it until you restock."
                if state == "out" else f"Only {stock} left (your alert level is {level}). Time to restock.",
                notification_type="low_stock",
                priority="high",
                related_entity="product",
                related_id=str(pid),
            )
        except Exception as e:
            db.rollback()
            print(f"[Stock alerts] Could not create alert for {name}: {e}")
    return len(to_alert)


def _loop():
    from app.database import get_db
    minutes = float(os.getenv("STOCK_CHECK_MINUTES", "5") or 5)
    time.sleep(15)  # let the app finish starting
    while True:
        gen = get_db()
        try:
            db = next(gen)
            sent = check(db)
            if sent:
                print(f"[Stock alerts] {sent} alert(s) added to the bell")
        except Exception as e:
            print(f"[Stock alerts] Check failed: {e}")
        finally:
            try:
                gen.close()
            except Exception:
                pass
        time.sleep(max(1.0, minutes) * 60)


_started = False


def start_loop():
    global _started
    if _started:
        return
    _started = True
    threading.Thread(target=_loop, name="stock-alerts", daemon=True).start()
