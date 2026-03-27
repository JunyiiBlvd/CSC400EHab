"""
Clean Baseline Profile Test
============================
Runs a single VirtualNode for 120 steps with PRODUCTION physics parameters
(identical to api.py make_node, node-1 / seed=42) and NO anomaly injection.

Purpose: establish the clean noise floor of the anomaly score so we know
how much separation exists between normal operation and the known anomaly
detection thresholds (HVAC min ~0.082, coolant leak min ~0.070).

Run from project root:
    PYTHONPATH=. python3 backend/tests/test_clean_baseline_profile.py
"""

import sys
import os

# ---------------------------------------------------------------------------
# Imports — only backend/simulation/ and backend/ml/
# ---------------------------------------------------------------------------
from backend.simulation.thermal_model import ThermalModel
from backend.simulation.airflow import AirflowModel
from backend.simulation.humidity import HumidityModel
from backend.simulation.node import VirtualNode

# ModelLoader is imported transitively through VirtualNode, but we do not
# import FastAPI, the database layer, or any server component.

# ---------------------------------------------------------------------------
# Production parameters — copied verbatim from api.py make_node(), node-1
# node-1: seed=42, initial_temp=21.0
# ---------------------------------------------------------------------------
SEED       = 42
INIT_TEMP  = 21.0

STEPS      = 120

# Known anomaly score lower bounds (from prior validation runs)
HVAC_MIN_SCORE    = 0.082
COOLANT_MIN_SCORE = 0.070


def build_node() -> VirtualNode:
    """Instantiate a fresh VirtualNode using api.py production parameters."""
    thermal = ThermalModel(
        air_mass=50.0,
        heat_capacity=1005.0,
        heat_coefficient=500.0,
        cooling_coefficient=300.0,
        initial_temperature=INIT_TEMP,
        ambient_temperature=20.0,
    )
    airflow = AirflowModel(
        nominal_flow=2.5,
        random_seed=SEED + 1000,   # 1042
    )
    humidity = HumidityModel(
        initial_humidity=45.0,
        drift=0.01,
        noise_amplitude=0.2,
        random_seed=SEED + 2000,   # 2042
        reference_temp=21.0,
    )
    return VirtualNode(
        node_id="test-baseline-node",
        thermal_model=thermal,
        airflow_model=airflow,
        humidity_model=humidity,
        random_seed=SEED + 3000,   # 3042
    )


def run():
    node = build_node()

    records = []  # list of dicts, one per step

    print("=" * 70)
    print("CLEAN BASELINE PROFILE — 120 steps, no anomaly injection")
    print(f"Production params: air_mass=50.0  heat_coeff=500.0  cool_coeff=300.0")
    print(f"                   nominal_flow=2.5  init_temp={INIT_TEMP}  seed={SEED}")
    print("=" * 70)
    print()
    print(f"{'Step':>4}  {'Temp':>7}  {'Airflow':>8}  {'Humidity':>9}  "
          f"{'CPU':>6}  {'Score':>10}  {'Anomaly'}")
    print("-" * 70)

    for step in range(1, STEPS + 1):
        t = node.step()

        score     = t.get('anomaly_score')   # None for first 9 steps (window not full)
        is_anom   = t.get('is_anomaly', False)

        records.append({
            'step':      step,
            'temp':      t['temperature'],
            'airflow':   t['airflow'],
            'humidity':  t['humidity'],
            'cpu_load':  t['cpu_load'],
            'score':     score,
            'is_anomaly': is_anom,
        })

        score_str = f"{score:10.6f}" if score is not None else f"{'(warmup)':>10}"
        anom_str  = "*** ANOMALY ***" if is_anom else "ok"

        print(f"{step:4}  {t['temperature']:7.3f}  {t['airflow']:8.4f}  "
              f"{t['humidity']:9.4f}  {t['cpu_load']:6.4f}  {score_str}  {anom_str}")

    # -----------------------------------------------------------------------
    # Summary statistics (only steps with a valid score, i.e. steps 10–120)
    # -----------------------------------------------------------------------
    scored = [r for r in records if r['score'] is not None]
    scores = [r['score'] for r in scored]

    import statistics

    min_score  = min(scores)
    max_score  = max(scores)
    mean_score = statistics.mean(scores)
    std_score  = statistics.stdev(scores) if len(scores) > 1 else 0.0

    below_010  = sum(1 for s in scores if s < 0.10)
    below_005  = sum(1 for s in scores if s < 0.05)
    anom_count = sum(1 for r in records if r['is_anomaly'])

    lowest_10 = sorted(scored, key=lambda r: r['score'])[:10]

    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Steps with valid score  : {len(scored)}  (steps 1–9 are warmup, no score)")
    print(f"Min score               : {min_score:.6f}")
    print(f"Max score               : {max_score:.6f}")
    print(f"Mean score              : {mean_score:.6f}")
    print(f"Std deviation           : {std_score:.6f}")
    print()
    print("Lowest 10 scores:")
    print(f"  {'Step':>4}  {'Score':>10}  {'Temp':>7}  {'Airflow':>8}")
    for r in lowest_10:
        print(f"  {r['step']:4}  {r['score']:10.6f}  {r['temp']:7.3f}  {r['airflow']:8.4f}")

    print()
    print(f"Steps with score < 0.10 (near-threshold zone) : {below_010}")
    print(f"Steps with score < 0.05                       : {below_005}")

    print()
    if anom_count == 0:
        print(f"is_anomaly == True count : {anom_count}  (correct — no anomalies injected)")
    else:
        print(f"!!! WARNING: is_anomaly == True count : {anom_count}  "
              f"— FALSE POSITIVES DETECTED !!!")

    # -----------------------------------------------------------------------
    # Verdict
    # -----------------------------------------------------------------------
    print()
    print("=" * 70)
    print("VERDICT")
    print("=" * 70)
    hvac_gap    = min_score - HVAC_MIN_SCORE
    coolant_gap = min_score - COOLANT_MIN_SCORE

    print(f"CLEAN FLOOR                  : {min_score:.6f}")
    print(f"GAP TO HVAC MINIMUM (0.082)  : {hvac_gap:+.6f}")
    print(f"GAP TO COOLANT MINIMUM (0.070): {coolant_gap:+.6f}")

    if min_score < HVAC_MIN_SCORE:
        print()
        print("WARNING — HVAC gap is within clean noise floor")
    if min_score < COOLANT_MIN_SCORE:
        print("WARNING — Coolant gap is within clean noise floor")

    if min_score >= HVAC_MIN_SCORE:
        print()
        print("OK — clean floor sits above both known anomaly thresholds.")

    print("=" * 70)


if __name__ == "__main__":
    run()
