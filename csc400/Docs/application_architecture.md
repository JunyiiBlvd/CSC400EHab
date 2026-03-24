# Application Architecture Documentation

## Repository Structure

```text
/
├── app/                        # Frontend (Next.js/React)
│   ├── components/             # React UI components (Gauges, Alerts, Grid)
│   ├── lib/                    # Frontend utilities and API clients
│   └── page.tsx                # Main Dashboard entry point
├── backend/                    # Backend (Python/FastAPI)
│   ├── api.py                  # API entry point & WebSocket orchestration
│   ├── ml/                     # Machine Learning pipeline
│   │   ├── feature_extraction.py
│   │   ├── model_loader.py
│   │   ├── train_hybrid_model.py
│   │   └── ...
│   ├── simulation/             # Physics simulation engine
│   │   ├── node.py             # VirtualNode orchestration
│   │   ├── thermal_model.py    # Heat & cooling physics
│   │   ├── airflow.py          # HVAC & obstruction logic
│   │   ├── humidity.py         # Humidity & coupling logic
│   │   └── ...
│   └── tests/                  # Backend test suite
├── models/                     # Trained ML models and scalers (Pickle files)
├── data/                       # Datasets (CSV)
│   ├── real/                   # Real-world telemetry
│   └── synthetic/              # Generated simulation data
├── Docs/                       # Documentation and reports
└── ...
```

## System Overview

E-Habitat is an edge-computing monitoring and anomaly detection system. It simulates the environmental dynamics (thermal, airflow, humidity) of compute nodes in a data center and uses Machine Learning to detect operational anomalies in real-time.

**Key Goals:**
- High-fidelity physics simulation of node environments.
- Real-time visualization of telemetry via a web dashboard.
- Proactive anomaly detection using Isolation Forest models.
- Interactive control and scenario injection (e.g., fan failures, thermal spikes).

---

## Core Modules

### 1. Application Entry Points
- **Frontend**: `app/page.tsx` - The main React entry point that establishes a WebSocket connection to the backend and renders the dashboard.
- **Backend**: `backend/api.py` - The FastAPI server that manages simulation instances and handles REST/WebSocket communication.

### 2. Machine Learning Pipeline
- **Purpose**: Processes raw telemetry into features and performs anomaly inference.
- **Key Files**: `feature_extraction.py`, `model_loader.py`.
- **Responsibilities**: Sliding window management, feature engineering (mean, variance, ROC), and model scoring.

### 3. Simulation Engine
- **Purpose**: Models the physical behavior of a compute node.
- **Key Files**: `node.py`, `thermal_model.py`, `airflow.py`, `humidity.py`.
- **Responsibilities**: Heat generation based on CPU load, cooling via airflow, HVAC feedback loops, and humidity-temperature coupling.

---

## File-Level Breakdown

### `backend/api.py`
- **Purpose**: Core service orchestrator.
- **Key Classes/Functions**: `websocket_simulation`, `inject_scenario`, `nodes` (global dict).
- **Responsibility**: Manages the lifecycle of `VirtualNode` instances; streams telemetry to the frontend; handles control requests.
- **Dependencies**: `VirtualNode`, `ThermalModel`, `AirflowModel`, `HumidityModel`, `ModelLoader`.
- **Dependents**: Frontend (via HTTP/WS).

### `backend/simulation/node.py`
- **Purpose**: Orchestrates the physics models and ML inference for a single node.
- **Key Classes/Functions**: `VirtualNode.step()`, `inject_thermal_spike()`.
- **Responsibility**: Coordinates the "physics loop" and feeds the resulting telemetry into the ML pipeline.
- **Dependencies**: `ThermalModel`, `AirflowModel`, `HumidityModel`, `SlidingWindowFeatureExtractor`, `ModelLoader`.
- **Dependents**: `api.py`.

### `backend/ml/model_loader.py`
- **Purpose**: Handles runtime model loading and scoring.
- **Key Classes/Functions**: `ModelLoader.predict()`.
- **Responsibility**: Loads `IsolationForest` and `RobustScaler`; transforms features and returns anomaly scores.
- **Dependencies**: `joblib`, `sklearn`.
- **Dependents**: `VirtualNode`, `api.py`.

