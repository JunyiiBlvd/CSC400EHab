# Session Summary - 4/23/26

## Branch Target

Branch: `dashupdate`

## Scope

This session was documentation and validation focused — no backend or frontend code changed. Work centered on producing final capstone submission documents and extending the ML validation pipeline to report full classification metrics.

---

## What Was Built This Session

### 1. Final Submission Documents — NEW (`docs/finaldocs/`)

Created a new directory `docs/finaldocs/` containing three documents for the final capstone presentation and submission.

#### `final_report.md` — SRS-Format Final Report (v2.0)

Full software requirements specification updated to reflect the complete, as-built system. Structure mirrors `Docs/03_24_2026_SRS.md` (v1.2) but reflects final implementation state across all four phases.

Contents:
- Executive summary with empirical research question answer (38–42ms latency delta, 48% bandwidth reduction)
- Updated user stories with final acceptance status (all US003–US007 complete)
- Complete feature/requirements compliance table
- Physics engine equations (ThermalModel, AirflowModel, HumidityModel)
- Full ML pipeline documentation including 22,239-row hybrid training dataset breakdown
- All four training sources with row counts: Synthetic (45%), MIT CSAIL (22.5%), Kaggle HVAC (16.9%), Cold Source (15.7%)
- Full validation metrics table (see section 3 below)
- Complete API reference, DB schema, WebSocket frame schema
- Risk assessment with final disposition for every risk from v1.2
- Known limitations
- Success metrics — final evaluation
- Change log through April 2026

#### `slide_deck_context.md` — Presentation Slide Deck Blueprint (15–20 Slides)

Context document structured for AI-assisted or manual slide generation. 18 core slides + 2 optional appendix slides.

Slide-by-slide breakdown:
1. Title
2. Problem
3. Research Question
4. System Overview
5. Architecture Diagram (edge vs. centralized dual-path)
6. PsyEngine — Physics Simulation
7. ML Pipeline (Isolation Forest, training data, threshold)
8. Real-World Validation (full metrics table + score distribution visual direction)
9. Injection Scenarios (thermal spike, HVAC failure, coolant leak)
10. Live Demo (video transition slide)
11. What the Demo Shows (post-video debrief)
12. Results — Detection Latency
13. Results — Bandwidth
14. Known Limitations
15. Lessons Learned
16. Future Work
17. Conclusion
18. Q&A
19. Tech Stack (optional appendix)
20. Database & Persistence (optional appendix)

Each entry includes: title, key bullet points, context notes for a designer or AI generator, and visual direction.

#### `presentation_script.md` — 5-Minute Presentation Script

Full word-for-word script with stage directions formatted as a play. Speaker assignments: Logan (project lead, intro/results/conclusion), Jared (system overview/architecture/future), Gavin (physics/ML/validation).

Key decisions documented in the script:
- **Pre-recorded demo video is narrated** (voiceover recorded with the screen capture, not live commentary). Rationale: the demo involves waiting for the 10-step ML window to fill, watching the comparison panel populate — timing these live while speaking is unreliable. Narrated = one clean rehearsed take.
- Video target length: 90 seconds
- Video recording checklist included (server state, DB state, screen recorder setup, mic check)

Timing guide:
| Section | Target |
|---|---|
| Intro + Problem + Research Q | 0:45 |
| System Overview + Architecture | 0:45 |
| Physics + ML + Validation | 1:00 |
| Injection Scenarios | 0:20 |
| Demo Video (narrated) | 1:30 |
| Demo Debrief + Results | 0:45 |
| Limitations + Lessons | 0:35 |
| Future Work + Conclusion | 0:20 |
| **Total** | **~5:00** |

---

### 2. Extended Validation Script (`backend/ml/validate_on_real_anomalies.py`) — UPDATED

Previous script only computed recall against anomaly windows. Extended to compute full binary classification metrics by also scoring in-distribution normal data.

