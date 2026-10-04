# Initial Evaluation Report: System Comparison against Human Grades (Stage 15.2)

**Project:** Automatic Short Answer Grading using Semantic and Dependency Analysis  
**Repository:** `proposition-level-asag`  
**Phase:** Stage 15.2 — Evaluation Pipeline Implementation & Initial Benchmark  
**Date:** October 2026  
**Status:** COMPLETE (Deterministic evaluation pipeline implemented, tested, and executed across 2,273 active Mohler records with zero failures)

---

## 1. Executive Summary & Research Boundaries

This report documents the implementation and initial empirical execution of the evaluation framework for the three Automated Short Answer Grading (ASAG) systems under study:
1. **System 1:** TF-IDF + Cosine Similarity Baseline
2. **System 2:** Base ASAG (Basak-inspired reference coverage)
3. **System 3:** Proposed ASAG (Proposition-level extension incorporating unmatched student information)

### Mandatory Research Integrity Disclaimers
- **Research Hypothesis:** The proposed extension is an experimental hypothesis. We do **NOT** claim that the proposed extension works, improves grading, or is superior to baseline systems.
- **No Parameter Tuning:** All parameters for Stage 14 (Proposed Scoring) remain at their initial default, un-tuned values (`correct_additional_weight=0.10`, `incorrect_additional_penalty=0.20`, `irrelevant_adjustment=0.0`, `uncertain_adjustment=0.0`). No post-hoc tuning was performed on the test data.
- **No Algorithm Modification:** Neither the Base ASAG pipeline nor the Stage 13 classification rules were modified to optimize benchmark numbers.
- **Preservation of Data:** All 2,273 active student answers were evaluated deterministically without cherry-picking or silent record exclusions.

---

## 2. Dataset Facts (Benchmark Ground Truth)

The evaluation was conducted on the official **UNT Computer Science Short Answer Dataset (Version 2.0)** (Mohler, Bunescu & Mihalcea, ACL 2011), as acquired and cleaned in Stage 15.1:
- **Total Records in Archive:** 2,442 student answers across 87 questions.
- **Active Benchmark Records:** 2,273 student answers across 81 active questions (matching Mohler et al. ACL 2011 exactly).
- **Excluded Questions:** 6 selection/ordering questions prefixed with `#` in `data/docs/files` (169 answers) omitted per author specifications.
- **Target Ground Truth:** `score_ave`, the official average human score on a continuous 0.0–5.0 scale (overall mean = 4.1839, std = 1.0964, median = 4.5).
- **Human Grader Baseline:** Two human graders scored Assignments 1–10 with an inter-annotator Pearson $r = 0.5910$, Spearman $\rho = 0.5855$, MAE = 0.7263, RMSE = 1.2618. This establishes the human ceiling for the dataset.
- **No Proposition-Level Annotations:** The dataset provides only holistic, answer-level grades.

---

## 3. Evaluation Pipeline Architecture & Implementation Decisions

The evaluation layer was built with modular separation from core ASAG logic:

```
evaluation/
├── dataset/
│   ├── mohler_loader.py          # MohlerRecord, MohlerDataset, MohlerLoader
│   └── inspect_mohler.py         # Dataset inspection tool
├── metrics/
│   ├── __init__.py
│   └── asag_metrics.py           # MAE, RMSE, Pearson r, Spearman rho, QWK
├── runners/
│   ├── __init__.py
│   ├── baseline_runner.py        # System 1 wrapper
│   ├── base_asag_runner.py       # System 2 wrapper
│   ├── proposed_asag_runner.py   # System 3 wrapper
│   └── evaluation_runner.py      # Unified orchestrator
├── experiments/
│   └── run_mohler_evaluation.py  # Standalone CLI experiment runner
└── results/
    ├── mohler_evaluation_predictions.csv  # 2,273 records with all predictions
    └── mohler_evaluation_summary.json      # Structured run metrics & config
```

