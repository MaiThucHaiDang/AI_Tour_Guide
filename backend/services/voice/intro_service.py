"""Service for pre-generating, caching, and retrieving randomized landmark introductions."""

from __future__ import annotations

import asyncio
import json
import logging
import random
from pathlib import Path
from typing import Dict, List, Optional
from sqlalchemy import select

from core.database import async_session_factory
from models.artifact import Artifact
from core.dependencies import get_llm_provider

_LOGGER = logging.getLogger(__name__)

CACHE_FILE_PATH = Path(__file__).resolve().parents[2] / "data" / "pre_generated_intros.json"

class IntroService:
    def __init__(self) -> None:
        self._cache: Dict[str, List[str]] = {}
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the cache from JSON file or generate in the background."""
        if self._initialized:
            return

        try:
            if CACHE_FILE_PATH.exists():
                with open(CACHE_FILE_PATH, "r", encoding="utf-8") as f:
                    raw_data = json.load(f)
                    self._cache = raw_data
                _LOGGER.info("Successfully loaded pre-generated introductions cache with %d entries.", len(self._cache))
                self._initialized = True
                return

            _LOGGER.info("Pre-generated introductions cache file not found. Starting background generation task...")
            # Run the generation in the background so it does not block application startup
            asyncio.create_task(self._generate_cache_in_background())
            self._initialized = True
        except Exception as exc:
            _LOGGER.error("Failed to initialize IntroService: %s", exc, exc_info=True)

    def get_random_intro(self, artifact_id: int, lang: str = "vi") -> Optional[str]:
        """Retrieve a random pre-generated introduction for the given artifact ID."""
        key = f"{artifact_id}:{lang}"
        versions = self._cache.get(key)
        if versions:
            selected = random.choice(versions)
            _LOGGER.info("Retrieved random intro cache for key %s (1 of %d versions)", key, len(versions))
            return selected
        return None

    async def _generate_cache_in_background(self) -> None:
        """Background generator to call LLM and pre-generate the 4 styles for all artifacts."""
        _LOGGER.info("Starting background pre-generation of artifact intros...")
        try:
            # Load mapped artifact IDs from map_calibrated.json
            map_file = Path(__file__).resolve().parents[2] / "data" / "map_calibrated.json"
            allowed_ids = set()
            if map_file.exists():
                try:
                    with open(map_file, "r", encoding="utf-8") as f:
                        map_data = json.load(f)
                        allowed_ids = {int(item["id"]) for item in map_data.get("artifacts", []) if "id" in item}
                    _LOGGER.info("Loaded %d allowed mapped landmark IDs from map_calibrated.json", len(allowed_ids))
                except Exception as e:
                    _LOGGER.error("Failed to load map_calibrated.json: %s", e)

            # 1. Fetch all artifacts
            async with async_session_factory() as session:
                result = await session.execute(select(Artifact).order_by(Artifact.art_id))
                artifacts = result.scalars().all()
                artifacts = list(artifacts)

            if allowed_ids:
                artifacts = [art for art in artifacts if int(art.art_id) in allowed_ids]

            if not artifacts:
                _LOGGER.warning("No artifacts found in the database matching map_calibrated.json to pre-generate.")
                return

            llm = get_llm_provider()
            new_cache: Dict[str, List[str]] = {}

            # Generate sequentially with a small delay to avoid overwhelming rate limits
            for art in artifacts:
                art_id = art.art_id
                
                # ─── Vietnamese ───
                vi_key = f"{art_id}:vi"
                vi_name = art.name_vi
                vi_history = art.history_text_vi or ""
                if len(vi_history.strip()) > 50:
                    try:
                        vi_versions = await self._generate_versions_via_llm(llm, vi_name, vi_history, "vi")
                        if vi_versions:
                            new_cache[vi_key] = vi_versions
                            _LOGGER.debug("Generated 4 VI versions for %s", vi_name)
                    except Exception as e:
                        _LOGGER.error("Failed to generate VI intro for %s (ID: %d): %s", vi_name, art_id, e)
                    await asyncio.sleep(1.0) # Rate limit cooling

                # ─── English ───
                en_key = f"{art_id}:en"
                en_name = art.name_en or art.name_vi
                en_history = art.history_text_en or art.history_text_vi or ""
                if len(en_history.strip()) > 50:
                    try:
                        en_versions = await self._generate_versions_via_llm(llm, en_name, en_history, "en")
                        if en_versions:
                            new_cache[en_key] = en_versions
                            _LOGGER.debug("Generated 4 EN versions for %s", en_name)
                    except Exception as e:
                        _LOGGER.error("Failed to generate EN intro for %s (ID: %d): %s", en_name, art_id, e)
                    await asyncio.sleep(1.0) # Rate limit cooling

            if new_cache:
                self._cache = new_cache
                # Save to disk
                CACHE_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
                with open(CACHE_FILE_PATH, "w", encoding="utf-8") as f:
                    json.dump(new_cache, f, ensure_ascii=False, indent=2)
                _LOGGER.info("Background pre-generation completed. Cached saved to: %s", CACHE_FILE_PATH)

        except Exception as exc:
            _LOGGER.exception("Failed in background intro pre-generation: %s", exc)

    async def _generate_versions_via_llm(self, llm, name: str, history: str, lang: str) -> Optional[List[str]]:
        """Call Gemini/Groq to generate a single rich introduction version."""
        if lang == "vi":
            prompt = (
                f"Bạn là hướng dẫn viên du lịch AI chuyên nghiệp tại Kinh thành Huế. "
                f"Hãy viết một bài thuyết minh giới thiệu ngắn gọn, lôi cuốn và tự nhiên về di tích '{name}' dựa trên tài liệu lịch sử sau:\n"
                f"{history[:1200]}\n\n"
                f"Yêu cầu:\n"
                f"- Kết hợp hài hòa cả yếu tố lịch sử quan trọng và nét đặc sắc nổi bật về kiến trúc.\n"
                f"- Giọng văn sinh động, tự nhiên, gần gũi, cuốn hút người nghe.\n"
                f"- Độ dài từ 100 - 120 từ.\n\n"
                f"Hãy trả về kết quả dưới định dạng JSON thuần túy (không dùng markdown codeblock, không thêm bất kỳ văn bản dẫn giải nào khác) theo cấu trúc sau:\n"
                f"{{\n"
                f"  \"versions\": [\n"
                f"    \"Nội dung thuyết minh hoàn chỉnh ở đây...\"\n"
                f"  ]\n"
                f"}}"
            )
        else:
            prompt = (
                f"You are a professional AI tour guide at the Hue Imperial City. "
                f"Write a concise, engaging, and natural introduction about '{name}' based on this historical reference:\n"
                f"{history[:1200]}\n\n"
                f"Requirements:\n"
                f"- Harmoniously blend historical significance with prominent architectural features.\n"
                f"- Lively, warm, and welcoming tone of a local tour guide.\n"
                f"- Word count: 100 - 120 words.\n\n"
                f"Return the result in pure JSON format (do not use markdown codeblock, do not add any conversational intros/outros):\n"
                f"{{\n"
                f"  \"versions\": [\n"
                f"    \"The complete introduction goes here...\"\n"
                f"  ]\n"
                f"}}"
            )

        resp = await llm.generate_response(prompt, context_data="", lang=lang)
        clean_resp = resp.strip()
        
        # Strip markdown wrapper if present
        if clean_resp.startswith("```"):
            lines = clean_resp.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            clean_resp = "\n".join(lines).strip()

        try:
            data = json.loads(clean_resp)
            versions = data.get("versions", [])
            if len(versions) >= 1:
                cleaned_versions = []
                for v in versions:
                    if isinstance(v, dict):
                        cleaned_versions.append(v.get("text") or v.get("noi_dung") or v.get("content") or str(v))
                    else:
                        cleaned_versions.append(str(v))
                return cleaned_versions[:1]
            _LOGGER.warning("LLM generated 0 versions instead of 1 for %s.", name)
            return None
        except Exception as e:
            _LOGGER.error("Failed to parse LLM intro json: %s. Raw response: %s", e, resp)
            return None

# Singleton instance
intro_service = IntroService()