### `backend/simulation/thermal_model.py`
- **Purpose**: Physics of heat and cooling.
- **Key Classes/Functions**: `ThermalModel.step()`.
- **Responsibility**: Calculates $T_{next}$ using Newton's Law of Cooling and heat generation from CPU load.

---

## ML Pipeline Architecture

The ML system follows a standard Training → Inference flow:

1.  **Data Generation**: `generate_baseline_data.py` runs the simulation to create "normal" telemetry.
2.  **Preprocessing**: `SlidingWindowFeatureExtractor` transforms raw telemetry into a 12-dimensional feature vector (Mean, Var, ROC for 4 variables) over a 10-step window.
3.  **Training**: `train_hybrid_model.py` uses an `IsolationForest` to learn the boundaries of normal operation.
4.  **Feature Scaling**: A `RobustScaler` is used to normalize features, ensuring outliers don't skew the model during training.
5.  **Inference**: `ModelLoader` executes `model.predict()` on real-time features.
6.  **Integration**: `VirtualNode` calls the model at every simulation step after the window is full.

---

## Anomaly Detection System

Anomalies are handled through three layers:

1.  **Detection**: The `IsolationForest` model flags vectors with an anomaly score below a threshold.
2.  **Persistence**: `VirtualNode` maintains `recent_anomaly_flags`. A "Persistent Anomaly" is reported if any anomaly was detected within the last 20 steps, preventing "flickering" alerts.
3.  **Reporting**: Telemetry sent via WebSocket includes `is_anomaly` (boolean) and `anomaly_score` (float). The Frontend (`AlertsFeed.tsx`) displays alerts when these flags are raised.

**Injection Scenarios**:
- **HVAC Failure**: Controlled via `airflow_model.simulate_fan_failure()`, setting obstruction to 100%.
- **Thermal Spike**: Overrides CPU load to 100% and reduces airflow cooling efficiency for a set duration.

---

## Simulation and Physics System

The simulation utilizes a coupled feedback loop:
- **CPU Load**: Generated via an AR(1) process to simulate realistic volatility.
- **Airflow (HVAC)**: Responds to temperature increases by increasing flow (proportional control).
- **Thermal**: Net heat is $(Heat_{CPU} - Cooling_{Airflow})$. Temperature change is inversely proportional to thermal mass ($mass \times capacity$).
- **Humidity**: Coupled to temperature; as temperature rises, relative humidity drops via a coupling coefficient.

---

## Data Flow

1.  **Input**: API control requests or internal AR(1) CPU load generation.
2.  **Physics**: `Thermal` → `Airflow` → `Humidity` updates in sequence.
3.  **Feature Extraction**: Telemetry is appended to the `SlidingWindow`.
4.  **Inference**: Once 10 points are collected, the `ModelLoader` scores the window.
5.  **Output**: Combined telemetry + ML results are sent via WebSocket to the React Dashboard.
6.  **Visualization**: Gauges and Sparklines update; Alerts are triggered if `is_anomaly` is true.

---

## Test Architecture

The system includes extensive tests in `backend/tests/`:
- **Model Tests**: `test_thermal_model.py`, `test_airflow_model.py`, `test_humidity_model.py` validate physics equations.
- **Integration Tests**: `test_environment_model.py` ensures models interact correctly.
- **ML Tests**: `test_feature_extraction.py`, `test_model_loader.py` verify windowing and inference logic.

---

## Key Files Summary

| File | Role |
| :--- | :--- |
| `backend/api.py` | System orchestrator and communication hub. |
| `backend/simulation/node.py` | Implementation of the virtual node and its lifecycle. |
| `backend/ml/model_loader.py` | Interface for anomaly detection scoring. |
| `app/page.tsx` | Main user interface and real-time visualization. |
| `models/model_v2_hybrid_real.pkl` | The brain of the anomaly detection system. |
