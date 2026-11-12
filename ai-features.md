# Chuẩn Hóa Dữ Liệu & Trích Xuất Đặc Trưng (Window Features)

## 1. Mục Tiêu
* Cung cấp đầu vào chuẩn hóa ($X$, $y$, $\text{groups}$) phục vụ trực tiếp cho bước huấn luyện mô hình.
* Tái sử dụng đồng nhất logic trích xuất đặc trưng (feature engineering) cho cả pipeline huấn luyện (training) và ứng dụng thời gian thực (real-time app).

---

## 2. Danh Sách File Đã Tạo / Sửa
* `ai/__init__.py`
* `ai/dataset.py`
* `ai/features.py`
* `tests/test_window_features.py`

---

## 3. Chi Tiết Chức Năng (Modules)

### `ai/dataset.py`

#### 1. `generate_synthetic_data`
```python
generate_synthetic_data(
    n_subjects=10, 
    frames_per_video=300, 
    seed=42, 
    videos_per_subject=2
)
```
* **Mục đích:** Trả về `DataFrame` giả lập đầy đủ cấu trúc theo đặc tả ở mục 3.1.
* **Mô phỏng thực tế:** Mỗi "người" có mức EAR và MAR nền riêng (lấy ngẫu nhiên quanh $0.30$), phản ánh đúng sự biến thiên sinh học giữa các cá nhân.
* **Quy luật tạo nhãn:**
  * **Nửa đầu (Nhãn `0` - Tỉnh):** Chèn $3$ cú chớp mắt ngắn ($3$ khung EAR rất thấp) để tránh mô hình học nhầm *"chớp mắt tức thời là buồn ngủ"*.
  * **Nửa sau (Nhãn `1` - Buồn ngủ):** $\text{EAR}$ giảm $0.10$ (mắt nhắm sâu hơn) và xuất hiện $2$ đoạn $\text{MAR}$ tăng $0.40$ (mô phỏng hành vi ngáp, duy trì tối đa $12$ khung).
* **Xử lý số liệu:**
  * Toàn bộ giá trị $\text{EAR}/\text{MAR}$ được chặn không âm thông qua `np.clip`.
  * Số ngẫu nhiên được sinh từ `np.random.default_rng(seed)`, đảm bảo cùng seed sẽ cho kết quả đồng nhất $100\%$.
  * Hàm hoạt động an toàn ngay cả với video có độ dài rất ngắn (đã xử lý biên ngoại lệ khi `frames_per_video` nhỏ).

---

#### 2. `load_frame_csv`
```python
load_frame_csv(path)
```
Đọc file CSV và kiểm tra tính toàn vẹn dữ liệu. Báo lỗi `ValueError` nếu:
- [ ] Thiếu bất kỳ cột nào thuộc danh sách `ALL_COLUMNS`.
- [ ] Chứa giá trị khuyết thiếu (`NaN`) tại các cột bắt buộc.
- [ ] Cột `label` chứa giá trị khác tập hợp $\{0, 1\}$.

> [!TIP]
> **Thứ tự kiểm tra có chủ đích:** Kiểm tra sự tồn tại của các cột trước khi kiểm tra giá trị bên trong nhằm đưa ra thông báo tường minh, tránh phát sinh lỗi ngắt dòng bất ngờ (`KeyError`).

---

#### 3. `split_by_subject`
```python
split_by_subject(df, test_size=0.25, seed=42)
```
* Chia `DataFrame` thành `(train_df, test_df)` sử dụng `GroupShuffleSplit` theo `groups = df["subject_id"]`.
* Tham số `test_size` đại diện cho **tỉ lệ số người** (groups), hoàn toàn không phải tỉ lệ số hàng (samples).
* Bảo đảm tính độc lập: Không người nào xuất hiện ở cả hai tập ($\text{Train} \cap \text{Test} = \emptyset$).
* Cùng `seed` sẽ cho ra kết quả phân chia hoàn toàn nhất quán.

---

### `ai/features.py`

#### 1. `build_window_features`
```python
build_window_features(window, ear_threshold=0.2, ear_index=0)
```
Nhận vào mảng NumPy kích thước `(window_size, n_features)` và trả về vector đặc trưng $1$ chiều gồm:
* Thống kê mô tả: $\text{mean}, \text{std}, \text{min}, \text{max}$ của từng đặc trưng ($4 \times n_{\text{features}}$).
* **PERCLOS:** Tỷ lệ số khung có $\text{EAR} < \text{ear\_threshold}$ trong cửa sổ.

