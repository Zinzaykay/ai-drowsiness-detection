# BÁO CÁO NHIỆM VỤ (TASK REPORT): SETUP GIAO DIỆN (GUI)

---

## 1. Thông Tin Task

- **Tên Task**: Thiết kế và refactor giao diện người dùng (Setup GUI Architecture)
- **Người thực hiện**: Hoàng Tuấn Dũng
- **Người review**: Nguyễn Mạnh Dũng
- **Nhánh (Branch)**: `feature/setup-gui*`
- **Dự án**: AI Drowsiness Detection System (Hệ thống cảnh báo buồn ngủ tài xế)

---

## 2. Mục Tiêu Task

- Xây dựng giao diện ứng dụng theo phong cách **Modern Dark Dashboard** hiện đại, trực quan, chuyên nghiệp bằng thư viện **CustomTkinter**.
- Refactor mã nguồn theo kiến trúc **Component-based** (chia nhỏ giao diện thành các thành phần độc lập) kết hợp mô hình **MVC (Model - View - Controller)**.
- Tách biệt rõ ràng tầng hiển thị (GUI) và tầng điều phối xử lý (Controller), đảm bảo GUI không tự tiện gọi các tác vụ nặng hay thuật toán AI.
- Chuẩn bị sẵn khung nhìn camera, khung trạng thái tài xế, khung chỉ số đo thị giác và lịch sử cảnh báo cùng các API / hooks để sẵn sàng ghép nối với các module xử lý thật (`detection/`, `ai/`, `alert/`) ở các giai đoạn tiếp theo.

---

## 3. Các File Đã Tạo Hoặc Chỉnh Sửa

| STT | Đường dẫn file                    |     Trạng thái     | Trách nhiệm chính                                                                                                                                                                                                                        |
| :-: | :-------------------------------- | :----------------: | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
|  1  | `main.py`                         |     Chỉnh sửa      | Điểm khởi chạy (Entry point) của ứng dụng; khởi tạo GUI và Controller, kết nối 2 bên và chạy `mainloop()`.                                                                                                                               |
|  2  | `app/app_config.py`               |      Tạo mới       | Cấu hình tập trung (Single Source of Truth): Camera (index, resolution, fps), ngưỡng AI (`EAR_THRESHOLD`, `MAR_THRESHOLD`), đường dẫn model/sound, và bảng màu/nội dung trạng thái (`STATUS_CONFIG`).                                    |
|  3  | `app/gui.py`                      | Tạo mới / Refactor | Cửa sổ ứng dụng chính: Tạo Header (logo, đồng hồ thực, Dark Mode switch), Footer, thiết lập bố cục Grid 2 cột, nhúng các components, bắt sự kiện `WM_DELETE_WINDOW` ủy thác cho Controller.                                              |
|  4  | `app/controller.py`               | Tạo mới / Refactor | Bộ điều phối trung tâm (MVC Controller): Quản lý trạng thái camera mock, quyết định màu chỉ số EAR/MAR theo ngưỡng, chống spam log (cooldown + đổi trạng thái), điều phối Demo Test Mode, và xử lý đóng ứng dụng an toàn (`on_closing`). |
|  5  | `app/components/__init__.py`      |      Tạo mới       | Package xuất bản các UI components dùng chung.                                                                                                                                                                                           |
|  6  | `app/components/camera_view.py`   |      Tạo mới       | Component khung hình camera: Viewport video, đồ họa placeholder khi camera tắt, nút Bật/Tắt camera, nhóm nút test nhanh trạng thái, và nhãn thông số Resolution/FPS.                                                                     |
|  7  | `app/components/status_panel.py`  |      Tạo mới       | Component trạng thái tài xế: Badge trạng thái lớn (`ALERT` / `WARNING` / `DROWSY`), dòng trạng thái tỉnh táo, dòng nhận xét / lời khuyên an toàn.                                                                                        |
|  8  | `app/components/metrics_panel.py` |      Tạo mới       | Component chỉ số thị giác: Hiển thị giá trị số và thanh tiến trình `CTkProgressBar` cho EAR (mắt) và MAR (miệng). Thuần hiển thị dữ liệu và màu sắc do Controller chỉ định.                                                              |
|  9  | `app/components/history_panel.py` |      Tạo mới       | Component lịch sử cảnh báo: Danh sách cuộn `CTkScrollableFrame`, thêm thẻ log thời gian thực và nút `🗑 Xóa` làm sạch toàn bộ log.                                                                                                       |

