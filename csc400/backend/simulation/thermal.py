"""
This module contains the thermal model for a single node in the E-Habitat simulation.
"""

class ThermalModel:
    """
    Represents the thermal physics of a virtual node.

    This model calculates temperature changes based on CPU load, heat generation,
    and cooling.
    """

    def __init__(
        self,
        air_mass: float,
        heat_capacity: float,
        heat_coefficient: float,
        cooling_coefficient: float,
        initial_temperature: float,
        ambient_temperature: float,
    ):
        """
        Initializes the ThermalModel.

        Args:
            air_mass (float): The mass of air being heated, in kg.
            heat_capacity (float): The specific heat capacity of air, in J/(kg*C).
            heat_coefficient (float): The heat generation coefficient (k), linking
                                      CPU load to power, in Watts.
            cooling_coefficient (float): The cooling efficiency coefficient, in Watts/C.
            initial_temperature (float): The starting temperature of the node, in Celsius.
            ambient_temperature (float): The constant temperature of the surroundings,
                                         in Celsius.
        """
        self.air_mass = air_mass
        self.heat_capacity = heat_capacity
        self.heat_coefficient = heat_coefficient
        self.cooling_coefficient = cooling_coefficient
        self.temperature = initial_temperature
        self.ambient_temperature = ambient_temperature

    def step(self, cpu_load: float, dt: float = 1.0) -> float:
        """
        Advances the thermal simulation by one time step.

        The temperature change is calculated based on the following physics:
        
        P_heat = k * cpu_load
            - Heat generated is proportional to the CPU load.

        CoolingPower = cooling_coefficient * (current_temp - ambient_temp)
            - Cooling is proportional to the temperature difference between
              the node and the ambient environment (Newton's Law of Cooling).

        T_next = T_current + (P_heat - CoolingPower) / (air_mass * heat_capacity) * dt
            - The change in temperature is the net power (heat generated minus
              cooling power) divided by the thermal mass, scaled by the time step.

        Args:
            cpu_load (float): The current CPU load, as a fraction (0.0 to 1.0).
            dt (float): The duration of the time step in seconds.

        Returns:
            float: The updated temperature of the node in Celsius.
        """
        # Clamp cpu_load to be between 0 and 1
        clamped_cpu_load = max(0.0, min(1.0, cpu_load))

        p_heat = self.heat_coefficient * clamped_cpu_load
        cooling_power = self.cooling_coefficient * (self.temperature - self.ambient_temperature)

        thermal_mass = self.air_mass * self.heat_capacity
        
        # Avoid division by zero if thermal_mass is zero
        if thermal_mass == 0:
            return self.temperature

        temperature_change = (p_heat - cooling_power) / thermal_mass * dt
        self.temperature += temperature_change

        return self.temperature
