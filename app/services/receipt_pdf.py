"""
Payment receipt as a PDF (attached to the customer's confirmation email once M-Pesa payment is received).

Pure Python - no extra packages to install. Uses the standard PDF fonts (Helvetica).
Business details come from EmailTemplates; the KRA PIN from BUSINESS_KRA_PIN in .env (left out if empty).
"""
import os
from datetime import datetime, timedelta, timezone

# Helvetica / Helvetica-Bold widths for characters 32..126 (1/1000 of the font size)
_W_REG = [278, 278, 355, 556, 556, 889, 667, 222, 333, 333, 389, 584, 278, 333, 278, 278, 556, 556, 556, 556, 556,
          556, 556, 556, 556, 556, 278, 278, 584, 584, 584, 556, 1015, 667, 667, 722, 722, 667, 611, 778, 722, 278,
          500, 667, 556, 833, 722, 778, 667, 778, 722, 667, 611, 722, 667, 944, 667, 667, 611, 278, 278, 278, 469,
          556, 222, 556, 556, 500, 556, 556, 278, 556, 556, 222, 222, 500, 222, 833, 556, 556, 556, 556, 333, 500,
          278, 556, 500, 722, 500, 500, 500, 334, 260, 334, 584]
_W_BOLD = [278, 333, 474, 556, 556, 889, 722, 278, 333, 333, 389, 584, 278, 333, 278, 278, 556, 556, 556, 556, 556,
           556, 556, 556, 556, 556, 333, 333, 584, 584, 584, 611, 975, 722, 722, 722, 722, 667, 611, 778, 722, 278,
           556, 722, 611, 833, 722, 778, 667, 778, 722, 667, 611, 722, 667, 944, 667, 667, 611, 333, 278, 333, 584,
           556, 278, 556, 611, 556, 611, 556, 333, 611, 611, 278, 278, 556, 278, 889, 611, 611, 611, 611, 389, 556,
           333, 611, 556, 778, 556, 556, 500, 389, 280, 389, 584]

PAGE_W, PAGE_H = 595.28, 841.89  # A4
MARGIN = 48

HONEY = (0.957, 0.753, 0.067)      # #F4C011
DARK = (0.125, 0.102, 0.043)       # #201A0B
TEXT = (0.10, 0.10, 0.10)
MUTED = (0.38, 0.38, 0.38)
LINE = (0.88, 0.86, 0.75)
SOFT = (1.0, 0.984, 0.878)         # #FFFBE0
GREEN = (0.18, 0.49, 0.20)


def _jpeg_info(data):
    """(width, height, components) of a JPEG, or None if it is not a usable JPEG."""
    if not data or data[:2] != b"\xff\xd8":
        return None
    i = 2
    while i + 9 < len(data):
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
            i += 2
            continue
        length = int.from_bytes(data[i + 2:i + 4], "big")
        if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
            height = int.from_bytes(data[i + 5:i + 7], "big")
            width = int.from_bytes(data[i + 7:i + 9], "big")
            return width, height, data[i + 9]
        i += 2 + length
    return None


def _load_logo():
    """Logo for the receipt: BUSINESS_LOGO_PATH in .env, or app/assets/logo.jpeg. None if missing."""
    from pathlib import Path
    candidates = [os.getenv("BUSINESS_LOGO_PATH") or "", str(Path(__file__).resolve().parent.parent / "assets" / "logo.jpeg"),
                  str(Path(__file__).resolve().parent.parent / "assets" / "logo.jpg")]
    for path in candidates:
        if path and os.path.isfile(path):
            try:
                data = open(path, "rb").read()
            except OSError:
                continue
            info = _jpeg_info(data)
            if info and info[2] in (1, 3, 4):
                return {"data": data, "width": info[0], "height": info[1], "components": info[2]}
    return None


def _width(text, size, bold=False):
    table = _W_BOLD if bold else _W_REG
    return sum(table[ord(c) - 32] if 32 <= ord(c) <= 126 else 556 for c in str(text)) * size / 1000.0


def _pdf_text(text):
    raw = str(text).replace("–", "-").replace("—", "-").replace("’", "'").replace("‘", "'")
    data = raw.encode("cp1252", "replace")
    return data.replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)")


def _ksh(n):
    try:
        return f"KSh {int(round(float(n or 0))):,}"
    except (TypeError, ValueError):
        return "KSh 0"


