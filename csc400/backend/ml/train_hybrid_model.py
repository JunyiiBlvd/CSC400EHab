
import os
import pandas as pd
import numpy as np
import joblib
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import precision_score, recall_score, f1_score
from backend.ml.feature_extraction import SlidingWindowFeatureExtractor

def extract_all_features(df, window_size=10):
    """Utility to extract all possible windows from a dataframe."""
    extractor = SlidingWindowFeatureExtractor(window_size=window_size)
    features_list = []
    
    # Ensure column names match what extractor expects
    df_copy = df.copy()
    if 'Humidity' in df_copy.columns: df_copy.rename(columns={'Humidity': 'humidity'}, inplace=True)
    if 'Temp (C)' in df_copy.columns: df_copy.rename(columns={'Temp (C)': 'temperature'}, inplace=True)
    
    # Fill missing columns with defaults
    if 'airflow' not in df_copy.columns: df_copy['airflow'] = 2.5
    if 'cpu_load' not in df_copy.columns: df_copy['cpu_load'] = 0.5
    if 'humidity' not in df_copy.columns: df_copy['humidity'] = 45.0
    
    group_col = 'window_id' if 'window_id' in df_copy.columns else 'Moteid' if 'Moteid' in df_copy.columns else None
    
    if group_col:
        for _, group in df_copy.groupby(group_col):
            extractor.window.clear()
            for _, row in group.iterrows():
                extractor.add_point(row.to_dict())
                if extractor.is_window_ready():
                    features_list.append(extractor.extract_features())
    else:
        extractor.window.clear()
        for _, row in df_copy.iterrows():
            extractor.add_point(row.to_dict())
            if extractor.is_window_ready():
                features_list.append(extractor.extract_features())
                
    return np.array(features_list)

def train_hybrid_model(real_normal_path='data/real/mit_normal_subset.csv',
                       synthetic_normal_path='data/synthetic/normal_telemetry.csv',
                       anomaly_validation_path='data/real/mit_anomaly_validation.csv',
                       model_output_path='models/model_v2_hybrid_real.pkl',
                       scaler_output_path='models/scaler_v2.pkl'):
    
    # 1. Load data
    print("Loading data...")
    df_real = pd.read_csv(real_normal_path)
    df_synthetic = pd.read_csv(synthetic_normal_path)
    df_anomalies = pd.read_csv(anomaly_validation_path)
    
    # 2. Extract features
    print("Extracting features (window=10)...")
    X_real = extract_all_features(df_real)
    X_synthetic = extract_all_features(df_synthetic)
    
    # 3. Combine 60/40 real/synthetic
    print(f"Combining real ({len(X_real)}) and synthetic ({len(X_synthetic)}) features...")
    target_real_size = min(len(X_real), int(len(X_synthetic) * 1.5))
    target_synthetic_size = int(target_real_size * (4/6))
    
    idx_real = np.random.choice(len(X_real), target_real_size, replace=False)
    idx_syn = np.random.choice(len(X_synthetic), target_synthetic_size, replace=False)
    
    X_train = np.vstack([X_real[idx_real], X_synthetic[idx_syn]])
    
    # 4. Scale features
    print("Scaling features...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    
    print("\nFeature Statistics (After Scaling):")
    print(f"Mean: {X_train_scaled.mean(axis=0)}")
    print(f"Std:  {X_train_scaled.std(axis=0)}")
    
    print("\nFeature Statistics (Original):")
    feature_names = [
        "temp_mean", "temp_var", "temp_roc",
        "hum_mean", "hum_var", "hum_roc",
        "cpu_mean", "cpu_var", "cpu_roc"
    ]
    for i, name in enumerate(feature_names):
        print(f"{name:10}: mean={X_train[:,i].mean():.4f}, std={X_train[:,i].std():.4f}")
    
    # 5. Train Isolation Forest
    print("Training Isolation Forest (contamination=0.01)...")
    model = IsolationForest(contamination=0.01, random_state=42)
    model.fit(X_train_scaled)
    
    # 6. Save model and scaler
    os.makedirs(os.path.dirname(model_output_path), exist_ok=True)
    joblib.dump(model, model_output_path)
    joblib.dump(scaler, scaler_output_path)
    print(f"Model saved to {model_output_path}")
    print(f"Scaler saved to {scaler_output_path}")
    
    # 7. Validate
    print("Validating model...")
    X_val_normal = np.delete(X_real, idx_real, axis=0)
    if len(X_val_normal) > 1000: X_val_normal = X_val_normal[:1000]
    X_val_anomalies = extract_all_features(df_anomalies)
    
    X_val = np.vstack([X_val_normal, X_val_anomalies])
    X_val_scaled = scaler.transform(X_val)
    y_true = np.array([1] * len(X_val_normal) + [-1] * len(X_val_anomalies))
    
    y_pred = model.predict(X_val_scaled)
    
    precision = precision_score(y_true, y_pred, pos_label=-1)
    recall = recall_score(y_true, y_pred, pos_label=-1)
    f1 = f1_score(y_true, y_pred, pos_label=-1)
    
    print("\nValidation Results (Anomaly Class):")
    print(f"Precision: {precision:.4f}")
    print(f"Recall:    {recall:.4f}")
    print(f"F1 Score:  {f1:.4f}")

if __name__ == "__main__":
    train_hybrid_model()
