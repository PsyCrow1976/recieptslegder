from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Category
from app.schemas import CategoryRead, CategoryUpdate, CategoryWrite
from app.services import category_read

router = APIRouter(prefix="/categories", tags=["categories"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[CategoryRead])
def list_categories(db: Annotated[Session, Depends(get_db)]) -> list[CategoryRead]:
    categories = db.scalars(select(Category).order_by(Category.name)).all()
    return [category_read(c) for c in categories]


@router.post("", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(payload: CategoryWrite, db: Annotated[Session, Depends(get_db)]) -> CategoryRead:
    existing = db.scalar(select(Category).where(func.lower(Category.name) == payload.name.strip().lower()))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A category with that name already exists")
    category = Category(name=payload.name.strip(), color=payload.color, notes=payload.notes)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category_read(category)


@router.patch("/{category_id}", response_model=CategoryRead)
def update_category(
    category_id: UUID, payload: CategoryUpdate, db: Annotated[Session, Depends(get_db)]
) -> CategoryRead:
    category = db.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    if payload.name is not None:
        name = payload.name.strip()
        clash = db.scalar(
            select(Category).where(func.lower(Category.name) == name.lower(), Category.id != category_id)
        )
        if clash:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A category with that name already exists")
        category.name = name
    if payload.color is not None:
        category.color = payload.color
    if payload.notes is not None:
        category.notes = payload.notes
    db.commit()
    db.refresh(category)
    return category_read(category)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: UUID, db: Annotated[Session, Depends(get_db)]) -> None:
    category = db.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    db.delete(category)
    db.commit()