def _wrap(text, size, max_width, bold=False, max_lines=2):
    words, lines, current = str(text or "").split(), [], ""
    for word in words:
        trial = (current + " " + word).strip()
        if _width(trial, size, bold) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
            while _width(current, size, bold) > max_width and len(current) > 1:
                current = current[:-1]
    if current:
        lines.append(current)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        last = lines[-1]
        while _width(last + "...", size, bold) > max_width and last:
            last = last[:-1]
        lines[-1] = last + "..."
    return lines or [""]


class _Page:
    def __init__(self):
        self.ops = []

    def color(self, rgb, stroke=False):
        self.ops.append(("%.3f %.3f %.3f " % rgb) + ("RG" if stroke else "rg"))

    def rect(self, x, y, w, h, fill=None, stroke=None, width=0.8):
        if fill:
            self.color(fill)
        if stroke:
            self.color(stroke, stroke=True)
            self.ops.append(f"{width:.2f} w")
        op = "B" if fill and stroke else ("f" if fill else "S")
        self.ops.append(f"{x:.2f} {y:.2f} {w:.2f} {h:.2f} re {op}")

    def line(self, x1, y1, x2, y2, rgb=LINE, width=0.8):
        self.color(rgb, stroke=True)
        self.ops.append(f"{width:.2f} w {x1:.2f} {y1:.2f} m {x2:.2f} {y2:.2f} l S")

    def text(self, x, y, s, size=10, bold=False, rgb=TEXT, align="left"):
        if align == "right":
            x -= _width(s, size, bold)
        elif align == "center":
            x -= _width(s, size, bold) / 2
        self.color(rgb)
        self.ops.append(b"BT /" + (b"F2" if bold else b"F1") + f" {size} Tf {x:.2f} {y:.2f} Td (".encode()
                        + _pdf_text(s) + b") Tj ET")

    def rotated_text(self, x, y, s, size, angle_deg, bold=True, rgb=GREEN):
        import math
        a = math.radians(angle_deg)
        c, sn = math.cos(a), math.sin(a)
        self.color(rgb)
        self.ops.append(b"BT /" + (b"F2" if bold else b"F1") + f" {size} Tf {c:.4f} {sn:.4f} {-sn:.4f} {c:.4f} {x:.2f} {y:.2f} Tm (".encode()
                        + _pdf_text(s) + b") Tj ET")

    def image(self, name, x, y, w, h):
        self.ops.append(f"q {w:.2f} 0 0 {h:.2f} {x:.2f} {y:.2f} cm /{name} Do Q")

    def stream(self):
        parts = [op if isinstance(op, bytes) else op.encode("latin-1") for op in self.ops if op != ""]
        return b"\n".join(parts)


def _build_pdf(pages, logo=None):
    objects = []

    def add(body):
        objects.append(body)
        return len(objects)

    font1 = add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>")
    font2 = add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>")
    xobjects = ""
    if logo:
        space = {1: "/DeviceGray", 3: "/DeviceRGB", 4: "/DeviceCMYK"}[logo["components"]]
        decode = " /Decode [1 0 1 0 1 0 1 0]" if logo["components"] == 4 else ""  # Adobe CMYK JPEGs are inverted
        img = add((f"<< /Type /XObject /Subtype /Image /Width {logo['width']} /Height {logo['height']} "
                   f"/ColorSpace {space} /BitsPerComponent 8 /Filter /DCTDecode{decode} /Length {len(logo['data'])} >>\nstream\n").encode()
                  + logo["data"] + b"\nendstream")
        xobjects = f" /XObject << /Logo {img} 0 R >>"
    pages_id = len(objects) + 1 + 2 * len(pages)  # reserved below
    page_ids = []
    for page in pages:
        data = page.stream()
        content_id = add(b"<< /Length " + str(len(data)).encode() + b" >>\nstream\n" + data + b"\nendstream")
        page_ids.append(add(
            (f"<< /Type /Page /Parent {pages_id} 0 R /MediaBox [0 0 {PAGE_W} {PAGE_H}] "
             f"/Resources << /Font << /F1 {font1} 0 R /F2 {font2} 0 R >>{xobjects} >> /Contents {content_id} 0 R >>").encode()))
    kids = " ".join(f"{p} 0 R" for p in page_ids)
    assert add(f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>".encode()) == pages_id
    catalog = add(f"<< /Type /Catalog /Pages {pages_id} 0 R >>".encode())
    info = add(b"<< /Title (Pedni Honey payment receipt) /Producer (Pedni Honey) >>")

    out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = []
    for i, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n".encode() + body + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
    for off in offsets:
        out += f"{off:010d} 00000 n \n".encode()
    out += (f"trailer\n<< /Size {len(objects) + 1} /Root {catalog} 0 R /Info {info} 0 R >>\n"
            f"startxref\n{xref}\n%%EOF\n").encode()
    return bytes(out)


def _nairobi_now():
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("Africa/Nairobi"))
    except Exception:
        return datetime.now(timezone(timedelta(hours=3)))


