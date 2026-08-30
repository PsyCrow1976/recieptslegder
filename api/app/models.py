import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Vendor(Base):
    __tablename__ = "vendors"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    cvr: Mapped[str | None] = mapped_column(String(20))
    base_url: Mapped[str | None] = mapped_column(String(500))
    product_url_template: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    products: Mapped[list["Product"]] = relationship(back_populates="vendor")
    receipts: Mapped[list["Receipt"]] = relationship(back_populates="vendor")


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    color: Mapped[str] = mapped_column(String(20), default="#c2410c", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    receipts: Mapped[list["Receipt"]] = relationship(secondary="receipt_tags", back_populates="tags")


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (UniqueConstraint("vendor_id", "item_number", name="uq_product_vendor_item"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vendor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("vendors.id"), nullable=False)
    item_number: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str | None] = mapped_column(String(400))
    url: Mapped[str | None] = mapped_column(String(1000))
    image_url: Mapped[str | None] = mapped_column(String(1000))
    last_web_price_ore: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default="found", nullable=False)
    last_fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    vendor: Mapped["Vendor"] = relationship(back_populates="products")


class ReceiptTag(Base):
    __tablename__ = "receipt_tags"

    receipt_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("receipts.id", ondelete="CASCADE"), primary_key=True
    )
    tag_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)


class Receipt(Base):
    __tablename__ = "receipts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vendor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("vendors.id"))
    vendor_name: Mapped[str] = mapped_column(String(200), nullable=False)
    store_name: Mapped[str | None] = mapped_column(String(200))
    store_address: Mapped[str | None] = mapped_column(String(400))
    cvr: Mapped[str | None] = mapped_column(String(20))
    purchased_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    register_no: Mapped[str | None] = mapped_column(String(20))
    invoice_no: Mapped[str | None] = mapped_column(String(50))
    payment_method: Mapped[str | None] = mapped_column(String(50))
    total_ore: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    vat_ore: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    barcode: Mapped[str | None] = mapped_column(String(80))
    cashier: Mapped[str | None] = mapped_column(String(100))
    image_path: Mapped[str | None] = mapped_column(String(500))
    image_content_type: Mapped[str | None] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False)
    lines_sum_ok: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    vat_ok: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    raw_parse: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    vendor: Mapped["Vendor | None"] = relationship(back_populates="receipts")
    lines: Mapped[list["ReceiptLine"]] = relationship(
        back_populates="receipt", cascade="all, delete-orphan", order_by="ReceiptLine.position"
    )
    tags: Mapped[list["Tag"]] = relationship(secondary="receipt_tags", back_populates="receipts")


class ReceiptLine(Base):
    __tablename__ = "receipt_lines"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    receipt_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("receipts.id", ondelete="CASCADE"), nullable=False
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    item_number: Mapped[str | None] = mapped_column(String(50))
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    description: Mapped[str] = mapped_column(String(400), nullable=False, default="")
    line_total_ore: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    unit_price_ore: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    product_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("products.id"))

    receipt: Mapped["Receipt"] = relationship(back_populates="lines")
    product: Mapped["Product | None"] = relationship()
