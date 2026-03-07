from backend.simulation.thermal_model import ThermalModel
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
        airflow = self.airflow_model.step()
        airflow_ratio = (
            airflow / self.airflow_model.nominal_flow 
            if self.airflow_model.nominal_flow > 0 else 0.0
        )
        
        temperature = self.thermal_model.step(cpu_load, airflow_ratio=airflow_ratio)
        humidity = self.humidity_model.step()

        return {
            "temperature": temperature,
            "airflow": airflow,
            "humidity": humidity,
        }
