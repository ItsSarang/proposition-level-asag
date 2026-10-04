# Final Experiment 5 Audit & Verification Report

**Project:** Automatic Short Answer Grading using Semantic and Dependency Analysis  
**Repository:** `proposition-level-asag`  
**Date:** October 4, 2026  
**Auditor:** Antigravity / Gemini CLI (Implementation Agent)  
**Status:** COMPLETE & FROZEN  
**Benchmark Scope:** $N = 2,273$ active student records, 81 active questions (Mohler et al. ASAG Benchmark)

---

## 1. Executive Audit Summary

This audit rigorously verifies the numerical consistency, scientific claims, and implementation integrity of **Experiment 5** against the frozen experimental artifacts and historical baselines (V0 through V4).

All benchmark metrics reported for Experiment 5 have been verified against the underlying result files:
- Result CSV: `evaluation/experiments/experiment_5/experiment_5_results.csv` ($N = 2,273$)
- Summary JSON: `evaluation/experiments/experiment_5/experiment_5_summary.json`
- Config JSON: `evaluation/experiments/experiment_5/experiment_5_config.json`
- Frozen Baseline: `evaluation/experiments/experiment_4/experiment_4_results.csv`

---

## 2. Metric Verification Across Systems (V0 through V5)

The table below confirms the exact numerical correspondence between the reported benchmark metrics and the underlying computed values in `experiment_5_summary.json`:

### Full Active Benchmark ($N = 2,273$)

| System | Metric | Summary JSON Value | Verified | Notes |
| :--- | :--- | :---: | :---: | :--- |
| **V0: TF-IDF Baseline** | MAE<br>RMSE<br>Pearson $r$<br>Spearman $\rho$<br>QWK<br>Mean Pred | 2.6571<br>2.9178<br>0.4184<br>0.4424<br>0.1151<br>1.5316 | **MATCH** | Exact match with frozen Experiment 1 & 4 records. Remains the globally strongest system on the benchmark. |
| **V1: Base ASAG** | MAE<br>RMSE<br>Pearson $r$<br>Spearman $\rho$<br>QWK<br>Mean Pred | 3.8050<br>4.0373<br>0.1379<br>0.1181<br>0.0180<br>0.3917 | **MATCH** | Exact match with frozen Stage 10/15 records. Strict clausal SPO triples. |
| **V2: Historical Proposed** | MAE<br>RMSE<br>Pearson $r$<br>Spearman $\rho$<br>QWK<br>Mean Pred | 3.2176<br>3.5179<br>0.1342<br>0.0765<br>0.0239<br>0.9990 | **MATCH** | Uncalibrated additive scoring; high verbosity inflation degrades Spearman $\rho$. |
| **V3: Current Proposed** | MAE<br>RMSE<br>Pearson $r$<br>Spearman $\rho$<br>QWK<br>Mean Pred | 3.5955<br>3.8862<br>0.2037<br>0.2007<br>0.0396<br>0.6042 | **MATCH** | Multi-tier semantics + Hungarian global matching. |
| **V4: Exp 4 Severity-Aware** | MAE<br>RMSE<br>Pearson $r$<br>Spearman $\rho$<br>QWK<br>Mean Pred | 3.6288<br>3.9270<br>0.2055<br>0.2033<br>0.0380<br>0.5730 | **MATCH** | Severity-aware Model D scorer. Hard zero floor causes 76.29% exact zeros. |
| **V5-A: Core + Fragments** | MAE<br>RMSE<br>Pearson $r$<br>Spearman $\rho$<br>QWK<br>Mean Pred | 3.4724<br>3.7651<br>0.2424<br>0.2397<br>0.0471<br>0.7250 | **MATCH** | Core paraphrase recovery + non-sentential fragment canonicalization. |
| **V5-B: V5-A + Guards** | MAE<br>RMSE<br>Pearson $r$<br>Spearman $\rho$<br>QWK<br>Mean Pred | 3.4711<br>3.7637<br>0.2428<br>0.2404<br>0.0472<br>0.7263 | **MATCH** | Contradiction guards suppress 47 spurious penalties. |
| **V5-C: Model D2 Alone** | MAE<br>RMSE<br>Pearson $r$<br>Spearman $\rho$<br>QWK<br>Mean Pred | 3.6288<br>3.9270<br>0.2055<br>0.2033<br>0.0380<br>0.5730 | **MATCH** | **Identical to V4.** Confirms that soft scoring alone does not improve performance. |
| **V5: Full Experiment 5** | MAE<br>RMSE<br>Pearson $r$<br>Spearman $\rho$<br>QWK<br>Mean Pred | 3.4711<br>3.7637<br>0.2428<br>0.2404<br>0.0472<br>0.7263 | **MATCH** | Full integrated system. Highest performing semantic/dependency model. |

---

## 3. Subset Metric Verification

