# E-Habitat Migration Log
## Branch: feature/modelrefinement | Spring 2026 CSC400

---

## 1. Physics Engine Changes

The simulation engine underwent a significant overhaul to transition from isolated, static models to a fully coupled physics environment. This was necessary to provide the machine learning pipeline with realistic multi-sensor correlations required for unsupervised anomaly detection.

### 1.1 Thermal Model (thermal_model.py + thermal.py)
- **What changed:** An `airflow_ratio` parameter was added to the `step()` function.
- **Before:** `CoolingPower = cooling_coefficient * (T - T_ambient)`
- **After:** `CoolingPower = cooling_coefficient * airflow_ratio * (T - T_ambient)`
- **Why:** In previous iterations, cooling was a constant force regardless of fan state. By introducing `airflow_ratio` (defined as `current_airflow / nominal_flow`), the cooling effectiveness now dynamically scales with the simulation's airflow. If a fan fails (airflow = 0), the cooling power drops to zero, causing a realistic thermal runaway.

### 1.2 Airflow Model (airflow.py)
- **What changed:** Deterministic static output was replaced with a dynamic process including Gaussian noise and HVAC feedback.
- **Before:** `step()` returned `nominal_flow * (1 - obstruction_ratio)` exactly.
- **After:** The model now incorporates an AR(1) noise process and a proportional HVAC feedback loop.
- **Formula:** `flow[t] = target_nominal + hvac_response + N(0, 0.08)`
  where `hvac_response = 0.05 * (temperature - 20.88)`
- **Why:** The previous model had zero variance at steady state. This caused the `StandardScaler` in the ML pipeline to encounter division-by-zero errors or produce unstable features. The new model provides the statistical "texture" required for Robust Scaling and simulates the fan speed increase as temperatures rise.

### 1.3 Humidity Model (humidity.py)
- **What changed:** Temperature coupling and mean reversion were added.
- **Before:** `H(t+1) = H(t) + drift + noise`
- **After:** `H(t+1) = H(t) + drift + reversion + coupling_drift + noise`
  - `reversion = -0.05 * (H - H_initial)`
  - `coupling_drift = -0.3 * (T - T_reference) * 0.01`
- **Why:** Real-world humidity levels are physically linked to temperature. As a compute node heats up, the relative humidity typically drops. This inverse correlation is a key "normal" behavior that the Isolation Forest learns; a break in this correlation (e.g., temperature rising while humidity stays flat) is a strong indicator of an anomaly.

### 1.4 VirtualNode (node.py)
- **What changed:** Full physics coupling was wired, and ML inference was integrated into the core step loop.
- **Before:** Only the `ThermalModel` was called in `step()`. `AirflowModel` and `HumidityModel` were orphaned or called independently, leading to uncoupled telemetry.
- **After:** The `VirtualNode` now orchestrates a strict physical sequence:
    1. **CPU Load Generation:** Generated via an AR(1) process (target 0.5, autocorrelation 0.95).
    2. **Airflow Update:** `airflow = airflow_model.step(temperature=last_step_temperature)`.
    3. **Efficiency Calculation:** `airflow_ratio = current_airflow / nominal_flow`.
    4. **Thermal Step:** `temperature = thermal_model.step(cpu_load, airflow_ratio)`.
    5. **Humidity Step:** `humidity = humidity_model.step(temperature)`.
    6. **ML Inference:** Features are extracted from a sliding window and passed to the `ModelLoader`.
    7. **Telemetry Enrichment:** `anomaly_score` and `is_anomaly` are appended to the telemetry dictionary.
- **Why:** This sequence ensures that every sensor reading in a single telemetry frame is physically consistent with the others, allowing the ML model to detect deviations in the *relationships* between variables.

### 1.5 Anomaly Injection
- **Thermal Spike:** `inject_thermal_spike()` was refactored. Instead of artificially incrementing the temperature variable, it now sets `cpu_load_override = 1.0`. This forces the physics engine to calculate the resulting heat, creating a "natural" spike that respects the node's thermal mass.
- **HVAC Failure:** `simulate_fan_failure()` sets `obstruction_ratio = 1.0`. This immediately drops airflow to zero, overriding any HVAC feedback and causing the thermal model to lose its primary cooling source.

---

## 2. ML Pipeline Changes

The transition to v2 of the ML pipeline focused on robustness and the integration of real-world data distributions.

### 2.1 Feature Vector
- **Before:** 9-dimensional vector. Airflow was excluded due to the zero-variance issue.
- **After:** 12-dimensional vector:
  `[temp_mean, temp_var, temp_roc, airflow_mean, airflow_var, airflow_roc, hum_mean, hum_var, hum_roc, cpu_mean, cpu_var, cpu_roc]`
- **Note:** All variables now include Mean, Variance, and Rate of Change (ROC) over a 10-step window.

### 2.2 Training Data Sources
The model was trained on a hybrid dataset totaling **22,239 rows**.

| Source | File | Rows | % of Training |
|-------------|----------------------------|-------|---------------|
| Synthetic | normal_telemetry.csv | 10000 | 45.0% |
| Cold Source | cold_source_features.csv | 3489 | 15.7% |
| MIT | mit_features.csv | 5000 | 22.5% |
| Kaggle HVAC | HVAC_Kaggle.csv | 3750 | 16.9% |

**Data Contributions & Imputation:**
- **Synthetic:** Provides the baseline "ideal" physics signatures.
- **Cold Source:** Real-world server room data. Missing humidity was sampled from `N(45, 2)` to match expected environmental baselines.
- **MIT:** High-frequency thermal data. CPU load was imputed based on thermal rate-of-change.
- **Kaggle:** Provides HVAC fan power correlations. Airflow was mapped from fan power using a linear transfer function.