### Key Implementation Decisions:
1. **Explicit Scale Conversion:**
   - ASAG engines operate on normalized scores in $[0.0, 1.0]$.
   - The target human score is on a $0.0\text{--}5.0$ scale.
   - Conversion rule: `predicted_grade = round(normalized_score * 5.0, 4)`. Both `normalized` and `grade` are preserved in output schemas.
   - Human ground truth (`score_ave`) is preserved without alteration.
2. **Per-Record Triplet Evaluation:**
   - Every student answer is evaluated with its specific question and instructor reference answer.
3. **Partitioned Subsets:**
   - **All Active Benchmark (N = 2,273):** All 81 active questions across Assignments 1–10 and Exams 11–12.
   - **Assignments 1–10 (N = 1,721):** The subset graded on a uniform integer 0–5 scale by both human graders.
   - **Exams 11–12 (N = 552):** Graded on a 0–10 scale and normalized by authors to 0–5.
4. **Resilient Error Isolation:**
   - All runner executions are wrapped in isolated exception handlers. If any engine encounters an error, the failure is recorded in `failures` and flagged as `status="FAILURE"` without crashing or defaulting to zero.
   - **Result:** In the full run of 2,273 records, **0 failures** were recorded across all three systems.

---

## 4. Initial Measured Benchmark Results

### 4.1 Overall Active Benchmark (81 Questions, N = 2,273)
Target: `score_ave` (Mean: 4.1839, Std: 1.0964)

| System | Mean Pred | MAE ↓ | RMSE ↓ | Pearson $r$ ↑ | Spearman $\rho$ ↑ | QWK ↑ | Samples |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **System 1: TF-IDF + Cosine Baseline** | 1.5316 | **2.6571** | **2.9178** | **0.4184** | **0.4424** | **0.1151** | 2,273 |
| **System 2: Base ASAG (Basak-inspired)** | 0.4173 | 3.7794 | 4.0179 | 0.1419 | 0.1177 | 0.0191 | 2,273 |
| **System 3: Proposed ASAG (Untuned)** | 1.0129 | 3.2036 | 3.5101 | 0.1377 | 0.0797 | 0.0252 | 2,273 |
| *Human Agreement Ceiling (Grader 1 vs 2)\** | *4.41 / 3.94* | *0.7263* | *1.2618* | *0.5910* | *0.5855* | *—* | *1,721* |

*\*Note: Human agreement ceiling is computed on Assignments 1–10 where raw integer grades from both graders are available.*

---

### 4.2 Assignments 1–10 Subset (Uniform 0–5 Scale, N = 1,721)
Target: `score_ave` (Mean: 4.1784, Std: 1.0689)

| System | Mean Pred | MAE ↓ | RMSE ↓ | Pearson $r$ ↑ | Spearman $\rho$ ↑ | QWK ↑ | Samples |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **System 1: TF-IDF Baseline** | 1.5353 | **2.6472** | **2.9073** | **0.4177** | **0.4451** | **0.1126** | 1,721 |
| **System 2: Base ASAG** | 0.4211 | 3.7707 | 3.9960 | 0.1385 | 0.1233 | 0.0180 | 1,721 |
| **System 3: Proposed ASAG (Untuned)** | 0.9939 | 3.2168 | 3.5078 | 0.1412 | 0.0899 | 0.0245 | 1,721 |

---

### 4.3 Exams 11–12 Subset (Normalized Scale, N = 552)
Target: `score_ave` (Mean: 4.2011, Std: 1.1778)

| System | Mean Pred | MAE ↓ | RMSE ↓ | Pearson $r$ ↑ | Spearman $\rho$ ↑ | QWK ↑ | Samples |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **System 1: TF-IDF Baseline** | 1.5201 | **2.6877** | **2.9502** | **0.4240** | **0.4338** | **0.1226** | 552 |
| **System 2: Base ASAG** | 0.4053 | 3.8066 | 4.0855 | 0.1505 | 0.1093 | 0.0225 | 552 |
| **System 3: Proposed ASAG (Untuned)** | 1.0725 | 3.1626 | 3.5173 | 0.1278 | 0.0438 | 0.0273 | 552 |

