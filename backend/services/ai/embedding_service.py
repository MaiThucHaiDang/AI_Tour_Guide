"""Embedding service using Google Gemini API."""

from __future__ import annotations

import logging
from typing import List
import asyncio
from google import genai

from core.config import settings
from utils.ai_utils import retry_with_backoff

_LOGGER = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating vector embeddings using Google Gemini API."""

    _client: genai.Client | None = None

    @classmethod
    def _get_client(cls) -> genai.Client:
        if cls._client is None:
            api_key = settings.GEMINI_API_KEY.strip()
            if not api_key:
                raise ValueError("GEMINI_API_KEY is not set in environment.")
            cls._client = genai.Client(api_key=api_key)
        return cls._client

    @classmethod
    async def get_embedding(cls, text: str) -> List[float]:
        """Generate a 768-dimensional vector embedding for a single text string."""
        if not text:
            return []

        try:
            client = cls._get_client()
            
            def _do_embed():
                return client.models.embed_content(
                    model=settings.GEMINI_EMBEDDING_MODEL,
                    contents=text,
                    config={
                        "task_type": "RETRIEVAL_QUERY",
                        "output_dimensionality": 768
                    }
                )

            # result = await asyncio.to_thread(_do_embed)
            result = await retry_with_backoff(asyncio.to_thread, _do_embed)
            
            if result and result.embeddings:
                return result.embeddings[0].values
            
            _LOGGER.error("Empty response from Gemini Embedding API")
            return []
        except Exception as e:
            _LOGGER.error("Gemini Embedding error: %s", e)
            return []

    @classmethod
    async def get_embeddings(cls, texts: List[str]) -> List[List[float]]:
        """Generate vector embeddings for a list of text strings (batch)."""
        if not texts:
            return []

        try:
            client = cls._get_client()

            def _do_embed_batch():
                return client.models.embed_content(
                    model=settings.GEMINI_EMBEDDING_MODEL,
                    contents=texts,
                    config={
                        "task_type": "RETRIEVAL_DOCUMENT",
                        "output_dimensionality": 768
                    }
                )

            # result = await asyncio.to_thread(_do_embed_batch)
            result = await retry_with_backoff(asyncio.to_thread, _do_embed_batch)
            
            if result and result.embeddings:
                return [e.values for e in result.embeddings]
            
            return []
        except Exception as e:
            _LOGGER.error("Gemini Batch Embedding error: %s", e)
            return []


def get_embedding_service() -> type[EmbeddingService]:
    """Dependency provider for EmbeddingService."""
    return EmbeddingService
