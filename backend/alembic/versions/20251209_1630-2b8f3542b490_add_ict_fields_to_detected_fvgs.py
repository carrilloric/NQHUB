"""add_ict_fields_to_detected_fvgs

Revision ID: 2b8f3542b490
Revises: b8b739263c73
Create Date: 2025-12-09 16:30:32.192976

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2b8f3542b490'
down_revision: Union[str, None] = 'b8b739263c73'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add ICT-specific fields to detected_fvgs table
    op.add_column('detected_fvgs', sa.Column('premium_level', sa.Double(), nullable=True))
    op.add_column('detected_fvgs', sa.Column('discount_level', sa.Double(), nullable=True))
    op.add_column('detected_fvgs', sa.Column('consequent_encroachment', sa.Double(), nullable=True))
    op.add_column('detected_fvgs', sa.Column('displacement_score', sa.Double(), nullable=True))
    op.add_column('detected_fvgs', sa.Column('has_break_of_structure', sa.Boolean(), nullable=True, server_default='false'))

    # Update existing records to populate new fields from existing data
    # premium_level = fvg_end for BULLISH, fvg_start for BEARISH
    # discount_level = fvg_start for BULLISH, fvg_end for BEARISH
    # consequent_encroachment = midpoint
    op.execute("""
        UPDATE detected_fvgs
        SET
            premium_level = CASE
                WHEN fvg_type = 'BULLISH' THEN fvg_end
                WHEN fvg_type = 'BEARISH' THEN fvg_start
            END,
            discount_level = CASE
                WHEN fvg_type = 'BULLISH' THEN fvg_start
                WHEN fvg_type = 'BEARISH' THEN fvg_end
            END,
            consequent_encroachment = midpoint,
            displacement_score = 0.0,
            has_break_of_structure = false
    """)


def downgrade() -> None:
    # Remove ICT-specific fields
    op.drop_column('detected_fvgs', 'has_break_of_structure')
    op.drop_column('detected_fvgs', 'displacement_score')
    op.drop_column('detected_fvgs', 'consequent_encroachment')
    op.drop_column('detected_fvgs', 'discount_level')
    op.drop_column('detected_fvgs', 'premium_level')
