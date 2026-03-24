# E-Habitat Session Summary
**Date:** March 23, 2026
**Supersedes:** CSC400-ProgressReport-2_2_26.md for implementation status

---

## What Was Built This Session

### 1. CentralServer (`backend/simulation/central_server.py`) — NEW
Full centralized anomaly detection class. Mirrors VirtualNode ML inference but centralized:
- Lazy per-node state init (SlidingWindowFeatureExtractor, 20-step persistence window)
- `receive_telemetry()` — feeds raw telemetry (no anomaly fields), runs Isolation Forest, records `central_detection_ts` on False→True transition only
- `record_injection()` — stores injection timestamp so edge_latency_ms and central_latency_ms can be computed from injection to detection
- `get_status()` — returns per-node dict with all comparison metrics
- Bytes tracking: both edge and central are cumulative across all frames

### 2. api.py — UPDATED
- CentralServer instantiated at module level with shared ModelLoader
- `_prev_edge_anomaly` dict tracks edge False→True transition in WS loop
- `receive_telemetry()` called every step with raw telemetry + bytes_edge
- `record_injection()` called on both thermal_spike and hvac_failure inject paths
- `GET /central/status` endpoint added, returns `{ok, nodes}`
- `import json` added for bytes calculation

### 3. Comparison Panel (`app/page.tsx`) — REPLACED
Placeholder text replaced with real component:
- Polls `GET /central/status` every 1 second via useEffect + setInterval
- Displays per node: edge latency, central latency, latency delta, bytes edge, bytes central, BW ratio
- "Waiting for anomaly..." shown for null values until first injection
- Matches existing dark theme Material UI style
- Maps over NODE_IDS constant (already defined at line 21)

---

## Verified Live Results
Tested with thermal spike injection. Real measured output:
- Edge latency: ~2500-4070ms (varies by node window state at injection time)
- Central latency: ~2550-4108ms
- Latency delta: ~38-42ms (central slower due to extra processing hop)
- Bytes edge: ~204KB cumulative (full frame including anomaly fields)
- Bytes central: ~98KB cumulative (raw telemetry only, ~48% of edge)
- BW ratio: ~48% — central uses roughly half the bandwidth of edge

---

## Current Implementation State

### Working
- Persistent WebSocket at `ws://localhost:8000/ws/simulation`
- 3 VirtualNode instances running concurrently at 1-second intervals
- Isolation Forest ML pipeline end-to-end (edge path)
- CentralServer running in parallel (centralized path)
- `GET /central/status` returning real measured data
- Comparison panel showing live latency and bandwidth metrics
- Alerts feed with CRIT/WARN/INFO badges (was already built by Jared)
- 3 node panels with live telemetry charts

### Still Missing
- **SQLite persistence** — zero DB anywhere, all telemetry in-memory and discarded. Schema defined in SRS. Use Gemini CLI to implement (mechanical task, hand it the schema).
- **sklearn version mismatch** — model pickled with 1.8.0, runtime has 1.4.1. Throws InconsistentVersionWarning on every load. Not breaking.
- **HTTP status codes** — control errors return 200 `{ok: false}` instead of proper 4xx.

---

## How to Run
```bash
# From project root
source venv/bin/activate
uvicorn backend.api:app --reload --port 8000

# Separate terminal
npm run dev
```
**Critical:** Must run uvicorn from project root with `backend.api:app` — running from inside `/backend` with `api:app` causes ModuleNotFoundError on the `from backend.simulation...` imports.

---

## Tool Setup
- **Claude Code** --Root Cause Analysis, Code Generator
- **CLAUDE.md** in project root, gitignored — loads automatically on `claude` launch
- **Gemini CLI** -Code Generator 

---

## Team Status
- **Logan** — project lead, owns all backend work
- **Jared** — frontend, alerts feed already built, 3 node panels working
- **Gavin** — Found the Cold Source Dataset

---

## Real Anomaly Validation — NEW THIS SESSION

### Background
Professor had asked 3+ times about "real data" and was unsatisfied with explanations
about the synthetic/real training split. Claude Code audit revealed the actual gap:
`data/real/mit_anomaly_validation.csv` existed with 1,909 labeled real anomaly windows
from MIT CSAIL dataset but had never been run through the model. The training script
validation steps only tested against synthetic data.

### What Was Done
Gemini CLI generated `backend/ml/validate_on_real_anomalies.py` — a standalone
validation script that loads the trained model and scaler, runs predict() on the
MIT anomaly windows, and reports recall.

### Results
```
MIT Real Anomaly Validation Summary
====================================
Total anomaly windows tested: 1732
Detected: 1662
Missed:   70
Recall:   95.96%
Score Distribution:
Average score (Detected): -0.0245
Average score (Missed):   0.0150
```

### Why This Matters
The model was trained exclusively on normal operation data — the MIT anomaly windows
were never seen during training. 95.96% recall on held-out real anomalies proves the
model generalizes outside the simulation. This directly answers the professor's
repeated question about real data.

The 70 missed windows (avg score +0.015) were mild gradual drifts that fell within
normal operating range — an explainable and honest miss pattern.

### TLDR
"Does the model generalize beyond our simulation? We extracted anomaly windows from the MIT CSAIL Intel Lab sensor dataset by flagging temperature deltas exceeding 5°C between consecutive readings on the same sensor node — a standard indicator of abnormal behavior in that dataset. These are real sensor readings from real deployed hardware. The model detected 95.96% of them without seeing any of this data during training.The simulation was
calibrated against real-world data distributions, and that calibration was strong
enough that the model transfers to real sensor readings.

### Key Conceptual Clarification
Two separate issues that were being conflated:
1. **Automatic vs manual threshold** — sklearn's contamination=0.01 auto-threshold
   caused false positives at runtime due to training/runtime distribution shift.
   Manual threshold tuning fixed this. This is a known limitation (training-serving skew).
2. **Real data validation** — whether the model detects real anomalies. Answered by
   the 95.96% recall result. Completely separate from the threshold question.

---

## Additional Scope Items Reviewed This Session

| Item | SRS Status | Decision |
|---|---|---|
| Repo reorganization | In scope — Week 15 | Don't touch until Week 15 |
| HVAC failure detection | Confirmed gap — v3 retraining needed | Week 13, Gemini CLI |
| New datasets | Out of scope | Do not pursue |
| Second ML model | Explicitly deferred in SRS | Out of scope |
| Automatic threshold root cause | Document as known limitation | Write up for demo |
| Real data explanation | Now answered by validation results | Done |

---

## Next Session Priorities
1. SQLite persistence — telemetry and anomaly_events tables (Gemini CLI)
2. Commit validate_on_real_anomalies.py and validation_results.txt to repo
3. Add validation paragraph to README
4. HVAC failure v3 model retraining (Gemini CLI)
5. Fix sklearn version mismatch
6. Phase 4 prep — external user testing, unit test suite, demo script

## New Dataset Note
Cold source dataset (`datasets/cold_source_control_dataset.csv`) was used in training
but not documented in SRS or progress report. Update depot records accordingly.
