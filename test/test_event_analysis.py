import numpy as np
import pandas as pd
import pytest

from ai.analyze_events import (
    assign_frame_events,
    build_event_windows,
    compute_event_metrics,
    load_annotations_csv,
)


def _make_dummy_frames() -> pd.DataFrame:
    rows = []
    for vid_idx, vid in enumerate(["v1", "v2"]):
        for f in range(40):
            rows.append(
                {
                    "subject_id": f"s{vid_idx}",
                    "video_id": vid,
                    "frame_idx": f,
                    "ear": 0.12 if 10 <= f <= 25 and vid == "v1" else 0.30,
                    "mar": 0.70 if 10 <= f <= 25 and vid == "v2" else 0.25,
                    "label": 1 if 10 <= f <= 25 else 0,
                }
            )
    return pd.DataFrame(rows)


def test_load_annotations_csv_supports_frame_columns(tmp_path):
    csv_path = tmp_path / "ann.csv"
    pd.DataFrame(
        {
            "video_id": ["v1", "v2"],
            "event_type": ["Eye_Closed", "head_nod"],
            "start_frame": [10, 15],
            "end_frame": [25, 30],
        }
    ).to_csv(csv_path, index=False)

    ann = load_annotations_csv(csv_path)
    assert list(ann["event_type"]) == ["eye_closed", "head_nod"]
    assert list(ann["start_frame"]) == [10, 15]
    assert list(ann["end_frame"]) == [25, 30]


def test_assign_frame_events_maps_intervals():
    df = _make_dummy_frames()
    ann = pd.DataFrame(
        {
            "video_id": ["v1", "v2"],
            "event_type": ["eye_closed", "yawn"],
            "start_frame": [10, 10],
            "end_frame": [25, 25],
            "event_id": [0, 1],
        }
    )

    mapped = assign_frame_events(df, ann)
    v1_ev = mapped[(mapped["video_id"] == "v1") & (mapped["frame_idx"].between(10, 25))]
    v1_norm = mapped[(mapped["video_id"] == "v1") & (mapped["frame_idx"] < 10)]
    assert (v1_ev["event_type"] == "eye_closed").all()
    assert (v1_norm["event_type"] == "normal").all()


def test_build_event_windows_no_cross_video():
    df = _make_dummy_frames()
    ann = pd.DataFrame(
        {
            "video_id": ["v1", "v2"],
            "event_type": ["eye_closed", "yawn"],
            "start_frame": [10, 10],
            "end_frame": [25, 25],
            "event_id": [0, 1],
        }
    )
    mapped = assign_frame_events(df, ann)
    X, y, groups, meta = build_event_windows(mapped, window_size=20, stride=10)

    # Mỗi video 40 khung, W=20, S=10 => (40-20)//10 + 1 = 3 cửa sổ/video => tổng 6 cửa sổ
    assert len(X) == 6
    assert len(y) == 6
    assert len(groups) == 6
    assert len(meta) == 6
    assert set(meta["event_type"]).issuperset({"eye_closed", "yawn"})


def test_compute_event_metrics_values_and_missing_event():
    meta = pd.DataFrame(
        {
            "event_type": ["eye_closed", "eye_closed", "head_nod", "head_nod"],
            "event_id": [0, 0, 1, 2],
            "ear_mean": [0.15, 0.14, 0.29, 0.30],
            "mar_mean": [0.25, 0.24, 0.26, 0.27],
            "perclos": [0.80, 0.90, 0.05, 0.00],
        }
    )
    y_proba = np.array([0.85, 0.90, 0.60, 0.20])

    summary = compute_event_metrics(
        meta,
        y_proba,
        threshold=0.5,
        event_types=("eye_closed", "head_nod", "yawn"),
    ).set_index("event_type")

    assert summary.loc["eye_closed", "window_recall"] == pytest.approx(1.0)
    assert summary.loc["eye_closed", "event_detection_rate"] == pytest.approx(1.0)
    assert summary.loc["head_nod", "window_recall"] == pytest.approx(0.5)
    assert summary.loc["head_nod", "event_detection_rate"] == pytest.approx(0.5)
    assert summary.loc["yawn", "n_windows"] == 0
    assert np.isnan(summary.loc["yawn", "window_recall"])

def test_load_features_csv_accepts_video_name(tmp_path):
    from ai.analyze_events import load_features_csv

    csv_path = tmp_path / "features.csv"
    pd.DataFrame(
        {
            "subject_id": ["s1", "s1"],
            "video_name": ["v1.mp4", "v1.mp4"],
            "frame_idx": [0, 1],
            "ear": [0.30, 0.28],
            "mar": [0.10, 0.12],
            "label": [0, 0],
        }
    ).to_csv(csv_path, index=False)

    df = load_features_csv(csv_path)
    assert "video_id" in df.columns
    assert list(df["video_id"]) == ["v1.mp4", "v1.mp4"]