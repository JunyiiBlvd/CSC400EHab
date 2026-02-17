import random
from typing import Optional

class HumidityModel:
    """
    A simple model for simulating humidity changes in an environment.
    """

    def __init__(self, initial_humidity: float, drift: float, noise_amplitude: float, random_seed: Optional[int] = None):
        """
        Initializes the HumidityModel.

        Args:
            initial_humidity (float): The starting humidity level (0-100).
            drift (float): The constant rate of change in humidity per step.
            noise_amplitude (float): The maximum amplitude of the random noise.
            random_seed (Optional[int]): A seed for the random number generator for deterministic behavior.
        """
        self.current_humidity = initial_humidity
        self.drift = drift
        self.noise_amplitude = noise_amplitude
        self.random = None
        if random_seed is not None:
            self.random = random.Random(random_seed)

    def step(self) -> float:
        """
        Calculates the humidity for the next time step.

        The new humidity is calculated as:
        H(t+1) = H(t) + drift + noise
        where noise is a random value within [-noise_amplitude, noise_amplitude].
        The humidity is clamped between 0 and 100.

        Returns:
            float: The updated humidity level.
        """
        if self.random:
            noise = self.random.uniform(-self.noise_amplitude, self.noise_amplitude)
        else:
            noise = random.uniform(-self.noise_amplitude, self.noise_amplitude)

        self.current_humidity += self.drift + noise
        self.current_humidity = max(0.0, min(100.0, self.current_humidity))

        return self.current_humidity