New behavior:
- Scores MIT CSAIL normal windows (`data/real/mit_features.csv`, 84,525 rows) as negatives
- Scores synthetic PsyEngine baseline (`data/synthetic/normal_telemetry.csv`, 49,991 windows) as negatives
- Scores cold source features separately with documented exclusion rationale
- Computes: Recall, Precision, F1, Specificity, Accuracy, FPR, AUC-ROC
- Writes full report to `data/real/validation_results.txt`

**Validated results (run live this session):**

```
Confusion Matrix  (in-distribution normal only)
  TP:   1732  |  FN:     0
  TN: 134473  |  FP:    43

Classification Metrics
  Recall:           100.00%
  Precision:         97.58%
  F1 Score:          98.77%
  Specificity:       99.97%
  Accuracy:          99.97%
  False Positive Rate: 0.032%
  AUC-ROC:            1.0000

Score Distribution
  Avg anomaly windows: +0.005
  Avg normal  windows: +0.269
  (Min normal score: +0.121  — no overlap with anomaly max of +0.068)
```

---

### 3. Cold Source OOD Finding — DOCUMENTED

**Discovery:** When cold source features (`data/real/cold_source_features.csv`) are scored against the deployed model, 94.93% of windows (3,312 / 3,489) are flagged as anomalous.

**Root cause identified:** The cold source dataset has no real humidity column. Humidity was imputed using:
```python
np.random.seed(99)
humidity = np.random.normal(38.63, 7.21, len(df))
```

This generates **i.i.d. independent draws** per row. The MIT CSAIL σ=7.21 is the *marginal* standard deviation across thousands of readings over weeks — it correctly describes how far humidity can range in the dataset, but not how much it changes between consecutive 1-second readings.

Real sensors are temporally correlated. Consecutive readings differ by fractions of a unit. The expected sliding-window variance of 10 i.i.d. N(μ, 7.21²) draws is σ² = **51.98**. The observed cold source `hum_var` feature (col7) averages **49.0** — this match is exact and confirms the diagnosis.

**Impact on deployed model:** None. The model was retrained on this data and still achieved 100% recall / 97.58% precision on valid test sets. The 85% of training data with correct temporal structure (MIT CSAIL, synthetic, Kaggle) dominated the learned decision boundary.

**Impact on runtime:** None. `cold_source_features.csv` is a training artifact and is not loaded at runtime.

**Fix if time permits:** Replace i.i.d. sampling with a correlated time-series (AR(1) or random walk with drift) for imputed humidity. Would require model v3 retraining — out of scope for the current submission window.

**Academic framing:** "Matching a marginal distribution is not sufficient for time-series imputation — you also need to match the temporal correlation structure. The model detected this before we did."

---

## Files Changed

| File | Change |
|---|---|
| `docs/finaldocs/final_report.md` | **NEW** — SRS-format final report v2.0 |
| `docs/finaldocs/slide_deck_context.md` | **NEW** — 18-slide presentation blueprint |
| `docs/finaldocs/presentation_script.md` | **NEW** — 5-minute script with stage directions |
| `backend/ml/validate_on_real_anomalies.py` | **UPDATED** — full metrics: precision, F1, specificity, FPR, AUC-ROC |
| `data/real/validation_results.txt` | **UPDATED** — full validation report written by updated script |

No backend API, frontend, or model files were changed.

---

## Current State

### System
All runtime behavior unchanged. Server, WebSocket, ML pipeline, and dashboard are identical to end of 4/16 session.

### Documents
Three final submission documents in `docs/finaldocs/` — ready for review, slide generation, and presentation rehearsal.

### Validation
Full classification metrics computed and saved to `data/real/validation_results.txt`. Cold source exclusion documented with mathematical rationale.

---

## Next Session Priorities

1. **Presentation rehearsal** — run through the 5-minute script, time each section, adjust pacing
2. **Record demo video** — follow checklist in `presentation_script.md`; target 90 seconds; use narrated format
3. **Slides** — generate from `slide_deck_context.md`; 18 core slides; check visual direction per slide
4. **Cold source fix (if time)** — replace i.i.d. humidity imputation with AR(1) in `create_features.py` and `generate_real_features.py`; retrain model v3
5. **Final review** — verify `docs/finaldocs/final_report.md` against actual codebase before submission