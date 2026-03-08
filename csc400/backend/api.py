from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict
import os
import asyncio
import json
import time

from backend.simulation.thermal_model import ThermalModel
from backend.simulation.node import VirtualNode
from backend.simulation.airflow import AirflowModel
from backend.simulation.humidity import HumidityModel
from backend.ml.feature_extraction import SlidingWindowFeatureExtractor
from backend.ml.model_loader import AnomalyModel

app = FastAPI(title="E-Habitat API")

# Allow your Next.js dev server to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# WebSocket Nodes Initialization
# -----------------------------
def make_node(node_id: str, seed: int, initial_temp: float):
    thermal = ThermalModel(50.0, 1005.0, 500.0, 300.0, 
                           initial_temp, 20.0)
    airflow = AirflowModel(nominal_flow=2.5, 
                           random_seed=seed + 1000)
    humidity = HumidityModel(45.0, 0.01, 0.2, 
                             seed + 2000, reference_temp=21.0)
    return VirtualNode(node_id, thermal, airflow, humidity,
                       random_seed=seed + 3000)

nodes: Dict[str, VirtualNode] = {
    'node-1': make_node('node-1', 42, 21.0),
    'node-2': make_node('node-2', 43, 22.0),
    'node-3': make_node('node-3', 44, 21.5),
}

# -----------------------------
# Request bodies
# -----------------------------
class AirflowObstructionRequest(BaseModel):
    ratio: float  # expected 0..1

class HumiditySetRequest(BaseModel):
    humidity: float  # expected 0..100


# -----------------------------
# Routes
# -----------------------------
@app.get("/health")
def health():
    return {"ok": True}


# -----------------------------
# WebSocket endpoint
# -----------------------------
@app.websocket('/ws/simulation')
async def websocket_simulation(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            frame = {}
            for node_id, node_inst in nodes.items():
                telemetry = node_inst.step()
                telemetry['node_id'] = node_id
                # Overwrite/Add numeric timestamp for latency calculation
                telemetry['timestamp'] = time.time()
                # Ensure anomaly fields are JSON serializable
                if telemetry.get('anomaly_score') is None:
                    telemetry['anomaly_score'] = None
                frame[node_id] = telemetry
            await websocket.send_json(frame)
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        print(f'[WS] Client disconnected')
    except Exception as e:
        print(f'[WS] Error: {e}')
        await websocket.close()


# -----------------------------
# Injection endpoint
# -----------------------------
@app.post('/simulation/inject')
async def inject_scenario(node_id: str, scenario: str):
    if node_id not in nodes:
        return {'error': f'Unknown node: {node_id}'}
    node_inst = nodes[node_id]
    if scenario == 'hvac_failure':
        node_inst.airflow_model.simulate_fan_failure()
        return {'status': 'injected', 'node': node_id, 
                'scenario': scenario}
    elif scenario == 'thermal_spike':
        node_inst.inject_thermal_spike(duration_seconds=30)
        return {'status': 'injected', 'node': node_id,
                'scenario': scenario}
    elif scenario == 'reset':
        nodes[node_id] = make_node(
            node_id, 
            {'node-1':42,'node-2':43,'node-3':44}[node_id],
            {'node-1':21.0,'node-2':22.0,'node-3':21.5}[node_id]
        )
        return {'status': 'reset', 'node': node_id}
    return {'error': f'Unknown scenario: {scenario}'}
