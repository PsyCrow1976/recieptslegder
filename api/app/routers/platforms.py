from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.auth import get_current_user
from app.database import get_db
from app.models import Account, Platform, PlatformKind
from app.schemas import PlatformRead, PlatformUpdate, PlatformWrite
from app.services import platform_read

router = APIRouter(prefix="/platforms", tags=["platforms"], dependencies=[Depends(get_current_user)])


def _kind(value: str) -> PlatformKind:
    try:
        return PlatformKind(value)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid platform kind") from exc


@router.get("", response_model=list[PlatformRead])
def list_platforms(db: Annotated[Session, Depends(get_db)]) -> list[PlatformRead]:
    platforms = db.scalars(select(Platform).options(selectinload(Platform.accounts)).order_by(Platform.name)).all()
    return [platform_read(p) for p in platforms]


@router.post("", response_model=PlatformRead, status_code=status.HTTP_201_CREATED)
def create_platform(payload: PlatformWrite, db: Annotated[Session, Depends(get_db)]) -> PlatformRead:
    existing = db.scalar(select(Platform).where(func.lower(Platform.name) == payload.name.strip().lower()))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A platform with that name already exists")
    platform = Platform(
        name=payload.name.strip(),
        kind=_kind(payload.kind),
        website=payload.website,
        color=payload.color,
        notes=payload.notes,
    )
    db.add(platform)
    db.commit()
    db.refresh(platform)
    return platform_read(platform, account_count=0)


@router.patch("/{platform_id}", response_model=PlatformRead)
def update_platform(
    platform_id: UUID, payload: PlatformUpdate, db: Annotated[Session, Depends(get_db)]
) -> PlatformRead:
    platform = db.scalar(select(Platform).options(selectinload(Platform.accounts)).where(Platform.id == platform_id))
    if not platform:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Platform not found")
    if payload.name is not None:
        name = payload.name.strip()
        clash = db.scalar(
            select(Platform).where(func.lower(Platform.name) == name.lower(), Platform.id != platform_id)
        )
        if clash:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A platform with that name already exists")
        platform.name = name
    if payload.kind is not None:
        platform.kind = _kind(payload.kind)
    if payload.website is not None:
        platform.website = payload.website
    if payload.color is not None:
        platform.color = payload.color
    if payload.notes is not None:
        platform.notes = payload.notes
    db.commit()
    db.refresh(platform)
    return platform_read(platform)


@router.delete("/{platform_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_platform(platform_id: UUID, db: Annotated[Session, Depends(get_db)]) -> None:
    platform = db.get(Platform, platform_id)
    if not platform:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Platform not found")
    count = db.scalar(select(func.count()).select_from(Account).where(Account.platform_id == platform_id))
    if count:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete a platform that still has accounts",
        )
    db.delete(platform)
    db.commit()
