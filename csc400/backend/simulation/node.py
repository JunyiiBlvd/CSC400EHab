"""
This module defines the VirtualNode, which wraps a thermal model, airflow model, and humidity model 
to simulate a single compute node.
"""
import random
from datetime import datetime, timezone
from typing import Optional

from .thermal_model import ThermalModel
from .airflow import AirflowModel
from .humidity import HumidityModel


class VirtualNode:
    """
    Represents a simulated node with its own thermal model, airflow model, humidity model, 
    and CPU load generation.
    """

    def __init__(
        self,
        node_id: str,
        thermal_model: ThermalModel,
        airflow_model: AirflowModel,
        humidity_model: HumidityModel,
        random_seed: Optional[int] = None,
    ):
        """
        Initializes the VirtualNode.

        Args:
            node_id (str): A unique identifier for the node.
            thermal_model (ThermalModel): The thermal model instance for this node.
            airflow_model (AirflowModel): The airflow model instance for this node.
            humidity_model (HumidityModel): The humidity model instance for this node.
            random_seed (Optional[int]): An optional seed for the random number
                                         generator to ensure deterministic runs.
        """
        self.node_id = node_id
        self.thermal_model = thermal_model
        self.airflow_model = airflow_model
        self.humidity_model = humidity_model
        if random_seed is not None:
            self.rng = random.Random(random_seed)
        else:
            self.rng = random.Random()

    def _generate_cpu_load(self) -> float:
        """
        Generates a semi-random CPU load for the current time step.

        The load has a baseline and includes random noise, clamped between 0 and 1.

        Returns:
            float: The generated CPU load.
        """
        baseline_load = 0.5
        noise = self.rng.uniform(-0.05, 0.05)
        cpu_load = baseline_load + noise
        return max(0.0, min(1.0, cpu_load))

    def step(self) -> dict:
        """
        Advances the node's simulation by one step and returns its telemetry.

        Returns:
            dict: A dictionary containing the node's telemetry data for the step.
        """
        cpu_load = self._generate_cpu_load()
        
        # Step the airflow model and calculate the ratio for the thermal model
        current_airflow = self.airflow_model.step()
        airflow_ratio = (
            current_airflow / self.airflow_model.nominal_flow 
            if self.airflow_model.nominal_flow > 0 else 0.0
        )
        
        # Step the humidity model
        current_humidity = self.humidity_model.step()
        
        # Pass the airflow ratio to the thermal model
        temperature = self.thermal_model.step(cpu_load, airflow_ratio=airflow_ratio)

        telemetry = {
            "node_id": self.node_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "temperature": temperature,
            "humidity": current_humidity,
            "cpu_load": cpu_load,
            "airflow": current_airflow,
        }
        return telemetry
