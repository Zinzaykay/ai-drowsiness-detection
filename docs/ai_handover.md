

Tài liệu tổng hợp sản phẩm bàn giao thuộc hạng mục **Machine Learning, Feature Engineering & Training** 

---

## 1. Danh mục sản phẩm bàn giao

| Thành phần | Đường dẫn | Mô tả |
| :--- | :--- | :--- |
| Chuẩn hóa dữ liệu & chia theo người | `ai/dataset.py` | Đọc CSV, kiểm tra hợp lệ, chia `GroupShuffleSplit` theo `subject_id` tránh data leakage |
| Trích xuất đặc trưng cửa sổ trượt | `ai/features.py` | `build_window_features()` (9 đặc trưng thuần NumPy), `make_windows()`, `get_feature_names()` |
| Mô hình Baseline (ngưỡng quy tắc) | `ai/baseline.py` | Luật ngưỡng EAR/MAR/PERCLOS làm mốc so sánh cho mô hình học máy |
| Huấn luyện & Lưu mô hình | `ai/train.py`, `ai/model/drowsiness_rf.joblib` | Random Forest kèm metadata danh sách đặc trưng |
| Đánh giá & Kiểm chứng chéo | `ai/evaluate.py`, `ai/cross_validate.py`, `ai/tune_threshold.py` | Đánh giá Precision/Recall/F1, `GroupKFold`, tinh chỉnh ngưỡng phân loại |
| Phân tích theo loại sự kiện | `ai/analyze_events.py` | Đánh giá OOF riêng cho `eye_closed`, `head_nod`, `yawn` |
| Suy luận thời gian thực (Inference) | `ai/predict.py` | Hàm nạp model `.joblib` và dự đoán từ cửa sổ đặc trưng |
| Kiểm thử đơn vị (Unit Tests) | `test/test_window_features.py`, `test/test_baseline.py`, `test/test_model.py`, `test/test_event_analysis.py` | Kiểm thử tự động toàn bộ pipeline ML bằng `pytest` |
| Báo cáo & Biểu đồ đánh giá | `docs/train-evaluate.md`, `docs/figures/*.png` | 4 biểu đồ (`confusion_matrix`, `pr_curve`, `feature_importance`, `event_analysis`) |

---

## 2. Quy ước dữ liệu & Vector đặc trưng (9 chiều)

> [!IMPORTANT]
> Cả lúc huấn luyện (`ai/train.py`) và chạy ứng dụng thực tế (`app/`), vector đầu vào **bắt buộc** giữ đúng thứ tự 9 đặc trưng dưới đây và cùng cấu hình cửa sổ trượt.

* **Cấu hình cửa sổ trượt mặc định:** `window_size = 30` khung hình, `stride = 10`, ngưỡng mắt nhắm `ear_threshold = 0.20`.
* **Quy ước nhãn (`y`):**
  * `0`: Tỉnh táo (`awake` / `normal`).
  * `1`: Buồn ngủ (`drowsy` — khi $\ge 50\%$ số khung trong cửa sổ mang nhãn `1`).
* **Thứ tự 9 đặc trưng trả về bởi `build_window_features(window)`** (với `window` có kích thước `(window_size, 2)` chứa 2 cột `[ear, mar]`):
  1. `ear_mean` — Trung bình EAR trong cửa sổ
  2. `mar_mean` — Trung bình MAR trong cửa sổ
  3. `ear_std` — Độ lệch chuẩn EAR
  4. `mar_std` — Độ lệch chuẩn MAR
  5. `ear_min` — Giá trị nhỏ nhất EAR
  6. `mar_min` — Giá trị nhỏ nhất MAR
  7. `ear_max` — Giá trị lớn nhất EAR
  8. `mar_max` — Giá trị lớn nhất MAR
  9. `perclos` — Tỷ lệ khung hình trong cửa sổ có $\text{EAR} < \text{ear\_threshold}$

---

## 3. Hướng dẫn tích hợp cho Thành viên D (`app/` & `alert/`)

Để ghép mô hình vào `app/workers/camera_worker.py` và `app/controller.py`:

1. **Tạo bộ đệm trượt (Rolling Buffer):** Dùng `collections.deque(maxlen=30)` lưu cặp `(ear, mar)` nhận từ `detection/feature_extractor.py` qua từng khung hình.
2. **Khi bộ đệm đủ 30 khung hình:** Chuyển thành mảng NumPy có kích thước `(30, 2)` và gọi hàm dự đoán từ `ai/predict.py` (nạp file `ai/model/drowsiness_rf.joblib`).
3. **Xử lý đầu ra cho cảnh báo:**
   ```python
   # Ví dụ logic ghép vào CameraWorker / Controller
   if len(ear_mar_buffer) == 30:
       # Dự đoán từ model Random Forest (0 = Tỉnh táo, 1 = Buồn ngủ)
       is_drowsy = (pred_label == 1)  # hoặc (pred_proba >= OPTIMAL_THRESHOLD)
       if is_drowsy:
           alert_manager.trigger()