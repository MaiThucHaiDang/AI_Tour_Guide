# AI Tour Guide
Nhóm 2 - Tư duy tính toán - 24CTT6

## Tính năng 1: Quét ảnh -> Nhận diện -> Thuyết minh bằng giọng nói

### 🛠 Yêu cầu hệ thống (Prerequisites)

Để chạy được mã nguồn này trên máy tính của bạn, bắt buộc phải cài đặt môi trường **Node.js**.

**Hướng dẫn cài đặt Node.js (Nếu máy chưa có):**
1. Truy cập trang web chính thức: [https://nodejs.org/](https://nodejs.org/)
2. Bấm tải xuống phiên bản **LTS (Long Term Support)** dành cho Windows/Mac.
3. Mở file vừa tải về và cứ bấm `Next` liên tục cho đến khi cài đặt xong (Finish).
4. Để kiểm tra xem đã cài thành công chưa:
   - Mở **Terminal** (trên VS Code) hoặc **Command Prompt (cmd)**.
   - Gõ lệnh `node -v` và ấn Enter. Nếu hiện ra version (ví dụ: `v18.17.0`) là bạn đã cài thành công.

---

### 🚀 Hướng dẫn Cài đặt & Chạy dự án chi tiết

#### Bước 1: Mở Terminal tại thư mục dự án
1. Mở phần mềm **Visual Studio Code (VS Code)**.
2. Chọn `File` > `Open Folder...` và chọn thư mục chứa đồ án.
3. Bấm tổ hợp phím `` Ctrl + ` `` (hoặc trên menu chọn `Terminal` > `New Terminal`) để mở cửa sổ dòng lệnh.

#### Bước 2: Cài đặt thư viện (Dependencies)
Trong Terminal, hãy gõ lệnh sau và ấn Enter:
```bash
npm install
```
*Lưu ý: Bạn chỉ cần chạy lệnh này 1 lần duy nhất để tải các thư viện React, Lucide Icons,... về thư mục `node_modules`. Quá trình này có thể mất 1-2 phút tùy tốc độ mạng.*

#### Bước 3: Khởi động Server (Chạy cả Frontend và Backend)

Vì dự án đã được tích hợp hoàn chỉnh, bạn cần mở **2 cửa sổ Terminal** riêng biệt để chạy song song cả 2 phần.

**Terminal 1: Khởi động Frontend (Giao diện React)**
Đảm bảo bạn đang ở thư mục gốc của dự án, gõ lệnh:
```bash
npm run dev
```
Khi chạy thành công, Terminal sẽ hiện ra: `➜  Local:   http://localhost:5173/`

**Terminal 2: Khởi động Backend (AI API bằng Python)**
1. Bấm biểu tượng dấu `+` trên giao diện Terminal của VS Code để mở thêm một cửa sổ Terminal thứ 2.
2. Di chuyển vào thư mục chứa code Backend:
```bash
cd src/backend
```
3. Cài đặt các thư viện AI (Yêu cầu máy tính đã cài Python):
```bash
pip install -r requirements.txt
```
4. Khởi động server Backend:
```bash
uvicorn main:app --reload
```
Khi chạy thành công, Terminal sẽ thông báo API đang hoạt động tại cổng: `http://localhost:8000/`. Đừng tắt Terminal này trong quá trình test nhé.

#### Bước 4: Xem App trên trình duyệt
1. Giữ phím `Ctrl` và click chuột trái vào đường link `http://localhost:5173/` để mở web.
2. **QUAN TRỌNG:** Vì đây là Mobile App, bạn CẦN xem ở giao diện điện thoại:
   - Bấm phím **F12** (hoặc chuột phải chọn `Inspect` / `Kiểm tra`).
   - Tìm icon **Hình chiếc điện thoại / Máy tính bảng** (hoặc bấm `Ctrl + Shift + M`).
   - Chọn loại thiết bị (Ví dụ: iPhone 12 Pro) và F5 tải lại trang.

---

### 📱 Hướng dẫn Test App trực tiếp trên Điện thoại thật (Cùng mạng WiFi)

Nếu bạn muốn dùng chính điện thoại của mình để soi camera thay vì dùng Webcam máy tính:
1. Đảm bảo điện thoại và máy tính kết nối **cùng một mạng WiFi**.
2. Ở Terminal VS Code đang chạy `npm run dev`, hãy tắt đi bằng `Ctrl + C` (Chọn Y).
3. Chạy lại server với lệnh:
   ```bash
   npm run dev -- --host
   ```
4. Terminal sẽ hiện thêm đường link **Network**, ví dụ: `http://192.168.1.11:5173/`.
5. Lấy điện thoại mở trình duyệt và gõ đúng đường link Network đó vào. Cấp quyền Camera và trải nghiệm!

---

### 🕹️ Hướng dẫn Sử dụng & Tích hợp Backend

Sau khi khởi động ứng dụng thành công, bạn sẽ được đưa đến **Màn hình chính (Home Screen)** cực kỳ hiện đại:

1. **Chuyển đổi Ngôn ngữ (VI/EN)**: Bấm vào nút gạt trên góc phải màn hình. Tính năng này sẽ thay đổi ngôn ngữ của toàn bộ giao diện và truyền vào API để AI trả lời đúng tiếng Việt/tiếng Anh.
2. **Trải nghiệm Tính năng**:
   - **Nhận diện hiện vật (Camera Scanner)**: Bấm vào thẻ này để cấp quyền và mở Camera. Hướng camera vào hiện vật và bấm nút chụp. App sẽ nén ảnh và gửi sang Backend xử lý. *Lưu ý: Nếu trình duyệt chặn Camera (do thiếu HTTPS), hệ thống sẽ hiển thị nút **Tải ảnh lên** để bạn chọn ảnh trực tiếp từ máy thay thế.*
   - **Hỏi đáp với AI (AI Chat)**: Tính năng đang trong quá trình phát triển (Coming soon).
   - Trong lúc sử dụng Camera, bạn có thể bấm nút `<- Quay lại` ở góc trái để trở về Màn hình chính.

**⚠️ Lưu ý quan trọng khi chạy thực tế (Tích hợp BE):**
- Ứng dụng hiện **đã được kết nối trực tiếp với Backend thật** thay vì dùng dữ liệu giả lập.
- Khi bạn chụp ảnh, hệ thống sẽ tự động gọi API `POST` lên địa chỉ: `http://localhost:8000/api/v1/recognize`.
- **Yêu cầu:** Người 2 (Backend) phải chạy server Python FastAPI. Nếu bạn dùng điện thoại để test (khác localhost), hãy yêu cầu Người 2 cung cấp **IP LAN** (vd: `192.168.1.11:8000`) và cập nhật URL này trong file `src/services/apiService.js`.

---

### 📂 Giải thích Cấu trúc Source Code (Dùng cho viết Báo cáo)

Dưới đây là sơ đồ kiến trúc dành cho phần Frontend (Người 1):

* **`src/App.jsx`**: File Controller chính. Nơi quản lý State tổng (`home`, `camera`, `scanning`, `result`), trạng thái ngôn ngữ (`language`), và xử lý luồng luân chuyển các màn hình.
* **`src/components/`**: Các mảnh ghép giao diện:
  * `HomeScreen.jsx`: **[MỚI]** Giao diện Trang chủ (Home) dùng phong cách Glassmorphism, xử lý chọn tính năng và đổi ngôn ngữ.
  * `CameraScanner.jsx`: Dùng `navigator.mediaDevices.getUserMedia` để lấy quyền và stream Camera.
  * `ScanningLoader.jsx`: UI màn hình chờ API chạy (Che giấu độ trễ mạng).
  * `ResultView.jsx`: Hiển thị kết quả AI nhận diện & tích hợp trình phát giọng nói.
  * `ErrorPopup.jsx`: Giao diện xử lý ngoại lệ (Lỗi mạng, Ảnh mờ...).
* **`src/services/apiService.js`**: Đảm nhiệm việc kết nối HTTP (Fetch API) gọi trực tiếp qua AI Backend Gateway. Đồng thời chứa hàm gọi **Web Speech API** (Đọc văn bản thành tiếng).
* **`src/utils/imageUtils.js`**: Core Logic tiền xử lý. Tự động vẽ ảnh lên `<canvas>`, resize chiều rộng về 800px và nén nén JPEG `quality=0.7` giúp giảm ảnh từ 5MB xuống Base64 dưới 1MB.
* **`src/index.css`**: Nơi chứa toàn bộ linh hồn đồ họa (Vanilla CSS). Kết hợp kỹ thuật tạo Background Gradient, thẻ nổi 3D, Glassmorphism, và CSS Animations (`fade-in`, `pop-in`).