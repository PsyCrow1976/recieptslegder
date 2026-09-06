from datetime import datetime
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.auth import get_current_user
from app.database import get_db
from app.models import Movement, Person, Platform
from app.schemas import CategorySpend, Dashboard, PersonBalance
from app.services import (
    account_balance_ore,
    account_query,
    account_summary,
    category_read,
    movement_query,
    movement_read,
    person_read,
)

router = APIRouter(tags=["dashboard"], dependencies=[Depends(get_current_user)])
TZ = ZoneInfo("Europe/Copenhagen")


@router.get("/dashboard", response_model=Dashboard)
def dashboard(db: Annotated[Session, Depends(get_db)]) -> Dashboard:
    accounts = list(db.scalars(account_query(db)).unique().all())
    summaries = [account_summary(a) for a in accounts]
    household = sum(s.balance_ore for s in summaries)

    today = datetime.now(TZ).date()
    month_start = today.replace(day=1)
    month_movements = list(
        db.scalars(
            select(Movement)
            .options(selectinload(Movement.categories))
            .where(Movement.posted_on >= month_start, Movement.posted_on <= today)
        )
        .unique()
        .all()
    )
    month_in = sum(m.amount_ore for m in month_movements if m.amount_ore > 0)
    month_out = sum(-m.amount_ore for m in month_movements if m.amount_ore < 0)

    people = list(db.scalars(select(Person).order_by(Person.name)).all())
    by_person: list[PersonBalance] = []
    for person in people:
        owned = [a for a in accounts if any(o.id == person.id for o in a.owners)]
        sole = 0
        shared = 0
        for account in owned:
            balance = account_balance_ore(account)
            if len(account.owners) == 1:
                sole += balance
            else:
                shared += balance
        by_person.append(
            PersonBalance(
                person=person_read(person),
                sole_balance_ore=sole,
                shared_balance_ore=shared,
                account_count=len(owned),
            )
        )

    category_totals: dict = {}
    for movement in month_movements:
        for category in movement.categories:
            bucket = category_totals.setdefault(category.id, {"category": category, "count": 0, "total": 0})
            bucket["count"] += 1
            bucket["total"] += movement.amount_ore
    by_category = [
        CategorySpend(category=category_read(b["category"]), movement_count=b["count"], total_ore=b["total"])
        for b in sorted(category_totals.values(), key=lambda x: abs(x["total"]), reverse=True)
    ]

    recent = list(
        db.scalars(movement_query().order_by(Movement.posted_on.desc(), Movement.created_at.desc()).limit(12))
        .unique()
        .all()
    )

    return Dashboard(
        household_balance_ore=household,
        this_month_in_ore=month_in,
        this_month_out_ore=month_out,
        movement_count=db.scalar(select(func.count()).select_from(Movement)) or 0,
        account_count=len(accounts),
        people_count=len(people),
        platform_count=db.scalar(select(func.count()).select_from(Platform)) or 0,
        accounts=summaries,
        by_person=by_person,
        by_category=by_category,
        recent=[movement_read(m) for m in recent],
    )
