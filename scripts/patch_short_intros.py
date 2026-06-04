import asyncio
import json
import os
import re
import sys
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq

# Load environment
load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    print("Error: GROQ_API_KEY not found in environment.")
    sys.exit(1)

groq_client = Groq(api_key=groq_api_key)
model_name = "llama-3.1-8b-instant"

DATA_TXT_PATH = Path(__file__).resolve().parents[1] / "data.txt"
CACHE_FILE_PATH = Path(__file__).resolve().parents[1] / "backend" / "data" / "pre_generated_intros.json"

TARGET_IDS = {3, 5, 7, 9, 15, 17}

def parse_raw_data():
    """Parse raw facts from data.txt grouped by landmark ID."""
    with open(DATA_TXT_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Split by double divider lines or section blocks
    sections = re.split(r'={10,}\s*\n(\d{2})\.\s*([^\n]+)\n\s*={10,}', content)
    
    parsed_facts = {}
    
    # sections[0] is the header text
    # sections[i] is ID (e.g. "01"), sections[i+1] is Name (e.g. "CỬA HÒA BÌNH"), sections[i+2] is facts
    for idx in range(1, len(sections), 3):
        art_id = int(sections[idx])
        name = sections[idx+1].strip()
        facts_text = sections[idx+2]
        
        # Extract lines starting with digits (e.g. "001. ")
        facts = []
        for line in facts_text.splitlines():
            line = line.strip()
            if re.match(r'^\d{3}\.\s*', line):
                facts.append(line)
        
        parsed_facts[art_id] = {
            "name": name,
            "facts": "\n".join(facts)
        }
        
    return parsed_facts

async def generate_vi_intro(name: str, facts: str) -> str:
    prompt = (
        f"Bạn là hướng dẫn viên du lịch AI chuyên nghiệp tại Kinh thành Huế.\n"
        f"Hãy viết một bài thuyết minh giới thiệu chi tiết, lôi cuốn và tự nhiên về di tích '{name}' dựa trên tài liệu lịch sử sau:\n"
        f"{facts[:4000]}\n\n"
        f"Yêu cầu:\n"
        f"- Kết hợp hài hòa cả các yếu tố lịch sử quan trọng, mốc thời gian, triều đại và nét đặc sắc nổi bật về kiến trúc, hiện trạng bảo tồn.\n"
        f"- Giọng văn sinh động, truyền cảm, cuốn hút người nghe như đang thuyết minh trực tiếp tại hiện trường.\n"
        f"- Độ dài từ 300 - 450 từ (thuyết minh chi tiết, sâu sắc).\n"
        f"- Phải trả về một chuỗi văn bản thuyết minh liên tục duy nhất trong mảng \"versions\" (không chia nhỏ thành tiêu đề hay các cặp khóa-giá trị phụ).\n\n"
        f"Hãy trả về kết quả dưới định dạng JSON thuần túy (không dùng markdown codeblock, không thêm bất kỳ văn bản dẫn giải nào khác) theo cấu trúc sau:\n"
        f"{{\n"
        f"  \"versions\": [\n"
        f"    \"Nội dung thuyết minh hoàn chỉnh ở đây...\"\n"
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
            temperature=0.2,
            max_tokens=2048
        )
        resp_text = response.choices[0].message.content.strip()
        
        # Clean codeblock wrappers
        if resp_text.startswith("```"):
            resp_text = re.sub(r'^```(?:json)?\n', '', resp_text)
            resp_text = re.sub(r'\n```$', '', resp_text)
            
        data = json.loads(resp_text)
        versions = data.get("versions", [])
        if not versions:
            return ""
        
        if isinstance(versions, dict):
            return "\n\n".join([str(v).strip() for v in versions.values() if v])
            
        if isinstance(versions, list):
            if not versions:
                return ""
            if isinstance(versions[0], dict):
                if len(versions) > 1:
                    parts = []
                    for item in versions:
                        if isinstance(item, dict):
                            part = item.get("text") or item.get("noi_dung") or item.get("content") or "\n\n".join([str(v).strip() for v in item.values() if v])
                            parts.append(part)
                        else:
                            parts.append(str(item))
                    return "\n\n".join([p.strip() for p in parts if p])
                else:
                    return "\n\n".join([str(v).strip() for v in versions[0].values() if v])
            
            if len(versions) > 1:
                first_len = len(str(versions[0]).split())
                if first_len < 200:
                    return "\n\n".join([str(v).strip() for v in versions if v])
            
            return str(versions[0])
            
        return str(versions)
    except Exception as e:
        print(f"Error generating intro for {name}: {e}")
        return ""

async def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    print("Parsing raw data from data.txt...")
    all_facts = parse_raw_data()
    
    if not CACHE_FILE_PATH.exists():
        print(f"Error: Cache file not found at {CACHE_FILE_PATH}")
        return
        
    with open(CACHE_FILE_PATH, "r", encoding="utf-8") as f:
        cache = json.load(f)
        
    for art_id in TARGET_IDS:
        if art_id not in all_facts:
            print(f"Warning: No facts found for ID {art_id} in data.txt")
            continue
            
        name = all_facts[art_id]["name"]
        facts = all_facts[art_id]["facts"]
        
        print(f"Generating detailed VI intro for ID {art_id} ({name})...")
        intro = await generate_vi_intro(name, facts)
        
        if intro and len(intro.split()) >= 250:
            key = f"{art_id}:vi"
            cache[key] = [intro]
            print(f"Successfully updated {key} ({len(intro.split())} words)")
        else:
            print(f"Failed or generated too short text for {name}, trying again...")
            intro = await generate_vi_intro(name, facts)
            if intro:
                key = f"{art_id}:vi"
                cache[key] = [intro]
                print(f"Updated {key} with retry ({len(intro.split())} words)")
                
        await asyncio.sleep(6)  # Rate limit cooling

    with open(CACHE_FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)
    print("Cache file successfully patched!")

if __name__ == "__main__":
    asyncio.run(main())
