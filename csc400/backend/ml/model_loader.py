import joblib
import os
from typing import List, Dict, Any


class IdentityScaler:
    def transform(self, rows):
        return rows


class ModelLoader:
    """Handles runtime loading and inference for the anomaly detection model."""

    def __init__(
        self,
        model_path: str | None = None,
        scaler_path: str | None = None,
    ):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.model_path = model_path or os.path.join(base_dir, "isolation_forest.pkl")
        self.scaler_path = scaler_path or os.path.join(base_dir, "scaler_v2.pkl")

        if not os.path.exists(self.model_path):
            raise FileNotFoundError(
                f"Model file not found at {self.model_path}."
            )

        try:
            self.model = joblib.load(self.model_path)
            if os.path.exists(self.scaler_path):
                self.scaler = joblib.load(self.scaler_path)
            else:
                self.scaler = IdentityScaler()

            print(f"[ModelLoader] Loaded model: {self.model_path}")
            if os.path.exists(self.scaler_path):
                print(f"[ModelLoader] Loaded scaler: {self.scaler_path}")
            else:
                print("[ModelLoader] No scaler found, using identity transform")
        except Exception as e:
            raise RuntimeError(f"Failed to load model or scaler: {e}")

    def predict(self, feature_vector: List[float]) -> Dict[str, Any]:
        scaled = self.scaler.transform([feature_vector])
        score = self.model.decision_function(scaled)[0]
        is_anomaly = self.model.predict(scaled)[0] == -1
        return {
            "anomaly_score": float(score),
            "is_anomaly": bool(is_anomaly),
        }


AnomalyModel = ModelLoader
