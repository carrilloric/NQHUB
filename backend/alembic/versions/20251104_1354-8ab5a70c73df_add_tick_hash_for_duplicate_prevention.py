"""add tick_hash for duplicate prevention

Revision ID: 8ab5a70c73df
Revises: f1a8f69db2a6
Create Date: 2025-11-04 13:54:44.648648

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8ab5a70c73df'
down_revision: Union[str, None] = 'f1a8f69db2a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add tick_hash column for duplicate prevention.

    This allows us to:
    1. Generate a unique hash for each tick based on its content
    2. Prevent duplicate ticks from being inserted
    3. Maintain data integrity when re-processing files
    """
    # Add tick_hash column (nullable initially to allow migration of existing data)
    op.add_column('market_data_ticks',
        sa.Column('tick_hash', sa.String(32), nullable=True)
    )

    # Create index for better performance on lookups
    # NOT unique initially to allow for migration
    op.create_index('idx_tick_hash', 'market_data_ticks', ['tick_hash'])

    # Note: In production, you would want to:
    # 1. Backfill tick_hash for existing records
    # 2. Make the column NOT NULL
    # 3. Add UNIQUE constraint
    # But for now, we'll handle duplicates at the application level with ON CONFLICT


def downgrade() -> None:
    """Remove tick_hash column and its index."""
    # Drop the index first
    op.drop_index('idx_tick_hash', table_name='market_data_ticks')

    # Drop the column
    op.drop_column('market_data_ticks', 'tick_hash')