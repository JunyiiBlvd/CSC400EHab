import os
import sys
import pandas as pd
import numpy as np
import joblib
from typing import List, Dict, Any

# Add project root to path
sys.path.append(os.getcwd())

from backend.ml.model_loader import ModelLoader
from backend.ml.feature_extraction import SlidingWindowFeatureExtractor

def validate_on_real_anomalies():
    print("--- REAL ANOMALY VALIDATION ---")
    
    # 1. Load model and scaler
    try:
        loader = ModelLoader()
        model = loader.model
        scaler = loader.scaler
        print("[1/4] Model and scaler loaded successfully.")
    except Exception as e:
        print(f"Error loading model: {e}")
        return

    # 2. Load anomaly dataset
    validation_path = 'data/real/mit_anomaly_validation.csv'
    if not os.path.exists(validation_path):
        print(f"Error: {validation_path} not found.")
        return
    
    df = pd.read_csv(validation_path)
    print(f"[2/4] Loaded {len(df)} raw anomaly rows from {validation_path}.")

    # 3. Extract features (using windowing)
    # Since the file is already sorted by Moteid and time, we can group by Moteid
    print("[3/4] Extracting anomaly windows...")
    
    # We need to map raw columns to our 4 variables: temperature, airflow, humidity, cpu_load
    # Using the same logic as create_features.py
    
    # Normalize Light to airflow [2.0, 3.0]
    l_min, l_max = df['Light'].min(), df['Light'].max()
    df['airflow'] = 2.0 + (df['Light'] - l_min) / (l_max - l_min + 1e-6) * 1.0
    
    # Normalize Voltage to cpu_load [0.1, 0.9]
    v_min, v_max = df['Voltage'].min(), df['Voltage'].max()
    df['cpu_load'] = 0.1 + (df['Voltage'] - v_min) / (v_max - v_min + 1e-6) * 0.8
    
    # Direct mappings
    df['temperature'] = df['Temp (C)']
    df['humidity'] = df['Humidity']
    
    # Handle NaNs in MIT data (especially Humidity/Light/Voltage can be missing)
    df = df.ffill().bfill().fillna(0)
    
    mote_groups = df.groupby('Moteid')
    
    all_features = []
    scores = []
    predictions = []
    
    for mote_id, group in mote_groups:
        extractor = SlidingWindowFeatureExtractor(window_size=10)
        for _, row in group.iterrows():
            point = {
                'temperature': float(row['temperature']),
                'airflow': float(row['airflow']),
                'humidity': float(row['humidity']),
                'cpu_load': float(row['cpu_load'])
            }
            extractor.add_point(point)
            if extractor.is_window_ready():
                feat = extractor.extract_features()
                all_features.append(feat)
                
                # Inference — matches model_loader.py deployed threshold
                feat_scaled = scaler.transform([feat])
                score = model.decision_function(feat_scaled)[0]
                is_anomaly = score < 0.15

                scores.append(score)
                predictions.append(is_anomaly)

    if not all_features:
        print("Error: No windows could be formed (all motes have < 10 points).")
        return

    # 4. Report results
    total_tested = len(all_features)
    detected = sum(predictions)
    missed = total_tested - detected
    recall = (detected / total_tested) * 100 if total_tested > 0 else 0
    
    detected_scores = [s for s, p in zip(scores, predictions) if p]
    missed_scores = [s for s, p in zip(scores, predictions) if not p]
    
    avg_detected_score = np.mean(detected_scores) if detected_scores else 0
    avg_missed_score = np.mean(missed_scores) if missed_scores else 0
    
    print(f"\n[4/4] VALIDATION RESULTS:")
    print(f"Total anomaly windows tested: {total_tested}")
    print(f"Anomalies detected (recall): {detected} ({recall:.2f}%)")
    print(f"Anomalies missed:           {missed}")
    print(f"\nScore Distribution:")
    print(f"Average score (Detected): {avg_detected_score:.4f}")
    print(f"Average score (Missed):   {avg_missed_score:.4f}")
    
    # Save summary
    results_path = 'data/real/validation_results.txt'
    with open(results_path, 'w') as f:
        f.write("MIT Real Anomaly Validation Summary\n")
        f.write("====================================\n")
        f.write(f"Total anomaly windows tested: {total_tested}\n")
        f.write(f"Detected: {detected}\n")
        f.write(f"Missed:   {missed}\n")
        f.write(f"Recall:   {recall:.2f}%\n")
        f.write("\nScore Distribution:\n")
        f.write(f"Average score (Detected): {avg_detected_score:.4f}\n")
        f.write(f"Average score (Missed):   {avg_missed_score:.4f}\n")
        if detected_scores:
            f.write(f"Min detected score:     {min(detected_scores):.4f}\n")
            f.write(f"Max detected score:     {max(detected_scores):.4f}\n")
            
    print(f"\nResults saved to {results_path}")

if __name__ == "__main__":
    validate_on_real_anomalies()
