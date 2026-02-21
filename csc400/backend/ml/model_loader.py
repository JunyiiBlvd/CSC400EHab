
import joblib
import numpy as np
import os
from typing import List, Dict, Any

class AnomalyModel:
    """
    Handles runtime loading and inference for the anomaly detection model.
    """

    def __init__(self, model_path: str = "backend/ml/isolation_forest.pkl"):
        """
        Initializes the AnomalyModel by loading the serialized Isolation Forest.

        Args:
            model_path (str): The path to the .pkl model file.
        """
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found at {model_path}. Please run train_model.py first.")
        
        try:
            self.model = joblib.load(model_path)
        except Exception as e:
            raise RuntimeError(f"Failed to load model from {model_path}: {e}")

    def predict(self, feature_vector: List[float]) -> Dict[str, Any]:
        """
        Predicts if a given feature vector is an anomaly.

        Args:
            feature_vector (List[float]): A 12-dimensional feature vector.

        Returns:
            Dict[str, Any]: A dictionary containing the anomaly score and a boolean flag.
                - "score": The anomaly score (higher means more normal).
                - "is_anomaly": True if detected as an anomaly, False otherwise.
        """
        # Reshape for scikit-learn (expects 2D array: [n_samples, n_features])
        X = np.array(feature_vector).reshape(1, -1)
        
        # decision_function returns the anomaly score (offset by contamination)
        # Higher score = more normal; Lower score = more anomalous
        score = float(self.model.decision_function(X)[0])
        
        # predict returns 1 for normal, -1 for anomaly
        prediction = int(self.model.predict(X)[0])
        is_anomaly = (prediction == -1)
        
        return {
            "score": score,
            "is_anomaly": is_anomaly
        }
