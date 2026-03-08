
import pandas as pd
import numpy as np
import os
import sys
import joblib
import random
from sklearn.preprocessing import RobustScaler
from sklearn.ensemble import IsolationForest
from sklearn.utils import shuffle

# Add project root to path
sys.path.append(os.getcwd())

from backend.ml.feature_extraction import SlidingWindowFeatureExtractor
from backend.simulation.thermal_model import ThermalModel
from backend.simulation.airflow import AirflowModel
from backend.simulation.humidity import HumidityModel
from backend.simulation.node import VirtualNode

def build_training_data():
    print("--- STEP 2: Building training data ---")
    
    # Source A: Synthetic
    print("Source A: Synthetic...")
    df_syn = pd.read_csv('data/synthetic/normal_telemetry.csv')
    extractor = SlidingWindowFeatureExtractor(window_size=10)
    syn_features = []
    for _, row in df_syn.iterrows():
        extractor.add_point(row.to_dict())
        if extractor.is_window_ready():
            syn_features.append(extractor.extract_features())
    syn_features = np.array(syn_features)
    
    # Source B: Cold Source
    print("Source B: Cold Source (Pre-processed)...")
    cold_features = pd.read_csv('data/real/cold_source_features.csv', header=None).values
    
    # Source C: MIT
    print("Source C: MIT (Pre-processed)...")
    mit_features = pd.read_csv('data/real/mit_features.csv', header=None, nrows=8000).values
    
    # Source D: Kaggle HVAC
    print("Source D: Kaggle HVAC...")
    df_kag = pd.read_csv('datasets/HVAC_Kaggle.csv')
    df_kag = df_kag[df_kag['Power'] > 0].copy()
    delta_t = df_kag['T_Return'] - df_kag['T_Supply']
    
    kag_data = pd.DataFrame()
    kag_data['temperature'] = df_kag['T_Supply']
    std_dt = delta_t.std()
    kag_data['airflow'] = (delta_t / std_dt) * 0.25 + 2.5
    p_min_kag, p_max_kag = df_kag['Power'].min(), df_kag['Power'].max()
    kag_data['cpu_load'] = (df_kag['Power'] - p_min_kag) / (p_max_kag - p_min_kag) * 0.8 + 0.1
    np.random.seed(77)
    kag_data['humidity'] = np.random.normal(45.0, 2.0, len(df_kag))
    
    extractor = SlidingWindowFeatureExtractor(window_size=10)
    kag_features = []
    for _, row in kag_data.iterrows():
        extractor.add_point(row.to_dict())
        if extractor.is_window_ready():
            kag_features.append(extractor.extract_features())
    kag_features = np.array(kag_features)
    
    total_target = 25000
    n_a = min(len(syn_features), int(total_target * 0.4))
    n_b = min(len(cold_features), int(total_target * 0.25))
    n_c = min(len(mit_features), int(total_target * 0.20))
    n_d = min(len(kag_features), int(total_target * 0.15))
    
    def sample(arr, n):
        idx = np.random.choice(len(arr), n, replace=False)
        return arr[idx]
    
    X_train = np.vstack([
        sample(syn_features, n_a),
        sample(cold_features, n_b),
        sample(mit_features, n_c),
        sample(kag_features, n_d)
    ])
    
    X_train = shuffle(X_train, random_state=42)
    
    print("\nTraining Data Composition:")
    print(f"| Source      | Rows  | Percentage |")
    print(f"|-------------|-------|------------|")
    print(f"| Synthetic   | {n_a:5} | {n_a/len(X_train)*100:9.1f}% |")
    print(f"| Cold Source | {n_b:5} | {n_b/len(X_train)*100:9.1f}% |")
    print(f"| MIT         | {n_c:5} | {n_c/len(X_train)*100:9.1f}% |")
    print(f"| Kaggle      | {n_d:5} | {n_d/len(X_train)*100:9.1f}% |")
    print(f"| TOTAL       | {len(X_train):5} | 100.0%     |")
    
    feature_names = [
        'temp_mean', 'temp_var', 'temp_roc',
        'airflow_mean', 'airflow_var', 'airflow_roc',
        'hum_mean', 'hum_var', 'hum_roc',
        'cpu_mean', 'cpu_var', 'cpu_roc'
    ]
    
    stds = np.std(X_train, axis=0)
    print("\nFeature Statistics (Standard Deviation):")
    for i, name in enumerate(feature_names):
        print(f"{name:<15}: {stds[i]:.6f}")
        if stds[i] < 0.001:
            raise ValueError(f"Feature {name} has too little variance (std={stds[i]:.6f})")
            
    print(f"\nMin Airflow Mean across all sources: {np.min(X_train[:, 3]):.4f}")
            
    return X_train

