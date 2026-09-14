import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from fastapi import HTTPException
from pydantic import ValidationError

from schemas.blog import (
    _clean_plain_text,
    _validate_public_url,
    BlogPostCreate,
    BlogCommentCreate,
)
from api.routers.blog_router import (
    _estimate_reading_time,
    _slugify,
    _safe_datetime,
    _build_unique_slug,
    _comment_to_response,
    _post_to_summary,
    _post_to_detail,
    _get_published_post,
)
from models.blog import BlogPost, BlogComment

# --- _clean_plain_text ---

def test_clean_plain_text_trims_title_and_removes_null():
    cleaned = _clean_plain_text("  Title \x00 Here  ", "title", 100)
    assert cleaned == "Title Here"
    
    cleaned_other = _clean_plain_text("  Content \x00 Here  ", "content", 100)
    assert cleaned_other == "Content  Here"

def test_clean_plain_text_rejects_empty():
    with pytest.raises(ValueError, match="title is required"):
        _clean_plain_text("   ", "title", 100)

def test_clean_plain_text_rejects_long_string():
    with pytest.raises(ValueError, match="title must be at most 5 characters"):
        _clean_plain_text("abcdef", "title", 5)

def test_clean_plain_text_rejects_script_javascript_onerror():
    with pytest.raises(ValueError, match="contains unsafe HTML or script"):
        _clean_plain_text("<script>alert(1)</script>", "content", 1000)
    
    with pytest.raises(ValueError, match="contains unsafe HTML or script"):
        _clean_plain_text("javascript:alert(1)", "content", 1000)
        
    with pytest.raises(ValueError, match="contains unsafe HTML or script"):
        _clean_plain_text("<img src=x onerror=alert(1)>", "content", 1000)

    with pytest.raises(ValueError, match="contains unsafe HTML or script"):
        _clean_plain_text("<SCRIPT src=foo></SCRIPT>", "content", 1000)

# --- _validate_public_url ---

def test_validate_public_url_accepts_http_https_rooted_asset():
    assert _validate_public_url("http://example.com/img.png") == "http://example.com/img.png"
    assert _validate_public_url("https://example.com/img.png") == "https://example.com/img.png"
    assert _validate_public_url("/assets/img.png") == "/assets/img.png"

def test_validate_public_url_returns_default():
    assert _validate_public_url(None, default="/default.png") == "/default.png"
    assert _validate_public_url("   ", default="/default.png") == "/default.png"

def test_validate_public_url_rejects_protocol_relative_and_traversal():
    with pytest.raises(ValueError, match="Relative asset paths must be rooted"):
        _validate_public_url("//example.com/img")
    
    with pytest.raises(ValueError, match="Relative asset paths must be rooted"):
        _validate_public_url("/assets/../etc/passwd")

def test_validate_public_url_rejects_unsupported_scheme():
    with pytest.raises(ValueError, match="URL must be http\\(s\\) or a rooted local asset path"):
        _validate_public_url("ftp://example.com/img.png")
    
    with pytest.raises(ValueError, match="URL must be http\\(s\\) or a rooted local asset path"):
        _validate_public_url("data:image/png;base64,iVBOR")

# --- BlogPostCreate.validate_tags ---

def test_blog_tags_dedupe_and_reject_unsupported():
    with pytest.raises(ValueError, match="Unsupported blog tag"):
        BlogPostCreate.validate_tags(["Invalid Tag"])

    tags = BlogPostCreate.validate_tags(["Review", "Review", "Ẩm thực"])
    assert tags == ["Review", "Ẩm thực"]

def test_blog_tags_rejects_empty():
    with pytest.raises(ValueError, match="At least one blog tag is required"):
        BlogPostCreate.validate_tags([])

# --- _estimate_reading_time ---

def test_estimate_reading_time_min_one_and_ceil():
    assert _estimate_reading_time(None) == 1
    assert _estimate_reading_time("") == 1
    assert _estimate_reading_time("word " * 220) == 1
    assert _estimate_reading_time("word " * 221) == 2
    assert _estimate_reading_time("word " * 440) == 2
    assert _estimate_reading_time("word " * 441) == 3

# --- _slugify ---

def test_slugify_vietnamese_title():
    assert _slugify("Khám phá Đại Nội Huế - Kỳ 1") == "kham-pha-dai-noi-hue-ky-1"
    assert _slugify("Đường đi đèo Hải Vân") == "duong-di-deo-hai-van"

