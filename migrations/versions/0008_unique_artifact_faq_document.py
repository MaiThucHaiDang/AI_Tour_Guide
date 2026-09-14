"""Deduplicate RAG documents and enforce stable index identity.

Revision ID: 0008_unique_faq_docs
Revises: 8a2c4e71f9b0
Create Date: 2026-09-14
"""

from __future__ import annotations

from alembic import op


revision = "0008_unique_faq_docs"
down_revision = "8a2c4e71f9b0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Keep the earliest embedded row for every deterministic document identity.
    # This also repairs databases populated by overlapping legacy indexer runs.
    op.execute(
        """
        DELETE FROM artifact_faqs
        WHERE id IN (
            SELECT id
            FROM (
                SELECT
                    id,
                    ROW_NUMBER() OVER (
                        PARTITION BY artifact_id, question_text
                        ORDER BY (embedding IS NOT NULL) DESC, id ASC
                    ) AS duplicate_rank
                FROM artifact_faqs
            ) ranked
            WHERE duplicate_rank > 1
        )
        """
    )
    op.create_unique_constraint(
        "uq_artifact_faq_document",
        "artifact_faqs",
        ["artifact_id", "question_text"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_artifact_faq_document",
        "artifact_faqs",
        type_="unique",
    )
