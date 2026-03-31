"""add_bracket_order_fields_to_orders

Revision ID: a1b2c3d4e5f6
Revises: c5939ce3671f
Create Date: 2026-03-31 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'c5939ce3671f'
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns for bracket orders
    op.add_column('orders', sa.Column('client_order_id', sa.String(length=100), nullable=True))
    op.add_column('orders', sa.Column('broker_order_id', sa.String(length=100), nullable=True))
    op.add_column('orders', sa.Column('order_type', sa.String(length=20), nullable=True))
    op.add_column('orders', sa.Column('bracket_role', sa.String(length=10), nullable=True))
    op.add_column('orders', sa.Column('parent_order_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('orders', sa.Column('contracts', sa.Integer(), nullable=True))
    op.add_column('orders', sa.Column('gross_pnl', sa.DECIMAL(precision=15, scale=2), nullable=True))
    op.add_column('orders', sa.Column('net_pnl', sa.DECIMAL(precision=15, scale=2), nullable=True))
    op.add_column('orders', sa.Column('commission', sa.DECIMAL(precision=10, scale=2), nullable=True))
    op.add_column('orders', sa.Column('rejection_reason', sa.Text(), nullable=True))
    op.add_column('orders', sa.Column('fill_time', sa.DateTime(timezone=True), nullable=True))
    op.add_column('orders', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True))

    # Copy data from old columns to new columns
    op.execute("UPDATE orders SET broker_order_id = rithmic_order_id WHERE rithmic_order_id IS NOT NULL")
    op.execute("UPDATE orders SET order_type = type WHERE type IS NOT NULL")
    op.execute("UPDATE orders SET contracts = quantity WHERE quantity IS NOT NULL")
    op.execute("UPDATE orders SET fill_time = filled_at WHERE filled_at IS NOT NULL")

    # Generate client_order_id for existing orders (bot_id + timestamp + random)
    op.execute("""
        UPDATE orders
        SET client_order_id = CONCAT(
            'ORD-',
            SUBSTRING(CAST(bot_id AS TEXT), 1, 8),
            '-',
            TO_CHAR(submitted_at, 'YYYYMMDDHH24MISS'),
            '-',
            SUBSTRING(MD5(RANDOM()::TEXT), 1, 6)
        )
        WHERE client_order_id IS NULL
    """)

    # Now make client_order_id NOT NULL and UNIQUE
    op.alter_column('orders', 'client_order_id', nullable=False)
    op.create_unique_constraint('uq_orders_client_order_id', 'orders', ['client_order_id'])

    # Create foreign key for parent_order_id
    op.create_foreign_key('fk_orders_parent_order_id', 'orders', 'orders', ['parent_order_id'], ['id'])

    # Create indices for new columns
    op.create_index('idx_orders_client_order_id', 'orders', ['client_order_id'])
    op.create_index('idx_orders_broker_order_id', 'orders', ['broker_order_id'])
    op.create_index('idx_orders_bracket_role', 'orders', ['bracket_role'])
    op.create_index('idx_orders_parent_order_id', 'orders', ['parent_order_id'])


def downgrade():
    # Drop indices
    op.drop_index('idx_orders_parent_order_id', table_name='orders')
    op.drop_index('idx_orders_bracket_role', table_name='orders')
    op.drop_index('idx_orders_broker_order_id', table_name='orders')
    op.drop_index('idx_orders_client_order_id', table_name='orders')

    # Drop foreign key
    op.drop_constraint('fk_orders_parent_order_id', 'orders', type_='foreignkey')

    # Drop unique constraint
    op.drop_constraint('uq_orders_client_order_id', 'orders', type_='unique')

    # Drop columns
    op.drop_column('orders', 'updated_at')
    op.drop_column('orders', 'fill_time')
    op.drop_column('orders', 'rejection_reason')
    op.drop_column('orders', 'commission')
    op.drop_column('orders', 'net_pnl')
    op.drop_column('orders', 'gross_pnl')
    op.drop_column('orders', 'contracts')
    op.drop_column('orders', 'parent_order_id')
    op.drop_column('orders', 'bracket_role')
    op.drop_column('orders', 'order_type')
    op.drop_column('orders', 'broker_order_id')
    op.drop_column('orders', 'client_order_id')
