from __future__ import annotations

import re
from typing import Any

from app.money import parse_dkk_to_ore
from app.services.hn_parser import HARALD_NYBORG_CVR, HARALD_NYBORG_SLUG, normalize_receipt

AMOUNT_RE = re.compile(r"(\d{1,5}(?:\.\d{3})?[.,]\d{2})$")
SKU_LINE_RE = re.compile(
    r"^(?P<sku>\d{2,6})\s+(?P<qty>\d{1,2})\s+(?P<desc>.+?)\s+(?P<amt>\d{1,5}(?:\.\d{3})?[.,]\d{2})$"
)
DATE_RE = re.compile(r"\b(\d{2}[./-]\d{2}[./-]\d{4})\b")
TIME_RE = re.compile(r"\b(\d{2}[:.]\d{2}[:.]\d{2})\b")
META_LINE_RE = re.compile(
    r"(?P<date>\d{2}[./-]\d{2}[./-]\d{4})\s+(?P<time>\d{2}[:.]\d{2}[:.]\d{2})\s+(?P<kasse>\d{1,2})\s+(?P<invoice>\d{5,7})"
)
BARCODE_RE = re.compile(r"\*\d{2}-\d{6}-\d+\*")
CVR_RE = re.compile(r"3778\s*3315")

SKIP_MARKERS = (
    "varenr",
    "varetekst",
    "antal",
    "heraf",
    "tak for",
    "returnering",
    "originalemball",
    "betjent",
    "altid lave",
    "www.harald",
    "harald-nyborg",
    "30 dages",
    "bytteservice",
    "hent vores",
    "ubrugt",
    "butikker",
    "dato",
    "fakturanr",
)

TOTAL_MARKERS = ("i a l t", "i alt", "ialt")


