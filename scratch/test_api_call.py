import requests
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

url = "http://127.0.0.1:8000/api/v1/chat/unified"
data = {
    "text": "được xây năm nào",
    "lang": "vi",
    "session_id": "test_session_123",
    "artifact_id": 8 # Điện Thái Hòa
}

try:
    print(f"Sending request to {url}...")
    response = requests.post(url, data=data, timeout=10)
    print("Status Code:", response.status_code)
    resp_json = response.json()
    with open("scratch/api_response.json", "w", encoding="utf-8") as f:
        json.dump(resp_json, f, indent=2, ensure_ascii=False)
    print("Response written to scratch/api_response.json")
    print("Response text:", resp_json.get("response_text"))
except Exception as e:
    print("Error calling API:", e)
