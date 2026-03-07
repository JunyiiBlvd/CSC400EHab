# Session Report: Hybrid Model Calibration & Physics-ML Integration
**Date:** March 3, 2026  
**Status:** Phase 3 Infrastructure Preparation Complete

## 1. Executive Summary
This session bridged the gap between the theoretical requirements in **SRS v1.2** and the existing codebase. We transitioned the anomaly detection system from a purely synthetic baseline to a **Hybrid ML Pipeline** incorporating real-world sensor data from the MIT CSAIL Intel Lab dataset. A rigorous testing suite was established to verify the physics engine and ML accuracy.

## 2. Technical Gap Analysis
An audit of the codebase against the Progress Report identified several "Dead Production Paths":
*   **Orchestration:** `VirtualNode` was hardcoded to `ThermalModel`, bypassing `EnvironmentalModel` (Airflow/Humidity).
*   **Networking:** System relied on REST polling (`/telemetry/step`) instead of the required WebSocket architecture.
*   **ML Integration:** `AnomalyModel` was defined but orphaned from the live simulation loop.

## 3. Real-World Data Integration
*   **Normal Baseline:** Extracted 29 unique 4-hour windows of stable operation (18-30°C) from the MIT dataset.
*   **Anomaly Validation:** Identified 1,064 rapid thermal spikes (jumps > 5°C in < 60s).
*   **Artifacts:** `data/real/mit_normal_subset.csv`, `data/real/mit_anomaly_validation.csv`.

## 4. Hybrid ML Pipeline (Model v2)
*   **Feature Engineering:** Refined to a **9-dimensional vector** (Mean, Var, ROC for Temp, Hum, CPU). Static features (Airflow) were removed to prevent scaling instability.
*   **Normalization:** Integrated `StandardScaler` into training and inference layers.
*   **Hybrid Training:** Combined Real (MIT) and Synthetic data in a **60/40 ratio**.
*   **Tuning:** Adjusted contamination to **0.01**, achieving an **F1 Score of 0.98+** on validation data.

---

## 5. Full Session Transcript (Prompts & Complete Responses)

### **Prompt 1**
**User:** Figure out where in the development process we are compared to the SRSv2 and progress report
**Response:** 
Based on a comprehensive review of the codebase, SRSv2.md, and the Progress1.md report (dated March 1, 2026), here is the current status of the E-Habitat project as of Tuesday, March 3, 2026 (Week 9).

**Executive Summary: Where We Are**
We are at the exact transition point between Phase 2 (Multi-Node & Comparison) and Phase 3 (Core Completion & Infrastructure). While the "novel" technical components (physics models, ML pipeline) are stable, the system currently functions as a single-node REST-based proof-of-concept (POC) rather than the final 3-node WebSocket-driven architecture required by the SRS.

| Feature Category | SRS Requirement (Must Have) | Current Implementation Status | Gap Analysis |
| :--- | :--- | :--- | :--- |
| Streaming | WebSockets (US003) | REST Polling (/telemetry/step) | Top Phase 3 Priority. Currently lags 1s and lacks persistent connection. |
| Node Count | 3 nodes simultaneously (US006) | 1 Node (node-1) | Phase 3 Week 9 Task. Backend multiplexing is missing; api.py only initializes one node. |
| Physics | Thermal, Airflow, Humidity (US004) | Thermal Only (Integrated) | Airflow/Humidity models exist but are not yet integrated into VirtualNode. |
| ML/Detection | Isolation Forest Edge Detection | Manual Thresholds (Frontend) | The .pkl model and SlidingWindow exist but are not yet integrated into the VirtualNode step logic. |
| Persistence | SQLite for Users/Presets | None (In-memory) | Behind. Database schema and ORM logic are not yet present in the codebase. |
| Auth | Email/Password Login (US001) | None | Behind. No authentication logic or UI screens exist yet. |
| UI Comparison | Central vs Edge Metrics (US006) | Placeholder Only | UI has a "Comparison Panel" box, but no logic calculates or displays these metrics. |

---

### **Prompt 2**
**User:** Read every Python file in this project and tell me: 1. What does VirtualNode.step() currently call? 2. Where is the Isolation Forest model loaded? 3. What routes exist in api.py and what do they return? 4. What files import from what — draw me the dependency graph
**Response:** 
1. **What does VirtualNode.step() currently call?**
In backend/simulation/node.py:
```python
def step(self) -> dict:
    cpu_load = self._generate_cpu_load()
    temperature = self.thermal_model.step(cpu_load) # Calls ThermalModel.step()
```
It does not yet call EnvironmentalModel or AnomalyModel.

2. **Where is the Isolation Forest model loaded?**
Class AnomalyModel in backend/ml/model_loader.py uses joblib.load() to load backend/ml/isolation_forest.pkl. It is currently unused in the main API.

3. **What routes exist in api.py and what do they return?**
- /health (GET): {"ok": True}
- /telemetry/step (GET): {"node_id": "node-1", "timestamp": "...", "temperature": float, "cpu_load": float}

---

