# Branch Engineering Documentation

## Branch
`feature/modelrefinement2`

## Overview
This branch finalizes the machine learning anomaly detection pipeline and enhances the simulation's physical fidelity. The primary outcome is a robust, real-time anomaly detection system integrated directly into the `VirtualNode`, capable of identifying HVAC failures and thermal spikes with high precision and low false-positive rates.

## ML Pipeline Final State
The ML system employs a hybrid approach, combining high-fidelity synthetic data with diverse real-world datasets for training.

- **Feature Engineering:** A `SlidingWindowFeatureExtractor` (window size 10) computes mean, variance, and rate of change for Temperature, Airflow, Humidity, and CPU Load.
- **Preprocessing:** `RobustScaler` is utilized to normalize the 12-dimensional feature vector, ensuring resilience against outliers in the training data.
- **Model:** `IsolationForest` (200 estimators, 1% contamination) performs unsupervised anomaly detection.
- **Training Data:** A balanced hybrid dataset:
    - 40% Synthetic (Normal simulation)
    - 25% Cold Source (Real data)
    - 20% MIT (Real data)
    - 15% Kaggle HVAC (Real data)

## Feature Changes
- **Real-time Inference:** `VirtualNode` now performs local inference on every simulation step once the feature window is primed.
- **Enriched Telemetry:** Telemetry output now includes `anomaly_score` (raw decision function output) and `is_anomaly` (boolean flag).
- **HVAC Feedback:** `AirflowModel` implements a dynamic HVAC response loop (~5% fan speed adjustment per 1°C deviation from 20.88°C setpoint).
- **Coupled Physics:** Humidity and Thermal models are now physically coupled, with humidity responding to instantaneous temperature changes.

## Architecture Changes
### ML Layer
- Introduced `ModelLoader` for unified model/scaler management.
- Implemented `train_hybrid_model.py` for reproducible offline training and validation.
- Added data auditing scripts (`audit_datasets.py`, `check_stats.py`).

### Simulation Layer
- **Airflow:** Added HVAC feedback loop and Gaussian noise (0.08) for statistical realism.
- **Node:** Integrated ML components (`FeatureExtractor`, `ModelLoader`) and added manual anomaly injection controls (`inject_thermal_spike`).
- **Thermal:** Refined cooling coefficients to allow for stable equilibrium points.

### Node Layer
- `VirtualNode` now acts as an "Edge" device, handling both simulation and analytics autonomously.

## Commit Summary
- `de39c7e` - Real Data Integration, physics coupling, scalar normalization, HVAC failure detection, virtualnode interference integration

## Files Changed
### Added
- `backend/ml/train_hybrid_model.py`
- `models/model_v2_hybrid_real.pkl`
- `models/scaler_v2.pkl`
- `data/real/cold_source_features.csv`
- `data/real/mit_anomaly_validation.csv`
- `data/real/mit_features.csv`
- `data/synthetic/normal_telemetry.csv`
- `test_airflow_physics.py`
- `verify_coupling.py`
- `verify_physics_spike.py`
- `audit_datasets.py`
- `check_stats.py`
- `diagnose.py`

### Modified
- `backend/ml/feature_extraction.py`
- `backend/ml/model_loader.py`
- `backend/simulation/airflow.py`
- `backend/simulation/humidity.py`
- `backend/simulation/node.py`
- `backend/simulation/thermal.py`
- `backend/simulation/thermal_model.py`
- `backend/tests/` (All simulation and ML tests updated for new physics/model logic)
- `.gitignore` (Added models and cache files)

## ML Related Code Changes
- **`backend/ml/model_loader.py`**: Encapsulates `joblib` loading and provides a `predict()` method that automatically applies the `RobustScaler` before inference.
- **`backend/ml/train_hybrid_model.py`**: Implements the full training pipeline, including source sampling, feature validation, and a 60-step HVAC failure sanity check.
- **`backend/simulation/node.py`**: Connects the `SlidingWindowFeatureExtractor` to the `ModelLoader`, updating the telemetry stream with analytics results.

## Anomaly Scenario Verification
Anomaly scenario logic was verified and enhanced in this branch.
- **HVAC Failure:** Verified in `train_hybrid_model.py` (Sanity Check). The model detects a fan failure within 40 steps as temperature rises and airflow drops.
- **Thermal Spike:** Implemented in `VirtualNode.inject_thermal_spike()`. This manually overrides CPU load to 100%, creating a statistical outlier that is detected by the Isolation Forest.
- **Files involved:** `backend/simulation/node.py`, `backend/simulation/airflow.py`, `backend/ml/train_hybrid_model.py`.

## Test Status
| Metric | Result |
|--------|--------|
| Total Tests | 33 |
| Passed | 33 |
| Failed | 0 |

Validation includes deterministic airflow tests, coupled physics verification, and ML inference precision checks.

## Next Development Phase
The project is transitioning from a polling-based frontend to **WebSocket-based real-time communication**. This will enable the `VirtualNode` to push enriched telemetry (including anomaly alerts) to the UI with minimal latency, supporting high-frequency simulation monitoring.