def validate_model(model, scaler):
    print("\n--- STEP 4: Validation ---")
    df_syn = pd.read_csv('data/synthetic/normal_telemetry.csv')
    normal_segment = df_syn.iloc[25000:25100]
    extractor = SlidingWindowFeatureExtractor(window_size=10)
    test_features = []
    for _, row in normal_segment.iterrows():
        extractor.add_point(row.to_dict())
        if extractor.is_window_ready():
            test_features.append(extractor.extract_features())
    
    X_test = scaler.transform(test_features)
    preds = model.predict(X_test)
    fp_rate = np.mean(preds == -1) * 100
    print(f"False Positive Rate (Synthetic Normal): {fp_rate:.1f}%")
    
    pass_fp = fp_rate < 10.0
    print(f"FP Check: {'PASS' if pass_fp else 'FAIL'}")
    return pass_fp

def sanity_check_hvac(model, scaler):
    print("\n--- STEP 5: HVAC failure sanity check (60 steps) ---")
    # AGGRESSIVE PHYSICS for faster temperature rise in demo
    thermal = ThermalModel(air_mass=5.0, heat_capacity=1005.0, heat_coefficient=2000.0, cooling_coefficient=100.0, initial_temperature=21.0, ambient_temperature=20.0)
    airflow = AirflowModel(nominal_flow=2.5, random_seed=1042)
    humidity = HumidityModel(45.0, 0.0, 0.2, 2042, reference_temp=21.0)
    
    node = VirtualNode("check-node", thermal, airflow, humidity, random_seed=42)
    extractor = SlidingWindowFeatureExtractor(window_size=10)
    
    for _ in range(50):
        t = node.step()
        extractor.add_point(t)
        
    print(f"{'Step':>4} | {'Temp':>7} | {'Airflow':>8} | {'Score':>13} | {'Anomaly'}")
    print("-" * 55)
    
    airflow.simulate_fan_failure()
    detected_at = None
    
    for i in range(1, 61):
        t = node.step()
        extractor.add_point(t)
        
        if extractor.is_window_ready():
            feat = np.array(extractor.extract_features()).reshape(1, -1)
            feat_scaled = scaler.transform(feat)
            score = model.decision_function(feat_scaled)[0]
            is_anomaly = model.predict(feat_scaled)[0] == -1
            
            if is_anomaly and detected_at is None:
                detected_at = i
                
            if i in [10, 15, 20, 25, 30, 40, 50, 60]:
                print(f"{i:4} | {t['temperature']:7.3f} | {t['airflow']:8.3f} | {score:13.4f} | {is_anomaly}")

    pass_hvac = detected_at is not None and detected_at <= 40
    print(f"\nHVAC Failure Detected at step: {detected_at if detected_at else 'N/A'}")
    print(f"HVAC Check: {'PASS' if pass_hvac else 'FAIL'}")
    return pass_hvac

if __name__ == "__main__":
    os.makedirs('models', exist_ok=True)
    X_train = build_training_data()
    print("\n--- STEP 3: Scale and train ---")
    scaler = RobustScaler()
    X_scaled = scaler.fit_transform(X_train)
    model = IsolationForest(contamination=0.01, random_state=42, n_estimators=200)
    model.fit(X_scaled)
    print(f"Model Decision Threshold: {model.offset_:.6f}")
    joblib.dump(scaler, 'models/scaler_v2.pkl')
    joblib.dump(model, 'models/model_v2_hybrid_real.pkl')
    pass_fp = validate_model(model, scaler)
    pass_hvac = sanity_check_hvac(model, scaler)
    print("\n--- STEP 6: Final Report ---")
    print(f"Overall Status: {'PASS' if pass_fp and pass_hvac else 'FAIL'}")
