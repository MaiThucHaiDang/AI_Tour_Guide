"""add_payments_table

Revision ID: c6aa79ab0a97
Revises: 0007_update_blog_covers
Create Date: 2026-06-21 07:20:17.889307
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = 'c6aa79ab0a97'
down_revision: Union[str, None] = '0007_update_blog_covers'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('payments',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('order_code', sa.String(length=50), nullable=False),
    sa.Column('amount', sa.Integer(), nullable=False),
    sa.Column('location', sa.String(length=100), nullable=False),
    sa.Column('customer_name', sa.String(length=255), nullable=False),
    sa.Column('customer_email', sa.String(length=255), nullable=False),
    sa.Column('customer_phone', sa.String(length=20), nullable=False),
    sa.Column('ticket_quantity', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('vnpay_txn_ref', sa.String(length=100), nullable=True),
    sa.Column('vnpay_response_code', sa.String(length=10), nullable=True),
    sa.Column('vnpay_transaction_no', sa.String(length=50), nullable=True),
    sa.Column('vnpay_bank_code', sa.String(length=20), nullable=True),
    sa.Column('vnpay_pay_date', sa.String(length=30), nullable=True),
    sa.Column('vnpay_secure_hash', sa.String(length=256), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_payments_order_code'), 'payments', ['order_code'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_payments_order_code'), table_name='payments')
    op.drop_table('payments')
