import joblib
import numpy as np
import os
from typing import List, Dict, Any

class ModelLoader:
    """
    Handles runtime loading and inference for the anomaly detection model and scaler.
    """

    def __init__(self, 
                 model_path: str = "models/model_v2_hybrid_real.pkl", 
                 scaler_path: str = "models/scaler_v2.pkl"):
        """
        Initializes the ModelLoader by loading the serialized Isolation Forest and RobustScaler.

        Args:
            model_path (str): The path to the .pkl model file.
            scaler_path (str): The path to the .pkl scaler file.
        """
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found at {model_path}. Please run train_hybrid_model.py first.")
        if not os.path.exists(scaler_path):
            raise FileNotFoundError(f"Scaler file not found at {scaler_path}. Please run train_hybrid_model.py first.")
        
        try:
            self.model = joblib.load(model_path)
            self.scaler = joblib.load(scaler_path)
            
            print(f'[ModelLoader] Loaded model: {model_path}')
            print(f'[ModelLoader] Loaded scaler: {scaler_path}')
            print(f'[ModelLoader] Decision threshold: {self.model.offset_:.4f}')
            
        except Exception as e:
            raise RuntimeError(f"Failed to load model or scaler: {e}")

    def predict(self, feature_vector: List[float]) -> Dict[str, Any]:
        """
        Applies scaling and predicts if a given feature vector is an anomaly.

        Args:
            feature_vector (List[float]): A 12-dimensional feature vector.

        Returns:
            Dict[str, Any]: A dictionary containing the anomaly score and a boolean flag.
                - "anomaly_score": The anomaly score (higher means more normal).
                - "is_anomaly": True if detected as an anomaly, False otherwise.
        """
        # Apply scaler automatically
        scaled = self.scaler.transform([feature_vector])
        
        # decision_function returns the anomaly score
        score = self.model.decision_function(scaled)[0]
        
        # predict returns 1 for normal, -1 for anomaly
        is_anomaly = self.model.predict(scaled)[0] == -1
        
        return {
            'anomaly_score': float(score),
            'is_anomaly': bool(is_anomaly)
        }

# For backward compatibility if any other script uses AnomalyModel name
AnomalyModel = ModelLoader
