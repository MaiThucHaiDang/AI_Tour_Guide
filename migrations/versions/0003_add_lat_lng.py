"""Add latitude and longitude to locations and artifacts.

Revision ID: 0003_add_lat_lng
Revises: 0002_feedback_events
Create Date: 2026-05-31
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0003_add_lat_lng"
down_revision = "0002_feedback_events"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add latitude and longitude to locations
    op.add_column("locations", sa.Column("latitude", sa.Float(), nullable=True))
    op.add_column("locations", sa.Column("longitude", sa.Float(), nullable=True))
    
    # Add latitude and longitude to artifacts
    op.add_column("artifacts", sa.Column("latitude", sa.Float(), nullable=True))
    op.add_column("artifacts", sa.Column("longitude", sa.Float(), nullable=True))


def downgrade() -> None:
    # Remove latitude and longitude from artifacts
    op.drop_column("artifacts", "longitude")
    op.drop_column("artifacts", "latitude")
    
    # Remove latitude and longitude from locations
    op.drop_column("locations", "longitude")
    op.drop_column("locations", "latitude")
