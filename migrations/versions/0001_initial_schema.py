"""Initial AI Tour Guide schema.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-05-20
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "locations",
        sa.Column("loc_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name_vi", sa.String(length=255), nullable=False),
        sa.Column("name_en", sa.String(length=255), nullable=False),
        sa.Column("gps_coordinates", sa.String(length=100), nullable=True),
        sa.Column("open_hours", sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint("loc_id"),
    )

    op.create_table(
        "artifacts",
        sa.Column("art_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("loc_id", sa.Integer(), nullable=False),
        sa.Column("name_vi", sa.String(length=255), nullable=False),
        sa.Column("name_en", sa.String(length=255), nullable=False),
        sa.Column("history_text_vi", sa.Text(), nullable=False),
        sa.Column("history_text_en", sa.Text(), nullable=False),
        sa.Column("author", sa.String(length=255), nullable=True),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["loc_id"], ["locations.loc_id"]),
        sa.PrimaryKeyConstraint("art_id"),
        sa.UniqueConstraint("name_vi", name="uq_artifacts_name_vi"),
    )
    op.create_index(op.f("ix_artifacts_name_en"), "artifacts", ["name_en"], unique=False)
    op.create_index(op.f("ix_artifacts_name_vi"), "artifacts", ["name_vi"], unique=False)

    op.create_table(
        "bilingual_content",
        sa.Column("content_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("artifact_id", sa.Integer(), nullable=False),
        sa.Column("lang", sa.String(length=10), nullable=False),
        sa.Column("content_type", sa.String(length=50), nullable=False),
        sa.Column("content_text", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["artifact_id"], ["artifacts.art_id"]),
        sa.PrimaryKeyConstraint("content_id"),
        sa.UniqueConstraint(
            "artifact_id", "lang", "content_type", name="uq_bilingual_artifact_lang_type"
        ),
    )
    op.create_index(
        op.f("ix_bilingual_content_artifact_id"),
        "bilingual_content",
        ["artifact_id"],
        unique=False,
    )

    op.create_table(
        "precomputed_audio",
        sa.Column("audio_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("artifact_id", sa.Integer(), nullable=False),
        sa.Column("question_vi", sa.String(length=255), nullable=False),
        sa.Column("question_en", sa.String(length=255), nullable=False),
        sa.Column("answer_vi", sa.Text(), nullable=False),
        sa.Column("answer_en", sa.Text(), nullable=False),
        sa.Column("audio_vi", sa.String(length=255), nullable=True),
        sa.Column("audio_en", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(["artifact_id"], ["artifacts.art_id"]),
        sa.PrimaryKeyConstraint("audio_id"),
    )
    op.create_index(
        op.f("ix_precomputed_audio_artifact_id"),
        "precomputed_audio",
        ["artifact_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_precomputed_audio_artifact_id"), table_name="precomputed_audio")
    op.drop_table("precomputed_audio")
    op.drop_index(op.f("ix_bilingual_content_artifact_id"), table_name="bilingual_content")
    op.drop_table("bilingual_content")
    op.drop_index(op.f("ix_artifacts_name_vi"), table_name="artifacts")
    op.drop_index(op.f("ix_artifacts_name_en"), table_name="artifacts")
    op.drop_table("artifacts")
    op.drop_table("locations")
