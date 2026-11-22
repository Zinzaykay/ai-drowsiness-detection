import numpy as np
import pytest
from sklearn.ensemble import RandomForestClassifier

from ai.baseline import RuleBaseline
from ai.cross_validate import make_splits, run_group_cv
from ai.tune_threshold import choose_threshold

NAMES = ["ear_mean", "perclos", "mar_max"]


def _data(n_subjects=6, per=40, seed=0):
    rng = np.random.default_rng(seed)
    X, y, g = [], [], []
    for s in range(n_subjects):
        yy = np.r_[np.zeros(per // 2), np.ones(per // 2)].astype(int)
        perclos = np.where(yy == 1, rng.uniform(0.4, 1.0, per), rng.uniform(0.0, 0.3, per))
        X.append(np.column_stack([rng.random(per), perclos, rng.random(per) * 0.1]))
        y.append(yy)
        g += [f"S{s}"] * per
    return np.vstack(X), np.concatenate(y), np.array(g)


def test_baseline_predicts_valid_labels():
    X, y, _ = _data()
    base = RuleBaseline(NAMES, use=["perclos"]).fit(X, y)
    pred = base.predict(X)
    assert set(np.unique(pred)) <= {0, 1}
    proba = base.predict_proba(X)
    assert proba.shape == (len(X), 2)
    assert np.all((proba >= 0) & (proba <= 1))


def test_baseline_unknown_feature_raises():
    with pytest.raises(ValueError):
        RuleBaseline(NAMES, use=["khong_co"])


@pytest.mark.parametrize("mode", ["loso", "kfold"])
def test_group_cv_no_subject_overlap(mode):
    X, y, g = _data()
    n_folds = 0
    for train_idx, test_idx in make_splits(X, y, g, mode=mode, n_splits=3):
        assert set(g[train_idx]).isdisjoint(set(g[test_idx]))
        n_folds += 1
    assert n_folds >= 2


def test_run_group_cv_returns_valid_proba():
    X, y, g = _data()
    res = run_group_cv(X, y, g, lambda: RandomForestClassifier(n_estimators=10, random_state=0))
    assert len(res["proba"]) == len(y)
    assert np.all((res["proba"] >= 0) & (res["proba"] <= 1))
    assert len(res["per_group"]) == len(np.unique(g))


def test_choose_threshold_respects_min_recall():
    X, y, g = _data()
    res = run_group_cv(X, y, g, lambda: RandomForestClassifier(n_estimators=10, random_state=0))
    chosen = choose_threshold(y, res["proba"], min_recall=0.90)
    assert chosen["reached_min_recall"]
    assert chosen["recall"] >= 0.90
