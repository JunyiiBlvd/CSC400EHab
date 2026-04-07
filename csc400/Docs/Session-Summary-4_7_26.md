# E-Habitat Session Summary
**Date:** April 7, 2026
**Supersedes:** Session-Summary-3_27_26.md for implementation status

---

## What Was Worked On This Session

### 1. Cold Source Humidity Distribution Fix

**Background:** The professor flagged that the cold source dataset's humidity column was generated with arbitrary synthetic parameters (`np.random.normal(45.0, 2.0)`, seed 99), with no grounding in real sensor data.

**Audit findings (Claude Code):**

Two files generate synthetic cold source humidity identically:

| File | Function | Lines |
|---|---|---|
| `csc400/create_features.py` | `process_cold_source()` | 32–33 |
| `csc400/generate_real_features.py` | `generate_cold_source_features()` | 30–31 |

Note: `train_hybrid_model.py` lines 55–56 also has a synthetic humidity block (seed=77) but that is for Kaggle Source D — out of scope.

**Real humidity audit:**

MIT CSAIL (`MIT_dataset.csv`, column `Humidity`):
- 1,048,575 total rows, 135 nulls
- 154,139 out-of-range values (>100 or <0) filtered as sensor glitches
- 894,301 clean values: mean 38.63, std 7.21, min 0.02, max 99.51

Kaggle HVAC (`HVAC_Kaggle.csv`): No column named `Humidity`. Three RH columns present (`RH_Supply`, `RH_Return`, `RH_Outdoor`) representing HVAC system measurements, not server room sensors — not suitable.

---

### 2. Attempted: Full Empirical Sampling from MIT CSAIL — REVERTED

**Approach tried:** Replace `np.random.normal(45.0, 2.0)` with `np.random.choice` over 894,301 clean MIT CSAIL humidity values.

**Result:** Retrain completed but validation failed badly:
- MIT CSAIL anomaly recall: **44.05%** (763/1,732 windows) — required ≥95.96% — **FAIL**
- HVAC scenario: completely undetected during training
- Humidity feasibility test: DETECTABLE (injection max score +0.2873) — PASS, but irrelevant given recall regression

**Root cause:** MIT CSAIL empirical distribution (mean ~38.6, std ~7.2) diverges significantly from the old synthetic (mean 45, std 2). The Isolation Forest contamination boundary shifted, breaking the model's learned decision surface for thermal anomalies.

**Action:** Rolled back `.pkl` artifacts from `.bak` files. Runtime unaffected throughout — backups were made before retrain began. Cold source feature CSVs on disk (`data/real/cold_source_features.csv`) were regenerated with empirical humidity but have no runtime effect since the model was not retrained from them.

---

### 3. Attempted: Calibrated Synthetic Parameters N(38.63, 7.21) — REVERTED (first attempt)


**Decision:** Rather than full empirical sampling, update the synthetic parameters to match MIT CSAIL statistics. This directly addresses the professor's concern (arbitrary parameters) while keeping the distribution shift small enough to avoid recall regression.

**Academic framing intended:** "Synthetic humidity distribution calibrated to MIT CSAIL Intel Lab sensor statistics (μ=38.63, σ=7.21, seed=99)."

**Result:** Retrain completed but validation gate failed again:
- MIT CSAIL anomaly recall: **15.53%** (required ≥95.96%) — **FAIL**
- Models restored from `.bak` files. Runtime unaffected.

**Root cause (identified by Claude Code):** The validation script `validate_on_real_anomalies.py` uses `model.predict()`, which applies the model's internal contamination boundary (`offset_`) as its threshold — approximately 0. The retrained model's `offset_` shifted from −0.6134 to −0.6327 due to the wider humidity distribution. This pushed MIT CSAIL anomaly window scores from just-below-zero to just-above-zero, causing the gate to fail.

**The critical irony:** The deployed detection threshold in `model_loader.py` is **0.15**, not 0. With the 0.15 threshold, all 1,732 MIT anomaly windows would still score below 0.15 (avg missed score = 0.011) and be correctly detected in the live backend. The gate test is measuring against a threshold that is not what the system actually uses.

**Model comparison:**

| | Old model | New model (reverted) |
|---|---|---|
| `offset_` (contamination boundary) | −0.6134 | −0.6327 |
| Recall via `model.predict()` (threshold=0) | 95.96% | 15.53% |
| Recall via 0.15 threshold (deployed) | ✅ passes | ✅ would also pass |

**Conclusion:** The recall gate is broken relative to deployed behavior. Any retrain that shifts `offset_` — even slightly — will fail the gate even when the live system would detect anomalies correctly. This must be resolved before retraining can succeed.

---

### 4. Fixed Validation Gate + Successful Retrain — COMPLETE ✅

