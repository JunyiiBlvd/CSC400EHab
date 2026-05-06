# Software Requirements Specification — Final Report

**Project Name:** E-Habitat: Interactive Server Room Monitoring Simulator
**Document Version:** v2.0 (Final — Capstone Submission)
**Date:** April 2026
**Course:** CSC400 — Computer Science Project Seminar, Spring 2026

**Team Members:**

| Name            | Role                    | Email                      |
| :-------------- | :---------------------- | :------------------------- |
| Logan Caraballo | Project Lead / Backend  | caraballol2@southernct.edu |
| Jared He        | Frontend / UI           | hej6@southernct.edu        |
| Gavin Paeth     | Data / Testing          | paethg1@southernct.edu     |

---

## 1. Executive Summary

### 1.1 Project Overview

E-Habitat is an interactive educational simulation platform that enables learners to observe and compare centralized vs. edge-based anomaly detection architectures running in real time on identical sensor data. The system simulates the thermal, airflow, humidity, and CPU-load dynamics of three virtual server room nodes. An Isolation Forest ML model trained on real-world sensor data detects deviations from normal operation. Both a local (edge) inference path and a remote (centralized) inference path execute concurrently, and the dashboard quantifies the detection latency delta and bandwidth trade-off between them.

### 1.2 Problem Statement

Students studying distributed systems encounter abstract concepts — edge computing, centralized monitoring, latency, bandwidth — without access to realistic experimentation environments. Existing tools are either production-grade monitoring systems too complex for educational use, or purely theoretical materials with no experiential component. E-Habitat bridges this gap by providing a controlled, visual, and interactive simulation environment that makes these trade-offs concrete and measurable.

### 1.3 Research Question

> **Does edge-based ML inference detect anomalies faster and with less network bandwidth consumption than centralized polling on identical sensor data?**

### 1.4 Answer (Empirical)

**Yes on bandwidth; marginal on latency.** Measured results from live simulation sessions:

| Metric | Edge | Centralized | Delta |
|---|---|---|---|
| Detection latency (ms) | 2,500–4,070 | 2,550–4,108 | +38–42 ms slower for central |
| Bandwidth per frame (bytes) | ~204 KB cumulative | ~98 KB cumulative | Central uses ~48% of edge bandwidth |

The latency difference is small but consistent: edge detects ~38–42 ms earlier than centralized because the inference step completes before the raw telemetry frame is transmitted. The bandwidth advantage is significant: the centralized path transmits only the four raw sensor fields, while the edge path transmits the full frame including anomaly score and anomaly flag.

---

## 2. User Research & Personas

### 2.1 Research Methods

- Review of distributed systems course curricula and objectives
- Analysis of existing monitoring tools and their complexity for educational use
- Team course experience as students of CS systems courses

**Key Findings:**
1. Visual feedback is the top priority for knowledge retention in abstract systems topics
2. Experiments must be repeatable — instructors need to be able to run the same scenario twice and get observable (though not identical) results
3. Interface must be simple enough that users focus on architectural behavior, not operational setup

### 2.2 User Personas

#### Primary: CS Student

**Name & Role:** John Doe, upper-level undergraduate studying distributed systems
**Needs:** Observe how centralized vs. edge architectures behave under the same conditions; inject anomalies; interpret latency and bandwidth data
**Pain Points:** Abstract concepts with no hands-on reinforcement; no accessible simulation tools
**Goals:** Develop intuition about latency and bandwidth trade-offs; understand anomaly detection in real systems

#### Secondary: Course Instructor

**Name & Role:** Jane Doe, university-level systems instructor
**Needs:** Reliable classroom demonstrations; controlled scenarios for illustrating specific concepts
**Pain Points:** Existing production tools are too complex to demonstrate concepts efficiently
**Goals:** Reinforce lecture material with visual, repeatable experiments; demonstrate architectural trade-offs live

---

## 3. User Stories

### Must Have (MVP) — Status: COMPLETE

**US003:** As a user, I want to start the simulation and see live telemetry streaming within one second.
- Telemetry begins streaming within one second of connection
- Simulation runs at one-second time steps with real-time updates
- Status: **COMPLETE** — WebSocket pushes one frame per second from three nodes concurrently

