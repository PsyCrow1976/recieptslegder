from datetime import date, datetime
from pathlib import Path
from typing import Annotated
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.auth import get_current_user
from app.config import settings
from app.database import get_db
from app.models import Receipt, ReceiptLine, Tag, User, Vendor
from app.receipt_serialize import apply_verification, replace_lines, set_tags, to_read
from app.schemas import ReceiptRead, ReceiptWrite
from app.services.hn_parser import ParsedReceipt
from app.services.hn_products import lookup_receipt_products
from app.services.ocr import scan_receipt_image

router = APIRouter(prefix="/receipts", tags=["receipts"])
COPENHAGEN = ZoneInfo("Europe/Copenhagen")

RECEIPT_LOAD = (
    selectinload(Receipt.lines).selectinload(ReceiptLine.product),
    selectinload(Receipt.tags),
    selectinload(Receipt.vendor),
)


def _get_receipt(db: Session, receipt_id: UUID) -> Receipt:
    receipt = db.scalar(select(Receipt).options(*RECEIPT_LOAD).where(Receipt.id == receipt_id))
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    return receipt


def _vendor_for(db: Session, parsed: ParsedReceipt) -> Vendor | None:
    if parsed.vendor_slug:
        return db.scalar(select(Vendor).where(Vendor.slug == parsed.vendor_slug))
    if parsed.cvr:
        return db.scalar(select(Vendor).where(Vendor.cvr == parsed.cvr))
    return None


def _apply_parsed(receipt: Receipt, parsed: ParsedReceipt, vendor: Vendor | None) -> None:
    receipt.vendor_id = vendor.id if vendor else None
    receipt.vendor_name = parsed.vendor_name
    receipt.store_name = parsed.store_name
    receipt.store_address = parsed.store_address
    receipt.cvr = parsed.cvr
    receipt.purchased_at = parsed.purchased_at
    receipt.register_no = parsed.register_no
    receipt.invoice_no = parsed.invoice_no
    receipt.payment_method = parsed.payment_method
    receipt.total_ore = parsed.total_ore
    receipt.vat_ore = parsed.vat_ore
    receipt.barcode = parsed.barcode
    receipt.cashier = parsed.cashier
    receipt.lines_sum_ok = parsed.lines_sum_ok
    receipt.vat_ok = parsed.vat_ok
    receipt.raw_parse = parsed.to_dict()
    receipt.lines.clear()
    for index, line in enumerate(parsed.lines):
        receipt.lines.append(
            ReceiptLine(
                position=index,
                item_number=line.item_number,
                quantity=line.quantity,
                description=line.description,
                line_total_ore=line.line_total_ore,
                unit_price_ore=line.unit_price_ore,
            )
        )


@router.post("/scan", response_model=ReceiptRead)
async def scan_receipt(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
    file: Annotated[UploadFile, File()],
) -> ReceiptRead:
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Upload a JPEG or PNG photo of the receipt")
    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Empty file")
    if len(image_bytes) > 20 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image must be 20 MB or smaller")

    storage = Path(settings.receipt_storage_path)
    storage.mkdir(parents=True, exist_ok=True)
    suffix = ".png" if "png" in (file.content_type or "") else ".jpg"
    filename = f"{uuid4()}{suffix}"
    dest = storage / filename
    dest.write_bytes(image_bytes)

    failed = False
    try:
        parsed, raw, failed = scan_receipt_image(image_bytes, file.content_type or "image/jpeg")
    except Exception as exc:
        failed = True
        parsed = ParsedReceipt(
            vendor_name="Unknown vendor",
            vendor_slug=None,
            store_name=None,
            store_address=None,
            cvr=None,
            purchased_at=None,
            register_no=None,
            invoice_no=None,
            payment_method=None,
            total_ore=0,
            vat_ore=0,
            barcode=None,
            cashier=None,
            warnings=[f"Local OCR failed ({exc}). Flagged for training."],
        )
        raw = {"ocr_engine": "tesseract", "error": str(exc)}

    vendor = _vendor_for(db, parsed)
    receipt = Receipt(
        status="draft",
        needs_training=failed,
        image_path=str(dest),
        image_content_type=file.content_type,
        raw_parse=raw,
        vendor_name=parsed.vendor_name,
        total_ore=parsed.total_ore,
        vat_ore=parsed.vat_ore,
    )
    _apply_parsed(receipt, parsed, vendor)
    receipt.needs_training = failed
    merged = dict(receipt.raw_parse or {})
    if isinstance(raw, dict):
        if raw.get("ocr_text"):
            merged["ocr_text"] = raw["ocr_text"]
        merged["ocr_engine"] = raw.get("ocr_engine", "tesseract")
        if raw.get("error"):
            merged["error"] = raw["error"]
    receipt.raw_parse = merged
    db.add(receipt)
    db.commit()
    receipt = _get_receipt(db, receipt.id)
    return to_read(receipt, parsed.warnings)


