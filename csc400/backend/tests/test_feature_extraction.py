
import unittest
import numpy as np
from collections import deque

# Adjust the import path to match your project structure
from backend.ml.feature_extraction import SlidingWindowFeatureExtractor

class TestSlidingWindowFeatureExtractor(unittest.TestCase):

    def setUp(self):
        """Set up a feature extractor and some test data."""
        self.window_size = 5
        self.extractor = SlidingWindowFeatureExtractor(window_size=self.window_size)
        # Order in extractor: [temperature, airflow, humidity, cpu_load]
        self.test_data = [
            {"timestamp": "2024-01-01T00:00:00Z", "temperature": 20, "airflow": 100, "humidity": 50, "cpu_load": 30},
            {"timestamp": "2024-01-01T00:00:01Z", "temperature": 21, "airflow": 101, "humidity": 51, "cpu_load": 32},
            {"timestamp": "2024-01-01T00:00:02Z", "temperature": 22, "airflow": 102, "humidity": 52, "cpu_load": 34},
            {"timestamp": "2024-01-01T00:00:03Z", "temperature": 23, "airflow": 103, "humidity": 53, "cpu_load": 36},
            {"timestamp": "2024-01-01T00:00:04Z", "temperature": 24, "airflow": 104, "humidity": 54, "cpu_load": 38},
        ]

    def test_window_readiness(self):
        """Test that the window readiness is correctly reported."""
        self.assertFalse(self.extractor.is_window_ready())
        for i in range(self.window_size - 1):
            self.extractor.add_point(self.test_data[i])
            self.assertFalse(self.extractor.is_window_ready())
        
        self.extractor.add_point(self.test_data[self.window_size - 1])
        self.assertTrue(self.extractor.is_window_ready())

    def test_feature_extraction_length(self):
        """Test that the feature vector has the correct length."""
        for point in self.test_data:
            self.extractor.add_point(point)
        
        features = self.extractor.extract_features()
        # 4 variables * 3 features each = 12
        self.assertEqual(len(features), 12)

    def test_mean_calculation(self):
        """Test the correctness of the mean calculation.
        Order: [temp_mean, temp_var, temp_roc, air_mean, air_var, air_roc, hum_mean, ..., cpu_mean, ...]
        """
        for point in self.test_data:
            self.extractor.add_point(point)
        
        features = self.extractor.extract_features()
        
        # Expected means
        temp_mean = np.mean([20, 21, 22, 23, 24])
        air_mean = np.mean([100, 101, 102, 103, 104])
        hum_mean = np.mean([50, 51, 52, 53, 54])
        cpu_mean = np.mean([30, 32, 34, 36, 38])

        self.assertAlmostEqual(features[0], temp_mean) # temp
        self.assertAlmostEqual(features[3], air_mean) # air
        self.assertAlmostEqual(features[6], hum_mean) # hum
        self.assertAlmostEqual(features[9], cpu_mean) # cpu

    def test_variance_calculation(self):
        """Test the correctness of the variance calculation."""
        for point in self.test_data:
            self.extractor.add_point(point)
        
        features = self.extractor.extract_features()
        
        # Expected variances
        temp_var = np.var([20, 21, 22, 23, 24])
        air_var = np.var([100, 101, 102, 103, 104])
        hum_var = np.var([50, 51, 52, 53, 54])
        cpu_var = np.var([30, 32, 34, 36, 38])

        self.assertAlmostEqual(features[1], temp_var)
        self.assertAlmostEqual(features[4], air_var)
        self.assertAlmostEqual(features[7], hum_var)
        self.assertAlmostEqual(features[10], cpu_var)

    def test_rate_of_change_calculation(self):
        """Test the correctness of the rate-of-change calculation."""
        for point in self.test_data:
            self.extractor.add_point(point)
        
        features = self.extractor.extract_features()
        
        # Expected rates of change
        temp_roc = 24 - 20
        air_roc = 104 - 100
        hum_roc = 54 - 50
        cpu_roc = 38 - 30

        self.assertAlmostEqual(features[2], temp_roc)
        self.assertAlmostEqual(features[5], air_roc)
        self.assertAlmostEqual(features[8], hum_roc)
        self.assertAlmostEqual(features[11], cpu_roc)

    def test_sliding_window_behavior(self):
        """Test that the window correctly slides."""
        # Fill the window
        for point in self.test_data:
            self.extractor.add_point(point)
        
        # Add a new point to slide the window
        new_point = {"timestamp": "2024-01-01T00:00:05Z", "temperature": 25, "airflow": 105, "humidity": 55, "cpu_load": 40}
        self.extractor.add_point(new_point)

        # The window should now contain the last `window_size` points
        self.assertTrue(self.extractor.is_window_ready())
        
        # Check if the oldest point is gone
        self.assertNotEqual(self.extractor.window[0]['temperature'], self.test_data[0]['temperature'])
        self.assertEqual(self.extractor.window[0]['temperature'], self.test_data[1]['temperature'])
        self.assertEqual(self.extractor.window[-1]['temperature'], new_point['temperature'])

        # Verify features are calculated on the new window
        features = self.extractor.extract_features()
        new_temps = [21, 22, 23, 24, 25]
        self.assertAlmostEqual(features[0], np.mean(new_temps))
        self.assertAlmostEqual(features[1], np.var(new_temps))
        self.assertAlmostEqual(features[2], 25 - 21)

if __name__ == '__main__':
    unittest.main()
