"""Travel blog API router."""

from __future__ import annotations

import logging
import math
import re
import unicodedata
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.database import get_db_session
from core.observability import increment
from models.blog import BlogComment, BlogPost
from schemas.blog import (
    ALLOWED_BLOG_TAGS,
    BlogCommentCreate,
    BlogCommentResponse,
    BlogDetailResponse,
    BlogInteractionRequest,
    BlogInteractionResponse,
    BlogListResponse,
    BlogPostCreate,
)

router = APIRouter(prefix="/api/v1/blog-posts", tags=["Blog"])
_LOGGER = logging.getLogger(__name__)


def _estimate_reading_time(content: str) -> int:
    word_count = len(re.findall(r"\S+", content or ""))
    return max(1, math.ceil(word_count / 220))


def _slugify(title: str) -> str:
    normalized = title.replace("Đ", "D").replace("đ", "d")
    normalized = unicodedata.normalize("NFKD", normalized)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii").lower()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text).strip("-")
    return (slug or "bai-viet")[:140].strip("-") or "bai-viet"


def _safe_datetime(value) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.now(timezone.utc)


async def _build_unique_slug(db: AsyncSession, title: str) -> str:
    base_slug = _slugify(title)
    slug = base_slug
    suffix = 2
    while True:
        result = await db.execute(select(BlogPost.post_id).where(BlogPost.slug == slug))
        if result.scalar_one_or_none() is None:
            return slug
        slug = f"{base_slug}-{suffix}"
        suffix += 1


def _comment_to_response(comment: BlogComment) -> dict:
    return {
        "id": comment.comment_id,
        "post_id": comment.post_id,
        "author_name": comment.author_name,
        "content": comment.content,
        "created_at": _safe_datetime(comment.created_at),
    }


def _post_to_summary(post: BlogPost) -> dict:
    return {
        "id": post.post_id,
        "slug": post.slug,
        "title": post.title,
        "excerpt": post.excerpt,
        "cover_image": post.cover_image,
        "cover_alt": post.cover_alt,
        "author_name": post.author_name,
        "source_type": post.source_type,
        "source_name": post.source_name,
        "source_url": post.source_url,
        "tags": post.tags or [],
        "created_at": _safe_datetime(post.created_at),
        "updated_at": _safe_datetime(post.updated_at),
        "published_at": post.published_at,
        "reading_time": max(1, post.reading_time or _estimate_reading_time(post.content)),
        "likes_count": max(0, post.likes_count or 0),
        "comments_count": max(0, post.comments_count or 0),
        "bookmarks_count": max(0, post.bookmarks_count or 0),
        "status": post.status,
    }


def _post_to_detail(post: BlogPost) -> dict:
    detail = _post_to_summary(post)
    detail["content"] = post.content
    detail["comments"] = [_comment_to_response(comment) for comment in (post.comments or [])]
    return detail


async def _get_published_post(db: AsyncSession, slug: str, *, with_comments: bool = False) -> BlogPost:
    stmt = select(BlogPost).where(BlogPost.slug == slug, BlogPost.status == "published")
    if with_comments:
        stmt = stmt.options(selectinload(BlogPost.comments))
    result = await db.execute(stmt)
    post = result.scalar_one_or_none()
    if post is None:
        raise HTTPException(status_code=404, detail="Blog post not found.")
    return post


