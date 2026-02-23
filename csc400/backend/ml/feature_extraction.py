
from collections import deque
import numpy as np

class SlidingWindowFeatureExtractor:
    """
    Extracts features from a sliding window of telemetry data.
    """

    def __init__(self, window_size: int = 10):
        """
        Initializes the feature extractor with a given window size.

        Args:
            window_size: The number of data points to include in the sliding window.
        """
        self.window_size = window_size
        self.window = deque(maxlen=window_size)
        self.variables = ['temperature', 'humidity', 'airflow', 'cpu_load']

    def add_point(self, data: dict):
        """
        Adds a new data point to the sliding window.

        Args:
            data: A dictionary representing a single telemetry reading.
        """
        self.window.append(data)

    def is_window_ready(self) -> bool:
        """
        Checks if the sliding window is full.

        Returns:
            True if the window is full, False otherwise.
        """
        return len(self.window) == self.window_size

    def extract_features(self) -> list[float]:
        """
        Calculates features from the current window of data.

        Returns:
            A list of floats representing the calculated features.
            The features are ordered as:
            [temp_mean, temp_var, temp_roc,
             hum_mean, hum_var, hum_roc,
             air_mean, air_var, air_roc,
             cpu_mean, cpu_var, cpu_roc]
        """
        if not self.is_window_ready():
            raise ValueError("Window is not ready for feature extraction.")

        features = []
        for var in self.variables:
            values = [point[var] for point in self.window]
            
            mean = np.mean(values)
            variance = np.var(values)
            rate_of_change = values[-1] - values[0]
            
            features.extend([mean, variance, rate_of_change])
            
        return features
