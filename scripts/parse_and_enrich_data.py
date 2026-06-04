import os
import re
import json
import time
import sys
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load env variables
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None

from groq import Groq
groq_api_key = os.getenv("GROQ_API_KEY")
groq_model = os.getenv("GROQ_LLM_MODEL", "llama-3.3-70b-versatile")
groq_client = Groq(api_key=groq_api_key) if groq_api_key else None

# Setup paths
ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_TXT = ROOT_DIR / "data.txt"
ENRICHED_JSON = ROOT_DIR / "backend" / "data" / "enriched_artifacts.json"

# Define mappings from seed_data.py name to data.txt sections and keywords
MAPPINGS = [
    {
        "id": 1,
        "name_vi": "Cửa Hòa Bình",
        "official_num": "01",
        "ytb_header": "- cửa hòa bình:",
        "keywords": ["hòa bình", "củng thần", "địa bình", "cửa bắc"]
    },
    {
        "id": 2,
        "name_vi": "Điện Kiến Trung",
        "official_num": "02",
        "ytb_header": "- điện kiến trung:",
        "keywords": ["kiến trung", "minh viễn", "du cửu"]
    },
    {
        "id": 3,
        "name_vi": "Cung Trường Sanh",
        "official_num": "03",
        "ytb_header": "- Cung trường sanh, cung diên thọ:",
        "keywords": ["trường sanh", "trường ninh", "vạn phúc lâu", "tân nguyệt", "đào nguyên", "ngũ đại đồng đường"]
    },
    {
        "id": 4,
        "name_vi": "Cung Diên Thọ",
        "official_num": "04",
        "ytb_header": "- Cung trường sanh, cung diên thọ:",
        "keywords": ["diên thọ", "thọ ninh", "trường du tạ", "tả trà", "khương ninh", "tịnh minh", "từ cung", "từ dũ"]
    },
    {
        "id": 5,
        "name_vi": "Cửa Chương Đức",
        "official_num": "05",
        "ytb_header": "- cửa chương đức và hiển nhơn:",
        "keywords": ["chương đức", "cửa tây"]
    },
    {
        "id": 6,
        "name_vi": "Hưng Miếu (Hưng Tổ Miếu)",
        "official_num": "06",
        "ytb_header": "- hưng tổ miếu:",
        "keywords": ["hưng miếu", "hưng tổ", "hoàng khảo", "nguyễn phúc luân", "khương ninh"]
    },
    {
        "id": 7,
        "name_vi": "Thế Miếu (Thế Tổ Miếu)",
        "official_num": "07",
        "ytb_header": "- thế miếu:",
        "keywords": ["thế miếu", "thế tổ", "cửu đỉnh", "hiển lâm các", "cao đỉnh", "nhân đỉnh", "chương đỉnh", "anh đỉnh", "nghị đỉnh", "thuần đỉnh", "tuyên đỉnh", "dụ đỉnh", "huyền đỉnh"]
    },
    {
        "id": 8,
        "name_vi": "Điện Thái Hòa",
        "official_num": "08",
        "ytb_header": "- điện thái hòa:",
        "keywords": ["thái hòa", "ngai vàng", "bửu tán", "sân đại triều", "nhất thi nhất họa", "trùng thiềm điệp ốc", "cầu trung đạo"]
    },
    {
        "id": 9,
        "name_vi": "Nền điện Cần Chánh",
        "official_num": "09",
        "ytb_header": "- nền điện cần chánh",
        "keywords": ["cần chánh"]
    },
    {
        "id": 10,
        "name_vi": "Duyệt Thị Đường",
        "official_num": "10",
        "ytb_header": "- Duyệt thị đường:",
        "keywords": ["duyệt thị", "duyệt thị đường", "nhà hát"]
    },
    {
        "id": 11,
        "name_vi": "Phủ Nội Vụ",
        "official_num": "11",
        "ytb_header": "- phủ nội vụ:",
        "keywords": ["nội vụ", "phủ nội vụ"]
    },
    {
        "id": 12,
        "name_vi": "Vườn Cơ Hạ",
        "official_num": "12",
        "ytb_header": "- vườn cơ hạ:",
        "keywords": ["cơ hạ", "vườn cơ hạ"]
    },
    {
        "id": 13,
        "name_vi": "Triệu Miếu (Triệu Tổ Miếu)",
        "official_num": "13",
        "ytb_header": "- triệu tổ miếu:",
        "keywords": ["triệu miếu", "triệu tổ", "nguyễn kim"]
    },
    {
        "id": 14,
        "name_vi": "Thái Miếu (Thái Tổ Miếu)",
        "official_num": "14",
        "ytb_header": "- thái miếu:",
        "keywords": ["thái miếu", "thái tổ", "chúa nguyễn", "hiển nhơn"]
    },
    {
        "id": 15,
        "name_vi": "Cửa Hiển Nhơn",
        "official_num": "15",
        "ytb_header": "- cửa chương đức và hiển nhơn:",
        "keywords": ["hiển nhơn", "cửa đông"]
    },
    {
        "id": 16,
        "name_vi": "Điện Long An (Bảo tàng Cổ vật Cung đình Huế)",
        "official_num": "16",
        "ytb_header": "- điện long an:",
        "keywords": ["long an", "điện long an", "bảo tàng cổ vật", "cổ vật cung đình"]
    },
    {
        "id": 17,
        "name_vi": "Ngọ Môn",
        "official_num": "17",
        "ytb_header": "- Ngọ Môn:",
        "keywords": ["ngọ môn", "ngũ phụng", "ban sóc", "truyền lô", "bảo đại thoái vị"]
    }
]

