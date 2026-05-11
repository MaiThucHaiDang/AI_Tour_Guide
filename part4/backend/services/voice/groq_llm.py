"""Groq LLM provider using the Groq SDK with Llama 3 model."""

from __future__ import annotations

import os

from groq import AsyncGroq

from services.voice.interfaces import BaseLLM


class GroqLLMProvider(BaseLLM):
    """LLM implementation backed by Groq's Llama 3 model."""

    def __init__(self) -> None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY is not set in environment variables.")
        self._client = AsyncGroq(api_key=api_key)
        self._model = "llama3-70b-8192"

    async def generate_response(self, prompt: str, context_data: str, lang: str) -> str:
        """Generate a response constrained by provided context.

        Args:
            prompt: The user's input prompt or query.
            context_data: Context information that must be used to answer.
            lang: The target language code for the response.

        Returns:
            The generated response text.

        Raises:
            Exception: If the API call fails.
        """
        system_instruction = (
            "You are an AI Tour Guide. Answer the prompt using strictly the provided "
            "context_data. You MUST answer in the language code "
            f"[{lang}]. Maximum 100 words."
        )
        full_prompt = (
            "System Instruction:\n"
            f"{system_instruction}\n\n"
            "Context Data:\n"
            f"{context_data}\n\n"
            "User Prompt:\n"
            f"{prompt}"
        )

        try:
            message = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {
                        "role": "system",
                        "content": system_instruction,
                    },
                    {
                        "role": "user",
                        "content": f"Context Data:\n{context_data}\n\nUser Prompt:\n{prompt}",
                    },
                ],
                temperature=0.7,
                max_tokens=160,
            )
            text = message.choices[0].message.content
            if text is None:
                return ""
            return self._limit_words(text.strip(), 100)
        except Exception as exc:
            raise RuntimeError(f"Groq LLM request failed: {exc}") from exc

    @staticmethod
    def _limit_words(text: str, max_words: int) -> str:
        if not text:
            return ""
        words = text.split()
        if len(words) <= max_words:
            return text
        return " ".join(words[:max_words]).strip()
