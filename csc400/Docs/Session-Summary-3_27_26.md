# E-Habitat Session Summary
**Date:** March 27, 2026
**Supersedes:** Session-Summary-3_23_26.md for implementation status

---

## What Was Built This Session

### 1. History API Endpoints (`backend/api.py` + `backend/simulation/database.py`) — NEW

Two new query functions added to `database.py`:
- `get_anomaly_events()` — `SELECT * FROM anomaly_events ORDER BY injection_timestamp DESC`, returns `list[dict]`
- `get_telemetry_range(node_id, start, end)` — parameterized query with `WHERE node_id = ? AND timestamp >= ? AND timestamp <= ?`, returns `list[dict]`

Two new GET endpoints added to `api.py` (no changes to WebSocket loop or existing endpoints):
- `GET /db/history/events` — returns all anomaly_events rows, newest first. Response: `{ok: true, events: [...]}`
- `GET /db/history/telemetry?node_id=&start=&end=` — returns telemetry rows for a node in a timestamp range. All three params required; returns 400 with `{ok: false, error: "..."}` if any are missing. Response: `{ok: true, rows: [...]}`

---

### 2. History Tab (`app/page.tsx`) — NEW

Tab bar added at top of page using MUI `Tabs`/`Tab`. Two tabs: **Dashboard** and **History**. Dark-themed (muted inactive, white selected, blue `#3b82f6` indicator line). WebSocket and all polling effects continue running regardless of active tab.

**Dashboard tab** — all existing content unchanged, wrapped in `{activeTab === 0 && ...}`.

**History tab** — new `HistoryTab` component (inline in `page.tsx`, no separate file):
- On mount, fetches `GET /db/history/events` and `GET /db/anomaly_summary` in parallel via `Promise.all`
- Refresh button re-fetches both endpoints

**Aggregate stats banner** — row of 6 MUI Paper cards above the events table:

| Card | Source field |
|---|---|
| Total Events | `sample_count` |
| Avg Edge Latency | `avg_edge_ms` |
| Avg Central Latency | `avg_central_ms` |
| Avg Delta | `avg_delta_ms` |
| Min Delta | `min_delta_ms` |
| Max Delta | `max_delta_ms` |

Values formatted to 1 decimal + "ms" suffix. Shows "—" for all cards if no events with both latencies exist yet.

**Events table** — MUI Table with 8 columns: Node ID, Detection Source, Injection Time (Unix float → `toLocaleString()`), Edge Latency (ms), Central Latency (ms), Delta (ms), Bytes Edge, Bytes Central. Null values show "—". Delta computed client-side (`central - edge`). Empty-state message shown if no events.

New style constants added at module level: `tabsStyle`, `thStyle`, `tdStyle`, `statCardStyle`.

---

### 3. Coolant Leak Anomaly Scenario — NEW

**`backend/simulation/node.py`** — three additions:

1. Three state flags in `__init__` under "Anomaly Injection State":
   ```python
   self.coolant_leak_active = False
   self.coolant_leak_remaining_steps = 0
   self.coolant_leak_base_humidity = 0.0
   ```

2. `inject_coolant_leak()` method (after `inject_hvac_failure`):
   - Sets `coolant_leak_active = True`, `coolant_leak_remaining_steps = 20`
   - Captures `self.humidity_model.current_humidity` as baseline at injection time

3. Override block in `step()`, inserted **after physics step 5 (humidity update), before telemetry dict construction and ML inference**:
   - While `remaining_steps > 0`: `current_humidity = min(85.0, base + 2.5 * (20 - remaining_steps))`, decrement remaining
   - When `remaining_steps == 0`: hold at `min(85.0, base + 50.0)`
   - The overridden value flows directly into `feature_extractor.add_point()` — anomalous humidity hits the sliding window and ML inference

**`backend/api.py`** — `coolant_leak` case added to `POST /simulation/inject` handler (between `thermal_spike` and `reset`):
```python
if scenario == "coolant_leak":
    node_inst.inject_coolant_leak()
    if central_server is not None:
        central_server.record_injection(node_id, time.time())
    return {"status": "injected", "node": node_id, "scenario": scenario}
```

---

### 4. Humidity Feasibility Test (`backend/tests/test_humidity_feasibility.py`) — NEW

Standalone script (no FastAPI, no pytest, no server). Answers: does the current Isolation Forest detect coolant_leak without retraining?

Structure:
- Phase A: 30 baseline steps, logs humidity + anomaly_score + is_anomaly per step
- Phase B: inject coolant_leak, 30 more steps, same logging
- Phase C: summary — baseline max score, injection max score, model threshold, first detection step, DETECTABLE/NOT DETECTABLE verdict

---

### 5. Humidity Feature Analysis (`backend/tests/test_humidity_feature_analysis.py`) — NEW

Diagnostic script for understanding *why* the model misses coolant_leak.

Structure:
- Phase A/B: same 30+30 step sequence, prints **full 12-feature vector** at every step
- Phase C: table comparing last baseline vector to peak injection vector (step with lowest score), sorted by % change descending
- Phase D: interpretation — computes avg % shift for humidity features vs all other features, prints root-cause finding

---

## Verified Live Results

### Feasibility Test — Run Confirmed
```
PHASE C — Summary
  Baseline max score : +0.2713
  Injection max score: +0.2490
  Model threshold    : -0.6134
  First detection at : NO DETECTION

  VERDICT: NOT DETECTABLE — model does not trigger on humidity anomaly, retraining required
```

