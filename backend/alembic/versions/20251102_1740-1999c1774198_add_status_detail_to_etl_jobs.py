"""add_status_detail_to_etl_jobs

Revision ID: 1999c1774198
Revises: d207e6ad07eb
Create Date: 2025-11-02 17:40:00.368820

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1999c1774198'
down_revision: Union[str, None] = 'd207e6ad07eb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add status_detail column to etl_jobs table
    op.add_column('etl_jobs', sa.Column('status_detail', sa.String(500), nullable=True))


def downgrade() -> None:
    # Remove status_detail column
    op.drop_column('etl_jobs', 'status_detail')
