"""Embedding service using Google Gemini API."""

from __future__ import annotations

import logging
from typing import List
import asyncio
from google import genai
from google.genai import types

from core.config import settings
from utils.ai_utils import retry_with_backoff

_LOGGER = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating vector embeddings using Google Gemini API."""

    _client: genai.Client | None = None
    _clients: dict[str, genai.Client] = {}
    _next_client_index: int = 0

    @classmethod
    def _get_client(cls) -> genai.Client:
        if cls._client is None:
            cls._client = cls._get_clients()[0][1]
        return cls._client

    @classmethod
    def _get_clients(cls) -> list[tuple[str, genai.Client]]:
        api_keys = settings.gemini_api_key_list
        if not api_keys:
            raise ValueError("GEMINI_API_KEY is not set in environment.")

        clients: list[tuple[str, genai.Client]] = []
        for index, api_key in enumerate(api_keys, start=1):
            if api_key not in cls._clients:
                cls._clients[api_key] = genai.Client(api_key=api_key)
            clients.append((f"gemini_key_{index}", cls._clients[api_key]))
        return clients

    @classmethod
    async def _embed_with_fallback(
        cls,
        contents: str | List[str],
        task_type: str,
    ) -> List[List[float]]:
        request_contents = contents
        if isinstance(contents, list):
            # Gemini embedding 2 treats a bare ``list[str]`` as one multimodal
            # Content with several Parts. Explicit Content objects preserve the
            # intended one-document-to-one-vector batch semantics.
            request_contents = [
                types.Content(parts=[types.Part.from_text(text=text)])
                for text in contents
            ]

        providers = cls._get_clients()
        start_index = cls._next_client_index % len(providers)
        provider_indices = [
            (start_index + offset) % len(providers)
            for offset in range(len(providers))
        ]

        for provider_index in provider_indices:
            provider_label, client = providers[provider_index]
            try:
                def _do_embed():
                    return client.models.embed_content(
                        model=settings.GEMINI_EMBEDDING_MODEL,
                        contents=request_contents,
                        config={
                            "task_type": task_type,
                            "output_dimensionality": 768,
                        },
                    )

                # Switch keys immediately on quota/auth/provider errors. Retrying
                # the same key first defeats the purpose of a configured pool.
                result = await retry_with_backoff(
                    asyncio.to_thread,
                    _do_embed,
                    max_retries=0,
                )
                if result and result.embeddings:
                    _LOGGER.info("Embedding provider %s succeeded", provider_label)
                    cls._next_client_index = (provider_index + 1) % len(providers)
                    return [embedding.values for embedding in result.embeddings]
                _LOGGER.warning("Embedding provider %s returned no vectors", provider_label)
            except Exception as exc:
                _LOGGER.warning("Embedding provider %s failed: %s", provider_label, exc)

        _LOGGER.error("All Gemini embedding providers failed")
        return []

    @classmethod
    async def get_embedding(cls, text: str) -> List[float]:
        """Generate a 768-dimensional vector embedding for a single text string."""
        if not text:
            return []
        embeddings = await cls._embed_with_fallback(text, "RETRIEVAL_QUERY")
        return embeddings[0] if embeddings else []

    @classmethod
    async def get_embeddings(cls, texts: List[str]) -> List[List[float]]:
        """Generate vector embeddings for a list of text strings (batch).
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors. Returns empty list on error.
            
        Raises:
            ValueError: If batch size exceeds maximum allowed.
        """
        if not texts:
            return []
        
        # Validate batch size to prevent API overload
        max_batch_size = 100
        if len(texts) > max_batch_size:
            raise ValueError(f"Batch size {len(texts)} exceeds maximum {max_batch_size}")

        return await cls._embed_with_fallback(texts, "RETRIEVAL_DOCUMENT")

    @classmethod
    async def get_query_embeddings(cls, texts: List[str]) -> List[List[float]]:
        """Generate query embeddings in batches for retrieval evaluation.

        Gemini distinguishes documents from queries through ``task_type``.  The
        production single-query method already uses ``RETRIEVAL_QUERY``; this
        batch variant keeps benchmark runs efficient without changing the
        embedding space or issuing one request per query.
        """
        if not texts:
            return []

        max_batch_size = 100
        if len(texts) > max_batch_size:
            raise ValueError(f"Batch size {len(texts)} exceeds maximum {max_batch_size}")

        return await cls._embed_with_fallback(texts, "RETRIEVAL_QUERY")


def get_embedding_service() -> type[EmbeddingService]:
    """Dependency provider for EmbeddingService."""
    return EmbeddingService
