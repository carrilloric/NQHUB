"""add_risk_config_jsonb_to_bot_instances

Revision ID: c5939ce3671f
Revises: 6ab4e7cd259c
Create Date: 2026-03-29 20:08:38.643950

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c5939ce3671f'
down_revision: Union[str, None] = '6ab4e7cd259c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add risk_config JSONB column to bot_instances table
    op.add_column('bot_instances',
        sa.Column('risk_config', postgresql.JSONB(astext_type=sa.Text()), nullable=True)
    )


def downgrade() -> None:
    # Remove risk_config column from bot_instances table
    op.drop_column('bot_instances', 'risk_config')
