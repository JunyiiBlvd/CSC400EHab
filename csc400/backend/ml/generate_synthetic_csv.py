
import os
import pandas as pd
from backend.simulation.thermal import ThermalModel
from backend.simulation.airflow import AirflowModel
from backend.simulation.humidity import HumidityModel
from backend.simulation.environment import EnvironmentalModel
from backend.simulation.node import VirtualNode

def generate_synthetic_data(output_path="data/synthetic/normal_telemetry.csv", duration_steps=10000):
    """Generates synthetic normal telemetry data."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    thermal_model = ThermalModel(50.0, 1005.0, 500.0, 300.0, 21.0, 20.0)
    airflow_model = AirflowModel(nominal_flow=2.5)
    humidity_model = HumidityModel(initial_humidity=45.0, drift=0.01, noise_amplitude=0.2, random_seed=42)
    
    env_model = EnvironmentalModel(thermal_model, airflow_model, humidity_model)
    # Note: VirtualNode.step() currently puts the return of its thermal_model.step() into "temperature"
    # If we pass EnvironmentalModel, it returns a dict, creating nested structures.
    node = VirtualNode("node-1", env_model, random_seed=42)
    
    telemetry_list = []
    print(f"Generating {duration_steps} steps of synthetic telemetry...")
    for _ in range(duration_steps):
        raw_telemetry = node.step()
        
        # Flatten the nested dictionary if it exists
        if isinstance(raw_telemetry.get('temperature'), dict):
            env_data = raw_telemetry.pop('temperature')
            raw_telemetry.update(env_data)
            
        telemetry_list.append(raw_telemetry)
        
    df = pd.DataFrame(telemetry_list)
    df.to_csv(output_path, index=False)
    print(f"Saved synthetic telemetry to {output_path}")

if __name__ == "__main__":
    generate_synthetic_data()
