import pandas as pd
import numpy as np
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from backend.ml.feature_extraction import SlidingWindowFeatureExtractor

def process_cold_source():
    print("Processing Cold Source dataset...")
    if not os.path.exists('datasets/cold_source_control_dataset.csv'):
        print("Error: datasets/cold_source_control_dataset.csv not found")
        return

    df = pd.read_csv('datasets/cold_source_control_dataset.csv')
    
    # temperature = Inlet_Temperature(°C)
    temp = df['Inlet_Temperature(°C)']
    
    # cpu_load = Server_Workload(%) / 100.0
    cpu = df['Server_Workload(%)'] / 100.0
    
    # airflow = normalize Cooling_Unit_Power_Consumption(kW)
    power = df['Cooling_Unit_Power_Consumption(kW)']
    power_clipped = power.clip(lower=power.quantile(0.05))
    airflow = (power_clipped / power_clipped.median()) * 2.5
    airflow = airflow.clip(lower=1.5, upper=4.0)
    
    # humidity = sampled from N(45.0, 2.0) with seed 99
    np.random.seed(99)
    humidity = np.random.normal(45.0, 2.0, len(df))
    
    # Create telemetry rows
    telemetry = pd.DataFrame({
        'temperature': temp,
        'airflow': airflow,
        'humidity': humidity,
        'cpu_load': cpu
    })
    
    extractor = SlidingWindowFeatureExtractor(window_size=10)
    features_list = []
    for _, row in telemetry.iterrows():
        extractor.add_point(row.to_dict())
        if extractor.is_window_ready():
            features_list.append(extractor.extract_features())
            
    output_file = 'data/real/cold_source_features.csv'
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    pd.DataFrame(features_list).to_csv(output_file, index=False, header=False)
    
    # Verify column 3 (airflow_mean)
    # The extractor order is [temp_mean, temp_var, temp_roc, airflow_mean, ...]
    # So airflow_mean is index 3.
    feat_df = pd.DataFrame(features_list)
    airflow_mean_stats = feat_df[3]
    print(f"Cold source column 3 (airflow_mean) stats:")
    print(f"  min={airflow_mean_stats.min():.4f}, max={airflow_mean_stats.max():.4f}, mean={airflow_mean_stats.mean():.4f}")

def process_mit():
    print("Processing MIT dataset...")
    if not os.path.exists('datasets/MIT_dataset.csv'):
        print("Error: datasets/MIT_dataset.csv not found")
        return
        
    # MIT is huge, taking subset for feature generation
    df = pd.read_csv('datasets/MIT_dataset.csv', nrows=20000)
    
    # Mapping:
    # temperature: Temp (C)
    # humidity: Humidity
    # airflow: Light (proxy) -> normalize to 2.0-3.0 range
    # cpu_load: Voltage (proxy) -> normalize to 0.1-0.9 range
    
    temp = df['Temp (C)']
    hum = df['Humidity']
    
    # Normalize Light to airflow range [2.0, 3.0]
    light = df['Light']
    airflow = 2.0 + (light - light.min()) / (light.max() - light.min() + 1e-6) * 1.0
    
    # Normalize Voltage to cpu_load range [0.1, 0.9]
    voltage = df['Voltage']
    cpu = 0.1 + (voltage - voltage.min()) / (voltage.max() - voltage.min() + 1e-6) * 0.8
    
    telemetry = pd.DataFrame({
        'temperature': temp,
        'airflow': airflow,
        'humidity': hum,
        'cpu_load': cpu
    })
    
    extractor = SlidingWindowFeatureExtractor(window_size=10)
    features_list = []
    for _, row in telemetry.iterrows():
        extractor.add_point(row.to_dict())
        if extractor.is_window_ready():
            features_list.append(extractor.extract_features())
            
    output_file = 'data/real/mit_features.csv'
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    pd.DataFrame(features_list).to_csv(output_file, index=False, header=False)
    print(f"Saved {len(features_list)} feature vectors to {output_file}")

if __name__ == "__main__":
    process_cold_source()
    process_mit()
