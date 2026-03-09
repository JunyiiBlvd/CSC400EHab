from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict
import asyncio
import time

from backend.simulation.thermal_model import ThermalModel
from backend.simulation.node import VirtualNode
from backend.simulation.airflow import AirflowModel
from backend.simulation.humidity import HumidityModel
from backend.ml.model_loader import ModelLoader

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
    node.airflow_model.simulate_fan_failure()
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
        node_inst.airflow_model.simulate_fan_failure()
        return {"status": "injected", "node": node_id, "scenario": scenario}
    if scenario == "thermal_spike":
        node_inst.inject_thermal_spike(duration_seconds=30)
        return {"status": "injected", "node": node_id, "scenario": scenario}
    if scenario == "reset":
        nodes[node_id] = make_node(node_id, NODE_SEEDS[node_id], NODE_TEMPS[node_id])
        return {"status": "reset", "node": node_id}
    return {"error": f"Unknown scenario: {scenario}"}
