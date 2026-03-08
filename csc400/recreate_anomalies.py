
import pandas as pd
import numpy as np
import os

def recreate_mit_anomalies():
    print("Reading MIT_dataset.csv...")
    # Read the full dataset
    df = pd.read_csv('datasets/MIT_dataset.csv')
    
    # Correctly parse datetime for proper sorting
    print("Parsing datetimes and sorting...")
    df['Datetime'] = pd.to_datetime(df['Date'] + ' ' + df['Timestamp'])
    df = df.sort_values(['Moteid', 'Datetime'])
    
    # Identify anomalies per mote
    print("Calculating temperature deltas per mote...")
    # Group by Moteid and calculate the absolute difference from the previous reading
    df['temp_diff'] = df.groupby('Moteid')['Temp (C)'].diff().abs()
    
    # Flag anomalies: temperature change > 5°C
    anomalies = df[df['temp_diff'] > 5.0].copy()
    
    # Drop helper columns before saving
    output_df = anomalies.drop(columns=['Datetime', 'temp_diff'])
    
    output_path = 'data/real/mit_anomaly_validation.csv'
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    output_df.to_csv(output_path, index=False)
    
    print(f"Recreation complete.")
    print(f"New row count: {len(output_df)}")
    
    if len(output_df) > 0:
        print("\nSample anomalies (Temp vs previous):")
        # To show previous temp, we need to look back at the original sorted df
        indices = anomalies.index
        for idx in indices[:5]:
            curr_row = df.loc[idx]
            # Find previous row index in the sorted dataframe
            # Since we sorted by Moteid and Datetime, we can just use positional index
            pos = df.index.get_loc(idx)
            prev_row = df.iloc[pos-1]
            print(f"Mote {curr_row['Moteid']} | {prev_row['Timestamp']} ({prev_row['Temp (C)']}C) -> {curr_row['Timestamp']} ({curr_row['Temp (C)']}C) | Delta: {curr_row['temp_diff']:.2f}C")

if __name__ == "__main__":
    recreate_mit_anomalies()
