"""refactor children_count to children_paid_count and children_free_count

Revision ID: 5420e63231b1
Revises: 1006edd9653a
Create Date: 2026-06-21 09:07:34.370261
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision: str = '5420e63231b1'
down_revision: Union[str, None] = '1006edd9653a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('payments', sa.Column('children_paid_count', sa.Integer(), nullable=True))
    op.add_column('payments', sa.Column('children_free_count', sa.Integer(), nullable=True))
    op.execute("UPDATE payments SET children_paid_count = children_count, children_free_count = 0")
    op.alter_column('payments', 'children_paid_count', nullable=False)
    op.alter_column('payments', 'children_free_count', nullable=False)
    op.drop_column('payments', 'children_count')


def downgrade() -> None:
    op.add_column('payments', sa.Column('children_count', sa.INTEGER(), autoincrement=False, nullable=True))
    op.execute("UPDATE payments SET children_count = children_paid_count")
    op.alter_column('payments', 'children_count', nullable=False)
    op.drop_column('payments', 'children_free_count')
    op.drop_column('payments', 'children_paid_count')
