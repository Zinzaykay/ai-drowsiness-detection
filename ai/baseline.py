"""Baseline luật đơn giản (không học máy) để so sánh với Random Forest.

Luật: DROWSY nếu BẤT KỲ đặc trưng nào trong `use` >= ngưỡng riêng của nó.
Ví dụ use=["perclos"]              -> chỉ dùng tỉ lệ khung hình nhắm mắt (EAR thấp)
        use=["perclos", "mar_max"]  -> thêm luật độ há miệng lớn (bắt ngáp)

Ngưỡng của từng đặc trưng được chọn trên tập TRAIN (cho F1 cao nhất của riêng luật đó),
sau đó áp dụng sang tập test. Có fit / predict / predict_proba để dùng chung
với run_group_cv.
"""
import numpy as np
from sklearn.metrics import f1_score


class RuleBaseline:
    classes_ = np.array([0, 1])

    def __init__(self, feature_names, use=("perclos",)):
        self.feature_names = list(feature_names)
        self.use = list(use)
        missing = [u for u in self.use if u not in self.feature_names]
        if missing:
            raise ValueError(f"Không có đặc trưng: {missing}")
        self.idx = [self.feature_names.index(u) for u in self.use]
        self.thresholds_ = None

    @staticmethod
    def _best_threshold(x, y):
        """Chọn ngưỡng cho luật 'x >= t' sao cho F1 của lớp 1 cao nhất."""
        candidates = np.unique(np.quantile(x, np.linspace(0.05, 0.95, 91)))
        best_t, best_f1 = candidates[0], -1.0
        for t in candidates:
            f1 = f1_score(y, (x >= t).astype(int), pos_label=1, zero_division=0)
            if f1 > best_f1:
                best_t, best_f1 = t, f1
        return float(best_t)

    def fit(self, X, y):
        X, y = np.asarray(X, dtype=float), np.asarray(y)
        self.thresholds_ = [self._best_threshold(X[:, i], y) for i in self.idx]
        return self

    def predict(self, X):
        if self.thresholds_ is None:
            raise RuntimeError("Hãy gọi fit() trước")
        X = np.asarray(X, dtype=float)
        hits = [X[:, i] >= t for i, t in zip(self.idx, self.thresholds_)]
        return np.any(hits, axis=0).astype(int)

    def predict_proba(self, X):
        """Baseline cho kết quả cứng: xác suất DROWSY là 0 hoặc 1."""
        p1 = self.predict(X).astype(float)
        return np.column_stack([1.0 - p1, p1])
