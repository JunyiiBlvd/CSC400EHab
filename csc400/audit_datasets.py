import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

def audit_mit():
    print("--- DATASET 1: MIT Intel Lab ---")
    try:
        df_normal = pd.read_csv('data/real/mit_normal_subset.csv')
        df_anomaly = pd.read_csv('data/real/mit_anomaly_validation.csv')
        
        print("1. Column Headers:", list(df_normal.columns))
        print("2. 3 Sample Rows:\n", df_normal.head(3).to_string())
        
        # Time interval (Timestamp is formatted like 12:59:16 AM)
        # Date is 2/28/2004
        dt = pd.to_datetime(df_normal['Date'] + ' ' + df_normal['Timestamp'])
        diffs = dt.diff().dt.total_seconds().dropna()
        print("3. Time Interval (mode):", diffs.mode()[0], "seconds")
        
        print("4. Value Ranges:")
        print(f"   Temperature: {df_normal['temperature'].min():.2f} to {df_normal['temperature'].max():.2f}")
        print(f"   Humidity: {df_normal['Humidity'].min():.2f} to {df_normal['Humidity'].max():.2f}")
        
        print("5. Rows in normal subset:", len(df_normal))
        print("6. Rows in anomaly validation:", len(df_anomaly))
        print()
    except Exception as e:
        print("Error auditing MIT:", e)

def audit_hvac():
    print("--- DATASET 2: Kaggle HVAC ---")
    try:
        df = pd.read_csv('datasets/HVAC_Kaggle.csv')
        print("1. Column Headers:", list(df.columns))
        print("2. 3 Sample Rows:\n", df.head(3).to_string())
        
        dt = pd.to_datetime(df['Timestamp'])
        diffs = dt.diff().dt.total_seconds().dropna()
        print("3. Time Interval (mode):", diffs.mode()[0], "seconds")
        
        df['Delta_T'] = df['T_Return'] - df['T_Supply']
        print("4. Value Ranges:")
        print(f"   T_Return: {df['T_Return'].min():.2f} to {df['T_Return'].max():.2f}")
        print(f"   T_Supply: {df['T_Supply'].min():.2f} to {df['T_Supply'].max():.2f}")
        print(f"   Delta T: {df['Delta_T'].min():.2f} to {df['Delta_T'].max():.2f}")
        
        print("5. Total Rows:", len(df))
        
        active_df = df[df['Power'] > 0]
        print("6. Active Rows (Power > 0):", len(active_df))
        
        print("7. Active Delta T Stats:")
        stats = active_df['Delta_T'].describe()
        print(f"   Mean: {stats['mean']:.4f}, Std: {stats['std']:.4f}, Min: {stats['min']:.4f}, Max: {stats['max']:.4f}")
        print()
    except Exception as e:
        print("Error auditing HVAC:", e)

def audit_cpu():
    print("--- DATASET 3: CPU Utilization (cold_source_control_dataset.csv) ---")
    try:
        df = pd.read_csv('datasets/cold_source_control_dataset.csv')
        print("1. Column Headers:", list(df.columns))
        print("2. 3 Sample Rows:\n", df.head(3).to_string())
        
        dt = pd.to_datetime(df['Timestamp'])
        diffs = dt.diff().dt.total_seconds().dropna()
        print("3. Time Interval (mode):", diffs.mode()[0], "seconds")
        
        cpu_col = 'Server_Workload(%)'
        print(f"4. CPU Utilization values ({cpu_col}):")
        print(f"   Range: {df[cpu_col].min():.2f} to {df[cpu_col].max():.2f}")
        print(f"   Units: 0-100 (percentage)")
        
        print("5. Total Rows:", len(df))
        
        print("6. Normal Utilization Stats:")
        stats = df[cpu_col].describe()
        print(f"   Mean: {stats['mean']:.4f}, Std: {stats['std']:.4f}, Min: {stats['min']:.4f}, Max: {stats['max']:.4f}")
        
        # Anomaly periods check (simple jump check)
        df['diff'] = df[cpu_col].diff().abs()
        print("7. Anomaly check (Max jump between steps):", df['diff'].max())
        
        # Signal smoothness (autocorrelation)
        autocorr = df[cpu_col].autocorr()
        print("8. Autocorrelation (Lag 1):", autocorr)
        if autocorr > 0.8:
            print("   Signal is smooth and autocorrelated.")
        else:
            print("   Signal jumps randomly.")
        print()
    except Exception as e:
        print("Error auditing CPU:", e)

if __name__ == "__main__":
    audit_mit()
    audit_hvac()
    audit_cpu()
