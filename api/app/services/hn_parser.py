from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from app.money import expected_vat_ore, parse_dkk_to_ore

COPENHAGEN = ZoneInfo("Europe/Copenhagen")
HARALD_NYBORG_CVR = "37783315"
HARALD_NYBORG_SLUG = "harald-nyborg"

STORE_HINTS = (
    ("herlev", "Harald Nyborg Herlev"),
    ("maribo", "Harald Nyborg Maribo"),
    ("bladsaxe", "Harald Nyborg Bladsaxe"),
    ("søborg", "Harald Nyborg Bladsaxe"),
    ("soborg", "Harald Nyborg Bladsaxe"),
)


@dataclass
class ParsedLine:
    item_number: str | None
    quantity: int
    description: str
    line_total_ore: int
    unit_price_ore: int


@dataclass
class ParsedReceipt:
    vendor_name: str
    vendor_slug: str | None
    store_name: str | None
    store_address: str | None
    cvr: str | None
    purchased_at: datetime | None
    register_no: str | None
    invoice_no: str | None
    payment_method: str | None
    total_ore: int
    vat_ore: int
    barcode: str | None
    cashier: str | None
    lines: list[ParsedLine] = field(default_factory=list)
    lines_sum_ore: int = 0
    expected_vat_ore: int = 0
    lines_sum_ok: bool = False
    vat_ok: bool = False
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        if self.purchased_at:
            data["purchased_at"] = self.purchased_at.isoformat()
        return data


def _digits(value: Any) -> str | None:
    if value is None:
        return None
    digits = re.sub(r"\D", "", str(value))
    return digits or None


def _clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = re.sub(r"\s+", " ", str(value)).strip()
    return text or None


