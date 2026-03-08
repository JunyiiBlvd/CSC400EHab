import pandas as pd
import numpy as np
import joblib

# Check cold source airflow range
try:
    df = pd.read_csv('data/real/cold_source_features.csv', header=None)
    print('Cold source feature columns shape:', df.shape)
    if 6 in df.columns:
        print('Column 6 (airflow_mean) stats:')
        print(f'  min={df[6].min():.4f}, max={df[6].max():.4f}, mean={df[6].mean():.4f}')
except Exception as e:
    print(f'Error reading cold_source_features.csv: {e}')

# Check MIT features airflow range  
try:
    df2 = pd.read_csv('data/real/mit_features.csv', header=None, nrows=1000)
    print('\nMIT feature column 3 (airflow_mean) stats:')
    if 3 in df2.columns:
        print(f'  min={df2[3].min():.4f}, max={df2[3].max():.4f}, mean={df2[3].mean():.4f}')
except Exception as e:
    print(f'Error reading mit_features.csv: {e}')

# Check model threshold
try:
    model = joblib.load('models/model_v2_hybrid_real.pkl')
    # scikit-learn's IsolationForest uses offset_
    if hasattr(model, 'offset_'):
        print(f'\nModel offset_: {model.offset_:.4f}')
        print('Decision function scores below this are considered anomalies.')
    else:
        print("\nModel does not have 'offset_' attribute.")
        print(f"Available attributes: {[attr for attr in dir(model) if not attr.startswith('_')]}")
except Exception as e:
    print(f'Error loading model: {e}')
