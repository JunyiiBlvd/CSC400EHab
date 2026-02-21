# Baseline Data Generation

This document describes the process of generating synthetic baseline data for the E-Habitat simulation. This data is used for offline training preparation of anomaly detection models.

## 1. Purpose of Baseline Generation
The primary goal is to create a dataset that represents "normal" operation of a compute node over a significant period (48 hours). By establishing a baseline of normal behavior, machine learning models can be trained to recognize deviations that might indicate system failures or environmental anomalies.

## 2. Simulated Time vs. Real Time
The simulation operates in discrete steps, where each step represents 1 second of "simulated time."
- **Simulated Duration:** 172,800 steps (48 hours).
- **Execution Time (Real Time):** The script runs as fast as the CPU can process the mathematical models, completing 172,800 steps in a few seconds. This is significantly faster than real-time execution, which would take exactly 48 hours.

## 3. Data Flow Diagram
```mermaid
graph LR
    A[VirtualNode Simulation] -->|Telemetry Dict| B[SlidingWindowFeatureExtractor]
    B -->|Feature Vector (List)| C[Baseline Collector]
    C -->|Numpy Array| D[backend/ml/baseline_features.npy]
```

1. **VirtualNode:** Generates raw telemetry (temperature, humidity, airflow, CPU load) for each step.
2. **Feature Extractor:** Buffers the last 10 steps and calculates statistical features (mean, variance, rate of change).
3. **Collector:** Aggregates valid feature vectors into a matrix.
4. **Numpy File:** Saves the final matrix to disk in a binary format for efficient loading during training.

## 4. Output Format Description
The output is a `.npy` file containing a 2D numpy array.
- **Shape:** `(172791, 12)`
    - **172,791 rows:** These represent the time steps where the sliding window (size 10) was full. (172,800 total steps - 9 initial steps).
    - **12 columns:** These represent the extracted features in the following order:
        - `temperature_mean`, `temperature_variance`, `temperature_roc`
        - `humidity_mean`, `humidity_variance`, `humidity_roc`
        - `airflow_mean`, `airflow_variance`, `airflow_roc`
        - `cpu_load_mean`, `cpu_load_variance`, `cpu_load_roc`

## 5. Why a Database is Not Used
For this specific offline task, a database is avoided for several reasons:
- **Performance:** Writing/reading 170k+ rows to a database is slower than binary file I/O for bulk data.
- **Simplicity:** A `.npy` file is directly compatible with standard ML libraries (NumPy, Scikit-learn, PyTorch, TensorFlow).
- **Portability:** The dataset is a single file that can be easily shared or moved between training environments without requiring a database setup.

## 6. How to Run the Script
To regenerate the baseline data, run the following command from the project root:
```bash
PYTHONPATH=. python3 backend/ml/generate_baseline_data.py
```

## 7. Performance Expectations
- **CPU:** Minimal impact; the simulation is computationally lightweight.
- **RAM:** The resulting matrix occupies approximately 16-20 MB in memory.
- **Time:** Should complete in under 5 seconds on modern hardware.

## 8. Known Limitations
- **No Variations:** The current baseline uses constant model parameters (e.g., ambient temperature, nominal flow). It does not simulate diurnal cycles or varying cooling efficiencies.
- **Linear Drift:** Humidity follows a simple linear drift with noise, which may not capture complex environmental interactions.
- **Static Window:** The feature extraction window size is fixed at 10.

## 9. Offline Training Preparation
This script is intended **exclusively for offline training**. It does not interact with the live simulation dashboard or real-time monitoring services. The generated file serves as the "Ground Truth" for normal operation.
