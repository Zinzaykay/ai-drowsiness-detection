# BÁO CÁO NHIỆM VỤ (TASK REPORT): TỐI ƯU HÓA HIỂN THỊ CAMERA (RESPONSIVE & ASPECT RATIO) VÀ TÍCH HỢP ĐO/HIỂN THỊ FPS THỜI GIAN THỰC

---

## 1. Thông Tin Task

- **Người thực hiện**: Hoàng Tuấn Dũng
- **Branch**: `feature/camera-gui`
- **Pull Request**: [Link PR]
- **Dự án**: AI Driver Drowsiness Detection System (Hệ thống giám sát và cảnh báo buồn ngủ tài xế)

---

## 2. Mục Tiêu Task

1. **Khắc phục lỗi hiển thị & Responsive trên mọi độ phân giải (Cross-display Compatibility)**:
   - Giải quyết triệt để xung đột kích thước cửa sổ cố định khi chạy trên màn hình laptop có bật Windows Display Scaling (125%, 150%, 175%), ngăn chặn hoàn toàn hiện tượng khung camera phình to đè bẹp/che mất khung thông số chỉ số EAR, MAR và trạng thái bên phải.
   - Thiết lập kích thước giới hạn an toàn (`minsize`) cho các cột bố cục để giao diện luôn co dãn mượt mà trên cả màn hình laptop nhỏ lẫn màn hình rời độ phân giải cao.

2. **Chuẩn hóa tỉ lệ hiển thị Camera (Aspect Ratio Preservation)**:
   - Loại bỏ lỗi méo hình ảnh (stretch ngang làm mặt người bị biến dạng) khi bật camera hoặc khi phóng to/toàn màn hình (fullscreen).
   - Tự động căn chỉnh và co dãn khung hình giữ nguyên tỉ lệ gốc của camera (4:3) bằng kỹ thuật Letterbox/Pillarbox bên trong vùng chứa video.

3. **Tối ưu hóa hiệu năng render hình ảnh (UI Performance Optimization)**:
   - Giảm tải tối đa cho Main Thread (UI Thread) của CustomTkinter bằng cách thay thế thuật toán resize ảnh của thư viện PIL bằng hàm tối ưu C++ của OpenCV (`cv2.resize`), khắc phục hiện tượng tụt FPS/micro-stuttering khi ứng dụng chạy trên GPU tích hợp (iGPU) của laptop.

4. **Sửa lỗi logic tính FPS và tích hợp hiển thị FPS thời gian thực lên GUI**:
   - Sửa dứt điểm lỗi biến cục bộ (immutable parameter) trong module `detection/camera.py` khiến FPS không được cập nhật.
   - Xây dựng luồng truyền dữ liệu từ `Camera` $\rightarrow$ `CameraWorker` (Background Thread) $\rightarrow$ `AppController` $\rightarrow$ `DrowsinessGUI` $\rightarrow$ `CameraView`, hiển thị FPS thực tế của pipeline AI lên thanh thông số dưới camera.

---

## 3. Các File Đã Tạo Hoặc Sửa

| STT | Đường dẫn file | Trạng thái | Nội dung chỉnh sửa chính |
| :-: | :--- | :---: | :--- |
| 1 | `app/app_config.py` | Chỉnh sửa | Đổi độ phân giải khởi tạo từ `1920x760` về chuẩn phổ thông `1280x720`, `min_width=1024`, `min_height=600` tương thích với mọi mức scale Windows. |
| 2 | `app/gui.py` | Chỉnh sửa | Bổ sung `minsize=500` cho Cột 0 (Camera) và `minsize=380` cho Cột 1 (Thông tin); thêm phương thức chuyển tiếp `update_fps(fps)` từ Controller xuống View. |
| 3 | `app/components/camera_view.py` | Chỉnh sửa | Thêm `grid_propagate(False)` chặn phình container; áp dụng thuật toán giữ Aspect Ratio và tăng tốc render bằng `cv2.resize`; bổ sung method `set_fps(fps)` và tự động reset `FPS: --` khi tắt cam. |
| 4 | `detection/camera.py` | Chỉnh sửa | Tái cấu trúc hàm `calculate_fps()`: cập nhật trực tiếp vào thuộc tính của instance (`self.frame_count`, `self.start_time`, `self.fps`), hỗ trợ tính ngầm không bắt buộc vẽ text đè lên frame. |
| 5 | `app/workers/camera_worker.py` | Chỉnh sửa | Gọi cập nhật FPS thực tế từ `self._camera.calculate_fps()` và đóng gói trường `"fps"` vào dictionary kết quả đẩy qua Queue. |
| 6 | `app/controller.py` | Chỉnh sửa | Tiếp nhận giá trị `fps` từ Queue trong hàm `process_frame()` và gửi lệnh cập nhật lên GUI qua `self.gui.update_fps()`. |

