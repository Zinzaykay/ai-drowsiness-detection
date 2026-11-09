"""Tạo, đọc và chia dữ liệu khung hình (DỮ LIỆU GIẢ để phát triển pipeline)."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit

# ---- Hằng số ----
FEATURE_COLUMNS = ["ear", "mar"]
LABEL_COLUMN = "label"
META_COLUMNS = ["subject_id", "video_id", "frame_idx"]
ALL_COLUMNS = META_COLUMNS + FEATURE_COLUMNS + [LABEL_COLUMN]
VALID_LABELS = {0, 1}


def generate_synthetic_data(n_subjects: int = 10,
                            frames_per_video: int = 300,
                            seed: int = 42,
                            videos_per_subject: int = 2) -> pd.DataFrame:
    """Sinh dữ liệu giả. Mỗi người có EAR/MAR nền riêng.

    Mỗi video: nửa đầu tỉnh (label 0), một đoạn sau buồn ngủ (label 1):
    EAR thấp hơn (nhắm mắt lâu), MAR đôi lúc cao (ngáp).
    """
    rng = np.random.default_rng(seed)
    rows = []
    for s in range(n_subjects):
        base_ear = rng.normal(0.30, 0.03)   # nền riêng từng người
        base_mar = rng.normal(0.30, 0.05)
        for v in range(videos_per_subject):
            n = frames_per_video
            ear = rng.normal(base_ear, 0.02, n)
            mar = rng.normal(base_mar, 0.03, n)
            label = np.zeros(n, dtype=int)

            start = int(n * 0.5)             # đoạn buồn ngủ
            label[start:] = 1
            ear[start:] -= 0.10               # mắt nhắm nhiều hơn
            # vài cú nhắm mắt ngắn (chớp) rải rác ở đoạn tỉnh
            if start > 0:
                for b in rng.integers(0, start, size=3):
                    ear[b:b+3] = rng.normal(0.08, 0.02, size=len(ear[b:b+3]))
            yawn_len = max(1, min(12, n - start))
            if n - start - yawn_len > 0:
                for y in rng.integers(start, n - yawn_len, size=2):
                    mar[y:y+yawn_len] += 0.40

            rows.append(pd.DataFrame({
                "subject_id": f"S{s:02d}",
                "video_id": f"S{s:02d}_V{v}",
                "frame_idx": np.arange(n),
                "ear": np.clip(ear, 0, None),
                "mar": np.clip(mar, 0, None),
                "label": label,
            }))
    return pd.concat(rows, ignore_index=True)[ALL_COLUMNS]


def load_frame_csv(path: str) -> pd.DataFrame:
    """Đọc CSV và kiểm tra: đủ cột, nhãn chỉ 0/1, không thiếu giá trị."""
    df = pd.read_csv(path)
    missing = [c for c in ALL_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Thiếu cột: {missing}")
    if df[ALL_COLUMNS].isna().any().any():
        raise ValueError("Dữ liệu có giá trị thiếu (NaN)")
    if not set(df[LABEL_COLUMN].unique()) <= VALID_LABELS:
        raise ValueError("Nhãn chỉ được gồm 0 và 1")
    return df


def split_by_subject(df: pd.DataFrame, test_size: float = 0.25,
                     seed: int = 42) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Chia train/test sao cho không người nào xuất hiện ở cả hai tập."""
    gss = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=seed)
    train_idx, test_idx = next(gss.split(df, groups=df["subject_id"]))
    return df.iloc[train_idx].reset_index(drop=True), \
           df.iloc[test_idx].reset_index(drop=True)