def _item_number(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip().replace(" ", "")
    text = re.sub(r"[^\dA-Za-z]", "", text)
    return text or None


def _quantity(value: Any) -> int:
    if value is None or value == "":
        return 1
    try:
        qty = int(float(str(value).replace(",", ".")))
    except ValueError:
        return 1
    return qty if qty > 0 else 1


def _is_harald_nyborg(payload: dict[str, Any]) -> bool:
    vendor = (payload.get("vendor") or payload.get("vendor_name") or "").lower()
    cvr = _digits(payload.get("cvr")) or ""
    store = (payload.get("store_name") or payload.get("store") or "").lower()
    address = (payload.get("store_address") or payload.get("address") or "").lower()
    blob = " ".join([vendor, store, address])
    return "harald" in blob or "nyborg" in blob or cvr.endswith(HARALD_NYBORG_CVR)


def _store_name(payload: dict[str, Any]) -> str | None:
    explicit = _clean_text(payload.get("store_name") or payload.get("store"))
    address = (_clean_text(payload.get("store_address") or payload.get("address")) or "").lower()
    haystack = f"{explicit or ''} {address}".lower()
    for needle, name in STORE_HINTS:
        if needle in haystack:
            return name
    return explicit


def _parse_purchased_at(payload: dict[str, Any]) -> datetime | None:
    raw = payload.get("purchased_at")
    if raw:
        try:
            dt = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=COPENHAGEN)
            return dt.astimezone(COPENHAGEN)
        except ValueError:
            pass

    date_text = _clean_text(payload.get("date") or payload.get("dato"))
    time_text = _clean_text(payload.get("time") or payload.get("tid")) or "00:00:00"
    if not date_text:
        return None

    date_text = date_text.replace("/", ".")
    time_text = time_text.replace(".", ":")
    for fmt in ("%d.%m.%Y %H:%M:%S", "%d.%m.%Y %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(f"{date_text} {time_text}", fmt).replace(tzinfo=COPENHAGEN)
        except ValueError:
            continue
    return None


def _parse_line(raw: dict[str, Any] | list[Any]) -> ParsedLine | None:
    if isinstance(raw, list):
        # [varenr, antal, description, ialt]
        while len(raw) < 4:
            raw.append(None)
        raw = {
            "item_number": raw[0],
            "quantity": raw[1],
            "description": raw[2],
            "line_total": raw[3],
        }
    if not isinstance(raw, dict):
        return None

    total = parse_dkk_to_ore(
        raw.get("line_total")
        or raw.get("ialt")
        or raw.get("total")
        or raw.get("price")
        or raw.get("line_total_ore")
    )
    if total is None:
        return None
    # If a fixture already stored øre as *_ore, don't multiply again.
    if raw.get("line_total_ore") is not None and isinstance(raw.get("line_total_ore"), int):
        total = int(raw["line_total_ore"])

    qty = _quantity(raw.get("quantity") or raw.get("antal"))
    unit = parse_dkk_to_ore(raw.get("unit_price") or raw.get("unit_price_ore"))
    if raw.get("unit_price_ore") is not None and isinstance(raw.get("unit_price_ore"), int):
        unit = int(raw["unit_price_ore"])
    if unit is None:
        unit = total // qty if qty else total

    description = _clean_text(raw.get("description") or raw.get("varetekst") or raw.get("name")) or ""
    return ParsedLine(
        item_number=_item_number(raw.get("item_number") or raw.get("varenr") or raw.get("sku")),
        quantity=qty,
        description=description,
        line_total_ore=total,
        unit_price_ore=unit,
    )


def normalize_receipt(payload: dict[str, Any]) -> ParsedReceipt:
    """Turn vision JSON (or a fixture) into a verified receipt structure."""
    is_hn = _is_harald_nyborg(payload)
    vendor_name = _clean_text(payload.get("vendor") or payload.get("vendor_name")) or (
        "Harald Nyborg" if is_hn else "Unknown vendor"
    )
    cvr = _digits(payload.get("cvr"))
    if is_hn and not cvr:
        cvr = HARALD_NYBORG_CVR

    lines: list[ParsedLine] = []
    for raw in payload.get("lines") or payload.get("items") or []:
        line = _parse_line(raw)
        if line:
            lines.append(line)

    total = parse_dkk_to_ore(payload.get("total") or payload.get("total_ore") or payload.get("ialt"))
    if payload.get("total_ore") is not None and isinstance(payload.get("total_ore"), int):
        total = int(payload["total_ore"])
    vat = parse_dkk_to_ore(payload.get("vat") or payload.get("moms") or payload.get("vat_ore"))
    if payload.get("vat_ore") is not None and isinstance(payload.get("vat_ore"), int):
        vat = int(payload["vat_ore"])

    line_sum = sum(line.line_total_ore for line in lines)
    if total is None:
        total = line_sum
    if vat is None:
        vat = expected_vat_ore(total)

    exp_vat = expected_vat_ore(total)
    lines_ok = abs(line_sum - total) <= 1
    vat_ok = abs(vat - exp_vat) <= 1

    warnings: list[str] = []
    if not lines:
        warnings.append("No line items were read from the receipt.")
    if not lines_ok:
        warnings.append(
            f"Line items sum to {line_sum} øre but the printed total is {total} øre."
        )
    if not vat_ok:
        warnings.append(f"Printed VAT {vat} øre does not match 25% inclusive ({exp_vat} øre).")

    payment = _clean_text(payload.get("payment_method") or payload.get("payment"))
    return ParsedReceipt(
        vendor_name=vendor_name,
        vendor_slug=HARALD_NYBORG_SLUG if is_hn else None,
        store_name=_store_name(payload),
        store_address=_clean_text(payload.get("store_address") or payload.get("address")),
        cvr=cvr,
        purchased_at=_parse_purchased_at(payload),
        register_no=_clean_text(payload.get("register_no") or payload.get("kasse")),
        invoice_no=_clean_text(payload.get("invoice_no") or payload.get("fakturanr")),
        payment_method=payment,
        total_ore=total or 0,
        vat_ore=vat or 0,
        barcode=_clean_text(payload.get("barcode")),
        cashier=_clean_text(payload.get("cashier")),
        lines=lines,
        lines_sum_ore=line_sum,
        expected_vat_ore=exp_vat,
        lines_sum_ok=lines_ok,
        vat_ok=vat_ok,
        warnings=warnings,
    )
