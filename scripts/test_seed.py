"""Quick test for chat endpoint response length."""
import httpx

for lang, text in [
    ("vi", "Hãy giới thiệu về Cửa Hòa Bình"),
    ("en", "Tell me about Hoa Binh Gate in detail"),
]:
    r = httpx.post("http://127.0.0.1:8000/api/v1/chat/unified",
                   data={"text": text, "lang": lang}, timeout=120)
    resp = r.json().get("response_text", "")
    print(f"[{lang.upper()}] {len(resp)} chars, {len(resp.split())} words")
