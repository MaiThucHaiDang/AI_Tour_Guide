"""SQLAlchemy ORM models for travel blog posts and comments."""

from __future__ import annotations

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class BlogPost(Base):
    __tablename__ = "blog_posts"
    __table_args__ = (
        CheckConstraint(
            "source_type IN ('seed', 'external', 'user')",
            name="ck_blog_posts_source_type",
        ),
        CheckConstraint(
            "status IN ('draft', 'pending', 'published')",
            name="ck_blog_posts_status",
        ),
    )

    post_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(180), nullable=False, unique=True, index=True)
    title: Mapped[str] = mapped_column(String(220), nullable=False, index=True)
    excerpt: Mapped[str] = mapped_column(String(420), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    cover_image: Mapped[str] = mapped_column(String(600), nullable=False)
    cover_alt: Mapped[str] = mapped_column(String(260), nullable=False)
    author_name: Mapped[str] = mapped_column(String(120), nullable=False)
    author_avatar: Mapped[str | None] = mapped_column(String(600))
    source_type: Mapped[str] = mapped_column(String(20), nullable=False, default="user")
    source_name: Mapped[str | None] = mapped_column(String(180))
    source_url: Mapped[str | None] = mapped_column(String(700))
    tags: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    published_at = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    created_at = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    reading_time: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    likes_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    comments_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    bookmarks_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="published", index=True)

    comments = relationship(
        "BlogComment",
        back_populates="post",
        cascade="all, delete-orphan",
        order_by="BlogComment.created_at",
    )


class BlogComment(Base):
    __tablename__ = "blog_comments"

    comment_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("blog_posts.post_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    author_name: Mapped[str] = mapped_column(String(120), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    post = relationship("BlogPost", back_populates="comments")
