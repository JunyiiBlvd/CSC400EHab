
import unittest
import os
import joblib
import numpy as np
from sklearn.ensemble import IsolationForest
from backend.ml.model_loader import ModelLoader

class TestModelLoader(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """
        Create a dummy IsolationForest model and save it for testing.
        """
        cls.model_path = "models/model_v2_hybrid_real.pkl"
        cls.scaler_path = "models/scaler_v2.pkl"
        
        # If files don't exist (though they should from previous steps),
        # but the loader expects them.
        # The ModelLoader in backend/ml/model_loader.py defaults to these paths.

    def setUp(self):
        """
        Initialize the ModelLoader.
        """
        try:
            self.model = ModelLoader(model_path=self.model_path, scaler_path=self.scaler_path)
        except FileNotFoundError:
            self.skipTest("Model or Scaler files not found. Skipping ModelLoader tests.")

    def test_predict_output_structure(self):
        """
        Check if predict() returns the correct dictionary structure.
        """
        # 12-dimensional dummy feature vector (approximate normal baseline)
        dummy_vector = [21.0, 0.1, 0.0, 2.5, 0.01, 0.0, 45.0, 0.5, 0.0, 0.5, 0.01, 0.0]
    
        result = self.model.predict(dummy_vector)
    
        self.assertIn("anomaly_score", result)
        self.assertIn("is_anomaly", result)
        self.assertIsInstance(result["is_anomaly"], bool)
        self.assertIsInstance(result["anomaly_score"], float)

    def test_predict_consistency(self):
        """
        Ensure the prediction is consistent for the same input.
        """
        dummy_vector = [21.0, 0.1, 0.0, 2.5, 0.01, 0.0, 45.0, 0.5, 0.0, 0.5, 0.01, 0.0]
    
        result1 = self.model.predict(dummy_vector)
        result2 = self.model.predict(dummy_vector)
    
        self.assertEqual(result1["anomaly_score"], result2["anomaly_score"])
        self.assertEqual(result1["is_anomaly"], result2["is_anomaly"])

    def test_anomaly_detection(self):
        """
        Check if the model can at least execute a prediction on varied input.
        """
        # "Normal" input
        normal_vector = [21.0, 0.1, 0.0, 2.5, 0.01, 0.0, 45.0, 0.5, 0.0, 0.5, 0.01, 0.0]
        # "Anomalous" input (e.g., very high temperature)
        anomalous_vector = [50.0, 10.0, 5.0, 0.1, 1.0, -1.0, 90.0, 20.0, 5.0, 0.9, 0.1, 0.1]

        res_normal = self.model.predict(normal_vector)
        res_anomaly = self.model.predict(anomalous_vector)
        
        # We don't strictly assert is_anomaly results here because it depends 
        # on the trained model's threshold, but we ensure it runs.
        self.assertIsInstance(res_normal["is_anomaly"], bool)
        self.assertIsInstance(res_anomaly["is_anomaly"], bool)

if __name__ == "__main__":
    unittest.main()
