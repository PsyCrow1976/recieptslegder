"""Account start amount date.

Revision ID: 003
Revises: 002
Create Date: 2026-09-06

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("accounts", sa.Column("opening_on", sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column("accounts", "opening_on")