@router.get("", response_model=list[ReceiptRead])
def list_receipts(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
    tag_id: UUID | None = None,
    vendor: str | None = None,
    q: str | None = None,
    day: date | None = None,
    include_drafts: bool = False,
    needs_training: bool | None = None,
) -> list[ReceiptRead]:
    stmt = select(Receipt).options(*RECEIPT_LOAD)
    if needs_training is True:
        stmt = stmt.where(Receipt.needs_training.is_(True))
        include_drafts = True
    if not include_drafts:
        stmt = stmt.where(Receipt.status == "saved")
    if tag_id:
        stmt = stmt.where(Receipt.tags.any(Tag.id == tag_id))
    if vendor:
        stmt = stmt.where(Receipt.vendor_name.ilike(f"%{vendor}%"))
    if day:
        start = datetime(day.year, day.month, day.day, tzinfo=COPENHAGEN)
        end = start.replace(hour=23, minute=59, second=59, microsecond=999999)
        stmt = stmt.where(Receipt.purchased_at >= start, Receipt.purchased_at <= end)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            or_(
                Receipt.vendor_name.ilike(like),
                Receipt.store_name.ilike(like),
                Receipt.invoice_no.ilike(like),
                Receipt.lines.any(ReceiptLine.description.ilike(like)),
                Receipt.lines.any(ReceiptLine.item_number.ilike(like)),
            )
        )
    stmt = stmt.order_by(Receipt.purchased_at.desc().nullslast(), Receipt.created_at.desc())
    return [to_read(receipt) for receipt in db.scalars(stmt).unique().all()]


@router.get("/{receipt_id}", response_model=ReceiptRead)
def get_receipt(
    receipt_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> ReceiptRead:
    return to_read(_get_receipt(db, receipt_id))


@router.get("/{receipt_id}/image")
def receipt_image(
    receipt_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> FileResponse:
    receipt = _get_receipt(db, receipt_id)
    if not receipt.image_path or not Path(receipt.image_path).is_file():
        raise HTTPException(status_code=404, detail="No image stored for this receipt")
    return FileResponse(
        receipt.image_path,
        media_type=receipt.image_content_type or "image/jpeg",
        filename=Path(receipt.image_path).name,
    )


@router.patch("/{receipt_id}", response_model=ReceiptRead)
def update_receipt(
    receipt_id: UUID,
    payload: ReceiptWrite,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> ReceiptRead:
    receipt = _get_receipt(db, receipt_id)
    fields = payload.model_dump(exclude_unset=True)
    tag_ids = fields.pop("tag_ids", None)
    lines = fields.pop("lines", None)
    for key, value in fields.items():
        setattr(receipt, key, value)
    if lines is not None:
        replace_lines(receipt, payload.lines or [])
    set_tags(db, receipt, tag_ids)
    apply_verification(receipt)
    db.commit()
    return to_read(_get_receipt(db, receipt.id))


@router.delete("/{receipt_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_receipt(
    receipt_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> None:
    receipt = _get_receipt(db, receipt_id)
    if receipt.image_path:
        Path(receipt.image_path).unlink(missing_ok=True)
    db.delete(receipt)
    db.commit()


@router.post("/{receipt_id}/lookup-products", response_model=ReceiptRead)
def lookup_products(
    receipt_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> ReceiptRead:
    receipt = _get_receipt(db, receipt_id)
    vendor = receipt.vendor
    if vendor is None or vendor.slug != "harald-nyborg":
        raise HTTPException(
            status_code=400,
            detail="Product lookup is available for Harald Nyborg receipts in this version",
        )
    lookup_receipt_products(db, receipt.id, vendor)
    return to_read(_get_receipt(db, receipt.id))


