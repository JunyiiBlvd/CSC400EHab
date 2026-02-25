from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone

from backend.simulation.thermal_model import ThermalModel
from backend.simulation.node import VirtualNode

app = FastAPI(title="E-Habitat API")

# Allow your Next.js dev server to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple: one node in memory
thermal_model = ThermalModel(
    air_mass=50.0,
    heat_capacity=1005.0,
    heat_coefficient=500.0,
    cooling_coefficient=300.0,
    initial_temperature=21.0,
    ambient_temperature=20.0,
)
node = VirtualNode(node_id="node-1", thermal_model=thermal_model, random_seed=42)

# ---- NEW: simple "environment + controls" state (kept in memory) ----
# obstruction_ratio: 0.0 = no blockage, 1.0 = fully blocked airflow
obstruction_ratio = 0.0

# a simple baseline airflow value (0..1); we reduce it by obstruction_ratio
BASE_AIRFLOW = 1.0

# a simple humidity state that drifts; not physically perfect, just a useful signal
humidity = 45.0


class AirflowObstructionRequest(BaseModel):
    ratio: float  # expected 0..1


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/telemetry/step")
def telemetry_step():
    # legacy endpoint: keep as-is
    return node.step()


@app.get("/telemetry/env_step")
def telemetry_env_step():
    """
    NEW endpoint: includes airflow + humidity fields alongside node.step().
    This is intentionally simple (in-memory state) so the frontend has more signals.
    """
    global humidity, obstruction_ratio

    base = node.step()

    # airflow reduced by obstruction
    airflow = max(0.0, BASE_AIRFLOW * (1.0 - obstruction_ratio))

    # humidity drifts a little (and tends to rise when airflow is low)
    humidity += (0.02 * (0.5 - airflow))  # small coupling to airflow
    humidity += 0.05  # slow upward drift
    humidity = max(0.0, min(100.0, humidity))

    # Optional ML placeholders (keep consistent shape even if not used yet)
    anomaly_score: Optional[float] = None
    is_anomaly: Optional[bool] = None

    # Ensure timestamp exists (in case node.step() doesn't include it)
    if "timestamp" not in base:
        base["timestamp"] = datetime.now(timezone.utc).isoformat()

    return {
        **base,
        "airflow": airflow,
        "humidity": humidity,
        "anomaly_score": anomaly_score,
        "is_anomaly": is_anomaly,
        "obstruction_ratio": obstruction_ratio,
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