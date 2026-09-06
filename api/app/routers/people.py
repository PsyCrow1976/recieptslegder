from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import AccountOwner, LoginUser, Person
from app.schemas import PersonRead, PersonUpdate, PersonWrite
from app.services import person_read

router = APIRouter(prefix="/people", tags=["people"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[PersonRead])
def list_people(db: Annotated[Session, Depends(get_db)]) -> list[PersonRead]:
    people = db.scalars(select(Person).order_by(Person.name)).all()
    return [person_read(p) for p in people]


@router.post("", response_model=PersonRead, status_code=status.HTTP_201_CREATED)
def create_person(payload: PersonWrite, db: Annotated[Session, Depends(get_db)]) -> PersonRead:
    existing = db.scalar(select(Person).where(func.lower(Person.name) == payload.name.strip().lower()))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A person with that name already exists")
    person = Person(name=payload.name.strip(), color=payload.color, notes=payload.notes)
    db.add(person)
    db.commit()
    db.refresh(person)
    return person_read(person)


@router.patch("/{person_id}", response_model=PersonRead)
def update_person(
    person_id: UUID, payload: PersonUpdate, db: Annotated[Session, Depends(get_db)]
) -> PersonRead:
    person = db.get(Person, person_id)
    if not person:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person not found")
    if payload.name is not None:
        name = payload.name.strip()
        clash = db.scalar(
            select(Person).where(func.lower(Person.name) == name.lower(), Person.id != person_id)
        )
        if clash:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A person with that name already exists")
        person.name = name
    if payload.color is not None:
        person.color = payload.color
    if payload.notes is not None:
        person.notes = payload.notes
    db.commit()
    db.refresh(person)
    return person_read(person)


@router.delete("/{person_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_person(
    person_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    _user: Annotated[LoginUser, Depends(get_current_user)],
) -> None:
    person = db.get(Person, person_id)
    if not person:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person not found")
    owned = db.scalars(select(AccountOwner.account_id).where(AccountOwner.person_id == person_id)).all()
    for account_id in owned:
        owner_count = db.scalar(
            select(func.count()).select_from(AccountOwner).where(AccountOwner.account_id == account_id)
        )
        if owner_count == 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete this person while they are the only owner of an account",
            )
    db.delete(person)
    db.commit()
