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
                 ear_threshold: float = EAR_LOW_THRESHOLD):
    """Cắt cửa sổ TRONG TỪNG VIDEO. Trả về X, y, groups."""
    X, y, groups = [], [], []
    for _, video in df.groupby("video_id", sort=False):
        video = video.sort_values("frame_idx")
        values = video[FEATURE_COLUMNS].to_numpy()
        labels = video[LABEL_COLUMN].to_numpy()
        subject = video["subject_id"].iloc[0]
        for start in range(0, len(video) - window_size + 1, stride):
            end = start + window_size
            X.append(build_window_features(values[start:end], ear_threshold))
            # Quy ước: nhãn cửa sổ theo ĐA SỐ (>= 50% khung là 1 thì nhãn = 1)
            y.append(int(labels[start:end].mean() >= 0.5))
            groups.append(subject)
    return np.array(X), np.array(y), np.array(groups)


def get_feature_names() -> list[str]:
    """Tên đặc trưng đúng thứ tự với build_window_features."""
    names = [f"{f}_{s}" for s in STAT_NAMES for f in FEATURE_COLUMNS]
    return names + ["perclos"]