**US004:** As a user, I want to adjust environmental parameters in real time.
- Airflow obstruction slider (0–100%), humidity slider (0–100%), per-node selection
- Status: **COMPLETE** — All sliders wired to REST control endpoints; changes reflected in next simulation step

**US005:** As a user, I want to inject predefined anomaly scenarios.
- Thermal spike, HVAC failure, coolant leak injection with visual indicators
- Status: **COMPLETE** — Three injection scenarios implemented: thermal_spike, hvac_failure, coolant_leak

**US006:** As a user, I want to view centralized and edge monitoring results side by side.
- Both architectures run simultaneously on identical data
- Metrics include detection latency and bandwidth per architecture
- Status: **COMPLETE** — Comparison panel shows per-node: edge latency, central latency, latency delta, bytes edge, bytes central, BW ratio

**US007:** As a user, I want to view real-time telemetry and alerts.
- Live charts update with less than 200ms latency
- Alerts appear when anomalies are detected
- Status: **COMPLETE** — Live Recharts telemetry, Isolation Forest anomaly alerts, topology hero with animated packet flow

### Should Have — Status: Out of Scope (not pursued)

- Saved simulations and templates
- Multi-user classroom support
- Advanced anomaly models (LSTM, Autoencoder)

---

## 4. Features & Requirements

### 4.1 Core Features — Final Implementation State

| Feature | Status | Notes |
|---|---|---|
| Physics simulation engine (3 nodes) | COMPLETE | ThermalModel, AirflowModel, HumidityModel per node |
| Edge ML inference (per-node) | COMPLETE | Isolation Forest inside VirtualNode.step() |
| Centralized ML inference | COMPLETE | CentralServer mirrors edge inference on raw telemetry |
| Anomaly injection — thermal spike | COMPLETE | CPU load override, ML detects via thermal feature deviation |
| Anomaly injection — HVAC failure | COMPLETE | Ramped 15-step airflow degradation; ML detectable |
| Anomaly injection — coolant leak | COMPLETE | Humidity ramp +2.5% RH/step over 20 steps; ML detectable |
| Real-time dashboard | COMPLETE | Topology hero, node gauges, alerts feed, node grid |
| Comparison panel | COMPLETE | Live latency and bandwidth metrics per node |
| SQLite persistence | COMPLETE | Telemetry and anomaly_events tables; history tab |
| Teaching / concept panel | COMPLETE | 7-slide explainer embedded in controls column |
| History tab | COMPLETE | Aggregate stats + full anomaly event log |

### 4.2 Technical Requirements — Compliance

#### Performance

| Requirement | Target | Measured |
|---|---|---|
| Dashboard update latency | < 200 ms | WebSocket push at 1 Hz; client renders < 50ms |
| Concurrent node support | ≥ 3 nodes | 3 nodes stable across 60+ minute sessions |
| Simulation startup | < 10 seconds | Server ready in < 2 seconds |

#### Usability

- Interface supports live demos without prior configuration: **MET** — one `uvicorn` command, one `npm run dev`
- Core actions accessible within two clicks: **MET** — inject buttons visible on load, no navigation required
- Dark mode UI: **MET** — full dark theme throughout

#### Reliability

- 60-minute continuous runtime: **MET** — tested stable
- ML false positives during normal operation: **MET** — baseline floor score 0.2275 (threshold 0.15); zero false positives in normal operation
- Database write failures non-crashing: **MET** — all DB writes wrapped in try/except with silent logging

---

## 5. System Design

### 5.1 Technology Stack

| Layer | Technology |
|---|---|
| Backend language | Python 3.12 |
| Backend framework | FastAPI + Uvicorn |
| Physics simulation | Custom (ThermalModel, AirflowModel, HumidityModel) |
| ML | scikit-learn 1.8.0, Isolation Forest |
| Database | SQLite via Python built-in sqlite3 |
| Frontend language | TypeScript |
| Frontend framework | Next.js 14, React |
| UI libraries | Tailwind CSS, Material UI, Recharts |
| WebSocket | Native browser WebSocket API + FastAPI WebSocket |

### 5.2 System Architecture

Two monitoring architectures run concurrently on identical sensor data. This dual-path design is the academic core of the project.

