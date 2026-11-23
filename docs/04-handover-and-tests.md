# 04. Tài Liệu Bàn Giao ML & Hướng Dẫn Kiểm Thử (Handover & Verification)

> [!IMPORTANT]
> Tài liệu tổng hợp toàn bộ sản phẩm bàn giao của **Thành viên C (Machine Learning, Feature Engineering & Training)** dành cho **Thành viên D** (tích hợp ứng dụng desktop/cảnh báo) và **Thành viên A** (tổng hợp báo cáo & slide).

## 1. Danh mục sản phẩm bàn giao

| Hạng mục | Đường dẫn | Đối tượng nhận |
| :--- | :--- | :---: |
| Mô hình đã huấn luyện | `ai/model/drowsiness_rf.joblib` | Thành viên D |
| Giao diện suy luận & Đặc trưng | `ai/predict.py`, `ai/features.py` | Thành viên D |
| Ngưỡng phân loại đề xuất | Kết quả từ `python -m ai.tune_threshold` (cấu hình vào `app/app_config.py`) | Thành viên D |
| Bộ 4 biểu đồ báo cáo | `docs/figures/confusion_matrix.png`, `pr_curve.png`, `feature_importance.png`, `event_analysis.png` | Thành viên A |
| Tài liệu phân tích & số liệu | `docs/01-data-and-features.md`, `02-baseline-and-model.md`, `03-evaluation-and-events.md`, `docs/train-evaluate.md` | Thành viên A |
| Bộ kiểm thử tự động | `test/test_baseline.py`, `test_event_analysis.py`, `test_model.py`, `test_window_features.py` | Cả nhóm |

---

## 2. Hợp đồng tích hợp API cho Thành viên D (`app/` & `alert/`)

> [!WARNING]
> **Ràng buộc bắt buộc:** Phía `app/` **không được tự viết lại công thức tính đặc trưng**. Bắt buộc gọi trực tiếp hàm `build_window_features()` từ `ai/features.py` với cùng `window_size = 30` và đúng thứ tự 2 cột `[ear, mar]` để đảm bảo vector 9 chiều khớp tuyệt đối với mô hình đã train.

* **Đầu vào (Input):** Bộ đệm trượt `collections.deque(maxlen=30)` lưu 30 cặp `(ear, mar)` liên tiếp từ `detection/feature_extractor.py`.
* **Quy ước nhãn đầu ra (Output):**
  * `0`: Tỉnh táo (`awake` / `normal`).
  * `1`: Buồn ngủ (`drowsy`).
* **Mẫu logic ghép vào `app/workers/camera_worker.py` / `app/controller.py`:**

```python
from collections import deque
import numpy as np

# 1. Khởi tạo bộ đệm trượt kích thước bằng window_size khi train
ear_mar_buffer = deque(maxlen=30)

# 2. Trong vòng lặp đọc từng khung hình webcam
ear_mar_buffer.append((ear, mar))

if len(ear_mar_buffer) == 30:
    window_arr = np.asarray(ear_mar_buffer, dtype=float)  # shape (30, 2)
    # Gọi hàm dự đoán từ ai/predict.py (dùng model ai/model/drowsiness_rf.joblib)
    # is_drowsy = (pred_label == 1)  hoặc  (pred_proba >= OPTIMAL_THRESHOLD)
    if is_drowsy:
        alert_manager.trigger()
```

> [!TIP]
> Để hạn chế báo động giả ở mức ứng dụng, nên kết hợp thêm bộ lọc **xác nhận liên tiếp** (ví dụ: chỉ bật chuông khi có 2–3 cửa sổ liên tiếp dự đoán `1`) và cơ chế **cooldown/debounce** trong `alert/alert_manager.py`.

---

## 3. Lệnh chạy toàn bộ pipeline & tái lập kết quả 

Chạy từ thư mục gốc dự án (`ai-drowsiness-detection/`):

```powershell
# 1. Chạy toàn bộ bộ kiểm thử tự động (hiển thị tên từng hàm test)
python -m pytest -v

# 2. Huấn luyện lại mô hình và đánh giá tổng thể
python -m ai.train
python -m ai.evaluate

# 3. Kiểm chứng chéo theo người (GroupKFold) và tinh chỉnh ngưỡng
python -m ai.cross_validate
python -m ai.tune_threshold

# 4. Phân tích theo loại sự kiện (tái tạo bảng số liệu & docs/figures/event_analysis.png)
python -m ai.analyze_events
```

---

## 4. Tổng hợp trạng thái bộ kiểm thử (`python -m pytest`)

| File test | Số test case | Trạng thái | Ghi chú |
| :--- | :---: | :---: | :--- |
| `test/test_baseline.py` | 6 | `PASSED` | Kiểm thử luật ngưỡng EAR/MAR/PERCLOS |
| `test/test_event_analysis.py` | 4 *(5 sau khi thêm test `video_name`)* | `PASSED` | Kiểm thử ánh xạ annotation, cắt cửa sổ sự kiện & tính metric |
| `test/test_model.py` | 4 | `PASSED` | Kiểm thử train, lưu/nạp `.joblib` và predict Random Forest |
| `test/test_window_features.py` | 6 | `PASSED` | Kiểm thử 9 đặc trưng, chia theo người không trùng, lỗi CSV |
| **Tổng cộng** | **20** *(21 khi thêm test mới)* | **100% PASS** | Không phụ thuộc dữ liệu thật, không để lại file rác (`tmp_path`) |