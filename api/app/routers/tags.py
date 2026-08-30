from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Receipt, ReceiptTag, Tag, User
from app.schemas import TagCreate, TagRead, TagSpend, TagUpdate

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("", response_model=list[TagRead])
def list_tags(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> list[Tag]:
    return list(db.scalars(select(Tag).order_by(Tag.name)))


@router.post("", response_model=TagRead, status_code=status.HTTP_201_CREATED)
def create_tag(
    payload: TagCreate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> Tag:
    existing = db.scalar(select(Tag).where(func.lower(Tag.name) == payload.name.lower()))
    if existing:
        raise HTTPException(status_code=400, detail="A tag with that name already exists")
    tag = Tag(name=payload.name.strip(), color=payload.color, notes=payload.notes)
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag


@router.patch("/{tag_id}", response_model=TagRead)
def update_tag(
    tag_id: UUID,
    payload: TagUpdate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> Tag:
    tag = db.get(Tag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    if payload.name is not None:
        clash = db.scalar(
            select(Tag).where(func.lower(Tag.name) == payload.name.lower(), Tag.id != tag_id)
        )
        if clash:
            raise HTTPException(status_code=400, detail="A tag with that name already exists")
        tag.name = payload.name.strip()
    if payload.color is not None:
        tag.color = payload.color
    if payload.notes is not None:
        tag.notes = payload.notes
    db.commit()
    db.refresh(tag)
    return tag


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tag(
    tag_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> None:
    tag = db.get(Tag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    db.delete(tag)
    db.commit()


@router.get("/{tag_id}/spend", response_model=TagSpend)
def tag_spend(
    tag_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> TagSpend:
    tag = db.get(Tag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    row = db.execute(
        select(func.count(Receipt.id), func.coalesce(func.sum(Receipt.total_ore), 0))
        .join(ReceiptTag, ReceiptTag.receipt_id == Receipt.id)
        .where(ReceiptTag.tag_id == tag_id, Receipt.status == "saved")
    ).one()
    return TagSpend(tag=tag, receipt_count=int(row[0]), total_ore=int(row[1]))
