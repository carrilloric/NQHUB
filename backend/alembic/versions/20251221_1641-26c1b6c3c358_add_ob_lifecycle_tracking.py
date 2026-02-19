"""add_ob_lifecycle_tracking

Revision ID: 26c1b6c3c358
Revises: eb92517323ec
Create Date: 2025-12-21 16:41:06.592222

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '26c1b6c3c358'
down_revision: Union[str, None] = 'eb92517323ec'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add lifecycle tracking fields to detected_order_blocks

    # Tracking fields for state update mechanism
    op.add_column('detected_order_blocks', sa.Column('last_checked_time', postgresql.TIMESTAMP(timezone=True), nullable=True))
    op.add_column('detected_order_blocks', sa.Column('last_checked_candle_time', postgresql.TIMESTAMP(timezone=True), nullable=True))

    # Test interaction tracking
    op.add_column('detected_order_blocks', sa.Column('test_count', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('detected_order_blocks', sa.Column('test_times', postgresql.ARRAY(postgresql.TIMESTAMP(timezone=True)), nullable=True))

    # Option 1: Edge touch (price touches OB boundary)
    op.add_column('detected_order_blocks', sa.Column('first_touch_edge_time', postgresql.TIMESTAMP(timezone=True), nullable=True))
    op.add_column('detected_order_blocks', sa.Column('first_touch_edge_price', sa.Float(), nullable=True))

    # Option 2: Midpoint touch (price reaches 50% level)
    op.add_column('detected_order_blocks', sa.Column('first_touch_midpoint_time', postgresql.TIMESTAMP(timezone=True), nullable=True))
    op.add_column('detected_order_blocks', sa.Column('first_touch_midpoint_price', sa.Float(), nullable=True))

    # Option 3: Entry without close (candle enters zone but doesn't close inside)
    op.add_column('detected_order_blocks', sa.Column('first_entry_no_close_time', postgresql.TIMESTAMP(timezone=True), nullable=True))
    op.add_column('detected_order_blocks', sa.Column('first_entry_candle_close', sa.Float(), nullable=True))

    # BROKEN state tracking
    op.add_column('detected_order_blocks', sa.Column('broken_time', postgresql.TIMESTAMP(timezone=True), nullable=True))
    op.add_column('detected_order_blocks', sa.Column('broken_candle_close', sa.Float(), nullable=True))

    # Penetration metrics
    op.add_column('detected_order_blocks', sa.Column('max_penetration_pts', sa.Float(), nullable=True, server_default='0.0'))
    op.add_column('detected_order_blocks', sa.Column('max_penetration_pct', sa.Float(), nullable=True, server_default='0.0'))

    # Set default values for existing records
    op.execute("""
        UPDATE detected_order_blocks
        SET
            test_count = 0,
            max_penetration_pts = 0.0,
            max_penetration_pct = 0.0
        WHERE test_count IS NULL
    """)

    # Make numeric fields NOT NULL after setting defaults
    op.alter_column('detected_order_blocks', 'test_count', nullable=False)
    op.alter_column('detected_order_blocks', 'max_penetration_pts', nullable=False)
    op.alter_column('detected_order_blocks', 'max_penetration_pct', nullable=False)


def downgrade() -> None:
    # Remove lifecycle tracking fields in reverse order
    op.drop_column('detected_order_blocks', 'max_penetration_pct')
    op.drop_column('detected_order_blocks', 'max_penetration_pts')
    op.drop_column('detected_order_blocks', 'broken_candle_close')
    op.drop_column('detected_order_blocks', 'broken_time')
    op.drop_column('detected_order_blocks', 'first_entry_candle_close')
    op.drop_column('detected_order_blocks', 'first_entry_no_close_time')
    op.drop_column('detected_order_blocks', 'first_touch_midpoint_price')
    op.drop_column('detected_order_blocks', 'first_touch_midpoint_time')
    op.drop_column('detected_order_blocks', 'first_touch_edge_price')
    op.drop_column('detected_order_blocks', 'first_touch_edge_time')
    op.drop_column('detected_order_blocks', 'test_times')
    op.drop_column('detected_order_blocks', 'test_count')
    op.drop_column('detected_order_blocks', 'last_checked_candle_time')
    op.drop_column('detected_order_blocks', 'last_checked_time')
