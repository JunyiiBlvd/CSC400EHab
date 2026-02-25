from backend.simulation.thermal import ThermalModel
from backend.simulation.airflow import AirflowModel
from backend.simulation.humidity import HumidityModel

class EnvironmentalModel:
    """
    Composes thermal, airflow, and humidity models to represent the complete
    environmental state of a virtual node.
    """

    def __init__(self, thermal_model: ThermalModel, airflow_model: AirflowModel, humidity_model: HumidityModel):
        """
        Initializes the EnvironmentalModel.

        Args:
            thermal_model (ThermalModel): The thermal model instance.
            airflow_model (AirflowModel): The airflow model instance.
            humidity_model (HumidityModel): The humidity model instance.
        """
        self.thermal_model = thermal_model
        self.airflow_model = airflow_model
        self.humidity_model = humidity_model

    def step(self, cpu_load: float) -> dict:
        """
        Advances all composed models by one time step.

        Args:
            cpu_load (float): The current CPU load for the thermal model.

        Returns:
            dict: A dictionary containing the updated environmental state:
                  {"temperature": float, "airflow": float, "humidity": float}
        """
        temperature = self.thermal_model.step(cpu_load)
        airflow = self.airflow_model.step()
        humidity = self.humidity_model.step()

        return {
            "temperature": temperature,
            "airflow": airflow,
            "humidity": humidity,
        }