---

## 4. Chức Năng Đã Hoàn Thiện

1. **Giao diện Modern Dark Dashboard**:
   - Sử dụng tông màu tối sang trọng (`#0f172a`, `#1e293b`), các khối bo góc tròn mượt mà, phân bố tỉ lệ 2 cột khoa học (Cột trái: Camera & điều khiển; Cột phải: Trạng thái & Lịch sử).
   - Hỗ trợ công tắc chuyển đổi tức thì giữa chế độ Sáng (`Light`) và Tối (`Dark`).
   - Đồng hồ số điện tử góc phải header hiển thị thời gian thực chính xác từng giây.

2. **Điều khiển Camera (Mock Mode)**:
   - Nút **`▶ BẬT CAMERA`** (màu xanh ngọc `#10b981`) bấm chuyển sang **`⏹ TẮT CAMERA`** (màu đỏ `#ef4444`).
   - Cập nhật trực quan huy hiệu `● ĐANG TẮT` $\leftrightarrow$ `● ĐANG HOẠT ĐỘNG`.
   - Khi camera tắt: Hiển thị đồ họa placeholder bo góc với biểu tượng camera gạch chéo đỏ và hướng dẫn sử dụng.

3. **Hiển thị Trạng thái Tài xế Động (Driver Status)**:
   - Badge trạng thái kích thước lớn đổi màu theo 3 cấp độ chuẩn:
     - 🟢 **TỈNH TÁO (ALERT)**: Nền xanh lá, tài xế tập trung tốt.
     - ⚠️ **CẢNH BÁO (WARNING)**: Nền vàng cam, phát hiện chớp mắt chậm hoặc ngáp.
     - 🚨 **NGỦ GẬT (DROWSY)**: Nền đỏ báo động, nguy cơ tai nạn cao.
   - Cập nhật tự động 2 dòng text chi tiết: _Dòng trạng thái tỉnh táo_ và _Dòng nhận xét / lời khuyên an toàn_.

4. **Thanh đo chỉ số AI thời gian thực (Metrics)**:
   - Hiển thị giá trị số và thanh tiến trình trực quan cho:
     - **EAR (Eye Aspect Ratio)**: Chỉ số mở mắt (ngưỡng 0.25).
     - **MAR (Mouth Aspect Ratio)**: Chỉ số mở miệng / ngáp (ngưỡng 0.65).
   - Thanh tiến trình tự động đổi sang màu đỏ cảnh báo khi vượt ngưỡng cho phép (do Controller tính toán chỉ định).

5. **Chế độ Kiểm thử nhanh (Demo Test Mode)**:
   - Tích hợp sẵn 3 nút nhỏ: `🟢 Alert`, `⚠️ Warn`, `🚨 Drowsy`.
   - Cho phép người dùng hoặc giảng viên bấm thử để kiểm tra ngay hiệu ứng đổi màu giao diện, đổi nội dung nhận xét, cập nhật progress bar và tự động sinh bản ghi nhật ký mà không cần bật webcam hay chạy model AI.

6. **Lịch sử Cảnh báo (Alert History Logs)**:
   - Khung cuộn hiển thị từng thẻ cảnh báo gồm: Thời gian thực `[hh:mm:ss]`, Huy hiệu cấp độ, và Nội dung chi tiết sự kiện.
   - **Nút `🗑 Xóa` lịch sử**: Làm sạch 100% các dòng log trong danh sách, cập nhật thông báo xác nhận ở Footer mà không tự tiện chèn thêm log giả vào bảng.
   - **Cơ chế chống spam log (Anti-Spam & Cooldown)**: Chỉ ghi log khi có sự thay đổi trạng thái (State Transition) hoặc khi cảnh báo nguy hiểm lặp lại sau khoảng giãn cách quy định (`alert_cooldown = 5.0s`), ngăn chặn tình trạng tràn bộ nhớ hay giật lag giao diện.

