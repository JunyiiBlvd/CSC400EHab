# E-Habitat Architecture Map

> Generated: 2026-03-27 (updated)
> Source: exhaustive static analysis of `/mnt/storage/projects/CSC400EHab/csc400/`

---

## Table of Contents

1. [Directory Tree](#1-directory-tree)
2. [Backend Python Modules](#2-backend-python-modules)
3. [Frontend Files](#3-frontend-files)
4. [API Endpoints](#4-api-endpoints)
5. [WebSocket Events](#5-websocket-events)
6. [Database Operations](#6-database-operations)
7. [Missing and Unused Files](#7-missing-and-unused-files)
8. [Code vs Documentation Discrepancies](#8-code-vs-documentation-discrepancies)

---

## 1. Directory Tree

```
/mnt/storage/projects/CSC400EHab/csc400/
├── app/
│   ├── components/
│   │   ├── AlertsFeed.tsx
│   │   ├── NodeGauges.tsx
│   │   ├── NodeGrid.tsx
│   │   └── Sparkline.tsx
│   ├── lib/
│   │   ├── api.ts
│   │   └── types.ts
│   ├── favicon.ico
│   ├── globals.css
│   ├── layout.tsx
│   └── page.tsx
├── backend/
│   ├── __init__.py
│   ├── api.py
│   ├── test_db.py
│   ├── ml/
│   │   ├── baseline_features.npy
│   │   ├── feature_extraction.py
│   │   ├── generate_baseline_data.py
│   │   ├── isolation_forest.pkl          ← superseded; not loaded at runtime
│   │   ├── model_loader.py
│   │   ├── train_hybrid_model.py
│   │   ├── train_model.py
│   │   └── validate_on_real_anomalies.py
│   ├── simulation/
│   │   ├── __init__.py
│   │   ├── airflow.py
│   │   ├── central_server.py
│   │   ├── database.py
│   │   ├── environment.py                ← unused in runtime; superseded by VirtualNode
│   │   ├── humidity.py
│   │   ├── node.py
│   │   ├── runner.py                     ← CLI only; not imported by api.py
│   │   ├── thermal.py                    ← dead duplicate of thermal_model.py
│   │   └── thermal_model.py
│   └── tests/
│       ├── test_airflow_model.py
│       ├── test_clean_baseline_profile.py
│       ├── test_environment_model.py
│       ├── test_feature_extraction.py
│       ├── test_humidity_feasibility.py
│       ├── test_humidity_feature_analysis.py
│       ├── test_hvac_feasibility.py
│       ├── test_hvac_ramp_feasibility.py
│       ├── test_humidity_model.py
│       ├── test_model_loader.py
│       ├── test_thermal.py
│       └── test_thermal_model.py
├── data/
│   ├── real/
│   │   ├── cold_source_features.csv
│   │   ├── mit_anomaly_validation.csv
│   │   ├── mit_features.csv
│   │   └── validation_results.txt
│   └── synthetic/
│       └── normal_telemetry.csv
├── datasets/
│   ├── HVAC_Kaggle.csv
│   ├── Kaggle_HVAC_processing.ipynb
│   ├── MIT_dataset.csv
│   └── MIT_Dataset_Proceessing.ipynb
├── db/
│   └── ehabitat.db                       ← SQLite runtime database
├── Docs/
│   ├── 03_24_2026_SRS.md
│   ├── application_architecture.md
│   ├── Baseline_Data_Generation.md
│   ├── branch-ai-summary.md
│   ├── branch-ml-pipeline-summary.md
│   ├── CSC400 SRS(1).docx
│   ├── Edge_Anomaly_Detection_Architecture.md
│   ├── Isolation_Forest_Training.md
│   ├── MIGRATION_LOG.md
│   ├── ML_Feature_Extraction.md
│   ├── Model_Runtime_Inference.md
│   ├── Session-Summary-3_23_26.md
│   ├── Session-Summary-3_23_26_P2.md
│   ├── SRS.md
│   ├── Thermal_Spike_Scenario.md
│   ├── Week1_Implementation_Summary.md
│   ├── Week_2.1_Implementation_Summary.md
│   ├── Week_2.2_Implementation_Summary.md
│   ├── Week_2.3_PsyEngine_Writeup
│   └── Week2_Implementation_Summary.md
├── models/
│   ├── model_v2_hybrid_real.pkl           ← active runtime model (1.9 MB)
│   └── scaler_v2.pkl                      ← active runtime scaler (695 B)
├── public/
│   ├── file.svg
│   ├── globe.svg
│   ├── next.svg
│   ├── vercel.svg
│   └── window.svg                         ← all default Next.js scaffolding; unused
├── scripts/
│   └── generatebranchdocs.sh
├── audit_datasets.py                      ← root-level diagnostic scripts (all unused)
├── check_stats.py
├── check_stats_simple.py
├── CLAUDE.md
├── create_features.py
├── debug_correlation.py
├── diagnose.py
├── eslint.config.mjs
├── feature_report.csv
├── GEMINI.md
├── generate_real_features.py
├── next-env.d.ts
├── next.config.ts
├── package.json
├── package-lock.json
├── postcss.config.mjs
├── pyproject.toml
├── README.md
├── recreate_anomalies.py
├── requirements.txt
├── task1_diag.py
├── test_airflow_physics.py
├── tsconfig.json
├── verify_coupling.py
├── verify_persistence.py
├── verify_physics_spike.py
└── verify_thermal_fix.py
```

---

## 2. Backend Python Modules

---

### `backend/api.py`

**Purpose:** Core FastAPI server. Instantiates all simulation nodes, ML models, and the database at startup. Runs the real-time WebSocket simulation loop. Provides all REST control endpoints. Coordinates edge vs central anomaly detection and persists results to SQLite.

#### Module-Level State

| Name | Type | Value / Description |
|---|---|---|
| `app` | `FastAPI` | Application instance; CORS allows `http://localhost:3000` |
| `nodes` | `Dict[str, VirtualNode]` | 3 nodes created at startup: `node-1`, `node-2`, `node-3` |
| `_central_model` | `ModelLoader` | Shared singleton used by `CentralServer` |
| `central_server` | `CentralServer` | Centralized anomaly detector (uses `_central_model`) |
| `_prev_edge_anomaly` | `Dict[str, bool]` | Last-known edge anomaly state per node (transition detection) |
| `_prev_central_detection` | `Dict[str, bool]` | Last-known central anomaly state per node |
| `_step_seq` | `Dict[str, int]` | Monotonic sequence counter per node; increments each WebSocket frame |
| `NODE_SEEDS` | `dict` | `{"node-1": 42, "node-2": 43, "node-3": 44}` |
| `NODE_TEMPS` | `dict` | `{"node-1": 21.0, "node-2": 22.0, "node-3": 21.5}` |

`init_db()` is called at module import time.

#### Classes

**`NodeTargetRequest(BaseModel)`**
- `node_id: str`

**`AirflowObstructionRequest(NodeTargetRequest)`**
- `node_id: str`
- `ratio: float`

**`HumiditySetRequest(NodeTargetRequest)`**
- `node_id: str`
- `humidity: float`

#### Functions

**`make_node(node_id, seed, initial_temp) → VirtualNode`**
- Constructs one VirtualNode with all sub-models:
  - `ThermalModel(air_mass=10, heat_capacity=1005, heat_coefficient=300, cooling_coefficient=150, initial_temperature=initial_temp)`
  - `AirflowModel(nominal_flow=2.5, seed=seed+1000)`
  - `HumidityModel(initial_humidity=45, drift=0.0, noise_amplitude=0.5, seed=seed+2000)`
  - `ModelLoader(model_path="models/model_v2_hybrid_real.pkl", scaler_path="models/scaler_v2.pkl")`
- Node random seed: `seed+3000`

**`reload_models() → (bool, str | None)`**
- Creates a new `ModelLoader` instance for every node
- Returns `(True, None)` on success; `(False, error_message)` on failure

**`GET /health`**
- Returns `{"ok": True, "nodes": ["node-1", "node-2", "node-3"]}`

**`GET /api/ml/status`**
- Reads `anomaly_model` fields from `nodes["node-1"]` only (assumes all nodes in sync)
- Returns: `{model_loaded, model_path, model_load_error, window_size, window_ready, points_in_window}`

**`POST /api/ml/reload`**
- Calls `reload_models()`
- Returns `{ok: bool, model_loaded: bool, error: str | None}`

**`POST /api/controls/airflow_obstruction`** — body: `AirflowObstructionRequest`
- `nodes[node_id].airflow_model.set_obstruction(ratio)`
- Returns `{ok, node_id, obstruction_ratio}`

**`POST /api/controls/fan_failure`** — body: `NodeTargetRequest`
- `nodes[node_id].inject_hvac_failure(duration_seconds=40)` — ramped HVAC failure (not instant snap)
- `central_server.record_injection(node_id, time.time())` — required so latency is measurable
- Returns `{ok, node_id, obstruction_ratio: 1.0}`

**`POST /api/controls/reset_airflow`** — body: `NodeTargetRequest`
- `nodes[node_id].airflow_model.reset()`
- Returns `{ok, node_id, obstruction_ratio: 0.0}`

**`POST /api/controls/set_humidity`** — body: `HumiditySetRequest`
- Sets `nodes[node_id].humidity_model.current_humidity = humidity`
- Also resets `nodes[node_id].humidity_model.initial_humidity = humidity` (resets mean-reversion target)
- Returns `{ok, node_id, humidity}`

**`GET /central/status`**
- Calls `central_server.get_status()`
- Returns `{"ok": True, "nodes": {...}}`

**`GET /db/anomaly_summary`**
- Runs SQL aggregation over `anomaly_events` table
- Groups by `detection_source`; returns averages for latency and delta metrics

**`GET /db/history/events`**
- Calls `get_anomaly_events()` → all rows from `anomaly_events`, ordered by `injection_timestamp DESC`
- Returns `{ok: True, events: [...]}`

**`GET /db/history/telemetry`** — query params: `node_id: str`, `start: float`, `end: float` (all required)
- Returns `400` if any param missing
- Calls `get_telemetry_range(node_id, start, end)` → telemetry rows in `[start, end]` ordered ASC
- Returns `{ok: True, rows: [...]}`

**`WebSocket /ws/simulation`** — PRIMARY SIMULATION LOOP
- Accepts connection, enters `while True:` with `asyncio.sleep(1.0)` per iteration
- Per iteration, for each node:
  1. Increment `_step_seq[node_id]`
  2. `raw = node.step()` → telemetry dict
  3. `insert_telemetry({seq_id, node_id, timestamp, temperature, humidity, airflow, cpu_load, is_anomaly, anomaly_score})`
  4. If `raw["is_anomaly"]` is True and `_prev_edge_anomaly[node_id]` was False (False→True transition):
     - Record `edge_detection_ts = time.time()`
     - `insert_anomaly_event({..., detection_source: "edge", ...})`
  5. `central_server.receive_telemetry(node_id, {temperature, humidity, airflow, cpu_load}, seq_id, edge_detection_ts, bytes_edge)`
  6. If central persistent anomaly transitions False→True:
     - `insert_anomaly_event({..., detection_source: "central", ...})`
  7. Assemble and send JSON frame to client
- Catches `WebSocketDisconnect` (clean exit) and generic `Exception` (logged, socket closed)

**`POST /simulation/inject?node_id=&scenario=`**
- `"hvac_failure"` → `node.inject_hvac_failure(duration_seconds=40)` + `central_server.record_injection()`
  - Ramped: airflow linearly drops over 15 steps, holds at 0 for remainder. Profiled 2026-03-27, confirmed detectable.
- `"thermal_spike"` → `node.inject_thermal_spike()` + `central_server.record_injection()`
- `"coolant_leak"` → `node.inject_coolant_leak()` + `central_server.record_injection()`
  - Humidity rises 2.5% RH/step for 20 steps, capped at 85.0 % RH
- `"reset"` → `airflow_model.reset()` + `node.reset_anomaly_state()`
- Returns `{status, node, scenario}` on success or `{error}` if node_id unknown

**Imports:** `fastapi`, `fastapi.responses.JSONResponse`, `starlette.websockets`, `asyncio`, `time`, `json`, `typing.Optional`, and all backend simulation/ml modules
**Imported by:** nothing (entry point via `uvicorn`)

---

### `backend/simulation/database.py`

**Purpose:** SQLite persistence layer. Creates schema on first run. Inserts telemetry rows and anomaly event rows.

#### Module-Level State

| Name | Value |
|---|---|
| `DB_DIR` | `Path("db")` |
| `DB_PATH` | `Path("db/ehabitat.db")` |

#### Functions

**`init_db()`**
- `DB_DIR.mkdir(parents=True, exist_ok=True)`
- Creates `telemetry` table if not exists:
  - `id INTEGER PRIMARY KEY, seq_id INTEGER, node_id TEXT, timestamp REAL, temperature REAL, humidity REAL, airflow REAL, cpu_load REAL, is_anomaly INTEGER, anomaly_score REAL`
- Creates `anomaly_events` table if not exists:
  - `id INTEGER PRIMARY KEY, seq_id INTEGER, node_id TEXT, injection_timestamp REAL, edge_detection_ts REAL, central_detection_ts REAL, edge_latency_ms REAL, central_latency_ms REAL, detection_source TEXT, bytes_edge INTEGER, bytes_central INTEGER`
- Creates indices: `idx_telemetry_timestamp` (on `timestamp`), `idx_telemetry_node_id` (on `node_id`)

**`insert_telemetry(record: dict)`**
- Parameterized `INSERT INTO telemetry` (`:param` syntax — SQL-injection safe)
- Expected keys: `seq_id, node_id, timestamp, temperature, humidity, airflow, cpu_load, is_anomaly, anomaly_score`
- On exception: `print(f"DB write error: {e}")` — silent, does not re-raise

**`insert_anomaly_event(record: dict)`**
- Parameterized `INSERT INTO anomaly_events`
- Expected keys: `seq_id, node_id, injection_timestamp, edge_detection_ts, central_detection_ts, edge_latency_ms, central_latency_ms, detection_source, bytes_edge, bytes_central`
- On exception: silent print, does not re-raise

**`get_anomaly_events() → list`**
- `SELECT * FROM anomaly_events ORDER BY injection_timestamp DESC`
- Uses `sqlite3.Row` as row factory → returns `list[dict]`
- On exception: prints error and returns `[]`

**`get_telemetry_range(node_id: str, start: float, end: float) → list`**
- `SELECT * FROM telemetry WHERE node_id = ? AND timestamp >= ? AND timestamp <= ? ORDER BY timestamp ASC`
- Uses `sqlite3.Row` as row factory → returns `list[dict]`
- On exception: prints error and returns `[]`

Uses `check_same_thread=False` on all connections (safe for async FastAPI).

**Imports:** `sqlite3`, `pathlib.Path`
**Imported by:** `backend/api.py` (`init_db`, `insert_telemetry`, `insert_anomaly_event`, `get_anomaly_events`, `get_telemetry_range`, `DB_PATH`)

---

### `backend/simulation/node.py`

**Purpose:** Single virtual compute node. Orchestrates per-step physics (thermal → airflow → humidity) and ML inference. Applies 20-step anomaly persistence.

#### Module-Level State

None.

#### Class: `VirtualNode`

**Constructor parameters:** `node_id, thermal_model, airflow_model, humidity_model, random_seed=None`

**Instance variables:**

| Variable | Type | Initial Value | Description |
|---|---|---|---|
| `node_id` | `str` | from arg | Node identifier |
| `thermal_model` | `ThermalModel` | from arg | Temperature physics |
| `airflow_model` | `AirflowModel` | from arg | HVAC airflow physics |
| `humidity_model` | `HumidityModel` | from arg | Humidity physics |
| `rng` | `random.Random` | seeded | Node-level RNG |
| `spike_remaining_steps` | `int` | `0` | Steps remaining in thermal spike |
| `cpu_load_override` | `float \| None` | `None` | Fixed CPU load during spike |
| `hvac_lag_steps` | `int` | `0` | Steps HVAC remains frozen (thermal spike path) |
| `_frozen_airflow` | `float \| None` | `None` | Airflow locked during HVAC lag |
| `hvac_failure_remaining_steps` | `int` | `0` | Steps remaining in ramped HVAC failure |
| `hvac_failure_total_steps` | `int` | `0` | Total duration of active HVAC failure |
| `coolant_leak_active` | `bool` | `False` | Whether a coolant leak is in progress |
| `coolant_leak_remaining_steps` | `int` | `0` | Steps remaining in the leak ramp |
| `coolant_leak_base_humidity` | `float` | `0.0` | Humidity value at leak injection time |
| `recent_anomaly_flags` | `deque` | `deque(maxlen=20)` | Rolling anomaly flag window |
| `anomaly_persistence_steps` | `int` | `20` | Persistence window length |
| `cpu_load_state` | `float` | `0.5` | AR(1) process state |
| `feature_extractor` | `SlidingWindowFeatureExtractor` | window_size=10 | Feature accumulator |
| `anomaly_model` | `ModelLoader` | from make_node | IsolationForest + scaler |

**Methods:**

**`reset_anomaly_state()`**
- Clears `recent_anomaly_flags`
- Replaces `feature_extractor` with a fresh instance

**`inject_thermal_spike(duration_seconds=120, lag_seconds=40)`**
- `cpu_load_override = 1.0`
- `spike_remaining_steps = duration_seconds`
- `hvac_lag_steps = lag_seconds`
- `_frozen_airflow = airflow_model.current_flow * 0.15`

**`inject_hvac_failure(duration_seconds=40)`**
- Sets `hvac_failure_remaining_steps = duration_seconds` and `hvac_failure_total_steps = duration_seconds`
- In `step()`: linearly ramps airflow down to 0 over the first 15 steps (`ramp_ratio = min(1.0, elapsed/15)`), then holds at 0 for the remainder
- Keeps `air_roc` non-zero for ~25 steps, making the anomaly signal detectable by the sliding window extractor
- Profiled 2026-03-27 (`test_hvac_ramp_feasibility.py`): 15-step anomaly streak, min score 0.073 (threshold 0.15)

**`inject_coolant_leak()`**
- Sets `coolant_leak_active = True`, `coolant_leak_remaining_steps = 20`, `coolant_leak_base_humidity = humidity_model.current_humidity`
- In `step()` (applied after physics, before ML): humidity overridden to `min(85.0, base + 2.5 * (20 - remaining_steps))`
  - Ramps for 20 steps (+2.5% RH/step from base), then holds at `min(85.0, base + 50.0)`

**`_generate_cpu_load() → float`**
- If `spike_remaining_steps > 0`: decrement counter, return `cpu_load_override`
- Else: AR(1) — `cpu_load_state = 0.95 * cpu_load_state + 0.05 * 0.5 + rng.gauss(0, 0.02)`, clamped to `[0.1, 0.9]`
- If spike just exhausted: clears `cpu_load_override = None`

**`step() → dict`**
1. `cpu_load = _generate_cpu_load()`
2. Airflow (priority order):
   - If `hvac_failure_remaining_steps > 0`: compute `ramp_ratio = min(1.0, elapsed/15.0)`, set `airflow_model.current_flow = nominal_flow * (1 - ramp_ratio)`, decrement counter
   - Elif `hvac_lag_steps > 0`: use `_frozen_airflow`, decrement counter (thermal spike HVAC lag path)
   - Else: `airflow_model.step(temperature=last_temp)`
3. `airflow_ratio = current_airflow / airflow_model.nominal_flow`
4. `new_temp = thermal_model.step(cpu_load, airflow_ratio=airflow_ratio)`
5. `humidity = humidity_model.step(temperature=new_temp)`
6. Coolant leak override (if active): replaces `humidity` with ramped value before ML inference
7. `feature_extractor.add_point({temperature, airflow, humidity, cpu_load})`
7. If window ready: `result = anomaly_model.predict(feature_extractor.extract_features())`; else `{anomaly_score: None, is_anomaly: None}`
8. `recent_anomaly_flags.append(result["is_anomaly"])`
9. `persistent_anomaly = any(f is True for f in recent_anomaly_flags)`
10. Returns `{node_id, timestamp (ISO 8601 UTC), temperature, humidity, airflow, cpu_load, obstruction_ratio, anomaly_score, is_anomaly: persistent_anomaly}`

**Imports:** `ThermalModel, AirflowModel, HumidityModel, SlidingWindowFeatureExtractor, ModelLoader`
**Imported by:** `backend/api.py`

---

### `backend/simulation/central_server.py`

**Purpose:** Replicates ML inference on raw telemetry only (no pre-computed anomaly fields). Measures the latency delta between edge detection and central detection. Tracks byte counts for bandwidth comparison.

#### Module-Level State

None.

#### Class: `CentralServer`

**Constructor:** `__init__(self, model: ModelLoader)`

**Instance variables:**

| Variable | Type | Description |
|---|---|---|
| `_model` | `ModelLoader` | Shared model reference from api.py |
| `_extractors` | `Dict[str, SlidingWindowFeatureExtractor]` | Per-node feature windows |
| `_anomaly_flags` | `Dict[str, deque]` | Per-node rolling anomaly flags (maxlen=20) |
| `_prev_persistent` | `Dict[str, bool]` | Previous persistent anomaly state per node |
| `_records` | `Dict[str, dict]` | Per-node tracking: injection_ts, edge_detection_ts, edge_latency_ms, central_detection_ts, central_latency_ms, latency_delta_ms, bytes_edge, bytes_central, last_updated |

`ANOMALY_PERSISTENCE_STEPS = 20`

**Methods:**

**`_ensure_node(node_id)`**
- Lazy-initializes extractor, flag deque, `_prev_persistent`, and `_records` entry on first call for a node

**`receive_telemetry(node_id, raw_telemetry, seq_id, edge_detection_ts, bytes_edge=None)`**
- `_records[node_id]["bytes_central"] += len(json.dumps(raw_telemetry).encode())`
- `_records[node_id]["bytes_edge"] = bytes_edge`
- `extractor.add_point(raw_telemetry)`
- If window ready:
  - `result = model.predict(extractor.extract_features())`
  - Appends `result["is_anomaly"]` to `_anomaly_flags[node_id]`
  - `persistent = any(f is True for f in _anomaly_flags[node_id])`
  - If False→True transition:
    - `central_detection_ts = time.time()`
    - Calculates and stores `central_latency_ms` and `latency_delta_ms`
  - Updates `_prev_persistent[node_id]`

**`record_injection(node_id, injection_ts)`**
- Stores `injection_ts` for latency calculation

**`get_status() → Dict[str, Any]`**
- Returns per-node dict for all known nodes:
  - `edge_detection_ts, central_detection_ts, edge_latency_ms, central_latency_ms, latency_delta_ms, bytes_edge, bytes_central, last_updated`

**Note on `bytes_central` vs `bytes_edge`:** `bytes_central` is a running cumulative total; `bytes_edge` is a snapshot of one frame size at detection time. They measure different things.

**Imports:** `json, time, SlidingWindowFeatureExtractor, ModelLoader`
**Imported by:** `backend/api.py`

---

### `backend/simulation/thermal_model.py`

**Purpose:** Newton's Law of Cooling physics model for compute rack temperature.

#### Class: `ThermalModel`

**Constructor:** `air_mass, heat_capacity, heat_coefficient, cooling_coefficient, initial_temperature, ambient_temperature=20.0`
- `self.temperature = initial_temperature`

**`step(cpu_load: float, airflow_ratio: float = 1.0, dt: float = 1.0) → float`**
- `P_heat = heat_coefficient * cpu_load`
- `effective_cooling = cooling_coefficient * airflow_ratio`
- `cooling_power = effective_cooling * (temperature - ambient_temperature)`
- `thermal_mass = air_mass * heat_capacity` (guard: if 0, return unchanged)
- `temperature += (P_heat - cooling_power) / thermal_mass * dt`
- Returns `self.temperature`

**Imports:** None
**Imported by:** `node.py`, `api.py`

---

### `backend/simulation/airflow.py`

**Purpose:** HVAC airflow model with proportional temperature feedback, obstruction, and Gaussian noise.

#### Class: `AirflowModel`

**Constructor:** `nominal_flow, obstruction_ratio=0.0, random_seed=None`
- `self.current_flow = nominal_flow * (1 - obstruction_ratio)`
- `self.rng = random.Random(random_seed)`

**`step(temperature: float = 21.0) → float`**
- `target_nominal = nominal_flow * (1 - obstruction_ratio)`
- `hvac_response = 0.05 * (temperature - 20.88)` — fans ramp up ~5% per 1°C above setpoint
- `noise = rng.gauss(0.0, 0.08)`
- `current_flow = max(0.0, target_nominal + hvac_response + noise)`
- Returns `current_flow`

**`set_obstruction(ratio: float)`** — clamps to [0,1], updates `current_flow`

**`simulate_fan_failure()`** — `set_obstruction(1.0)`

**`reset()`** — `set_obstruction(0.0)`

**Imports:** `random`
**Imported by:** `node.py`, `api.py`

---

### `backend/simulation/humidity.py`

**Purpose:** % RH model with mean-reversion, temperature coupling, drift, and bounded noise.

#### Class: `HumidityModel`

**Constructor:** `initial_humidity, drift=0.0, noise_amplitude=0.5, random_seed=None, reference_temp=21.0`
- `self.current_humidity = initial_humidity`
- `self.initial_humidity = initial_humidity` (mean-reversion target)

**`step(temperature: float = None) → float`**
- `noise = uniform(-noise_amplitude, noise_amplitude)`
- `coupling_drift = -0.3 * (temperature - reference_temp) * 0.01` if temperature provided else `0.0`
  - Interpretation: +1°C above setpoint → −0.003% RH per step
- `reversion = -0.05 * (current_humidity - initial_humidity)` — pulls toward initial
- `current_humidity += drift + reversion + coupling_drift + noise`
- Clamped to `[0, 100]`
- Returns `current_humidity`

**Imports:** `random`
**Imported by:** `node.py`, `api.py`

---

### `backend/simulation/thermal.py`

**Purpose:** Exact duplicate of `thermal_model.py`. **Never imported in the runtime path.**
Only reference: `backend/tests/test_thermal.py`.
Status: dead code.

---

### `backend/simulation/environment.py`

**Purpose:** `EnvironmentalModel` — composition wrapper around Thermal + Airflow + Humidity.
**Never instantiated in runtime.** Superseded by `VirtualNode` (which adds ML inference).
Only reference: `backend/tests/test_environment_model.py`.

#### Class: `EnvironmentalModel`

**Constructor:** `thermal_model, airflow_model, humidity_model`

**`step(cpu_load: float) → dict`**
- Returns `{temperature, airflow, humidity}` — no ML inference, no anomaly fields

---

### `backend/simulation/runner.py`

**Purpose:** CLI runner for a single-node offline simulation. Writes CSV output.

**Not imported by `api.py`.** Not part of the runtime path.

**`run_simulation(duration, seed=None, output_file=None, fast_mode=False)`**
- Creates VirtualNode with seeds `seed`, `seed+1000`, `seed+2000`, `seed+3000`
- Loops `duration` steps; optionally writes telemetry to CSV

**`main()`** — Argparse entry: `--duration` (required), `--seed`, `--output`

---

### `backend/ml/feature_extraction.py`

**Purpose:** Extracts 12 statistical features from a 10-point sliding window of telemetry.

#### Class: `SlidingWindowFeatureExtractor`

**Constructor:** `window_size=10`
- `self.window = deque(maxlen=window_size)`
- `self.variables = ['temperature', 'airflow', 'humidity', 'cpu_load']`

**`add_point(data: dict)`** — Appends dict to window; auto-evicts oldest when full

**`is_window_ready() → bool`** — `len(window) == window_size`

**`extract_features() → list[float]`**
- For each variable in fixed order `[temperature, airflow, humidity, cpu_load]`:
  - `vals = [point[var] for point in window]`
  - `mean = np.mean(vals)`
  - `variance = np.var(vals)`
  - `rate_of_change = vals[-1] - vals[0]` (not a derivative; endpoint difference)
- Returns 12 floats in order: `[T_mean, T_var, T_roc, Air_mean, Air_var, Air_roc, Hum_mean, Hum_var, Hum_roc, CPU_mean, CPU_var, CPU_roc]`

**Imports:** `collections.deque`, `numpy`
**Imported by:** `node.py`, `central_server.py`

---

### `backend/ml/model_loader.py`

**Purpose:** Loads `IsolationForest` + `RobustScaler` from disk via joblib. Exposes `predict()`.

#### Class: `ModelLoader`

**Constructor:** `model_path="models/model_v2_hybrid_real.pkl", scaler_path="models/scaler_v2.pkl"`
- Raises `FileNotFoundError` if either file is missing
- Loads both files via `joblib.load()`
- Prints `model.offset_` at load time (decision threshold ≈ −0.6134)
- Sets: `model_loaded=True`, `model_path`, `model_load_error=None`, `window_size=10`, `window_ready=False`, `points_in_window=0`

**`predict(feature_vector: List[float]) → Dict[str, Any]`**
- `scaled = scaler.transform([feature_vector])`
- `score = float(model.decision_function(scaled)[0])`
- `is_anomaly = float(score) < 0.15` — **custom threshold, not `model.offset_`**
  - Profiled 2026-03-27 (`test_clean_baseline_profile.py`): clean baseline floor = 0.2275 (11σ above threshold)
  - HVAC failure minimum detectable score: 0.082; Coolant leak minimum: 0.070
  - Avoids retraining while enabling detection of the new ramped and coolant scenarios
- Returns `{"anomaly_score": score, "is_anomaly": is_anomaly}`

**Module-level alias:** `AnomalyModel = ModelLoader` (backward compatibility)

**Imports:** `joblib`, `sklearn` (used at load time only)
**Imported by:** `node.py`, `api.py` (per-node instances), `central_server.py` (shared singleton)

---

### `backend/ml/` — Offline Training Scripts

These files are used to produce `models/model_v2_hybrid_real.pkl` and `models/scaler_v2.pkl`. **Not imported or executed by `api.py` at runtime.**

| File | Purpose |
|---|---|
| `generate_baseline_data.py` | Generates synthetic normal telemetry CSV |
| `train_model.py` | Trains initial IsolationForest on synthetic data only |
| `train_hybrid_model.py` | Retrains on hybrid dataset (synthetic + real MIT data) → produces active model |
| `validate_on_real_anomalies.py` | Validates model against labeled anomaly data in `data/real/` |
| `baseline_features.npy` | Generated artifact from `generate_baseline_data.py`; not loaded at runtime |

---

### `backend/tests/` — Unit and Integration Tests

12 pytest files. **Not imported at runtime.** Offline-only.

| File | Coverage |
|---|---|
| `test_thermal_model.py` | ThermalModel.step() — heating, cooling, equilibrium |
| `test_airflow_model.py` | AirflowModel — feedback response, fan failure, obstruction |
| `test_humidity_model.py` | HumidityModel — coupling, reversion, noise bounds |
| `test_thermal.py` | Duplicate test for the dead `thermal.py` module |
| `test_environment_model.py` | EnvironmentalModel composition (unused in runtime) |
| `test_feature_extraction.py` | SlidingWindowFeatureExtractor — 12-feature shape and values |
| `test_model_loader.py` | ModelLoader.predict() — output shape, is_anomaly type, score range |
| `test_clean_baseline_profile.py` | Profiles normal score distribution; establishes 0.2275 floor used for threshold selection |
| `test_humidity_feasibility.py` | Feasibility check — humidity signal detectability under normal conditions |
| `test_humidity_feature_analysis.py` | Detailed feature analysis of humidity signal across window fills |
| `test_hvac_feasibility.py` | Validates that HVAC anomaly signal is detectable by the current model |
| `test_hvac_ramp_feasibility.py` | Profiles `inject_hvac_failure()` ramp; confirms 15-step anomaly streak, min score 0.073 |

---

### `backend/test_db.py`

Manual smoke test for database schema and insert operations. Not integrated into the pytest suite in `backend/tests/`. Not called at startup.

---

## 3. Frontend Files

---

### `app/page.tsx`

**Purpose:** Root page component. Owns all application state. Renders the full dashboard: header, sidebar controls, node gauges, alerts feed, central/edge comparison panel, and node grid.

#### New Types (defined in `page.tsx`, not `types.ts`)

```ts
AnomalyEvent {
  id: number
  seq_id: number
  node_id: string
  injection_timestamp: number | null
  edge_detection_ts: number | null
  central_detection_ts: number | null
  edge_latency_ms: number | null
  central_latency_ms: number | null
  detection_source: string | null
  bytes_edge: number | null
  bytes_central: number | null
}

SummaryRow {
  detection_source: string | null
  sample_count: number
  avg_edge_ms: number | null
  avg_central_ms: number | null
  avg_delta_ms: number | null
  min_delta_ms: number | null
  max_delta_ms: number | null
}
```

#### `HistoryTab` Component (defined in `page.tsx`)

**Purpose:** Standalone component rendered in the History tab. Shows all recorded anomaly events from the DB plus aggregate stats.

**State:** `events: AnomalyEvent[]`, `summary: SummaryRow | null`, `loading: boolean`, `fetchError: string | null`

**Fetches on mount** (via `useEffect`):
- `GET /db/history/events` → populates `events`
- `GET /db/anomaly_summary` → populates `summary` (first row only)

**Refresh button** triggers `fetchEvents()` manually.

**Renders:**
- 6 stat cards: Total Events, Avg Edge Latency, Avg Central Latency, Avg Delta, Min Delta, Max Delta
- If no events: "No anomaly events recorded yet" message
- MUI `Table` with columns: Node ID, Detection Source, Injection Time, Edge Latency (ms), Central Latency (ms), Delta (ms), Bytes Edge, Bytes Central
- Inline fetches — not wrapped in `api.ts`

#### State Variables

| Variable | Type | Initial Value | Purpose |
|---|---|---|---|
| `telemetryByNode` | `TelemetryByNode` | `{}` | Latest telemetry per node |
| `apiError` | `string \| null` | `null` | WebSocket error message |
| `selectedNodeId` | `string` | `"node-1"` | Node shown in gauges and controls |
| `historyByNode` | `HistoryByNode` | `{}` | Rolling 300-point history per node |
| `alerts` | `AlertItem[]` | `[]` | Alert feed; max 10 items |
| `controlsError` | `string \| null` | `null` | Error from any REST control call |
| `mlStatus` | `MlStatus \| null` | `null` | ML model status |
| `mlError` | `string \| null` | `null` | Error from ML status polling |
| `obstructionDraftByNode` | `Record<string, number>` | `{}` | Obstruction slider in-progress value |
| `humidityDraftByNode` | `Record<string, number>` | `{}` | Humidity slider in-progress value |
| `draggingObstructionNodeId` | `string \| null` | `null` | Locks obstruction slider from WS updates |
| `draggingHumidityNodeId` | `string \| null` | `null` | Locks humidity slider from WS updates |
| `centralStatus` | `Record<string, CentralNodeStatus>` | `{}` | Central vs edge latency/bandwidth data |
| `activeTab` | `number` | `0` | Selected tab index (0 = Live, 1 = History) |
| `prevMlReady` (ref) | `boolean` | `false` | Tracks ML window_ready transition |
| `prevAnomalyRef` (ref) | `Record<string, boolean>` | `{}` | Tracks per-node anomaly state transition |

#### `useEffect` Hooks

**Hook 1 — WebSocket Connection** (deps: `[]`, runs once on mount)
- Connects to `ws://localhost:8000/ws/simulation`
- `onopen`: clears `apiError`
- `onmessage`:
  - Parses JSON frame `Record<string, Telemetry>`
  - Timestamp normalization: if `typeof timestamp === "number"`, converts via `new Date(ts * 1000).toISOString()`; else uses string as-is
  - Updates `telemetryByNode`
  - Appends to `historyByNode`, slices to last 300 points per node
  - Syncs `obstructionDraftByNode` and `humidityDraftByNode` from incoming data — only if that node is not currently being dragged
  - Clears `apiError`
- `onerror`: sets `apiError = "WebSocket connection error"`
- `onclose`: sets `apiError = "WebSocket disconnected, reconnecting..."`, schedules reconnect after 2000 ms
- Cleanup: cancels reconnect timer, closes socket

**Hook 2 — ML Status Polling** (deps: `[]`, polls every 3000 ms)
- Calls `fetchMlStatus()` → `GET /api/ml/status`
- On success: sets `mlStatus`, clears `mlError`
- If `mlStatus?.window_ready` was false and new value is true:
  - Generates alert: `{level: "info", message: "ML model window ready — anomaly detection active"}`
- Updates `prevMlReady.current`
- On error: sets `mlError`
- Cleanup: clears interval

**Hook 3 — Anomaly Alert Generation** (deps: `[telemetryByNode]`)
- Runs on every telemetry update
- For each node: if `is_anomaly` transitions False→True:
  - Calls `getAnomalyReason(telemetry)` → human-readable reason string
  - Creates alert: `{id: \`${ts}-${nodeId}\`, level: "crit", message: \`ANOMALY: ${nodeId} — score ${score}\nReason: ${reason}\`}`
  - Prepends to alerts, trims to max 10
- Updates `prevAnomalyRef.current`

**`getAnomalyReason(t: Telemetry) → string`** (inline helper)
- `cpu_load * 100 > 85` → "High CPU load (XX%)"
- `temperature > 21.5` → "Elevated temperature (XX°C)"
- `airflow < 1.25` (nominal × 0.5) → "Critical airflow degradation"
- `airflow < 2.0` (nominal × 0.8) → "Airflow degradation detected"
- `humidity > 55` → "High humidity (XX%)"
- Else → "Multiple sensor readings outside normal range"

**Hook 4 — Central Status Polling** (deps: `[]`, polls every 1000 ms)
- `fetch("http://localhost:8000/central/status")` (inline fetch, not via `api.ts`)
- On success: `setCentralStatus(data.nodes)`
- Silent on error — does not update state on failure
- Cleanup: clears interval

#### API Calls

| Call | Function | Endpoint | Trigger |
|---|---|---|---|
| WebSocket | (direct) | `ws://localhost:8000/ws/simulation` | Mount |
| GET | `fetchMlStatus()` | `/api/ml/status` | Every 3 s |
| GET | inline `fetch` | `/central/status` | Every 1 s |
| POST | `reloadMlModel()` | `/api/ml/reload` | Button click |
| POST | `setAirflowObstruction()` | `/api/controls/airflow_obstruction` | Slider release |
| POST | `simulateFanFailure()` | `/api/controls/fan_failure` | Button click |
| POST | `resetAirflow()` | `/api/controls/reset_airflow` | Button click |
| POST | `setHumidity()` | `/api/controls/set_humidity` | Slider release |
| POST | `injectThermalSpike()` | `/simulation/inject` | Button click |
| POST | inline `fetch` | `/simulation/inject?scenario=coolant_leak` | Button click |

#### Render Structure

```
<Box> full viewport, dark bg, flex column
  <Box> header bar
    Title | ML status chip (ANOMALY / ML Ready / ML Warming) | connection status
  <Tabs> — Tab 0: Live | Tab 1: History
  [Tab 0 — Live]
    <Box> flex row, main content
      <Box> sidebar 320px fixed
        Node selection (3 buttons: node-1, node-2, node-3)
        Obstruction slider (0–100%)
        Fan Failure button
        Reset Airflow button
        Humidity slider (0–100%)
        Thermal Spike button
        Coolant Leak button          ← new
        Reload ML button
        mlError display
        controlsError display
      <Box> right panel, flex grow
        <NodeGauges> for selectedNodeId
        <AlertsFeed>
        Central vs Edge comparison table (latency + bandwidth per node)
        <NodeGrid>
  [Tab 1 — History]
    <HistoryTab> — stat cards + anomaly events table
```

---

### `app/lib/api.ts`

**Purpose:** Typed HTTP client wrappers for all REST endpoints. Base URL `http://localhost:8000` is hardcoded.

| Function | Method | Path | Body / Params | Returns |
|---|---|---|---|---|
| `setAirflowObstruction(nodeId, ratio)` | POST | `/api/controls/airflow_obstruction` | `{node_id, ratio}` | `{ok, node_id, obstruction_ratio}` |
| `simulateFanFailure(nodeId)` | POST | `/api/controls/fan_failure` | `{node_id}` | `{ok, node_id, obstruction_ratio}` |
| `resetAirflow(nodeId)` | POST | `/api/controls/reset_airflow` | `{node_id}` | `{ok, node_id, obstruction_ratio}` |
| `setHumidity(nodeId, humidity)` | POST | `/api/controls/set_humidity` | `{node_id, humidity}` | `{ok, node_id, humidity}` |
| `fetchMlStatus()` | GET | `/api/ml/status` | `cache: "no-store"` | `MlStatus` |
| `reloadMlModel()` | POST | `/api/ml/reload` | — | `{ok, model_loaded, error?}` |
| `injectThermalSpike(nodeId)` | POST | `/simulation/inject` | URLSearchParams `node_id, scenario="thermal_spike"` | `{status, node, scenario}` |

All functions throw on non-2xx responses.

---

### `app/lib/types.ts`

**Purpose:** TypeScript type definitions shared across the frontend.

```ts
Telemetry {
  node_id: string
  timestamp: string          // ISO 8601 (normalized from float by page.tsx)
  temperature: number        // °C
  cpu_load: number           // 0–1
  airflow: number
  humidity: number           // 0–100
  obstruction_ratio: number  // 0–1
  anomaly_score: number | null
  is_anomaly: boolean | null
}

TelemetryByNode = Record<string, Telemetry>

HistoryByNode = Record<string, Telemetry[]>

MlStatus {
  model_loaded: boolean
  model_path: string
  model_load_error: string | null
  window_size: number
  window_ready: boolean
  points_in_window: number
}

AlertItem {
  id: string
  ts: string          // ISO 8601
  level: "info" | "warn" | "crit"
  message: string
}

CentralNodeStatus (inferred from page.tsx usage) {
  edge_detection_ts: number | null
  central_detection_ts: number | null
  edge_latency_ms: number | null
  central_latency_ms: number | null
  latency_delta_ms: number | null
  bytes_edge: number | null
  bytes_central: number
  last_updated: number | null
}
```

---

### `app/components/NodeGauges.tsx`

**Purpose:** Four MUI Gauge components showing live readings for the selected node.

**Props:** `temperature: number, cpuLoad: number, humidity?: number, airflow?: number, isAnomaly?: boolean, nodeId?: string`

**Renders:**
- Header chip: "ANOMALY" (red) or "Normal" (gray)
- Temperature gauge: range 0–100, label "Temperature (°C)"
- CPU gauge: `cpuLoad * 100`, range 0–100, label "CPU Load (%)"
- Humidity gauge: range 0–100 (only if `humidity` defined)
- Airflow gauge: range 0–1, label "Airflow" (only if `airflow` defined)

**Known issue:** Airflow gauge range is 0–1 but actual values are ~2.3–2.7 (nominal 2.5). The gauge will always peg at or above max for normal operation. See Section 8, item 7.

---

### `app/components/NodeGrid.tsx`

**Purpose:** Three-column card grid — one card per node with current readings and sparklines.

**Props:** `telemetryByNode, apiError, historyByNode, selectedNodeId, onSelectNode`

**Renders:**
- 3 cards for `node-1`, `node-2`, `node-3`
- Each card: T °C, CPU%, humidity, airflow, last update, anomaly chip
- If `history.length > 5`: temperature sparkline and CPU sparkline
- Click → `onSelectNode(nodeId)`; selected card gets highlighted border

---

### `app/components/AlertsFeed.tsx`

**Purpose:** Scrollable color-coded alert feed.

**Props:** `alerts: AlertItem[]`

**Renders:**
- `crit` → `rgba(255,0,0,0.15)` background
- `warn` → `rgba(255,165,0,0.15)` background
- `info` → `rgba(0,150,255,0.15)` background
- Empty state: "No active alerts"
- Container: `max-height: 200px, overflow-y: auto`

---

### `app/components/Sparkline.tsx`

**Purpose:** SVG mini line chart.

**Props:** `points: SparkPoint[]` (`{t: number, v: number}`), `width?: number` (default 220), `height?: number` (default 40)

**Renders:**
- Returns `null` if `points.length < 2`
- Auto-scales x to time range, y to value range
- SVG `<polyline>` with white stroke, no fill

---

### `app/layout.tsx`

**Purpose:** Next.js root layout.

- Metadata: `title: "Create Next App"`, `description: "Generated by create next app"` — placeholder not updated
- Fonts: Geist (sans-serif), Geist_Mono via `next/font/google`
- Body: applies font CSS variables and Tailwind `antialiased`

---

## 4. API Endpoints

### REST Endpoints

| Method | Path | Input | Returns |
|---|---|---|---|
| GET | `/health` | — | `{ok: true, nodes: string[]}` |
| GET | `/api/ml/status` | — | `{model_loaded, model_path, model_load_error, window_size, window_ready, points_in_window}` |
| POST | `/api/ml/reload` | — | `{ok, model_loaded, error}` |
| POST | `/api/controls/airflow_obstruction` | JSON `{node_id, ratio}` | `{ok, node_id, obstruction_ratio}` |
| POST | `/api/controls/fan_failure` | JSON `{node_id}` | `{ok, node_id, obstruction_ratio: 1.0}` |
| POST | `/api/controls/reset_airflow` | JSON `{node_id}` | `{ok, node_id, obstruction_ratio: 0.0}` |
| POST | `/api/controls/set_humidity` | JSON `{node_id, humidity}` | `{ok, node_id, humidity}` |
| GET | `/central/status` | — | `{ok, nodes: {[nodeId]: CentralNodeStatus}}` |
| GET | `/db/anomaly_summary` | — | `{ok, summary: [{detection_source, sample_count, avg_edge_ms, avg_central_ms, avg_delta_ms, min_delta_ms, max_delta_ms}]}` |
| GET | `/db/history/events` | — | `{ok, events: AnomalyEvent[]}` ordered by `injection_timestamp DESC` |
| GET | `/db/history/telemetry` | Query params `?node_id=&start=&end=` | `{ok, rows: TelemetryRow[]}` or `400 {ok: false, error}` |
| POST | `/simulation/inject` | Query params `?node_id=&scenario=` | `{status, node, scenario}` or `{error}` |

**Valid `scenario` values:** `"hvac_failure"`, `"thermal_spike"`, `"coolant_leak"`, `"reset"`

### WebSocket Endpoint

| Path | Direction | Rate |
|---|---|---|
| `/ws/simulation` | Server → Client (push only) | 1 Hz (1 frame/sec) |

---

## 5. WebSocket Events

**Single endpoint:** `ws://localhost:8000/ws/simulation`

**Client sends:** nothing after handshake.

**Server sends:** one JSON object per second.

### Frame Schema

```json
{
  "node-1": {
    "node_id": "node-1",
    "timestamp": 1711270800.123,
    "temperature": 21.45,
    "humidity": 45.2,
    "airflow": 2.31,
    "cpu_load": 0.52,
    "obstruction_ratio": 0.0,
    "anomaly_score": 0.05,
    "is_anomaly": false
  },
  "node-2": { ... },
  "node-3": { ... }
}
```

### Field Reference

| Field | Type | Units / Range | Notes |
|---|---|---|---|
| `node_id` | string | — | Echoed from server's `nodes` dict key |
| `timestamp` | float | Unix epoch (seconds) | Frontend normalizes: `new Date(ts * 1000).toISOString()` |
| `temperature` | float | °C | ~21°C baseline; rises during thermal spike |
| `humidity` | float | % RH, 0–100 | Mean-reverts to initial value |
| `airflow` | float | dimensionless | Nominal ~2.5; drops to ~0 on fan failure |
| `cpu_load` | float | 0–1 | AR(1); fixed at 1.0 during thermal spike |
| `obstruction_ratio` | float | 0–1 | Reflects last control call |
| `anomaly_score` | float \| null | IsolationForest decision score | `null` during first 10 steps (window warming) |
| `is_anomaly` | bool \| null | — | Includes 20-step persistence; `null` during warmup |

### Connection Lifecycle

1. Client connects to `/ws/simulation`
2. Server enters infinite `while True:` loop with `asyncio.sleep(1.0)`
3. Frame assembled and sent each second
4. Telemetry and anomaly events written to DB each second
5. On `WebSocketDisconnect`: clean exit from loop
6. Client-side: reconnects after 2-second delay on close or error

---

## 6. Database Operations

**Database:** SQLite at `db/ehabitat.db`
**Initialization:** `init_db()` called at api.py import time (creates tables if not exist)

---

### Table: `telemetry`

**Schema:**

| Column | Type | Constraint | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY | Auto-increment |
| `seq_id` | INTEGER | — | Sequence counter from `_step_seq` |
| `node_id` | TEXT | — | "node-1" / "node-2" / "node-3" |
| `timestamp` | REAL | — | Unix epoch float |
| `temperature` | REAL | — | °C |
| `humidity` | REAL | — | % RH |
| `airflow` | REAL | — | Dimensionless |
| `cpu_load` | REAL | — | 0–1 |
| `is_anomaly` | INTEGER | — | 1 = true, 0 = false |
| `anomaly_score` | REAL | — | IsolationForest decision score |

**Indices:** `idx_telemetry_timestamp`, `idx_telemetry_node_id`

**Write:** `insert_telemetry()` called from `websocket_simulation()` — 3 rows/sec (one per node), every second
**Read:** No SELECT queries on this table exist in `api.py`. The table is write-only from the server's perspective.

---

### Table: `anomaly_events`

**Schema:**

| Column | Type | Constraint | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY | Auto-increment |
| `seq_id` | INTEGER | — | Step sequence at detection time |
| `node_id` | TEXT | — | Node identifier |
| `injection_timestamp` | REAL | — | When scenario was injected (null if spontaneous) |
| `edge_detection_ts` | REAL | — | Unix epoch when edge ML detected anomaly |
| `central_detection_ts` | REAL | — | Unix epoch when central ML detected anomaly |
| `edge_latency_ms` | REAL | — | `(edge_detection_ts - injection_ts) * 1000` |
| `central_latency_ms` | REAL | — | `(central_detection_ts - injection_ts) * 1000` |
| `detection_source` | TEXT | — | `"edge"` or `"central"` |
| `bytes_edge` | INTEGER | — | Byte size of one edge telemetry frame at detection time |
| `bytes_central` | INTEGER | — | Cumulative bytes received by central server for this node |

**Write — edge event:** `insert_anomaly_event()` called when `raw["is_anomaly"]` transitions False→True
**Write — central event:** `insert_anomaly_event()` called when central persistent anomaly transitions False→True

**Read — `GET /db/anomaly_summary`** executes:
```sql
SELECT
  detection_source,
  COUNT(*)                              AS sample_count,
  AVG(edge_latency_ms)                  AS avg_edge_ms,
  AVG(central_latency_ms)               AS avg_central_ms,
  AVG(edge_latency_ms - central_latency_ms) AS avg_delta_ms,
  MIN(edge_latency_ms - central_latency_ms) AS min_delta_ms,
  MAX(edge_latency_ms - central_latency_ms) AS max_delta_ms
FROM anomaly_events
GROUP BY detection_source
```

**Read — `GET /db/history/events`:** `SELECT * FROM anomaly_events ORDER BY injection_timestamp DESC` via `get_anomaly_events()`

**Read — `GET /db/history/telemetry`:** `SELECT * FROM telemetry WHERE node_id = ? AND timestamp >= ? AND timestamp <= ? ORDER BY timestamp ASC` via `get_telemetry_range()`

**Note on `bytes_edge` vs `bytes_central`:** These are not directly comparable.
- `bytes_edge`: snapshot size of one frame (temperature + humidity + airflow + cpu_load + anomaly_score + is_anomaly)
- `bytes_central`: running cumulative total of raw telemetry bytes received since server start

---

## 7. Missing and Unused Files

### Files Referenced in Code That Do Not Exist

**None.** All imports and file references are satisfied on disk:
- `models/model_v2_hybrid_real.pkl` — present
- `models/scaler_v2.pkl` — present
- All Python module imports resolve

---

### Files That Exist But Are Unused in the Runtime Path

**Dead code — `backend/simulation/`:**

| File | Status | Only Reference |
|---|---|---|
| `thermal.py` | Exact duplicate of `thermal_model.py` | `backend/tests/test_thermal.py` only |
| `environment.py` | EnvironmentalModel never instantiated at runtime | `backend/tests/test_environment_model.py` only |
| `runner.py` | CLI tool; not imported by `api.py` | Not imported anywhere |

**Superseded model artifact:**

| File | Status |
|---|---|
| `backend/ml/isolation_forest.pkl` | Superseded; runtime loads `models/model_v2_hybrid_real.pkl` |
| `backend/ml/baseline_features.npy` | Training artifact; not loaded at runtime |

**Offline-only training scripts:**

| File | Status |
|---|---|
| `backend/ml/generate_baseline_data.py` | Offline training only |
| `backend/ml/train_model.py` | Offline training only |
| `backend/ml/train_hybrid_model.py` | Offline training only |
| `backend/ml/validate_on_real_anomalies.py` | Offline validation only |

**Root-level diagnostic/verification scripts (all unused in runtime or test suite):**

```
audit_datasets.py       check_stats.py          check_stats_simple.py
create_features.py      debug_correlation.py    diagnose.py
generate_real_features.py                       recreate_anomalies.py
task1_diag.py           test_airflow_physics.py verify_coupling.py
verify_persistence.py   verify_physics_spike.py verify_thermal_fix.py
feature_report.csv      (output artifact)
```

**Frontend scaffolding never referenced:**
- `public/file.svg`, `public/globe.svg`, `public/next.svg`, `public/vercel.svg`, `public/window.svg` — default Next.js assets; not used in any component

---

## 8. Code vs Documentation Discrepancies

---

**1. `app/layout.tsx` metadata not updated**
- `title: "Create Next App"`, `description: "Generated by create next app"` — placeholder text, not E-Habitat branding
- No documentation addresses this

---

**2. `EnvironmentalModel` described as active in `application_architecture.md`**
- `Docs/application_architecture.md` and `Docs/Week1_Implementation_Summary.md` list `EnvironmentalModel` as a core abstraction
- Reality: `EnvironmentalModel` is never instantiated; `VirtualNode` performs the same composition plus ML inference
- Documentation describes an architecture that was superseded

---

**3. `thermal.py` is a dead duplicate**
- No documentation distinguishes `thermal.py` from `thermal_model.py`
- Both exist on disk; only `thermal_model.py` is imported in the runtime path
- `backend/tests/test_thermal.py` tests the dead duplicate, not the live module

---

**4. Wrong path for `central_server.py` in `CLAUDE.md`**
- `CLAUDE.md` references `"backend/centralized/central_server.py"`
- Actual path: `backend/simulation/central_server.py`
- No `backend/centralized/` directory exists

---

**5. `/api/ml/status` samples only `node-1`**
- `api.py` returns status from `nodes["node-1"]` only, assuming all nodes are in sync
- No documentation states this assumption
- If a partial `ml_reload()` failure leaves nodes in different states, the endpoint will misreport node-2 and node-3

---

**6. WebSocket `timestamp` field is float (Unix epoch), not ISO string**
- `node.step()` originally returned `datetime.utcnow().isoformat()` (ISO string)
- `page.tsx` handles both types: if `typeof timestamp === "number"`, converts via `new Date(ts * 1000).toISOString()`; else uses string as-is
- This dual-type branch in the client is evidence of an unresolved data contract change
- No documentation specifies the `timestamp` type in the WebSocket schema

---

**7. NodeGauges airflow gauge range is wrong**
- `NodeGauges.tsx`: `<Gauge value={airflow} min={0} max={1} ...>`
- Actual airflow values are ~2.3–2.7 at nominal — well outside the 0–1 range
- The gauge will always read at max during normal operation
- No documentation addresses gauge scaling for airflow

---

**8. `backend/ml/isolation_forest.pkl` is an undocumented superseded artifact**
- The older model at `backend/ml/isolation_forest.pkl` is never loaded at runtime
- Runtime uses `models/model_v2_hybrid_real.pkl`
- `MIGRATION_LOG.md` does not mark the old file as deprecated
- Could cause confusion in future maintenance

---

**9. `backend/test_db.py` is not discoverable by the test suite**
- Exists at `backend/test_db.py`, not under `backend/tests/`
- `pyproject.toml` test discovery targets `backend/tests/`
- The file is neither run automatically nor documented

---

**10. Database writes silently drop on error**
- `database.py`: `except Exception as e: print(f"DB write error: {e}")` — no re-raise, no alerting, no retry
- If the SQLite file is locked, corrupted, or the disk is full, telemetry and anomaly events are lost without any visible system state change
- Not documented in `application_architecture.md` or `MIGRATION_LOG.md`

---

**11. `/simulation/inject` endpoint not formally specified in the SRS**
- The endpoint with scenarios `"hvac_failure"`, `"thermal_spike"`, `"coolant_leak"`, `"reset"` is fully implemented
- `Docs/Thermal_Spike_Scenario.md` documents thermal_spike physics; no equivalent doc exists for coolant_leak
- No SRS requirement formally specifies this injection interface as a system function
- The inject → record_injection → latency measurement pipeline is entirely absent from formal requirements

---

**12. `bytes_edge` and `bytes_central` measure incomparable quantities**
- `bytes_edge` in `anomaly_events`: size of one full edge frame (includes `anomaly_score`, `is_anomaly`)
- `bytes_central` in `anomaly_events`: cumulative raw telemetry bytes since server start (4-field only)
- The comparison panel in `page.tsx` displays both numbers side by side without clarifying the semantic difference
- No documentation describes this asymmetry

---

**13. `/db/anomaly_summary` endpoint absent from `application_architecture.md`**
- Added in the most recent commit; the architecture document predates it and does not mention it

---

**14. Anomaly detection threshold changed — `CLAUDE.md` references stale value**
- `CLAUDE.md` and old docs state threshold is `model.offset_` ≈ `−0.6134`
- Reality since 2026-03-27: `is_anomaly = float(score) < 0.15` (a fixed positive threshold)
- The `model.predict()` call (which uses `offset_`) is no longer used for the anomaly decision
- Any document citing `−0.6134` or `model.offset_` as the operative threshold is stale

---

**15. `POST /api/controls/fan_failure` behavior changed — docs still describe instant snap**
- Previous behavior: `airflow_model.simulate_fan_failure()` — instant obstruction to 100%
- Current behavior: `node.inject_hvac_failure(duration_seconds=40)` — ramped over 15 steps
- `central_server.record_injection()` is now also called (was missing before), enabling latency measurement from this control endpoint
- Any documentation describing fan_failure as an instantaneous event is stale

---

**16. `HistoryTab` new types (`AnomalyEvent`, `SummaryRow`) defined in `page.tsx`, not `types.ts`**
- All other shared types live in `app/lib/types.ts`
- `AnomalyEvent` and `SummaryRow` are defined inline in `page.tsx` as local types for `HistoryTab`
- If `HistoryTab` is ever split into its own component file, these types will need to be moved to `types.ts`

---

*End of architecture map.*
