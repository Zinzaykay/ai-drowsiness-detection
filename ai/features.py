"""Biến chuỗi khung hình thành đặc trưng theo cửa sổ trượt.
Dùng CHUNG cho lúc train và lúc chạy app."""
from __future__ import annotations

import numpy as np
import pandas as pd
from ai.dataset import FEATURE_COLUMNS, LABEL_COLUMN

EAR_LOW_THRESHOLD = 0.2   # ngưỡng EAR thấp (tham số)
STAT_NAMES = ["mean", "std", "min", "max"]


def build_window_features(window: np.ndarray,
                          ear_threshold: float = EAR_LOW_THRESHOLD,
                          ear_index: int = 0) -> np.ndarray:
    """window: (window_size, n_features) -> vector 1 chiều.

    Gồm mean, std, min, max của từng đặc trưng + tỷ lệ khung EAR thấp (PERCLOS).
    Độ dài vector = 4 * n_features + 1.
    """
    window = np.asarray(window, dtype=float)
    if window.ndim != 2:
        raise ValueError("window phải có dạng (window_size, n_features)")
    stats = np.concatenate([
        window.mean(axis=0),
        window.std(axis=0),
        window.min(axis=0),
        window.max(axis=0),
    ])
    perclos = np.mean(window[:, ear_index] < ear_threshold)
    return np.append(stats, perclos)


def make_windows(df: pd.DataFrame, window_size: int = 30, stride: int = 10,
                 ear_threshold: float = EAR_LOW_THRESHOLD,
                 feature_columns: list[str] | None = None,
                 min_face_ratio: float | None = None):
    """Cắt cửa sổ TRONG TỪNG VIDEO. Trả về X, y, groups.

    feature_columns: cột dùng làm đặc trưng (mặc định FEATURE_COLUMNS = ear, mar).
        Cột "ear" phải đứng đầu (ear_index = 0).
    min_face_ratio: nếu có cột face_detected, bỏ cửa sổ có tỉ lệ khung thấy mặt
        nhỏ hơn giá trị này (mặc định None = không lọc).
    """
    feature_columns = list(feature_columns or FEATURE_COLUMNS)
    use_face = min_face_ratio is not None and "face_detected" in df.columns
    X, y, groups = [], [], []
    for _, video in df.groupby("video_id", sort=False):
        video = video.sort_values("frame_idx")
        values = video[feature_columns].to_numpy()
        faces = video["face_detected"].to_numpy() if use_face else None
        labels = video[LABEL_COLUMN].to_numpy()
        subject = video["subject_id"].iloc[0]
        for start in range(0, len(video) - window_size + 1, stride):
            end = start + window_size
            if use_face and faces[start:end].mean() < min_face_ratio:
                continue
            X.append(build_window_features(values[start:end], ear_threshold))
            # Quy ước: nhãn cửa sổ theo ĐA SỐ (>= 50% khung là 1 thì nhãn = 1)
            y.append(int(labels[start:end].mean() >= 0.5))
            groups.append(subject)
    return np.array(X), np.array(y), np.array(groups)


def get_feature_names(feature_columns: list[str] | None = None) -> list[str]:
    """Tên đặc trưng đúng thứ tự với build_window_features."""
    feature_columns = list(feature_columns or FEATURE_COLUMNS)
    names = [f"{f}_{s}" for s in STAT_NAMES for f in feature_columns]
    return names + ["perclos"]