"""created a new column sessions_name in sessions table and moved the data from session_place there

Revision ID: 40560afc74d8
Revises: 
Create Date: 2025-05-20 21:22:29.665457

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from datetime import datetime
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '40560afc74d8'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("sessions", sa.Column('session_name', sa.String(), nullable=True))
    op.execute("UPDATE sessions SET session_name = session_place")
    op.drop_column('sessions', 'session_place')

def downgrade() -> None:
    op.add_column("sessions", sa.Column('session_place', sa.String(), nullable=True))
    op.execute("UPDATE sessions SET session_place = session_name")
    op.drop_column('sessions', 'session_name')
