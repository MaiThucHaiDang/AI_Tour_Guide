import sys
from pathlib import Path
import pytest
from unittest.mock import AsyncMock, patch

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from repositories.artifact_repository import (
    find_artifact_by_name,
    get_artifact_context,
    canonicalize_transcript_entities,
    graph_augmented_search,
)

@pytest.fixture(autouse=True)
def mock_embedding_service():
    with patch("services.ai.embedding_service.EmbeddingService.get_embedding", AsyncMock(return_value=[0.0] * 768)):
        yield

@pytest.mark.asyncio
async def test_find_artifact_by_name_vi():
    """Verify that we can retrieve Điện Thái Hòa by its exact Vietnamese name."""
    art = await find_artifact_by_name("Điện Thái Hòa")
    assert art is not None
    assert art.name_vi == "Điện Thái Hòa"
    assert "Thái Hòa" in art.history_text_vi

@pytest.mark.asyncio
async def test_find_artifact_by_name_en():
    """Verify that we can retrieve Điện Kiến Trung by its English name."""
    art = await find_artifact_by_name("Kien Trung Palace")
    assert art is not None
    assert art.name_en == "Kien Trung Palace"
    assert "Điện Kiến Trung" in art.name_vi

@pytest.mark.asyncio
async def test_find_artifact_fuzzy():
    """Verify fuzzy matching for lowercase/accentless search terms (e.g. cung truong sanh)."""
    art = await find_artifact_by_name("cung truong sanh")
    assert art is not None
    assert art.name_vi == "Cung Trường Sanh"

@pytest.mark.asyncio
async def test_get_artifact_context():
    """Verify that we can retrieve full context text for Thế Miếu in Vietnamese."""
    context = await get_artifact_context("Thế Miếu", "history_text_vi")
    assert context is not None
    assert "Thế Miếu" in context
    assert "đối diện" in context or "triều Nguyễn" in context or "miếu" in context.lower()

@pytest.mark.asyncio
async def test_canonicalize_transcript_entities():
    """Verify transcript canonicalization correctly fixes spelling/casing for di tích."""
    corrected = await canonicalize_transcript_entities("tôi muốn tham quan dien kien trung")
    assert "Điện Kiến Trung" in corrected

@pytest.mark.asyncio
async def test_graph_augmented_search():
    """Verify hybrid vector-FAQ + knowledge graph search returns correct entry point and neighbors."""
    results = await graph_augmented_search("Điện Kiến Trung")
    assert len(results) > 0
    names = [r.name_vi for r in results]
    assert "Điện Kiến Trung" in names
