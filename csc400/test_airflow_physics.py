
import random
from backend.simulation.airflow import AirflowModel

def test():
    # Fixed seed for reproducibility
    seed = 42
    airflow = AirflowModel(nominal_flow=2.5, random_seed=seed)
    
    cpu_loads = [0.1, 0.9, 0.1, 0.9, 0.5]
    for load in cpu_loads:
        val = airflow.step(cpu_load=load)
        print(f"CPU: {load:.2f} -> Airflow: {val:.4f}")

if __name__ == "__main__":
    test()