---

## 4. Chức Năng Đã Hoàn Thiện

1. **Hiển thị Camera chuẩn tỉ lệ (Aspect Ratio Fitting)**:
   - Khung hình camera giữ chuẩn tỉ lệ 4:3 (640x480) trong mọi kích thước cửa sổ, không bị kéo dãn bẹp lùn khi fullscreen. Vùng trống thừa được phủ nền tối tự nhiên.
2. **Giao diện Responsive chống tràn/đè khung**:
   - Khung camera không còn tự do mở rộng lấn át cột thông tin bên phải.
   - Khung chỉ số EAR, MAR, thẻ trạng thái cảnh báo và bảng lịch sử luôn hiển thị rõ ràng, đầy đủ kể cả trên màn hình laptop 14-16 inch có Windows Scale 125% - 150%.
3. **Đo và hiển thị FPS thời gian thực (Real-time Pipeline FPS Counter)**:
   - Góc dưới bên phải của camera hiển thị thông số: `Res: 640x480 | FPS: XX.X`.
   - Giá trị FPS được tính toán dựa trên tốc độ xử lý thực tế của cả pipeline (đọc camera + MediaPipe Face Landmarker).
   - Khi tắt camera, nhãn tự động đưa về trạng thái chờ `FPS: --`.

---

## 5. Nguyên Lý Hoạt Động

### 5.1. Luồng truyền dữ liệu FPS (Thread-Safe Pipeline)
```mermaid
flowchart TD
    A["Camera.read_frame()"] --> B["MediaPipe Face Landmarker"]
    B --> C["Camera.calculate_fps()<br>(Cập nhật chu kỳ 1s)"]
    C --> D["Đóng gói dict kết quả:<br>{frame, ear, fps, ...}"]
    D -->|queue.Queue| E["AppController._poll_camera_queue()<br>(Main Thread polling sau mỗi 30ms)"]
    E --> F["gui.update_camera_frame(frame)"]
    E --> G["gui.update_fps(fps)"]
    G --> H["camera_view.set_fps(fps)<br>Cập nhật nhãn GUI"]
```

1. **Tại `detection/camera.py`**:
   - Mỗi frame đi qua, biến đếm `self.frame_count` tăng thêm 1.
   - Khi thời gian trôi qua $\Delta t = \text{time.time()} - \text{self.start\_time} \ge 1.0\text{ giây}$:
     $$\text{self.fps} = \frac{\text{self.frame\_count}}{\Delta t}$$
   - Reset `self.frame_count = 0` và gán lại `self.start_time` cho chu kỳ tiếp theo.
2. **Tại `CameraWorker` & `AppController`**:
   - Background Thread tính toán xong đẩy dictionary có chứa `"fps"` vào Queue an toàn (`queue.Queue(maxsize=2)`).
   - Controller chạy trên Main Thread lấy kết quả từ Queue và gọi chuyển tiếp sang GUI mà không gây race condition.

### 5.2. Thuật toán giữ Aspect Ratio & Tối ưu Render
1. **Khóa lan truyền kích thước (Size Propagation Lock)**:
   - Sử dụng `video_container.grid_propagate(False)` để khóa cứng kích thước container do Grid cha phân bổ, cấm widget con `video_label` đòi nới rộng container.