Humidity ramped from ~45% to 85% over 20 steps. Score dropped from +0.27 to a minimum of +0.07 (step 15, humidity=80.12%) — never negative, never near -0.6134. After the hold phase began at 85%, the score drifted back toward baseline (+0.23 by step 30) as the window filled with constant values that look "normal" to the model.

### Feature Analysis — Run Confirmed
```
PHASE C — Feature delta (peak = most-anomalous step, score +0.0708)

  Feature       Baseline      Injection     % change
  hum_var       +0.026359     +51.562500    +195517.9%
  hum_roc       +0.103182     +22.500000    +21706.1%
  cpu_roc       +0.109091     -0.097104     -189.0%
  air_var       +0.004653     +0.000326     -93.0%
  (all other features <3% change)

PHASE D — Interpretation
  Humidity feature avg % shift   : 72425.3%
  Other feature avg % shift      : 42.4%

  FINDING: Humidity features shift significantly MORE than other signals.
  The model's decision boundary does not weight humidity strongly enough.
  Retraining with humidity anomaly examples in the training set is needed.
```

**Root cause confirmed:** `hum_var` and `hum_roc` explode by 5 and 3 orders of magnitude respectively during injection. Temperature, airflow, and CPU all move less than 2%. The model sees the humidity shift in feature space but the Isolation Forest's tree ensemble was trained only on steady-state data — it never learned that large `hum_var` + large `hum_roc` while all other signals are stable is anomalous. The trees route these points through the same isolation paths used for normal humidity variation, producing short paths (high score = normal) instead of long paths (low/negative score = anomalous).

---

## Current Implementation State

### Working
- Persistent WebSocket at `ws://localhost:8000/ws/simulation`
- 3 VirtualNode instances streaming telemetry at 1-second intervals
- Isolation Forest ML pipeline end-to-end (edge path)
- CentralServer running in parallel (centralized path)
- SQLite persistence — telemetry and anomaly_events tables writing every step
- `GET /central/status` returning real measured latency and bandwidth data
- `GET /db/anomaly_summary` returning aggregate latency stats
- `GET /db/history/events` returning all anomaly events
- `GET /db/history/telemetry` returning time-ranged telemetry by node
- `POST /simulation/inject` handling: `thermal_spike`, `hvac_failure`, `coolant_leak`, `reset`
- Dashboard tab — controls panel, gauges, alerts feed, comparison panel, 3 node charts
- History tab — aggregate stats banner + events table, both fetched on mount + refresh
- `thermal_spike` scenario — detectable by ML, confirmed in prior sessions
- `coolant_leak` scenario — physics working, injected via API, **not yet detectable by ML**

### Still Missing / Known Gaps
- **coolant_leak ML detection** — confirmed NOT DETECTABLE by current model. Root cause: model trained only on steady-state data. Fix: retrain with humidity anomaly examples. `hum_var` shifts +195,517% during injection but score never crosses -0.6134 threshold.
- **hvac_failure ML detection** — also not reliably detected (documented gap from prior session). Same class of problem — model not trained on that anomaly type.
- **Retraining pipeline** — no script yet for adding coolant_leak or hvac_failure anomaly windows to training data and retraining the model.
- **`/db/history/telemetry` frontend wiring** — endpoint is live and correct but not yet used by any frontend component. Available for a telemetry drill-down view if added.
- **HTTP status codes** — control errors still return 200 `{ok: false}` instead of proper 4xx. Low priority.
- **Unit test suite** — pytest not installed in venv, Gavin owns (do not block on him).

---

## How to Run

```bash
# From project root
source venv/bin/activate
PYTHONPATH=. uvicorn backend.api:app --reload --port 8000

# Separate terminal
npm run dev

# Feasibility test (no server needed)
PYTHONPATH=. python3 backend/tests/test_humidity_feasibility.py

# Feature analysis (no server needed)
PYTHONPATH=. python3 backend/tests/test_humidity_feature_analysis.py
```

**Critical:** Always `PYTHONPATH=.` with `uvicorn backend.api:app` from project root — omitting PYTHONPATH breaks all `from backend.simulation...` imports.

---

## Files Changed This Session

| File | Status | Change |
|---|---|---|
| `backend/simulation/database.py` | Modified | Added `get_anomaly_events()`, `get_telemetry_range()` |
| `backend/api.py` | Modified | Added `GET /db/history/events`, `GET /db/history/telemetry`, `coolant_leak` inject case, `JSONResponse` import |
| `backend/simulation/node.py` | Modified | Added `inject_coolant_leak()`, coolant leak state flags, `step()` override block |
| `app/page.tsx` | Modified | Tab bar, History tab, `HistoryTab` component, stats banner, events table, 4 new style constants |
| `backend/tests/test_humidity_feasibility.py` | New | Standalone feasibility test — runs and confirmed NOT DETECTABLE |
| `backend/tests/test_humidity_feature_analysis.py` | New | Feature-space diagnostic — root cause confirmed |

---

## Team Status
- **Logan** — project lead, owns all backend and session work
- **Jared** — frontend; alerts feed and node panels already built
- **Gavin** — found cold source dataset; unit test suite (not blocking)

---

## Next Session Priorities
1. **Retrain model with coolant_leak anomaly windows** — generate humidity ramp training examples, add to training set, retrain `model_v2_hybrid_real.pkl` and `scaler_v2.pkl`, re-run feasibility test to confirm detection
2. **HVAC failure retraining** — same problem class, same fix, can batch with coolant_leak retrain
3. **Wire coolant_leak inject button in frontend** — controls panel currently has thermal_spike only
4. **Wire `/db/history/telemetry`** into a frontend drill-down if in scope
5. **Unit test suite** — Gavin (do not block)
