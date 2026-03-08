
import sys
import os
import numpy as np

# Add project root to path
sys.path.append(os.getcwd())

from backend.simulation.thermal_model import ThermalModel
from backend.simulation.airflow import AirflowModel
from backend.simulation.humidity import HumidityModel
from backend.simulation.node import VirtualNode

def verify_physically_coherent_coupling():
    # Setup models (consistent with runner.py defaults)
    thermal = ThermalModel(50.0, 1005.0, 500.0, 300.0, 21.0, 20.0)
    airflow = AirflowModel(nominal_flow=2.5, random_seed=1042)
    humidity = HumidityModel(45.0, 0.0, 0.2, 2042, reference_temp=21.0)
    
    node = VirtualNode(
        node_id="test-node",
        thermal_model=thermal,
        airflow_model=airflow,
        humidity_model=humidity,
        random_seed=3042
    )
    
    # 1. Normal Operation Analysis
    print("--- 1. Normal Operation (1000 steps) ---")
    temps, airflows, loads, hums = [], [], [], []
    for _ in range(1000):
        t = node.step()
        temps.append(t['temperature'])
        airflows.append(t['airflow'])
        loads.append(t['cpu_load'])
        hums.append(t['humidity'])
    
    def corr(x, y):
        return np.corrcoef(x, y)[0, 1]

    print(f"Airflow / Temp Correlation: {corr(airflows, temps):.4f}")
    print(f"Airflow / CPU Correlation: {corr(airflows, loads):.4f}")
    print(f"Temp / Humidity Correlation: {corr(temps, hums):.4f}")
    
    # 2. HVAC Failure Scenario
    print("\n--- 2. HVAC Failure Scenario (Obstruction=1.0) ---")
    airflow.simulate_fan_failure()
    
    print(f"{'Step':>4} | {'Temp':>7} | {'Airflow':>8} | {'Humidity':>8}")
    print("-" * 40)
    
    for i in range(1, 41):
        t = node.step()
        if i % 5 == 0 or i == 1:
            print(f"{i:4} | {t['temperature']:7.3f} | {t['airflow']:8.3f} | {t['humidity']:8.3f}")

if __name__ == "__main__":
    verify_physically_coherent_coupling()
