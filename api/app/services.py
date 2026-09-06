from pathlib import Path
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    Account,
    Category,
    Movement,
    MovementItem,
    Person,
    Platform,
    PlatformKind,
    Vendor,
)
from app.schemas import (
    AccountBrief,
    AccountSummary,
    AttachmentRead,
    CategoryRead,
    MovementItemRead,
    MovementRead,
    PersonRead,
    PlatformRead,
    VendorRead,
)


def person_read(person: Person) -> PersonRead:
    return PersonRead.model_validate(person)


def vendor_read(vendor: Vendor | None) -> VendorRead | None:
    return VendorRead.model_validate(vendor) if vendor else None


def category_read(category: Category) -> CategoryRead:
    return CategoryRead.model_validate(category)


def platform_read(platform: Platform, account_count: int | None = None) -> PlatformRead:
    data = PlatformRead.model_validate(platform)
    if account_count is not None:
        data.account_count = account_count
    else:
        data.account_count = len(platform.accounts) if platform.accounts is not None else 0
    return data


def account_balance_ore(account: Account) -> int:
    movements = account.movements or []
    return int(account.opening_balance_ore) + sum(m.amount_ore for m in movements)


def account_summary(account: Account) -> AccountSummary:
    return AccountSummary(
        id=account.id,
        name=account.name,
        account_number=account.account_number,
        currency=account.currency,
        opening_balance_ore=account.opening_balance_ore,
        balance_ore=account_balance_ore(account),
        notes=account.notes,
        created_at=account.created_at,
        platform=platform_read(account.platform, account_count=0),
        owners=[person_read(p) for p in account.owners],
        movement_count=len(account.movements or []),
    )


def movement_read(movement: Movement) -> MovementRead:
    items_sum = sum(item.amount_ore for item in movement.items)
    return MovementRead(
        id=movement.id,
        account_id=movement.account_id,
        posted_on=movement.posted_on,
        amount_ore=movement.amount_ore,
        description=movement.description,
        notes=movement.notes,
        created_at=movement.created_at,
        updated_at=movement.updated_at,
        vendor=vendor_read(movement.vendor),
        categories=[category_read(c) for c in movement.categories],
        items=[
            MovementItemRead(
                id=item.id,
                position=item.position,
                description=item.description,
                vendor=vendor_read(item.vendor),
                product_url=item.product_url,
                amount_ore=item.amount_ore,
                quantity=item.quantity,
            )
            for item in movement.items
        ],
        attachments=[AttachmentRead.model_validate(a) for a in movement.attachments],
        items_sum_ore=items_sum,
        items_sum_ok=len(movement.items) == 0 or items_sum == movement.amount_ore,
        account=AccountBrief(
            id=movement.account.id,
            name=movement.account.name,
            currency=movement.account.currency,
            platform_name=movement.account.platform.name,
            platform_kind=movement.account.platform.kind.value
            if isinstance(movement.account.platform.kind, PlatformKind)
            else str(movement.account.platform.kind),
        ),
    )


def get_or_create_vendor(
    db: Session, vendor_id: UUID | None, vendor_name: str | None
) -> Vendor | None:
    if vendor_id:
        vendor = db.get(Vendor, vendor_id)
        if not vendor:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found")
        return vendor
    name = (vendor_name or "").strip()
    if not name:
        return None
    existing = db.scalar(select(Vendor).where(Vendor.name.ilike(name)))
    if existing:
        return existing
    vendor = Vendor(name=name)
    db.add(vendor)
    db.flush()
    return vendor


def load_people(db: Session, ids: list[UUID]) -> list[Person]:
    if not ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one owner is required")
    people = list(db.scalars(select(Person).where(Person.id.in_(ids))).all())
    if len(people) != len(set(ids)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="One or more people were not found")
    order = {pid: i for i, pid in enumerate(ids)}
    people.sort(key=lambda p: order[p.id])
    return people


def load_categories(db: Session, ids: list[UUID]) -> list[Category]:
    if not ids:
        return []
    categories = list(db.scalars(select(Category).where(Category.id.in_(ids))).all())
    if len(categories) != len(set(ids)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="One or more categories were not found")
    return categories


def account_query(db: Session):
    return (
        select(Account)
        .options(
            selectinload(Account.platform),
            selectinload(Account.owners),
            selectinload(Account.movements),
        )
        .order_by(Account.name)
    )


def movement_query():
    return select(Movement).options(
        selectinload(Movement.vendor),
        selectinload(Movement.categories),
        selectinload(Movement.items).selectinload(MovementItem.vendor),
        selectinload(Movement.attachments),
        selectinload(Movement.account).selectinload(Account.platform),
        selectinload(Movement.account).selectinload(Account.owners),
    )


def unlink_file(path: str) -> None:
    file_path = Path(path)
    try:
        file_path.unlink(missing_ok=True)
    except OSError:
        pass
    parent = file_path.parent
    if parent.exists() and parent.is_dir() and not any(parent.iterdir()):
        try:
            parent.rmdir()
        except OSError:
            pass
