# E-Habitat Session Summary — Part 2
**Date:** March 23, 2026
**Continues:** Session-Summary-3_23_26.md
**Supersedes:** "Still Missing" section of Session-Summary-3_23_26.md

---

## What Was Built This Session

### 1. SQLite Persistence Layer (`backend/simulation/database.py`) — NEW

Full database module using Python's built-in `sqlite3` only. No ORM, no SQLAlchemy, per SRS hard decision.

- `init_db()` — creates `db/` directory and `db/ehabitat.db` if they don't exist. Creates both tables with `IF NOT EXISTS`. Called once at module level on startup.
- `insert_telemetry(record: dict)` — inserts one telemetry row. Keys match column names exactly.
- `insert_anomaly_event(record: dict)` — inserts one anomaly event row.
- `check_same_thread=False` — required for FastAPI async context.
- Indexes created on `telemetry(timestamp)` and `telemetry(node_id)` for query performance.

Tables created:

```sql
CREATE TABLE IF NOT EXISTS telemetry (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    seq_id        INTEGER NOT NULL,
    node_id       TEXT NOT NULL,
    timestamp     REAL NOT NULL,
    temperature   REAL,
    humidity      REAL,
    airflow       REAL,
    cpu_load      REAL,
    is_anomaly    INTEGER,
    anomaly_score REAL
);

CREATE TABLE IF NOT EXISTS anomaly_events (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    seq_id               INTEGER NOT NULL,
    node_id              TEXT NOT NULL,
    injection_timestamp  REAL,
    edge_detection_ts    REAL,
    central_detection_ts REAL,
    edge_latency_ms      REAL,
    central_latency_ms   REAL,
    detection_source     TEXT,
    bytes_edge           INTEGER,
    bytes_central        INTEGER
);
```

### 2. api.py — UPDATED (DB wiring)

- `from backend.simulation.database import init_db, insert_telemetry, insert_anomaly_event` added.
- `init_db()` called at module level — DB and tables created on every server start if not present.
- `insert_telemetry()` called inside the WebSocket loop on every frame from every node.
- `insert_anomaly_event()` called on edge False→True transition with `detection_source="edge"`.
- `insert_anomaly_event()` called when CentralServer records a detection with `detection_source="central"`.

### 3. GET /db/anomaly_summary — NEW ENDPOINT

Read endpoint that gives the DB a purpose beyond write-only storage. Queries `anomaly_events` and returns aggregate statistics across all recorded injections:

```sql
SELECT
    detection_source,
    COUNT(*) as sample_count,
    ROUND(AVG(edge_latency_ms), 1) as avg_edge_ms,
    ROUND(AVG(central_latency_ms), 1) as avg_central_ms,
    ROUND(AVG(central_latency_ms - edge_latency_ms), 1) as avg_delta_ms,
    ROUND(MIN(central_latency_ms - edge_latency_ms), 1) as min_delta_ms,
    ROUND(MAX(central_latency_ms - edge_latency_ms), 1) as max_delta_ms
FROM anomaly_events
WHERE edge_latency_ms IS NOT NULL
AND central_latency_ms IS NOT NULL;
```

Returns `{ok: true, summary: [...]}`. Returns empty summary array if no injections recorded yet.

### 4. requirements.txt — FIXED

The ML/data science dependency layer was entirely absent from requirements.txt. numpy, joblib, and scikit-learn were installed in the venv but never recorded. Fixed by installing missing packages and regenerating:

```bash
pip install numpy joblib scikit-learn
pip freeze > requirements.txt
```

Final requirements.txt now includes all runtime dependencies including scipy and threadpoolctl pulled in by scikit-learn.

---

## Issues Resolved This Session

| Issue | Status in Previous Summary | Resolution |
|---|---|---|
| SQLite persistence | Not started | Fully implemented — telemetry and anomaly_events tables, read endpoint |
| sklearn version mismatch (1.4.1 vs 1.8.0) | Known warning, not breaking | Resolved as side effect — scikit-learn 1.8.0 now installed in venv, matches pickle version |
| requirements.txt incomplete | Not documented | Fixed — numpy, joblib, scikit-learn, scipy added |
| node_modules missing | Not documented | Resolved — `npm install` run, frontend now starts correctly |

---

## Verified Live Results

### DB Counts (after one session with thermal spike injections)
```
Telemetry rows: 384
Anomaly events: 7
```
384 telemetry rows = WebSocket loop writing every 1-second step across all 3 nodes. 7 anomaly events = both edge and central detections recorded across multiple injections.

### Summary Endpoint Output
```json
{
  "ok": true,
  "summary": [{
    "detection_source": "edge",
    "sample_count": 4,
    "avg_edge_ms": 2654.0,
    "avg_central_ms": 2912.0,
    "avg_delta_ms": 258.0,
    "min_delta_ms": 10.6,
    "max_delta_ms": 1000.0
  }]
}
```

