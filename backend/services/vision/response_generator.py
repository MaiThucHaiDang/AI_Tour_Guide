"""LLM response generation for recognized artifacts.

Moved from: src/backend/services/llm_orchestrator.py
"""

from __future__ import annotations

import logging
import hashlib
import asyncio

from google import genai

from core.config import settings
from schemas.vision import ArtifactInfo, LLMResponse
from utils.prompt_templates import build_vision_system_prompt

logger = logging.getLogger(__name__)

_text_client = None
_response_cache: dict[str, LLMResponse] = {}
_MAX_CACHE_SIZE = 100


def _get_text_client():
    global _text_client
    if _text_client is not None:
        return _text_client
    api_key = settings.GEMINI_API_KEY.strip()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured.")
    _text_client = genai.Client(api_key=api_key)
    return _text_client


def _make_cache_key(artifact_id: str, lang: str, question: str) -> str:
    """Generate cache key from artifact and question."""
    key_str = f"{artifact_id}|{lang}|{question}"
    return hashlib.md5(key_str.encode()).hexdigest()


def _manage_cache_size():
    """Keep cache size under control."""
    global _response_cache
    if len(_response_cache) > _MAX_CACHE_SIZE:
        # Remove oldest 20% of entries
        to_remove = len(_response_cache) // 5
        for key in list(_response_cache.keys())[:to_remove]:
            del _response_cache[key]
        logger.debug("Cache evicted %d oldest entries", to_remove)


async def generate_response(
    artifact_data: ArtifactInfo,
    lang: str = "vi",
    user_question: str = "Hãy giới thiệu ngắn gọn về hiện vật này.",
    use_cache: bool = True,
) -> LLMResponse:
    """Generate a tour-guide response for a recognized artifact.
    
    Args:
        artifact_data: Artifact information from database
        lang: Language code ('vi' or 'en')
        user_question: User's question about the artifact
        use_cache: Whether to use cached responses
        
    Returns:
        LLMResponse with generated text
        
    Raises:
        Exception: If LLM generation fails after retries
    """
    # Check cache
    cache_key = _make_cache_key(artifact_data.art_id, lang, user_question)
    if use_cache and cache_key in _response_cache:
        logger.debug("Cache hit for artifact %s", artifact_data.art_id)
        return _response_cache[cache_key]
    
    system_prompt = build_vision_system_prompt(artifact_data, lang)
    full_prompt = f"{system_prompt}\n\nCâu hỏi của khách tham quan: {user_question}"

    logger.info("Calling Gemini text for artifact: %s (lang=%s)", artifact_data.art_id, lang)

    model_name = settings.GEMINI_TEXT_MODEL.strip() or "gemini-2.0-flash"
    
    # Retry logic for LLM generation with exponential backoff
    last_error = None
    for attempt in range(3):
        try:
            response = await _get_text_client().aio.models.generate_content(
                model=model_name,
                contents=full_prompt,
            )
            response_text = response.text.strip()
            
            if not response_text:
                logger.warning("Empty response from LLM (attempt %d)", attempt + 1)
                if attempt < 2:
                    await asyncio.sleep((2 ** attempt) * 0.5)
                    continue
                raise ValueError("LLM returned empty response")
            
            result = LLMResponse(
                response_text=response_text,
                token_count=0,
                model_used=model_name,
            )
            
            # Store in cache
            _response_cache[cache_key] = result
            _manage_cache_size()
            logger.debug("Cached response for artifact %s", artifact_data.art_id)
            
            return result
            
        except Exception as e:
            last_error = e
            error_str = str(e).lower()
            is_retryable = "429" in str(e) or "timeout" in error_str or "temporarily" in error_str
            
            logger.warning("LLM generation error (attempt %d): %s", attempt + 1, e)
            if attempt < 2 and is_retryable:
                wait_time = (2 ** attempt) * 0.5
                logger.debug("Retrying after %.1fs...", wait_time)
                await asyncio.sleep(wait_time)
            else:
                logger.error("LLM generation failed: %s", e, exc_info=True)
                raise
    
    # Fallback error
    raise last_error or Exception("LLM generation failed after retries")
