from __future__ import annotations

import json
from collections import deque
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from backend.ml.feature_extraction import SlidingWindowFeatureExtractor


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_DIR = ROOT / "analysis"
MODEL_PATH = ROOT / "models" / "model_v2_hybrid_real.pkl"
SCALER_PATH = ROOT / "models" / "scaler_v2.pkl"
MIT_PATH = ROOT / "datasets" / "MIT_dataset.csv"
VALIDATION_PATH = ROOT / "data" / "real" / "mit_anomaly_validation.csv"

SCHEMA = ["Date", "Timestamp", "Epoch", "Moteid", "Temp (C)", "Humidity", "Light", "Voltage"]
CANDIDATES = [
    ("sklearn native", None),
    ("0.027690941863431795", 0.027690941863431795),
    ("0.04", 0.04),
    ("0.05", 0.05),
    ("0.15", 0.15),
]


def load_streams():
    raw = pd.read_csv(MIT_PATH)
    validation = pd.read_csv(VALIDATION_PATH)

    raw_no_null = raw[raw["Humidity"].notna()].copy()
    out_of_range = (raw_no_null["Humidity"] < 0) | (raw_no_null["Humidity"] > 100)
    clean = raw_no_null[~out_of_range].copy()

    train_excluded = clean.iloc[20000:].copy()
    validation_keyed = validation[SCHEMA].copy()
    validation_keyed["_is_validation_row"] = 1

    normal_pool = train_excluded.merge(validation_keyed, on=SCHEMA, how="left")
    overlap_rows_removed = int(len(train_excluded) - normal_pool["_is_validation_row"].isna().sum())
    normal_pool = normal_pool[normal_pool["_is_validation_row"].isna()].copy().drop(columns=["_is_validation_row"])

    for df in (normal_pool, validation):
        df["Datetime"] = pd.to_datetime(df["Date"] + " " + df["Timestamp"], errors="coerce")

    return normal_pool, validation, overlap_rows_removed


def build_windows_with_meta(df: pd.DataFrame):
    d = df.copy()
    l_min, l_max = d["Light"].min(), d["Light"].max()
    v_min, v_max = d["Voltage"].min(), d["Voltage"].max()
    d["airflow"] = 2.0 + (d["Light"] - l_min) / (l_max - l_min + 1e-6) * 1.0
    d["cpu_load"] = 0.1 + (d["Voltage"] - v_min) / (v_max - v_min + 1e-6) * 0.8
    d["temperature"] = d["Temp (C)"]
    d["humidity"] = d["Humidity"]

    d = d.sort_values(["Moteid", "Datetime", "Epoch"]).copy()
    d[["temperature", "humidity", "airflow", "cpu_load"]] = (
        d.groupby("Moteid")[["temperature", "humidity", "airflow", "cpu_load"]]
        .transform(lambda g: g.ffill().bfill())
    )
    d[["temperature", "humidity", "airflow", "cpu_load"]] = (
        d[["temperature", "humidity", "airflow", "cpu_load"]].fillna(0)
    )

    features = []
    meta = []
    for mote_id, group in d.groupby("Moteid", sort=False):
        group = group.sort_values(["Datetime", "Epoch"])
        extractor = SlidingWindowFeatureExtractor(window_size=10)
        for _, row in group.iterrows():
            extractor.add_point(
                {
                    "temperature": float(row["temperature"]),
                    "airflow": float(row["airflow"]),
                    "humidity": float(row["humidity"]),
                    "cpu_load": float(row["cpu_load"]),
                }
            )
            if extractor.is_window_ready():
                features.append(extractor.extract_features())
                meta.append(
                    {
                        "moteid": int(row["Moteid"]),
                        "end_datetime": row["Datetime"],
                        "end_epoch": int(row["Epoch"]) if not pd.isna(row["Epoch"]) else None,
                    }
                )

    features = np.asarray(features, dtype=float)
    meta_df = pd.DataFrame(meta)
    if len(meta_df):
        meta_df["_orig_idx"] = np.arange(len(meta_df))
        meta_df = meta_df.sort_values(
            ["end_datetime", "moteid", "end_epoch", "_orig_idx"], kind="stable"
        ).reset_index(drop=True)
        order = meta_df["_orig_idx"].to_numpy()
        features = features[order]
        meta_df = meta_df.drop(columns=["_orig_idx"])
    return features, meta_df


