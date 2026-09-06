from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

PlatformKind = Literal["bank", "investment", "other"]


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


class PersonWrite(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    color: str = Field(default="#0f766e", max_length=20)
    notes: str | None = None


class PersonUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    color: str | None = Field(default=None, max_length=20)
    notes: str | None = None


class PersonRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    color: str
    notes: str | None
    created_at: datetime


class PlatformWrite(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    kind: PlatformKind = "bank"
    website: str | None = None
    color: str = Field(default="#1e3a5f", max_length=20)
    notes: str | None = None


class PlatformUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    kind: PlatformKind | None = None
    website: str | None = None
    color: str | None = Field(default=None, max_length=20)
    notes: str | None = None


class PlatformRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    kind: PlatformKind
    website: str | None
    color: str
    notes: str | None
    created_at: datetime
    account_count: int = 0


class VendorWrite(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    website: str | None = None
    notes: str | None = None


class VendorUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    website: str | None = None
    notes: str | None = None


class VendorRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    website: str | None
    notes: str | None
    created_at: datetime


class CategoryWrite(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    color: str = Field(default="#0f766e", max_length=20)
    notes: str | None = None


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    color: str | None = Field(default=None, max_length=20)
    notes: str | None = None


class CategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    color: str
    notes: str | None
    created_at: datetime


class AccountWrite(BaseModel):
    platform_id: UUID
    name: str = Field(min_length=1, max_length=200)
    account_number: str | None = None
    currency: str = Field(default="DKK", min_length=3, max_length=3)
    opening_balance_ore: int = 0
    owner_ids: list[UUID] = Field(min_length=1)
    notes: str | None = None


class AccountUpdate(BaseModel):
    platform_id: UUID | None = None
    name: str | None = Field(default=None, min_length=1, max_length=200)
    account_number: str | None = None
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    opening_balance_ore: int | None = None
    owner_ids: list[UUID] | None = Field(default=None, min_length=1)
    notes: str | None = None


class AccountSummary(BaseModel):
    id: UUID
    name: str
    account_number: str | None
    currency: str
    opening_balance_ore: int
    balance_ore: int
    notes: str | None
    created_at: datetime
    platform: PlatformRead
    owners: list[PersonRead]
    movement_count: int = 0


class MovementItemWrite(BaseModel):
    description: str = Field(default="", max_length=400)
    vendor_id: UUID | None = None
    vendor_name: str | None = None
    product_url: str | None = None
    amount_ore: int
    quantity: int = Field(default=1, ge=1)


class MovementItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    position: int
    description: str
    vendor: VendorRead | None = None
    product_url: str | None
    amount_ore: int
    quantity: int


class AttachmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    original_filename: str
    content_type: str
    size_bytes: int
    created_at: datetime


class MovementWrite(BaseModel):
    account_id: UUID
    posted_on: date
    amount_ore: int | None = None
    description: str = Field(default="", max_length=400)
    vendor_id: UUID | None = None
    vendor_name: str | None = None
    category_ids: list[UUID] = []
    notes: str | None = None
    items: list[MovementItemWrite] = []


class MovementUpdate(BaseModel):
    account_id: UUID | None = None
    posted_on: date | None = None
    amount_ore: int | None = None
    description: str | None = Field(default=None, max_length=400)
    vendor_id: UUID | None = None
    vendor_name: str | None = None
    category_ids: list[UUID] | None = None
    notes: str | None = None
    items: list[MovementItemWrite] | None = None


class AccountBrief(BaseModel):
    id: UUID
    name: str
    currency: str
    platform_name: str
    platform_kind: PlatformKind


class MovementRead(BaseModel):
    id: UUID
    account_id: UUID
    posted_on: date
    amount_ore: int
    description: str
    notes: str | None
    created_at: datetime
    updated_at: datetime
    vendor: VendorRead | None
    categories: list[CategoryRead]
    items: list[MovementItemRead]
    attachments: list[AttachmentRead]
    items_sum_ore: int
    items_sum_ok: bool
    account: AccountBrief


class PersonBalance(BaseModel):
    person: PersonRead
    sole_balance_ore: int
    shared_balance_ore: int
    account_count: int


class CategorySpend(BaseModel):
    category: CategoryRead
    movement_count: int
    total_ore: int


class ImportMatch(BaseModel):
    id: UUID
    name: str
    score: float
    kind: str


class ImportPreviewRow(BaseModel):
    line_number: int
    import_key: str
    posted_on: date | None
    amount_ore: int | None
    name: str
    description: str
    label: str
    currency: str
    status: Literal["new", "duplicate", "skipped"]
    skip_reason: str | None = None
    existing_movement_id: UUID | None = None
    vendor_text: str
    vendor_exists: bool
    vendor_match: ImportMatch | None = None
    category_match: ImportMatch | None = None
    suggested_vendor_name: str
    suggested_vendor_id: UUID | None = None
    suggested_category_id: UUID | None = None


class ImportPreview(BaseModel):
    filename: str
    detected_account_number: str | None
    suggested_account_id: UUID | None
    row_count: int
    new_count: int
    duplicate_count: int
    skipped_count: int
    rows: list[ImportPreviewRow]


class ImportCommitRow(BaseModel):
    import_key: str
    posted_on: date
    amount_ore: int
    description: str = ""
    vendor_id: UUID | None = None
    vendor_name: str | None = None
    category_ids: list[UUID] = []


class ImportCommitRequest(BaseModel):
    account_id: UUID
    rows: list[ImportCommitRow]


class ImportCommitResult(BaseModel):
    created: int
    skipped_duplicate: int
    skipped_missing: int


class Dashboard(BaseModel):
    household_balance_ore: int
    this_month_in_ore: int
    this_month_out_ore: int
    movement_count: int
    account_count: int
    people_count: int
    platform_count: int
    accounts: list[AccountSummary]
    by_person: list[PersonBalance]
    by_category: list[CategorySpend]
    recent: list[MovementRead]
