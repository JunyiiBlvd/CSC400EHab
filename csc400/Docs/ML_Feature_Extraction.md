
# ML Feature Extraction for Anomaly Detection

## 1. Overview

This document outlines the feature extraction process for the anomaly detection model in the CSC400EHab project. The core of this process is a sliding window mechanism that transforms raw time-series telemetry data into a structured feature vector suitable for machine learning.

## 2. Why Sliding Windows?

Anomaly detection in time-series data often requires contextual information. A single data point is rarely enough to determine if a system is in an anomalous state. Sliding windows provide this context by capturing the recent history of the telemetry data. This allows the model to learn patterns and identify deviations from normal operating behavior.

## 3. Feature Definitions

For each variable in the telemetry stream, we calculate the following three features over the current window:

*   **Mean:** The average value of the variable within the window. This provides a measure of the central tendency.
*   **Variance:** The variance of the values within the window. This measures the dispersion or volatility of the variable.
*   **Rate of Change:** The difference between the last and first data points in the window. This captures the trend of the variable over the window.

## 4. Feature Vector Structure

The feature extraction process produces a 12-dimensional feature vector. The features are calculated for each of the four variables and ordered as follows:

1.  `temperature_mean`
2.  `temperature_variance`
3.  `temperature_rate_of_change`
4.  `humidity_mean`
5.  `humidity_variance`
6.  `humidity_rate_of_change`
7.  `airflow_mean`
8.  `airflow_variance`
9.  `airflow_rate_of_change`
10. `cpu_load_mean`
11. `cpu_load_variance`
12. `cpu_load_rate_of_change`

## 5. Example

**Input Telemetry (Window Size = 5):**

```json
[
    {"temperature": 20, "humidity": 50, "airflow": 100, "cpu_load": 30},
    {"temperature": 21, "humidity": 51, "airflow": 101, "cpu_load": 32},
    {"temperature": 22, "humidity": 52, "airflow": 102, "cpu_load": 34},
    {"temperature": 23, "humidity": 53, "airflow": 103, "cpu_load": 36},
    {"temperature": 24, "humidity": 54, "airflow": 104, "cpu_load": 38}
]
```

**Output Feature Vector:**

```
[
    22.0,  // temperature mean
    2.0,   // temperature variance
    4.0,   // temperature rate of change (24 - 20)
    52.0,  // humidity mean
    2.0,   // humidity variance
    4.0,   // humidity rate of change (54 - 50)
    102.0, // airflow mean
    2.0,   // airflow variance
    4.0,   // airflow rate of change (104 - 100)
    34.0,  // cpu_load mean
    8.0,   // cpu_load variance
    8.0    // cpu_load rate of change (38 - 30)
]
```

## 6. Limitations

*   **Fixed Window Size:** The current implementation uses a fixed window size. This may not be optimal for all types of anomalies.
*   **Limited Features:** The feature set is relatively simple. More complex features, such as frequency domain features (e.g., Fourier transforms), could capture additional information.

## 7. Future Improvements

*   **Adaptive Window Size:** The window size could be dynamically adjusted based on the characteristics of the data.
*   **Expanded Feature Set:** Additional features could be incorporated, such as moving averages with different window sizes, or features derived from the frequency domain.
*   **Online Standardization:** The features could be standardized (e.g., using a running mean and standard deviation) to improve the performance of some machine learning models.