> [!NOTE]
> **Cấu trúc vector đầu ra ($9$ phần tử đối với $2$ đặc trưng EAR, MAR):**
> $$[\text{ear\_mean}, \text{mar\_mean}, \text{ear\_std}, \text{mar\_std}, \text{ear\_min}, \text{mar\_min}, \text{ear\_max}, \text{mar\_max}, \text{perclos}]$$
> *Hàm chỉ nhận mảng thuần (không phụ thuộc pandas DataFrame) nên có thể tái sử dụng trực tiếp trên bộ đệm $N$ khung gần nhất khi chạy app.*

---

#### 2. `make_windows`
```python
make_windows(df, window_size=30, stride=10, ear_threshold=0.2)
```
Cắt cửa sổ trượt trong từng video (nhóm theo `video_id`, sắp xếp tăng dần theo `frame_idx`), tuyệt đối **không** tạo cửa sổ vắt ngang qua hai video khác nhau.

* **Công thức xác định số cửa sổ cho một video có độ dài $L$ khung:**
  $$\text{Số cửa sổ} = \left\lfloor \frac{L - \text{window\_size}}{\text{stride}} \right\rfloor + 1 \quad (\text{bằng } 0 \text{ nếu } L < \text{window\_size})$$
* **Quy ước gán nhãn cửa sổ (Majority Voting):** Cửa sổ mang nhãn $1$ nếu có từ $50\%$ số khung trở lên mang `label = 1`; ngược lại mang nhãn $0$.
* **Đầu ra:** Mảng dữ liệu $(X, y, \text{groups})$ phục vụ huấn luyện và kiểm chứng chéo theo đối tượng.

---

#### 3. `get_feature_names`
```python
get_feature_names()
```
* Trả về danh sách tên đặc trưng theo đúng thứ tự logic của `build_window_features`.
* Danh sách này sẽ được lưu kèm theo model (metadata) ở Task 1B để đảm bảo trích xuất đặc trưng chuẩn xác khi inference trên app.

---

## 4. Kiểm Thử Đơn Vị (`tests/test_window_features.py`)

| Tên Test Case | Mục Tiêu Kiểm Tra |
| :--- | :--- |
| `test_feature_vector_size` | Vector đặc trưng có độ dài chuẩn bằng số tên đặc trưng ($9$). |
| `test_split_by_subject_no_overlap` | Giao của hai tập `subject_id` rỗng ($\text{Train} \cap \text{Test} = \emptyset$); cả hai tập đều có dữ liệu. |
| `test_windows_do_not_cross_videos` | $6 \text{ video} \times 50 \text{ frames}$ với $W=20, S=10$ ra đúng $6 \times 4 = 24$ cửa sổ; $X, y, \text{groups}$ khớp kích thước. |
| `test_synthetic_is_reproducible` | Cùng thiết lập `seed`, hàm sinh ra hai DataFrame hoàn toàn giống hệt nhau. |
| `test_load_frame_csv_missing_column` | Báo lỗi `ValueError` khi file CSV thiếu cột bắt buộc (`ear`). |
| `test_load_frame_csv_bad_label` | Báo lỗi `ValueError` khi file CSV chứa giá trị nhãn không hợp lệ (nhãn $2$). |

> [!TIP]
> Toàn bộ test case tự động tạo dữ liệu giả lập qua `generate_synthetic_data` và sử dụng fixture `tmp_path` của `pytest` cho file CSV, hoàn toàn độc lập với dữ liệu bên ngoài và không để lại file rác sau khi chạy.

---

## 5. Nguyên Lý Kỹ Thuật Cốt Lõi

