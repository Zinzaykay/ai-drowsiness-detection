"""Chọn ngưỡng bằng đường precision-recall, vẽ hình cho báo cáo.

Ngưỡng được chọn trên các dự đoán của ĐÁNH GIÁ CHÉO (mỗi cửa sổ được dự đoán khi
người đó nằm ở tập test), KHÔNG chọn trên một tập test cố định.

Chạy:
    python -m ai.tune_threshold --min-recall 0.90
"""
import argparse
from pathlib import Path

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix, f1_score, precision_recall_curve

from ai.cross_validate import metrics_at, run_group_cv
from ai.train import DEFAULT_PARAMS, load_windows


def choose_threshold(y_true, proba, min_recall=0.90):
    """Trong các ngưỡng có recall >= min_recall, chọn ngưỡng cho precision cao nhất.

    Nếu không ngưỡng nào đạt min_recall thì chọn ngưỡng cho F1 cao nhất và đặt
    reached_min_recall = False. Trả về dict: threshold, precision, recall, f1.
    """
    y_true, proba = np.asarray(y_true), np.asarray(proba)
    precision, recall, thresholds = precision_recall_curve(y_true, proba)
    # precision/recall dài hơn thresholds đúng 1 phần tử (điểm cuối), bỏ nó đi
    precision, recall = precision[:-1], recall[:-1]

    ok = recall >= min_recall
    if ok.any():
        idx = np.flatnonzero(ok)
        # precision cao nhất; hòa thì lấy ngưỡng lớn hơn (ít báo động giả hơn)
        best = max(idx, key=lambda i: (precision[i], thresholds[i]))
        reached = True
    else:
        f1 = 2 * precision * recall / np.maximum(precision + recall, 1e-12)
        best = int(np.argmax(f1))
        reached = False

    t = float(thresholds[best])
    f1_best = f1_score(y_true, (proba >= t).astype(int), zero_division=0)
    return {"threshold": t, "precision": float(precision[best]),
            "recall": float(recall[best]), "f1": float(f1_best),
            "reached_min_recall": reached}


def plot_pr_curve(y_true, proba, chosen, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    precision, recall, _ = precision_recall_curve(y_true, proba)
    plt.figure(figsize=(5, 4))
    plt.plot(recall, precision, label="Random Forest")
    plt.scatter([chosen["recall"]], [chosen["precision"]], color="red", zorder=3,
                label=f"ngưỡng {chosen['threshold']:.2f}")
    plt.xlabel("Recall (DROWSY)")
    plt.ylabel("Precision (DROWSY)")
    plt.title("Đường precision-recall (đánh giá chéo theo người)")
    plt.legend()
    plt.grid(alpha=0.3)
    _save(plt, path)


def plot_feature_importance(model, feature_names, path, top=15):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    imp = np.asarray(model.feature_importances_)
    order = np.argsort(imp)[::-1][:top][::-1]
    plt.figure(figsize=(6, 5))
    plt.barh([feature_names[i] for i in order], imp[order])
    plt.xlabel("Độ quan trọng")
    plt.title("Độ quan trọng đặc trưng (Random Forest)")
    _save(plt, path)


def plot_confusion_matrix(y_true, proba, threshold, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    cm = confusion_matrix(y_true, (proba >= threshold).astype(int), labels=[0, 1])
    plt.figure(figsize=(4, 3.6))
    plt.imshow(cm, cmap="Blues")
    for (i, j), v in np.ndenumerate(cm):
        plt.text(j, i, str(v), ha="center", va="center")
    plt.xticks([0, 1], ["ALERT", "DROWSY"])
    plt.yticks([0, 1], ["ALERT", "DROWSY"])
    plt.xlabel("Dự đoán")
    plt.ylabel("Thực tế")
    plt.title(f"Confusion matrix gộp (ngưỡng {threshold:.2f})")
    _save(plt, path)


def _save(plt, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()


def main():
    parser = argparse.ArgumentParser(description="Chọn ngưỡng và vẽ hình")
    parser.add_argument("--min-recall", type=float, default=0.90)
    parser.add_argument("--window-size", type=int, default=30)
    parser.add_argument("--mode", choices=["loso", "kfold"], default="loso")
    parser.add_argument("--figures-dir", default="docs/figures")
    args = parser.parse_args()

    X, y, groups, feature_names = load_windows(args.window_size)
    X, y, groups = np.asarray(X), np.asarray(y), np.asarray(groups)

    res = run_group_cv(X, y, groups, lambda: RandomForestClassifier(**DEFAULT_PARAMS),
                       mode=args.mode)
    chosen = choose_threshold(y, res["proba"], args.min_recall)

    base = metrics_at(y, res["proba"], 0.5)
    print(f"Ngưỡng 0.5      : P {base['precision']:.3f}  R {base['recall']:.3f}  F1 {base['f1']:.3f}")
    print(f"Ngưỡng đã chọn  : {chosen['threshold']:.3f} -> "
          f"P {chosen['precision']:.3f}  R {chosen['recall']:.3f}  F1 {chosen['f1']:.3f}")
    if not chosen["reached_min_recall"]:
        print(f"CẢNH BÁO: không ngưỡng nào đạt recall >= {args.min_recall}; "
              f"đã chọn ngưỡng cho F1 cao nhất.")

    out = Path(args.figures_dir)
    plot_pr_curve(y, res["proba"], chosen, out / "pr_curve.png")
    plot_confusion_matrix(y, res["proba"], chosen["threshold"], out / "confusion_matrix.png")

    # Model cuối huấn luyện trên TOÀN BỘ dữ liệu, chỉ để xem độ quan trọng đặc trưng
    final = RandomForestClassifier(**DEFAULT_PARAMS).fit(X, y)
    plot_feature_importance(final, feature_names, out / "feature_importance.png")
    print(f"Đã lưu hình vào {out}/")
    print(f"\nĐể train model cuối: python -m ai.train --threshold {chosen['threshold']:.2f}")


if __name__ == "__main__":
    main()
