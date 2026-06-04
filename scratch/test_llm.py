import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

load_dotenv()
sys.stdout.reconfigure(encoding='utf-8')

from core.dependencies import get_llm_provider
from core.config import get_settings

async def main():
    settings = get_settings()
    print("LLM Provider Order:", settings.llm_provider_list)
    print("Gemini model:", settings.GEMINI_TEXT_MODEL)
    print("Groq model:", settings.GROQ_LLM_MODEL)
    print("Gemini key starting with:", settings.GEMINI_API_KEY[:10] if settings.GEMINI_API_KEY else "None")
    print("Groq key starting with:", settings.GROQ_API_KEY[:10] if settings.GROQ_API_KEY else "None")
    
    try:
        provider = get_llm_provider()
        print("Obtained provider:", type(provider))
        
        # Test Gemini directly
        print("\n--- Testing provider response ---")
        response = await provider.generate_response(
            prompt="được xây năm nào",
            context_data="Điện Thái Hòa được xây dựng vào năm 1805 dưới thời vua Gia Long.",
            lang="vi"
        )
        print("Response:", response)
    except Exception as e:
        print("\n--- Error encountered ---")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
