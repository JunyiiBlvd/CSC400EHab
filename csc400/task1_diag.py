from backend.ml.model_loader import ModelLoader
from backend.ml.feature_extraction import SlidingWindowFeatureExtractor
import pandas as pd
import numpy as np
import os

def run_diag():
    ml = ModelLoader()
    
    # Check what a real normal vector looks like
    if os.path.exists('data/synthetic/normal_telemetry.csv'):
        df = pd.read_csv('data/synthetic/normal_telemetry.csv')
        ext = SlidingWindowFeatureExtractor(window_size=10)
        
        # Collect window
        for _, row in df.iloc[100:110].iterrows():
            ext.add_point(row.to_dict())
            
        feat = ext.extract_features()
        print('Real normal feature vector:', feat)
        result = ml.predict(feat)
        print('Real normal prediction:', result)
        
        if result['is_anomaly']:
            print("\nDIAGNOSIS: False Positive confirmed on real normal data.")
            print("Action: Raise contamination to 0.03 and retrain.")
        else:
            print("\nDIAGNOSIS: Model is working correctly.")
            print("The [0.5]*12 test was likely out-of-distribution (wrong scale).")
    else:
        print("Error: data/synthetic/normal_telemetry.csv not found")

if __name__ == "__main__":
    run_diag()
