"""Abstract base classes for voice processing services.

This module defines the interfaces for Speech-to-Text (STT), Large Language Model (LLM),
and Text-to-Speech (TTS) services. Each service implementation should inherit from the
corresponding abstract base class.
"""

from abc import ABC, abstractmethod


class BaseSTT(ABC):
    """Abstract base class for Speech-to-Text services.
    
    Defines the interface for converting audio data to text transcriptions
    with language detection.
    """

    @abstractmethod
    async def transcribe(
        self,
        audio_bytes: bytes,
        filename: str | None = None,
        content_type: str | None = None,
    ) -> tuple[str, str]:
        """Transcribe audio to text.
        
        Args:
            audio_bytes: The audio data in bytes format.
            filename: Optional filename for inferring audio format.
            content_type: Optional MIME type for inferring audio format.
            
        Returns:
            A tuple containing:
                - text_query (str): The transcribed text.
                - detected_lang (str): The detected language code (e.g., 'en', 'vi').
        """
        pass


class BaseLLM(ABC):
    """Abstract base class for Large Language Model services.
    
    Defines the interface for generating contextual responses using
    large language models.
    """

    @abstractmethod
    async def generate_response(
        self, prompt: str, context_data: str, lang: str
    ) -> str:
        """Generate a response using the language model.
        
        Args:
            prompt: The user's input prompt or query.
            context_data: Additional context information for the model.
            lang: The language code for the response (e.g., 'en', 'vi').
            
        Returns:
            The generated response text in the specified language.
        """
        pass


class BaseTTS(ABC):
    """Abstract base class for Text-to-Speech services.
    
    Defines the interface for converting text to synthesized audio.
    """

    @abstractmethod
    async def synthesize(self, text: str, lang: str) -> bytes:
        """Synthesize text to audio.
        
        Args:
            text: The text content to synthesize.
            lang: The language code for synthesis (e.g., 'en', 'vi').
            
        Returns:
            The synthesized audio data in bytes format.
        """
        pass
