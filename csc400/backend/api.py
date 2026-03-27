from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Optional
import asyncio
import json
import time
import sqlite3

from backend.simulation.thermal_model import ThermalModel
from backend.simulation.node import VirtualNode
from backend.simulation.airflow import AirflowModel
from backend.simulation.humidity import HumidityModel
from backend.simulation.central_server import CentralServer
from backend.ml.model_loader import ModelLoader
from backend.simulation.database import init_db, insert_telemetry, insert_anomaly_event, get_anomaly_events, get_telemetry_range, DB_PATH

init_db()

app = FastAPI(title="E-Habitat API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def make_node(node_id: str, seed: int, initial_temp: float):
    thermal = ThermalModel(50.0, 1005.0, 500.0, 300.0, initial_temp, 20.0)
    airflow = AirflowModel(nominal_flow=2.5, random_seed=seed + 1000)
    humidity = HumidityModel(45.0, 0.01, 0.2, seed + 2000, reference_temp=21.0)
    return VirtualNode(node_id, thermal, airflow, humidity, random_seed=seed + 3000)


NODE_SEEDS = {"node-1": 42, "node-2": 43, "node-3": 44}
NODE_TEMPS = {"node-1": 21.0, "node-2": 22.0, "node-3": 21.5}

nodes: Dict[str, VirtualNode] = {
    node_id: make_node(node_id, NODE_SEEDS[node_id], NODE_TEMPS[node_id])
    for node_id in NODE_SEEDS
}

# CentralServer — shared ModelLoader, separate from the per-node instances
try:
    _central_model = ModelLoader()
    central_server = CentralServer(_central_model)
except Exception as e:
    print(f"[CentralServer] Failed to load model, central detection disabled: {e}")
    central_server = None

# Per-node state for detecting edge False→True anomaly transitions
_prev_edge_anomaly: Dict[str, bool] = {nid: False for nid in NODE_SEEDS}
_prev_central_detection: Dict[str, bool] = {nid: False for nid in NODE_SEEDS}
_step_seq: Dict[str, int] = {nid: 0 for nid in NODE_SEEDS}


class NodeTargetRequest(BaseModel):
    node_id: str


class AirflowObstructionRequest(NodeTargetRequest):
    ratio: float


class HumiditySetRequest(NodeTargetRequest):
    humidity: float


def reload_models() -> tuple[bool, str | None]:
    try:
        for node in nodes.values():
            node.anomaly_model = ModelLoader()
        return True, None
    except Exception as e:
        for node in nodes.values():
            node.anomaly_model = None
        return False, str(e)


@app.get("/health")
def health():
    return {"ok": True, "nodes": list(nodes.keys())}


@app.get("/api/ml/status")
def ml_status():
    node = nodes["node-1"]
    model = getattr(node, "anomaly_model", None)
    extractor = node.feature_extractor
    return {
        "model_loaded": model is not None,
        "model_path": getattr(model, "model_path", ""),
        "model_load_error": None if model is not None else "Model not loaded",
        "window_size": extractor.window_size,
        "window_ready": extractor.is_window_ready(),
        "points_in_window": len(extractor.window),
    }


@app.post("/api/ml/reload")
def ml_reload():
    ok, error = reload_models()
    return {"ok": ok, "model_loaded": ok, "error": error}


@app.post("/api/controls/airflow_obstruction")
def set_airflow_obstruction(body: AirflowObstructionRequest):
    if body.node_id not in nodes:
        return {"ok": False, "error": f"Unknown node: {body.node_id}"}

    ratio = max(0.0, min(1.0, body.ratio))
    node = nodes[body.node_id]
    node.airflow_model.set_obstruction(ratio)
    return {"ok": True, "node_id": body.node_id, "obstruction_ratio": ratio}


@app.post("/api/controls/fan_failure")
def fan_failure(body: NodeTargetRequest):
    if body.node_id not in nodes:
        return {"ok": False, "error": f"Unknown node: {body.node_id}"}

    node = nodes[body.node_id]
    node.inject_hvac_failure(duration_seconds=40)
    if central_server is not None:
        central_server.record_injection(body.node_id, time.time())
    return {"ok": True, "node_id": body.node_id, "obstruction_ratio": 1.0}


@app.post("/api/controls/reset_airflow")
def reset_airflow(body: NodeTargetRequest):
    if body.node_id not in nodes:
        return {"ok": False, "error": f"Unknown node: {body.node_id}"}

    node = nodes[body.node_id]
    node.airflow_model.reset()
    return {"ok": True, "node_id": body.node_id, "obstruction_ratio": 0.0}


@app.post("/api/controls/set_humidity")
def set_humidity(body: HumiditySetRequest):
    if body.node_id not in nodes:
        return {"ok": False, "error": f"Unknown node: {body.node_id}"}

    humidity = max(0.0, min(100.0, body.humidity))
    node = nodes[body.node_id]
    node.humidity_model.initial_humidity = humidity
    node.humidity_model.current_humidity = humidity
    return {"ok": True, "node_id": body.node_id, "humidity": humidity}


@app.get("/central/status")
def central_status():
    if central_server is None:
        return {"ok": False, "error": "Central server not available"}
    return {"ok": True, "nodes": central_server.get_status()}


@app.get("/db/anomaly_summary")
def get_anomaly_summary():
    query = """
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
    """
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query)
        row = cursor.fetchone()
        conn.close()

        if row and row["sample_count"] > 0:
            # Convert Row to dict
            return {"ok": True, "summary": [dict(row)]}
        else:
            return {"ok": True, "summary": []}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.get("/db/history/events")
def history_events():
    events = get_anomaly_events()
    return {"ok": True, "events": events}


