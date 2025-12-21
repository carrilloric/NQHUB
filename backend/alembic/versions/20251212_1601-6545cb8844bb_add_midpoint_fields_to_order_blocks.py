"""add_midpoint_fields_to_order_blocks

Revision ID: 6545cb8844bb
Revises: 806a6254ad87
Create Date: 2025-12-12 16:01:17.570443

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6545cb8844bb'
down_revision: Union[str, None] = '806a6254ad87'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add midpoint columns
    op.add_column('detected_order_blocks', sa.Column('ob_body_midpoint', sa.Float(), nullable=True))
    op.add_column('detected_order_blocks', sa.Column('ob_range_midpoint', sa.Float(), nullable=True))

    # Calculate values for existing records
    op.execute("""
        UPDATE detected_order_blocks
        SET
            ob_body_midpoint = (ob_open + ob_close) / 2.0,
            ob_range_midpoint = (ob_high + ob_low) / 2.0
    """)

    # Make columns NOT NULL after populating
    op.alter_column('detected_order_blocks', 'ob_body_midpoint', nullable=False)
    op.alter_column('detected_order_blocks', 'ob_range_midpoint', nullable=False)


def downgrade() -> None:
    # Remove midpoint columns
    op.drop_column('detected_order_blocks', 'ob_range_midpoint')
    op.drop_column('detected_order_blocks', 'ob_body_midpoint')
