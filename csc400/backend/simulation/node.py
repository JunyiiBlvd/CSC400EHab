"""
This module defines the VirtualNode, which wraps a thermal model to simulate
a single compute node.
"""
import random
from datetime import datetime, timezone
from typing import Optional

from .thermal import ThermalModel


class VirtualNode:
    """
    Represents a simulated node with its own thermal model and CPU load generation.
    """

    def __init__(
        self,
        node_id: str,
        thermal_model: ThermalModel,
        random_seed: Optional[int] = None,
    ):
        """
        Initializes the VirtualNode.

        Args:
            node_id (str): A unique identifier for the node.
            thermal_model (ThermalModel): The thermal model instance for this node.
            random_seed (Optional[int]): An optional seed for the random number
                                         generator to ensure deterministic runs.
        """
        self.node_id = node_id
        self.thermal_model = thermal_model
        if random_seed is not None:
            random.seed(random_seed)

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
        Advances the node's simulation by one step and returns its telemetry.

        Returns:
            dict: A dictionary containing the node's telemetry data for the step.
        """
        cpu_load = self._generate_cpu_load()
        temperature = self.thermal_model.step(cpu_load)

        telemetry = {
            "node_id": self.node_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "temperature": temperature,
            "cpu_load": cpu_load,
        }
        return telemetry
