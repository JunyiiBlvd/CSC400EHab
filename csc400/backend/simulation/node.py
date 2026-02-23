"""
This module defines the VirtualNode, which wraps an environmental model to simulate
a single compute node.
"""
import random
from datetime import datetime, timezone
from typing import Optional

from .environment import EnvironmentalModel
from backend.ml.feature_extraction import SlidingWindowFeatureExtractor
from backend.ml.model_loader import AnomalyModel


class VirtualNode:
    """
    Represents a simulated node with its own environmental model, CPU load generation,
    and integrated edge anomaly detection.
    """

    def __init__(
        self,
        node_id: str,
        environmental_model: EnvironmentalModel,
        random_seed: Optional[int] = None,
        model_path: str = "backend/ml/isolation_forest.pkl"
    ):
        """
        Initializes the VirtualNode.

        Args:
            node_id (str): A unique identifier for the node.
            environmental_model (EnvironmentalModel): The environmental model for this node.
            random_seed (Optional[int]): An optional seed for the random number
                                         generator to ensure deterministic runs.
            model_path (str): Path to the pre-trained anomaly detection model.
        """
        self.node_id = node_id
        self.environmental_model = environmental_model
        if random_seed is not None:
            # Note: This sets the seed for the global random module.
            # If the humidity model also uses its own seeded random instance,
            # this ensures the CPU load is also deterministic.
            random.seed(random_seed)
        
        # Integration of ML Components
        self.feature_extractor = SlidingWindowFeatureExtractor(window_size=10)
        try:
            self.anomaly_model = AnomalyModel(model_path)
        except (FileNotFoundError, RuntimeError) as e:
            # Fallback for cases where model is not yet trained
            print(f"Warning: Anomaly detection disabled for {node_id}. {e}")
            self.anomaly_model = None

        # Anomaly Injection State
        self.spike_remaining_steps = 0
        self.spike_magnitude = 0.0

    def inject_thermal_spike(self, duration_seconds: int, magnitude: float):
        """
        Manually injects a thermal spike anomaly into the simulation.

        Args:
            duration_seconds (int): How many steps the spike should last.
            magnitude (float): The temperature increase to apply at each step.
        """
        self.spike_remaining_steps = duration_seconds
        self.spike_magnitude = magnitude

    def _generate_cpu_load(self) -> float:
        """
        Generates a semi-random CPU load for the current time step.

        The load has a baseline and includes random noise, clamped between 0 and 1.

        Returns:
            float: The generated CPU load.
        """
        baseline_load = 0.5
        noise = random.uniform(-0.05, 0.05)
        cpu_load = baseline_load + noise
        return max(0.0, min(1.0, cpu_load))

    def step(self) -> dict:
        """
        Advances the node's simulation by one step and returns its telemetry,
        including real-time anomaly detection results.

        Returns:
            dict: A dictionary containing the node's telemetry data and anomaly status.
        """
        cpu_load = self._generate_cpu_load()
        env_state = self.environmental_model.step(cpu_load)

        # Apply Thermal Spike if active
        current_temp = env_state["temperature"]
        is_spike_active = False
        if self.spike_remaining_steps > 0:
            current_temp += self.spike_magnitude
            self.spike_remaining_steps -= 1
            is_spike_active = True

        telemetry = {
            "node_id": self.node_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "temperature": current_temp,
            "humidity": env_state["humidity"],
            "airflow": env_state["airflow"],
            "cpu_load": cpu_load,
            "injected_anomaly": is_spike_active
        }

        # Real-time Anomaly Detection Logic
        anomaly_score = None
        is_anomaly = False

        if self.anomaly_model:
            # 1. Add current telemetry to sliding window
            self.feature_extractor.add_point(telemetry)

            # 2. Check if window is ready for inference
            if self.feature_extractor.is_window_ready():
                features = self.feature_extractor.extract_features()
                result = self.anomaly_model.predict(features)
                anomaly_score = result["score"]
                is_anomaly = result["is_anomaly"]

        # Attach anomaly results to telemetry
        telemetry["anomaly_score"] = anomaly_score
        telemetry["is_anomaly"] = is_anomaly

        return telemetry
