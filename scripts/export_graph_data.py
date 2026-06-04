"""Export knowledge_facts and artifact_relations tables to a JSON file.
"""

from __future__ import annotations

import asyncio
import sys
import json
import logging
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from core.database import async_session_factory
from models.graph import KnowledgeFact, ArtifactRelation
from sqlalchemy import select

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    logger.info("Exporting Knowledge Graph data from database...")
    
    async with async_session_factory() as session:
        # Fetch facts
        facts_result = await session.execute(select(KnowledgeFact).order_by(KnowledgeFact.id))
        facts = facts_result.scalars().all()
        
        # Fetch relations
        relations_result = await session.execute(select(ArtifactRelation).order_by(ArtifactRelation.id))
        relations = relations_result.scalars().all()
        
    facts_data = [
        {
            "artifact_id": f.artifact_id,
            "fact_text": f.fact_text
        } for f in facts
    ]
    
    relations_data = [
        {
            "source_artifact_id": r.source_artifact_id,
            "target_artifact_id": r.target_artifact_id,
            "relation_type": r.relation_type,
            "weight": r.weight
        } for r in relations
    ]
    
    output_data = {
        "facts": facts_data,
        "relations": relations_data
    }
    
    dest_path = Path(__file__).resolve().parents[1] / "backend" / "data" / "knowledge_graph_data.json"
    with open(dest_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
        
    logger.info(f"Successfully exported {len(facts_data)} facts and {len(relations_data)} relations to {dest_path}")

if __name__ == "__main__":
    asyncio.run(main())
