"""Automated Knowledge Graph Construction using Gemini.

This script:
1. Fetches all artifacts from the database.
2. Uses Gemini to extract atomic facts from history descriptions.
3. Uses Gemini to identify relationships between artifacts.
4. Populates the knowledge_facts and artifact_relations tables.
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from core.config import settings
from core.database import async_session_factory
from models.artifact import Artifact
from models.graph import KnowledgeFact, ArtifactRelation, ArtifactFAQ
from utils.ai_utils import retry_with_backoff
from groq import AsyncGroq
from sqlalchemy import select, delete

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GraphBuilder:
    def __init__(self):
        api_keys = settings.groq_api_key_list
        if not api_keys:
            raise ValueError("GROQ_API_KEY is not set in environment variables.")
        self.clients = [
            AsyncGroq(api_key=api_key, max_retries=0) for api_key in api_keys
        ]
        self.client = self.clients[0]
        self.next_client_index = 0
        self.model_name = settings.GROQ_LLM_MODEL

    async def get_all_artifacts(self) -> List[Artifact]:
        async with async_session_factory() as session:
            result = await session.execute(select(Artifact))
            return list(result.scalars().all())

    async def extract_knowledge(self, artifact: Artifact, all_artifacts: List[Artifact]) -> Dict[str, Any]:
        """Ask Groq to extract facts and identify relations."""
        artifact_list_str = "\n".join([f"- ID {a.art_id}: {a.name_vi} / {a.name_en}" for a in all_artifacts if a.art_id != artifact.art_id])
        
        prompt = f"""
Phân tích hiện vật lịch sử sau đây và trích xuất dữ liệu cho Đồ thị Tri thức (Knowledge Graph).

TÊN HIỆN VẬT: {artifact.name_vi} / {artifact.name_en}
MÔ TẢ LỊCH SỬ:
{artifact.history_text_vi}

DANH SÁCH CÁC HIỆN VẬT KHÁC TRONG HỆ THỐNG:
{artifact_list_str}

YÊU CẦU:
1. Trích xuất các "Sự thật" (Facts): Chia nhỏ mô tả thành các câu khẳng định ngắn gọn, súc tích về hiện vật này (tối đa 5-7 facts).
2. Xác định "Quan hệ" (Relations): Tìm mối liên hệ giữa hiện vật này với DANH SÁCH CÁC HIỆN VẬT KHÁC ở trên.
   Các loại quan hệ cho phép: 
   - SAME_AUTHOR: Cùng tác giả/triều đại.
   - SAME_PERIOD: Cùng thời kỳ lịch sử (ví dụ: Nhà Nguyễn, Kháng chiến chống Mỹ).
   - LOCATED_NEAR: Nằm gần nhau về địa lý.
   - HISTORICAL_LINK: Có liên quan về sự kiện lịch sử.

TRẢ VỀ ĐỊNH DẠNG JSON SAU:
{{
  "facts": ["fact 1", "fact 2", ...],
  "relations": [
    {{"target_id": ID_CỦA_HIỆN_VẬT_LIÊN_QUAN, "type": "LOẠI_QUAN_HỆ", "reason": "Giải thích ngắn gọn"}}
  ]
}}
"""
        last_exc: Exception | None = None
        client_indices = [
            (self.next_client_index + offset) % len(self.clients)
            for offset in range(len(self.clients))
        ]
        for client_index in client_indices:
            client = self.clients[client_index]
            label = client_index + 1
            try:
                async def _call_groq():
                    response = await client.chat.completions.create(
                        model=self.model_name,
                        messages=[
                            {"role": "system", "content": "You are a data extraction assistant. Always respond with valid JSON."},
                            {"role": "user", "content": prompt}
                        ],
                        response_format={"type": "json_object"}
                    )
                    return response.choices[0].message.content

                response_text = await retry_with_backoff(_call_groq, max_retries=0)
                if not response_text:
                    raise RuntimeError("Groq returned an empty graph response")
                result = json.loads(response_text)
                self.next_client_index = (client_index + 1) % len(self.clients)
                logger.info("Groq graph key %d succeeded", label)
                return result
            except Exception as exc:
                last_exc = exc
                logger.warning(
                    "Groq graph key %d failed for artifact %s: %s",
                    label,
                    artifact.art_id,
                    exc,
                )

        logger.error(
            "All Groq keys failed for artifact %s: %s", artifact.art_id, last_exc
        )
        return {"facts": [], "relations": []}

    async def build(self):
        logger.info("Starting Knowledge Graph construction...")
        artifacts = await self.get_all_artifacts()
        if not artifacts:
            logger.warning("No artifacts found in database. Please run seed_data.py first.")
            return

        async with async_session_factory() as session:
            # Handle Foreign Key constraints carefully
            logger.info("Cleaning up existing graph data...")
            
            # 1. Delete relations
            await session.execute(delete(ArtifactRelation))
            
            # 2. Clear references in FAQ instead of deleting them (preserves expensive embeddings)
            from sqlalchemy import update
            await session.execute(update(ArtifactFAQ).values(fact_id=None))
            
            # 3. Delete old facts
            await session.execute(delete(KnowledgeFact))
            
            await session.commit()

            for artifact in artifacts:
                logger.info(f"Processing artifact {artifact.art_id}: {artifact.name_vi}")
                data = await self.extract_knowledge(artifact, artifacts)
                
                # Add Facts
                for fact_text in data.get("facts", []):
                    session.add(KnowledgeFact(artifact_id=artifact.art_id, fact_text=fact_text))
                
                # Add Relations
                for rel in data.get("relations", []):
                    try:
                        target_id = int(rel["target_id"])
                        # Basic validation: ensure target exists and isn't self
                        if target_id != artifact.art_id and any(a.art_id == target_id for a in artifacts):
                            session.add(ArtifactRelation(
                                source_artifact_id=artifact.art_id,
                                target_artifact_id=target_id,
                                relation_type=rel["type"],
                                weight=1.0
                            ))
                    except (ValueError, KeyError):
                        continue
                
                await session.flush()
                # Wait a bit more to avoid hitting rate limits too hard (3s is safer for free tiers)
                await asyncio.sleep(3)

            await session.commit()
            logger.info("Knowledge Graph construction complete!")

if __name__ == "__main__":
    builder = GraphBuilder()
    asyncio.run(builder.build())
