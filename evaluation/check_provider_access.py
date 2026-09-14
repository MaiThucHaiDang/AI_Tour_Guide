"""Verify configured AI credentials and model access without exposing API keys."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

from core.config import settings  # noqa: E402


def _error_payload(exc: Exception) -> dict[str, str]:
    return {"status": "error", "error_type": type(exc).__name__}


def _normalize_model_names(models: list[Any]) -> set[str]:
    return {
        str(model.name).removeprefix("models/")
        for model in models
        if getattr(model, "name", None)
    }


async def _check_gemini(smoke: bool) -> list[dict[str, Any]]:
    from google import genai

    results: list[dict[str, Any]] = []
    for index, api_key in enumerate(settings.gemini_api_key_list, start=1):
        client = genai.Client(api_key=api_key)
        try:
            models = await asyncio.to_thread(lambda: list(client.models.list()))
            names = _normalize_model_names(models)
            result: dict[str, Any] = {
                "key": f"gemini_key_{index}",
                "status": "ok",
                "embedding_model_available": settings.GEMINI_EMBEDDING_MODEL in names,
                "vision_model_available": settings.GEMINI_VISION_MODEL in names,
            }
            if smoke:
                embedding_response = await asyncio.to_thread(
                    client.models.embed_content,
                    model=settings.GEMINI_EMBEDDING_MODEL,
                    contents="provider availability check",
                    config={
                        "task_type": "RETRIEVAL_QUERY",
                        "output_dimensionality": 768,
                    },
                )
                generation_response = await client.aio.models.generate_content(
                    model=settings.GEMINI_VISION_MODEL,
                    contents="Return only the word OK.",
                )
                result["embedding_dimensions"] = len(
                    embedding_response.embeddings[0].values
                )
                result["generation_succeeded"] = bool(generation_response.text)
            results.append(result)
        except Exception as exc:
            results.append({"key": f"gemini_key_{index}", **_error_payload(exc)})
        finally:
            client.close()
    return results


async def _check_groq(smoke: bool) -> list[dict[str, Any]]:
    from groq import AsyncGroq

    results: list[dict[str, Any]] = []
    for index, api_key in enumerate(settings.groq_api_key_list, start=1):
        try:
            async with AsyncGroq(api_key=api_key) as client:
                response = await client.models.list()
                names = {model.id for model in response.data}
                result: dict[str, Any] = {
                    "key": f"groq_key_{index}",
                    "status": "ok",
                    "llm_model_available": settings.GROQ_LLM_MODEL in names,
                    "stt_model_available": settings.GROQ_STT_MODEL in names,
                }
                if smoke:
                    completion = await client.chat.completions.create(
                        model=settings.GROQ_LLM_MODEL,
                        messages=[
                            {
                                "role": "system",
                                "content": "Return valid JSON and no explanatory text.",
                            },
                            {
                                "role": "user",
                                "content": 'Return exactly {"status":"ok"}.',
                            },
                        ],
                        response_format={"type": "json_object"},
                        max_tokens=256,
                        temperature=0,
                    )
                    content = completion.choices[0].message.content or ""
                    parsed = json.loads(content)
                    result["generation_succeeded"] = parsed.get("status") == "ok"
                results.append(result)
        except Exception as exc:
            results.append({"key": f"groq_key_{index}", **_error_payload(exc)})
    return results


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Also make one tiny embedding/generation request per configured provider key.",
    )
    args = parser.parse_args()

    gemini = await _check_gemini(args.smoke)
    groq = await _check_groq(args.smoke)
    gemini_ready = any(
        item.get("status") == "ok"
        and item.get("embedding_model_available") is True
        and item.get("vision_model_available") is True
        and (not args.smoke or item.get("embedding_dimensions") == 768)
        and (not args.smoke or item.get("generation_succeeded") is True)
        for item in gemini
    )
    groq_ready = any(
        item.get("status") == "ok"
        and item.get("llm_model_available") is True
        and item.get("stt_model_available") is True
        and (not args.smoke or item.get("generation_succeeded") is True)
        for item in groq
    )

    result = {
        "ready_for_full_evaluation": gemini_ready and groq_ready,
        "configured": {
            "gemini_keys": len(settings.gemini_api_key_list),
            "groq_keys": len(settings.groq_api_key_list),
        },
        "models": {
            "embedding": settings.GEMINI_EMBEDDING_MODEL,
            "vision": settings.GEMINI_VISION_MODEL,
            "graph_llm": settings.GROQ_LLM_MODEL,
        },
        "gemini": gemini,
        "groq": groq,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["ready_for_full_evaluation"]:
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