@app.get("/db/history/telemetry")
def history_telemetry(
    node_id: Optional[str] = None,
    start: Optional[float] = None,
    end: Optional[float] = None,
):
    if node_id is None or start is None or end is None:
        return JSONResponse(
            status_code=400,
            content={"ok": False, "error": "node_id, start, and end are required"},
        )
    rows = get_telemetry_range(node_id, start, end)
    return {"ok": True, "rows": rows}


@app.websocket("/ws/simulation")
async def websocket_simulation(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            frame = {}
            for node_id, node_inst in nodes.items():
                telemetry = node_inst.step()
                telemetry["node_id"] = node_id
                telemetry["timestamp"] = time.time()
                telemetry["obstruction_ratio"] = node_inst.airflow_model.obstruction_ratio
                if telemetry.get("anomaly_score") is None:
                    telemetry["anomaly_score"] = None
                frame[node_id] = telemetry

                # Increment sequence
                _step_seq[node_id] += 1

                # DB Insert: Telemetry
                insert_telemetry({
                    "seq_id": _step_seq[node_id],
                    "node_id": node_id,
                    "timestamp": telemetry["timestamp"],
                    "temperature": telemetry.get("temperature"),
                    "humidity": telemetry.get("humidity"),
                    "airflow": telemetry.get("airflow"),
                    "cpu_load": telemetry.get("cpu_load"),
                    "is_anomaly": 1 if telemetry.get("is_anomaly") else 0,
                    "anomaly_score": telemetry.get("anomaly_score")
                })

                # Detect edge False→True transition
                curr_anomaly: bool = telemetry.get("is_anomaly", False)
                edge_ts = None
                if curr_anomaly and not _prev_edge_anomaly[node_id]:
                    edge_ts = time.time()

                    # DB Insert: Edge Anomaly Event
                    c_status = central_server.get_status().get(node_id, {}) if central_server else {}
                    injection_ts = None
                    if central_server and node_id in getattr(central_server, "_records", {}):
                        injection_ts = central_server._records[node_id].get("injection_ts")

                    insert_anomaly_event({
                        "seq_id": _step_seq[node_id],
                        "node_id": node_id,
                        "injection_timestamp": injection_ts,
                        "edge_detection_ts": edge_ts,
                        "central_detection_ts": None,
                        "edge_latency_ms": c_status.get("edge_latency_ms"),
                        "central_latency_ms": None,
                        "detection_source": "edge",
                        "bytes_edge": len(json.dumps(telemetry).encode()),
                        "bytes_central": c_status.get("bytes_central")
                    })
                _prev_edge_anomaly[node_id] = curr_anomaly

                # Feed central server with raw telemetry (no anomaly fields)
                if central_server is not None:
                    raw_telemetry = {
                        k: telemetry[k]
                        for k in ("temperature", "humidity", "airflow", "cpu_load")
                    }
                    central_server.receive_telemetry(
                        node_id, raw_telemetry, _step_seq[node_id], edge_ts,
                        bytes_edge=len(json.dumps(telemetry).encode()),
                    )

                    # DB Insert: Central Anomaly Event check
                    c_status = central_server.get_status().get(node_id, {})
                    c_det_ts = c_status.get("central_detection_ts")
                    if c_det_ts and not _prev_central_detection[node_id]:
                        injection_ts = central_server._records[node_id].get("injection_ts")
                        insert_anomaly_event({
                            "seq_id": _step_seq[node_id],
                            "node_id": node_id,
                            "injection_timestamp": injection_ts,
                            "edge_detection_ts": c_status.get("edge_detection_ts"),
                            "central_detection_ts": c_det_ts,
                            "edge_latency_ms": c_status.get("edge_latency_ms"),
                            "central_latency_ms": c_status.get("central_latency_ms"),
                            "detection_source": "central",
                            "bytes_edge": c_status.get("bytes_edge"),
                            "bytes_central": c_status.get("bytes_central")
                        })
                        _prev_central_detection[node_id] = True
                    elif not c_det_ts:
                        _prev_central_detection[node_id] = False

            await websocket.send_json(frame)
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        print("[WS] Client disconnected")
    except Exception as e:
        print(f"[WS] Error: {e}")
        await websocket.close()


@app.post("/simulation/inject")
async def inject_scenario(node_id: str, scenario: str):
    if node_id not in nodes:
        return {"error": f"Unknown node: {node_id}"}
    node_inst = nodes[node_id]
    if scenario == "hvac_failure":
        # Ramped injection — sustains air_roc signal for 15 steps vs 9 for instant snap
        # Confirmed DETECTABLE: 15-step streak, min score 0.073, threshold 0.15
        # Profiled 2026-03-27 — backend/tests/test_hvac_ramp_feasibility.py
        node_inst.inject_hvac_failure(duration_seconds=40)
        if central_server is not None:
            central_server.record_injection(node_id, time.time())
        return {"status": "injected", "node": node_id, "scenario": scenario}
    if scenario == "thermal_spike":
        node_inst.inject_thermal_spike(duration_seconds=30)
        if central_server is not None:
            central_server.record_injection(node_id, time.time())
        return {"status": "injected", "node": node_id, "scenario": scenario}
    if scenario == "coolant_leak":
        node_inst.inject_coolant_leak()
        if central_server is not None:
            central_server.record_injection(node_id, time.time())
        return {"status": "injected", "node": node_id, "scenario": scenario}
    if scenario == "reset":
        nodes[node_id] = make_node(node_id, NODE_SEEDS[node_id], NODE_TEMPS[node_id])
        nodes[node_id].reset_anomaly_state()
        return {"status": "reset", "node": node_id}
    return {"error": f"Unknown scenario: {scenario}"}
