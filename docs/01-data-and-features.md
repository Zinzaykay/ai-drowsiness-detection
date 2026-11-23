# 01. Chuẩn Hóa Dữ Liệu & Trích Xuất Đặc Trưng (Data & Window Features)

> [!NOTE]
> **Mục tiêu của nhóm module:** Chuẩn hóa dữ liệu đầu vào $(X, y, \text{groups})$ cho bước huấn luyện, phòng chống rò rỉ dữ liệu theo cá nhân (data leakage), và dùng chung một hàm trích xuất đặc trưng giữa bước **huấn luyện (training)** và **ứng dụng webcam thời gian thực (inference)**.

## 1. Danh sách file thuộc nhóm

| Đường dẫn | Vai trò chính |
| :--- | :--- |
| `ai/__init__.py` | Đánh dấu `ai/` là Python package để chạy lệnh dạng `python -m ai.<module>` và import chéo. |
| `ai/dataset.py` | Sinh dữ liệu giả lập kiểm thử pipeline, đọc & kiểm tra tính hợp lệ của CSV, chia tập Train/Test theo `subject_id`. |
| `ai/features.py` | Trích xuất vector 9 đặc trưng trên từng cửa sổ trượt thuần NumPy và cắt cửa sổ không vắt ngang video. |
| `test/test_window_features.py` | Bộ 6 unit test kiểm tra kích thước vector, chia không trùng người, cắt cửa sổ, tính tái lập và bắt lỗi CSV. |

---

## 2. Chi tiết mã nguồn

### 2.1. `ai/dataset.py`

#### `generate_synthetic_data(...)`
```python
generate_synthetic_data(
    n_subjects=10,
    frames_per_video=300,
    seed=42,
    videos_per_subject=2,
)
```

* **Mô phỏng cá nhân hóa:** Mỗi `subject_id` có mức `EAR` và `MAR` nền riêng (lấy ngẫu nhiên quanh `0.30`), giúp việc kiểm thử chia theo người phản ánh đúng thực tế sinh học.
* **Quy luật sinh nhãn trong mỗi video:**
  * **Nửa đầu — Nhãn `0` (Tỉnh táo):** Chèn 3 cú chớp mắt ngắn (mỗi cú 3 khung có `EAR` giảm mạnh) để mô hình không học nhầm *"EAR thấp thoáng qua là buồn ngủ"*.
  * **Nửa sau — Nhãn `1` (Buồn ngủ):** `EAR` giảm `0.10` (mắt nhắm kéo dài) và xuất hiện 2 đoạn `MAR` tăng `0.40` (ngáp, tối đa 12 khung).
* **An toàn & tái lập:** Chặn giá trị không âm bằng `np.clip`, dùng duy nhất `np.random.default_rng(seed)` để cùng `seed` luôn sinh ra DataFrame giống hệt nhau, hoạt động an toàn cả khi `frames_per_video` nhỏ.

> [!WARNING]
> Dữ liệu giả lập từ `generate_synthetic_data` **chỉ dùng để kiểm tra pipeline và chạy unit test**, tuyệt đối không dùng để đánh giá chất lượng mô hình trong báo cáo.

---

#### `load_frame_csv(path)`
```python
load_frame_csv(path)
```

Đọc file CSV cấp khung hình và kiểm tra tính hợp lệ theo thứ tự nghiêm ngặt; nếu vi phạm sẽ ném `ValueError`:
1. **Chuẩn hóa tên cột video:** Nếu file thực tế dùng `video_name` (như `data/features/train_features.csv`) mà chưa có `video_id`, tự động đổi `video_name` $\rightarrow$ `video_id`.
2. **Kiểm tra thiếu cột:** Thiếu bất kỳ cột nào trong `ALL_COLUMNS` (`subject_id`, `video_id`, `frame_idx`, `ear`, `mar`, `label`).
3. **Kiểm tra giá trị thiếu (`NaN`):** Xuất hiện giá trị rỗng trong các cột bắt buộc.
4. **Kiểm tra tập nhãn:** Cột `label` chứa giá trị ngoài tập $\{0, 1\}$.

> [!TIP]
> **Thứ tự kiểm tra có chủ đích:** Kiểm tra thiếu cột trước khi truy cập dữ liệu bên trong để báo `ValueError` tường minh thay vì để Python văng lỗi `KeyError` khó gỡ.

---

#### `split_by_subject(df, test_size=0.25, seed=42)`
```python
train_df, test_df = split_by_subject(df, test_size=0.25, seed=42)
```

* Sử dụng `GroupShuffleSplit` với `groups = df["subject_id"]`.
* Tham số `test_size` là **tỷ lệ số người** (nhóm), không phải tỷ lệ số dòng.
* Đảm bảo tuyệt đối $\text{Subjects}_{\text{Train}} \cap \text{Subjects}_{\text{Test}} = \emptyset$ và tái lập 100% khi cố định `seed`.

---

### 2.2. `ai/features.py`

#### `build_window_features(window, ear_threshold=0.2, ear_index=0)`
```python
features = build_window_features(window, ear_threshold=0.2, ear_index=0)
```

