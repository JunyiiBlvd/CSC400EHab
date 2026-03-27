"""
Feasibility test: does the current Isolation Forest model detect a
coolant_leak humidity anomaly without retraining?

Run with:
    PYTHONPATH=. python backend/tests/test_humidity_feasibility.py
"""

from backend.ml.model_loader import ModelLoader
from backend.ml.feature_extraction import SlidingWindowFeatureExtractor
from backend.simulation.node import VirtualNode
from backend.simulation.thermal_model import ThermalModel
from backend.simulation.airflow import AirflowModel
from backend.simulation.humidity import HumidityModel


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
        humidity = telemetry["humidity"]
        extractor.add_point(telemetry)

        if extractor.is_window_ready():
            features = extractor.extract_features()
            result = model_loader.predict(features)
            score = result["anomaly_score"]
            is_anomaly = result["is_anomaly"]
            if baseline_max_score is None or score > baseline_max_score:
                baseline_max_score = score
            print(
                f"  step {i:02d} | humidity={humidity:6.2f}% | "
                f"score={score:+.4f} | anomaly={is_anomaly}"
            )
        else:
            print(
                f"  step {i:02d} | humidity={humidity:6.2f}% | "
                f"window filling ({len(extractor.window)}/{extractor.window_size})"
            )

    # ── Phase B — Coolant leak injection ─────────────────────────────────────
    print()
    print("=" * 62)
    print("PHASE B — Coolant leak injection (30 steps)")
    print("=" * 62)

    node.inject_coolant_leak()

    injection_max_score = None
    first_detection_step = None

    for i in range(1, 31):
        telemetry = node.step()
        humidity = telemetry["humidity"]
        extractor.add_point(telemetry)

        features = extractor.extract_features()
        result = model_loader.predict(features)
        score = result["anomaly_score"]
        is_anomaly = result["is_anomaly"]

        if injection_max_score is None or score > injection_max_score:
            injection_max_score = score
        if is_anomaly and first_detection_step is None:
            first_detection_step = i

        print(
            f"  step {i:02d} | humidity={humidity:6.2f}% | "
            f"score={score:+.4f} | anomaly={is_anomaly}"
        )

    # ── Phase C — Summary ─────────────────────────────────────────────────────
    print()
    print("=" * 62)
    print("PHASE C — Summary")
    print("=" * 62)

    threshold = model_loader.model.offset_

    baseline_str = (
        f"{baseline_max_score:+.4f}" if baseline_max_score is not None else "N/A"
    )
    injection_str = (
        f"{injection_max_score:+.4f}" if injection_max_score is not None else "N/A"
    )
    detection_str = (
        f"step {first_detection_step}" if first_detection_step is not None else "NO DETECTION"
    )

    print(f"  Baseline max score : {baseline_str}")
    print(f"  Injection max score: {injection_str}")
    print(f"  Model threshold    : {threshold:+.4f}")
    print(f"  First detection at : {detection_str}")
    print()

    if first_detection_step is not None:
        print(
            "  VERDICT: DETECTABLE — model catches coolant_leak without retraining"
        )
    else:
        print(
            "  VERDICT: NOT DETECTABLE — model does not trigger on humidity anomaly,"
            " retraining required"
        )
    print()


if __name__ == "__main__":
    main()