### How These Numbers Were Obtained

The server was started, the frontend loaded, and the simulation run for approximately 10 seconds before a thermal spike was injected via the dashboard controls. After several injections across the session, the DB was queried directly and the summary endpoint was hit via curl. All numbers are real measured values from the running simulation — not mocked, not hardcoded.

---

## Analysis of Live Findings

### avg_delta_ms: 258ms

Central detection is on average 258ms slower than edge across 4 recorded injection events. This is the core architectural claim of the project — edge processes anomaly inference locally before transmitting, while central receives raw telemetry and runs inference after the fact. 258ms is a real, measured confirmation of that tradeoff.

**Presentation use:** This number with sample_count backing it is stronger than a single live demo moment. Run additional injections in demo prep to increase sample_count before the final presentation.

### min_delta_ms: 10.6ms / max_delta_ms: 1000ms — High Variance

The spread between 10.6ms and 1000ms is wide. This is not a bug — it is a real distributed systems phenomenon worth explaining in the presentation.

**Why this happens:** Both edge and central architectures use a sliding window feature extractor. At the moment of injection, each node's window is at a different fill state. A node whose window is nearly full will trigger detection much faster than a node whose window just reset. Since injection hits all three nodes simultaneously but each node has an independent window state, the delta between edge and central detection varies based on how much window data existed at the moment of injection.

**Academic framing:** This demonstrates that architectural latency comparisons in distributed systems are not fixed constants — they depend on system state at the time of the event. A student observing this variance gains more realistic intuition than if the delta were always the same number.

### sample_count: 4 vs anomaly_events rows: 7

The summary endpoint filters on `WHERE edge_latency_ms IS NOT NULL AND central_latency_ms IS NOT NULL`. 3 of the 7 anomaly_events rows have null values in one or both latency fields. This occurs when edge and central detections are recorded as separate rows rather than a single row with both timestamps populated.

**Not a data integrity problem** — the rows are correct, the filter is conservative. Do not misrepresent the sample size in the presentation; use the number the endpoint returns.

---

## Current Implementation State

### Working
- Persistent WebSocket at `ws://localhost:8000/ws/simulation`
- 3 VirtualNode instances running concurrently at 1-second intervals
- Isolation Forest ML pipeline end-to-end (edge path)
- CentralServer running in parallel (centralized path)
- `GET /central/status` — live per-node comparison metrics
- `GET /db/anomaly_summary` — aggregate historical metrics across all injections
- SQLite persistence — telemetry and anomaly_events writing on every step
- Comparison panel showing live latency and bandwidth metrics
- Alerts feed with CRIT/WARN/INFO badges
- 3 node panels with live telemetry charts
- sklearn version aligned — no more InconsistentVersionWarning

### Still Missing
- **HTTP status codes** — control errors return 200 `{ok: false}` instead of proper 4xx. Low priority, does not affect demo.
- **Aggregate summary on frontend** — `/db/anomaly_summary` endpoint exists but is not wired to any UI component. Data is available via curl. Consider adding to comparison panel in Phase 4 if Jared has bandwidth, otherwise use in presentation slides directly.
- **Unit test suite** — pytest not installed in venv. Phase 4 deliverable, owned by Gavin (do not block on him).
- **External user testing** — Phase 4, Weeks 13–14.
- **Demo script** — Phase 4, Week 15.

---

## Notes on Gemini CLI Usage This Session

Gemini completed the database implementation correctly but exhibited two recurring behaviors that cost time:

1. **Over-verification** — after confirming DB file exists and tables are correct, it continued chasing pytest (not installed) and attempted to delete the DB file before re-running a smoke test. Interrupted before it could execute the delete.

2. **Self-initiated scope expansion** — tasks not in the prompt (running existing test suites, reading requirements.txt unprompted) consumed time and caused drift.

**Mitigation going forward:** End every Gemini prompt with "Do not run any tests. Stop after the file is written and confirm what was changed." Keep prompts scoped to one file or one endpoint per invocation.

---

## How to Run

```bash
# Terminal 1 — Backend
source venv/bin/activate
uvicorn backend.api:app --reload --port 8000

# Terminal 2 — Frontend
npm run dev
```

**Critical:** Run uvicorn from project root with `backend.api:app`. Running from inside `/backend` with `api:app` causes ModuleNotFoundError on relative imports.

---

## Next Session Priorities

1. Wire `/db/anomaly_summary` to frontend comparison panel (optional — evaluate Jared's bandwidth first, presentation slides are an acceptable alternative)
2. HTTP status codes — fix control errors returning 200 `{ok: false}` (low priority)
3. Phase 4 prep — recruit external testers, begin demo script, unit test suite
4. Run 10+ injections in a single session to build sample_count for presentation data
