
import pytest
import numpy as np
from backend.simulation.thermal_model import ThermalModel
from backend.simulation.airflow import AirflowModel
from backend.ml.model_loader import AnomalyModel

# --- 1. ThermalModel Test ---
def test_temperature_rises_with_cpu_load():
    model = ThermalModel(
        air_mass=50.0,
        heat_capacity=1005.0,
        heat_coefficient=500.0,
        cooling_coefficient=10.0, # Low cooling to see rise
        initial_temperature=21.0,
        ambient_temperature=20.0
    )
    
    # Step with 1.0 (100%) CPU load
    temp_after_load = model.step(cpu_load=1.0)
    
    assert temp_after_load > 21.0, f"Expected temp > 21.0, but got {temp_after_load}"

# --- 2. AirflowModel Test ---
def test_airflow_decreases_with_blockage():
    model = AirflowModel(nominal_flow=100.0)
    
    # Initial state: 0% obstruction
    initial_flow = model.step()
    assert initial_flow == 100.0
    
    # Set 50% obstruction
    model.set_obstruction(0.5)
    flow_with_blockage = model.step()
    
    assert flow_with_blockage == 50.0
    assert flow_with_blockage < initial_flow

# --- 3. Isolation Forest Anomaly Tests ---
# Note: We use the hybrid model (v2) and its associated scaler
# These use 9-dimensional vectors: [temp_mean, temp_var, temp_roc, hum_mean, hum_var, hum_roc, cpu_mean, cpu_var, cpu_roc]
HYBRID_MODEL_PATH = "models/model_v2_hybrid_real.pkl"
HYBRID_SCALER_PATH = "models/scaler_v2.pkl"

def test_isolation_forest_flags_high_temperature_anomaly():
    model = AnomalyModel(model_path=HYBRID_MODEL_PATH, scaler_path=HYBRID_SCALER_PATH)
    
    # Simulate a rapid thermal spike:
    # High mean (95), High variance (due to spike), High ROC (upward trend)
    anomaly_vector = [
        95.0, 10.0, 5.0,  # Temperature (Extreme spike)
        45.0, 0.1, 0.0,   # Humidity (Normal)
        0.5, 0.01, 0.0    # CPU Load (Normal)
    ]
    
    result = model.predict(anomaly_vector)
    
    assert result["is_anomaly"] is True, f"Expected 95°C spike to be an anomaly, but got result: {result}"

def test_isolation_forest_accepts_normal_temperature():
    model = AnomalyModel(model_path=HYBRID_MODEL_PATH, scaler_path=HYBRID_SCALER_PATH)
    
    # 24.0°C is well within the 18-30°C range of the MIT normal subset used for training v2
    normal_vector = [
        24.0, 0.1, 0.0,  # Temperature (Normal mean)
        45.0, 0.1, 0.0,  # Humidity (Normal)
        0.5, 0.0, 0.0    # CPU Load (Normal)
    ]
    
    result = model.predict(normal_vector)
    
    assert result["is_anomaly"] is False, f"Expected 24°C to be normal, but got result: {result}"
