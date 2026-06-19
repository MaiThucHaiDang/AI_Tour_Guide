"""Schemas and validation for the travel blog API."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Literal
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator

ALLOWED_BLOG_TAGS = [
    "Kinh nghiệm",
    "Lịch trình",
    "Văn hóa - lịch sử",
    "Ẩm thực",
    "Review",
    "Mẹo du lịch",
]

_UNSAFE_TEXT_PATTERN = re.compile(
    r"(<\s*/?\s*script\b|javascript\s*:|on[a-z]+\s*=)",
    re.IGNORECASE,
)


def _clean_plain_text(value: str, field_name: str, max_length: int) -> str:
    cleaned = " ".join(value.replace("\x00", "").split()) if field_name == "title" else value.replace("\x00", "").strip()
    if not cleaned:
        raise ValueError(f"{field_name} is required")
    if len(cleaned) > max_length:
        raise ValueError(f"{field_name} must be at most {max_length} characters")
    if _UNSAFE_TEXT_PATTERN.search(cleaned):
        raise ValueError(f"{field_name} contains unsafe HTML or script content")
    return cleaned


def _validate_public_url(value: str | None, *, default: str | None = None) -> str | None:
    if value is None or not str(value).strip():
        return default
    cleaned = str(value).strip()
    if cleaned.startswith("/"):
        if cleaned.startswith("//") or ".." in cleaned:
            raise ValueError("Relative asset paths must be rooted and cannot contain traversal")
        return cleaned

    parsed = urlparse(cleaned)
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        return cleaned
    raise ValueError("URL must be http(s) or a rooted local asset path")


class BlogCommentCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    author_name: str = Field(default="Khách", alias="authorName", max_length=120)
    content: str = Field(min_length=1, max_length=1000)

    @field_validator("author_name")
    @classmethod
    def validate_author_name(cls, value: str) -> str:
        return _clean_plain_text(value or "Khách", "author_name", 120)

    @field_validator("content")
    @classmethod
    def validate_comment_content(cls, value: str) -> str:
        return _clean_plain_text(value, "content", 1000)


class BlogCommentResponse(BaseModel):
    id: int
    post_id: int
    author_name: str
    content: str
    created_at: datetime


class BlogPostCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    title: str = Field(min_length=1, max_length=220)
    excerpt: str = Field(min_length=1, max_length=420)
    content: str = Field(min_length=1, max_length=12000)
    cover_image: str | None = Field(default=None, alias="coverImage")
    cover_alt: str | None = Field(default=None, alias="coverAlt", max_length=260)
    author_name: str = Field(default="Khách", alias="authorName", max_length=120)
    tags: list[str] = Field(min_length=1, max_length=4)
    status: Literal["draft", "published"] = "published"

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        return _clean_plain_text(value, "title", 220)

    @field_validator("excerpt")
    @classmethod
    def validate_excerpt(cls, value: str) -> str:
        return _clean_plain_text(value, "excerpt", 420)

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        return _clean_plain_text(value, "content", 12000)

    @field_validator("cover_image")
    @classmethod
    def validate_cover_image(cls, value: str | None) -> str:
        return _validate_public_url(value, default="/assets/images/art_17_1.jpg") or "/assets/images/art_17_1.jpg"

    @field_validator("cover_alt")
    @classmethod
    def validate_cover_alt(cls, value: str | None) -> str:
        if not value:
            return "Ảnh bìa mặc định bài chia sẻ du lịch Huế"
        return _clean_plain_text(value, "cover_alt", 260)

    @field_validator("author_name")
    @classmethod
    def validate_post_author(cls, value: str) -> str:
        return _clean_plain_text(value or "Khách", "author_name", 120)

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, value: list[str]) -> list[str]:
        unique_tags = []
        for tag in value:
            cleaned = tag.strip()
            if cleaned not in ALLOWED_BLOG_TAGS:
                raise ValueError(f"Unsupported blog tag: {cleaned}")
            if cleaned not in unique_tags:
                unique_tags.append(cleaned)
        if not unique_tags:
            raise ValueError("At least one blog tag is required")
        return unique_tags


class BlogPostSummary(BaseModel):
    id: int
    slug: str
    title: str
    excerpt: str
    cover_image: str
    cover_alt: str
    author_name: str
    source_type: Literal["seed", "external", "user"]
    source_name: str | None = None
    source_url: str | None = None
    tags: list[str]
    created_at: datetime
    updated_at: datetime
    published_at: datetime | None = None
    reading_time: int
    likes_count: int
    comments_count: int
    bookmarks_count: int
    status: Literal["draft", "pending", "published"]


class BlogPostDetail(BlogPostSummary):
    content: str
    comments: list[BlogCommentResponse] = Field(default_factory=list)


class BlogListResponse(BaseModel):
    success: bool = True
    posts: list[BlogPostSummary]
    total: int


class BlogDetailResponse(BaseModel):
    success: bool = True
    post: BlogPostDetail


class BlogInteractionRequest(BaseModel):
    action: Literal["like", "bookmark"]
    active: bool


class BlogInteractionResponse(BaseModel):
    success: bool = True
    likes_count: int
    bookmarks_count: int