7. **Xử lý Vòng đời Ứng dụng An toàn (Application Lifecycle)**:
   - Bắt sự kiện người dùng bấm nút [X] đóng cửa sổ (`WM_DELETE_WINDOW`).
   - Gọi hàm `controller.on_closing()` để dừng camera và dọn dẹp tài nguyên trước khi hủy cửa sổ giao diện.

---

## 5. Nguyên Lý Hoạt Động (Kiến Trúc & Luồng Dữ Liệu)

Ứng dụng được tổ chức theo mô hình **MVC (Model - View - Controller)** kết hợp **Component-Based UI**:

```
                         ┌─────────────────────────────┐
                         │      app/app_config.py      │
                         │ (Ngưỡng, Camera, Bảng màu)  │
                         └──────────────┬──────────────┘
                                        │ Đọc cấu hình
                                        ▼
┌─────────────────────────┐      Sự kiện UI      ┌─────────────────────────┐
│     TẦNG VIEW (GUI)     ├─────────────────────►│  TẦNG ĐIỀU PHỐI (CTRL)  │
│                         │                      │                         │
│  - DrowsinessGUI        │◄─────────────────────┤  - AppController        │
│  - CameraView           │   Cập nhật hiển thị  │  - Quản lý trạng thái   │
│  - StatusPanel          │   (Thread-Safe API)  │  - So sánh ngưỡng AI    │
│  - MetricsPanel         │                      │  - Lọc spam log         │
│  - HistoryPanel         │                      │  - Dọn dẹp on_closing   │
└─────────────────────────┘                      └────────────┬────────────┘
                                                              │ (Giai đoạn sau)
                                                              ▼
                                                 ┌─────────────────────────┐
                                                 │   TẦNG XỬ LÝ (BACKEND)  │
                                                 │  - Camera Worker        │
                                                 │  - AI Face Detector     │
                                                 │  - Alert Manager Sound  │
                                                 └─────────────────────────┘
```

### Luồng tương tác chi tiết:

1. **Khởi tạo**: `main.py` tạo thể hiện của `DrowsinessGUI` và `AppController`. GUI lưu tham chiếu tới Controller và Controller lưu tham chiếu tới GUI.
2. **Thao tác Bật/Tắt Camera**:
   - Người dùng bấm nút trên `CameraView` -> kích hoạt callback `on_toggle_camera` -> chuyển tiếp tới `controller.toggle_camera()`.
   - Controller cập nhật cờ `is_camera_running`, thông báo xuống GUI để đổi màu/nội dung nút và ghi một log khởi tạo vào `HistoryPanel`.
3. **Thao tác Demo Test / Nhận kết quả AI**:
   - Khi có dữ liệu mới (từ nút test hoặc sau này từ AI worker) -> gọi `controller.update_driver_status(status_level, ear, mar, ...)`.
   - Controller đối chiếu `ear` và `mar` với các ngưỡng trong `app_config.py` để xác định mã màu cảnh báo.
   - Controller gọi `gui.update_status()` và `gui.update_metrics()` để cập nhật thẻ trạng thái và thanh tiến trình.
   - Controller kiểm tra: Nếu trạng thái thay đổi HOẶC đã hết thời gian cooldown 5s thì mới gọi `gui.add_alert_log()` để thêm thẻ vào `HistoryPanel`.
4. **Xóa Lịch sử**:
   - Người dùng bấm nút `🗑 Xóa` -> gọi `controller.clear_history()` -> gọi `gui.clear_alert_history()` (hủy tất cả widget con) -> đặt thông báo tại Footer _"● Lịch sử cảnh báo đã được làm sạch."_.
5. **Đóng Ứng dụng**:
   - Người dùng bấm nút [X] -> kích hoạt sự kiện `WM_DELETE_WINDOW` -> gọi `controller.on_closing()` -> Controller kiểm tra và dừng camera mock -> gọi `gui.destroy()` an toàn.

---

## 6. Hướng Dẫn Sử Dụng

### 6.1. Cài đặt môi trường

Đảm bảo đã cài đặt Python 3.10+ cùng các thư viện cần thiết:

