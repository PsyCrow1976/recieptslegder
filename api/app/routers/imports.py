from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.import_match import (
    account_number_matches,
    best_category_match,
    best_vendor_match,
    suggested_vendor_name,
    vendor_texts,
)
from app.models import Account, Category, Movement, Vendor
from app.nordea_csv import detected_account_number, parse_nordea_csv
from app.schemas import (
    ImportCommitRequest,
    ImportCommitResult,
    ImportMatch,
    ImportPreview,
    ImportPreviewRow,
)
from app.services import get_or_create_vendor, load_categories

router = APIRouter(prefix="/imports", tags=["imports"], dependencies=[Depends(get_current_user)])


def _match_schema(match) -> ImportMatch | None:
    if not match:
        return None
    return ImportMatch(id=UUID(match.id), name=match.name, score=match.score, kind=match.kind)


@router.post("/preview", response_model=ImportPreview)
async def preview_csv(
    db: Annotated[Session, Depends(get_db)],
    file: UploadFile = File(...),
    account_id: UUID | None = Form(default=None),
) -> ImportPreview:
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The CSV file is empty")
    try:
        parsed = parse_nordea_csv(raw)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    accounts = list(db.scalars(select(Account)).all())
    vendors = list(db.scalars(select(Vendor).order_by(Vendor.name)).all())
    categories = list(db.scalars(select(Category).order_by(Category.name)).all())
    detected = detected_account_number(parsed)
    suggested_account_id = None
    for account in accounts:
        if account_number_matches(account.account_number, detected):
            suggested_account_id = account.id
            break

    chosen_account_id = account_id or suggested_account_id
    existing_keys: dict[str, UUID] = {}
    if chosen_account_id:
        for movement in db.scalars(
            select(Movement).where(Movement.account_id == chosen_account_id, Movement.import_key.is_not(None))
        ).all():
            if movement.import_key:
                existing_keys[movement.import_key] = movement.id

    rows: list[ImportPreviewRow] = []
    new_count = duplicate_count = skipped_count = 0
    for item in parsed:
        vendor_match = best_vendor_match(item, vendors) if not item.skip_reason else None
        category_match = best_category_match(item, categories) if not item.skip_reason else None
        vendor_text = (vendor_texts(item) or [item.label])[0]
        suggested_name = suggested_vendor_name(item)
        vendor_exists = bool(vendor_match and vendor_match.kind == "exact")
        if item.skip_reason:
            status_name = "skipped"
            skipped_count += 1
            existing_id = None
        elif item.import_key in existing_keys:
            status_name = "duplicate"
            duplicate_count += 1
            existing_id = existing_keys[item.import_key]
        else:
            status_name = "new"
            new_count += 1
            existing_id = None
        rows.append(
            ImportPreviewRow(
                line_number=item.line_number,
                import_key=item.import_key,
                posted_on=item.posted_on,
                amount_ore=item.amount_ore,
                name=item.name,
                description=item.description,
                label=item.label,
                currency=item.currency,
                status=status_name,  # type: ignore[arg-type]
                skip_reason=item.skip_reason,
                existing_movement_id=existing_id,
                vendor_text=vendor_text,
                vendor_exists=vendor_exists,
                vendor_match=_match_schema(vendor_match),
                category_match=_match_schema(category_match),
                suggested_vendor_name=suggested_name,
                suggested_vendor_id=UUID(vendor_match.id) if vendor_match else None,
                suggested_category_id=UUID(category_match.id) if category_match else None,
            )
        )

    return ImportPreview(
        filename=file.filename or "statement.csv",
        detected_account_number=detected,
        suggested_account_id=suggested_account_id,
        row_count=len(rows),
        new_count=new_count,
        duplicate_count=duplicate_count,
        skipped_count=skipped_count,
        rows=rows,
    )


@router.post("/commit", response_model=ImportCommitResult)
def commit_import(payload: ImportCommitRequest, db: Annotated[Session, Depends(get_db)]) -> ImportCommitResult:
    account = db.get(Account, payload.account_id)
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

    existing = set(
        db.scalars(
            select(Movement.import_key).where(
                Movement.account_id == payload.account_id, Movement.import_key.is_not(None)
            )
        ).all()
    )
    created = skipped_duplicate = skipped_missing = 0
    for row in payload.rows:
        if not row.posted_on or row.amount_ore is None:
            skipped_missing += 1
            continue
        if row.import_key in existing:
            skipped_duplicate += 1
            continue
        vendor = get_or_create_vendor(db, row.vendor_id, row.vendor_name)
        movement = Movement(
            account_id=payload.account_id,
            posted_on=row.posted_on,
            amount_ore=row.amount_ore,
            description=(row.description or "").strip()[:400],
            vendor_id=vendor.id if vendor else None,
            import_key=row.import_key,
            notes="Imported from Nordea CSV",
            categories=load_categories(db, row.category_ids),
        )
        db.add(movement)
        existing.add(row.import_key)
        created += 1
    db.commit()
    return ImportCommitResult(created=created, skipped_duplicate=skipped_duplicate, skipped_missing=skipped_missing)
