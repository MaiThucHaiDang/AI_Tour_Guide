"""Add knowledge graph tables (artifact_relations, knowledge_facts, artifact_faqs).

Revision ID: 0004_add_knowledge_graph
Revises: 0003_add_lat_lng
Create Date: 2026-06-03
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


revision = "0004_add_knowledge_graph"
down_revision = "0003_add_lat_lng"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create pgvector extension if not exists
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    
    # Create knowledge_facts table
    op.create_table(
        "knowledge_facts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("artifact_id", sa.Integer(), nullable=False),
        sa.Column("fact_text", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["artifact_id"], ["artifacts.art_id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create artifact_faqs table
    op.create_table(
        "artifact_faqs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("artifact_id", sa.Integer(), nullable=False),
        sa.Column("fact_id", sa.Integer(), nullable=True),
        sa.Column("question_text", sa.String(length=500), nullable=False),
        sa.Column("embedding", Vector(768), nullable=True),
        sa.ForeignKeyConstraint(["artifact_id"], ["artifacts.art_id"]),
        sa.ForeignKeyConstraint(["fact_id"], ["knowledge_facts.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create artifact_relations table
    op.create_table(
        "artifact_relations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("source_artifact_id", sa.Integer(), nullable=False),
        sa.Column("target_artifact_id", sa.Integer(), nullable=False),
        sa.Column("relation_type", sa.String(length=50), nullable=False),
        sa.Column("weight", sa.Float(), server_default="1.0", nullable=False),
        sa.ForeignKeyConstraint(["source_artifact_id"], ["artifacts.art_id"]),
        sa.ForeignKeyConstraint(["target_artifact_id"], ["artifacts.art_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    
    # Create indexes
    op.create_index(
        op.f("ix_knowledge_facts_artifact_id"),
        "knowledge_facts",
        ["artifact_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_artifact_faqs_artifact_id"),
        "artifact_faqs",
        ["artifact_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_artifact_faqs_fact_id"),
        "artifact_faqs",
        ["fact_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_artifact_relations_source"),
        "artifact_relations",
        ["source_artifact_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_artifact_relations_target"),
        "artifact_relations",
        ["target_artifact_id"],
        unique=False,
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index(
        op.f("ix_artifact_relations_target"),
        table_name="artifact_relations",
    )
    op.drop_index(
        op.f("ix_artifact_relations_source"),
        table_name="artifact_relations",
    )
    op.drop_index(
        op.f("ix_artifact_faqs_fact_id"),
        table_name="artifact_faqs",
    )
    op.drop_index(
        op.f("ix_artifact_faqs_artifact_id"),
        table_name="artifact_faqs", 
    )
    op.drop_index(
        op.f("ix_knowledge_facts_artifact_id"),
        table_name="knowledge_facts",
    )

    # Drop tables
    op.drop_table("artifact_relations")
    op.drop_table("artifact_faqs")
    op.drop_table("knowledge_facts")
