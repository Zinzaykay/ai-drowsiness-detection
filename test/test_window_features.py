import numpy as np
import pandas as pd
import pytest

from ai.dataset import (generate_synthetic_data, split_by_subject,
                        load_frame_csv, FEATURE_COLUMNS)
from ai.features import build_window_features, make_windows, get_feature_names


def test_feature_vector_size():
    window = np.random.rand(30, len(FEATURE_COLUMNS))
    vec = build_window_features(window)
    assert vec.shape == (len(get_feature_names()),)


def test_split_by_subject_no_overlap():
    df = generate_synthetic_data(n_subjects=10, frames_per_video=100, seed=1)
    train, test = split_by_subject(df, test_size=0.3, seed=1)
    assert set(train["subject_id"]) & set(test["subject_id"]) == set()
    assert len(train) > 0 and len(test) > 0


def test_windows_do_not_cross_videos():
    df = generate_synthetic_data(n_subjects=3, frames_per_video=50, seed=2)
    X, y, groups = make_windows(df, window_size=20, stride=10)
    # mỗi video 50 khung -> (50-20)//10+1 = 4 cửa sổ; 3 người x 2 video = 6 video
    assert len(X) == 6 * 4
    assert X.shape[1] == len(get_feature_names())
    assert len(y) == len(groups) == len(X)


def test_synthetic_is_reproducible():
    a = generate_synthetic_data(n_subjects=3, frames_per_video=40, seed=7)
    b = generate_synthetic_data(n_subjects=3, frames_per_video=40, seed=7)
    pd.testing.assert_frame_equal(a, b)


def test_load_frame_csv_missing_column(tmp_path):
    df = generate_synthetic_data(n_subjects=2, frames_per_video=20, seed=3)
    bad = df.drop(columns=["ear"])
    path = tmp_path / "bad.csv"
    bad.to_csv(path, index=False)
    with pytest.raises(ValueError):
        load_frame_csv(str(path))


def test_load_frame_csv_bad_label(tmp_path):
    df = generate_synthetic_data(n_subjects=2, frames_per_video=20, seed=3)
    df.loc[0, "label"] = 2
    path = tmp_path / "bad_label.csv"
    df.to_csv(path, index=False)
    with pytest.raises(ValueError):
        load_frame_csv(str(path))