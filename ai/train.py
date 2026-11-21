import argparse
from pathlib import Path
import joblib
import numpy as np
import sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GroupShuffleSplit
from ai.evaluate import evaluate_model, print_report

DEFAULT_PARAMS = {
    "n_estimators": 200,
    "max_depth": 10,
    "min_samples_leaf": 2,
    "class_weight": "balanced",
    "random_state": 42,
    "n_jobs": -1,
}

def train_model(X_train, y_train, params=None):
    """Huấn luyện random forest, trả về model đã fit"""
    final_params = {**DEFAULT_PARAMS, **(params or {})}
    model = RandomForestClassifier(**final_params)
    model.fit(X_train, y_train)
    return model

def split_by_person(X, y, groups, test_size = 0.25, seed = 42):
    """chia train/test sao cho một người chỉ nằm ở 1 phía"""
    splitter = GroupShuffleSplit(n_splits = 1, test_size = test_size, random_state = seed)
    train_idx, test_idx = next(splitter.split(X, y, groups))
    return X[train_idx], X[test_idx], y[train_idx], y[test_idx]

def save_bundle(model, feature_name, window_size, threshold, path):
    """Lưu model cùng toàn bộ cấu hình cần để dự đoán lại."""
    bundle = {
        "model": model,
        "feature_name": list(feature_name),
        "window_size": window_size,
        "threshold": threshold,
        "labels": {0: "ALERT", 1: "DROWSY"},
        "sklearn_verison": sklearn_version_,
    }
    path = Path(path)
    path.parent.mkdir(parents = True, exits_ok = True)
    joblib.dump(bundle, path)
    return path

def load_windows(window_size):
    """Lấy dữ liệu từ 1A.

    PHẢI trả về: X (n_cửa_sổ x n_đặc_trưng), y (0/1), groups (id người), feature_names.
    Hãy thay phần thân hàm bằng các hàm thật của 1A.
    """
    raise NotImplementedError("Nối với ai/dataset.py và ai/features.py của 1A")

def main():
    parser = argparse.ArgumentParser(description = "Train Random Forest phát hiện buồn ngủ")
    parser.add_argument("--out", default = "ai/model/drowsiness_rf.joblib")
    parser.add_argument("--window_size", type = int, default = 30)
    parser.add_argument("--threshold", type = float, default = 0.5)
    args = parser.parse_args()

    X, y, groups, feature_names = load_windows(args.window_size)
    X, y, groups = np.array(X), np.asarray(y), np.asarray(groups)

    X_train, X_test, y_train, y_test = split_by_person(X, y, groups)
    model = train_model(X_train, y_train)

    print(f"Train acc: {model.score(X_train, y_train):.3f} | Test acc: {model.score(X_test, y_test):.3f}")
    print_report(evaluate_model(model, X_test, y_test))

    saved = save_bundle(model, feature_names, args.window_size, args.threshold, args.out)
    print(f"Đã lưu model vào: {saved}")
    print("Lưu ý: kết quả trên dữ liệu giả chỉ để kiểm tra pipeline, không phải kết quả hệ thống")

if _name_ == "__main__":
    main()