```
VirtualNode.step() [1 second, per node × 3]
    │
    ├─► EDGE PATH
    │       SlidingWindowFeatureExtractor (10-step window)
    │       → ModelLoader.predict()
    │       → is_anomaly + anomaly_score set BEFORE telemetry leaves the node
    │       → Full frame pushed via WebSocket (includes anomaly fields)
    │       Bytes counted: full frame (temperature, humidity, airflow,
    │                      cpu_load, anomaly_score, is_anomaly)
    │
    └─► CENTRAL PATH
            Raw telemetry only (no anomaly fields) → CentralServer.receive_telemetry()
            CentralServer maintains its own SlidingWindowFeatureExtractor per node
            CentralServer.ModelLoader.predict() runs AFTER raw data is received
            Frontend polls GET /central/status every 1 second
            Bytes counted: raw fields only (temperature, humidity, airflow, cpu_load)

Latency delta = central_detection_ts − edge_detection_ts
Measured: ~38–42 ms average; range 10–1,000 ms depending on window fill state at injection
```

### 5.3 Physics Simulation Engine ("PsyEngine")

The physics engine models three independent virtual server room nodes through coupled differential equations:

**CPU Load:** AR(1) process — `cpu_load = 0.95 × prev + 0.05 × 0.5 + N(0, 0.02)`, clamped to [0.1, 0.9]

