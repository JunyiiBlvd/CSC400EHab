# Model Runtime Inference

This document describes the runtime architecture for the anomaly detection system in the E-Habitat simulation.

## 1. Separation of Training vs. Inference
The system strictly separates the **training phase** from the **inference phase**:
- **Training (Offline):** Handled by `train_model.py`. This process reads large amounts of baseline data, builds the Isolation Forest, and serializes the result into a `.pkl` file. It is resource-intensive and performed only once or periodically.
- **Inference (Online/Real-time):** Handled by the `AnomalyModel` class in `model_loader.py`. This process loads the pre-trained model and provides instant predictions for incoming telemetry data. It is lightweight and designed to run alongside the simulation.

## 2. Why Model Loader Abstraction Exists
The `AnomalyModel` class provides a clean interface for the simulation's runner or API:
- **Encapsulation:** The rest of the system does not need to know that `scikit-learn` or `IsolationForest` is being used.
- **State Management:** It handles the complex logic of loading model artifacts and managing memory.
- **Simplified API:** It transforms raw model outputs into a standard, easy-to-consume dictionary format.

## 3. Explanation of Anomaly Score
The `score` returned by the `predict()` method is derived from scikit-learn's `decision_function`.
- **Value Range:** The score is a real number (typically between -0.5 and 0.5 in this implementation).
- **Interpretation:** 
    - **Higher (Positive) Scores:** The data point is deep within a dense cluster of normal baseline samples.
    - **Lower (Negative) Scores:** The data point is in a sparse region of the feature space, suggesting it is "isolated" from the baseline.

## 4. How Predictions are Interpreted
The model converts the raw anomaly score into a binary `is_anomaly` flag using a pre-defined threshold:
- **Prediction = 1 (Normal):** Maps to `is_anomaly: False`.
- **Prediction = -1 (Anomaly):** Maps to `is_anomaly: True`.

The threshold is determined by the `contamination` parameter set during the offline training phase.

## 5. Data Contract for Feature Vector
The `predict()` method expects a **12-dimensional list of floats** in the following order:
1. `temperature_mean`
2. `temperature_variance`
3. `temperature_roc` (Rate of Change)
4. `humidity_mean`
5. `humidity_variance`
6. `humidity_roc`
7. `airflow_mean`
8. `airflow_variance`
9. `airflow_roc`
10. `cpu_load_mean`
11. `cpu_load_variance`
12. `cpu_load_roc`

**Requirement:** All values must be numerical. Any missing values or incorrect data types will result in an error.

## 6. Error Handling Considerations
The `AnomalyModel` includes basic error handling for common runtime scenarios:
- **FileNotFoundError:** Raised if the `.pkl` model file is missing from the expected directory.
- **RuntimeError:** Raised if the model file is corrupted or incompatible with the current scikit-learn version.
- **Input Validation:** While currently minimal, future versions will include explicit checks for the feature vector's dimensionality.

## 7. Limitations of Real-time Inference
- **Latency:** While inference is fast, the bottleneck is often the **feature extraction** step (Sliding Window), which requires 10 steps of data to accumulate before the first prediction can be made.
- **Static Decision Boundary:** The model uses a fixed threshold learned during training. It cannot adapt to gradual changes in "normal" behavior (e.g., seasonal ambient temperature shifts) without retraining.
- **Cold Start:** The system provides no predictions for the first 9 seconds of a simulation session until the sliding window is full.

## 8. Deployment Model
The model is deployed as a local asset (`.pkl`). This ensures zero network latency for the simulation and allows the system to operate completely offline. Any updates to the model require distributing a new `.pkl` file to the inference environment.
