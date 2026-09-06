from __future__ import annotations

import enum
import uuid
from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PlatformKind(str, enum.Enum):
    BANK = "bank"
    INVESTMENT = "investment"
    OTHER = "other"


class LoginUser(Base):
    """App sign-in (household admin). Separate from people who own accounts."""

    __tablename__ = "login_users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Person(Base):
    __tablename__ = "people"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    color: Mapped[str] = mapped_column(String(20), default="#0f766e", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    accounts: Mapped[list[Account]] = relationship(
        secondary="account_owners", back_populates="owners"
    )


class Platform(Base):
    __tablename__ = "platforms"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    kind: Mapped[PlatformKind] = mapped_column(
        Enum(
            PlatformKind,
            name="platform_kind",
            values_callable=lambda items: [i.value for i in items],
            native_enum=True,
            create_constraint=False,
        ),
        nullable=False,
        default=PlatformKind.BANK,
    )
    website: Mapped[str | None] = mapped_column(String(500))
    color: Mapped[str] = mapped_column(String(20), default="#1e3a5f", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    accounts: Mapped[list[Account]] = relationship(back_populates="platform")


class AccountOwner(Base):
    __tablename__ = "account_owners"

    account_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE"), primary_key=True
    )
    person_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("people.id", ondelete="CASCADE"), primary_key=True
    )


class Account(Base):
    __tablename__ = "accounts"
    __table_args__ = (UniqueConstraint("platform_id", "name", name="uq_account_platform_name"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    platform_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("platforms.id", ondelete="RESTRICT"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    account_number: Mapped[str | None] = mapped_column(String(80))
    currency: Mapped[str] = mapped_column(String(3), default="DKK", nullable=False)
    opening_balance_ore: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    platform: Mapped[Platform] = relationship(back_populates="accounts")
    owners: Mapped[list[Person]] = relationship(
        secondary="account_owners", back_populates="accounts"
    )
    movements: Mapped[list[Movement]] = relationship(
        back_populates="account", cascade="all, delete-orphan"
    )


class Vendor(Base):
    __tablename__ = "vendors"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    website: Mapped[str | None] = mapped_column(String(500))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    color: Mapped[str] = mapped_column(String(20), default="#0f766e", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MovementCategory(Base):
    __tablename__ = "movement_categories"

    movement_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("movements.id", ondelete="CASCADE"), primary_key=True
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True
    )


class Movement(Base):
    __tablename__ = "movements"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    posted_on: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    amount_ore: Mapped[int] = mapped_column(BigInteger, nullable=False)
    description: Mapped[str] = mapped_column(String(400), default="", nullable=False)
    vendor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("vendors.id", ondelete="SET NULL"))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    account: Mapped[Account] = relationship(back_populates="movements")
    vendor: Mapped[Vendor | None] = relationship()
    categories: Mapped[list[Category]] = relationship(secondary="movement_categories")
    items: Mapped[list[MovementItem]] = relationship(
        back_populates="movement", cascade="all, delete-orphan", order_by="MovementItem.position"
    )
    attachments: Mapped[list[Attachment]] = relationship(
        back_populates="movement", cascade="all, delete-orphan"
    )


class MovementItem(Base):
    __tablename__ = "movement_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    movement_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("movements.id", ondelete="CASCADE"), nullable=False, index=True
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    description: Mapped[str] = mapped_column(String(400), nullable=False, default="")
    vendor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("vendors.id", ondelete="SET NULL"))
    product_url: Mapped[str | None] = mapped_column(String(2000))
    amount_ore: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    movement: Mapped[Movement] = relationship(back_populates="items")
    vendor: Mapped[Vendor | None] = relationship()


class Attachment(Base):
    __tablename__ = "attachments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    movement_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("movements.id", ondelete="CASCADE"), nullable=False, index=True
    )
    original_filename: Mapped[str] = mapped_column(String(400), nullable=False)
    stored_path: Mapped[str] = mapped_column(String(600), nullable=False)
    content_type: Mapped[str] = mapped_column(String(120), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    movement: Mapped[Movement] = relationship(back_populates="attachments")
