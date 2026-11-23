# 02. Mô Hình Baseline, Huấn Luyện Random Forest & Suy Luận (Model & Inference)

> [!NOTE]
> **Mục tiêu của nhóm module:** Xây dựng mô hình cơ sở dựa trên luật ngưỡng (Baseline) làm mốc đối chứng, huấn luyện mô hình học máy **Random Forest** trên bảng đặc trưng 9 chiều và cung cấp giao diện suy luận thời gian thực (`ai/predict.py`) để ghép trực tiếp vào ứng dụng desktop.

## 1. Danh sách file thuộc nhóm

| Đường dẫn | Vai trò chính |
| :--- | :--- |
| `ai/baseline.py` | Mô hình cơ sở dựa trên luật ngưỡng cố định (EAR, MAR, PERCLOS) để so sánh với mô hình ML. |
| `ai/train.py` | Pipeline huấn luyện Random Forest từ đặc trưng cửa sổ trượt và đóng gói lưu model ra đĩa. |
| `ai/model/drowsiness_rf.joblib` | Artifact trọng số mô hình Random Forest đã huấn luyện sẵn kèm metadata danh sách đặc trưng. |
| `ai/predict.py` | Module nạp model `.joblib` và thực hiện dự đoán từ cửa sổ dữ liệu thời gian thực (bàn giao cho thành viên D). |
| `test/test_baseline.py` | Bộ 6 unit test kiểm chứng logic phân loại theo ngưỡng của mô hình Baseline. |
| `test/test_model.py` | Bộ 4 unit test kiểm chứng quy trình huấn luyện, lưu/nạp file `.joblib` và suy đoán của Random Forest. |

---

## 2. Luồng hoạt động của từng module

### 2.1. Mô hình cơ sở (`ai/baseline.py`)
* **Ý tưởng:** Áp dụng trực tiếp các quy tắc sinh học kinh điển (ngưỡng `EAR` thấp, `PERCLOS` cao khi mắt nhắm lâu, hoặc `MAR` vượt ngưỡng khi ngáp) để phân loại cửa sổ thành `0` (tỉnh táo) hoặc `1` (buồn ngủ).
* **Vai trò khoa học:** Tạo mốc chuẩn (benchmark) khách quan. Nếu Random Forest không vượt trội rõ rệt so với Baseline đơn giản thì việc dùng học máy là không cần thiết.

### 2.2. Huấn luyện & Đóng gói mô hình (`ai/train.py`)
Luồng huấn luyện chuẩn gồm 4 bước:
1. Đọc dữ liệu đặc trưng cấp khung hình (qua `ai/dataset.py`), tách tập Train/Test theo `subject_id` để chống rò rỉ dữ liệu.
2. Cắt cửa sổ trượt bằng `make_windows()` từ `ai/features.py` để thu ma trận đặc trưng `X` (9 cột) và nhãn `y`.
3. Huấn luyện `RandomForestClassifier` (kết hợp xử lý mất cân bằng lớp như `class_weight="balanced"` và cố định `random_state` để tái lập kết quả).
4. Lưu mô hình kèm danh sách tên đặc trưng (`get_feature_names()`) vào `ai/model/drowsiness_rf.joblib`.

> [!TIP]
> **Vì sao chọn Random Forest cho bài toán này?**
> * Hoạt động rất mạnh trên dữ liệu dạng bảng ít chiều (9 đặc trưng thống kê).
> * Học được quan hệ phi tuyến và tổ hợp điều kiện giữa các chỉ số (ví dụ: mắt hơi híp **kết hợp** miệng mở to khi ngáp) mà luật ngưỡng rời rạc khó tinh chỉnh thủ công.
> * Ít nhạy cảm với nhiễu ngoại lai, không cần chuẩn hóa thang đo (`StandardScaler`), cung cấp trực tiếp mức độ quan trọng đặc trưng (`feature_importances_`) và suy luận cực nhanh đáp ứng thời gian thực.

### 2.3. Suy luận thời gian thực (`ai/predict.py`)
`ai/predict.py` là cầu nối trực tiếp giữa phần ML (Thành viên C) và phần Ứng dụng/Cảnh báo (Thành viên D):
* Nạp duy nhất một lần file `ai/model/drowsiness_rf.joblib` khi khởi động ứng dụng để tránh độ trễ đọc ổ đĩa mỗi frame.
* Nhận bộ đệm trượt gồm `window_size` (mặc định `30`) cặp `(ear, mar)` từ `detection/feature_extractor.py`.
* Gọi đúng hàm `build_window_features()` trong `ai/features.py` để đảm bảo 9 đặc trưng đầu vào khớp tuyệt đối với lúc huấn luyện.
* Trả về kết quả dự đoán (`label` `0`/`1` và/hoặc xác suất buồn ngủ `proba`) để bộ điều khiển kích hoạt cảnh báo âm thanh khi vượt ngưỡng.

```python
# Minh họa luồng suy luận (Inference Flow)
# Camera -> MediaPipe (EAR, MAR) -> Buffer 30 frames -> build_window_features() -> RF Model -> Cảnh báo
import numpy as np
from ai.features import build_window_features

window_arr = np.asarray(ear_mar_buffer, dtype=float)   # shape: (30, 2)
feat_vec = build_window_features(window_arr).reshape(1, -1)  # shape: (1, 9)
```

---

## 3. Lệnh chạy & Kiểm thử

```powershell
# Huấn luyện mô hình và xuất ai/model/drowsiness_rf.joblib
python -m ai.train

# Chạy kiểm thử riêng cho Baseline (6 tests) và Random Forest (4 tests)
python -m pytest -v test/test_baseline.py test/test_model.py
```

| File kiểm thử | Số test | Phạm vi xác nhận |
| :--- | :---: | :--- |
| `test/test_baseline.py` | 6 | Hành vi luật ngưỡng trên các trạng thái tỉnh táo, nhắm mắt, ngáp và biên ngưỡng. |
| `test/test_model.py` | 4 | Huấn luyện Random Forest, lưu/nạp artifact `.joblib`, định dạng đầu ra dự đoán & xác suất. |