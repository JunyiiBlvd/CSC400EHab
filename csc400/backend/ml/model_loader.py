import joblib
import os
from typing import List, Dict, Any


class ModelLoader:
    """Handles runtime loading and inference for the anomaly detection model."""

    def __init__(
        self,
        model_path: str | None = None,
        scaler_path: str | None = None,
    ):
        # Paths relative to project root
        self.model_path = model_path or "models/model_v2_hybrid_real.pkl"
        self.scaler_path = scaler_path or "models/scaler_v2.pkl"

        if not os.path.exists(self.model_path):
            raise FileNotFoundError(
                f"Model file not found at {self.model_path}."
            )
        
        if not os.path.exists(self.scaler_path):
            raise FileNotFoundError(
                f"Scaler file not found at {self.scaler_path}. Identity fallback disabled."
            )

        try:
            self.model = joblib.load(self.model_path)
            self.scaler = joblib.load(self.scaler_path)

            print(f"[ModelLoader] Loaded model: {self.model_path}")
            print(f"[ModelLoader] Loaded scaler: {self.scaler_path}")
            
            # IsolationForest offset_ is the decision threshold
            if hasattr(self.model, "offset_"):
                print(f"[ModelLoader] Decision threshold: {self.model.offset_:.4f}")
            else:
                # Fallback if for some reason it's not present
                print("[ModelLoader] Decision threshold: unknown")

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