def extract_transcript_context(keywords, transcripts_text, window_size=20):
    lines = transcripts_text.split('\n')
    matching_indices = []
    for idx, line in enumerate(lines):
        line_lower = line.lower()
        if any(kw in line_lower for kw in keywords):
            matching_indices.append(idx)
    
    # Merge intervals
    intervals = []
    for idx in matching_indices:
        start = max(0, idx - window_size)
        end = min(len(lines), idx + window_size + 1)
        if not intervals:
            intervals.append((start, end))
        else:
            prev_start, prev_end = intervals[-1]
            if start <= prev_end:
                intervals[-1] = (prev_start, max(prev_end, end))
            else:
                intervals.append((start, end))
    
    extracted_blocks = []
    for start, end in intervals:
        extracted_blocks.append('\n'.join(lines[start:end]))
    return '\n\n---\n\n'.join(extracted_blocks)

def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    print(f"Reading {DATA_TXT}...")
    with open(DATA_TXT, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Split into Part 1 (Official) and Part 2 (YouTube)
    parts = content.split("##### BỔ SUNG ĐA DẠNG TỪ YOUTOBE")
    if len(parts) < 2:
        print("ERROR: Could not split file by '##### BỔ SUNG ĐA DẠNG TỪ YOUTOBE'")
        sys.exit(1)
        
    official_text = parts[0]
    youtube_text = parts[1]
    
    # 1. Parse TÀI LIỆU CHÍNH GỐC
    print("Parsing official locations and facts...")
    pattern = r'={10,}\s*\n(\d{2})\.\s*([^\n]+)\n\s*={10,}'
    matches = list(re.finditer(pattern, official_text))
    
    official_data = {}
    for i, match in enumerate(matches):
        loc_num = match.group(1)
        loc_name = match.group(2).strip()
        start_idx = match.end()
        end_idx = matches[i+1].start() if i+1 < len(matches) else len(official_text)
        section_content = official_text[start_idx:end_idx].strip()
        
        facts = []
        for line in section_content.split('\n'):
            line = line.strip()
            if re.match(r'^\d{3}\.', line):
                facts.append(line)
        official_data[loc_num] = {
            "name": loc_name,
            "facts": facts
        }
    print(f"Parsed {len(official_data)} official locations.")
    
    # 2. Parse YouTube Subheadings under `from ytb:`
    print("Parsing YouTube notes...")
    ytb_part = youtube_text.split("------------------------------------------------------------------------")[0]
    ytb_lines = ytb_part.split('\n')
    
    subheading_indices = []
    for idx, line in enumerate(ytb_lines):
        line_s = line.strip()
        if line_s.startswith('- ') and (line_s.endswith(':') or line_s == "- nền điện cần chánh"):
            subheading_indices.append((idx, line_s))
            
    youtube_sections = {}
    for i, (idx, heading) in enumerate(subheading_indices):
        start = idx + 1
        end = subheading_indices[i+1][0] if i+1 < len(subheading_indices) else len(ytb_lines)
        content_lines = ytb_lines[start:end]
        section_text = '\n'.join([l.strip() for l in content_lines if l.strip()])
        youtube_sections[heading.lower()] = section_text
    print(f"Parsed {len(youtube_sections)} YouTube notes sections.")
    
    # Extract transcripts part (from line 3206 onwards)
    transcripts_part = ""
    transcript_start_idx = youtube_text.find("- Hướng dẫn viên:")
    if transcript_start_idx != -1:
        transcripts_part = youtube_text[transcript_start_idx:]
    print(f"Transcripts text size: {len(transcripts_part)} characters.")
    
    # 3. Call Gemini to enrich each location
    enriched_results = []
    
    for item in MAPPINGS:
        loc_id = item["id"]
        name_vi = item["name_vi"]
        num = item["official_num"]
        ytb_header_key = item["ytb_header"].lower()
        keywords = item["keywords"]
        
        print(f"\nProcessing Location {loc_id}: {name_vi}...")
        
        # Get official facts
        off_info = official_data.get(num, {"name": name_vi, "facts": []})
        official_facts_str = "\n".join(off_info["facts"])
        
        # Get YouTube notes
        youtube_notes_str = youtube_sections.get(ytb_header_key, "Không có ghi chú tóm tắt riêng.")
        
        # Extract transcript context (optimized window size to prevent rate limits)
        transcript_context_str = extract_transcript_context(keywords, transcripts_part, window_size=5)[:3000]
        if not transcript_context_str:
            transcript_context_str = "Không tìm thấy đoạn thoại trực tiếp liên quan trong transcript."
            
        # Build prompt
        prompt = f"""Bạn là một nhà nghiên cứu lịch sử và chuyên gia thuyết minh du lịch cao cấp về Di sản Huế.
Nhiệm vụ của bạn là tổng hợp các thông tin dưới đây về di tích/hiện vật "{name_vi}" để tạo ra một bài thuyết minh lịch sử và kiến trúc cực kỳ chi tiết, phong phú, sống động và hấp dẫn.

THÔNG TIN ĐẦU VÀO:
1. Danh sách Sự thật chính thống (Ground Truth - TÀI LIỆU CHÍNH GỐC):
{official_facts_str}

2. Ghi chú tóm tắt từ YouTube:
{youtube_notes_str}

3. Các đoạn lời thoại thô trích xuất từ YouTube:
{transcript_context_str}

YÊU CẦU NỘI DUNG:
1. Đầy đủ chi tiết: Đảm bảo không bỏ sót bất kỳ sự thật quan trọng nào từ tài liệu chính thống (các mốc năm, các đời vua liên quan, tên gọi cũ, chức năng sử dụng, cấu trúc kiến trúc, kích thước, số lượng cột, loại ngói...).
2. Văn phong phong phú và cuốn hút: Sử dụng lối hành văn trôi chảy, sinh động, tự nhiên của hướng dẫn viên du lịch chuyên nghiệp (được lấy cảm hứng từ các lời thoại YouTube nhưng được chuẩn hóa, nâng cấp học thuật hơn). Không dùng danh sách gạch đầu dòng thô.
3. Sửa lỗi chính tả/nghe từ giọng nói: Bản ghi âm YouTube có thể chứa lỗi nhận diện từ (ví dụ: "Kim Thành ủy" -> "Kinh thành Huế", "Thiện Khánh môn" -> "Hiển Khánh môn" hoặc "Diên Khánh môn" tùy ngữ cảnh, "giáo" -> "giáp", v.v.). Bạn cần tự động sửa những lỗi này dựa trên kiến thức lịch sử chuẩn xác.
4. Bài viết cần có bố cục mạch lạc gồm nhiều đoạn văn (mỗi đoạn tập trung vào một khía cạnh như: lịch sử & tên gọi, kiến trúc & cấu trúc, công năng & vai trò lịch sử, bài học & bảo tồn ngày nay).
5. Trả về đồng thời phiên bản tiếng Anh (history_text_en) được dịch/thuyết minh tương ứng, đảm bảo dịch thuật chuẩn xác các thuật ngữ lịch sử (ví dụ: "Ngọ Môn" -> "Meridian Gate", "Lầu Ngũ Phụng" -> "Five Phoenix Pavilion", "Trường Du Tạ" -> "Trường Du Pavilion/Water Pavilion", "Khương Ninh Các" -> "Khương Ninh Pavilion", v.v.).

HÃY TRẢ VỀ KẾT QUẢ DƯỚI ĐỊNH DẠNG JSON SAU (chỉ trả về JSON, không kèm giải thích hay ký hiệu ```json):
{{
  "name_vi": "{name_vi}",
  "history_text_vi": "Nội dung thuyết minh tiếng Việt cực kỳ chi tiết ở đây...",
  "history_text_en": "Nội dung thuyết minh tiếng Anh cực kỳ chi tiết tương ứng ở đây..."
}}
"""
        
        # Call Groq (with Gemini fallback)
        success = False
        attempts = 3
        while not success and attempts > 0:
            try:
                if groq_client:
                    # Try primary model and then fallback models on Groq
                    groq_models = [groq_model, "llama-3.1-8b-instant"]
                    response_text = None
                    for model in groq_models:
                        try:
                            response = groq_client.chat.completions.create(
                                model=model,
                                messages=[
                                    {"role": "system", "content": "You are an expert historian specializing in Hue Citadel. You always respond in valid JSON format matching the schema requested."},
                                    {"role": "user", "content": prompt}
                                ],
                                response_format={"type": "json_object"}
                            )
                            response_text = response.choices[0].message.content.strip()
                            break # Success!
                        except Exception as model_err:
                            err_str = str(model_err).lower()
                            if "rate_limit_exceeded" in err_str or "limit" in err_str or "429" in err_str or "413" in err_str:
                                print(f"  Model {model} hit rate limit or exceeded size. Trying fallback model...")
                                continue
                            raise model_err
                    
                    if response_text is None:
                        raise ValueError("All Groq models failed or were rate limited.")
                elif client:
                    # Fallback to Gemini
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            temperature=0.2,
                            max_output_tokens=8192,
                            response_mime_type="application/json"
                        )
                    )
                    response_text = response.text.strip()
                else:
                    raise ValueError("Neither GROQ_API_KEY nor GEMINI_API_KEY is configured.")
                
                # Clean code blocks if returned
                if response_text.startswith("```"):
                    # remove ```json and ```
                    response_text = re.sub(r'^```(?:json)?\n', '', response_text)
                    response_text = re.sub(r'\n```$', '', response_text)
                
                data = json.loads(response_text)
                enriched_results.append({
                    "id": loc_id,
                    "name_vi": name_vi,
                    "history_text_vi": data["history_text_vi"],
                    "history_text_en": data["history_text_en"]
                })
                success = True
                print(f"Successfully enriched {name_vi}.")
            except Exception as e:
                attempts -= 1
                print(f"Error enriching {name_vi}: {e}. Attempts left: {attempts}")
                time.sleep(2)
        
        # Safe delay to avoid API rate limits
        time.sleep(2)
        
    # Write enriched output to json
    print(f"\nWriting results to {ENRICHED_JSON}...")
    with open(ENRICHED_JSON, "w", encoding="utf-8") as f:
        json.dump(enriched_results, f, ensure_ascii=False, indent=2)
    print("Done! Data enrichment complete.")

if __name__ == "__main__":
    main()
