import argparse
from pathlib import Path

import joblib
import numpy as np
import sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GroupShuffleSplit

from ai.dataset import REAL_FEATURE_COLUMNS, load_real_csv
from ai.evaluate import evaluate_model, print_report
from ai.features import get_feature_names, make_windows

REAL_CSV_PATH = "data/features/train_features.csv"

DEFAULT_PARAMS = {
    "n_estimators": 200,
    "max_depth": 8,
    "min_samples_leaf": 2,
    "class_weight": "balanced",
    "random_state": 42,
    "n_jobs": -1,
}


def train_model(X_train, y_train, params=None):
    """Huấn luyện Random Forest, trả về model đã fit."""
    final_params = {**DEFAULT_PARAMS, **(params or {})}
    model = RandomForestClassifier(**final_params)
    model.fit(X_train, y_train)
    return model


def split_by_person(X, y, groups, test_size=0.25, seed=42):
    """Chia train/test sao cho mỗi người chỉ nằm ở một phía."""
    splitter = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=seed)
    train_idx, test_idx = next(splitter.split(X, y, groups))
    return X[train_idx], X[test_idx], y[train_idx], y[test_idx]


def save_bundle(model, feature_names, window_size, threshold, path):
    """Lưu model cùng toàn bộ cấu hình cần để dự đoán lại."""
    bundle = {
        "model": model,
        "feature_names": list(feature_names),
        "window_size": window_size,
        "threshold": threshold,
        "labels": {0: "ALERT", 1: "DROWSY"},
        "sklearn_version": sklearn.__version__,
    }
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, path)
    return path


def load_windows(window_size=30):
    """Lấy dữ liệu thật của A: cắt cửa sổ và tính đặc trưng.

    Trả về: X (n_cửa_sổ x n_đặc_trưng), y (0/1), groups (id người), feature_names.
    """
    df = load_real_csv(REAL_CSV_PATH)
    X, y, groups = make_windows(
        df, window_size=window_size, stride=10,
        feature_columns=REAL_FEATURE_COLUMNS, min_face_ratio=0.5,
    )
    return X, y, groups, get_feature_names(REAL_FEATURE_COLUMNS)


def main():
    parser = argparse.ArgumentParser(description="Train Random Forest phát hiện buồn ngủ")
    parser.add_argument("--out", default="ai/model/drowsiness_rf.joblib")
    parser.add_argument("--window-size", type=int, default=30)
    parser.add_argument("--threshold", type=float, default=0.5)
    args = parser.parse_args()

    X, y, groups, feature_names = load_windows(args.window_size)
    X, y, groups = np.asarray(X), np.asarray(y), np.asarray(groups)

    X_train, X_test, y_train, y_test = split_by_person(X, y, groups)
    print(f"Cửa sổ train: {len(y_train)} (DROWSY {int(y_train.sum())}) | "
          f"test: {len(y_test)} (DROWSY {int(y_test.sum())})")

    model = train_model(X_train, y_train)

    print(f"Train acc: {model.score(X_train, y_train):.3f} | "
          f"Test acc: {model.score(X_test, y_test):.3f}")
    print_report(evaluate_model(model, X_test, y_test))

    saved = save_bundle(model, feature_names, args.window_size, args.threshold, args.out)
    print(f"Đã lưu model vào: {saved}")


if __name__ == "__main__":
    main()