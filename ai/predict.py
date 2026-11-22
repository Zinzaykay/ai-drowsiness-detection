import warnings
import joblib
import numpy as np
import sklearn

from ai.features import build_window_features

class DrowsinessPredictor:
    """Nạp gói model và dự đoán cho một cửa sổ khung hình"""
    def __init__(self, model_path):
        bundle = joblib.load(model_path)
        self.model = bundle["model"]
        self.feature_names = bundle["feature_names"]
        self.window_size = bundle["window_size"]
        self.threshold = bundle["threshold"]
        self.labels = bundle["labels"]

        if bundle.get("sklearn_version") != sklearn.__version__:
            saved_version = bundle.get("sklearn_version")
            warnings.warn(
                f"Model lưu bằng sklearn {saved_version},"
                f"đang chạy {sklearn.__version__}. Kết quả có thể sai lệch."
            )
        if self.model.n_features_in_ != len(self.feature_names):
            raise ValueError("Gói model không nhất quán: số đặc trưng không khớp")

    def _to_vector(self, features):
        """Đưa đặc trưng về vector đúng thứ tự feature_names."""
        if isinstance(features, dict):
            missing = [n for n in self.feature_names if n not in features]
            if missing:
                raise ValueError(f"Thiếu đặc trưng: {missing}")
            features = [features[n] for n in self.feature_names]
        vec = np.asarray(features, dtype = float).ravel()
        if vec.shape[0] != len(self.feature_names):
            raise ValueError (
                f"Cần {len(self.feature_names)} đặc trưng, nhận được {vec.shape[0]}."
            )
        return vec.reshape(1, -1)
    
    def predict_features(self, features):
        """Dự đoán từ đặc trưng đã tính sẵn. Trả về (nhãn, xác suất DROWSY)."""
        x = self._to_vector(features)
        probs = self.model.predict_proba(x)[0]
        classes = list(self.model.classes_)
        # Tìm đúng cột của lớp 1 (DROWSY) theo model.classes_, không mặc định cột thứ hai
        proba = float(probs[classes.index(1)]) if 1 in classes else 0.0
        label = int(proba >= self.threshold)
        return label, proba

    def predict(self, window):
        """Dự đoán từ cửa sổ khung hình (gọi hàm đặc trưng của 1A)."""
        return self.predict_features(build_window_features(window))
    
