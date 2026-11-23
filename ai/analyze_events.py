"""Phân tích hiệu năng mô hình theo từng loại sự kiện (eye_closed, head_nod, yawn).

Cách chạy:
    python -m ai.analyze_events
    python -m ai.analyze_events --threshold 0.5 --window-size 30 --stride 10
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GroupKFold

from ai.features import build_window_features

DEFAULT_EVENTS = ("eye_closed", "head_nod", "yawn")


def _resolve_column(
    df: pd.DataFrame,
    candidates: Iterable[str],
    override: str | None = None,
) -> str:
    """Tìm tên cột hợp lệ trong DataFrame từ danh sách ứng viên."""
    if override:
        if override not in df.columns:
            raise ValueError(f"Không tìm thấy cột '{override}' trong {list(df.columns)}")
        return override
    for col in candidates:
        if col in df.columns:
            return col
    raise ValueError(
        f"Không tìm thấy cột phù hợp trong {list(df.columns)}. "
        f"Các tên được hỗ trợ: {list(candidates)}"
    )


def load_features_csv(path: str | Path) -> pd.DataFrame:
    """Đọc file features CSV và chuẩn hóa cột video_name -> video_id."""
    df = pd.read_csv(path)
    if "video_id" not in df.columns and "video_name" in df.columns:
        df = df.rename(columns={"video_name": "video_id"})

    required = ["subject_id", "video_id", "frame_idx", "ear", "mar", "label"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Thiếu cột trong features CSV: {missing}")

    df = df.dropna(subset=["ear", "mar", "label"]).copy()
    df["label"] = df["label"].astype(int)
    return df


def load_annotations_csv(
    path: str | Path,
    video_col: str | None = None,
    event_col: str | None = None,
    start_col: str | None = None,
    end_col: str | None = None,
    fps: float = 30.0,
) -> pd.DataFrame:
    """Đọc file annotations và chuẩn hóa về [video_id, event_type, start_frame, end_frame, event_id]."""
    raw = pd.read_csv(path)
    v_col = _resolve_column(
        raw, ["video_id", "video_name", "video", "clip_id", "filename"], video_col
    )
    e_col = _resolve_column(
        raw, ["event_type", "behavior", "event", "type", "class"], event_col
    )

    if start_col or any(c in raw.columns for c in ["start_frame", "frame_start", "start_idx"]):
        s_col = _resolve_column(raw, ["start_frame", "frame_start", "start_idx"], start_col)
        t_col = _resolve_column(raw, ["end_frame", "frame_end", "end_idx"], end_col)
        start_frames = raw[s_col].astype(int)
        end_frames = raw[t_col].astype(int)
    else:
        s_col = _resolve_column(raw, ["start_sec", "start_time", "start"], start_col)
        t_col = _resolve_column(raw, ["end_sec", "end_time", "end"], end_col)
        start_frames = np.floor(raw[s_col].astype(float) * fps).astype(int)
        end_frames = np.ceil(raw[t_col].astype(float) * fps).astype(int)

    ann = pd.DataFrame(
        {
            "video_id": raw[v_col].astype(str),
            "event_type": raw[e_col].astype(str).str.strip().str.lower(),
            "start_frame": start_frames,
            "end_frame": end_frames,
        }
    )
    ann["event_id"] = np.arange(len(ann), dtype=int)
    return ann


def assign_frame_events(df: pd.DataFrame, annotations: pd.DataFrame) -> pd.DataFrame:
    """Gán cột event_type và event_id cho từng khung hình dựa trên khoảng frame."""
    out = df.copy()
    out["video_id"] = out["video_id"].astype(str)
    out["event_type"] = "normal"
    out["event_id"] = -1

    for row in annotations.itertuples(index=False):
        mask = (
            (out["video_id"] == row.video_id)
            & (out["frame_idx"] >= row.start_frame)
            & (out["frame_idx"] <= row.end_frame)
        )
        out.loc[mask, "event_type"] = row.event_type
        out.loc[mask, "event_id"] = row.event_id

    return out


def build_event_windows(
    df_with_events: pd.DataFrame,
    window_size: int = 30,
    stride: int = 10,
    ear_threshold: float = 0.2,
    min_event_frames: int = 1,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, pd.DataFrame]:
    """Cắt cửa sổ trượt theo từng video và lưu metadata sự kiện của từng cửa sổ."""
    X_list: list[np.ndarray] = []
    y_list: list[int] = []
    groups_list: list = []
    meta_rows: list[dict] = []

    for video_id, group in df_with_events.groupby("video_id", sort=False):
        g = group.sort_values("frame_idx").reset_index(drop=True)
        n_frames = len(g)
        if n_frames < window_size:
            continue

        ear_mar = g[["ear", "mar"]].to_numpy(dtype=float)
        labels = g["label"].to_numpy(dtype=int)
        events = g["event_type"].to_numpy()
        event_ids = g["event_id"].to_numpy(dtype=int)
        subject_id = g["subject_id"].iloc[0]

        for start in range(0, n_frames - window_size + 1, stride):
            end = start + window_size
            feats = build_window_features(ear_mar[start:end], ear_threshold=ear_threshold)
            win_label = int(labels[start:end].mean() >= 0.5)

            win_events = events[start:end]
            win_eids = event_ids[start:end]
            non_normal_mask = win_events != "normal"

            if int(non_normal_mask.sum()) >= min_event_frames:
                vals, counts = np.unique(win_events[non_normal_mask], return_counts=True)
                dom_event = str(vals[np.argmax(counts)])
                eids_for_dom = win_eids[win_events == dom_event]
                eid_vals, eid_counts = np.unique(eids_for_dom, return_counts=True)
                dom_event_id = int(eid_vals[np.argmax(eid_counts)])
            else:
                dom_event = "normal"
                dom_event_id = -1

            X_list.append(feats)
            y_list.append(win_label)
            groups_list.append(subject_id)
            meta_rows.append(
                {
                    "video_id": video_id,
                    "subject_id": subject_id,
                    "start_frame": int(g["frame_idx"].iloc[start]),
                    "end_frame": int(g["frame_idx"].iloc[end - 1]),
                    "y_true": win_label,
                    "event_type": dom_event,
                    "event_id": dom_event_id,
                    "ear_mean": float(feats[0]),
                    "mar_mean": float(feats[1]),
                    "perclos": float(feats[-1]),
                }
            )

    X = np.vstack(X_list) if X_list else np.empty((0, 9), dtype=float)
    y = np.asarray(y_list, dtype=int)
    groups = np.asarray(groups_list)
    meta_df = pd.DataFrame(meta_rows)
    return X, y, groups, meta_df


def get_oof_probabilities(
    X: np.ndarray,
    y: np.ndarray,
    groups: np.ndarray,
    n_estimators: int = 200,
    seed: int = 42,
) -> np.ndarray:
    """Tính xác suất dự đoán Out-of-Fold theo subject_id để tránh data leakage."""
    unique_subjects = np.unique(groups)
    n_splits = min(5, len(unique_subjects))
    if n_splits < 2:
        raise ValueError("Cần ít nhất 2 subject_id để đánh giá GroupKFold.")

    gkf = GroupKFold(n_splits=n_splits)
    oof_proba = np.zeros(len(y), dtype=float)

    for train_idx, val_idx in gkf.split(X, y, groups=groups):
        clf = RandomForestClassifier(
            n_estimators=n_estimators,
            random_state=seed,
            class_weight="balanced",
            n_jobs=-1,
        )
        clf.fit(X[train_idx], y[train_idx])
        oof_proba[val_idx] = clf.predict_proba(X[val_idx])[:, 1]

    return oof_proba


def compute_event_metrics(
    meta_df: pd.DataFrame,
    y_proba: np.ndarray,
    threshold: float = 0.5,
    event_types: Iterable[str] = DEFAULT_EVENTS,
) -> pd.DataFrame:
    """Tính các chỉ số phân tích cho từng loại sự kiện."""
    df = meta_df.copy()
    df["y_proba"] = y_proba
    df["y_pred"] = (y_proba >= threshold).astype(int)

    rows: list[dict] = []
    for ev in event_types:
        sub = df[df["event_type"] == ev]
        n_windows = len(sub)
        if n_windows == 0:
            rows.append(
                {
                    "event_type": ev,
                    "n_windows": 0,
                    "n_events": 0,
                    "window_recall": np.nan,
                    "event_detection_rate": np.nan,
                    "mean_proba": np.nan,
                    "mean_ear": np.nan,
                    "mean_mar": np.nan,
                    "mean_perclos": np.nan,
                }
            )
            continue

        window_recall = float(sub["y_pred"].mean())
        valid_events = sub[sub["event_id"] >= 0]
        if len(valid_events) > 0:
            detected_per_event = valid_events.groupby("event_id")["y_pred"].max()
            n_events = int(len(detected_per_event))
            event_det_rate = float(detected_per_event.mean())
        else:
            n_events = 0
            event_det_rate = np.nan

        rows.append(
            {
                "event_type": ev,
                "n_windows": n_windows,
                "n_events": n_events,
                "window_recall": window_recall,
                "event_detection_rate": event_det_rate,
                "mean_proba": float(sub["y_proba"].mean()),
                "mean_ear": float(sub["ear_mean"].mean()),
                "mean_mar": float(sub["mar_mean"].mean()),
                "mean_perclos": float(sub["perclos"].mean()),
            }
        )

    return pd.DataFrame(rows)


def plot_event_analysis(summary_df: pd.DataFrame, output_path: str | Path) -> None:
    """Vẽ biểu đồ cột so sánh Window Recall và Event Detection Rate theo loại sự kiện."""
    plot_df = summary_df.dropna(subset=["window_recall"]).copy()
    if plot_df.empty:
        return

    x = np.arange(len(plot_df))
    width = 0.35

    fig, ax = plt.subplots(figsize=(8.5, 5.2))
    bars1 = ax.bar(
        x - width / 2,
        plot_df["window_recall"] * 100,
        width,
        label="Window-level Recall (%)",
        color="#2563eb",
    )
    bars2 = ax.bar(
        x + width / 2,
        plot_df["event_detection_rate"].fillna(0) * 100,
        width,
        label="Event-level Detection Rate (%)",
        color="#10b981",
    )

    ax.set_ylabel("Tỷ lệ phát hiện (%)")
    ax.set_title("Hiệu năng phát hiện buồn ngủ theo loại sự kiện (GroupKFold OOF)")
    ax.set_xticks(x)
    ax.set_xticklabels(
        [
            f"{row.event_type}\n(n_win={int(row.n_windows)}, n_ev={int(row.n_events)})"
            for row in plot_df.itertuples(index=False)
        ]
    )
    ax.set_ylim(0, 122)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.legend(loc="upper center", ncol=2, frameon=True)

    for bars in (bars1, bars2):
        for bar in bars:
            h = bar.get_height()
            ax.annotate(
                f"{h:.1f}%",
                xy=(bar.get_x() + bar.get_width() / 2, h),
                xytext=(0, 4),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=9.5,
                fontweight="bold",
            )

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Phân tích hiệu năng theo loại sự kiện.")
    parser.add_argument("--features", default="data/features/train_features.csv")
    parser.add_argument("--annotations", default="data/annotations/annotations_train.csv")
    parser.add_argument("--out-fig", default="docs/figures/event_analysis.png")
    parser.add_argument("--window-size", type=int, default=30)
    parser.add_argument("--stride", type=int, default=10)
    parser.add_argument("--ear-threshold", type=float, default=0.2)
    parser.add_argument("--threshold", type=float, default=0.5)
    parser.add_argument("--fps", type=float, default=30.0)
    parser.add_argument("--video-col", default=None)
    parser.add_argument("--event-col", default=None)
    parser.add_argument("--start-col", default=None)
    parser.add_argument("--end-col", default=None)
    args = parser.parse_args()

    df = load_features_csv(args.features)
    ann = load_annotations_csv(
        args.annotations,
        video_col=args.video_col,
        event_col=args.event_col,
        start_col=args.start_col,
        end_col=args.end_col,
        fps=args.fps,
    )

    df_events = assign_frame_events(df, ann)
    X, y, groups, meta_df = build_event_windows(
        df_events,
        window_size=args.window_size,
        stride=args.stride,
        ear_threshold=args.ear_threshold,
    )

    oof_proba = get_oof_probabilities(X, y, groups)

    found_events = list(DEFAULT_EVENTS)
    for ev in sorted(ann["event_type"].unique()):
        if ev not in found_events:
            found_events.append(ev)

    summary = compute_event_metrics(
        meta_df,
        oof_proba,
        threshold=args.threshold,
        event_types=found_events,
    )

    print("\n=== PHÂN TÍCH THEO LOẠI SỰ KIỆN (OOF GroupKFold) ===")
    print(summary.to_string(index=False, float_format=lambda v: f"{v:.3f}"))

    plot_event_analysis(summary, args.out_fig)
    print(f"\nĐã lưu biểu đồ tại: {args.out_fig}")


if __name__ == "__main__":
    main()