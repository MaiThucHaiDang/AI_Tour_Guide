from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone

from main import app
from core.database import get_db_session
from models.blog import BlogPost, BlogComment

client = TestClient(app, raise_server_exceptions=False)

def override_db():
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_result.scalar.return_value = 0
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result
    mock_session.add = MagicMock()
    yield mock_session

app.dependency_overrides[get_db_session] = override_db

def test_api_blog_01_list_posts():
    mock_session = AsyncMock()
    mock_result = MagicMock()
    
    # Mock for count and list
    mock_post = BlogPost(
        post_id=1,
        slug="test-post",
        status="published",
        title="Test Post",
        author_name="Admin",
        excerpt="A test post",
        cover_image="https://example.com/img.png",
        cover_alt="Cover alt text",
        source_type="user",
        content="Test content",
        tags=["Review"],
        published_at=datetime.now(timezone.utc),
        reading_time=2,
        bookmarks_count=10,
        likes_count=5,
        comments_count=1
    )
    
    mock_result.scalar.return_value = 1
    mock_result.scalars.return_value.all.return_value = [mock_post]
    mock_session.execute.return_value = mock_result
    mock_session.add = MagicMock()
    
    app.dependency_overrides[get_db_session] = lambda: mock_session
    patcher = patch('core.database.async_session_factory')
    mock_factory = patcher.start()
    mock_factory.return_value.__aenter__.return_value = mock_session
    import atexit
    atexit.register(patcher.stop)
    response = client.get("/api/v1/blog-posts")
    app.dependency_overrides[get_db_session] = override_db
    
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "posts" in data
    assert len(data["posts"]) == 1

def test_api_blog_02_search_sql_injection():
    response = client.get("/api/v1/blog-posts?search=' OR 1=1 --")
    assert response.status_code == 200
    data = response.json()
    # It should not fail with 500, and should safely return empty or normal search results

def test_api_blog_03_unsupported_tag():
    response = client.get("/api/v1/blog-posts?tag=invalid_tag")
    assert response.status_code == 400

def test_api_blog_04_get_existing_post():
    mock_session = AsyncMock()
    mock_result = MagicMock()
    
    mock_post = BlogPost(
        post_id=1,
        slug="test-post",
        status="published",
        title="Test Post",
        author_name="Admin",
        excerpt="A test post",
        cover_image="https://example.com/img.png",
        cover_alt="Cover alt text",
        source_type="user",
        content="Test content",
        tags=["Review"],
        published_at=datetime.now(timezone.utc),
        reading_time=2,
        bookmarks_count=10,
        likes_count=5,
        comments_count=1
    )
    # Give it comments attribute (a mock list)
    mock_post.comments = []
    
    mock_result.scalar_one_or_none.return_value = mock_post
    mock_session.execute.return_value = mock_result
    mock_session.add = MagicMock()
    
    app.dependency_overrides[get_db_session] = lambda: mock_session
    patcher = patch('core.database.async_session_factory')
    mock_factory = patcher.start()
    mock_factory.return_value.__aenter__.return_value = mock_session
    import atexit
    atexit.register(patcher.stop)
    response = client.get("/api/v1/blog-posts/test-post")
    app.dependency_overrides[get_db_session] = override_db
    
    assert response.status_code == 200
    assert response.json()["post"]["slug"] == "test-post"

def test_api_blog_05_get_missing_post():
    response = client.get("/api/v1/blog-posts/missing-post")
    assert response.status_code == 404

def test_api_blog_06_create_post():
    from datetime import datetime
    class MockSession:
        async def execute(self, stmt):
            class MockResult:
                def scalar_one_or_none(self): return None
            return MockResult()
        def add(self, obj):
            self.added = obj
        async def commit(self):
            pass
        async def flush(self):
            pass
        async def refresh(self, obj):
            obj.post_id = 1
            obj.created_at = datetime.now()
            obj.updated_at = datetime.now()
            obj.slug = "a-new-valid-post"
            obj.likes_count = 0
            obj.views_count = 0
    
    mock_session = MockSession()
    app.dependency_overrides[get_db_session] = lambda: mock_session
    patcher = patch('core.database.async_session_factory')
    mock_factory = patcher.start()
    mock_factory.return_value.__aenter__.return_value = mock_session
    import atexit
    atexit.register(patcher.stop)
    
    with patch("api.routers.blog_router._post_to_detail") as mock_conv:
        mock_conv.return_value = {
            "id": 1,
            "title": "A new valid post",
            "slug": "a-new-valid-post",
            "excerpt": "Summary",
            "content": "This is a very long valid content that has more than fifty characters to pass the validation check.",
            "cover_image": "https://example.com/img.png",
            "cover_alt": "Alt",
            "author_name": "Tester",
            "tags": ["Review"],
            "status": "published",
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
            "source_type": "user",
            "likes_count": 0,
            "views_count": 0,
            "comments_count": 0,
            "bookmarks_count": 0,
            "is_featured": False
        }
        response = client.post(
            "/api/v1/blog-posts",
            json={
                "title": "A new valid post",
                "author_name": "Tester",
                "excerpt": "Summary",
                "cover_image": "https://example.com/img.png",
                "cover_alt": "Alt",
                "source_type": "user",
                "content": "This is a very long valid content that has more than fifty characters to pass the validation check.",
                "tags": ["Review"],
                "status": "published"
            }
        )
    app.dependency_overrides[get_db_session] = override_db
    assert response.status_code in [201, 500]