2. **Thuật toán co dãn bảo toàn tỉ lệ**:
   - Lấy kích thước khả dụng của container: $W_{box}, H_{box}$.
   - Lấy kích thước gốc của frame: $W_{orig}, H_{orig}$ ($640 \times 480$).
   - Tính hệ số tỉ lệ:
     $$\text{scale} = \min\left(\frac{W_{box}}{W_{orig}}, \frac{H_{box}}{H_{orig}}\right)$$
     $$W_{new} = \text{int}(W_{orig} \times \text{scale}), \quad H_{new} = \text{int}(H_{orig} \times \text{scale})$$
3. **Tăng tốc xử lý ảnh**:
   - Thay vì dùng `PIL.Image.resize(..., Resampling.BILINEAR)` chạy bằng CPU Python đơn nhân, code sử dụng `cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)` trực tiếp trên mảng NumPy của OpenCV. Hàm này được biên dịch bằng C++ và tối ưu SIMD/AVX, cho tốc độ nhanh gấp 4 - 6 lần.

---

## 6. Cách Sử Dụng

1. **Khởi chạy ứng dụng**:
   ```bash
   python main.py
   ```
2. **Kiểm tra giao diện & Responsive**:
   - Thử kéo dãn cửa sổ hoặc phóng to toàn màn hình (Fullscreen): Quan sát khung hình camera luôn giữ đúng tỉ lệ khuôn mặt chuẩn, không bị dãn bè ngang, hai cột camera và bảng chỉ số bên phải giữ nguyên bố cục cân đối.
3. **Bật/Tắt Camera để theo dõi FPS**:
   - Nhấn nút **`▶ BẬT CAMERA`**: Quan sát góc dưới bên phải khung hình sẽ bắt đầu hiển thị FPS thực tế (thông thường dao động ổn định ở mức ~28 - 30 FPS).
   - Nhấn nút **`⏹ TẮT CAMERA`**: Nhãn FPS tự động quay về trạng thái chờ `FPS: --` và khung hiển thị placeholder mặc định.
4. **Chạy kịch bản kiểm thử tích hợp (Test suite)**:
   ```bash
   python test_integration.py
   ```
   Kết quả trả về đạt chuẩn toàn bộ 9/9 test case.

---

## 7. Kiến Thức Áp Dụng

1. **Kỹ thuật Đồ họa & Xử lý Ảnh (Computer Vision)**:
   - Khái niệm **Aspect Ratio (Tỉ lệ khung hình)** và kỹ thuật **Letterbox/Pillarbox** trong hiển thị video.
   - Tối ưu hóa pipeline xử lý ảnh số giữa **OpenCV (NumPy BGR array)** và **Pillow/CustomTkinter (PIL RGB Image, CTkImage)**.

2. **Lập trình GUI Nâng Cao với Tkinter / CustomTkinter**:
   - Cơ chế quản lý hình học **Tkinter Geometry Management** (`grid_propagate`, `weight`, `minsize`).
   - Xử lý vấn đề tương thích màn hình độ phân giải cao và đa tỉ lệ thu phóng **DPI Awareness & Windows Display Scaling**.

3. **Lập trình Đa Luồng & Đồng Bộ Hóa (Multithreading & Concurrency)**:
   - Giao tiếp luồng an toàn (Thread-Safe Communication) thông qua **`queue.Queue`** giữa Producer (Background Worker) và Consumer (GUI Main Thread).
   - Cơ chế Polling phi chặn (Non-blocking Polling) bằng callback **`after()`** của Tkinter.

4. **Kiến Trúc Phần Mềm (Software Architecture)**:
   - Áp dụng mô hình **MVC (Model - View - Controller)**: View chỉ lo hiển thị, Worker lo tính toán/đọc thiết bị, Controller đóng vai trò trung gian điều phối và chuyển tiếp dữ liệu.
   - Sửa lỗi tham trị / tham chiếu đối tượng bất biến (Mutable vs Immutable objects) trong ngôn ngữ lập trình Python.
