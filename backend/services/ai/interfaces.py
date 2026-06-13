"""Abstract base classes for AI services (STT, LLM, TTS).

Moved from: part4/backend/services/voice/interfaces.py
"""

from abc import ABC, abstractmethod


class BaseSTT(ABC):
    """Abstract base class for Speech-to-Text services."""

    @abstractmethod
    async def transcribe(
        self,
        audio_bytes: bytes,
        filename: str | None = None,
        content_type: str | None = None,
        language_hint: str | None = None,
    ) -> tuple[str, str]:
        """Transcribe audio to text.

        Returns:
            A tuple of (transcribed_text, detected_language_code).
        """
        pass


class BaseLLM(ABC):
    """Abstract base class for Large Language Model services."""

    @abstractmethod
    async def generate_response(
        self, prompt: str, context_data: str, lang: str, max_tokens: int | None = None, system_prompt: str | None = None
    ) -> str:
        """Generate a response using the language model."""
        pass

    @abstractmethod
    async def generate_response_stream(
        self, prompt: str, context_data: str, lang: str, system_prompt: str | None = None
    ):
        """Generate a response stream using the language model."""
        pass


class BaseTTS(ABC):
    """Abstract base class for Text-to-Speech services."""

    @abstractmethod
    async def synthesize(self, text: str, lang: str) -> bytes:
        """Synthesize text to audio bytes."""
        pass
