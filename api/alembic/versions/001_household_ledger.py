"""Household ledger schema.

Revision ID: 001
Revises:
Create Date: 2026-09-06

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
    platform_kind = postgresql.ENUM("bank", "investment", "other", name="platform_kind", create_type=False)
    postgresql.ENUM("bank", "investment", "other", name="platform_kind").create(op.get_bind(), checkfirst=True)

    op.create_table(
        "login_users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("username", sa.String(100), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "people",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False, unique=True),
        sa.Column("color", sa.String(20), nullable=False, server_default="#0f766e"),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "platforms",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False, unique=True),
        sa.Column("kind", platform_kind, nullable=False),  # enum created above
        sa.Column("website", sa.String(500)),
        sa.Column("color", sa.String(20), nullable=False, server_default="#1e3a5f"),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "vendors",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False, unique=True),
        sa.Column("website", sa.String(500)),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("color", sa.String(20), nullable=False, server_default="#0f766e"),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("platform_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("platforms.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("account_number", sa.String(80)),
        sa.Column("currency", sa.String(3), nullable=False, server_default="DKK"),
        sa.Column("opening_balance_ore", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("platform_id", "name", name="uq_account_platform_name"),
    )
    op.create_table(
        "account_owners",
        sa.Column("account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("accounts.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("person_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people.id", ondelete="CASCADE"), primary_key=True),
    )
    op.create_table(
        "movements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("posted_on", sa.Date(), nullable=False),
        sa.Column("amount_ore", sa.BigInteger(), nullable=False),
        sa.Column("description", sa.String(400), nullable=False, server_default=""),
        sa.Column("vendor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("vendors.id", ondelete="SET NULL")),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_movements_account_id", "movements", ["account_id"])
    op.create_index("ix_movements_posted_on", "movements", ["posted_on"])
    op.create_table(
        "movement_categories",
        sa.Column("movement_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("movements.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True),
    )
    op.create_table(
        "movement_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("movement_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("movements.id", ondelete="CASCADE"), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("description", sa.String(400), nullable=False, server_default=""),
        sa.Column("vendor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("vendors.id", ondelete="SET NULL")),
        sa.Column("product_url", sa.String(2000)),
        sa.Column("amount_ore", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
    )
    op.create_index("ix_movement_items_movement_id", "movement_items", ["movement_id"])
    op.create_table(
        "attachments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("movement_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("movements.id", ondelete="CASCADE"), nullable=False),
        sa.Column("original_filename", sa.String(400), nullable=False),
        sa.Column("stored_path", sa.String(600), nullable=False),
        sa.Column("content_type", sa.String(120), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_attachments_movement_id", "attachments", ["movement_id"])


def downgrade() -> None:
    op.drop_table("attachments")
    op.drop_table("movement_items")
    op.drop_table("movement_categories")
    op.drop_table("movements")
    op.drop_table("account_owners")
    op.drop_table("accounts")
    op.drop_table("categories")
    op.drop_table("vendors")
    op.drop_table("platforms")
    op.drop_table("people")
    op.drop_table("login_users")
    postgresql.ENUM(name="platform_kind").drop(op.get_bind(), checkfirst=True)
