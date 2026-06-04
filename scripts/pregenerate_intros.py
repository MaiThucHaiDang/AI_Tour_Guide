"""Pre-generate introductions cache file using Groq llama-3.1-8b-instant to avoid rate limits at backend startup.
"""

from __future__ import annotations

import asyncio
import sys
import json
import logging
import os
import re
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq
from sqlalchemy import select

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from core.database import async_session_factory
from models.artifact import Artifact

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    logger.error("GROQ_API_KEY not found in environment.")
    sys.exit(1)

groq_client = Groq(api_key=groq_api_key)
model_name = "llama-3.1-8b-instant"  # Using free model with high quotas

CACHE_FILE_PATH = Path(__file__).resolve().parents[1] / "backend" / "data" / "pre_generated_intros.json"

async def generate_versions_via_groq(name: str, history: str, lang: str) -> list[str] | None:
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

    try:
        response = groq_client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a JSON assistant. Always respond with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.2
        )
        resp_text = response.choices[0].message.content.strip()
        
        # Clean codeblock wrappers
        if resp_text.startswith("```"):
            resp_text = re.sub(r'^```(?:json)?\n', '', resp_text)
            resp_text = re.sub(r'\n```$', '', resp_text)
            
        data = json.loads(resp_text)
        versions = data.get("versions", [])
        if len(versions) >= 1:
            cleaned_versions = []
            for v in versions:
                if isinstance(v, dict):
                    cleaned_versions.append(v.get("text") or v.get("noi_dung") or v.get("content") or str(v))
                else:
                    cleaned_versions.append(str(v))
            return cleaned_versions[:1]
        logger.warning(f"Generated 0 versions instead of 1 for {name}.")
        return None
    except Exception as e:
        logger.error(f"Error generating versions for {name}: {e}")
        return None

async def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    logger.info("Fetching artifacts from database...")
    async with async_session_factory() as session:
        result = await session.execute(select(Artifact).order_by(Artifact.art_id))
        artifacts = list(result.scalars().all())

    if not artifacts:
        logger.error("No artifacts found in the database. Run seed_enriched_data.py first.")
        return

    logger.info(f"Loaded {len(artifacts)} artifacts. Starting cache pre-generation...")
    new_cache = {}

    for art in artifacts:
        art_id = art.art_id
        
        # ─── Vietnamese ───
        vi_key = f"{art_id}:vi"
        vi_name = art.name_vi
        vi_history = art.history_text_vi or ""
        if len(vi_history.strip()) > 50:
            success = False
            attempts = 3
            while not success and attempts > 0:
                logger.info(f"Generating VI intros for {vi_name} (ID: {art_id})...")
                versions = await generate_versions_via_groq(vi_name, vi_history, "vi")
                if versions:
                    new_cache[vi_key] = versions
                    success = True
                else:
                    attempts -= 1
                    logger.warning(f"Retrying VI intro generation. Attempts left: {attempts}")
                    await asyncio.sleep(5)
            await asyncio.sleep(3) # Safe cooling delay

        # ─── English ───
        en_key = f"{art_id}:en"
        en_name = art.name_en or art.name_vi
        en_history = art.history_text_en or art.history_text_vi or ""
        if len(en_history.strip()) > 50:
            success = False
            attempts = 3
            while not success and attempts > 0:
                logger.info(f"Generating EN intros for {en_name} (ID: {art_id})...")
                versions = await generate_versions_via_groq(en_name, en_history, "en")
                if versions:
                    new_cache[en_key] = versions
                    success = True
                else:
                    attempts -= 1
                    logger.warning(f"Retrying EN intro generation. Attempts left: {attempts}")
                    await asyncio.sleep(5)
            await asyncio.sleep(3) # Safe cooling delay

    if new_cache:
        CACHE_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CACHE_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(new_cache, f, ensure_ascii=False, indent=2)
        logger.info(f"Successfully generated cache and saved to: {CACHE_FILE_PATH}")
    else:
        logger.error("Failed to generate cache for any artifacts.")

if __name__ == "__main__":
    asyncio.run(main())
