from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Account, Movement, Platform
from app.schemas import AccountSummary, AccountUpdate, AccountWrite
from app.services import account_query, account_summary, load_people, movement_query, unlink_file

router = APIRouter(prefix="/accounts", tags=["accounts"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[AccountSummary])
def list_accounts(db: Annotated[Session, Depends(get_db)]) -> list[AccountSummary]:
    accounts = db.scalars(account_query(db)).unique().all()
    return [account_summary(a) for a in accounts]


@router.get("/{account_id}", response_model=AccountSummary)
def get_account(account_id: UUID, db: Annotated[Session, Depends(get_db)]) -> AccountSummary:
    account = db.scalars(account_query(db).where(Account.id == account_id)).unique().first()
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    return account_summary(account)


@router.post("", response_model=AccountSummary, status_code=status.HTTP_201_CREATED)
def create_account(payload: AccountWrite, db: Annotated[Session, Depends(get_db)]) -> AccountSummary:
    platform = db.get(Platform, payload.platform_id)
    if not platform:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Platform not found")
    owners = load_people(db, payload.owner_ids)
    account = Account(
        platform_id=payload.platform_id,
        name=payload.name.strip(),
        account_number=(payload.account_number or "").strip() or None,
        currency=payload.currency.upper(),
        opening_balance_ore=payload.opening_balance_ore,
        notes=payload.notes,
        owners=owners,
    )
    db.add(account)
    db.commit()
    account = db.scalars(account_query(db).where(Account.id == account.id)).unique().one()
    return account_summary(account)


@router.patch("/{account_id}", response_model=AccountSummary)
def update_account(
    account_id: UUID, payload: AccountUpdate, db: Annotated[Session, Depends(get_db)]
) -> AccountSummary:
    account = db.scalars(account_query(db).where(Account.id == account_id)).unique().first()
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    if payload.platform_id is not None:
        platform = db.get(Platform, payload.platform_id)
        if not platform:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Platform not found")
        account.platform_id = payload.platform_id
    if payload.name is not None:
        account.name = payload.name.strip()
    if payload.account_number is not None:
        account.account_number = payload.account_number.strip() or None
    if payload.currency is not None:
        account.currency = payload.currency.upper()
    if payload.opening_balance_ore is not None:
        account.opening_balance_ore = payload.opening_balance_ore
    if payload.notes is not None:
        account.notes = payload.notes
    if payload.owner_ids is not None:
        account.owners = load_people(db, payload.owner_ids)
    db.commit()
    account = db.scalars(account_query(db).where(Account.id == account_id)).unique().one()
    return account_summary(account)


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(account_id: UUID, db: Annotated[Session, Depends(get_db)]) -> None:
    account = db.get(Account, account_id)
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    movements = db.scalars(movement_query().where(Movement.account_id == account_id)).unique().all()
    for movement in movements:
        for attachment in movement.attachments:
            unlink_file(attachment.stored_path)
        db.delete(movement)
    db.delete(account)
    db.commit()
