"""add_bracket_id_to_orders

Revision ID: f041615105c9
Revises: c5939ce3671f
Create Date: 2026-03-30 10:52:43.237175

Adds bracket_id column to orders table to support bracket order tracking.
This allows matching entry/exit orders from the same bracket (entry + stop loss + take profit).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = 'f041615105c9'
down_revision: Union[str, None] = 'c5939ce3671f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add bracket_id column to orders table
    # This is nullable because existing orders won't have a bracket_id
    # For bracket orders, all orders (entry, stop loss, take profit) share the same bracket_id
    op.add_column(
        'orders',
        sa.Column('bracket_id', UUID(as_uuid=True), nullable=True)
    )

    # Add index for efficient bracket order lookups
    op.create_index('idx_orders_bracket', 'orders', ['bracket_id'])


def downgrade() -> None:
    # Remove index first
    op.drop_index('idx_orders_bracket', table_name='orders')

    # Remove bracket_id column
    op.drop_column('orders', 'bracket_id')
