"""Add import_key for CSV duplicate detection.

Revision ID: 002
Revises: 001
Create Date: 2026-09-06

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("movements", sa.Column("import_key", sa.String(64), nullable=True))
    op.create_index("ix_movements_import_key", "movements", ["import_key"])
    op.create_unique_constraint("uq_movement_account_import_key", "movements", ["account_id", "import_key"])


def downgrade() -> None:
    op.drop_constraint("uq_movement_account_import_key", "movements", type_="unique")
    op.drop_index("ix_movements_import_key", table_name="movements")
    op.drop_column("movements", "import_key")
