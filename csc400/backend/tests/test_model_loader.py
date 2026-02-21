
import unittest
import os
import numpy as np
from backend.ml.model_loader import AnomalyModel

class TestModelLoader(unittest.TestCase):
    """
    Unit tests for the AnomalyModel class.
    """

    @classmethod
    def setUpClass(cls):
        """
        Verify that the model file exists before running tests.
        """
        cls.model_path = "backend/ml/isolation_forest.pkl"
        if not os.path.exists(cls.model_path):
            raise unittest.SkipTest(f"Model file {cls.model_path} not found. Run train_model.py.")
        
        cls.model = AnomalyModel(cls.model_path)

    def test_predict_output_structure(self):
        """
        Check if predict() returns the correct dictionary structure.
        """
        # 12-dimensional dummy feature vector (approximate normal baseline)
        dummy_vector = [21.0, 0.1, 0.0] * 4  # temp, hum, air, cpu (mean, var, roc)
        
        result = self.model.predict(dummy_vector)
        
        self.assertIn("score", result)
        self.assertIn("is_anomaly", result)
        self.assertIsInstance(result["score"], float)
        self.assertIsInstance(result["is_anomaly"], bool)

    def test_predict_consistency(self):
        """
        Ensure the prediction is consistent for the same input.
        """
        dummy_vector = [0.5] * 12
        
        result1 = self.model.predict(dummy_vector)
        result2 = self.model.predict(dummy_vector)
        
        self.assertEqual(result1["score"], result2["score"])
        self.assertEqual(result1["is_anomaly"], result2["is_anomaly"])

    def test_anomaly_detection(self):
        """
        Verify that an obvious anomaly (extreme values) is detected.
        """
        # Extreme anomaly values (extremely high temperature mean and variance)
        extreme_vector = [1000.0, 500.0, 100.0] + [0.0] * 9
        
        result = self.model.predict(extreme_vector)
        self.assertTrue(result["is_anomaly"])

if __name__ == "__main__":
    unittest.main()
