
import numpy as np
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from backend.simulation.thermal_model import ThermalModel
from backend.simulation.node import VirtualNode
from backend.ml.feature_extraction import SlidingWindowFeatureExtractor

def simulate():
    # Setup models (same parameters as in api.py)
    thermal = ThermalModel(
        air_mass=50.0,
        heat_capacity=1005.0,
        heat_coefficient=500.0,
        cooling_coefficient=300.0,
        initial_temperature=21.0,
        ambient_temperature=20.0,
    )
    
    node = VirtualNode(
        node_id="test-node",
        thermal_model=thermal,
        random_seed=42
    )
    
    extractor = SlidingWindowFeatureExtractor(window_size=10)
    
    # Fill window with normal data
    print("Normalizing...")
    for _ in range(50):
        t = node.step()
        t['humidity'] = 45.0
        t['airflow'] = 1.0
        extractor.add_point(t)
    
    print(f"Start: Temp={t['temperature']:.3f}, CPU={t['cpu_load']:.3f}")
    
    # Inject Thermal Spike (cpu_load = 1.0 for 30 steps)
    node.inject_thermal_spike(duration_seconds=30)
    
    print(f"{'Step':>4} | {'Temp':>7} | {'Temp_Mean':>9} | {'Temp_Var':>8} | {'Temp_ROC':>8} | {'CPU_Mean':>8}")
    print("-" * 65)
    
    for i in range(1, 31):
        t = node.step()
        t['humidity'] = 45.0
        t['airflow'] = 1.0
        extractor.add_point(t)
        
        if i in [1, 5, 10, 20, 30]:
            f = extractor.extract_features()
            # features: [temp_mean, temp_var, temp_roc, hum_mean, hum_var, hum_roc, cpu_mean, cpu_var, cpu_roc]
            print(f"{i:4} | {t['temperature']:7.3f} | {f[0]:9.4f} | {f[1]:8.4f} | {f[2]:8.4f} | {f[6]:8.4f}")

if __name__ == "__main__":
    simulate()