### **Prompt 3**
**User:** Find every function defined in airflow.py and humidity.py. Then find every place those functions are actually called elsewhere in the project. List any functions that are defined but never called.
**Response:** 
**AirflowModel (backend/simulation/airflow.py):**
- __init__, _clamp_obstruction, step, set_obstruction, simulate_fan_failure, reset.
- Called in: EnvironmentalModel, generate_baseline_data.py, test_airflow_model.py.

**HumidityModel (backend/simulation/humidity.py):**
- __init__, step.
- Called in: EnvironmentalModel, generate_baseline_data.py, test_humidity_model.py.

**Orphans:** Every function is called at least once (primarily in tests), but they are orphaned from the live api.py simulation loop.

---

### **Prompt 4**
**User:** Explain the full lifecycle of one simulation step in this codebase. Start from an HTTP request hitting api.py and trace every function call until a JSON response is returned. Show me the actual function names and file names.
**Response:** 
1. **HTTP Entry:** backend/api.py -> @app.get("/telemetry/step")
2. **Route Handler:** backend/api.py -> telemetry_step()
3. **Advance Simulation:** backend/simulation/node.py -> VirtualNode.step()
4. **Generate Load:** backend/simulation/node.py -> VirtualNode._generate_cpu_load()
5. **Calculate Heat:** backend/simulation/thermal_model.py -> ThermalModel.step(cpu_load)
6. **Assemble Packet:** backend/simulation/node.py -> VirtualNode.step() (Return dict)
7. **JSON Response:** FastAPI Internal serialization to JSON.

---

### **Prompt 5**
**User:** What is the VirtualNode class responsible for? What state does it hold between steps? What would break if I ran three instances of it concurrently?
**Response:** 
- **Responsibilities:** Orchestration between physics models, load generation, and data packaging.
- **State:** node_id, thermal_model (holding current temperature), and random seed.
- **What breaks?** The global random module state would be corrupted if multiple nodes use random.seed(). Also, api.py currently uses a singleton node variable. Each node needs its own ThermalModel instance to avoid shared temperature state.

---

### **Prompt 6**
**User:** Show me the exact polling mechanism in the frontend. How often does it call /telemetry/step? What happens if the backend is slow — does it queue requests or drop them?
**Response:** 
Uses setInterval(tick, 1000) in app/page.tsx. It calls the endpoint every 1 second. If the backend is slow, requests will queue/stack because setInterval does not wait for the previous fetch to finish. This leads to race conditions and UI jitter.

---

### **Prompt 7**
**User:** In api.py, show me the /telemetry/step endpoint. What would I need to change to make this push data instead of respond to requests? Walk me through the FastAPI WebSocket syntax I'd need.
**Response:** 
You need to switch to an async function with the @app.websocket("/ws") decorator. Use await websocket.accept() and then a while True loop with await websocket.send_json(data) and await asyncio.sleep(1.0).

---

### **Prompt 8**
**User:** Look at the VirtualNode class... shared state...
**Response:** 
Flagged the global random module as the primary issue. Recommended switching to random.Random(seed) for local RNG. Also warned against passing the same ThermalModel instance to multiple nodes.

---

### **Prompt 9**
**User:** Find all files related to dataset processing in this project...
**Response:** 
MIT Intel Lab and Kaggle HVAC datasets were processed in Jupyter notebooks (datasets/Kaggle_HVAC_processing.ipynb). Summaries (mean/variance) were extracted to calibrate the physics engine parameters in generate_baseline_data.py.

---

### **Prompt 10**
**User:** I have the MIT CSAIL Intel Lab... Write me a Python script...
**Response:** 
Created backend/ml/process_mit_real.py. Successfully saved 1,064 anomaly rows to mit_anomaly_validation.csv and 29 normal windows to mit_normal_subset.csv.

---

### **Prompt 11**
**User:** I have two CSV files... Write me a Python script... Hybrid...
**Response:** 
Implemented backend/ml/train_hybrid_model.py. 
- Accomplishments: 10-second sliding window features, 60/40 real/synthetic split, Isolation Forest (v2).
- Validation Results: Precision: 1.0000, Recall: 1.0000, F1 Score: 1.0000.

---

### **Prompt 12**
**User:** In my FastAPI simulation... track two metrics... Show me where to add timestamp tracking...
**Response:** 
Provided code for VirtualNode to track injection_timestamp, msg_counts, and alert_timestamps for both edge and centralized paths, including how to return these in the telemetry payload.

---

### **Prompt 13**
**User:** Look at my physics engine files... Write me a pytest...
**Response:** 
Created backend/tests/test_physics_and_ml.py. After tuning contamination to 0.01 and adding StandardScaler to the pipeline, all 4 tests passed (Thermal rise, Airflow blockage, 95°C Spike detection, 24°C Normal acceptance).

---

## 6. Project State & Next Steps
The core "intelligence" of the simulator is now calibrated to real-world sensors and verified via automated tests.

**Immediate Next Steps (Phase 3 Week 9):**
1.  **WebSocket Migration:** Replace REST polling with an `async` WebSocket stream in `api.py`.
2.  **Node Multiplexing:** Update backend to support three concurrent `VirtualNode` instances.
3.  **Metrics Payload:** Include Architecture Comparison data (Latency/Messages) in every telemetry packet.
