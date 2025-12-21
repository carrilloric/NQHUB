"""add_zone_fields_to_liquidity_pools

Revision ID: 806a6254ad87
Revises: 8f06482e1048
Create Date: 2025-12-11 19:56:16.489935

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '806a6254ad87'
down_revision: Union[str, None] = '8f06482e1048'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add zone_low and zone_high columns to detected_liquidity_pools
    # These fields will be NULL for session levels (point levels)
    # and populated for EQH/EQL pools (zones)
    op.add_column('detected_liquidity_pools', sa.Column('zone_low', sa.Float(), nullable=True))
    op.add_column('detected_liquidity_pools', sa.Column('zone_high', sa.Float(), nullable=True))


def downgrade() -> None:
    # Remove zone fields
    op.drop_column('detected_liquidity_pools', 'zone_high')
    op.drop_column('detected_liquidity_pools', 'zone_low')
