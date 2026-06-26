"""add_artifact_ratings

Revision ID: 8a2c4e71f9b0
Revises: 5420e63231b1
Create Date: 2026-06-26 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8a2c4e71f9b0"
down_revision: Union[str, None] = "5420e63231b1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "artifact_ratings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("artifact_id", sa.Integer(), nullable=False),
        sa.Column("artifact_name", sa.String(length=255), nullable=False),
        sa.Column("service_rating", sa.Integer(), nullable=False),
        sa.Column("scenery_rating", sa.Integer(), nullable=False),
        sa.Column("price_rating", sa.Integer(), nullable=False),
        sa.Column("review", sa.Text(), nullable=True),
        sa.Column("customer_name", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["artifact_id"], ["artifacts.art_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_artifact_ratings_artifact_id"), "artifact_ratings", ["artifact_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_artifact_ratings_artifact_id"), table_name="artifact_ratings")
    op.drop_table("artifact_ratings")
