# Báo cáo Phân tích và So sánh: AI Tour Guide (web_root vs web_new)

Báo cáo này cung cấp cái nhìn chi tiết về sự thay đổi, cải tiến và kiến trúc mới của phiên bản **web_new** so với phiên bản gốc **web_root**.

---

## 1. Tổng quan sự thay đổi (High-level Overview)

Sự thay đổi lớn nhất là sự chuyển đổi từ một hệ thống **phân mảnh (Monolithic but split)** sang một hệ thống **nhất quán và hiện đại (Unified & Professional)**.

| Đặc điểm | web_root (Cũ) | web_new (Mới) |
| :--- | :--- | :--- |
| **Kiến trúc Backend** | Chia làm 2 server riêng biệt (Port 8000 & 8001). | Hợp nhất (Unified) thành 1 server duy nhất (Port 8000). |
| **Cơ sở dữ liệu** | SQL Server (pyodbc - synchronous). | PostgreSQL (SQLAlchemy - asynchronous). |
| **Luồng xử lý** | Tách biệt hoàn toàn tính năng Vision và Voice. | Hợp nhất (Multimodal): Có thể gửi ảnh kèm câu hỏi giọng nói. |
| **Giao diện (UI)** | Dạng các màn hình rời rạc (Camera -> Result). | Dạng Chatbot hiện đại (Bong bóng chat, lịch sử hội thoại). |
| **Quản lý trạng thái** | Không có lịch sử (Stateless cho mỗi lần chụp). | Có Session Memory (Nhớ nội dung đã nói trước đó). |

---

## 2. Phân tích Chi tiết Cải tiến Backend

### 2.1. Hợp nhất và Chuẩn hóa (Unification)
- **Cấu trúc thư mục:** `web_new` tổ chức theo mô hình Layered Architecture: `api` (routers), `core` (config/db), `models` (ORM), `repositories` (DB logic), `services` (AI logic), `orchestrators` (Business logic).
- **Middleware:** Bổ sung `error_handler.py` giúp bắt mọi lỗi hệ thống và trả về JSON chuẩn, tránh việc app bị crash hoặc trả về lỗi HTML 500 thô sơ.
- **Rate Limiting:** Tích hợp `slowapi` để bảo vệ server khỏi việc spam request.

### 2.2. Database & Repository Pattern
- **Chuyển đổi DB:** Thay thế SQL Server bằng **PostgreSQL**. Sử dụng `asyncpg` và `SQLAlchemy 2.0` (Async) giúp tăng hiệu năng xử lý đồng thời (concurrency).
- **Repository Pattern:** Toàn bộ logic truy vấn DB được đưa vào `ArtifactRepository`.
- **Cải tiến tìm kiếm:** 
    - `web_root` dùng bản đồ cứng (`VISION_LABEL_MAP`).
    - `web_new` sử dụng thuật toán tìm kiếm thông minh: Loại bỏ dấu (Unaccented), tách từ (Tokenization), loại bỏ từ dừng (Stop words), và tìm kiếm mờ (Fuzzy/Substring match) giúp nhận diện hiện vật chính xác hơn dù AI trả về tên không khớp 100%.

### 2.3. Orchestration & RAG (Retrieval-Augmented Generation)
- **UnifiedOrchestrator:** Đây là "bộ não" mới. Nó điều phối:
    1. Nhận Audio -> Chuyển thành Text (STT).
    2. Nhận Image -> Nhận diện hiện vật (Vision).
    3. Truy vấn Database để lấy thông tin chi tiết về hiện vật đó.
    4. Tổng hợp tất cả vào một Prompt gửi cho LLM.
- **Intent Classification:** Hệ thống có khả năng phân loại ý định người dùng (Hỏi về hiện vật vs. Tán gẫu) để đưa ra câu trả lời phù hợp nhất.

---

## 3. Phân tích Chi tiết Cải tiến Frontend

### 3.1. Trải nghiệm người dùng (UX)
- **Chat-centric UI:** Thay vì phải chuyển qua lại giữa các màn hình, người dùng tương tác trong một cửa sổ chat duy nhất. Điều này giúp theo dõi dòng thông tin dễ dàng hơn.
- **Multimodal Input:** Người dùng có thể:
    - Chụp ảnh.
    - Nhấn giữ Micro để hỏi.
    - Nhập văn bản.
    - Gửi ảnh kèm lời nhắn (Ví dụ: Chụp ảnh và hỏi "Cái này xây năm bao nhiêu?").

### 3.2. Quản lý phiên (Session Management)
- Sử dụng `session_id` lưu ở `sessionStorage`. Khi gửi request, Backend sẽ dựa vào ID này để lấy lại lịch sử hội thoại (`ConversationMemory`), giúp AI hiểu được các câu hỏi nối tiếp (Ví dụ: "Ai xây nó?" sau khi đã biết hiện vật là gì).

---

## 4. Cách hoạt động và Luồng xử lý (Flow Analysis)

Dưới đây là luồng xử lý của một yêu cầu tiêu biểu trong `web_new`:

1. **Người dùng hành động:** Người dùng chụp một tấm ảnh điện Thái Hòa và nói vào micro "Đây là đâu?".
2. **Frontend xử lý:**
    - Nén ảnh về kích thước tối ưu.
    - Đóng gói ảnh (base64) + audio (blob) + session_id gửi lên `/api/v1/chat`.
3. **Backend Orchestrator tiếp nhận:**
    - **Bước A (STT):** Chuyển âm thanh thành văn bản: "Đây là đâu?".
    - **Bước B (Vision):** Gửi ảnh qua Gemini Vision. AI trả về JSON: `{"artifact_name": "Điện Thái Hòa", "confidence": 0.95}`.
    - **Bước C (Search):** Repository tìm trong DB từ khóa "Điện Thái Hòa", lấy ra đoạn lịch sử/thuyết minh đầy đủ.
    - **Bước D (Memory):** Lấy các câu hội thoại trước đó từ bộ nhớ RAM/Cache.
    - **Bước E (LLM):** Gửi toàn bộ (System Prompt + History + DB Context + User Query) cho Gemini LLM.
    - **Bước F (TTS):** Chuyển văn bản trả lời của AI thành file âm thanh.
4. **Kết quả:** Trả về cho Frontend gồm: Văn bản trả lời, File âm thanh, Tên hiện vật nhận diện được.
5. **Frontend hiển thị:** Hiển thị bong bóng chat, tự động phát âm thanh thuyết minh.

---

## 5. Kết luận

**web_new** không chỉ là một bản cập nhật giao diện, mà là một **sự tái cấu trúc toàn diện (Refactoring)**:
- **Tính chuyên nghiệp:** Code sạch, dễ bảo trì, áp dụng các design pattern chuẩn.
- **Tính thông minh:** Khả năng hiểu ngữ cảnh tốt hơn nhờ RAG và Memory.
- **Tính linh hoạt:** Dễ dàng mở rộng thêm các loại hiện vật mới mà không cần sửa code (chỉ cần cập nhật DB).
- **Hiệu năng:** Xử lý bất đồng bộ hoàn toàn, giúp hệ thống chịu tải tốt hơn.

Đây là một bước tiến lớn giúp ứng dụng thực sự trở thành một "Hướng dẫn viên ảo" chuyên nghiệp.