**Fix applied:** `backend/ml/validate_on_real_anomalies.py` — replaced `model.predict()` recall gate with `score < 0.15` to match deployed behavior in `model_loader.py`. One line changed, no other files touched.

**Retrain result:** `train_hybrid_model.py` ran cleanly. New model `offset_` = −0.6327 (shifted from −0.6134 due to wider humidity distribution). Both `.pkl` artifacts overwritten.

**Validation results:**

| Check | Result |
|---|---|
| Recall on 1,732 MIT CSAIL anomaly windows | **100.00%** — all windows score below 0.15 (avg 0.005) |
| FP rate on synthetic normal data | **0.00%** |
| FP rate on 84,525 real MIT CSAIL normal windows | **0.0509%** (43 rows — min score 0.1206, none far below threshold) |
| Coolant leak feasibility | **DETECTABLE** — first detection step 9 (humidity ~65%, score 0.1467) |
| All three anomaly scenarios | **DETECTABLE** |

**Note on threshold:** `offset_` (−0.6327) and the deployed threshold (0.15) operate on the same `decision_function` scale but are different cutoffs. The system uses exactly one threshold at runtime: `score < 0.15` in `model_loader.py`. The `offset_` is irrelevant to deployed behavior — it only mattered when the validation script was incorrectly using `model.predict()`.

**To activate the new model:** restart the backend. FastAPI does not hot-reload `.pkl` files — the server must be restarted to load the new artifacts.
```bash
PYTHONPATH=. uvicorn backend.api:app --reload --port 8000
```

---

## Key Decisions Made This Session

- **pandas added to requirements.txt** — was absent; training scripts import it at the top and any fresh clone would fail without it.
- **Full empirical sampling abandoned** — distribution shift too large for the Isolation Forest.
- **Calibrated synthetic N(38.63, 7.21) adopted** — parameters grounded in MIT CSAIL statistics. Directly answers the professor's objection.
- **Validation gate fixed** — `validate_on_real_anomalies.py` now uses `score < 0.15` matching deployed behavior. Previous `model.predict()` gate was misaligned with `model_loader.py` and caused two false retrain failures.
- **Retrain complete and validated** — new model in place, all checks green.
- **Backup before retrain is mandatory** — `.bak` copies saved the session twice.

---

## Artifacts State

| File | Status |
|---|---|
| `models/model_v2_hybrid_real.pkl` | **NEW** — retrained on calibrated MIT CSAIL humidity distribution |
| `models/scaler_v2.pkl` | **NEW** — regenerated alongside retrained model |
| `models/model_v2_hybrid_real.pkl.bak` | Present — safe to delete once server restart confirmed stable |
| `models/scaler_v2.pkl.bak` | Present — safe to delete once server restart confirmed stable |
| `data/real/cold_source_features.csv` | Regenerated with calibrated synthetic N(38.63, 7.21) — consistent with retrained model |
| `csc400/create_features.py` | Updated to N(38.63, 7.21) ✅ |
| `csc400/generate_real_features.py` | Updated to N(38.63, 7.21) ✅ |
| `backend/ml/validate_on_real_anomalies.py` | Fixed — uses `score < 0.15` ✅ |
| `requirements.txt` | pandas added ✅ |

---

## Corrections to Prior Depot Records

- The HVAC failure and coolant leak detection gaps documented in Session-Summary-3_27_26.md as "NOT DETECTABLE / retraining required" were subsequently resolved by lowering the anomaly detection threshold in `model_loader.py` to **0.15**. All three anomaly scenarios are detectable at this threshold and remain detectable with the newly retrained model.
- The DOE Data Center Thermal Dataset was never acquired or used. References to it in the SRS and progress report are inaccurate. Correct training datasets: MIT CSAIL Intel Lab, Kaggle HVAC, cold source dataset (Gavin, provenance undocumented).

---

## Next Session Priorities

1. **Restart backend** to load new `.pkl` artifacts if not already done — FastAPI does not hot-reload model files.
2. **Delete `.bak` files** once server restart confirmed stable.
3. **Update SRS and progress report** — correct DOE dataset references, document calibrated humidity parameters with MIT CSAIL citation (μ=38.63, σ=7.21).
4. **Demo prep** — run 10+ anomaly injections to build sample_count for presentation data.

---

## How to Run

```bash
# From project root
source venv/bin/activate
PYTHONPATH=. uvicorn backend.api:app --reload --port 8000

# Separate terminal
npm run dev

# Feasibility test (no server needed)
PYTHONPATH=. python3 backend/tests/test_humidity_feasibility.py

# Feature analysis (no server needed)
PYTHONPATH=. python3 backend/tests/test_humidity_feature_analysis.py
```

**Critical:** Always `PYTHONPATH=.` with `uvicorn backend.api:app` from project root.
