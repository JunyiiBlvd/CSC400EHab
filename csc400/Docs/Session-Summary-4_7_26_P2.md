# E-Habitat Session Summary  
**Date:** April 7, 2026 (Threshold Optimization Phase)  
**Supersedes:** Session-Summary-4_7_26.md for thresholding, evaluation, and deployment logic  

---

## What Was Worked On This Session

### 1. Full Threshold Audit on Raw MIT Dataset

A complete end-to-end evaluation was performed using:

- Raw MIT CSAIL dataset (`datasets/MIT_dataset.csv`)
- Cleaned dataset (894,301 rows after filtering)
- Existing trained model (`models/model_v2_hybrid_real.pkl`)
- Existing scaler (`models/scaler_v2.pkl`)

#### Validation Results

- Schema matches expected raw format  
- Cleaning reproduced exactly:
  - Total rows: **1,048,575**
  - Removed: **154,274**
  - Final: **894,301**
- Humidity statistics confirmed:
  - Mean ≈ **38.63**
  - Std ≈ **7.21**

**Conclusion:**  
The humidity calibration change introduced in the previous session is **fully validated against the raw dataset**.

---

### 2. Score Distribution Analysis (Critical Finding)

Decision function scores were computed for:

- **873,745 normal windows**
- **1,732 anomaly windows**

#### Normal Distribution
- Mean ≈ **0.233**
- p01 ≈ **0.124**
- p05 ≈ **0.155**

#### Anomaly Distribution
- Mean ≈ **0.005**
- p99 ≈ **0.032**
- Max ≈ **0.067**

#### Key Observation

There is a **clear separation gap**:

- Anomaly max ≈ **0.067**
- Normal p01 ≈ **0.124**

**Conclusion:**  
The model produces **strongly separable score distributions**, indicating that the feature pipeline and Isolation Forest are functioning correctly.

---

### 3. Threshold Sweep (Core Result)

Five candidate thresholds were evaluated:

- `sklearn native (model.predict)`
- `0.027690941863431795`
- `0.04`
- `0.05`
- `0.15`

#### Key Metrics

| Threshold | Recall | FPR | Precision | F1 |
|----------|-------|-----|----------|-----|
| sklearn native | 0.155 | 0.00021 | 0.590 | 0.245 |
| **0.02769** | **0.985** | **0.00052** | **0.788** | **0.876** |
| 0.04 | 0.994 | 0.00069 | 0.741 | 0.849 |
| 0.05 | 0.997 | 0.00083 | 0.703 | 0.824 |
| 0.15 | 1.000 | 0.0412 | 0.046 | 0.088 |

#### Interpretation

- `0.15` achieves **100% recall** but produces **extreme false positives**
- Optimal threshold ≈ **0.0277**
- Strong tradeoff:
  - High recall (~98.5%)
  - Very low FPR (~0.05%)
  - High precision (~78.8%)

**Conclusion:**  
Previous 100% recall results were caused by an **overly permissive threshold**, not improved model performance.

---

### 4. Deployment Consequence Analysis

False alarms per normal data:

| Threshold | False alarms / 10,000 windows |
|----------|-------------------------------|
| sklearn native | 2.1 |
| **0.0277** | **5.24** |
| 0.04 | 6.88 |
| 0.05 | 8.34 |
| 0.15 | **412.08** |

**Conclusion:**  
- `0.15` is **not deployable**
- `0.0277` is **highly efficient and stable**

---

### 5. Temporal Alert Policy Evaluation

Temporal rules tested:

- A: Single window
- B: 2 consecutive
- C: 3 consecutive
- D: 2 of last 3
- E: 3 of last 5

#### Best Results

**Threshold = 0.0277 + 3 consecutive windows (Policy C)**

- Alert recall ≈ **96.48%**
- Alert FPR ≈ **0.005%**
- Precision ≈ **97%**
- Detection delay: **2 windows**

**Conclusion:**  
Temporal smoothing significantly reduces false positives while preserving detection capability.

---

### 6. Sklearn Native Threshold Analysis

Model properties:

- Contamination: **0.01**
- `offset_`: **-0.6327**
- Decision rule: anomaly if `score < 0`

#### Performance

- Recall ≈ **15.5%**
- FPR ≈ **0.021%**
- Precision ≈ **59%**

#### Assessment

| Role | Viability |
|------|----------|
| Primary detector | ❌ Not viable |
| Secondary confirmation | ✅ Plausible |
| Baseline reference | ✅ Valid |

**Conclusion:**  
Sklearn’s threshold is **too conservative** for this system and misses most anomalies.

---

## Key Decisions Made This Session

- Threshold **0.15 is deprecated**
- Optimal threshold identified: **0.027690941863431795**
- Temporal rule selected: **3 consecutive anomaly windows**
- Sklearn threshold retained only as:
  - reference baseline
  - optional secondary confirmation

---

## Final Deployment Configuration (Proposed)

```python
THRESHOLD = 0.027690941863431795

if score < THRESHOLD:
    anomaly_flag = True
else:
    anomaly_flag = False
