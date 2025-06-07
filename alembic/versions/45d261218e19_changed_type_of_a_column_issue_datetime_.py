"""changed type of a column issue_datetime to include timezone

Revision ID: 45d261218e19
Revises: ba6482e7c74c
Create Date: 2025-06-07 12:10:11.617371

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '45d261218e19'
down_revision: Union[str, None] = 'ba6482e7c74c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        'orders',
        'issue_datetime',
        existing_type=sa.DateTime(),
        type_=sa.DateTime(timezone=True),
        existing_nullable=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        'orders',
        'issue_datetime',
        existing_type=sa.DateTime(timezone=True),
        type_=sa.DateTime(),
        existing_nullable=True,
    )