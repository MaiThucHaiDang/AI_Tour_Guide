"""Gemini LLM provider using the google-generativeai SDK."""

from __future__ import annotations

import asyncio
import os
from typing import Any

import google.generativeai as genai

from services.voice.interfaces import BaseLLM


class GeminiLLMProvider(BaseLLM):
    """LLM implementation backed by Gemini models."""

    def __init__(self) -> None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set in environment variables.")
        genai.configure(api_key=api_key)
        
        # Try models in order of preference
        model_candidates = [
            "gemini-2.0-flash",      # Latest model
            "gemini-1.5-flash",      # Original choice
            "gemini-1.5-pro",        # Alternative fast model
            "gemini-pro",            # Fallback stable model
        ]
        
        self._model = None
        self._model_name = None
        
        # Get list of available models
        try:
            available_models = [m.name for m in genai.list_models()]
            print(f"Available models: {available_models}")
        except Exception as e:
            print(f"Could not list available models: {e}")
            available_models = []
        
        for model_name in model_candidates:
            # Normalize model name (add 'models/' prefix if not present)
            full_model_name = model_name if model_name.startswith("models/") else f"models/{model_name}"
            
            if available_models and full_model_name not in available_models:
                print(f"✗ Model {model_name} not in available models list")
                continue
            
            try:
                test_model = genai.GenerativeModel(model_name)
                self._model = test_model
                self._model_name = model_name
                print(f"✓ Successfully initialized model: {model_name}")
                break
            except Exception as e:
                print(f"✗ Model {model_name} initialization failed: {str(e)[:100]}")
                continue
        
        if self._model is None:
            raise ValueError(
                f"Could not initialize any Gemini model. Tried: {model_candidates}. "
                f"Available models: {available_models}. "
                "Please check your API key and verify available models at "
                "https://ai.google.dev/models"
            )

    async def generate_response(self, prompt: str, context_data: str, lang: str) -> str:
        """Generate a response constrained by provided context.

        Args:
            prompt: The user's input prompt or query.
            context_data: Context information that must be used to answer.
            lang: The target language code for the response.

        Returns:
            The generated response text.
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

        def _do_generate() -> Any:
            return self._model.generate_content(full_prompt)

        response = await asyncio.to_thread(_do_generate)
        text = getattr(response, "text", None)
        if text is None:
            return ""
        return text.strip()