@router.get("", response_model=BlogListResponse)
async def list_blog_posts(
    search: str | None = Query(default=None, max_length=120),
    tag: str | None = Query(default=None, max_length=40),
    limit: int = Query(default=12, ge=1, le=60),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db_session),
) -> BlogListResponse:
    filters = [BlogPost.status == "published"]

    if search and search.strip():
        pattern = f"%{search.strip()}%"
        filters.append(
            or_(
                BlogPost.title.ilike(pattern),
                BlogPost.excerpt.ilike(pattern),
                BlogPost.content.ilike(pattern),
            )
        )

    if tag and tag.strip():
        cleaned_tag = tag.strip()
        if cleaned_tag not in ALLOWED_BLOG_TAGS:
            raise HTTPException(status_code=400, detail="Unsupported blog tag.")
        filters.append(BlogPost.tags.contains([cleaned_tag]))

    total_result = await db.execute(select(func.count()).select_from(BlogPost).where(*filters))
    total = int(total_result.scalar_one() or 0)

    stmt = (
        select(BlogPost)
        .where(*filters)
        .order_by(BlogPost.published_at.desc().nullslast(), BlogPost.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(stmt)
    posts = result.scalars().all()
    return BlogListResponse(posts=[_post_to_summary(post) for post in posts], total=total)


@router.get("/{slug}", response_model=BlogDetailResponse)
async def get_blog_post(
    slug: str,
    db: AsyncSession = Depends(get_db_session),
) -> BlogDetailResponse:
    post = await _get_published_post(db, slug, with_comments=True)
    return BlogDetailResponse(post=_post_to_detail(post))


@router.post("", response_model=BlogDetailResponse, status_code=201)
async def create_blog_post(
    body: BlogPostCreate,
    db: AsyncSession = Depends(get_db_session),
) -> BlogDetailResponse:
    now = datetime.now(timezone.utc)
    post = BlogPost(
        slug=await _build_unique_slug(db, body.title),
        title=body.title,
        excerpt=body.excerpt,
        content=body.content,
        cover_image=body.cover_image or "/assets/icons/palace.png",
        cover_alt=body.cover_alt or "Ảnh minh họa bài chia sẻ du lịch Huế",
        author_name=body.author_name or "Khách",
        source_type="user",
        source_name=None,
        source_url=None,
        tags=body.tags,
        published_at=now if body.status == "published" else None,
        reading_time=_estimate_reading_time(body.content),
        likes_count=0,
        comments_count=0,
        bookmarks_count=0,
        status=body.status,
    )
    db.add(post)
    try:
        await db.flush()
        await db.commit()
    except SQLAlchemyError:
        await db.rollback()
        _LOGGER.exception("Failed to create blog post title=%s", body.title)
        raise HTTPException(status_code=503, detail="Unable to create blog post right now.")

    increment("blog.post_created")
    return BlogDetailResponse(post=_post_to_detail(post))


@router.post("/{slug}/comments", response_model=BlogCommentResponse, status_code=201)
async def add_blog_comment(
    slug: str,
    body: BlogCommentCreate,
    db: AsyncSession = Depends(get_db_session),
) -> BlogCommentResponse:
    post = await _get_published_post(db, slug)
    comment = BlogComment(
        post_id=post.post_id,
        author_name=body.author_name or "Khách",
        content=body.content,
    )
    post.comments_count = max(0, post.comments_count or 0) + 1
    db.add(comment)
    try:
        await db.flush()
        await db.commit()
    except SQLAlchemyError:
        await db.rollback()
        _LOGGER.exception("Failed to add blog comment slug=%s", slug)
        raise HTTPException(status_code=503, detail="Unable to add comment right now.")

    increment("blog.comment_created")
    return BlogCommentResponse(**_comment_to_response(comment))


@router.post("/{slug}/interactions", response_model=BlogInteractionResponse)
async def update_blog_interaction(
    slug: str,
    body: BlogInteractionRequest,
    db: AsyncSession = Depends(get_db_session),
) -> BlogInteractionResponse:
    post = await _get_published_post(db, slug)
    delta = 1 if body.active else -1

    if body.action == "like":
        post.likes_count = max(0, (post.likes_count or 0) + delta)
        increment("blog.like")
    else:
        post.bookmarks_count = max(0, (post.bookmarks_count or 0) + delta)
        increment("blog.bookmark")

    try:
        await db.flush()
        await db.commit()
    except SQLAlchemyError:
        await db.rollback()
        _LOGGER.exception("Failed to update blog interaction slug=%s action=%s", slug, body.action)
        raise HTTPException(status_code=503, detail="Unable to update interaction right now.")

    return BlogInteractionResponse(
        likes_count=post.likes_count,
        bookmarks_count=post.bookmarks_count,
    )