def compute_metrics(normal_pos: np.ndarray, anomaly_pos: np.ndarray):
    tp = int(anomaly_pos.sum())
    fn = int((~anomaly_pos).sum())
    fp = int(normal_pos.sum())
    tn = int((~normal_pos).sum())
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    fpr = fp / (fp + tn) if (fp + tn) else 0.0
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    return {
        "recall": float(recall),
        "false_positive_rate": float(fpr),
        "precision": float(precision),
        "F1": float(f1),
        "TP": tp,
        "FP": fp,
        "TN": tn,
        "FN": fn,
    }


def raw_flags(rule_name: str, threshold: float | None, scores: np.ndarray, native_flags: np.ndarray):
    if rule_name == "sklearn native":
        return native_flags.copy()
    return scores < float(threshold)


def onset_count(alerts: np.ndarray) -> int:
    if len(alerts) == 0:
        return 0
    prev = np.r_[False, alerts[:-1]]
    return int(np.sum(alerts & ~prev))


def onset_indices(alerts: np.ndarray) -> np.ndarray:
    if len(alerts) == 0:
        return np.array([], dtype=int)
    prev = np.r_[False, alerts[:-1]]
    return np.flatnonzero(alerts & ~prev)


def policy_single(flags: np.ndarray):
    return flags.copy()


def policy_two_consecutive(flags: np.ndarray):
    out = np.zeros(len(flags), dtype=bool)
    if len(flags) >= 2:
        out[1:] = flags[1:] & flags[:-1]
    return out


def policy_three_consecutive(flags: np.ndarray):
    out = np.zeros(len(flags), dtype=bool)
    if len(flags) >= 3:
        out[2:] = flags[2:] & flags[1:-1] & flags[:-2]
    return out


def rolling_count_policy(flags: np.ndarray, window: int, needed: int):
    out = np.zeros(len(flags), dtype=bool)
    q: deque[int] = deque()
    s = 0
    for i, flag in enumerate(flags):
        q.append(int(flag))
        s += int(flag)
        if len(q) > window:
            s -= q.popleft()
        out[i] = s >= needed
    return out


TEMPORAL_POLICIES = {
    "A_single_window": policy_single,
    "B_2_consecutive": policy_two_consecutive,
    "C_3_consecutive": policy_three_consecutive,
    "D_2_of_last_3": lambda flags: rolling_count_policy(flags, 3, 2),
    "E_3_of_last_5": lambda flags: rolling_count_policy(flags, 5, 3),
}


def percentile_dict(values: np.ndarray, labels):
    percentiles = np.percentile(values, labels)
    return {f"p{int(label):02d}": float(value) for label, value in zip(labels, percentiles)}


