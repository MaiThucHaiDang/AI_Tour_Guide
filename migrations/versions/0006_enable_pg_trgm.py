"""Enable pg_trgm for fuzzy artifact search.

Revision ID: 0006_enable_pg_trgm
Revises: 1b35fba3832a
Create Date: 2026-06-18
"""

from __future__ import annotations

from alembic import op


revision = "0006_enable_pg_trgm"
down_revision = "1b35fba3832a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")


def downgrade() -> None:
    op.execute("DROP EXTENSION IF EXISTS pg_trgm")