def test_slugify_special_chars_and_defaults():
    assert _slugify("!@#$%^&*()") == "bai-viet"
    assert _slugify("") == "bai-viet"
    assert _slugify("   ") == "bai-viet"
    assert _slugify("Hello   World") == "hello-world"
    assert _slugify("-Hello-") == "hello"

# --- _safe_datetime ---

def test_safe_datetime_fallback_now():
    now = datetime.now(timezone.utc)
    assert _safe_datetime(now) == now
    
    fallback = _safe_datetime(None)
    assert isinstance(fallback, datetime)
    assert fallback.tzinfo == timezone.utc

# --- _build_unique_slug ---

@pytest.mark.asyncio
async def test_build_unique_slug_appends_suffix():
    mock_db = AsyncMock()
    mock_result_1 = MagicMock()
    mock_result_1.scalar_one_or_none.return_value = 1
    
    mock_result_2 = MagicMock()
    mock_result_2.scalar_one_or_none.return_value = 1
    
    mock_result_3 = MagicMock()
    mock_result_3.scalar_one_or_none.return_value = None
    
    mock_db.execute.side_effect = [mock_result_1, mock_result_2, mock_result_3]
    
    slug = await _build_unique_slug(mock_db, "Test Title")
    assert slug == "test-title-3"

# --- _comment_to_response ---

def test_comment_to_response_fields():
    dt = datetime.now(timezone.utc)
    comment = BlogComment(comment_id=1, post_id=10, author_name="Khách", content="Hay", created_at=dt)
    resp = _comment_to_response(comment)
    assert resp["id"] == 1
    assert resp["post_id"] == 10
    assert resp["author_name"] == "Khách"
    assert resp["content"] == "Hay"
    assert resp["created_at"] == dt

# --- _post_to_summary and _post_to_detail ---

def test_post_to_summary_counts_non_negative():
    dt = datetime.now(timezone.utc)
    post = BlogPost(
        post_id=1, slug="slug", title="T", excerpt="E", cover_image="/img", cover_alt="Alt",
        author_name="A", source_type="user", tags=["Review"], created_at=dt, updated_at=dt,
        likes_count=-5, comments_count=None, bookmarks_count=-1, status="published",
        reading_time=None, content="Some content here"
    )
    summary = _post_to_summary(post)
    assert summary["likes_count"] == 0
    assert summary["comments_count"] == 0
    assert summary["bookmarks_count"] == 0
    assert summary["reading_time"] == 1
    assert summary["tags"] == ["Review"]

def test_post_to_summary_none_tags():
    dt = datetime.now(timezone.utc)
    post = BlogPost(
        post_id=1, slug="slug", title="T", excerpt="E", cover_image="/img", cover_alt="Alt",
        author_name="A", source_type="user", tags=None, created_at=dt, updated_at=dt,
        status="published"
    )
    summary = _post_to_summary(post)
    assert summary["tags"] == []

def test_post_to_detail_includes_comments():
    dt = datetime.now(timezone.utc)
    post = BlogPost(
        post_id=1, slug="s", title="T", excerpt="E", content="C", cover_image="/img", cover_alt="A",
        author_name="A", source_type="user", tags=[], created_at=dt, updated_at=dt,
        status="published", comments=[BlogComment(comment_id=1, post_id=1, author_name="A", content="C", created_at=dt)]
    )
    detail = _post_to_detail(post)
    assert len(detail["comments"]) == 1
    assert detail["comments"][0]["id"] == 1
    assert detail["content"] == "C"

def test_post_to_detail_none_comments():
    dt = datetime.now(timezone.utc)
    post = BlogPost(
        post_id=1, slug="s", title="T", excerpt="E", content="C", cover_image="/img", cover_alt="A",
        author_name="A", source_type="user", tags=[], created_at=dt, updated_at=dt,
        status="published"
    )
    post.__dict__['comments'] = None
    detail = _post_to_detail(post)
    assert detail["comments"] == []

# --- _get_published_post ---

@pytest.mark.asyncio
async def test_get_published_post_404_for_missing_or_draft():
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result
    
    with pytest.raises(HTTPException) as exc:
        await _get_published_post(mock_db, "missing-slug")
    assert exc.value.status_code == 404

@pytest.mark.asyncio
async def test_get_published_post_returns_post():
    mock_db = AsyncMock()
    mock_result = MagicMock()
    post = BlogPost(post_id=1, status="published")
    mock_result.scalar_one_or_none.return_value = post
    mock_db.execute.return_value = mock_result
    
    result_post = await _get_published_post(mock_db, "valid-slug", with_comments=True)
    assert result_post.post_id == 1
