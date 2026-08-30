"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-08-30

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
    )
    op.create_table(
        "vendors",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("cvr", sa.String(length=20), nullable=True),
        sa.Column("base_url", sa.String(length=500), nullable=True),
        sa.Column("product_url_template", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_table(
        "tags",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("color", sa.String(length=20), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "products",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("vendor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("item_number", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=400), nullable=True),
        sa.Column("url", sa.String(length=1000), nullable=True),
        sa.Column("image_url", sa.String(length=1000), nullable=True),
        sa.Column("last_web_price_ore", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("last_fetched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["vendor_id"], ["vendors.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("vendor_id", "item_number", name="uq_product_vendor_item"),
    )
    op.create_table(
        "receipts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("vendor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("vendor_name", sa.String(length=200), nullable=False),
        sa.Column("store_name", sa.String(length=200), nullable=True),
        sa.Column("store_address", sa.String(length=400), nullable=True),
        sa.Column("cvr", sa.String(length=20), nullable=True),
        sa.Column("purchased_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("register_no", sa.String(length=20), nullable=True),
        sa.Column("invoice_no", sa.String(length=50), nullable=True),
        sa.Column("payment_method", sa.String(length=50), nullable=True),
        sa.Column("total_ore", sa.Integer(), nullable=False),
        sa.Column("vat_ore", sa.Integer(), nullable=False),
        sa.Column("barcode", sa.String(length=80), nullable=True),
        sa.Column("cashier", sa.String(length=100), nullable=True),
        sa.Column("image_path", sa.String(length=500), nullable=True),
        sa.Column("image_content_type", sa.String(length=80), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("lines_sum_ok", sa.Boolean(), nullable=False),
        sa.Column("vat_ok", sa.Boolean(), nullable=False),
        sa.Column("raw_parse", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["vendor_id"], ["vendors.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_receipts_purchased_at", "receipts", ["purchased_at"])
    op.create_index("ix_receipts_invoice_no", "receipts", ["invoice_no"])
    op.create_index("ix_receipts_status", "receipts", ["status"])
    op.create_table(
        "receipt_lines",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("receipt_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("item_number", sa.String(length=50), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("description", sa.String(length=400), nullable=False),
        sa.Column("line_total_ore", sa.Integer(), nullable=False),
        sa.Column("unit_price_ore", sa.Integer(), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["receipt_id"], ["receipts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_receipt_lines_item_number", "receipt_lines", ["item_number"])
    op.create_table(
        "receipt_tags",
        sa.Column("receipt_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tag_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["receipt_id"], ["receipts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tag_id"], ["tags.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("receipt_id", "tag_id"),
    )


def downgrade() -> None:
    op.drop_table("receipt_tags")
    op.drop_index("ix_receipt_lines_item_number", table_name="receipt_lines")
    op.drop_table("receipt_lines")
    op.drop_index("ix_receipts_status", table_name="receipts")
    op.drop_index("ix_receipts_invoice_no", table_name="receipts")
    op.drop_index("ix_receipts_purchased_at", table_name="receipts")
    op.drop_table("receipts")
    op.drop_table("products")
    op.drop_table("tags")
    op.drop_table("vendors")
    op.drop_table("users")
