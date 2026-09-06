from datetime import date
from pathlib import Path
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.config import settings
from app.database import get_db
from app.models import Account, AccountOwner, Attachment, Movement, MovementCategory, MovementItem
from app.schemas import MovementRead, MovementUpdate, MovementWrite
from app.services import (
    get_or_create_vendor,
    load_categories,
    movement_query,
    movement_read,
    unlink_file,
)

router = APIRouter(prefix="/movements", tags=["movements"], dependencies=[Depends(get_current_user)])

MAX_UPLOAD_BYTES = 25 * 1024 * 1024
ALLOWED_PREFIXES = ("image/",)
ALLOWED_TYPES = {
    "application/pdf",
    "text/plain",
    "text/csv",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}


def _load_movement(db: Session, movement_id: UUID) -> Movement:
    movement = db.scalars(movement_query().where(Movement.id == movement_id)).unique().first()
    if not movement:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found")
    return movement


def _apply_items(db: Session, movement: Movement, items: list) -> int | None:
    movement.items.clear()
    db.flush()
    total = 0
    for position, item in enumerate(items):
        vendor = get_or_create_vendor(db, item.vendor_id, item.vendor_name)
        movement.items.append(
            MovementItem(
                position=position,
                description=(item.description or "").strip(),
                vendor_id=vendor.id if vendor else None,
                product_url=(item.product_url or "").strip() or None,
                amount_ore=item.amount_ore,
                quantity=item.quantity,
            )
        )
        total += item.amount_ore
    return total if items else None


def _require_account(db: Session, account_id: UUID) -> Account:
    account = db.get(Account, account_id)
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    return account


@router.get("", response_model=list[MovementRead])
def list_movements(
    db: Annotated[Session, Depends(get_db)],
    account_id: UUID | None = None,
    person_id: UUID | None = None,
    category_id: UUID | None = None,
    vendor_id: UUID | None = None,
    q: str | None = None,
    posted_from: date | None = Query(default=None, alias="from"),
    posted_to: date | None = Query(default=None, alias="to"),
) -> list[MovementRead]:
    stmt = movement_query()
    if account_id:
        stmt = stmt.where(Movement.account_id == account_id)
    if vendor_id:
        stmt = stmt.where(Movement.vendor_id == vendor_id)
    if posted_from:
        stmt = stmt.where(Movement.posted_on >= posted_from)
    if posted_to:
        stmt = stmt.where(Movement.posted_on <= posted_to)
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(Movement.description.ilike(like))
    if category_id:
        stmt = stmt.join(MovementCategory).where(MovementCategory.category_id == category_id)
    if person_id:
        stmt = stmt.join(AccountOwner, AccountOwner.account_id == Movement.account_id).where(
            AccountOwner.person_id == person_id
        )
    stmt = stmt.order_by(Movement.posted_on.desc(), Movement.created_at.desc()).limit(5000)
    movements = db.scalars(stmt).unique().all()
    return [movement_read(m) for m in movements]


@router.get("/{movement_id}", response_model=MovementRead)
def get_movement(movement_id: UUID, db: Annotated[Session, Depends(get_db)]) -> MovementRead:
    return movement_read(_load_movement(db, movement_id))


@router.post("", response_model=MovementRead, status_code=status.HTTP_201_CREATED)
def create_movement(payload: MovementWrite, db: Annotated[Session, Depends(get_db)]) -> MovementRead:
    _require_account(db, payload.account_id)
    vendor = get_or_create_vendor(db, payload.vendor_id, payload.vendor_name)
    movement = Movement(
        account_id=payload.account_id,
        posted_on=payload.posted_on,
        amount_ore=payload.amount_ore or 0,
        description=payload.description.strip(),
        vendor_id=vendor.id if vendor else None,
        notes=payload.notes,
        categories=load_categories(db, payload.category_ids),
    )
    db.add(movement)
    db.flush()
    items_total = _apply_items(db, movement, payload.items)
    if items_total is not None and payload.amount_ore is None:
        movement.amount_ore = items_total
    elif payload.amount_ore is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Amount is required")
    db.commit()
    return movement_read(_load_movement(db, movement.id))


