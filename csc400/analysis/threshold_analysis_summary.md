# Threshold Analysis Summary

## Input Artifacts Used
- Model: `models/model_v2_hybrid_real.pkl`
- Scaler: `models/scaler_v2.pkl`
- Raw MIT dataset: `datasets/MIT_dataset.csv`
- MIT anomaly validation dataset: `data/real/mit_anomaly_validation.csv`
- Normal windows: `873745`
- Anomaly windows: `1732`

## Candidate Thresholds Tested
- `sklearn native`
- `0.027690941863431795`
- `0.04`
- `0.05`
- `0.15`

## Key Metrics Table
| threshold/rule | recall | false_positive_rate | precision | F1 |
|---|---:|---:|---:|---:|
| `sklearn native` | `0.154734411085` | `0.000212876755` | `0.590308370044` | `0.245196706313` |
| `0.027690941863431795` | `0.984988452656` | `0.000524180396` | `0.788354898336` | `0.875770020534` |
| `0.04` | `0.993648960739` | `0.000687843707` | `0.741171403962` | `0.849037987173` |
| `0.05` | `0.996535796767` | `0.000834339538` | `0.703054989817` | `0.824456651540` |
| `0.15` | `1.000000000000` | `0.041208819507` | `0.045895383963` | `0.087762857867` |

## Best Threshold By F1
- `0.027690941863431795` with `F1=0.875770020534`

## Best Threshold With Recall >= 0.95 And Lowest FPR
- `0.027690941863431795` with `recall=0.984988452656` and `false_positive_rate=0.000524180396`

## Sklearn Native Plausibility
- Primary: `not plausible`
- Secondary: `plausible`
- Baseline: `plausible`

## Top Temporal Policy Combinations
- Best by alert F1: `0.027690941863431795` + `E_3_of_last_5` with `alert_F1=0.979766315190`
- Best recall>=0.95 lowest FPR: `0.027690941863431795` + `C_3_consecutive` with `alert_false_positive_rate=0.000052646939` and `alert_recall=0.964780600462`
- Fastest acceptable detection: `0.027690941863431795` + `C_3_consecutive` with `first_detection_index=2`
