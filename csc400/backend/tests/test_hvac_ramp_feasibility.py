"""
Feasibility test: does the current Isolation Forest model detect an
HVAC failure using node.inject_hvac_failure() (linear ramp) without retraining?

Unlike test_hvac_feasibility.py which uses simulate_fan_failure() (instant step
to zero), inject_hvac_failure() ramps airflow to zero over 15 steps, keeping
air_roc non-zero for longer and sustaining the anomaly signal across the full
sliding window fill cycle.

Run with:
    PYTHONPATH=. python backend/tests/test_hvac_ramp_feasibility.py
"""

from backend.ml.model_loader import ModelLoader
from backend.ml.feature_extraction import SlidingWindowFeatureExtractor
from backend.simulation.node import VirtualNode
from backend.simulation.thermal_model import ThermalModel
from backend.simulation.airflow import AirflowModel
from backend.simulation.humidity import HumidityModel


MANUAL_THRESHOLD = 0.15  # score < 0.15 → anomaly (set in model_loader.py 2026-03-27)


def make_test_node() -> VirtualNode:
    thermal = ThermalModel(50.0, 1005.0, 500.0, 300.0, 21.0, 20.0)
    airflow = AirflowModel(nominal_flow=2.5, random_seed=1042)
    humidity = HumidityModel(45.0, 0.01, 0.2, random_seed=2042, reference_temp=21.0)
    return VirtualNode("test-node", thermal, airflow, humidity, random_seed=3042)


def main():
    node = make_test_node()
    model_loader = ModelLoader()
    extractor = SlidingWindowFeatureExtractor(window_size=10)

    # ── Phase A — Baseline ────────────────────────────────────────────────────
    print()
    print("=" * 62)
    print("PHASE A — Baseline (30 steps, no anomaly)")
    print("=" * 62)

    baseline_max_score = None

    for i in range(1, 31):
        telemetry = node.step()
        airflow = telemetry["airflow"]
        extractor.add_point(telemetry)

        if extractor.is_window_ready():
            features = extractor.extract_features()
            result = model_loader.predict(features)
            score = result["anomaly_score"]
            is_anomaly = result["is_anomaly"]
            if baseline_max_score is None or score > baseline_max_score:
                baseline_max_score = score
            print(
                f"  step {i:02d} | airflow={airflow:6.4f} | "
                f"score={score:+.4f} | anomaly={is_anomaly}"
            )
        else:
            print(
                f"  step {i:02d} | airflow={airflow:6.4f} | "
                f"window filling ({len(extractor.window)}/{extractor.window_size})"
            )

    # ── Phase B — HVAC ramp failure injection ────────────────────────────────
    print()
    print("=" * 62)
    print("PHASE B — HVAC ramp failure injection (40 steps)")
    print("=" * 62)

    node.inject_hvac_failure(duration_seconds=40)

    injection_min_score = None
    first_detection_step = None
    phase_b_anomalies = []   # bool per step, index 0 = step 1

    for i in range(1, 41):
        telemetry = node.step()
        airflow = telemetry["airflow"]
        extractor.add_point(telemetry)

        features = extractor.extract_features()
        result = model_loader.predict(features)
        score = result["anomaly_score"]
        is_anomaly = result["is_anomaly"]

        phase_b_anomalies.append(is_anomaly)

        if injection_min_score is None or score < injection_min_score:
            injection_min_score = score
        if is_anomaly and first_detection_step is None:
            first_detection_step = i

        print(
            f"  step {i:02d} | airflow={airflow:6.4f} | "
            f"score={score:+.4f} | anomaly={is_anomaly}"
        )

    # ── Compute streak and gap statistics ────────────────────────────────────
    longest_streak = 0
    current_streak = 0
    for flag in phase_b_anomalies:
        if flag:
            current_streak += 1
            longest_streak = max(longest_streak, current_streak)
        else:
            current_streak = 0

    # Detection gaps: ranges of False after first True
    gaps = []
    if first_detection_step is not None:
        in_gap = False
        gap_start = None
        for i, flag in enumerate(phase_b_anomalies, start=1):
            if i < first_detection_step:
                continue
            if not flag and not in_gap:
                in_gap = True
                gap_start = i
            elif flag and in_gap:
                gaps.append((gap_start, i - 1))
                in_gap = False
        if in_gap:
            gaps.append((gap_start, 40))

    # ── Phase C — Summary ─────────────────────────────────────────────────────
    print()
    print("=" * 62)
    print("PHASE C — Summary")
    print("=" * 62)

    baseline_str = (
        f"{baseline_max_score:+.4f}" if baseline_max_score is not None else "N/A"
    )
    injection_str = (
        f"{injection_min_score:+.4f}" if injection_min_score is not None else "N/A"
    )
    detection_str = (
        f"step {first_detection_step}" if first_detection_step is not None else "NO DETECTION"
    )
    streak_str = f"{longest_streak} step(s)" if first_detection_step is not None else "N/A"
    if gaps:
        gap_str = ", ".join(f"steps {s}–{e}" for s, e in gaps)
    elif first_detection_step is not None:
        gap_str = "none (continuous)"
    else:
        gap_str = "N/A"

    print(f"  Baseline max score       : {baseline_str}")
    print(f"  Injection min score      : {injection_str}")
    print(f"  Model threshold          : {MANUAL_THRESHOLD:.4f}")
    print(f"  First detection at       : {detection_str}")
    print(f"  Consecutive detect steps : {streak_str}")
    print(f"  Detection gaps           : {gap_str}")
    print()

    if first_detection_step is not None:
        print(
            "  VERDICT: DETECTABLE — model catches hvac_failure (ramp) without retraining"
        )
    else:
        print(
            "  VERDICT: NOT DETECTABLE — model does not trigger on HVAC ramp failure,"
            " retraining required"
        )
    print()


if __name__ == "__main__":
    main()
