"""add_last_checked_time_to_detected_fvgs

Revision ID: 8f06482e1048
Revises: 2b8f3542b490
Create Date: 2025-12-09 16:54:53.955975

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8f06482e1048'
down_revision: Union[str, None] = '2b8f3542b490'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add last_checked_time field to detected_fvgs
    op.add_column('detected_fvgs', sa.Column('last_checked_time', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    # Remove last_checked_time field
    op.drop_column('detected_fvgs', 'last_checked_time')
