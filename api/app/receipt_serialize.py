from uuid import UUID

from sqlalchemy.orm import Session

from app.models import Receipt, ReceiptLine, Tag
from app.money import expected_vat_ore
from app.schemas import ReceiptLineWrite, ReceiptRead


def apply_verification(receipt: Receipt) -> None:
    line_sum = sum(line.line_total_ore for line in receipt.lines)
    receipt.lines_sum_ok = abs(line_sum - receipt.total_ore) <= 1
    receipt.vat_ok = abs(receipt.vat_ore - expected_vat_ore(receipt.total_ore)) <= 1


def set_tags(db: Session, receipt: Receipt, tag_ids: list[UUID] | None) -> None:
    if tag_ids is None:
        return
    found: list[Tag] = []
    for tag_id in tag_ids:
        tag = db.get(Tag, tag_id)
        if tag:
            found.append(tag)
    receipt.tags = found


def replace_lines(receipt: Receipt, lines: list[ReceiptLineWrite]) -> None:
    receipt.lines.clear()
    for index, line in enumerate(lines):
        qty = line.quantity if line.quantity > 0 else 1
        receipt.lines.append(
            ReceiptLine(
                position=index,
                item_number=(line.item_number or "").strip() or None,
                quantity=qty,
                description=line.description.strip(),
                line_total_ore=line.line_total_ore,
                unit_price_ore=line.line_total_ore // qty,
            )
        )


def to_read(receipt: Receipt, warnings: list[str] | None = None) -> ReceiptRead:
    data = ReceiptRead.model_validate(receipt)
    data.image_url = f"/api/v1/receipts/{receipt.id}/image" if receipt.image_path else None
    extra = list(warnings or [])
    if not receipt.lines_sum_ok:
        extra.append("Line items do not add up to the printed total.")
    if not receipt.vat_ok:
        extra.append("VAT does not match 25% inclusive of the total.")
    data.warnings = list(dict.fromkeys(extra))
    return data
