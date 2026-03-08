import random
from typing import Optional

class HumidityModel:
    """
    A simple model for simulating humidity changes in an environment.
    """

    def __init__(self, initial_humidity: float, drift: float, noise_amplitude: float, random_seed: Optional[int] = None, reference_temp: float = 21.0):
        """
        Initializes the HumidityModel.

        Args:
            initial_humidity (float): The starting humidity level (0-100).
            drift (float): The constant rate of change in humidity per step.
            noise_amplitude (float): The maximum amplitude of the random noise.
            random_seed (Optional[int]): A seed for the random number generator for deterministic behavior.
            reference_temp (float): The baseline temperature for coupling (default 21.0).
        """
        self.initial_humidity = initial_humidity
        self.current_humidity = initial_humidity
        self.drift = drift
        self.noise_amplitude = noise_amplitude
        self.reference_temp = reference_temp
        self.random = None
        if random_seed is not None:
            self.random = random.Random(random_seed)

    def step(self, temperature: float = None) -> float:
        """
        Calculates the humidity for the next time step.

        The new humidity is calculated as:
        H(t+1) = H(t) + drift + reversion + coupling_drift + noise
        where:
        - drift = the constant rate of change per step
        - reversion = -0.05 * (current_humidity - initial_humidity)
        - coupling_drift = -0.3 * (temperature - reference_temp) * 0.01
        - noise = random value within [-noise_amplitude, noise_amplitude]
        """
        if self.random:
            noise = self.random.uniform(-self.noise_amplitude, self.noise_amplitude)
        else:
            noise = random.uniform(-self.noise_amplitude, self.noise_amplitude)

        coupling_drift = 0.0
        if temperature is not None:
            # Back to -0.3: each 1C rise = 0.3% RH drop, gradual not instant
            coupling_drift = -0.3 * (temperature - self.reference_temp) * 0.01

        # Mean-reversion to keep humidity near initial value (e.g., 45%)
        reversion = -0.05 * (self.current_humidity - self.initial_humidity)

        self.current_humidity += self.drift + reversion + coupling_drift + noise
        self.current_humidity = max(0.0, min(100.0, self.current_humidity))

        return self.current_humidity