@router.patch("/{movement_id}", response_model=MovementRead)
def update_movement(
    movement_id: UUID, payload: MovementUpdate, db: Annotated[Session, Depends(get_db)]
) -> MovementRead:
    movement = _load_movement(db, movement_id)
    if payload.account_id is not None:
        _require_account(db, payload.account_id)
        movement.account_id = payload.account_id
    if payload.posted_on is not None:
        movement.posted_on = payload.posted_on
    if payload.description is not None:
        movement.description = payload.description.strip()
    if payload.notes is not None:
        movement.notes = payload.notes
    if payload.vendor_id is not None or payload.vendor_name is not None:
        vendor = get_or_create_vendor(db, payload.vendor_id, payload.vendor_name)
        movement.vendor_id = vendor.id if vendor else None
    if payload.category_ids is not None:
        movement.categories = load_categories(db, payload.category_ids)
    if payload.items is not None:
        items_total = _apply_items(db, movement, payload.items)
        if items_total is not None and payload.amount_ore is None:
            movement.amount_ore = items_total
    if payload.amount_ore is not None:
        movement.amount_ore = payload.amount_ore
    db.commit()
    return movement_read(_load_movement(db, movement_id))


@router.delete("/{movement_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_movement(movement_id: UUID, db: Annotated[Session, Depends(get_db)]) -> None:
    movement = _load_movement(db, movement_id)
    for attachment in list(movement.attachments):
        unlink_file(attachment.stored_path)
    db.delete(movement)
    db.commit()


@router.post("/{movement_id}/attachments", response_model=MovementRead)
async def upload_attachments(
    movement_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    files: list[UploadFile] = File(...),
) -> MovementRead:
    movement = _load_movement(db, movement_id)
    storage = Path(settings.document_storage_path) / str(movement.id)
    storage.mkdir(parents=True, exist_ok=True)

    for upload in files:
        content_type = upload.content_type or "application/octet-stream"
        if not (content_type in ALLOWED_TYPES or content_type.startswith(ALLOWED_PREFIXES)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type not allowed: {content_type}",
            )
        data = await upload.read()
        if len(data) > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File is larger than 25 MB")
        original = Path(upload.filename or "document").name
        stored_name = f"{uuid4().hex}_{original}"
        dest = storage / stored_name
        dest.write_bytes(data)
        movement.attachments.append(
            Attachment(
                original_filename=original,
                stored_path=str(dest),
                content_type=content_type,
                size_bytes=len(data),
            )
        )

    db.commit()
    return movement_read(_load_movement(db, movement_id))


@router.get("/{movement_id}/attachments/{attachment_id}/file")
def download_attachment(
    movement_id: UUID, attachment_id: UUID, db: Annotated[Session, Depends(get_db)]
) -> FileResponse:
    movement = _load_movement(db, movement_id)
    attachment = next((a for a in movement.attachments if a.id == attachment_id), None)
    if not attachment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found")
    path = Path(attachment.stored_path)
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File missing on disk")
    return FileResponse(path, media_type=attachment.content_type, filename=attachment.original_filename)


@router.delete("/{movement_id}/attachments/{attachment_id}", response_model=MovementRead)
def delete_attachment(
    movement_id: UUID, attachment_id: UUID, db: Annotated[Session, Depends(get_db)]
) -> MovementRead:
    movement = _load_movement(db, movement_id)
    attachment = next((a for a in movement.attachments if a.id == attachment_id), None)
    if not attachment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found")
    unlink_file(attachment.stored_path)
    db.delete(attachment)
    db.commit()
    return movement_read(_load_movement(db, movement_id))