### Sentential Reference Subset ($N = 1,341$)
- **Base ASAG (V1)**: MAE 3.5535, Pearson $r = 0.1969$, Spearman $\rho = 0.1968$, QWK 0.0325, 68.53% zeros.
- **Experiment 4 (V4)**: MAE 3.6807, Pearson $r = 0.1864$, Spearman $\rho = 0.1924$, QWK 0.0275, 72.11% zeros.
- **Experiment 5 (V5)**: MAE 3.5575, Pearson $r = 0.2373$, Spearman $\rho = 0.2590$, QWK 0.0363, 55.63% zeros.
- *Audit Status:* **VERIFIED.** V5 achieves $+34.6\%$ relative gain in Spearman rank correlation over V4 and exceeds Base ASAG ($0.2590$ vs $0.1968$).

### Non-Sentential Reference Subset ($N = 932$)
- **Base ASAG (V1)**: MAE 4.1668, Pearson $r = \text{N/A}$, Spearman $\rho = \text{N/A}$, QWK 0.0000, 100.0% zeros.
- **Experiment 4 (V4)**: MAE 3.5543, Pearson $r = 0.2253$, Spearman $\rho = 0.2296$, QWK 0.0528, 82.29% zeros.
- **Experiment 5 (V5)**: MAE 3.3467, Pearson $r = 0.2525$, Spearman $\rho = 0.2260$, QWK 0.0635, 67.70% zeros.
- *Audit Status:* **VERIFIED.** Non-sentential failure mode is substantially reduced, but NOT eliminated (67.70% zeros remain).

### Homework Assignments 1–10 ($N = 1,721$)
- **V4**: MAE 3.6597, Pearson 0.1963, Spearman 0.1968, QWK 0.0348.
- **V5**: MAE 3.5054, Pearson 0.2331, Spearman 0.2360, QWK 0.0437.
- *Audit Status:* **VERIFIED.**

### Exams 11–12 ($N = 552$)
- **V4**: MAE 3.5327, Pearson 0.2284, Spearman 0.2065, QWK 0.0478.
- **V5**: MAE 3.3641, Pearson 0.2684, Spearman 0.2324, QWK 0.0583.
- *Audit Status:* **VERIFIED.**

---

## 4. Controlled Test Suite & Backward Compatibility Verification

1. **Controlled Invariants (R1–R20)**:
   - Target: 20 requirements implemented in `tests/test_experiment_5_controlled.py`.
   - Verified count: 31 unit test functions.
   - Status: **31 / 31 passed in 3.73s** (100% pass rate).
2. **Full Repository Regression Test**:
   - Status: **571 / 571 tests passed in 32.70s with 0 failures and 0 regressions**.
3. **Experiment 4 Backward Compatibility**:
   - All files in `evaluation/experiments/experiment_4/` remain byte-for-byte identical.
   - `proposed_asag/scoring/severity_scorer.py` (Model D) and `proposed_asag/pipeline_v4.py` remain untouched.
   - In `run_experiment_5_benchmark.py`, V0–V4 predictions are imported directly from frozen baseline files.

---

## 5. Verification of Scientific Claims & Required Wording Calibrations

| Subject | Original / Potential Overstatement | Corrected, Academically Defensible Formulation | Audit Check |
| :--- | :--- | :--- | :---: |
| **System Ranking** | "V5 is the best overall ASAG system" | "V5 is the strongest semantic/dependency ASAG system developed in this project, but TF-IDF remains substantially stronger on the overall Mohler benchmark (Pearson 0.4184 vs 0.2428)." | **VERIFIED** |
| **Hypothesis H1** | "Hypothesis H1 is proven / confirmed" | "Hypothesis H1 is supported by the observed results on sentential data (without claiming formal statistical significance proof)." | **VERIFIED** |
| **Hypothesis H2** | "Contradiction guards eliminate false contradictions" | "Contradiction guards filter 47 spurious penalties with modest benchmark gains, supported by controlled tests and benchmark evidence." | **VERIFIED** |
| **Hypothesis H3** | "Hypothesis H3 is confirmed by Model D2" | "Hypothesis H3 is NOT independently supported. Ablation variant V5-C is identical to V4; soft scoring alone without upstream structural recovery yields no measurable performance improvement." | **VERIFIED** |
| **Non-Sentential Fix** | "Non-sentential fragment issue is solved" | "V5 substantially reduces the non-sentential reference failure mode, but 67.70% exact zero predictions remain on this subset." | **VERIFIED** |
| **Floor Compression** | "Floor compression and calibration are solved" | "V5 reduces floor compression (exact zeros drop from 76.29% to 60.58%), but calibration is not solved (predicted mean 0.7263 vs human 4.1839)." | **VERIFIED** |
| **AI Annotation** | "Human gold standard proved..." | "The 500-item AI annotation exercise served as diagnostic evidence only, not human ground truth. Human proposition-level validation remains incomplete." | **VERIFIED** |

---

## 6. Audit Conclusion

The Experiment 5 benchmark and documentation have passed all consistency checks. No mathematical, numerical, or architectural discrepancies exist between the recorded data and the final reports. The experiment is officially certified as **COMPLETE, VERIFIED, AND FROZEN**.
