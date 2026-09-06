from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Vendor
from app.schemas import VendorRead, VendorUpdate, VendorWrite
from app.services import vendor_read

router = APIRouter(prefix="/vendors", tags=["vendors"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[VendorRead])
def list_vendors(db: Annotated[Session, Depends(get_db)]) -> list[VendorRead]:
    vendors = db.scalars(select(Vendor).order_by(Vendor.name)).all()
    return [vendor_read(v) for v in vendors if v]


@router.post("", response_model=VendorRead, status_code=status.HTTP_201_CREATED)
def create_vendor(payload: VendorWrite, db: Annotated[Session, Depends(get_db)]) -> VendorRead:
    existing = db.scalar(select(Vendor).where(func.lower(Vendor.name) == payload.name.strip().lower()))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A vendor with that name already exists")
    vendor = Vendor(name=payload.name.strip(), website=payload.website, notes=payload.notes)
    db.add(vendor)
    db.commit()
    db.refresh(vendor)
    return vendor_read(vendor)  # type: ignore[return-value]


@router.patch("/{vendor_id}", response_model=VendorRead)
def update_vendor(vendor_id: UUID, payload: VendorUpdate, db: Annotated[Session, Depends(get_db)]) -> VendorRead:
    vendor = db.get(Vendor, vendor_id)
    if not vendor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found")
    if payload.name is not None:
        name = payload.name.strip()
        clash = db.scalar(
            select(Vendor).where(func.lower(Vendor.name) == name.lower(), Vendor.id != vendor_id)
        )
        if clash:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A vendor with that name already exists")
        vendor.name = name
    if payload.website is not None:
        vendor.website = payload.website
    if payload.notes is not None:
        vendor.notes = payload.notes
    db.commit()
    db.refresh(vendor)
    return vendor_read(vendor)  # type: ignore[return-value]


@router.delete("/{vendor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vendor(vendor_id: UUID, db: Annotated[Session, Depends(get_db)]) -> None:
    vendor = db.get(Vendor, vendor_id)
    if not vendor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found")
    db.delete(vendor)
    db.commit()