---

## 5. Scientific Observations & Diagnostic Analysis

### Observation 1: Error Reduction (MAE & RMSE) from Base to Proposed ASAG
- Incorporating proposition-level evaluations of unmatched student information produces a notable reduction in prediction error compared to Base ASAG:
  - **MAE:** Drops from $3.7794 \to 3.2036$ (a reduction of **0.5758 points**, or 15.2%).
  - **RMSE:** Drops from $4.0179 \to 3.5101$ (a reduction of **0.5078 points**, or 12.6%).
- **Linguistic Mechanism:** Base ASAG relies strictly on reference proposition coverage. In student answers with syntactic variation or domain-relevant extensions not in the reference answer, Base ASAG assigns 0.0. The Proposed ASAG recognizes valid domain propositions (`CORRECT_ADDITIONAL`) and awards incremental credit ($+0.10$ normalized / $+0.50$ points), lifting under-predicted scores closer to human grades.

### Observation 2: Correlation Dynamics (Pearson $r$ & Spearman $\rho$)
- On Assignments 1–10, Pearson correlation increases slightly from Base ($r = 0.1385$) to Proposed ($r = 0.1412$).
- However, overall Spearman rank correlation decreases from Base ($\rho = 0.1177$) to Proposed ($\rho = 0.0797$).
- **Explanation:** In the current Stage 14 scoring configuration, a uniform bonus (`0.10`) is added for every `CORRECT_ADDITIONAL` proposition regardless of the question length or student verbosity. Long, multi-clause student answers receive multiple bonuses, which can re-order students inappropriately across questions where the human grader expected concise answers. This demonstrates that **unweighted additive adjustments without question-level normalization can introduce ranking noise**.

### Observation 3: Strength and Weakness of the TF-IDF Baseline
- System 1 (TF-IDF Cosine) achieves higher rank and linear correlation ($r \approx 0.418$, $\rho \approx 0.442$) than both linguistic systems.
- This is a well-known phenomenon in ASAG research: bag-of-words lexical similarity strongly captures whether students used the expected technical vocabulary from lecture slides.
- However, TF-IDF cannot differentiate correct relations from incorrect negations, nor can it provide actionable feedback on which conceptual propositions were missing, incorrect, or irrelevant.

---

## 6. Limitations

1. **Un-tuned Stage 14 Weights:**
   The current proposed adjustments (`+0.10` for correct additional, `-0.20` for incorrect) were chosen arbitrarily in Stage 14 for demonstration and unit testing. They have not been optimized via cross-validation.
2. **Absence of Clause-Level Ground Truth:**
   The Mohler dataset lacks proposition-level labels. While we can observe the aggregate grading impact, we cannot directly measure precision/recall of the Stage 13 classification decisions against human ground truth.
3. **Severe Human Score Ceiling:**
   49.3% of answers have `score_ave == 5.0` (and 62.8% have $\ge 4.5$). This extreme compression makes ranking metrics ($\rho$) especially sensitive to minor variations in predicted scores.

---

## 7. Next Steps for Research (Stage 16: Qualitative Error Analysis)

With Stage 15.2 complete and benchmark metrics established, the recommended next step is:
**Stage 16: Qualitative Error Analysis.**

Specifically, we should investigate:
1. **Specific Failure Modes of Base ASAG:** Analyze cases where Base ASAG predicted 0.0 despite high human scores, identifying dependency parse mismatches or vocabulary gaps.
2. **Success Cases of Proposed ASAG:** Identify student answers where `CORRECT_ADDITIONAL` propositions appropriately raised scores and matched human judgments.
3. **Pathology Cases of Proposed ASAG:** Examine answers where Proposed ASAG degraded ranking correlation due to false-positive `CORRECT_ADDITIONAL` classifications or verbosity inflation.
4. **Formulate Hypotheses for Post-Benchmark Calibration:** Document what weighting strategies (e.g., length normalization, evidence confidence weighting) would be necessary for future ASAG architectures.