def fold(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def detect_vendor(text: str) -> dict[str, str | None]:
    blob = text.lower()
    digits = re.sub(r"\D", "", text)
    if (
        "harald" in blob
        or "nyborg" in blob
        or "harald-nyborg" in blob
        or digits.endswith(HARALD_NYBORG_CVR)
        or HARALD_NYBORG_CVR in digits
    ):
        return {"slug": HARALD_NYBORG_SLUG, "name": "Harald Nyborg"}
    return {"slug": None, "name": None}


def _is_skip_line(text: str) -> bool:
    low = text.lower()
    if any(marker in low for marker in SKIP_MARKERS):
        return True
    if "cvr" in low:
        return True
    return False


def _is_total_line(text: str) -> bool:
    low = text.lower().replace(" ", "")
    return "ialt" in low and ("betal" in low or "kort" in low or "kontant" in low or low.startswith("ialt"))


def parse_item_line(text: str) -> dict[str, Any] | None:
    line = fold(text)
    if not line or _is_skip_line(line) or _is_total_line(line):
        return None
    low = line.lower()
    if "moms" in low:
        return None
    match = SKU_LINE_RE.match(line)
    if match:
        return {
            "item_number": match.group("sku"),
            "quantity": int(match.group("qty")),
            "description": fold(match.group("desc")),
            "line_total": match.group("amt"),
        }
    amount_match = AMOUNT_RE.search(line)
    if not amount_match:
        return None
    head = fold(line[: amount_match.start()])
    parts = head.split()
    if len(parts) < 2:
        return None
    if not parts[0].isdigit() or not (2 <= len(parts[0]) <= 6):
        return None
    qty = 1
    desc_parts = parts[1:]
    if parts[1].isdigit() and 1 <= int(parts[1]) <= 99:
        qty = int(parts[1])
        desc_parts = parts[2:]
    description = fold(" ".join(desc_parts))
    if not description:
        return None
    return {
        "item_number": parts[0],
        "quantity": qty,
        "description": description,
        "line_total": amount_match.group(1),
    }


def parse_hn_ocr_text(ocr_text: str) -> dict[str, Any]:
    """Turn Tesseract text into the JSON shape expected by normalize_receipt."""
    lines = [fold(line) for line in ocr_text.splitlines() if fold(line)]
    payload: dict[str, Any] = {
        "vendor": "Harald Nyborg",
        "store_name": None,
        "store_address": None,
        "cvr": None,
        "date": None,
        "time": None,
        "kasse": None,
        "fakturanr": None,
        "payment_method": None,
        "barcode": None,
        "cashier": None,
        "total": None,
        "vat": None,
        "lines": [],
    }

    full = "\n".join(lines)
    date_match = DATE_RE.search(full)
    if date_match:
        payload["date"] = date_match.group(1).replace("-", ".").replace("/", ".")
    time_match = TIME_RE.search(full)
    if time_match:
        payload["time"] = time_match.group(1).replace(".", ":")
    barcode_match = BARCODE_RE.search(full.replace(" ", ""))
    if barcode_match:
        payload["barcode"] = barcode_match.group(0)
    if CVR_RE.search(full):
        payload["cvr"] = HARALD_NYBORG_CVR

    address_parts: list[str] = []
    for line in lines:
        low = line.lower()
        if "www.harald" in low or "harald-nyborg" in low:
            continue
        if re.search(r"\d{4}\s+\w+", line) and any(ch.isalpha() for ch in line):
            if "dato" in low or "kasse" in low:
                continue
            address_parts.append(line)
        if "herlev" in low or "maribo" in low or "bladsaxe" in low or "søborg" in low or "soborg" in low:
            if "harald" in low:
                payload["store_name"] = line
            elif not payload["store_name"]:
                payload["store_name"] = line
    if address_parts:
        payload["store_address"] = ", ".join(address_parts[:2])

    for index, line in enumerate(lines):
        low = line.lower()
        meta = META_LINE_RE.search(line)
        if meta:
            payload["date"] = payload["date"] or meta.group("date").replace("-", ".").replace("/", ".")
            payload["time"] = payload["time"] or meta.group("time").replace(".", ":")
            payload["kasse"] = payload["kasse"] or meta.group("kasse")
            payload["fakturanr"] = payload["fakturanr"] or meta.group("invoice")
        if "kasse" in low:
            nums = re.findall(r"\b(\d{1,2})\b", line)
            if nums:
                payload["kasse"] = nums[0]
            # Fakturanr is usually the larger number on the same header row or the next
            invoices = [n for n in re.findall(r"\b(\d{5,7})\b", line)]
            if invoices:
                payload["fakturanr"] = invoices[-1]
        if "fakturanr" in low and not payload["fakturanr"]:
            invoices = re.findall(r"\b(\d{5,7})\b", line)
            if invoices:
                payload["fakturanr"] = invoices[-1]
            elif index + 1 < len(lines):
                invoices = re.findall(r"\b(\d{5,7})\b", lines[index + 1])
                if invoices:
                    payload["fakturanr"] = invoices[-1]
        if "kontant" in low:
            payload["payment_method"] = payload["payment_method"] or "KONTANT"
        if "betalingskort" in low:
            payload["payment_method"] = "BETALINGSKORT"
        if "betjent af" in low:
            payload["cashier"] = fold(re.split(r"betjent af", line, flags=re.I)[-1])
        if "heraf" in low and "moms" in low:
            amount = AMOUNT_RE.search(line)
            if amount:
                payload["vat"] = amount.group(1)
        if _is_total_line(line) or (low.replace(" ", "").startswith("ialt") and AMOUNT_RE.search(line)):
            amount = AMOUNT_RE.search(line)
            if amount:
                payload["total"] = amount.group(1)
            if "betalingskort" in low:
                payload["payment_method"] = "BETALINGSKORT"

    for line in lines:
        item = parse_item_line(line)
        if item:
            payload["lines"].append(item)

    if not payload["fakturanr"] and payload["barcode"]:
        tail = payload["barcode"].strip("*").split("-")[-1]
        if tail.isdigit():
            payload["fakturanr"] = tail

    return payload


def parse_ocr_document(ocr_text: str) -> tuple[Any, dict[str, Any], bool]:
    """Detect vendor from OCR text, then apply the Harald Nyborg layout if it matches."""
    vendor = detect_vendor(ocr_text)
    if vendor["slug"] == HARALD_NYBORG_SLUG:
        payload = parse_hn_ocr_text(ocr_text)
        parsed = normalize_receipt(payload)
        failed = not parsed.lines or parsed.total_ore == 0
        if failed:
            parsed.warnings.append("Local OCR could not read enough Harald Nyborg line items. Flagged for training.")
        return parsed, payload, failed

    payload = {
        "vendor": vendor["name"] or "Unknown vendor",
        "lines": [],
        "ocr_text": ocr_text,
    }
    parsed = normalize_receipt(payload)
    parsed.warnings.append("Vendor layout is not trained yet. Flagged for training.")
    return parsed, payload, True
