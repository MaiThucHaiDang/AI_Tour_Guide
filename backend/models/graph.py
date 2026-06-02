"""SQLAlchemy ORM models for the Knowledge Graph and Vector FAQ."""

from __future__ import annotations
from sqlalchemy import ForeignKey, Integer, String, Float, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
from core.database import Base


class KnowledgeFact(Base):
    """Stores atomic facts extracted from artifact history."""
    __tablename__ = "knowledge_facts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    artifact_id: Mapped[int] = mapped_column(Integer, ForeignKey("artifacts.art_id"), nullable=False)
    fact_text: Mapped[str] = mapped_column(Text, nullable=False)

    artifact = relationship("Artifact", backref="facts")


class ArtifactFAQ(Base):
    """Stores hypothetical questions (FAQ) for artifacts and their vector embeddings."""
    __tablename__ = "artifact_faqs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    artifact_id: Mapped[int] = mapped_column(Integer, ForeignKey("artifacts.art_id"), nullable=False)
    fact_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("knowledge_facts.id"), nullable=True)
    question_text: Mapped[str] = mapped_column(String(500), nullable=False)
    # Gemini text-embedding-004 produces 768-dimensional vectors
    embedding: Mapped[Vector] = mapped_column(Vector(768), nullable=True)

    artifact = relationship("Artifact", backref="faqs")
    fact = relationship("KnowledgeFact", backref="faqs")


class ArtifactRelation(Base):
    """Knowledge Graph edges: Defines relationships between artifacts."""
    __tablename__ = "artifact_relations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_artifact_id: Mapped[int] = mapped_column(Integer, ForeignKey("artifacts.art_id"), nullable=False)
    target_artifact_id: Mapped[int] = mapped_column(Integer, ForeignKey("artifacts.art_id"), nullable=False)
    relation_type: Mapped[str] = mapped_column(String(50), nullable=False) # e.g., "SAME_AUTHOR", "SAME_PERIOD", "LOCATED_NEAR"
    weight: Mapped[float] = mapped_column(Float, default=1.0)

    source = relationship("Artifact", foreign_keys=[source_artifact_id], backref="source_relations")
    target = relationship("Artifact", foreign_keys=[target_artifact_id], backref="target_relations")
