from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os

from backend.simulation.thermal_model import ThermalModel
from backend.simulation.node import VirtualNode

# Use existing backend logic
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
# Core simulation (existing)
# -----------------------------
thermal_model = ThermalModel(
    air_mass=50.0,
    heat_capacity=1005.0,
    heat_coefficient=500.0,
    cooling_coefficient=300.0,
    initial_temperature=21.0,
    ambient_temperature=20.0,
)
node = VirtualNode(node_id="node-1", thermal_model=thermal_model, random_seed=42)

# -----------------------------
# Environment models (existing backend logic)
# -----------------------------
airflow_model = AirflowModel(nominal_flow=1.0, obstruction_ratio=0.0)
humidity_model = HumidityModel(
    initial_humidity=45.0,
    drift=0.05,
    noise_amplitude=0.2,
    random_seed=42,
)

# -----------------------------
# ML runtime (existing backend logic)
# -----------------------------
feature_extractor = SlidingWindowFeatureExtractor(window_size=10)

# Robust absolute path to the model file (works no matter where uvicorn is launched)
BACKEND_DIR = os.path.dirname(__file__)
MODEL_PATH = os.path.join(BACKEND_DIR, "ml", "isolation_forest.pkl")

anomaly_model: Optional[AnomalyModel] = None
model_loaded: bool = False
model_load_error: Optional[str] = None

try:
    anomaly_model = AnomalyModel(model_path=MODEL_PATH)
    model_loaded = True
except Exception as e:
    anomaly_model = None
    model_loaded = False
    model_load_error = str(e)


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


@app.get("/telemetry/step")
def telemetry_step():
    """
    Legacy endpoint (kept).
    Returns the base node telemetry (temperature, cpu_load, timestamp, node_id).
    """
    return node.step()


@app.get("/telemetry/env_step")
def telemetry_env_step():
    """
    Main endpoint for the dashboard:
    - node telemetry (temperature/cpu/timestamp)
    - airflow + humidity from real backend models
    - anomaly_score + is_anomaly from IsolationForest once the window is ready
    """
    base = node.step()

    airflow = airflow_model.step()
    humidity = humidity_model.step()

    enriched = {
        **base,
        "airflow": airflow,
        "humidity": humidity,
        "obstruction_ratio": airflow_model.obstruction_ratio,
    }

    # Feed the sliding window (expects keys: temperature/humidity/airflow/cpu_load)
    feature_extractor.add_point(enriched)

    anomaly_score: Optional[float] = None
    is_anomaly: Optional[bool] = None

    # Only predict once window is full and model is loaded
    if anomaly_model is not None and feature_extractor.is_window_ready():
        features = feature_extractor.extract_features()
        pred = anomaly_model.predict(features)
        anomaly_score = pred["score"]
        is_anomaly = pred["is_anomaly"]

    return {
        **enriched,
        "anomaly_score": anomaly_score,
        "is_anomaly": is_anomaly,
    }


# -----------------------------
# Controls (use real airflow_model methods)
# -----------------------------
@app.post("/controls/airflow_obstruction")
def set_airflow_obstruction(req: AirflowObstructionRequest):
    airflow_model.set_obstruction(req.ratio)
    return {"ok": True, "obstruction_ratio": airflow_model.obstruction_ratio}


@app.post("/controls/fan_failure")
def fan_failure():
    airflow_model.simulate_fan_failure()
    return {"ok": True, "obstruction_ratio": airflow_model.obstruction_ratio}


@app.post("/controls/reset_airflow")
def reset_airflow():
    airflow_model.reset()
    return {"ok": True, "obstruction_ratio": airflow_model.obstruction_ratio}

@app.post("/controls/set_humidity")
def set_humidity(req: HumiditySetRequest):
    # clamp 0..100
    humidity_model.current_humidity = max(0.0, min(100.0, float(req.humidity)))
    return {"ok": True, "humidity": humidity_model.current_humidity}


# -----------------------------
# ML utility endpoints (nice for frontend)
# -----------------------------
@app.get("/ml/status")
def ml_status():
    return {
        "model_loaded": model_loaded,
        "model_path": MODEL_PATH,
        "model_load_error": model_load_error,
        "window_size": feature_extractor.window_size,
        "window_ready": feature_extractor.is_window_ready(),
        "points_in_window": len(feature_extractor.window),
    }


@app.post("/ml/reload")
def ml_reload():
    """
    Reload the IsolationForest model from disk (dev convenience).
    """
    global anomaly_model, model_loaded, model_load_error

    try:
        anomaly_model = AnomalyModel(model_path=MODEL_PATH)
        model_loaded = True
        model_load_error = None
        return {"ok": True, "model_loaded": True}
    except Exception as e:
        anomaly_model = None
        model_loaded = False
        model_load_error = str(e)
        return {"ok": False, "model_loaded": False, "error": model_load_error}