import pytest
from sklearn.datasets import make_classification

from ai.evaluate import evaluate_model
from ai.predict import DrowsinessPredictor
from ai.train import save_bundle, train_model

FEATURE_NAMES = [f"f{i}" for i in range(6)]


def _make_data():
    X, y = make_classification(
        n_samples=200, n_features=6, n_informative=4, random_state=0
    )
    return X, y


def _train_and_save(tmp_path):
    X, y = _make_data()
    model = train_model(X, y, {"n_estimators": 20})
    path = save_bundle(model, FEATURE_NAMES, window_size=30, threshold=0.5,
                       path=tmp_path / "m.joblib")
    return X, path


def test_predict_returns_valid_types(tmp_path):
    X, path = _train_and_save(tmp_path)
    predictor = DrowsinessPredictor(path)
    label, proba = predictor.predict_features(X[0])
    assert label in (0, 1)
    assert 0.0 <= proba <= 1.0


def test_reload_gives_same_prediction(tmp_path):
    X, path = _train_and_save(tmp_path)
    p1 = DrowsinessPredictor(path)
    p2 = DrowsinessPredictor(path)
    assert p1.predict_features(X[5]) == p2.predict_features(X[5])


def test_wrong_feature_count_raises(tmp_path):
    _, path = _train_and_save(tmp_path)
    predictor = DrowsinessPredictor(path)
    with pytest.raises(ValueError):
        predictor.predict_features([0.1, 0.2])


def test_evaluate_returns_expected_keys():
    X, y = _make_data()
    model = train_model(X, y, {"n_estimators": 10})
    metrics = evaluate_model(model, X, y)
    for key in ("accuracy", "precision", "recall", "f1", "confusion_matrix"):
        assert key in metrics