import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

load_dotenv()
sys.stdout.reconfigure(encoding='utf-8')

from orchestrators.unified_orchestrator import UnifiedOrchestrator
from core.dependencies import get_stt_provider, get_llm_provider, get_tts_provider, get_conversation_memory

async def main():
    stt = get_stt_provider()
    tts = get_tts_provider()
    memory = get_conversation_memory()
    
    orchestrator = UnifiedOrchestrator(
        stt,
        None,
        tts,
        memory,
        llm_factory=get_llm_provider,
        tts_factory=get_tts_provider,
    )
    
    print("Orchestrator created. Processing request...")
    try:
        result = await orchestrator.process_chat_request(
            text_query="được xây năm nào",
            lang="vi",
            session_id="test_session_123",
            artifact_id=8 # Điện Thái Hòa
        )
        print("\n--- Response Result ---")
        print("Response text:", result.response_text)
        print("Answer source:", result.answer_source)
        print("Processing steps:", result.processing_steps)
    except Exception as e:
        print("\n--- Exception raised ---")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
