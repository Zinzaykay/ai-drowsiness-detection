"""Đánh giá chéo THEO NGƯỜI: Random Forest so với baseline luật.

Chạy:
    python -m ai.cross_validate --mode loso
    python -m ai.cross_validate --mode kfold --n-splits 5
"""
import argparse

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score, precision_score, recall_score
from sklearn.model_selection import GroupKFold, LeaveOneGroupOut

from ai.baseline import RuleBaseline
from ai.train import DEFAULT_PARAMS, load_windows


def make_splits(X, y, groups, mode="loso", n_splits=5):
    """Sinh (train_idx, test_idx). Mỗi người chỉ nằm ở MỘT phía trong mỗi lần."""
    if mode == "loso":
        splitter = LeaveOneGroupOut()
    elif mode == "kfold":
        n_groups = len(np.unique(groups))
        splitter = GroupKFold(n_splits=min(n_splits, n_groups))
    else:
        raise ValueError("mode phải là 'loso' hoặc 'kfold'")
    yield from splitter.split(X, y, groups)


def _proba_drowsy(model, X):
    """Xác suất lớp 1 theo model.classes_ (không mặc định là cột thứ hai)."""
    classes = list(model.classes_)
    if 1 not in classes:
        return np.zeros(len(X))
    return model.predict_proba(X)[:, classes.index(1)]


def metrics_at(y_true, proba, threshold=0.5):
    """Precision/recall/F1 của lớp DROWSY. Nhãn không có mẫu dương -> recall = NaN."""
    y_pred = (np.asarray(proba) >= threshold).astype(int)
    has_pos = np.sum(y_true == 1) > 0
    return {
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0) if has_pos else np.nan,
        "f1": f1_score(y_true, y_pred, zero_division=0) if has_pos else np.nan,
    }


def run_group_cv(X, y, groups, model_factory, mode="loso", n_splits=5, threshold=0.5):
    """Chạy đánh giá chéo theo người.

    model_factory: hàm không tham số trả về model CHƯA fit (có fit, predict_proba, classes_).
    Trả về dict:
        proba       : xác suất DROWSY của MỌI cửa sổ (khi người đó nằm ở tập test)
        per_group   : {subject_id: {precision, recall, f1}} (chỉ với mode loso)
        per_fold    : list các dict chỉ số từng lần
    """
    X, y, groups = np.asarray(X), np.asarray(y), np.asarray(groups)
    proba = np.zeros(len(y))
    per_fold, per_group = [], {}

    for train_idx, test_idx in make_splits(X, y, groups, mode, n_splits):
        model = model_factory()
        model.fit(X[train_idx], y[train_idx])
        proba[test_idx] = _proba_drowsy(model, X[test_idx])
        m = metrics_at(y[test_idx], proba[test_idx], threshold)
        per_fold.append(m)
        if mode == "loso":
            per_group[str(groups[test_idx][0])] = m

    return {"proba": proba, "per_fold": per_fold, "per_group": per_group}


def summarize(result, y, threshold=0.5):
    """mean ± std qua các lần (bỏ NaN) và điểm GỘP (gom mọi dự đoán rồi tính một lần)."""
    out = {}
    for key in ("precision", "recall", "f1"):
        vals = np.array([f[key] for f in result["per_fold"]], dtype=float)
        out[key] = (float(np.nanmean(vals)), float(np.nanstd(vals)))
    out["pooled"] = metrics_at(np.asarray(y), result["proba"], threshold)
    return out


def print_summary(name, summary):
    p = summary["pooled"]
    print(f"{name:<28} "
          f"P {summary['precision'][0]:.3f}±{summary['precision'][1]:.3f} | "
          f"R {summary['recall'][0]:.3f}±{summary['recall'][1]:.3f} | "
          f"F1 {summary['f1'][0]:.3f}±{summary['f1'][1]:.3f} || "
          f"gộp: P {p['precision']:.3f} R {p['recall']:.3f} F1 {p['f1']:.3f}")


def main():
    parser = argparse.ArgumentParser(description="Đánh giá chéo theo người")
    parser.add_argument("--mode", choices=["loso", "kfold"], default="loso")
    parser.add_argument("--n-splits", type=int, default=5)
    parser.add_argument("--window-size", type=int, default=30)
    parser.add_argument("--threshold", type=float, default=0.5)
    args = parser.parse_args()

    X, y, groups, feature_names = load_windows(args.window_size)
    X, y, groups = np.asarray(X), np.asarray(y), np.asarray(groups)
    print(f"{len(y)} cửa sổ, {len(np.unique(groups))} người, "
          f"tỉ lệ DROWSY {y.mean():.3f}, chế độ {args.mode}\n")

    models = {
        "Baseline (perclos)": lambda: RuleBaseline(feature_names, use=["perclos"]),
        "Baseline (perclos + mar_max)": lambda: RuleBaseline(feature_names, use=["perclos", "mar_max"]),
        "Random Forest": lambda: RandomForestClassifier(**DEFAULT_PARAMS),
    }
    results = {}
    for name, factory in models.items():
        res = run_group_cv(X, y, groups, factory, args.mode, args.n_splits, args.threshold)
        results[name] = res
        print_summary(name, summarize(res, y, args.threshold))

    if args.mode == "loso":
        print("\nRandom Forest theo từng người (recall/F1 = nan nếu người đó không có cửa sổ DROWSY):")
        for sid, m in sorted(results["Random Forest"]["per_group"].items()):
            print(f"  {sid:<12} P {m['precision']:.3f}  R {m['recall']:.3f}  F1 {m['f1']:.3f}")


if __name__ == "__main__":
    main()
