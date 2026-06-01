# Kế Hoạch Chuyển Đổi: AI Tour Guide -> Bản Đồ Tương Tác & Thuyết Minh Chuyên Sâu

## 1. Bối cảnh & Mục tiêu (Background & Motivation)
Ứng dụng hiện tại đang hoạt động dưới dạng một Chatbot thuần túy. Yêu cầu mới chuyển đổi ứng dụng thành một **Hướng dẫn viên du lịch tương tác dựa trên vị trí (Location-aware Interactive Guide)**. 

Hệ thống sẽ cung cấp:
- Danh sách các địa điểm (locations) có sẵn.
- **Bản đồ nội bộ tương tác (Vector/Tile Map hoặc Image Overlay).**
- Lấy vị trí ban đầu bằng GPS, nhưng cho phép **người dùng tự chọn vị trí hiện tại** trên bản đồ (Hybrid Location System) để xử lý trường hợp GPS sai số hoặc di chuyển không báo trước.
- Hệ thống tìm đường (Pathfinding/Routing) giữa vị trí hiện tại đã xác định và điểm đến được chọn.
- Luồng âm thanh chỉ đường tuần tự.
- Chế độ **Thuyết minh chuyên sâu (Deep-dive Storytelling)** khi đến nơi, hoạt động như một hướng dẫn viên thực thụ (đề xuất chủ đề, kể chuyện tương tác, trả lời câu hỏi).

## 2. Phạm vi & Tác động (Scope & Impact)

Sự thay đổi này tác động lớn đến cả Frontend và Backend:
- **Frontend:** Tích hợp bản đồ (Leaflet), thiết kế tính năng chọn/cập nhật vị trí bằng tay và GPS, và luồng UI mới (Màn hình chính -> Bản đồ -> Dẫn đường -> Thuyết minh).
- **Backend:** Thêm API tìm đường (Routing Engine), quản lý tọa độ nội bộ. Nâng cấp Agent để hỗ trợ chuyển đổi từ "State" dẫn đường sang "State" thuyết minh sâu.
- **Dữ liệu (Database):** Thêm tọa độ (lat/lng) cho các `Location` và `Artifact`, xây dựng đồ thị đường đi (Path Graph).

## 3. Kiến trúc Đề xuất (Proposed Solution)

### 3.1. Frontend (React + Vite)
- **Thư viện Bản đồ:** Sử dụng `React-Leaflet`.
- **Định vị (Hybrid Geolocation):**
  - Khởi tạo: Lấy vị trí bằng `navigator.geolocation.getCurrentPosition()`.
  - Nút "Cập nhật vị trí": Cung cấp 2 tùy chọn: (1) Tự động lấy lại GPS hiện tại, (2) Chạm vào bản đồ để "Ghim" vị trí thủ công.
- **UI States:**
  - `MapExplore`: Xem bản đồ, vị trí hiện tại (Blue dot/Pin có thể di chuyển), các điểm tham quan (Pins).
  - `Navigating`: Chế độ dẫn đường. Người dùng chọn điểm B, hệ thống lấy điểm A (vị trí hiện tại), vẽ đường đi và hiện nút "Bắt đầu đi".
  - `StoryTelling`: Khi người dùng nhấn nút "Tôi đã đến nơi" (hoặc chọn trực tiếp hiện vật), mở chế độ thuyết minh chuyên sâu.

### 3.2. Backend & Dữ liệu (FastAPI + PostgreSQL)
- **Geospatial Data:** Lưu tọa độ chuẩn hoặc tọa độ pixel/tương đối (nếu dùng Image Overlay) cho các địa điểm.
- **Routing Engine (Tìm đường):**
  - Xây dựng đồ thị (Graph) đường đi.
  - Áp dụng thuật toán Dijkstra/A* (có thể implement ở Backend trả về API, hoặc dùng thư viện Frontend nếu data nhỏ).
- **Voice Orchestrator (Nâng cấp):**
  - **Dẫn đường:** Text-to-Speech đọc hướng dẫn tĩnh (vd: "Hãy đi theo đường màu xanh, quẹo trái ở ngã tư...").
  - **Thuyết minh:** Agent tương tác. Khi Frontend báo đã đến nơi, Agent chủ động hỏi: *"Bạn đã đến nơi, bạn có muốn nghe tôi kể về lịch sử của nó không?"* và bắt đầu RAG chuyên sâu.

## 4. Các Bước Triển Khai (Phased Implementation Plan)

### Phase 1: Chuẩn bị Bản đồ & Routing (Data/Backend)
1. **Thiết lập Bản đồ:** Xác định tọa độ các điểm trên sơ đồ.
2. **Xây dựng Đồ thị Tìm đường:** Tạo danh sách Nodes/Edges các lối đi hợp lệ.
3. **API (Tùy chọn):** Nếu xử lý routing ở Backend, viết API `/api/v1/map/route` nhận (A, B) và trả về Path. (Nếu làm ở Frontend thì bỏ qua bước này).

### Phase 2: Tích hợp Bản đồ & Vị trí (Frontend)
1. Tích hợp `react-leaflet`. Hiển thị sơ đồ (dùng Image Overlay hoặc GeoJSON).
2. Xây dựng logic **Hybrid Location**:
   - Nút lấy GPS (getCurrentPosition).
   - Chế độ "Chọn vị trí trên bản đồ" (click để thả pin).
3. Hiển thị các điểm tham quan (Markers) có thể click.

### Phase 3: Luồng Dẫn đường (Routing & UI)
1. Khi click vào một điểm tham quan, gọi hàm tìm đường từ (Vị trí hiện tại) đến (Điểm tham quan).
2. Vẽ đường đi (Polyline).
3. Đọc Audio chỉ đường tổng quan bằng `EdgeTTSProvider`.

### Phase 4: Chế độ Thuyết minh Chuyên sâu (Storytelling Agent)
1. Thêm nút **"Tôi đã đến nơi / Nghe thuyết minh"** tại điểm tham quan.
2. Nâng cấp LLM System Prompt để đóng vai "Hướng dẫn viên thực thụ", chia nhỏ nội dung RAG thành các đoạn giao tiếp ngắn, gợi mở.
3. Hiển thị giao diện Thuyết minh (phát audio tự động, hiển thị ảnh chất lượng cao, chat tương tác).

## 5. Alternatives Considered (Các Lựa chọn Thay thế)
- **Map hiển thị:** Thay vì Vector Map (như GeoJSON) có thể tốn thời gian dựng, có thể sử dụng **Image Overlay trên Leaflet** (Map một ảnh tĩnh sơ đồ nội bộ chất lượng cao khớp 4 góc với tọa độ GPS thực tế). Rất tốt cho proof-of-concept.
- **Routing Engine:** Thay vì triển khai A* phức tạp trên Backend, có thể đóng gói file `graph.json` và dùng `turf.js` hoặc custom logic pathfinding ngay tại Frontend để giảm tải độ trễ (latency).

## 6. Xác nhận & Kiểm tra (Verification)
- **Test GPS Mapping:** Chạy Web trên điện thoại thực tế hoặc dùng công cụ giả lập GPS để kiểm tra hiển thị Blue dot.
- **Test Pathfinding:** Kiểm tra xem các tuyến đường vẽ ra có tránh được vật cản và có hướng dẫn audio chính xác không.
- **Test Workflow:** Mô phỏng đi bộ đến gần hiện vật xem trigger "Thuyết minh chuyên sâu" có nhảy đúng lúc không.