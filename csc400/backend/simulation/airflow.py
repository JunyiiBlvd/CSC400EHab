"""
This module defines the AirflowModel, simulating airflow within a controlled environment.
"""

class AirflowModel:
    """
    Simulates airflow dynamics within an environment, accounting for nominal flow
    and potential obstructions.
    """
    def __init__(self, nominal_flow: float, obstruction_ratio: float = 0.0):
        """
        Initializes the AirflowModel.

        Args:
            nominal_flow (float): The maximum airflow when there is no obstruction.
            obstruction_ratio (float, optional): The ratio of obstruction,
                                                 clamped between 0.0 and 1.0.
                                                 Defaults to 0.0 (no obstruction).
        """
        self.nominal_flow = nominal_flow
        self.current_flow = nominal_flow * (1 - self._clamp_obstruction(obstruction_ratio))
        self.obstruction_ratio = self._clamp_obstruction(obstruction_ratio)

    def _clamp_obstruction(self, ratio: float) -> float:
        """Clamps the obstruction ratio between 0.0 and 1.0."""
        return max(0.0, min(1.0, ratio))

    def step(self) -> float:
        """
        Updates and returns the current airflow based on nominal flow and obstruction.

        Returns:
            float: The current airflow.
        """
        self.current_flow = self.nominal_flow * (1 - self.obstruction_ratio)
        return self.current_flow

    def set_obstruction(self, ratio: float):
        """
        Sets the obstruction ratio, clamping it between 0.0 and 1.0.

        Args:
            ratio (float): The new obstruction ratio to set.
        """
        self.obstruction_ratio = self._clamp_obstruction(ratio)

    def simulate_fan_failure(self):
        """
        Simulates a complete fan failure by setting the obstruction ratio to 1.0,
        resulting in zero airflow.
        """
        self.set_obstruction(1.0)

    def reset(self):
        """
        Resets the airflow model to its initial state (no obstruction).
        """
        self.set_obstruction(0.0)
