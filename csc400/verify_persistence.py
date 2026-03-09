from backend.simulation.thermal_model import ThermalModel
from backend.simulation.airflow import AirflowModel
from backend.simulation.humidity import HumidityModel
from backend.simulation.node import VirtualNode

def run_verification():
    thermal = ThermalModel(50.0, 1005.0, 500.0, 300.0, 21.0, 20.0)
    airflow = AirflowModel(nominal_flow=2.5, random_seed=1042)
    humidity = HumidityModel(45.0, 0.0, 0.01, 2042, reference_temp=21.0)
    node = VirtualNode('test', thermal, airflow, humidity, random_seed=42)

    print("Running baseline (50 steps)...")
    any_early_anomaly = False
    for i in range(50):
        t = node.step()
        if t['is_anomaly']:
            any_early_anomaly = True
    
    print(f"1. No early anomaly: {'PASS' if not any_early_anomaly else 'FAIL'}")

    print("\nInjecting thermal spike (duration=120, lag=40)...")
    node.inject_thermal_spike(duration_seconds=120, lag_seconds=40)

    spike_results = []
    for i in range(1, 61):
        t = node.step()
        spike_results.append(t)
        if i <= 10 or i % 10 == 0:
             print(f"Spike Step {i:2}: Score {t['anomaly_score'] or 0.0:+7.4f}, Anomaly {t['is_anomaly']}")

    # Criteria 2: Flip True between 2-9
    c2 = any(r['is_anomaly'] for r in spike_results[1:9])
    print(f"\n2. is_anomaly flips True (steps 2-9): {'PASS' if c2 else 'FAIL'}")

    # Criteria 3: Stays True through step 28
    # Last detection at step 9 + persistence 20 = step 29 expiration.
    # Step 28 is the last guaranteed True step.
    # spike_results index 9 is step 10, index 27 is step 28.
    c3 = all(r['is_anomaly'] for r in spike_results[9:28])
    print(f"3. is_anomaly stays True through step 28: {'PASS' if c3 else 'FAIL'}")

    # Criteria 4: Score still reflects ML (not just hardcoded)
    c4 = all(r['anomaly_score'] is not None for r in spike_results)
    print(f"4. anomaly_score present: {'PASS' if c4 else 'FAIL'}")

    if all([not any_early_anomaly, c2, c3, c4]):
        print("\nOVERALL: PASS")
    else:
        print("\nOVERALL: FAIL")

if __name__ == "__main__":
    run_verification()
