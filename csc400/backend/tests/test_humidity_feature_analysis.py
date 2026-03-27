"""
Feature-space analysis: why doesn't the model detect coolant_leak?

Prints the full feature vector at every step, then compares the last
baseline vector to the peak-injection vector (step with the lowest/most
anomalous score) to show which features shift most in feature space.

Run with:
    PYTHONPATH=. python backend/tests/test_humidity_feature_analysis.py
"""

from backend.ml.model_loader import ModelLoader
from backend.ml.feature_extraction import SlidingWindowFeatureExtractor
from backend.simulation.node import VirtualNode
from backend.simulation.thermal_model import ThermalModel
from backend.simulation.airflow import AirflowModel
from backend.simulation.humidity import HumidityModel

# Feature names in the order SlidingWindowFeatureExtractor produces them
# variables = ['temperature', 'airflow', 'humidity', 'cpu_load'], stats = mean/var/roc
FEATURE_NAMES = [
    "temp_mean",  "temp_var",  "temp_roc",
    "air_mean",   "air_var",   "air_roc",
    "hum_mean",   "hum_var",   "hum_roc",
    "cpu_mean",   "cpu_var",   "cpu_roc",
]


def make_test_node() -> VirtualNode:
    thermal = ThermalModel(50.0, 1005.0, 500.0, 300.0, 21.0, 20.0)
    airflow = AirflowModel(nominal_flow=2.5, random_seed=1042)
    humidity = HumidityModel(45.0, 0.01, 0.2, random_seed=2042, reference_temp=21.0)
    return VirtualNode("test-node", thermal, airflow, humidity, random_seed=3042)


def print_feature_vector(step_label: str, features: list, score: float):
    print(f"\n  [{step_label}]  score={score:+.4f}")
    for name, val in zip(FEATURE_NAMES, features):
        print(f"    {name:<12} = {val:+12.6f}")


def pct_change(baseline: float, injection: float) -> str:
    if abs(baseline) < 1e-9:
        return "  N/A (baseline≈0)"
    return f"{((injection - baseline) / abs(baseline)) * 100:+.1f}%"


def main():
    node = make_test_node()
    model_loader = ModelLoader()
    extractor = SlidingWindowFeatureExtractor(window_size=10)

    # ── Phase A — Baseline ────────────────────────────────────────────────────
    print()
    print("=" * 66)
    print("PHASE A — Baseline (30 steps) — full feature vectors")
    print("=" * 66)

    last_baseline_features = None
    last_baseline_score = None

    for i in range(1, 31):
        telemetry = node.step()
        extractor.add_point(telemetry)

        if extractor.is_window_ready():
            features = extractor.extract_features()
            result = model_loader.predict(features)
            score = result["anomaly_score"]
            print_feature_vector(f"baseline step {i:02d}", features, score)
            last_baseline_features = features
            last_baseline_score = score
        else:
            print(f"\n  [baseline step {i:02d}]  window filling "
                  f"({len(extractor.window)}/{extractor.window_size})")

    # ── Phase B — Coolant leak injection ─────────────────────────────────────
    print()
    print("=" * 66)
    print("PHASE B — Coolant leak injection (30 steps) — full feature vectors")
    print("=" * 66)

    node.inject_coolant_leak()

    peak_features = None
    peak_score = None  # lowest (most anomalous) score seen

    for i in range(1, 31):
        telemetry = node.step()
        extractor.add_point(telemetry)

        features = extractor.extract_features()
        result = model_loader.predict(features)
        score = result["anomaly_score"]

        print_feature_vector(f"injection step {i:02d}", features, score)

        if peak_score is None or score < peak_score:
            peak_score = score
            peak_features = features[:]

    # ── Phase C — Feature delta analysis ─────────────────────────────────────
    print()
    print("=" * 66)
    print("PHASE C — Feature delta: last baseline vs. peak injection step")
    print(f"          (peak = step with lowest/most-anomalous score: {peak_score:+.4f})")
    print("=" * 66)

    if last_baseline_features is None or peak_features is None:
        print("  ERROR: insufficient data for comparison.")
        return

    print(f"\n  {'Feature':<12}  {'Baseline':>12}  {'Injection':>12}  "
          f"{'Abs diff':>12}  {'% change':>14}")
    print(f"  {'-'*12}  {'-'*12}  {'-'*12}  {'-'*12}  {'-'*14}")

    rows = []
    for name, b, inj in zip(FEATURE_NAMES, last_baseline_features, peak_features):
        abs_diff = abs(inj - b)
        pct = ((inj - b) / abs(b)) * 100 if abs(b) > 1e-9 else None
        rows.append((name, b, inj, abs_diff, pct))

    # Sort by percentage change descending (None sorts last)
    rows.sort(key=lambda r: abs(r[4]) if r[4] is not None else 0.0, reverse=True)

    for name, b, inj, abs_diff, pct in rows:
        pct_str = f"{pct:+.1f}%" if pct is not None else "N/A (baseline≈0)"
        print(f"  {name:<12}  {b:>+12.6f}  {inj:>+12.6f}  {abs_diff:>12.6f}  {pct_str:>14}")

    # ── Phase D — Interpretation ──────────────────────────────────────────────
    print()
    print("=" * 66)
    print("PHASE D — Interpretation")
    print("=" * 66)

    # Identify humidity features vs others
    hum_rows = [r for r in rows if r[0].startswith("hum_")]
    other_rows = [r for r in rows if not r[0].startswith("hum_")]

    hum_pcts = [abs(r[4]) for r in hum_rows if r[4] is not None]
    other_pcts = [abs(r[4]) for r in other_rows if r[4] is not None]

    avg_hum_shift = sum(hum_pcts) / len(hum_pcts) if hum_pcts else 0.0
    avg_other_shift = sum(other_pcts) / len(other_pcts) if other_pcts else 0.0

    print(f"\n  Humidity feature avg % shift   : {avg_hum_shift:.1f}%")
    print(f"  Other feature avg % shift      : {avg_other_shift:.1f}%")
    print()

    top3 = rows[:3]
    print("  Top 3 features by % change:")
    for name, b, inj, abs_diff, pct in top3:
        pct_str = f"{pct:+.1f}%" if pct is not None else "N/A"
        print(f"    {name:<12}  {pct_str}")

    print()
    if avg_hum_shift > avg_other_shift * 2:
        print("  FINDING: Humidity features shift significantly MORE than other signals.")
        print("  The model's decision boundary does not weight humidity strongly enough.")
        print("  Retraining with humidity anomaly examples in the training set is needed.")
    elif avg_hum_shift > avg_other_shift:
        print("  FINDING: Humidity features shift more than other signals, but not")
        print("  dramatically. The model sees the change but the boundary is too permissive.")
        print("  Retraining with humidity anomaly examples would sharpen the boundary.")
    else:
        print("  FINDING: Humidity features do NOT dominate the shift.")
        print("  Stable temperature/airflow/cpu features may be anchoring the score.")
        print("  The model treats the normal-range values of other signals as 'safe',")
        print("  overwhelming the humidity deviation in the isolation path lengths.")
    print()


if __name__ == "__main__":
    main()