```bash
pip install customtkinter pillow opencv-python
```

### 6.2. Khởi chạy ứng dụng

Chạy lệnh trực tiếp tại thư mục gốc của dự án:

```bash
python main.py
```

### 6.3. Các thao tác kiểm thử giao diện

1. **Kiểm tra Camera Mock**:
   - Nhấn nút **`▶ BẬT CAMERA`** $\rightarrow$ Nút chuyển sang màu đỏ **`⏹ TẮT CAMERA`**, badge chuyển sang `● ĐANG HOẠT ĐỘNG` và xuất hiện 1 dòng log trong khung lịch sử.
   - Nhấn lại để tắt camera và đưa giao diện về trạng thái chờ.
2. **Kiểm tra Demo Test trạng thái AI**:
   - Nhấn **`🟢 Alert`**: Badge đổi sang màu xanh lá, trạng thái _"Bình thường - Đang tập trung"_, EAR = 0.33, MAR = 0.18 (cả 2 thanh tiến trình màu xanh).
   - Nhấn **`⚠️ Warn`**: Badge đổi sang màu vàng cam, trạng thái _"Có dấu hiệu mệt mỏi / Mất tập trung"_, EAR = 0.22 (thanh đỏ), MAR = 0.68 (thanh đỏ), sinh 1 dòng log cảnh báo.
   - Nhấn **`🚨 Drowsy`**: Badge đổi sang màu đỏ, trạng thái _"CỰC KỲ NGUY HIỂM - ĐANG NGỦ GẬT!"_, sinh 1 dòng log nguy hiểm.
3. **Kiểm tra Xóa lịch sử**:
   - Nhấn nút **`🗑 Xóa`** ở góc phải khung Lịch sử cảnh báo $\rightarrow$ Toàn bộ log biến mất, dòng chữ dưới footer hiển thị _"● Lịch sử cảnh báo đã được làm sạch."_.
4. **Kiểm tra Theme**:
   - Gạt nút switch **`Dark Mode`** ở góc phải thanh tiêu đề để trải nghiệm giao diện Light và Dark.

---

## 7. Kiến Thức Áp Dụng Trong Task

1. **Lập trình Hướng đối tượng (OOP) & Kế thừa trong Python**:
   - Xây dựng từng component giao diện thành các lớp kế thừa từ `customtkinter.CTkFrame`.
   - Cửa sổ ứng dụng chính kế thừa từ `customtkinter.CTk`.
   - Đóng gói dữ liệu (Encapsulation) và bảo vệ giao diện bằng các phương thức public API rõ ràng (`set_camera_state`, `update_frame`, `update_status`, `update_metrics`).
2. **Mô hình Kiến trúc Phần mềm MVC (Model - View - Controller)**:
   - Phân tách rạch ròi trách nhiệm giữa cấu hình dữ liệu (`app_config`), lớp hiển thị (`gui` và `components`) và lớp điều phối logic (`controller`).
   - Sử dụng **Callback Pattern** để View phát sự kiện cho Controller mà không cần biết logic bên trong Controller.
3. **Xử lý Đồ họa & UI với CustomTkinter và Pillow**:
   - Quản trị bố cục nâng cao với Tkinter Grid Manager (`grid`, `sticky`, `weight`) tạo giao diện co giãn responsive.
   - Sử dụng `PIL.ImageDraw` để vẽ đồ họa vector placeholder camera tắt sắc nét (khung bo góc, biểu tượng camera, đường gạch chéo báo tắt).
4. **Kỹ thuật Lọc Sự kiện & Chống Spam Log (Rate Limiting / Cooldown Pattern)**:
   - Sử dụng biến mốc thời gian `last_alert_time` và biến trạng thái `last_logged_status` kết hợp hàm `time.time()` để giới hạn tần suất ghi nhận log cảnh báo, giữ ứng dụng luôn mượt mà.
5. **Quản lý Vòng đời Cửa sổ Hệ điều hành (Window Lifecycle & Protocol Binding)**:
   - Sử dụng giao thức `protocol("WM_DELETE_WINDOW", ...)` để chặn và giải phóng tài nguyên phần cứng an toàn trước khi đóng tiến trình.
