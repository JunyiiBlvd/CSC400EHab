from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/telemetry/step")
def telemetry_step():
    return node.step()
