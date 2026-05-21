"""Add feedback events table.

Revision ID: 0002_feedback_events
Revises: 0001_initial_schema
Create Date: 2026-05-21
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0002_feedback_events"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "feedback_events",
        sa.Column("feedback_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("request_id", sa.String(length=64), nullable=True),
        sa.Column("session_id", sa.String(length=128), nullable=True),
        sa.Column("message_id", sa.String(length=128), nullable=True),
        sa.Column("artifact_id", sa.String(length=64), nullable=True),
        sa.Column("rating", sa.String(length=32), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("intent", sa.String(length=64), nullable=True),
        sa.Column("answer_source", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("feedback_id"),
    )
    op.create_index(op.f("ix_feedback_events_answer_source"), "feedback_events", ["answer_source"], unique=False)
    op.create_index(op.f("ix_feedback_events_artifact_id"), "feedback_events", ["artifact_id"], unique=False)
    op.create_index(op.f("ix_feedback_events_message_id"), "feedback_events", ["message_id"], unique=False)
    op.create_index(op.f("ix_feedback_events_rating"), "feedback_events", ["rating"], unique=False)
    op.create_index(op.f("ix_feedback_events_request_id"), "feedback_events", ["request_id"], unique=False)
    op.create_index(op.f("ix_feedback_events_session_id"), "feedback_events", ["session_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_feedback_events_session_id"), table_name="feedback_events")
    op.drop_index(op.f("ix_feedback_events_request_id"), table_name="feedback_events")
    op.drop_index(op.f("ix_feedback_events_rating"), table_name="feedback_events")
    op.drop_index(op.f("ix_feedback_events_message_id"), table_name="feedback_events")
    op.drop_index(op.f("ix_feedback_events_artifact_id"), table_name="feedback_events")
    op.drop_index(op.f("ix_feedback_events_answer_source"), table_name="feedback_events")
    op.drop_table("feedback_events")