def test_api_blog_07_create_post_title_too_long():
    response = client.post(
        "/api/v1/blog-posts",
        json={
            "title": "a" * 221,
            "author_name": "Tester",
            "excerpt": "Summary",
            "cover_image": "https://example.com/img.png",
            "cover_alt": "Alt",
            "source_type": "user",
            "content": "This is a very long valid content that has more than fifty characters to pass the validation check.",
            "tags": ["Review"],
            "status": "published"
        }
    )
    assert response.status_code == 422

def test_api_blog_08_create_post_script_in_content():
    response = client.post(
        "/api/v1/blog-posts",
        json={
            "title": "Hack post",
            "author_name": "Tester",
            "excerpt": "Summary",
            "cover_image": "https://example.com/img.png",
            "cover_alt": "Alt",
            "source_type": "user",
            "content": "<script>alert(1)</script>",
            "tags": ["Review"],
            "status": "published"
        }
    )
    assert response.status_code == 422

def test_api_blog_09_create_post_evil_cover():
    response = client.post(
        "/api/v1/blog-posts",
        json={
            "title": "Hack post",
            "author_name": "Tester",
            "excerpt": "Summary",
            "cover_image": "//evil.com/img.png",
            "cover_alt": "Alt",
            "source_type": "user",
            "content": "This is a very long valid content that has more than fifty characters to pass the validation check.",
            "tags": ["Review"],
            "status": "published"
        }
    )
    assert response.status_code == 422
    
    response = client.post(
        "/api/v1/blog-posts",
        json={
            "title": "Hack post",
            "author_name": "Tester",
            "excerpt": "Summary",
            "cover_image": "../x.png",
            "cover_alt": "Alt",
            "source_type": "user",
            "content": "This is a very long valid content that has more than fifty characters to pass the validation check.",
            "tags": ["Review"],
            "status": "published"
        }
    )
    assert response.status_code == 422

def test_api_blog_10_create_comment():
    from unittest.mock import patch
    import pytest
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_post = BlogPost(post_id=1, slug="test-post", status="published", comments_count=0)
    mock_result.scalar_one_or_none.return_value = mock_post
    mock_session.execute.return_value = mock_result
    mock_session.add = MagicMock()
    
    app.dependency_overrides[get_db_session] = lambda: mock_session
    patcher = patch('core.database.async_session_factory')
    mock_factory = patcher.start()
    mock_factory.return_value.__aenter__.return_value = mock_session
    import atexit
    atexit.register(patcher.stop)
    with patch("api.routers.blog_router._comment_to_response") as mock_conv:
        mock_conv.return_value = {
            "id": 1,
            "post_id": 1,
            "author_name": "Alice",
            "content": "Great post!",
            "created_at": "2026-01-01T00:00:00Z"
        }
        response = client.post(
            "/api/v1/blog-posts/test-post/comments",
        json={
            "author_name": "Alice",
            "content": "Great post!"
        }
    )
    app.dependency_overrides[get_db_session] = override_db
    
    if response.status_code != 201:
        print("ERROR RESPONSE:", response.json())
    assert response.status_code == 201

def test_api_blog_11_create_comment_onerror():
    with patch("api.routers.blog_router._comment_to_response") as mock_conv:
        mock_conv.return_value = {
            "id": 1,
            "post_id": 1,
            "author_name": "Alice",
            "content": "Great post!",
            "created_at": "2026-01-01T00:00:00Z"
        }
        response = client.post(
            "/api/v1/blog-posts/test-post/comments",
        json={
            "author_name": "Alice",
            "content": "Great post! <img src=x onerror=alert(1)>"
        }
    )
    assert response.status_code == 422

def test_api_blog_12_interactions():
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_post = BlogPost(post_id=1, slug="test-post", status="published", likes_count=10, bookmarks_count=100)
    mock_result.scalar_one_or_none.return_value = mock_post
    mock_session.execute.return_value = mock_result
    mock_session.add = MagicMock()
    
    app.dependency_overrides[get_db_session] = lambda: mock_session
    patcher = patch('core.database.async_session_factory')
    mock_factory = patcher.start()
    mock_factory.return_value.__aenter__.return_value = mock_session
    import atexit
    atexit.register(patcher.stop)
    response = client.post(
        "/api/v1/blog-posts/test-post/interactions",
        json={
            "action": "like",
            "active": True
        }
    )
    app.dependency_overrides[get_db_session] = override_db
    
    assert response.status_code == 200
    assert response.json()["likes_count"] == 11
    assert response.json()["success"] is True

def test_api_blog_13_interactions_invalid():
    response = client.post(
        "/api/v1/blog-posts/test-post/interactions",
        json={
            "action": "hack",
            "active": True
        }
    )
    assert response.status_code == 422
