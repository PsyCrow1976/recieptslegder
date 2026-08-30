from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    username: str
    password: str


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str
    is_admin: bool = False


class TagCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    color: str = Field(default="#c2410c", max_length=20)
    notes: str | None = None


class TagUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    color: str | None = Field(default=None, max_length=20)
    notes: str | None = None


class TagRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    color: str
    notes: str | None
    created_at: datetime


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    item_number: str
    title: str | None
    url: str | None
    image_url: str | None
    last_web_price_ore: int | None
    status: str
    last_fetched_at: datetime | None


class ReceiptLineWrite(BaseModel):
    item_number: str | None = None
    quantity: int = 1
    description: str = ""
    line_total_ore: int


class ReceiptLineRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    position: int
    item_number: str | None
    quantity: int
    description: str
    line_total_ore: int
    unit_price_ore: int
    product: ProductRead | None = None


class ReceiptWrite(BaseModel):
    vendor_name: str | None = None
    store_name: str | None = None
    store_address: str | None = None
    cvr: str | None = None
    purchased_at: datetime | None = None
    register_no: str | None = None
    invoice_no: str | None = None
    payment_method: str | None = None
    total_ore: int | None = None
    vat_ore: int | None = None
    barcode: str | None = None
    cashier: str | None = None
    notes: str | None = None
    status: str | None = None
    tag_ids: list[UUID] | None = None
    lines: list[ReceiptLineWrite] | None = None


class ReceiptRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    vendor_id: UUID | None
    vendor_name: str
    store_name: str | None
    store_address: str | None
    cvr: str | None
    purchased_at: datetime | None
    register_no: str | None
    invoice_no: str | None
    payment_method: str | None
    total_ore: int
    vat_ore: int
    barcode: str | None
    cashier: str | None
    status: str
    lines_sum_ok: bool
    vat_ok: bool
    notes: str | None
    created_at: datetime
    lines: list[ReceiptLineRead]
    tags: list[TagRead]
    warnings: list[str] = []
    image_url: str | None = None


class TagSpend(BaseModel):
    tag: TagRead
    receipt_count: int
    total_ore: int


class DashboardSummary(BaseModel):
    this_month_ore: int
    all_time_ore: int
    receipt_count: int
    by_tag: list[TagSpend]
    by_vendor: list[dict]


class CalendarDay(BaseModel):
    date: str
    receipt_count: int
    total_ore: int
    receipts: list[ReceiptRead]
