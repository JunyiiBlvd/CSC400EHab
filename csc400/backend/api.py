from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone

from backend.simulation.thermal_model import ThermalModel
from backend.simulation.node import VirtualNode

app = FastAPI(title="E-Habitat API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

thermal_model = ThermalModel(
    air_mass=50.0,
    heat_capacity=1005.0,
    heat_coefficient=500.0,
    cooling_coefficient=300.0,
    initial_temperature=21.0,
    ambient_temperature=20.0,
)
node = VirtualNode(node_id="node-1", thermal_model=thermal_model, random_seed=42)

# Simple environment, controls
obstruction_ratio = 0.0  # 0..1
BASE_AIRFLOW = 1.0
humidity = 45.0


class AirflowObstructionRequest(BaseModel):
    ratio: float


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/telemetry/step")
def telemetry_step():
    return node.step()


@app.get("/telemetry/env_step")
def telemetry_env_step():
    global humidity, obstruction_ratio

    base = node.step()

    airflow = max(0.0, BASE_AIRFLOW * (1.0 - obstruction_ratio))

    # small drift; rises when airflow is low
    humidity += 0.02 * (0.5 - airflow)
    humidity += 0.05
    humidity = max(0.0, min(100.0, humidity))

    if "timestamp" not in base:
        base["timestamp"] = datetime.now(timezone.utc).isoformat()

    anomaly_score: Optional[float] = None
    is_anomaly: Optional[bool] = None

    return {
        **base,
        "airflow": airflow,
        "humidity": humidity,
        "obstruction_ratio": obstruction_ratio,
        "anomaly_score": anomaly_score,
        "is_anomaly": is_anomaly,
    }


@app.post("/controls/airflow_obstruction")
def set_airflow_obstruction(req: AirflowObstructionRequest):
    global obstruction_ratio
    obstruction_ratio = max(0.0, min(1.0, req.ratio))
    return {"ok": True, "obstruction_ratio": obstruction_ratio}


@app.post("/controls/fan_failure")
def fan_failure():
    global obstruction_ratio
    obstruction_ratio = 1.0
    return {"ok": True, "obstruction_ratio": obstruction_ratio}


@app.post("/controls/reset_airflow")
def reset_airflow():
    global obstruction_ratio
    obstruction_ratio = 0.0
    return {"ok": True, "obstruction_ratio": obstruction_ratio}