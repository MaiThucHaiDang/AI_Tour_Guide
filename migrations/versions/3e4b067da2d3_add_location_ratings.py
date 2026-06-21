"""add_location_ratings

Revision ID: 3e4b067da2d3
Revises: c6aa79ab0a97
Create Date: 2026-06-21 07:51:25.073005
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = '3e4b067da2d3'
down_revision: Union[str, None] = 'c6aa79ab0a97'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('location_ratings',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('location_id', sa.Integer(), nullable=False),
    sa.Column('location_name', sa.String(length=255), nullable=False),
    sa.Column('service_rating', sa.Integer(), nullable=False),
    sa.Column('scenery_rating', sa.Integer(), nullable=False),
    sa.Column('price_rating', sa.Integer(), nullable=False),
    sa.Column('review', sa.Text(), nullable=True),
    sa.Column('customer_name', sa.String(length=100), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['location_id'], ['locations.loc_id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_location_ratings_location_id'), 'location_ratings', ['location_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_location_ratings_location_id'), table_name='location_ratings')
    op.drop_table('location_ratings')