Nhận mảng NumPy thuần có kích thước `(window_size, 2)` gồm 2 cột `[ear, mar]` và trả về vector 1 chiều gồm **9 đặc trưng** theo thứ tự cố định:

| Thứ tự | Tên đặc trưng | Ý nghĩa |
| :---: | :--- | :--- |
| 0 | `ear_mean` | Trung bình EAR trong cửa sổ |
| 1 | `mar_mean` | Trung bình MAR trong cửa sổ |
| 2 | `ear_std` | Độ lệch chuẩn EAR (mức độ dao động của mắt) |
| 3 | `mar_std` | Độ lệch chuẩn MAR (mức độ dao động của miệng) |
| 4 | `ear_min` | Giá trị EAR nhỏ nhất (mắt nhắm sâu nhất) |
| 5 | `mar_min` | Giá trị MAR nhỏ nhất |
| 6 | `ear_max` | Giá trị EAR lớn nhất |
| 7 | `mar_max` | Giá trị MAR lớn nhất (miệng há to nhất khi ngáp) |
| 8 | `perclos` | Tỷ lệ khung trong cửa sổ có $\text{EAR} < \text{ear\_threshold}$ |

> [!IMPORTANT]
> Hàm chỉ xử lý trên mảng NumPy thuần (không phụ thuộc `pandas.DataFrame`), nhờ đó ứng dụng webcam (`app/`) có thể truyền thẳng bộ đệm $N$ khung hình gần nhất vào hàm này mà không bị lệch đặc trưng giữa lúc train và lúc chạy thật.

---

#### `make_windows(df, window_size=30, stride=10, ear_threshold=0.2)`
```python
X, y, groups = make_windows(df, window_size=30, stride=10, ear_threshold=0.2)
```

* Nhóm dữ liệu theo từng `video_id`, sắp xếp tăng dần theo `frame_idx`, **không để cửa sổ vắt ngang giữa 2 video**.
* **Công thức số cửa sổ** cho một video dài $L$ khung:
  $$\text{Số cửa sổ} = \left\lfloor \frac{L - \text{window\_size}}{\text{stride}} \right\rfloor + 1 \quad (\text{bằng } 0 \text{ nếu } L < \text{window\_size})$$
* **Quy ước nhãn theo đa số (Majority Voting):** Cửa sổ mang nhãn `1` nếu có từ $50\%$ số khung trở lên mang `label = 1`; ngược lại mang nhãn `0`.
* **Đầu ra:** `X` kích thước `(n_windows, 9)`, `y` kích thước `(n_windows,)`, `groups` chứa `subject_id` tương ứng từng cửa sổ.

#### `get_feature_names()`
Trả về đúng danh sách 9 tên đặc trưng khớp 1-1 với thứ tự của `build_window_features`, dùng để lưu làm metadata kèm mô hình `.joblib`.

---

## 3. Nguyên lý kỹ thuật cốt lõi

1. **Vì sao dùng Cửa sổ trượt (Sliding Window) thay vì từng frame?**
   * Buồn ngủ là trạng thái diễn ra theo thời gian: một frame có EAR thấp chỉ có thể là cú chớp mắt sinh lý, còn nhắm mắt gục ngủ hoặc ngáp kéo dài qua nhiều frame liên tiếp.
   * Dữ liệu từng frame từ landmark rất nhiễu; thống kê `(mean, std, min, max, perclos)` giúp khử nhiễu và nắm bắt xu hướng.
   * Thiết lập `stride < window_size` (ví dụ `10 < 30`) giúp các cửa sổ gối đầu nhau, không bỏ sót sự kiện ở ranh giới.
2. **Vì sao phải chia theo `subject_id`?**
   * Mỗi người có mức EAR/MAR nền riêng và các cửa sổ kế tiếp của cùng một người rất giống nhau. Chia ngẫu nhiên theo dòng sẽ làm cùng một người xuất hiện ở cả Train và Test (data leakage), khiến điểm đánh giá ảo cao nhưng chạy kém khi gặp người lái mới.

---

## 4. Kiểm thử đơn vị (`test/test_window_features.py`)

| Tên hàm test | Mục tiêu kiểm chứng |
| :--- | :--- |
| `test_feature_vector_size` | Độ dài vector đặc trưng khớp chính xác với `len(get_feature_names()) == 9`. |
| `test_split_by_subject_no_overlap` | Giao tập `subject_id` giữa Train và Test rỗng; cả hai tập đều không rỗng. |
| `test_windows_do_not_cross_videos` | $6 \text{ video} \times 50 \text{ khung}$ ($W=20, S=10$) sinh đúng $6 \times 4 = 24$ cửa sổ; `X, y, groups` khớp chiều. |
| `test_synthetic_is_reproducible` | Gọi `generate_synthetic_data` cùng `seed` sinh hai DataFrame giống nhau hoàn toàn. |
| `test_load_frame_csv_missing_column` | CSV thiếu cột `ear` (tạo qua `tmp_path`) bắt buộc ném `ValueError`. |
| `test_load_frame_csv_bad_label` | CSV có nhãn không hợp lệ (`label = 2`) bắt buộc ném `ValueError`. |