def main():
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

    normal_pool, validation, overlap_rows_removed = load_streams()
    normal_features, normal_meta = build_windows_with_meta(normal_pool)
    anomaly_features, anomaly_meta = build_windows_with_meta(validation)

    model = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)

    normal_scaled = scaler.transform(normal_features)
    anomaly_scaled = scaler.transform(anomaly_features)
    normal_scores = model.decision_function(normal_scaled)
    anomaly_scores = model.decision_function(anomaly_scaled)
    normal_native = model.predict(normal_scaled) == -1
    anomaly_native = model.predict(anomaly_scaled) == -1

    threshold_rows = []
    threshold_metrics_lookup = {}
    for rule_name, threshold in CANDIDATES:
        row = compute_metrics(
            raw_flags(rule_name, threshold, normal_scores, normal_native),
            raw_flags(rule_name, threshold, anomaly_scores, anomaly_native),
        )
        row["threshold_rule"] = rule_name
        row["threshold"] = threshold
        threshold_rows.append(row)
        threshold_metrics_lookup[rule_name] = row

    normal_stats = {
        "min": float(normal_scores.min()),
        **percentile_dict(normal_scores, [1, 5, 50, 95, 99]),
        "median": float(np.percentile(normal_scores, 50)),
        "max": float(normal_scores.max()),
    }
    anomaly_stats = {
        "min": float(anomaly_scores.min()),
        **percentile_dict(anomaly_scores, [1, 5, 50, 95, 99]),
        "median": float(np.percentile(anomaly_scores, 50)),
        "max": float(anomaly_scores.max()),
    }

    anom_max = anomaly_stats["max"]
    norm_p01 = normal_stats["p01"]
    norm_p05 = normal_stats["p05"]

    threshold_comparison = {
        "inputs": {
            "model_path": str(MODEL_PATH.relative_to(ROOT)),
            "scaler_path": str(SCALER_PATH.relative_to(ROOT)),
            "normal_windows_count": int(len(normal_scores)),
            "anomaly_windows_count": int(len(anomaly_scores)),
            "overlap_rows_removed": overlap_rows_removed,
        },
        "model_properties": {
            "model_type": type(model).__name__,
            "contamination": float(model.contamination),
            "offset_": float(model.offset_),
            "n_estimators": int(model.n_estimators),
            "max_samples_": int(model.max_samples_),
        },
        "candidate_thresholds_rules": [rule for rule, _ in CANDIDATES],
        "metrics": threshold_rows,
        "distribution_reference_points": {
            "normal": normal_stats,
            "anomaly": anomaly_stats,
            "score_gap": {
                "anomaly_max": anom_max,
                "normal_p01": norm_p01,
                "normal_p05": norm_p05,
                "gap_anomaly_max_to_normal_p01": float(norm_p01 - anom_max),
                "gap_anomaly_max_to_normal_p05": float(norm_p05 - anom_max),
                "gap_normal_p01_to_normal_p05": float(norm_p05 - norm_p01),
            },
        },
    }

    temporal_results = []
    for rule_name, threshold in CANDIDATES:
        n_raw = raw_flags(rule_name, threshold, normal_scores, normal_native)
        a_raw = raw_flags(rule_name, threshold, anomaly_scores, anomaly_native)
        raw_before = {
            "normal": int(n_raw.sum()),
            "anomaly": int(a_raw.sum()),
            "total": int(n_raw.sum() + a_raw.sum()),
        }
        for policy_name, policy_fn in TEMPORAL_POLICIES.items():
            n_alert = policy_fn(n_raw)
            a_alert = policy_fn(a_raw)
            n_onsets = onset_count(n_alert)
            a_onsets = onset_count(a_alert)
            n_onset_idx = onset_indices(n_alert)
            a_onset_idx = onset_indices(a_alert)
            avg_gap = float(np.diff(n_onset_idx).mean()) if len(n_onset_idx) >= 2 else None
            first_detection_index = int(a_onset_idx[0]) if len(a_onset_idx) else None
            detection_delay_windows = int(a_onset_idx[0]) if len(a_onset_idx) else None

            tp = int(a_alert.sum())
            fp = int(n_alert.sum())
            fn = int((~a_alert).sum())
            tn = int((~n_alert).sum())
            recall = tp / len(a_alert) if len(a_alert) else 0.0
            fpr = fp / len(n_alert) if len(n_alert) else 0.0
            precision = tp / (tp + fp) if (tp + fp) else 0.0
            f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

            temporal_results.append(
                {
                    "threshold_rule": rule_name,
                    "threshold": threshold,
                    "temporal_policy": policy_name,
                    "alert_recall": float(recall),
                    "alert_false_positive_rate": float(fpr),
                    "normal_alert_count": n_onsets,
                    "anomaly_alert_count": a_onsets,
                    "avg_gap_between_false_alerts_on_normal": avg_gap,
                    "first_detection_index": first_detection_index,
                    "detection_delay_windows": detection_delay_windows,
                    "raw_window_flags_before_policy": raw_before,
                    "alerts_after_policy": {
                        "normal": int(n_alert.sum()),
                        "anomaly": int(a_alert.sum()),
                        "total": int(n_alert.sum() + a_alert.sum()),
                    },
                    "alert_precision": float(precision),
                    "alert_F1": float(f1),
                    "TP": tp,
                    "FP": fp,
                    "TN": tn,
                    "FN": fn,
                }
            )

    chronological_preserved = bool(
        len(normal_meta)
        and len(anomaly_meta)
        and normal_meta["end_datetime"].notna().all()
        and anomaly_meta["end_datetime"].notna().all()
    )

    eligible_recall = [r for r in temporal_results if r["alert_recall"] >= 0.95]
    best_lowest_fpr = None
    if eligible_recall:
        best_lowest_fpr = sorted(
            eligible_recall,
            key=lambda r: (
                r["alert_false_positive_rate"],
                -r["alert_recall"],
                -r["alert_F1"],
                r["first_detection_index"] if r["first_detection_index"] is not None else 10**12,
            ),
        )[0]

    best_f1_temporal = sorted(
        temporal_results,
        key=lambda r: (
            -r["alert_F1"],
            -r["alert_recall"],
            r["alert_false_positive_rate"],
            r["first_detection_index"] if r["first_detection_index"] is not None else 10**12,
        ),
    )[0]

    acceptable_fp_candidates = []
    if eligible_recall:
        min_fpr_recall95 = min(r["alert_false_positive_rate"] for r in eligible_recall)
        acceptable_fp_candidates = [
            r for r in eligible_recall if abs(r["alert_false_positive_rate"] - min_fpr_recall95) < 1e-15
        ]
    fastest_detection = None
    if acceptable_fp_candidates:
        fastest_detection = sorted(
            acceptable_fp_candidates,
            key=lambda r: (
                r["first_detection_index"] if r["first_detection_index"] is not None else 10**12,
                -r["alert_recall"],
                -r["alert_F1"],
            ),
        )[0]

    temporal_output = {
        "inputs": {
            "model_path": str(MODEL_PATH.relative_to(ROOT)),
            "scaler_path": str(SCALER_PATH.relative_to(ROOT)),
            "normal_window_count": int(len(normal_scores)),
            "anomaly_window_count": int(len(anomaly_scores)),
            "chronological_order_preserved": chronological_preserved,
            "warning_note": None if chronological_preserved else "Most faithful available ordering used.",
        },
        "thresholds_tested": [rule for rule, _ in CANDIDATES],
        "temporal_policies_tested": list(TEMPORAL_POLICIES.keys()),
        "results_matrix": temporal_results,
        "best_combinations_by_objective": {
            "best_by_lowest_false_positive_rate_with_recall_>=_0.95": best_lowest_fpr,
            "best_by_highest_F1_if_computable_at_alert_level": best_f1_temporal,
            "best_by_fastest_detection_among_combinations_with_acceptable_false_positives": fastest_detection,
        },
    }

    sklearn_rule = threshold_metrics_lookup["sklearn native"]
    offset_value = 0.0
    if offset_value < anom_max:
        offset_placement = "below anomaly max"
    elif anom_max <= offset_value < norm_p01:
        offset_placement = "between anomaly max and normal p01"
    elif norm_p01 <= offset_value < norm_p05:
        offset_placement = "between normal p01 and normal p05"
    else:
        offset_placement = "above normal p05"

    role_assessment = {
        "native_sklearn_decision_properties": {
            "model_type": type(model).__name__,
            "contamination": float(model.contamination),
            "offset_": float(model.offset_),
            "equivalent_score_cutoff_interpretation": "model.predict() flags anomaly when decision_function < 0",
            "score_ranges": {
                "normal": {"min": float(normal_scores.min()), "max": float(normal_scores.max())},
                "anomaly": {"min": float(anomaly_scores.min()), "max": float(anomaly_scores.max())},
            },
            "normal_score_distribution": {
                "p01": normal_stats["p01"],
                "p05": normal_stats["p05"],
                "median": normal_stats["median"],
            },
            "anomaly_score_distribution": {
                "p95": anomaly_stats["p95"],
                "p99": anomaly_stats["p99"],
                "max": anomaly_stats["max"],
            },
        },
        "metrics_comparison": [
            {
                "threshold_rule": row["threshold_rule"],
                "recall": row["recall"],
                "false_positive_rate": row["false_positive_rate"],
                "precision": row["precision"],
                "F1": row["F1"],
            }
            for row in threshold_rows
        ],
        "distribution_placement": {
            "offset_relative_to_normal_distribution": f"offset_cutoff=0.0, normal_min={normal_stats['min']}, normal_p01={normal_stats['p01']}, normal_p05={normal_stats['p05']}",
            "offset_relative_to_anomaly_distribution": f"offset_cutoff=0.0, anomaly_min={anomaly_stats['min']}, anomaly_p95={anomaly_stats['p95']}, anomaly_max={anomaly_stats['max']}",
            "offset_cluster_placement": offset_placement,
        },
        "role_assessment": {
            "primary_detector": {
                "plausible": False,
                "evidence": f"recall={sklearn_rule['recall']} and F1={sklearn_rule['F1']} versus 0.027690941863431795 recall={threshold_metrics_lookup['0.027690941863431795']['recall']} and F1={threshold_metrics_lookup['0.027690941863431795']['F1']}",
            },
            "secondary_confirmation_gate": {
                "plausible": True,
                "evidence": f"precision={sklearn_rule['precision']} with false_positive_rate={sklearn_rule['false_positive_rate']} and recall={sklearn_rule['recall']}",
            },
            "precision_oriented_alarm": {
                "plausible": True,
                "evidence": f"false_positive_rate={sklearn_rule['false_positive_rate']} is the lowest among tested rules while recall={sklearn_rule['recall']}",
            },
            "baseline_reference_only": {
                "plausible": True,
                "evidence": f"F1={sklearn_rule['F1']} trails 0.027690941863431795 F1={threshold_metrics_lookup['0.027690941863431795']['F1']}, 0.04 F1={threshold_metrics_lookup['0.04']['F1']}, and 0.05 F1={threshold_metrics_lookup['0.05']['F1']}",
            },
        },
    }

    deployment_rows = []
    for row in threshold_rows:
        deployment_rows.append(
            {
                "threshold_rule": row["threshold_rule"],
                "false_alarms_per_1000_normal_windows": row["false_positive_rate"] * 1000.0,
                "false_alarms_per_10000_normal_windows": row["false_positive_rate"] * 10000.0,
                "missed_anomalies_per_1000_anomaly_windows": (1.0 - row["recall"]) * 1000.0,
                "percent_detected": row["recall"] * 100.0,
            }
        )

    placements = []
    for rule_name, threshold in CANDIDATES:
        value = 0.0 if threshold is None else float(threshold)
        if value < anom_max:
            category = "below anomaly max"
        elif anom_max <= value < norm_p01:
            category = "between anomaly max and normal p01"
        elif norm_p01 <= value < norm_p05:
            category = "between normal p01 and normal p05"
        else:
            category = "above normal p05"
        placements.append(
            {
                "threshold_rule": rule_name,
                "placement_category": category,
                "numeric_justification": f"value={value:.15f}, anomaly_max={anom_max:.15f}, normal_p01={norm_p01:.15f}, normal_p05={norm_p05:.15f}",
            }
        )

    deployment_evidence = {
        "candidate_thresholds_rules": [rule for rule, _ in CANDIDATES],
        "metrics_table": threshold_rows,
        "deployment_consequence_table": deployment_rows,
        "distribution_reference_points": {
            "normal_stats": normal_stats,
            "anomaly_stats": anomaly_stats,
            "score_gap_references": {
                "anomaly_max": anom_max,
                "normal_p01": norm_p01,
                "normal_p05": norm_p05,
                "gap_anomaly_max_to_normal_p01": float(norm_p01 - anom_max),
                "gap_anomaly_max_to_normal_p05": float(norm_p05 - anom_max),
            },
        },
        "placement_of_each_threshold": placements,
    }

    best_by_f1 = sorted(threshold_rows, key=lambda r: (-r["F1"], r["false_positive_rate"]))[0]
    recall_95_candidates = [r for r in threshold_rows if r["recall"] >= 0.95]
    best_recall95_lowest_fpr = sorted(
        recall_95_candidates, key=lambda r: (r["false_positive_rate"], -r["recall"], -r["F1"])
    )[0]

    summary_lines = [
        "# Threshold Analysis Summary",
        "",
        "## Input Artifacts Used",
        f"- Model: `{MODEL_PATH.relative_to(ROOT)}`",
        f"- Scaler: `{SCALER_PATH.relative_to(ROOT)}`",
        f"- Raw MIT dataset: `{MIT_PATH.relative_to(ROOT)}`",
        f"- MIT anomaly validation dataset: `{VALIDATION_PATH.relative_to(ROOT)}`",
        f"- Normal windows: `{len(normal_scores)}`",
        f"- Anomaly windows: `{len(anomaly_scores)}`",
        "",
        "## Candidate Thresholds Tested",
        "- `sklearn native`",
        "- `0.027690941863431795`",
        "- `0.04`",
        "- `0.05`",
        "- `0.15`",
        "",
        "## Key Metrics Table",
        "| threshold/rule | recall | false_positive_rate | precision | F1 |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in threshold_rows:
        summary_lines.append(
            f"| `{row['threshold_rule']}` | `{row['recall']:.12f}` | `{row['false_positive_rate']:.12f}` | `{row['precision']:.12f}` | `{row['F1']:.12f}` |"
        )
    summary_lines.extend(
        [
            "",
            "## Best Threshold By F1",
            f"- `{best_by_f1['threshold_rule']}` with `F1={best_by_f1['F1']:.12f}`",
            "",
            "## Best Threshold With Recall >= 0.95 And Lowest FPR",
            f"- `{best_recall95_lowest_fpr['threshold_rule']}` with `recall={best_recall95_lowest_fpr['recall']:.12f}` and `false_positive_rate={best_recall95_lowest_fpr['false_positive_rate']:.12f}`",
            "",
            "## Sklearn Native Plausibility",
            f"- Primary: `{'plausible' if role_assessment['role_assessment']['primary_detector']['plausible'] else 'not plausible'}`",
            f"- Secondary: `{'plausible' if role_assessment['role_assessment']['secondary_confirmation_gate']['plausible'] else 'not plausible'}`",
            f"- Baseline: `{'plausible' if role_assessment['role_assessment']['baseline_reference_only']['plausible'] else 'not plausible'}`",
            "",
            "## Top Temporal Policy Combinations",
            f"- Best by alert F1: `{best_f1_temporal['threshold_rule']}` + `{best_f1_temporal['temporal_policy']}` with `alert_F1={best_f1_temporal['alert_F1']:.12f}`",
            f"- Best recall>=0.95 lowest FPR: `{best_lowest_fpr['threshold_rule']}` + `{best_lowest_fpr['temporal_policy']}` with `alert_false_positive_rate={best_lowest_fpr['alert_false_positive_rate']:.12f}` and `alert_recall={best_lowest_fpr['alert_recall']:.12f}`",
            f"- Fastest acceptable detection: `{fastest_detection['threshold_rule']}` + `{fastest_detection['temporal_policy']}` with `first_detection_index={fastest_detection['first_detection_index']}`",
            "",
        ]
    )

    (ANALYSIS_DIR / "threshold_comparison.json").write_text(json.dumps(threshold_comparison, indent=2) + "\n")
    (ANALYSIS_DIR / "temporal_policy_results.json").write_text(json.dumps(temporal_output, indent=2) + "\n")
    (ANALYSIS_DIR / "sklearn_threshold_role_assessment.json").write_text(json.dumps(role_assessment, indent=2) + "\n")
    (ANALYSIS_DIR / "deployment_threshold_evidence.json").write_text(json.dumps(deployment_evidence, indent=2) + "\n")
    (ANALYSIS_DIR / "threshold_analysis_summary.md").write_text("\n".join(summary_lines))


if __name__ == "__main__":
    main()
