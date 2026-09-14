from __future__ import annotations

from types import SimpleNamespace

import pytest


@pytest.mark.asyncio
async def test_batch_embedding_falls_back_to_next_gemini_key(monkeypatch):
    from services.ai import embedding_service

    calls: list[str] = []

    class FakeModels:
        def __init__(self, api_key: str) -> None:
            self.api_key = api_key

        def embed_content(self, **kwargs):
            calls.append(self.api_key)
            if self.api_key == "bad-key":
                raise RuntimeError("provider unavailable")
            return SimpleNamespace(
                embeddings=[
                    SimpleNamespace(values=[0.25] * 768)
                    for _ in kwargs["contents"]
                ]
            )

    class FakeClient:
        def __init__(self, api_key: str) -> None:
            self.models = FakeModels(api_key)

    monkeypatch.setattr(
        embedding_service,
        "settings",
        SimpleNamespace(
            gemini_api_key_list=["bad-key", "good-key"],
            GEMINI_EMBEDDING_MODEL="embedding-model",
        ),
    )
    monkeypatch.setattr(embedding_service.genai, "Client", FakeClient)
    embedding_service.EmbeddingService._client = None
    embedding_service.EmbeddingService._clients = {}
    embedding_service.EmbeddingService._next_client_index = 0

    result = await embedding_service.EmbeddingService.get_embeddings(
        ["document one", "document two"]
    )

    assert calls == ["bad-key", "good-key"]
    assert len(result) == 2
    assert len(result[0]) == 768

    embedding_service.EmbeddingService._client = None
    embedding_service.EmbeddingService._clients = {}
    embedding_service.EmbeddingService._next_client_index = 0