**Thermal Model (Newton's Law of Cooling):**
```
P_heat = heat_coefficient × cpu_load
cooling_power = cooling_coefficient × airflow_ratio × (T − T_ambient)
ΔT = (P_heat − cooling_power) / (air_mass × heat_capacity) × dt
```
Parameters: air_mass=10, heat_capacity=1005, heat_coefficient=300, cooling_coefficient=150, T_ambient=20°C

**Airflow Model (Proportional HVAC Control):**
```
flow = nominal_flow × (1 − obstruction) + 0.05 × (T − 20.88) + N(0, 0.08)
```
Nominal flow: 2.5; proportional response ~5% per °C above setpoint

**Humidity Model (Mean-Reversion + Temperature Coupling):**
```
ΔH = drift + (−0.05 × (H − H₀)) + (−0.003 × (T − T_ref)) + U(−noise, +noise)
```
Mean-reverts to initial humidity; inversely coupled to temperature

All three models are calibrated against real-world sensor data distributions from the MIT CSAIL Intel Lab dataset and a Kaggle HVAC dataset.

### 5.4 ML Pipeline

**Model:** Isolation Forest (scikit-learn 1.8.0), trained offline as `model_v2_hybrid_real.pkl`
**Scaler:** RobustScaler (`scaler_v2.pkl`) — applied before inference; required for valid scoring

**Feature Extraction (SlidingWindowFeatureExtractor):**
- 10-step sliding window per node
- 12 features: mean, variance, rate-of-change for each of [temperature, airflow, humidity, cpu_load]
- Feature vector order: `[T_mean, T_var, T_roc, Air_mean, Air_var, Air_roc, Hum_mean, Hum_var, Hum_roc, CPU_mean, CPU_var, CPU_roc]`

**Detection Threshold:** `score < 0.15` (custom positive threshold, not model's internal offset_)
- Normal score range: +0.2275 to +∞ (baseline floor established by test_clean_baseline_profile.py)
- Anomaly range: < 0.15
- Gap of ~0.08 between normal floor and threshold — zero false positives in baseline testing

**Training Data (Hybrid, 22,239 rows total):**

| Source | File | Rows | % of Training | Notes |
|---|---|---|---|---|
| Synthetic | `normal_telemetry.csv` | 10,000 | 45.0% | Baseline "ideal" physics signatures from PsyEngine |
| Cold Source | `cold_source_features.csv` | 3,489 | 15.7% | Real-world server room data (found by Gavin; exact provenance undocumented). No humidity column — imputed with `N(38.63, 7.21)` calibrated against MIT CSAIL statistics. |
| MIT CSAIL | `mit_features.csv` | 5,000 | 22.5% | Intel Lab Intel Research deployment; high-frequency thermal data. CPU load imputed from thermal rate-of-change. |
| Kaggle HVAC | `HVAC_Kaggle.csv` | 3,750 | 16.9% | HVAC fan power correlations. Airflow mapped from fan power via linear transfer function. |

**Note on cold source humidity:** The dataset has no humidity column. Initially it was filled with `N(45.0, 2.0)` (arbitrary). In April 2026 the professor flagged this. MIT CSAIL statistics (μ=38.63, σ=7.21) were used to calibrate the synthetic parameters. The model was retrained and validated — recall held at 100% on the MIT CSAIL anomaly windows under the 0.15 threshold.

**Real-World Validation (full metrics — `data/real/validation_results.txt`):**

Test set: 1,732 MIT CSAIL anomaly windows (positive) + 134,516 in-distribution normal windows (negative: 84,525 MIT CSAIL + 49,991 synthetic)

| Metric | Value |
|---|---|
| Recall (sensitivity) | **100.00%** |
| Precision (PPV) | **97.58%** |
| F1 Score | **98.77%** |
| Specificity (TNR) | **99.97%** |
| Accuracy | **99.97%** |
| False Positive Rate | **0.032%** (43 / 134,516 normal windows) |
| AUC-ROC | **1.0000** |

Score separation: anomaly windows avg +0.005, normal windows avg +0.269 — a 0.264-point gap at the 0.15 threshold.

**Cold source OOD finding:** When the cold source feature file is scored independently, 94.93% of its windows (3,312 / 3,489) are flagged as anomalous. The root cause is a data imputation error, not an operational difference. The cold source dataset has no real humidity column. Humidity was imputed as i.i.d. draws from N(38.63, 7.21) — the correct *marginal* distribution from MIT CSAIL, but with no temporal correlation. Real sensors drift slowly; consecutive readings differ by fractions of a unit. I.i.d. sampling from σ=7.21 produces readings that jump ~7.21 RH per step. The expected sliding-window variance of 10 i.i.d. N(μ, 7.21²) draws is σ²≈52 — matching the observed cold source hum_var of 49.0 exactly. The model correctly identifies this as anomalous high-frequency noise. The fix would be to generate humidity as a correlated time-series (e.g., AR(1) or random walk with drift) rather than i.i.d. samples. This finding is documented in `validation_results.txt` and cold source is excluded from precision/F1/FPR metrics.

### 5.5 Anomaly Injection Scenarios

| Scenario | Mechanism | ML Detection | Notes |
|---|---|---|---|
| Thermal Spike | CPU override to 100% for 120s, HVAC lag 40s | Reliable — thermal + CPU features diverge strongly | Primary demo scenario |
| HVAC Failure | Airflow linear ramp to 0 over 15 steps, holds | Reliable — 15-step anomaly streak, min score 0.073 | Ramped design allows ML window to fill with deviant data |
| Coolant Leak | Humidity +2.5% RH/step for 20 steps, capped at 85% | Reliable — humidity variance and ROC features diverge | Added in Phase 3 |

### 5.6 Database Schema

```sql
CREATE TABLE telemetry (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    seq_id        INTEGER NOT NULL,
    node_id       TEXT NOT NULL,
    timestamp     REAL NOT NULL,
    temperature   REAL, humidity REAL, airflow REAL, cpu_load REAL,
    is_anomaly    INTEGER, anomaly_score REAL
);

CREATE TABLE anomaly_events (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    seq_id               INTEGER NOT NULL,
    node_id              TEXT NOT NULL,
    injection_timestamp  REAL,
    edge_detection_ts    REAL, central_detection_ts REAL,
    edge_latency_ms      REAL, central_latency_ms   REAL,
    detection_source     TEXT,
    bytes_edge INTEGER, bytes_central INTEGER
);
```

**Indices:** `idx_telemetry_timestamp`, `idx_telemetry_node_id`
**Write rate:** 3 rows/second to `telemetry` (one per node); rows to `anomaly_events` on False→True detection transitions only

### 5.7 API Reference

| Method | Endpoint | Description |
|---|---|---|
| WS | `/ws/simulation` | Push 1 frame/sec per node (edge path) |
| GET | `/central/status` | Centralized architecture metrics per node |
| POST | `/simulation/inject` | Inject anomaly scenario (`thermal_spike`, `hvac_failure`, `coolant_leak`, `reset`) |
| GET | `/api/ml/status` | ML window readiness and model info |
| POST | `/api/controls/airflow_obstruction` | Set airflow obstruction ratio |
| POST | `/api/controls/fan_failure` | Trigger ramped HVAC failure |
| POST | `/api/controls/set_humidity` | Set humidity setpoint |
| GET | `/db/anomaly_summary` | Aggregate latency stats from SQLite |
| GET | `/db/history/events` | All anomaly events ordered by injection time |
| GET | `/db/history/telemetry` | Telemetry rows for a node within a timestamp range |

### 5.8 Frontend Dashboard

**Dashboard (Live tab):**
- **Topology hero:** Full-width animated SVG showing edge vs. centralized data paths with animated packet flows (cyan = edge, amber = central)
- **Node gauges:** Temperature, CPU, humidity, airflow gauges for the selected node
- **Alerts feed:** Real-time ML-driven alert feed (CRIT/WARN/INFO) with color coding
- **Controls panel:** Node selector, obstruction/humidity sliders, anomaly injection buttons, 7-slide teaching panel
- **Node grid:** Three-node card grid with sparklines per node

**History tab:**
- Aggregate stats: total events, avg edge latency, avg central latency, avg/min/max delta
- Full anomaly event log with per-event edge latency, central latency, delta, and bytes

---

## 6. Implementation Status

### 6.1 Phase Completion

| Phase | Description | Status |
|---|---|---|
| Phase 1 — Foundation | Environment setup, dataset analysis, physics calibration | COMPLETE |
| Phase 2 — Core ML | Feature extraction, Isolation Forest training, real-data validation | COMPLETE |
| Phase 3 — Integration | CentralServer, WebSocket, comparison panel, SQLite, 3-node UI | COMPLETE |
| Phase 4 — Polish | Dashboard redesign, topology hero, teaching panel, History tab | COMPLETE |

### 6.2 All Must-Have Requirements Met

All five Must Have user stories (US003–US007) are implemented and tested. The comparison panel answers the project's core research question with live measured data. Three anomaly scenarios are injectable and ML-detectable. The system runs continuously without failure for 60+ minutes.

---

## 7. Risk Assessment — Final Disposition

| Risk | Initial Status | Final Disposition |
|---|---|---|
| HVAC failure not ML-detectable | High — confirmed gap | RESOLVED — ramped injection (15-step ramp) produces detectable signal; 15-step anomaly streak, min score 0.073 |
| Comparison panel empty at submission | High | RESOLVED — CentralServer implemented; comparison panel shows real measured data |
| WebSocket performance at 3-node scale | Low | RESOLVED — Stable in 60+ minute tests; no dropped messages |
| SQLite performance for time-series | Medium | MITIGATED — Indexed; short demo sessions; write rate 3 rows/sec is well within SQLite limits |
| Physics/ML training distribution divergence | Medium | DOCUMENTED — model locked; any physics change requires v3 retraining |
| Recall gate vs. deployed threshold mismatch | Discovered April 2026 | RESOLVED — validate_on_real_anomalies.py updated to use 0.15 threshold; new retrain maintains ≥95.96% recall |

---

## 8. Known Limitations

1. **HTTP status codes on control errors:** Some error responses return `200 {ok: false}` instead of proper 4xx codes. Low priority; does not affect demo functionality.

2. **NodeGauges airflow gauge range:** The airflow gauge UI is configured for 0–1 range; actual airflow values are ~2.3–2.7. The gauge pegs at max during normal operation. Visual bug only; telemetry data is correct.

3. **`bytes_edge` vs. `bytes_central` semantic asymmetry:** `bytes_edge` is a per-frame snapshot; `bytes_central` is a running cumulative total. They measure different things but appear side by side in the comparison panel. This is documented but not surfaced to the user in-UI.

4. **HVAC failure with old instant-snap injection:** The original `simulate_fan_failure()` method (instant obstruction to 100%) was not reliably ML-detectable. The fix — a ramped 15-step descent — was added in Phase 3. The old method still exists in the codebase but is not used in the injection path.

5. **ML model trained on steady-state normal data only:** The model detects deviations from normal. It does not predict future events or diagnose root causes. Gradual drifts near the boundary of normal operation may be missed.

---

## 9. Success Metrics — Final Evaluation

### Technical

| Metric | Target | Result |
|---|---|---|
| Simulation startup | < 10 seconds | < 2 seconds |
| Dashboard update latency | < 200 ms | WebSocket 1 Hz, renders < 50 ms |
| Continuous uptime | > 60 minutes | Confirmed stable |
| ML Recall | N/A (stretch) | **100.00%** on 1,732 MIT CSAIL held-out anomaly windows |
| ML Precision | N/A (stretch) | **97.58%** (43 FP / 134,516 normal windows) |
| ML F1 Score | N/A (stretch) | **98.77%** |
| ML AUC-ROC | N/A (stretch) | **1.0000** |
| Edge vs. central latency delta | Measurable | 38–42 ms consistently |
| Bandwidth ratio | Measurable | ~48% (central uses roughly half the edge bandwidth) |

### Academic

The project directly answers its research question with empirical data. The comparison panel provides live evidence of the trade-offs between edge and centralized inference. The simulation is calibrated against real-world sensor data and the model generalizes to real anomalies with 95.96% recall.

---

## 10. Appendix

### A. Glossary

- **Edge Computing:** Data processing that occurs locally at or near the data source, before any network transmission.
- **Centralized Computing:** Data processing that occurs at a central server after raw data is transmitted over the network.
- **Isolation Forest:** An unsupervised ML algorithm for anomaly detection based on random recursive partitioning of the feature space.
- **PsyEngine:** Internal name for E-Habitat's physics simulation engine (ThermalModel + AirflowModel + HumidityModel + VirtualNode coupling).
- **Sliding Window:** A fixed-size buffer of recent telemetry steps used to compute statistical features for ML inference.
- **seq_id:** Monotonically increasing integer assigned to each simulation step per node; used to synchronize edge and central sliding windows.
- **WebSocket:** Persistent full-duplex communication protocol enabling real-time server-to-client data streaming.
- **RobustScaler:** Scikit-learn feature scaler that normalizes using median and IQR rather than mean and variance; less sensitive to outliers.

### B. Repository Structure

```
csc400/
├── backend/
│   ├── api.py                         ← FastAPI entry point, WebSocket loop, all endpoints
│   ├── ml/
│   │   ├── model_loader.py            ← ModelLoader (Isolation Forest + scaler)
│   │   └── feature_extraction.py     ← SlidingWindowFeatureExtractor
│   └── simulation/
│       ├── node.py                    ← VirtualNode (physics + edge ML)
│       ├── central_server.py          ← CentralServer (centralized ML)
│       ├── database.py                ← SQLite layer
│       ├── thermal_model.py           ← Newton's Law of Cooling
│       ├── airflow.py                 ← Proportional HVAC airflow
│       └── humidity.py                ← Mean-reversion humidity model
├── models/
│   ├── model_v2_hybrid_real.pkl       ← Active Isolation Forest artifact
│   └── scaler_v2.pkl                  ← Active RobustScaler
├── app/
│   ├── page.tsx                       ← Next.js single-page dashboard
│   └── components/
│       ├── TopologyOverview.tsx       ← Animated SVG architecture diagram
│       ├── NodeGauges.tsx
│       ├── NodeGrid.tsx
│       ├── AlertsFeed.tsx
│       └── Sparkline.tsx
└── db/
    └── ehabitat.db                    ← SQLite runtime database (auto-created)
```

### C. Change Log

| Date | Version | Changes | Author |
|---|---|---|---|
| Feb 2026 | v1.0 | Initial SRS draft | Logan, Jared, Gavin |
| Feb 2026 | v1.1 | Revised per professor feedback | Logan, Jared, Gavin |
| Mar 2026 | v1.2 | Auth removed; DB schema, WebSocket, CentralServer design added | Logan |
| Mar 23, 2026 | — | CentralServer built; comparison panel live; MIT validation 95.96% | Logan |
| Mar 27, 2026 | — | History API, History tab, coolant leak scenario, HVAC ramp fix | Logan, Jared |
| Apr 7, 2026 | — | Cold source humidity recalibrated to N(38.63, 7.21) matching MIT CSAIL stats; validation gate fixed (score < 0.15); model retrained — recall 100% on 1,732 anomaly windows | Logan, Gavin |
| Apr 16, 2026 | — | Dashboard redesign: topology hero, teaching panel, controls refactor | Jared |
| Apr 2026 | v2.0 | Final report — all phases complete; empirical results recorded | Logan |

---

**Document Status:** Final — Capstone Submission
**Prepared by:** Logan Caraballo, Jared He, Gavin Paeth
**Course:** CSC400 — Computer Science Project Seminar, Spring 2026
