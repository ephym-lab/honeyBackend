"""
Delivery fee for Pedni Honey: priced by ZONE (the customer's county) and WEIGHT.

    delivery = zone fee + (kg above the free allowance, rounded up) x price per extra kg

Optional bulk rule: an order with at least `bulk_min_products` DIFFERENT products pays
`bulk_fee` instead, but only when that is cheaper.

Optional free delivery (off by default): orders whose subtotal reaches
`free_delivery_min_order` pay no delivery at all.

All numbers are set by the admin (Admin > Delivery) and stored in the `store_settings` table.
"""
import json
import math
import uuid
from copy import deepcopy

from sqlalchemy import text

SETTINGS_KEY = "delivery"

DEFAULT_SETTINGS = {
    "zones": [
        {"name": "Zone 1 - Local", "fee": 200, "counties": ["Homa Bay"]},
        {"name": "Zone 2 - Nearby", "fee": 400,
         "counties": ["Kisumu", "Migori", "Kisii", "Nyamira", "Siaya"]},
    ],
    "other_zone_name": "Rest of Kenya",
    "other_zone_fee": 700,
    "free_kg": 5,             # kg included in the zone fee
    "per_extra_kg": 50,       # KSh for every kg above free_kg
    "default_weight_kg": 1,   # used for products with no weight set
    "bulk_min_products": 0,   # 0 = bulk rule off
    "bulk_fee": 0,
    "free_delivery_enabled": False,
    "free_delivery_min_order": 0,
}


# --------------------------------------------------------------------------- settings

def _num(value, default, minimum=0.0):
    try:
        n = float(value)
    except (TypeError, ValueError):
        return default
    return max(minimum, n)


def clean_settings(data: dict) -> dict:
    """Validate what the admin sends; fall back to defaults for anything missing or invalid."""
    data = data or {}
    out = deepcopy(DEFAULT_SETTINGS)

    zones = data.get("zones")
    if isinstance(zones, list):
        cleaned, seen = [], set()
        for z in zones:
            if not isinstance(z, dict):
                continue
            name = str(z.get("name") or "").strip() or f"Zone {len(cleaned) + 1}"
            counties = []
            for c in z.get("counties") or []:
                c = str(c).strip()
                if c and c.lower() not in seen:      # a county can only be in one zone
                    seen.add(c.lower())
                    counties.append(c)
            cleaned.append({"name": name[:60], "fee": int(_num(z.get("fee"), 0)), "counties": counties})
        out["zones"] = cleaned

    out["other_zone_name"] = str(data.get("other_zone_name") or out["other_zone_name"]).strip()[:60]
    out["other_zone_fee"] = int(_num(data.get("other_zone_fee"), out["other_zone_fee"]))
    out["free_kg"] = _num(data.get("free_kg"), out["free_kg"])
    out["per_extra_kg"] = int(_num(data.get("per_extra_kg"), out["per_extra_kg"]))
    out["default_weight_kg"] = _num(data.get("default_weight_kg"), out["default_weight_kg"])
    out["bulk_min_products"] = int(_num(data.get("bulk_min_products"), out["bulk_min_products"]))
    out["bulk_fee"] = int(_num(data.get("bulk_fee"), out["bulk_fee"]))
    out["free_delivery_enabled"] = bool(data.get("free_delivery_enabled", False))
    out["free_delivery_min_order"] = int(_num(data.get("free_delivery_min_order"), 0))
    return out


def get_settings(db) -> dict:
    try:
        row = db.execute(
            text("SELECT value FROM store_settings WHERE key = :k"), {"k": SETTINGS_KEY}
        ).first()
    except Exception as e:  # table missing etc. - use defaults rather than break checkout
        db.rollback()
        print(f"[Delivery] Could not read settings, using defaults: {e}")
        return deepcopy(DEFAULT_SETTINGS)
    if not row:
        return deepcopy(DEFAULT_SETTINGS)
    value = row[0]
    if isinstance(value, str):
        value = json.loads(value)
    return clean_settings(value)


def save_settings(db, data: dict) -> dict:
    settings = clean_settings(data)
    db.execute(
        text(
            "INSERT INTO store_settings (key, value, updated_at) "
            "VALUES (:k, CAST(:v AS JSONB), now()) "
            "ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = now()"
        ),
        {"k": SETTINGS_KEY, "v": json.dumps(settings)},
    )
    db.commit()
    return settings


# --------------------------------------------------------------------------- calculation

def find_zone(settings: dict, county):
    if county:
        key = str(county).strip().lower()
        for z in settings["zones"]:
            if key in (c.lower() for c in z["counties"]):
                return z["name"], z["fee"]
    return settings["other_zone_name"], settings["other_zone_fee"]


def calculate(settings: dict, lines, county, subtotal=0) -> dict:
    """
    lines = [(product_id, quantity, weight_kg or None), ...]
    subtotal = value of the goods (only needed for the free-delivery rule)
    Returns the delivery fee and how it was worked out.
    """
    zone_name, zone_fee = find_zone(settings, county)

    total_kg = 0.0
    for _pid, qty, weight in lines:
        w = settings["default_weight_kg"] if weight in (None, "") else float(weight)
        total_kg += max(0.0, w) * max(0, int(qty))
    total_kg = round(total_kg, 2)

    extra_kg = max(0, math.ceil(round(total_kg - settings["free_kg"], 6)))
    weight_charge = extra_kg * settings["per_extra_kg"]
    normal_fee = int(zone_fee + weight_charge)

    distinct = len({str(pid) for pid, qty, _w in lines if int(qty) > 0})
    bulk_on = settings["bulk_min_products"] > 0
    bulk_applied = bulk_on and distinct >= settings["bulk_min_products"] and settings["bulk_fee"] < normal_fee
    shipping = int(settings["bulk_fee"]) if bulk_applied else normal_fee

    free_applied = (
        settings["free_delivery_enabled"]
        and distinct > 0
        and int(subtotal or 0) >= settings["free_delivery_min_order"]
    )
    if free_applied:
        shipping = 0

    return {
        "shipping": shipping,
        "zone": zone_name,
        "zoneFee": int(zone_fee),
        "weightKg": total_kg,
        "freeKg": settings["free_kg"],
        "extraKg": extra_kg,
        "weightCharge": int(weight_charge),
        "normalFee": normal_fee,
        "distinctProducts": distinct,
        "bulkApplied": bool(bulk_applied),
        "bulkFee": int(settings["bulk_fee"]),
        "bulkMinProducts": int(settings["bulk_min_products"]),
        "freeDeliveryApplied": bool(free_applied),
        "freeDeliveryMinOrder": int(settings["free_delivery_min_order"]) if settings["free_delivery_enabled"] else None,
    }


def quote_for_items(db, items, county) -> dict:
    """items = [(product_id, quantity), ...]  -> delivery breakdown + subtotal + total."""
    from app.models.product import Products

    lines, subtotal = [], 0
    for pid, qty in items:
        try:
            pid = uuid.UUID(str(pid))
        except ValueError:
            continue
        product = db.query(Products).filter(Products.id == pid).first()
        if not product:
            continue
        weight = getattr(product, "weight_kg", None)
        lines.append((str(product.id), int(qty), float(weight) if weight is not None else None))
        subtotal += int(product.price) * int(qty)

    result = calculate(get_settings(db), lines, county, subtotal)
    result["subtotal"] = subtotal
    result["total"] = subtotal + result["shipping"]
    return result