### Vì Sao Cần Dùng Cửa Sổ Trượt (Sliding Window)?
Buồn ngủ là một trạng thái biến thiên theo chuỗi thời gian, không thể kết luận chính xác từ một khung hình đơn lẻ:
* **Chống báo động giả:** Một khung có $\text{EAR}$ thấp có thể chỉ là một cú chớp mắt sinh lý bình thường ($0.2 - 0.3\text{s}$). Chỉ khi mắt nhắm kéo dài nhiều khung liên tiếp mới là dấu hiệu nguy hiểm.
* **Thời lượng hành vi:** Ngáp thực sự luôn kéo dài qua nhiều khung hình liên tiếp ($2 - 4\text{s}$), không bao giờ diễn ra trong một khung đơn lẻ.
* **Lọc nhiễu:** Dữ liệu từng khung rất nhiễu do rung chấn hoặc sai số từ bộ định vị facial landmarks. Thống kê mô tả ($\text{mean}, \text{std}, \text{min}, \text{max}$) trên một cửa sổ giúp làm phẳng nhiễu và làm rõ xu hướng vận động.
* **Tránh bỏ sót sự kiện:** Khi $\text{stride} < \text{window\_size}$, các cửa sổ gối đầu lên nhau giúp bắt trọn các hành vi nằm ở ranh giới khung.

### Chỉ Số Sinh Học: EAR, MAR & PERCLOS
* **EAR (Eye Aspect Ratio):** Tỉ lệ hình học giữa chiều cao và chiều rộng của mắt từ các điểm landmark. Mắt mở tỉnh táo thì $\text{EAR}$ dao động quanh $0.25 - 0.35$; mắt nhắm thì $\text{EAR}$ tụt nhanh về gần $0$.
* **MAR (Mouth Aspect Ratio):** Tỉ lệ tương tự cho khuôn miệng. Miệng ngậm hoặc nói chuyện bình thường thì $\text{MAR}$ thấp; khi ngáp mở to theo chiều dọc thì $\text{MAR}$ tăng vọt.
* **PERCLOS:** Tỷ lệ phần trăm thời gian mắt nhắm (hoặc gần nhắm) trong một khoảng quan sát. Ở đây được xấp xỉ bằng tỉ lệ số khung có $\text{EAR} < \text{threshold}$ (mặc định $0.2$) bên trong cửa sổ trượt.

### Chống Rò Rỉ Dữ Liệu (Data Leakage) Bằng Phân Nhóm
* **Nguyên nhân:** Mỗi người có cấu trúc giải phẫu và mức $\text{EAR}/\text{MAR}$ nền riêng biệt. Các cửa sổ liên tiếp của cùng một người có mức độ tương quan cực kỳ cao.
* **Rủi ro:** Nếu chia ngẫu nhiên theo từng dòng, các cửa sổ của cùng một cá nhân sẽ xuất hiện ở cả tập Train và Test. Mô hình sẽ học cách *"nhận diện người lái"* qua giá trị nền thay vì học *"dấu hiệu buồn ngủ"*, dẫn đến điểm số đánh giá trên tập kiểm thử cao ảo.
* **Giải pháp:** Sử dụng `GroupShuffleSplit` theo `subject_id` để tập Test luôn là người hoàn toàn mới (unseen subjects), phản ánh chính xác điều kiện triển khai ứng dụng thực tế.

### Quy Ước Nhãn Cửa Sổ (Majority Voting)
Cửa sổ nằm ở ranh giới giữa tỉnh táo và buồn ngủ sẽ chứa cả nhãn $0$ và nhãn $1$. Hệ thống áp dụng quy ước **theo đa số**:
$$\text{Nhãn cửa sổ} = 
\begin{cases} 
1 & \text{nếu } \frac{\sum \text{label}_1}{\text{window\_size}} \ge 0.5 \\
0 & \text{ngược lại}
\end{cases}$$

> [!WARNING]
> **Lưu ý quan trọng:** Toàn bộ dữ liệu sinh trong module này là dữ liệu giả lập (synthetic data), phục vụ mục đích kiểm tra tính toàn vẹn của đường ống xử lý mã nguồn (pipeline test), hoàn toàn không dùng để đánh giá chất lượng hay độ chính xác thực tế của mô hình học máy.

---

## 6. Kiến Thức Áp Dụng
* **Xử lý dữ liệu mảng & bảng:** `NumPy`, `pandas` (`groupby`, thống kê mô tả).
* **Thuật toán & Phân chia tập mẫu:** Cửa sổ trượt (Sliding Window), `GroupShuffleSplit` (`scikit-learn`).
* **Kiểm thử tự động:** `pytest`, kiểm tra ngoại lệ (`pytest.raises`), fixture quản lý thư mục tạm (`tmp_path`).