# Hướng dẫn Setup và Chạy Hệ thống (OpenStreetMap & Real Coordinates)

Hệ thống sử dụng dữ liệu thực tế tại Kinh thành Huế (Đại Nội) và dịch vụ bản đồ & tìm đường đi bộ của **OpenStreetMap (Leaflet) & OSRM**. Hệ thống bản đồ và chỉ đường này **hoàn toàn miễn phí, không yêu cầu API Key hay kích hoạt thẻ tín dụng**.

## 1. Hướng dẫn lấy API Keys

Để ứng dụng hoạt động đầy đủ tính năng AI (Chatbot, Nhận diện ảnh, Giọng nói), bạn chỉ cần chuẩn bị 2 loại API Keys sau:

### 1.1. Google Gemini API Key (Dùng cho Chatbot & Vision)
- **Bước 1:** Truy cập vào [Google AI Studio](https://aistudio.google.com/).
- **Bước 2:** Đăng nhập bằng tài khoản Google.
- **Bước 3:** Nhấn vào nút **"Get API key"** ở cột bên trái.
- **Bước 4:** Nhấn **"Create API key in new project"**.
- **Bước 5:** Copy mã key và dán vào biến `GEMINI_API_KEY` trong file `.env`.

### 1.2. Groq API Key (Dùng cho Speech-to-Text - Whisper)
- **Bước 1:** Truy cập vào [Groq Console](https://console.groq.com/).
- **Bước 2:** Đăng nhập (có thể dùng tài khoản Google).
- **Bước 3:** Vào mục **"API Keys"** ở menu bên trái.
- **Bước 4:** Nhấn **"Create API Key"**, đặt tên bất kỳ (ví dụ: "AITourGuide").
- **Bước 5:** Copy mã key và dán vào biến `GROQ_API_KEY` trong file `.env`.

> [!NOTE]
> **Không cần Google Maps API Key:**
> Hệ thống bản đồ hoạt động trực tiếp qua nền tảng OpenStreetMap và công cụ định tuyến OSRM mà không cần bất kỳ khóa truy cập hay đăng ký dịch vụ trả phí nào.

---

## 2. Cài đặt Thư viện & Dữ liệu

### Backend:
```bash
cd backend
# Cài đặt các thư viện
pip install -r requirements.txt
```

### Frontend:
```bash
cd frontend
# Cài đặt các thư viện frontend cần thiết (đã tích hợp Leaflet)
npm install
```

### Khởi tạo lại Dữ liệu:
```bash
# Đảm bảo Docker Postgres đang chạy
alembic upgrade head

# Nạp dữ liệu thuyết minh phong phú & Đồ thị tri thức (Knowledge Graph)
python scripts/seed_enriched_data.py
```

> [!TIP]
> **Dữ liệu Đồ thị RAG và Cache Thuyết minh Sẵn có:**
> Cả dữ liệu Đồ thị tri thức (`backend/data/knowledge_graph_data.json`) và cache thuyết minh di tích (`backend/data/pre_generated_intros.json`) đều đã được tạo sẵn và commit lên Git. Người khác pull về chỉ cần chạy lệnh seed bên trên là cơ sở dữ liệu sẽ được điền đầy đủ thông tin lập tức. Không cần gọi LLM hay chạy lại script `build_graph.py` hoặc `pregenerate_intros.py` trừ khi thay đổi dữ liệu gốc trong `data.txt`.

---

## 3. Khởi chạy Ứng dụng

### Terminal 1 - Backend:
```bash
cd backend
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

### Terminal 2 - Frontend:
```bash
cd frontend
npm run dev
```

---

## 4. Cách sử dụng Tính năng Chỉ đường

1. **Truy cập:** `http://localhost:5173`.
2. **Chọn Địa điểm:** Nhấn vào card **"Kinh thành Huế"** trên trang chủ.
3. **Xác định vị trí bắt đầu:**
   * Modal sẽ hiện ra – chọn GPS tự động hoặc chọn trên bản đồ.
   * Có thể thay đổi vị trí bất kỳ lúc nào bằng nút GPS (🔵) hoặc Manual Pin (📍) ở góc phải.
4. **Dẫn đường:** Nhấn vào marker trên bản đồ → chọn **"Chỉ đường đến đây"**. Hệ thống sẽ vẽ đường đi bộ thực tế (uốn lượn quanh các lối đi bộ thật sự của Đại Nội qua dịch vụ OSRM miễn phí) và hiển thị chỉ dẫn chi tiết từng bước.
5. **Thuyết minh:** Nhấn **"ĐÃ ĐẾN NƠI"** để AI tự động thuyết minh/giới thiệu công trình.
6. **Căn chỉnh bản đồ:** Truy cập `http://localhost:5173/?view=calibrate` (hoặc bấm biểu tượng cờ lê 🔧) để di chuyển kéo thả các điểm di tích và lưu lại tọa độ cố định vào database.
