from calendar import monthrange
from datetime import date, datetime
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.auth import get_current_user
from app.database import get_db
from app.models import Receipt, ReceiptLine, ReceiptTag, Tag, User
from app.receipt_serialize import to_read
from app.schemas import CalendarDay, DashboardSummary, TagSpend

router = APIRouter(tags=["dashboard"])
COPENHAGEN = ZoneInfo("Europe/Copenhagen")


@router.get("/dashboard", response_model=DashboardSummary)
def dashboard(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> DashboardSummary:
    today = datetime.now(COPENHAGEN).date()
    month_start = datetime(today.year, today.month, 1, tzinfo=COPENHAGEN)

    saved = Receipt.status == "saved"
    all_time = db.execute(
        select(func.count(Receipt.id), func.coalesce(func.sum(Receipt.total_ore), 0)).where(saved)
    ).one()
    this_month = db.execute(
        select(func.coalesce(func.sum(Receipt.total_ore), 0)).where(saved, Receipt.purchased_at >= month_start)
    ).scalar_one()

    tag_rows = db.execute(
        select(Tag, func.count(Receipt.id), func.coalesce(func.sum(Receipt.total_ore), 0))
        .join(ReceiptTag, ReceiptTag.tag_id == Tag.id)
        .join(Receipt, Receipt.id == ReceiptTag.receipt_id)
        .where(Receipt.status == "saved")
        .group_by(Tag.id)
        .order_by(func.coalesce(func.sum(Receipt.total_ore), 0).desc())
    ).all()

    vendor_rows = db.execute(
        select(Receipt.vendor_name, func.count(Receipt.id), func.coalesce(func.sum(Receipt.total_ore), 0))
        .where(saved)
        .group_by(Receipt.vendor_name)
        .order_by(func.coalesce(func.sum(Receipt.total_ore), 0).desc())
    ).all()

    return DashboardSummary(
        this_month_ore=int(this_month or 0),
        all_time_ore=int(all_time[1] or 0),
        receipt_count=int(all_time[0] or 0),
        by_tag=[TagSpend(tag=tag, receipt_count=int(count), total_ore=int(total)) for tag, count, total in tag_rows],
        by_vendor=[
            {"vendor_name": name, "receipt_count": int(count), "total_ore": int(total)}
            for name, count, total in vendor_rows
        ],
    )


@router.get("/calendar", response_model=list[CalendarDay])
def calendar(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
    year: int = Query(...),
    month: int = Query(..., ge=1, le=12),
) -> list[CalendarDay]:
    start = datetime(year, month, 1, tzinfo=COPENHAGEN)
    last_day = monthrange(year, month)[1]
    end = datetime(year, month, last_day, 23, 59, 59, tzinfo=COPENHAGEN)
    receipts = list(
        db.scalars(
            select(Receipt)
            .options(
                selectinload(Receipt.lines).selectinload(ReceiptLine.product),
                selectinload(Receipt.tags),
            )
            .where(
                Receipt.status == "saved",
                Receipt.purchased_at >= start,
                Receipt.purchased_at <= end,
            )
            .order_by(Receipt.purchased_at)
        ).unique().all()
    )
    buckets: dict[date, list[Receipt]] = {}
    for receipt in receipts:
        if receipt.purchased_at is None:
            continue
        day = receipt.purchased_at.astimezone(COPENHAGEN).date()
        buckets.setdefault(day, []).append(receipt)

    days: list[CalendarDay] = []
    for day in range(1, last_day + 1):
        key = date(year, month, day)
        items = buckets.get(key, [])
        days.append(
            CalendarDay(
                date=key.isoformat(),
                receipt_count=len(items),
                total_ore=sum(item.total_ore for item in items),
                receipts=[to_read(item) for item in items],
            )
        )
    return days