### 2.3 Scaler
- **Before:** `StandardScaler`. This model failed (NaN outputs) because the physics engine occasionally produced features with near-zero standard deviation.
- **After:** `RobustScaler`. This scaler uses the median and Interquartile Range (IQR). It is significantly more resilient to the outliers present in the real-world datasets and handles low-variance features without numerical instability.
- **Saved to:** `models/scaler_v2.pkl`

### 2.4 Model
- **Before:** `models/isolation_forest.pkl` (v1).
- **After:** `models/model_v2_hybrid_real.pkl` (v2).
- **Parameters:** `IsolationForest(contamination=0.01, n_estimators=200, random_state=42)`
- **Actual Decision Threshold (`offset_`):** `-0.6134` (Values below this are flagged as anomalies).

### 2.5 Validation Results
- **False Positive Rate:** 1.0% on synthetic normal data (verified during training).
- **HVAC Failure Detection:** Detected at **Step 4** after fan failure (Requirement was detection within 20 steps).
- **Real-World Validation:** Successfully validated against the MIT anomaly dataset containing 1,908 documented thermal events.

### 2.6 ModelLoader (model_loader.py)
- **Class Update:** Renamed from `AnomalyModel` to `ModelLoader` to better reflect its role in managing both the scaler and the model.
- **Simplified Inference:** The `predict()` method now accepts a raw 12-D feature vector, applies the `RobustScaler` internally, and returns a unified dictionary: `{'anomaly_score': float, 'is_anomaly': bool}`.

---

## 3. API Changes (api.py)

The API was migrated from a polling-based architecture to a real-time streaming architecture.

### 3.1 Removed
- **`GET/POST /telemetry/step`**: Removed legacy REST polling endpoint to reduce server overhead and prevent uncoordinated simulation steps.
- **Single-node Instance**: The global `node` variable was removed in favor of a multi-node dictionary.

### 3.2 Added
- **WebSocket Endpoint**: `ws://localhost:8000/ws/simulation`.
    - Streams a JSON "frame" every 1 second.
    - Each frame contains telemetry for all three nodes.
    - Each node's telemetry includes a Unix `timestamp` (float) for frontend latency tracking.
- **Scenario Injection**: `POST /simulation/inject?node_id=...&scenario=...`.
    - Supported: `hvac_failure`, `thermal_spike`, `reset`.
- **Persistent Nodes**: Three `VirtualNode` instances initialized at the module level:
    - `node-1`: seed=42, T_init=21.0
    - `node-2`: seed=43, T_init=22.0
    - `node-3`: seed=44, T_init=21.5
- **CORS**: `CORSMiddleware` configured with `allow_origins=['*']` to support cross-origin WebSocket handshakes.

### 3.3 WebSocket Frame Schema
```json
{
  "node-1": {
    "node_id": "string",
    "timestamp": 1709827200.123,
    "temperature": 21.0,
    "humidity": 45.0,
    "airflow": 2.5,
    "cpu_load": 0.5,
    "injected_anomaly": false,
    "anomaly_score": 0.123,
    "is_anomaly": false
  },
  "node-2": { ... },
  "node-3": { ... }
}
```

---

## 4. Test Suite Changes

The test suite was updated to accommodate the new physics parameters and 12-dimensional feature vectors.

| Test File | Tests | Changes Made |
|----------------------------|-------|---------------------------------------------------------------------------------------|
| `test_airflow_model.py` | 6 | Updated tolerances for AR(1) noise; verified HVAC feedback slopes. |
| `test_environment_model.py`| 2 | Added checks for humidity-temperature coupling drift. |
| `test_feature_extraction.py`| 6 | Updated expected vector length from 9 to 12. |
| `test_humidity_model.py` | 6 | Verified mean-reversion logic and range clamping (0-100%). |
| `test_model_loader.py` | 3 | Updated to use `model_v2_hybrid_real.pkl`; verified `predict()` output schema. |
| `test_thermal_model.py` | 5 | Added `airflow_ratio` to all `step()` calls; updated equilibrium range checks. |
| `test_thermal.py` | 5 | Legacy checks updated to match `ThermalModel` constructor signature. |

**Final Result:** 33 passed, 0 failed.

---

## 5. Known Limitations and Technical Debt

- **HVAC Lag:** The simulation uses a 1-step lag for HVAC response. In real-world data centers, fans have a mechanical ramp-up time of 2-5 minutes.
- **Setpoint Hardcoding:** The 20.88°C setpoint is hardcoded as an equilibrium approximation for the specific synthetic thermal mass used.
- **MIT Data Imputation:** MIT `cpu_load` and `airflow` are derived from temperature rate-of-change rather than direct measurement.
- **Security:** There is currently no WebSocket authentication or rate-limiting (Week 10 goal).
- **Time Compression:** The simulation runs at real-time (1:1). High-speed training requires a headless runner mode.
- **Persistence:** Node state is kept in memory; a server restart resets all simulation history.

---

## 6. How to Run

### 6.1 Environment Setup
```bash
# Activate the virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 6.2 Start the Backend
```bash
# Run the FastAPI server with the project root in PYTHONPATH
PYTHONPATH=. python3 -m uvicorn backend.api:app --port 8000 --reload
```

### 6.3 Run Validation Tests
```bash
# Run all backend tests
PYTHONPATH=. pytest backend/tests/
```

### 6.4 Model Retraining
```bash
# Generate fresh features and retrain the hybrid model
PYTHONPATH=. python3 backend/ml/train_hybrid_model.py
```

---
MIGRATION LOG COMPLETE
