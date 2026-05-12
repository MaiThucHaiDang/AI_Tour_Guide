# Hướng Dẫn Backend

Tài liệu này hướng dẫn cách thiết lập và chạy backend FastAPI cho dự án AI Tour Guide.

## 1. Môi Trường

Trước tiên, hãy kích hoạt môi trường ảo `venv` trong thư mục `part4/backend/`.

### Trên Windows

```powershell
venv\Scripts\activate
```

### Trên Mac/Linux

```bash
source venv/bin/activate
```

Sau khi kích hoạt thành công, tên môi trường ảo thường sẽ xuất hiện ở đầu dòng lệnh.

## 2. Khởi Chạy Server

Để chạy FastAPI server ở chế độ phát triển, sử dụng lệnh sau trong thư mục `part4/backend/`:

```bash
uvicorn main:app --reload --port 8001
```

Server sẽ chạy tại:

```text
http://localhost:8001
```

## 3. Test API Thủ Công bằng Swagger UI

FastAPI cung cấp giao diện Swagger UI để kiểm tra API trực tiếp trên trình duyệt.

### Các bước thực hiện

1. Mở trình duyệt web.
2. Truy cập đường dẫn sau:

   ```text
   http://localhost:8001/docs
   ```

3. Tìm endpoint `POST /api/voice/chat`.
4. Nhấn vào endpoint để mở chi tiết.
5. Chọn nút **Try it out**.
6. Tải lên một file âm thanh mẫu định dạng `.wav` hoặc `.m4a` ở trường `audio`.
7. Nhập giá trị `vi` hoặc `en` cho trường `lang`.
8. Nhấn **Execute** để gửi request.
9. Nếu thành công, hệ thống sẽ trả về dữ liệu âm thanh `audio/mpeg`.

### Lưu ý

- File âm thanh nên rõ tiếng và có dung lượng vừa phải để kiểm tra dễ hơn.
- Nếu endpoint trả lỗi, hãy kiểm tra lại biến môi trường API key và định dạng file đầu vào.

## 4. Chạy Unit Test

Để chạy toàn bộ unit test của backend, dùng lệnh sau trong thư mục `part4/backend/`:

```bash
pytest tests/ -v
```

Lệnh này sẽ chạy các test trong thư mục `tests/` với chế độ hiển thị chi tiết.

## 5. Ghi Chú Nhanh

- Hãy đảm bảo `venv` đã được kích hoạt trước khi chạy server hoặc test.
- Nếu dùng terminal mới, cần kích hoạt lại môi trường ảo.
- Đặt file `.env` trong `part4/backend/` hoặc ở root project (load fallback) để các provider STT, LLM và TTS hoạt động.
- Co the cau hinh thu tu LLM bang bien `LLM_PROVIDER_ORDER` (vi du: `groq,gemini` hoac `gemini,groq`). Mac dinh la `groq,gemini`.