import pandas as pd
import numpy as np

def calculate_stats(df, col):
    mean = df[col].mean()
    std = df[col].std()
    autocorr = df[col].autocorr(lag=1)
    return mean, std, autocorr

if __name__ == "__main__":
    df = pd.read_csv('data/synthetic/normal_telemetry.csv')

    variables = ['temperature', 'airflow', 'humidity', 'cpu_load']
    
    print("| Variable    | Mean    | Std     | Lag-1 AutoCorr |")
    print("|-------------|---------|---------|----------------|")
    for var in variables:
        m, s, a = calculate_stats(df, var)
        print(f"| {var:<11} | {m:7.4f} | {s:7.4f} | {a:14.4f} |")

    # Correlation between airflow and cpu_load
    corr = df['airflow'].corr(df['cpu_load'])
    print(f"\nCorrelation between airflow and cpu_load: {corr:.4f}")
