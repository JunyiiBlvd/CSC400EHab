
import random
from backend.simulation.airflow import AirflowModel

def debug():
    seed = 42
    airflow = AirflowModel(nominal_flow=2.5, random_seed=seed)
    
    loads = []
    flows = []
    
    # Generate 1000 steps
    for _ in range(1000):
        # Semi-random load
        load = random.uniform(0.1, 0.9)
        flow = airflow.step(cpu_load=load)
        loads.append(load)
        flows.append(flow)
        
    def corr(x, y):
        n = len(x)
        mx = sum(x)/n
        my = sum(y)/n
        num = sum((x[i]-mx)*(y[i]-my) for i in range(n))
        den = (sum((x[i]-mx)**2 for i in range(n)) * sum((y[i]-my)**2 for i in range(n)))**0.5
        return num/den if den != 0 else 0

    print(f"Direct Correlation (1000 random loads): {corr(loads, flows):.4f}")

if __name__ == "__main__":
    debug()
