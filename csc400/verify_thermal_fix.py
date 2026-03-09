from backend.simulation.thermal_model import ThermalModel
from backend.simulation.airflow import AirflowModel
from backend.simulation.humidity import HumidityModel
from backend.simulation.node import VirtualNode
import numpy as np

def run_verification():
    thermal = ThermalModel(50.0, 1005.0, 500.0, 300.0, 21.0, 20.0)
    airflow = AirflowModel(nominal_flow=2.5, random_seed=1042)
    humidity = HumidityModel(45.0, 0.0, 0.01, 2042, reference_temp=21.0)
    node = VirtualNode('test', thermal, airflow, humidity, random_seed=42)

    baseline_temps = []
    print("Running baseline (50 steps)...")
    any_early_anomaly = False
    for i in range(50):
        t = node.step()
        baseline_temps.append(t['temperature'])
        if t['is_anomaly']:
            any_early_anomaly = True
    
    baseline = sum(baseline_temps[-10:]) / 10
    print(f'Baseline temp: {baseline:.4f}C')
    print()

    print("Injecting thermal spike (duration=120, lag=40)...")
    node.inject_thermal_spike(duration_seconds=120, lag_seconds=40)

    print(f'Step | CPU  | Airflow | Temp    | Delta   | Score   | Anomaly')
    print('-' * 70)
    
    results = []
    for i in range(1, 121):
        t = node.step()
        delta = t['temperature'] - baseline
        score = t['anomaly_score'] if t['anomaly_score'] is not None else 0
        results.append(t)
        
        if i <= 10 or i % 10 == 0:
            print(f'{i:4} | {t["cpu_load"]:.2f} | '
                  f'{t["airflow"]:.4f} | '
                  f'{t["temperature"]:.4f} | '
                  f'{delta:+.4f} | '
                  f'{score:+.4f} | '
                  f'{t["is_anomaly"]}')

    # Criteria Verification
    print("\n" + "="*30)
    print("VERIFICATION RESULTS")
    print("="*30)
    
    c1 = not any_early_anomaly
    print(f"1. No early anomaly: {'PASS' if c1 else 'FAIL'}")
    
    c2 = all(r['cpu_load'] == 1.0 for r in results)
    print(f"2. CPU Load = 1.0: {'PASS' if c2 else 'FAIL'}")
    
    # Airflow check during lag (first 40 steps of results)
    # Expected airflow: ~0.375 (15% of 2.5)
    lag_airflow = [r['airflow'] for r in results[:40]]
    c3 = all(abs(a - 0.375) < 0.01 for a in lag_airflow)
    print(f"3. Airflow reduction (~0.375): {'PASS' if c3 else 'FAIL'} (avg: {np.mean(lag_airflow):.4f})")
    
    # Temperature rise by step 40
    temp_at_40 = results[39]['temperature']
    rise_at_40 = temp_at_40 - baseline
    c4 = rise_at_40 >= 0.25
    print(f"4. Temp rise >= 0.25C at step 40: {'PASS' if c4 else 'FAIL'} (rise: {rise_at_40:.4f}C)")
    
    # Anomaly detected between spike steps 10-50 (overall steps 60-100)
    # The results list index 0 is spike step 1 (total step 51)
    # So we check results index 9 to 49.
    detected_in_range = any(r['is_anomaly'] for r in results[9:50])
    c5 = detected_in_range
    print(f"5. Anomaly detected in range: {'PASS' if c5 else 'FAIL'}")
    
    # is_anomaly comes from ML model (already implied by it being False early and True later)
    # but we can double check it's not hardcoded to True immediately
    not_immediate = not results[0]['is_anomaly'] 
    print(f"6. Not hardcoded (not True at step 1): {'PASS' if not_immediate else 'FAIL'}")

    if all([c1, c2, c3, c4, c5, not_immediate]):
        print("\nOVERALL: PASS")
    else:
        print("\nOVERALL: FAIL")

if __name__ == "__main__":
    run_verification()
