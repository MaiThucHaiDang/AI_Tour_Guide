import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from core.config import get_settings
from google import genai

async def test_model(client, model_name):
    try:
        response = client.models.generate_content(
            model=model_name,
            contents="Hello, say test",
        )
        return f"Success: {response.text}"
    except Exception as e:
        return f"Failed: {str(e)}"

async def main():
    settings = get_settings()
    api_key = settings.GEMINI_API_KEY.strip()
    client = genai.Client(api_key=api_key)
    
    models = ["gemini-1.5-flash", "gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"]
    
    with open("scratch_gemini_models_test.txt", "w", encoding="utf-8") as f:
        for model in models:
            res = await test_model(client, model)
            f.write(f"Model: {model} -> {res}\n")
            print(f"Tested {model}")

if __name__ == "__main__":
    asyncio.run(main())