def receipt_number(order_id):
    return f"RCT-{str(order_id).replace('ORD-', '')}"


def build_receipt(order, paid_at=None) -> bytes:
    """PDF bytes for one paid order."""
    try:
        from app.services.email_templates import EmailTemplates as T
        biz = {"name": T.BUSINESS_NAME, "tagline": T.TAGLINE, "address": T.POSTAL_ADDRESS,
               "phone": T.CONTACT_PHONE, "email": T.CONTACT_EMAIL}
    except Exception:
        biz = {"name": "Pedni Honey", "tagline": "Nurturing Nature's Gift", "address": "P.O Box 157-40301, Kendu Bay",
               "phone": "0704 089 414", "email": "pedni2021@gmail.com"}
    kra_pin = (os.getenv("BUSINESS_KRA_PIN") or "").strip()
    paid_at = paid_at or _nairobi_now()

    g = lambda name, default=None: getattr(order, name, default)  # noqa: E731
    items = [i for i in (g("items") or []) if isinstance(i, dict)]
    mpesa_code = g("mpesa_transaction_id")
    method = "M-Pesa" if str(g("payment_method") or "").lower() == "mpesa" else str(g("payment_method") or "-").title()

    pages, page = [], _Page()
    left, right = MARGIN, PAGE_W - MARGIN
    logo = _load_logo()

    def header(p, first):
        p.rect(0, PAGE_H - 96, PAGE_W, 96, fill=DARK)
        p.rect(0, PAGE_H - 100, PAGE_W, 4, fill=HONEY)
        name_x = left
        if logo:
            box = 64.0  # logo fits inside a 64 x 64 pt square, on a light tile so dark logos stay visible
            scale = min(box / logo["width"], box / logo["height"])
            w, h = logo["width"] * scale, logo["height"] * scale
            tile_y = PAGE_H - 48 - box / 2
            p.rect(left - 4, tile_y - 4, box + 8, box + 8, fill=(1, 1, 1))
            p.image("Logo", left + (box - w) / 2, tile_y + (box - h) / 2, w, h)
            name_x = left + box + 18
        p.text(name_x, PAGE_H - 50, biz["name"], 24, bold=True, rgb=HONEY)
        p.text(name_x, PAGE_H - 70, biz["tagline"], 10, rgb=(0.92, 0.88, 0.75))
        p.text(right, PAGE_H - 48, "PAYMENT RECEIPT" if first else "PAYMENT RECEIPT (continued)", 16, bold=True,
               rgb=(1, 1, 1), align="right")
        p.text(right, PAGE_H - 68, receipt_number(g("id")), 11, rgb=HONEY, align="right")

    header(page, True)
    y = PAGE_H - 132

    # business (left) and receipt details (right)
    biz_lines = [biz["address"], f"Phone: {biz['phone']}", f"Email: {biz['email']}"]
    if kra_pin:
        biz_lines.append(f"KRA PIN: {kra_pin}")
    page.text(left, y, "FROM", 8, bold=True, rgb=MUTED)
    page.text(left, y - 15, biz["name"], 11, bold=True)
    for n, line in enumerate(biz_lines):
        page.text(left, y - 30 - n * 13, line, 9.5, rgb=MUTED)

    details = [
        ("Receipt no.", receipt_number(g("id"))),
        ("Order no.", str(g("id") or "-")),
        ("Date paid", paid_at.strftime("%d %b %Y, %I:%M %p").replace(" 0", " ") + " (EAT)"),
        ("Paid with", method),
    ]
    if mpesa_code:
        details.append(("M-Pesa code", str(mpesa_code)))
    label_x = right - 210
    for n, (label, value) in enumerate(details):
        yy = y - n * 15
        page.text(label_x, yy, label, 9.5, rgb=MUTED)
        page.text(right, yy, value, 9.5, bold=True, align="right")

    y -= max(30 + len(biz_lines) * 13, len(details) * 15) + 18

    # billed to
    page.rect(left, y - 62, right - left, 62, fill=SOFT, stroke=LINE)
    page.text(left + 12, y - 16, "BILLED TO", 8, bold=True, rgb=MUTED)
    page.text(left + 12, y - 31, g("customer_name") or "-", 11, bold=True)
    contact = "   ".join(x for x in [str(g("phone") or ""), str(g("email") or "")] if x)
    page.text(left + 12, y - 45, contact, 9.5, rgb=MUTED)
    place = ", ".join(x for x in [str(g("address") or "").strip(), str(g("county") or "").strip()] if x)
    page.text(left + 12, y - 57, _wrap(f"Delivery: {place}" if place else "", 9.5, right - left - 24, max_lines=1)[0],
              9.5, rgb=MUTED)
    y -= 86

    # items table
    col_item, col_qty, col_unit, col_amt = left + 10, right - 200, right - 110, right - 10
    name_width = col_qty - col_item - 50

    def table_head(p, yy):
        p.rect(left, yy - 22, right - left, 22, fill=HONEY)
        p.text(col_item, yy - 15, "Item", 9.5, bold=True, rgb=DARK)
        p.text(col_qty, yy - 15, "Qty", 9.5, bold=True, rgb=DARK, align="right")
        p.text(col_unit, yy - 15, "Unit price", 9.5, bold=True, rgb=DARK, align="right")
        p.text(col_amt, yy - 15, "Amount", 9.5, bold=True, rgb=DARK, align="right")
        return yy - 22

    y = table_head(page, y)
    for item in items:
        qty = int(item.get("quantity") or 0)
        price = float(item.get("price") or 0)
        lines = _wrap(item.get("productName") or "Item", 10, name_width)
        row_h = 12 + 13 * len(lines)
        if y - row_h < 170:  # leave room for totals/footer; continue on a new page
            pages.append(page)
            page = _Page()
            header(page, False)
            y = table_head(page, PAGE_H - 132)
        for n, line in enumerate(lines):
            page.text(col_item, y - 16 - n * 13, line, 10)
        page.text(col_qty, y - 16, str(qty), 10, align="right")
        page.text(col_unit, y - 16, _ksh(price), 10, align="right")
        page.text(col_amt, y - 16, _ksh(price * qty), 10, bold=True, align="right")
        y -= row_h
        page.line(left, y, right, y)

    # totals
    y -= 10
    totals = [("Subtotal", _ksh(g("subtotal"))), ("Delivery", _ksh(g("shipping")))]
    for label, value in totals:
        page.text(col_unit, y - 12, label, 10, rgb=MUTED, align="right")
        page.text(col_amt, y - 12, value, 10, align="right")
        y -= 18
    box_left = right - 230
    page.rect(box_left, y - 30, right - box_left, 30, fill=DARK)
    page.text(box_left + 12, y - 19, "TOTAL PAID", 10.5, bold=True, rgb=HONEY)
    page.text(col_amt, y - 20, _ksh(g("total")), 13, bold=True, rgb=(1, 1, 1), align="right")

    # PAID stamp
    stamp_x, stamp_y = left + 40, y - 30
    page.rect(stamp_x - 6, stamp_y - 4, 112, 40, stroke=GREEN, width=2.2)
    page.text(stamp_x + 50, stamp_y + 10, "PAID", 24, bold=True, rgb=GREEN, align="center")
    page.text(stamp_x + 50, stamp_y - 1, "M-PESA" if method == "M-Pesa" else method.upper(), 6.5, bold=True,
              rgb=GREEN, align="center")
    y -= 70

    # footer
    page.line(left, 92, right, 92)
    page.text(PAGE_W / 2, 74, f"Thank you for shopping with {biz['name']}!", 11, bold=True, align="center")
    page.text(PAGE_W / 2, 58, "Keep this receipt for your records. Questions? Call "
              f"{biz['phone']} or email {biz['email']} and quote {g('id')}.", 8.5, rgb=MUTED, align="center")
    page.text(PAGE_W / 2, 44, f"Issued {_nairobi_now().strftime('%d %b %Y')} - this receipt confirms payment received.",
              7.5, rgb=MUTED, align="center")
    pages.append(page)
    return _build_pdf(pages, logo)
