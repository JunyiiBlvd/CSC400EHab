
import numpy as np
import os
from backend.simulation.thermal import ThermalModel
from backend.simulation.airflow import AirflowModel
from backend.simulation.humidity import HumidityModel
from backend.simulation.environment import EnvironmentalModel
from backend.simulation.node import VirtualNode
from backend.ml.feature_extraction import SlidingWindowFeatureExtractor

def generate_baseline(duration_steps=172800, seed=42, output_path="backend/ml/baseline_features.npy"):
    """
    Generates synthetic baseline data for normal operation.
    
    Args:
        duration_steps (int): Number of simulation steps (default 48h = 172800s).
        seed (int): Random seed for reproducibility.
        output_path (str): Path to save the resulting feature vectors.
    """
    # 1. Setup Models with deterministic seed
    thermal_model = ThermalModel(
        air_mass=50.0,
        heat_capacity=1005.0,
        heat_coefficient=500.0,
        cooling_coefficient=300.0,
        initial_temperature=21.0,
        ambient_temperature=20.0,
    )
    
    airflow_model = AirflowModel(
        nominal_flow=2.5
    )

    humidity_model = HumidityModel(
        initial_humidity=45.0,
        drift=0.01,
        noise_amplitude=0.2,
        random_seed=seed
    )

    environmental_model = EnvironmentalModel(
        thermal_model=thermal_model,
        airflow_model=airflow_model,
        humidity_model=humidity_model,
    )

    node = VirtualNode(
        node_id="baseline-node",
        environmental_model=environmental_model,
        random_seed=seed
    )

    # 2. Setup Feature Extractor
    extractor = SlidingWindowFeatureExtractor(window_size=10)
    baseline_features = []

    # 3. Run Simulation (No time.sleep for offline generation)
    print(f"Generating baseline data for {duration_steps} steps...")
    for i in range(duration_steps):
        telemetry = node.step()
        extractor.add_point(telemetry)
        
        if extractor.is_window_ready():
            features = extractor.extract_features()
            baseline_features.append(features)
        
        if (i + 1) % 10000 == 0:
            print(f"Progress: {i + 1}/{duration_steps} steps completed.")

    # 4. Save to Numpy File
    features_array = np.array(baseline_features)
    np.save(output_path, features_array)
    
    print(f"Baseline generation complete. Saved to {output_path}")
    print(f"Shape of feature matrix: {features_array.shape}")

if __name__ == "__main__":
    # Ensure we are in the project root or handle paths correctly
    # For this script, we assume it's run from the project root.
    generate_baseline()
