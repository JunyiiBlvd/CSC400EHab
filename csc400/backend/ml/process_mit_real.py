
import pandas as pd
import numpy as np
import os
from datetime import timedelta

def process_mit_dataset(input_file='datasets/MIT_dataset.csv', 
                        output_normal='data/real/mit_normal_subset.csv',
                        output_anomalies='data/real/mit_anomaly_validation.csv'):
    """
    Identifies clean 4-hour windows and rapid temperature anomalies from the MIT dataset.
    """
    print(f"Loading {input_file}...")
    # Read CSV, specifying data types for speed
    df = pd.read_csv(input_file, dtype={
        'Date': str, 'Timestamp': str, 'Epoch': int, 'Moteid': int,
        'Temp (C)': float, 'Humidity': float, 'Light': float, 'Voltage': float
    })
    
    # Rename for easier access
    df.rename(columns={'Temp (C)': 'temperature'}, inplace=True)
    
    # Combine Date and Timestamp for proper time handling
    # Note: MIT dataset format is M/D/YYYY, H:MM:SS AM/PM
    print("Parsing timestamps...")
    df['dt'] = pd.to_datetime(df['Date'] + ' ' + df['Timestamp'], errors='coerce')
    df.dropna(subset=['dt'], inplace=True)
    df.sort_values(by=['Moteid', 'dt'], inplace=True)

    # 1. Identify Anomalies (Jump > 5°C in < 60s)
    print("Searching for rapid temperature anomalies...")
    df['temp_diff'] = df.groupby('Moteid')['temperature'].diff().abs()
    df['time_diff'] = df.groupby('Moteid')['dt'].diff().dt.total_seconds()
    
    anomalies = df[(df['temp_diff'] > 5) & (df['time_diff'] <= 60)].copy()
    anomalies.drop(columns=['dt', 'temp_diff', 'time_diff'], inplace=True)
    anomalies.to_csv(output_anomalies, index=False)
    print(f"Saved {len(anomalies)} anomaly rows to {output_anomalies}")

    # 2. Identify 4-Hour Normal Windows
    print("Searching for clean 4-hour windows...")
    normal_windows = []
    window_id_counter = 0

    # Group by Moteid to find continuous normal operation
    for mote_id, group in df.groupby('Moteid'):
        # Initial Filter: Temp 18-30°C and no nulls
        group = group.dropna(subset=['temperature', 'Humidity'])
        group = group[(group['temperature'] >= 18) & (group['temperature'] <= 30)]
        
        # Split into continuous chunks where jumps are <= 5°C
        group['jump'] = group['temperature'].diff().abs() > 5
        group['chunk'] = group['jump'].cumsum()
        
        for chunk_id, chunk in group.groupby('chunk'):
            if len(chunk) < 2: continue
            
            # Use a rolling window of 4 hours
            # Start time and end time of the entire chunk
            chunk_duration = (chunk['dt'].max() - chunk['dt'].min()).total_seconds()
            
            if chunk_duration >= 4 * 3600:
                # This chunk is at least 4 hours long. 
                # Take the first 4-hour block as a representative window.
                start_time = chunk['dt'].min()
                end_time = start_time + timedelta(hours=4)
                
                four_hour_window = chunk[chunk['dt'] <= end_time].copy()
                four_hour_window['window_id'] = f"node-{mote_id}-win-{window_id_counter}"
                normal_windows.append(four_hour_window)
                window_id_counter += 1

    if normal_windows:
        normal_df = pd.concat(normal_windows)
        normal_df.drop(columns=['dt', 'temp_diff', 'time_diff', 'jump', 'chunk'], inplace=True)
        normal_df.to_csv(output_normal, index=False)
        print(f"Saved {len(normal_windows)} normal windows to {output_normal}")
    else:
        print("No 4-hour windows found matching criteria.")

if __name__ == "__main__":
    process_mit_dataset()
