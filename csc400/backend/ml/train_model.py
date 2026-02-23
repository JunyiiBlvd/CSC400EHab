
import numpy as np
import joblib
import os
from sklearn.ensemble import IsolationForest

def train_isolation_forest(input_path="backend/ml/baseline_features.npy", 
                           output_path="backend/ml/isolation_forest.pkl"):
    """
    Trains an Isolation Forest model on synthetic baseline data.
    
    Args:
        input_path (str): Path to the baseline features .npy file.
        output_path (str): Path to save the trained model .pkl file.
    """
    # 1. Load baseline_features.npy
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Baseline features not found at {input_path}. Please run generate_baseline_data.py first.")
    
    X = np.load(input_path)
    num_samples = X.shape[0]
    
    # 2. Initialize IsolationForest
    contamination = 0.01
    model = IsolationForest(
        n_estimators=100,
        contamination=contamination,
        random_state=42,
        n_jobs=-1  # Use all available cores for training
    )
    
    # 3. Fit model
    print(f"Training Isolation Forest model on {num_samples} samples...")
    model.fit(X)
    
    # 4. Save model
    joblib.dump(model, output_path)
    
    # Print summary
    print(f"Model Training Summary:")
    print(f"- Number of samples: {num_samples}")
    print(f"- Contamination value: {contamination}")
    print(f"- Save location: {output_path}")

if __name__ == "__main__":
    train_isolation_forest()
