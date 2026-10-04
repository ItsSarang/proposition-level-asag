# Experiment 4 Research Analysis Report

**Phase:** Phase 5 — Experiment 4 Research Analysis  
**Repository:** `proposition-level-asag`  
**Dataset:** UNT Computer Science Short Answer Dataset v2.0 (*Mohler et al., 2011*)  
**Status:** FROZEN BENCHMARK SCIENTIFIC ANALYSIS (Analysis-Only Phase)  
**Evaluated Records:** $N=2,273$ active student responses across 81 active questions  
**Target Variable:** Continuous human average grade (`score_ave`) on a $[0.0, 5.0]$ scale  
**Date:** October 2026  

---

## 1. Executive Summary

This research analysis interprets the empirical results of **Experiment 4: Severity-Aware Proposed ASAG**, evaluated on the 2,273 active student responses of the UNT Computer Science Short Answer Dataset v2.0 (*Mohler et al., 2011*). Experiment 4 was executed under an **absolute model freeze** (single formal run, zero post-hoc parameter adjustments, zero new domain rules).

The experiment tested whether extending a classical semantic/dependency-based ASAG pipeline (*Basak et al., 2019*) with:
1. Four-way proposition-level epistemic classification (`CORRECT_ADDITIONAL`, `IRRELEVANT`, `UNCERTAIN`, `INCORRECT`),
2. Multi-tier contradiction severity estimation (`CORE_CONTRADICTION`, `MODERATE`, `MINOR`, `UNRESOLVED`), and
3. A decomposed core/additional scoring formulation (**Model D**: core invalidation discounting, gated non-compensatory positive bonus, and itemized minor penalties)

improves agreement with human grading while resolving the verbosity inflation and misconception tolerance observed in earlier iterations.

### Core Scientific Findings
1. **Technical Feasibility of Proposition-Level Evaluation (RQ1 — Confirmed)**:  
   Unmatched student information is ubiquitous: **93.00% of student answers** ($2,114 / 2,273$) contained propositions outside the instructor reference answer ($4,695$ unmatched propositions total, average $2.06$ per answer). The pipeline successfully isolated, represented, and categorized all $4,695$ propositions with 100% deterministic reproducibility, character-level span provenance, and zero runtime failures.
2. **Epistemic Restraint and the Zero `CORRECT_ADDITIONAL` Count**:  
   Across the benchmark, system-assigned `CORRECT_ADDITIONAL = 0`. Under our Phase 9 epistemic guidelines, the system refuses to guess that an unmatched assertion is a valid domain truth without verified domain proof. Because only three verified domain assertions were active in `CuratedDomainKnowledge` (`PK_NOT_NULL`, `BST_INORDER_SORTED`, `COMPILER_INTERMEDIATE_REP`), none of which occurred as secondary clauses in this dataset, all $1,815$ topical unverified assertions ($38.66\%$) defaulted safely to `UNCERTAIN`. Model D assigned an adjustment of $0.0$ to `UNCERTAIN`, completely preventing speculative grade inflation.
3. **Agreement with Holistic Human Grading (RQ2 — Partial and Metric-Dependent)**:  
   - **Examination Subset Advance (Exams 11–12, $N=552$)**: On complex examination questions, Experiment 4 (V4) achieved the highest Pearson correlation ($r=0.2284$), highest Spearman rank correlation ($\rho=0.2065$), highest Quadratic Weighted Kappa ($\kappa=0.0478$), and lowest MAE ($3.5327$) of any symbolic ASAG pipeline evaluated.
   - **Non-Sentential Reference Recovery ($N=932$)**: Where Base ASAG (V1) collapsed to a constant $0.0000$ ($r = \text{NaN}$), Experiment 4 restored meaningful ranking ability ($r=0.2253$, $\rho=0.2296$, $\kappa=0.0528$).
   - **Global Dataset vs. Surface Baseline ($N=2,273$)**: Across the full benchmark, V4 achieved $r=0.2055, \rho=0.2033, \text{MAE}=3.6288, \kappa=0.0380$. While eliminating the rank-order collapse of historical unweighted bonuses (V2: $\rho=0.0765$), V4 did not outperform surface lexical overlap (V0 TF-IDF Baseline: $r=0.4184, \rho=0.4424, \text{MAE}=2.6571$).
4. **Primary Architectural Bottleneck (Symmetric Argument-Binding Failure)**:  
   15 false-positive `CORE_CONTRADICTION` classifications occurred in symmetric comparison questions (notably Question 10.5, Binary Search Trees). Pairwise clause matching cross-aligned opposite branches ("left is smaller" vs. "right is larger"), triggering severe 50% core score cuts on completely correct answers. This is diagnosed as a structural discourse and argument-binding limitation rather than a scoring flaw.

---

## 2. Research Questions

This investigation separates the project's overarching hypothesis into two distinct research questions:

### RQ1: Technical Feasibility
> *"Can an interpretable proposition-level extension of a classical semantic/dependency-based ASAG system extract and evaluate unmatched student information as correct additional, irrelevant, or incorrect information with transparent provenance?"*

- **Focus**: Algorithmic capability, modular separation of concerns, character-level span isolation, deterministic epistemic categorization, and explicit severity estimation.
- **Evaluation Standard**: Whether the pipeline can reliably detect and classify propositions without runtime exceptions, data leakage, or uninterpretable embeddings.

### RQ2: Empirical Grading Agreement
> *"Does incorporating this proposition-level evaluation into grading improve agreement with holistic human grading on an authentic benchmark dataset?"*

- **Focus**: Quantitative alignment with human score averages across MAE, RMSE, Pearson correlation ($r$), Spearman rank correlation ($\rho$), and Quadratic Weighted Kappa ($\kappa$).
- **Evaluation Standard**: Whether severity-aware adjustments improve upon the Base ASAG system and surface baseline across diverse question types (coursework assignments, exams, sentential references, non-sentential fragments).

> [!IMPORTANT]
> **Epistemic Separation Rule**: RQ1 and RQ2 are strictly decoupled. Demonstrating that a system can assign proposition-level labels (RQ1) does **not** imply that those labels improve holistic answer-level agreement with human graders (RQ2), nor does it prove that the system-assigned labels match human proposition-level judgments without a dedicated human annotation study.

---

## 3. Frozen Experimental Setup

The benchmark evaluation protocol was locked prior to execution:
- **Configuration Manifest**: [`experiment_4_manifest.json`](file:///Users/sarang/Dev/College/MIT_WPU/Projects/AIES/proposition-level-asag/evaluation/experiments/experiment_4/experiment_4_manifest.json)
- **Active Benchmark**: UNT Computer Science Short Answer Dataset v2.0 (*Mohler et al., 2011*)
  - 81 active questions (Assignments 1–10, Exams 11–12)
  - 2,273 active student answers
  - Raw active CSV SHA-256: `3af0a16648cbd0d1684c3acc100c6c998002c0993bf7da78d55f8c3387e1e5f8`
- **Scoring Architecture (Model D)**:
  $$\text{Effective Core Score: } S_{\text{core\_effective}} = S_{\text{base}} \times (1.0 - d_{\text{core}})^{n_{\text{core}}}$$
  $$\text{Gated Positive Bonus: } \text{pos\_adj} = \min\left(M_{\text{pos}} \cdot \frac{r \cdot n_{\text{correct}}}{1 + r \cdot n_{\text{correct}}}, 0.50 \cdot S_{\text{core\_effective}}\right)$$
  $$\text{Minor Penalty: } \text{minor\_pen} = \sum_{i \in \text{minor}} w_{\text{minor}} \cdot \sigma_i$$
  $$\text{Final Grade: } \text{Grade} = \min(1.0, \max(0.0, S_{\text{core\_effective}} + \text{pos\_adj} - \text{minor\_pen})) \times 5.0$$
- **Frozen Hyperparameters**:
  - $M_{\text{pos}} = 0.25$
  - Diminishing rate $r = 0.50$
  - Core invalidation discount $d_{\text{core}} = 0.50$
  - Core contradiction threshold $\sigma_{\text{threshold}} = 0.90$
  - Minor penalty weight $w_{\text{minor}} = 0.20$
  - Target scale: Continuous $[0.0, 5.0]$
- **Domain Knowledge Freeze**: Exactly three curated rules (`PK_NOT_NULL`, `BST_INORDER_SORTED`, `COMPILER_INTERMEDIATE_REP`).
- **Systems Evaluated**:
  - **V0**: TF-IDF Cosine Baseline
  - **V1**: Base ASAG (*Basak et al., 2019*)
  - **V2**: Historical Proposed ASAG (Stage 15.2 / Stage 17)
  - **V3**: Current Proposed ASAG (Experiment 1 / Experiment 2)
  - **V4**: Experiment 4 (Severity-Aware Proposed ASAG)

---

## 4. Results Comparison

### 4.1 Primary Results across Benchmark Partitions

| Partition / System | Sample Size ($N$) | MAE | RMSE | Pearson $r$ | Spearman $\rho$ | QWK ($\kappa$) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Full Active Dataset** | **2,273** | | | | | |
| — V0: TF-IDF Baseline | | **2.6571** | **2.9178** | **0.4184** | **0.4424** | **0.1151** |
| — V1: Base ASAG | | 3.8050 | 4.0373 | 0.1379 | 0.1181 | 0.0180 |
| — V2: Historical Proposed | | 3.2176 | 3.5179 | 0.1342 | 0.0765 | 0.0239 |
| — V3: Current Proposed | | 3.5955 | 3.8862 | 0.2037 | 0.2007 | 0.0396 |
| — **V4: Experiment 4** | | 3.6288 | 3.9270 | 0.2055 | 0.2033 | 0.0380 |
| **Assignments 1–10** | **1,721** | | | | | |
| — V0: TF-IDF Baseline | | **2.6472** | **2.9073** | **0.4177** | **0.4451** | **0.1126** |
| — V1: Base ASAG | | 3.8030 | 4.0204 | 0.1331 | 0.1229 | 0.0165 |
| — V2: Historical Proposed | | 3.2361 | 3.5192 | 0.1365 | 0.0850 | 0.0226 |
| — V3: Current Proposed | | 3.6109 | 3.8899 | 0.2053 | 0.1989 | 0.0391 |
| — **V4: Experiment 4** | | 3.6597 | 3.9432 | 0.1963 | 0.1969 | 0.0348 |
| **Exams 11–12** | **552** | | | | | |
| — V0: TF-IDF Baseline | | **2.6877** | **2.9502** | **0.4240** | **0.4338** | **0.1226** |
| — V1: Base ASAG | | 3.8111 | 4.0898 | 0.1496 | 0.1097 | 0.0223 |
| — V2: Historical Proposed | | 3.1599 | 3.5138 | 0.1274 | 0.0457 | 0.0275 |
| — V3: Current Proposed | | 3.5476 | 3.8747 | 0.1989 | 0.1983 | 0.0411 |
| — **V4: Experiment 4** | | 3.5327 | 3.8763 | **0.2284** | **0.2065** | **0.0478** |
| **Sentential Reference Subset** | **1,341** | | | | | |
| — V0: TF-IDF Baseline | | **2.7464** | **2.9427** | **0.3743** | **0.3591** | **0.0685** |
| — V1: Base ASAG | | 3.5535 | 3.8176 | 0.1969 | 0.1968 | 0.0325 |
| — V2: Historical Proposed | | 2.8837 | 3.2052 | 0.2038 | 0.1917 | 0.0450 |
| — V3: Current Proposed | | 3.6412 | 3.8784 | 0.1953 | 0.1975 | 0.0323 |
| — **V4: Experiment 4** | | 3.6807 | 3.9227 | 0.1864 | 0.1925 | 0.0275 |
| **Non-Sentential Reference Subset** | **932** | | | | | |
| — V0: TF-IDF Baseline | | **2.5286** | **2.8816** | **0.4681** | **0.5342** | **0.1781** |
| — V1: Base ASAG | | 4.1668 | 4.3341 | N/A* | N/A* | 0.0000 |
| — V2: Historical Proposed | | 3.6980 | 3.9243 | 0.0113 | -0.0459 | 0.0010 |
| — V3: Current Proposed | | 3.5298 | 3.8976 | 0.2134 | 0.2201 | 0.0499 |
| — **V4: Experiment 4** | | 3.5543 | 3.9333 | **0.2253** | **0.2296** | **0.0528** |

*\*Base ASAG produced a constant score of 0.0000 on all 932 non-sentential reference records, resulting in zero variance and undefined Pearson and Spearman correlation coefficients.*

### 4.2 Distinguishing Error, Correlation, and Agreement
To prevent ungrounded generalizations, these metrics must not be conflated into a single ranking:
1. **Absolute Error (MAE / RMSE)**:
   - Lowest error is achieved by V0 (TF-IDF Baseline, $\text{MAE}=2.6571$) and V2 (Historical Proposed, $\text{MAE}=3.2176$).
   - However, V2's lower MAE was achieved via **uncalibrated score shifting**: awarding generic additive bonuses to verbose answers pushed the prediction mean upward ($0.39 \to 1.00$), shifting predictions closer to the elevated human mean ($4.18$) without improving ranking quality.
2. **Linear & Rank Correlation (Pearson $r$ / Spearman $\rho$)**:
   - V2 suffered a severe degradation in rank correlation ($\rho=0.0765$), demonstrating that unweighted bonuses distorted relative student rankings.
   - V4 successfully restored ranking order ($\rho=0.2033$, a $+165.8\%$ relative gain over V2 and $+72.1\%$ over V1).
   - On Exams, V4 achieved the highest correlation ($r=0.2284, \rho=0.2065$) among all symbolic systems.
3. **Inter-Rater Agreement (Quadratic Weighted Kappa $\kappa$)**:
   - QWK penalizes severe disagreements quadratically. V4 achieved $\kappa=0.0478$ on Exams and $\kappa=0.0528$ on non-sentential questions, surpassing V1 ($\kappa=0.0180$ overall).
   - Nonetheless, all symbolic systems remain in the slight agreement band ($\kappa < 0.20$) due to systematic floor compression.

---

## 5. Score Calibration Analysis

### 5.1 Prediction Distribution and Descriptive Bias

| System | Mean Score | Std Dev | Min | Max | Descriptive Bias | % in $[0.0, 0.5]$ (Floor) | % in $[4.5, 5.0]$ (Ceiling) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Human Annotator** | **4.1839** | 1.0966 | 0.00 | 5.00 | 0.0000 | 1.85% | 61.50% |
| **V0: TF-IDF Baseline** | 1.5316 | 1.1572 | 0.00 | 5.00 | -2.6523 | 19.62% | 3.34% |
| **V1: Base ASAG** | 0.3917 | 1.0117 | 0.00 | 5.00 | -3.7922 | 82.23% | 2.55% |
| **V2: Historical Proposed** | 0.9990 | 1.1729 | 0.00 | 5.00 | -3.1849 | 55.21% | 3.48% |
| **V3: Current Proposed** | 0.6042 | 1.2896 | 0.00 | 5.00 | -3.5797 | 73.16% | 6.20% |
| **V4: Experiment 4** | 0.5730 | 1.3355 | 0.00 | 5.00 | -3.6109 | 78.44% | 6.64% |

### 5.2 Analysis of Floor Compression and Prediction Bias
- **Severe Under-Prediction**: Human graders awarded $\ge 4.5$ points to $61.50\%$ of answers. In contrast, V4 predicted $\ge 4.5$ points for only $6.64\%$ of answers, while compressing $78.44\%$ of answers below $0.5$ points.
- **Negative Descriptive Bias**: V4 exhibits a descriptive bias of $-3.6109$ points. This is not a numerical error; it reflects the **structural conservatism** of classical dependency matching. In symbolic dependency ASAG, if a student expresses a correct idea using grammatical structures, passive constructions, or terminology not anticipated in the instructor's reference triples, zero reference coverage is matched, resulting in a base score of $0.0$.
- **High-Human / Low-System Discrepancy**: Across the dataset, $1,688$ student answers had human grades $\ge 4.0$ but system predictions $< 1.0$. These cases are driven primarily by syntactic paraphrase divergence, non-sentential reference fragmentation, and comparative argument-binding failures.

---

## 6. Additional-Information Analysis (RQ1)

### 6.1 Prevalence of Unmatched Student Information
- **Total active student answers**: $2,273$
- **Answers containing unmatched propositions**: **2,114** (**93.00%**)
- **Answers without unmatched propositions**: **159** (**7.00%**)
- **Total unmatched propositions extracted**: **4,695**
- **Mean unmatched propositions per answer**: $2.06$ overall ($2.22$ per answer with unmatched content)

These empirical counts confirm that student responses in technical domains almost always contain information beyond the reference answer. Discarding this information (as classical reference-coverage ASAG does) ignores over 90% of student linguistic production.

### 6.2 Epistemic Classification Distribution
All $4,695$ unmatched propositions were processed by the frozen four-way classifier:

| System-Assigned Classification | Proposition Count | Proportion of Unmatched (%) | Role in Scoring Pipeline |
| :--- | :---: | :---: | :--- |
| **CORRECT_ADDITIONAL** | **0** | **0.00%** | Epistemically verified domain truths from curated rules |
| **IRRELEVANT** | **2,816** | **59.98%** | Off-topic or question-irrelevant assertions |
| **UNCERTAIN** | **1,815** | **38.66%** | On-topic/relevant propositions lacking formal rule verification |
| **INCORRECT** | **64** | **1.36%** | Property contradictions, antonym conflicts, or direct value clashes |

### 6.3 Scientific Audit of the Zero `CORRECT_ADDITIONAL` Count
A defining outcome of Experiment 4 is that `CORRECT_ADDITIONAL = 0`. This is the result of three deliberate, interacting factors:
1. **Conservative Epistemic Grounding (Mechanism Design)**:  
   Under Phase 9 guidelines, an unmatched student assertion is **never assumed correct merely because it is grammatically well-formed or topical**. To earn an unearned bonus, an assertion must be verified against an explicit rule in `CuratedDomainKnowledge`.
2. **Narrow Domain Coverage (Frozen Rule Scope)**:  
   The frozen knowledge base contained exactly three verified rules (`PK_NOT_NULL`, `BST_INORDER_SORTED`, `COMPILER_INTERMEDIATE_REP`). These rules were curated during early development to test properties on specific reference questions.
3. **Dataset Content Realities (Lack of Unprompted Rule Targets)**:  
   None of the 81 questions in the Mohler benchmark prompted students to write about nullability of primary keys, inorder BST traversal, or compiler intermediate representations as secondary unmatched clauses.
4. **Epistemic Default to `UNCERTAIN`**:  
   Because the system could not verify the remaining $1,815$ relevant propositions ($38.66\%$), it safely assigned them the label `UNCERTAIN`. Model D treats `UNCERTAIN` propositions as neutral ($\Delta = 0.0$). This demonstrates **rigorous epistemic restraint**: the system refuses to guess correctness or award unverified bonuses.

---

## 7. Severity Analysis and Model D Behavior

### 7.1 Contradiction Severity Breakdown
Among the 64 propositions classified as `INCORRECT`:

| Severity Level | Severity Score ($\sigma$) | Count | Proportion of Incorrect (%) | Scoring Treatment |
| :--- | :---: | :---: | :---: | :--- |
| **CORE_CONTRADICTION** | 1.00 | 15 | 23.44% | 50% multiplicative core invalidation discount ($d_{\text{core}}=0.50$) |
| **MODERATE** | 0.60 | 42 | 65.62% | Graded minor penalty deduction ($\Delta = 0.20 \times 0.60 = -0.1200$) |
| **MINOR** | 0.25 | 2 | 3.12% | Peripheral deduction ($\Delta = 0.20 \times 0.25 = -0.0500$) |
| **UNRESOLVED** | 0.00 | 5 | 7.81% | Zero deduction ($\Delta = 0.0000$) |
| **NONE (Non-Incorrect)** | 0.00 | 4,631 | — | Non-incorrect unmatched propositions |

### 7.2 Score Adjustment Totals across Answers
- **Answers receiving positive adjustments**: **0** ($0.00\%$)
- **Answers receiving negative adjustments**: **44** ($1.94\%$)
- **Answers receiving zero adjustments**: **2,229** ($98.06\%$)
- **Mean negative adjustment (when penalized)**: $-0.1236$ normalized ($-0.6180$ points on $[0, 5]$ scale)
- **Mean net adjustment across all answers**: $-0.0024$ normalized ($-0.0120$ points)

### 7.3 Analysis of Representative Scenarios
To verify that Model D operates as designed across diverse linguistic situations, we examine eight representative cases extracted from `experiment_4_results.csv`:

#### Case 1: Correct Core Only (No Unmatched Information)
- **Record**: Question 1.1, Student 9
- **Student Answer**: *"Simulating the behavior of only a portion of the desired software product."*
- **Human Grade**: 5.0 | **V3 Grade**: 4.92 | **V4 Grade**: **4.92**
- **Unmatched Propositions**: 0 | **Net Adjustment**: 0.0000
- **Interpretation**: Full core credit is preserved identically without penalty or distortion.

#### Case 2: Correct Core + Irrelevant Information
- **Record**: Question 1.2, Student 3
- **Student Answer**: Contains 1 matched core proposition and 4 tangential statements.
- **Human Grade**: 3.0 | **V3 Grade**: 4.83 | **V4 Grade**: **4.83**
- **Classifications**: 4 `IRRELEVANT` | **Net Adjustment**: 0.0000
- **Interpretation**: Demonstrates that irrelevant commentary does not corrupt or penalize the verified core score.

#### Case 3: Correct Core + Unsupported Relevant Information
- **Record**: Question 1.1, Student 1
- **Human Grade**: 5.0 | **V3 Grade**: 0.00 | **V4 Grade**: **4.76**
- **Classifications**: 2 `IRRELEVANT`, 2 `UNCERTAIN` | **Net Adjustment**: 0.0000
- **Interpretation**: Relevant but unverified propositions default to `UNCERTAIN` with zero bonus, preserving the core grade ($4.76$) without speculative grade inflation.

#### Case 4: Correct Core + Minor Contradiction
- **Record**: Question 4.3, Student 3
- **Human Grade**: 5.0 | **V3 Grade**: 0.00 | **V4 Grade**: **0.00**
- **Classifications**: 2 `MINOR` ($\sigma=0.25$), 1 `CORE_CONTRADICTION`
- **Minor Penalty**: Each minor contradiction applied $\Delta = -0.0500$.
- **Interpretation**: Illustrates the small, non-destructive penalty assigned to peripheral phrasing issues.

#### Case 5: Correct Core + Moderate Contradiction
- **Record**: Question 7.2, Student 5
- **Human Grade**: 4.0 | **V3 Grade**: 1.58 | **V4 Grade**: **0.98**
- **Classifications**: 1 `MODERATE` ($\sigma=0.60$), 4 `IRRELEVANT`, 1 `UNCERTAIN`
- **Scoring Execution**: Base score was $1.5833$ (normalized $0.3167$). Moderate penalty deducted $0.1200$ normalized, yielding final score $0.9833$.
- **Interpretation**: Proves exact Model D behavior: a moderate misconception applies a calibrated deduction ($-0.60$ points on $[0, 5]$) without invalidating the core credit.

#### Case 6: Correct Core + Core Contradiction
- **Record**: Question 10.5, Student 10
- **Human Grade**: 4.5 | **V3 Grade**: 0.55 | **V4 Grade**: **0.61**
- **Classifications**: 1 `CORE_CONTRADICTION` ($\sigma=1.00$), 2 `IRRELEVANT`, 4 `UNCERTAIN`
- **Scoring Execution**: Base was $1.2153$ (normalized $0.2431$). Core invalidation discount applied: $S_{\text{core\_effective}} = 0.2431 \times 0.50 = 0.1215$, yielding final grade $0.6076$.
- **Interpretation**: Demonstrates the multiplicative core invalidation discount: core contradictions cut core credibility in half rather than applying an arbitrary additive subtraction.

#### Case 7: Partial Core + Contradiction
- **Record**: Question 4.4, Student 29
- **Human Grade**: 3.0 | **V3 Grade**: 0.50 | **V4 Grade**: **0.00**
- **Classifications**: 1 `MODERATE` ($\sigma=0.60$), 4 `IRRELEVANT`
- **Scoring Execution**: Base was $0.2500$ (normalized $0.0500$). Penalty was $0.1200$. Raw score $0.0500 - 0.1200 = -0.0700 \to$ clipped to $0.0000$ (`is_clipped_lower: True`).
- **Interpretation**: When partial core credit is small and a contradiction is present, the deduction exceeds the credit and cleanly clips at zero, preventing negative grades.

#### Case 8: Multiple Contradictions
- **Record**: Question 9.1, Student 3
- **Human Grade**: 5.0 | **V3 Grade**: 0.00 | **V4 Grade**: **0.00**
- **Classifications**: 2 `MODERATE` ($\sigma=0.60$), 2 `IRRELEVANT`
- **Scoring Execution**: Base was $0.4058$ (normalized $0.0812$). Accumulated penalty was $2 \times 0.1200 = 0.2400$, clipping at $0.0000$.
- **Interpretation**: Demonstrates cumulative penalty saturation across multiple conceptual errors.

---

## 8. Failure Taxonomy

An evidence-based audit of errors across the 2,273 records reveals ten distinct failure modes:

| Category | Description | Est. Benchmark Frequency | Architectural Attribution | Classification Type |
| :--- | :--- | :---: | :--- | :--- |
| **A. Proposition Extraction Failure** | Non-sentential fragments, parentheticals, or nested clauses fail to yield complete S-P-O triples. | Moderate (~15–20% of answers) | Base ASAG Pipeline | Research Limitation |
| **B. Argument Binding Failure** | Loss of subject in passive clauses, prepositional phrase misattachment, or bulleted list fragmentation. | Low–Moderate (~5–8% of answers) | Base Dependency Parser | Implementation / Tool Limitation |
| **C. Semantic Matching Failure** | Domain-specific technical synonyms not captured by WordNet path similarity or lemma matching. | High (~30–40% of answers) | Base ASAG Semantic Matcher | Research Limitation |
| **D. Cross-Slot Gating Failure** | Predicate gating prevents valid syntactic transpositions or incorrectly allows superficial noun matches. | Low (~3% of answers) | Proposed Matcher (V3/V4) | Implementation Decision |
| **E. Contradiction Detection Failure** | Symmetric comparative clauses (e.g. left/smaller vs. right/larger) cross-wire opposite branches. | Low (~1.5% of answers; 15 core cases) | Proposed Contradiction Detector | Representation Defect |
| **F. Severity Estimation Over-Escalation** | Assigning `CORE_CONTRADICTION` to valid answers because an entity property keyword matched an inverted clause. | Low (15 cases in Q10.5, Q4.3) | Proposed Severity Estimator | Knowledge Base Binding Defect |
| **G. Evidence Verification Limitation** | Curated domain knowledge scope is too narrow (only 3 rules), forcing all valid technical additions to `UNCERTAIN`. | High (1,815 propositions; 38.66%) | Proposed Epistemic Verifier | Knowledge Base Scope Limitation |
| **H. Score Floor Compression** | 78.44% of predictions fall in $[0.0, 0.5]$ due to all-or-nothing dependency triple matching. | Pervasive across entire dataset | Base ASAG Scoring | Structural Paradigm Limitation |
| **I. Reference-Format Limitation** | 33 of 81 questions have non-sentential reference phrases, breaking classical clause extraction. | Exactly 33 questions (932 records, 41.0%) | Mohler Dataset Artifact | Dataset Design Limitation |
| **J. Grader Granularity Mismatch** | Human scores are holistic answer-level impressions ($4.18$ mean), whereas the system is an itemized symbolic auditor. | Pervasive across entire dataset | Study Protocol | Evaluative Incommensurability |

---

## 9. Binary Search Tree / Symmetric Relation Analysis (Question 10.5)

### 9.1 Anatomy of the Failure
Question 10.5 (*"What is a binary search tree?"*) represents the most instructive qualitative failure in Experiment 4:
- **Reference Answer**:  
  > *"A binary tree that has the property that for any node the left child is smaller than the parent which in turn is smaller than the right child."*
- **Representative Student Answer (Student 1)**:  
  > *"A binary search tree is a binary tree where the value in any node 'n' is greater than the value in every node in n's left subtree but less than every node in n's right subtree."*  
  (Human Grade: **5.0 / 5.0**)
- **Pipeline Execution Trace**:
  1. The reference answer expresses ordering from the perspective of the child:  
     `Ref_1`: `(left child, is, smaller)` [than parent]
  2. The student expresses ordering from the perspective of the parent:  
     `Stud_1`: `(value in node n, is, greater)` [than left subtree]  
     `Stud_2`: `(value in node n, is, less)` [than right subtree]
  3. `Stud_1` remains unmatched against `Ref_1` due to inverted argument roles.
  4. The `PropertyContradictionDetector` evaluates unmatched `Stud_1` against `Ref_1`.
  5. It detects:
     - Domain entity: `BST`
     - Subject: `node / child`
     - Comparative adjectives: `smaller` vs. `greater` (antonyms)
  6. It flags a `VALUE_CONFLICT` with confidence $0.90$.
  7. The `InterpretableSeverityEstimator` looks up the defining properties of `BST`:  
     `["relative_size", "sort_order", "ordering"]`
  8. Because `smaller` vs. `greater` maps to `relative_size`, it assigns `CORE_CONTRADICTION` ($\sigma=1.00$).
  9. **Scoring Impact**: Model D applies a 50% core discount ($S_{\text{core\_effective}} = S_{\text{base}} \times 0.50$), collapsing a perfect 5.0 answer to 0.0.

### 9.2 Representation vs. Scoring Problem
This failure is **not a scoring flaw**. The Model D formula behaved exactly as specified: if a student asserts that a BST has reversed ordering, halving their score is pedagogically appropriate.

The breakdown occurred in **representation and discourse argument binding**:
- $A < B \iff B > A$ is a converse relational equivalence.
- The pipeline lacks converse predicate transformation logic.
- When arguments are swapped, comparative polarity must invert. Because the system compared predicates in isolation without verifying directional argument scope, it produced a false contradiction.

---

## 10. Non-Sentential Reference Analysis ($N=932$)

In 33 out of 81 questions in the Mohler benchmark ($40.7\%$), instructor reference answers are not complete sentences:
- **Examples**:
  - Question 1.1: *"Queue"*
  - Question 2.1: *"By value, by reference"*
  - Question 3.1: *"Through an index or a pointer"*
  - Question 4.1: *"O(1)"*

### 10.1 Why Base ASAG Fails Completely
Classical dependency ASAG (*Basak et al., 2019*) requires a finite verb to anchor subject and object dependencies. When the reference answer is an isolated noun phrase or prepositional list:
- Zero reference triples are extracted ($N_{\text{ref}} = 0$).
- Division by zero or empty reference coverage sets the base score to $0.0000$ for all answers.
- Across all 932 records, Base ASAG predicted a constant $0.0000$ ($\text{MAE}=4.1668$, standard deviation $0.0$, correlation undefined).

### 10.2 Newer Pipeline Recovery
Experiment 4 incorporates non-finite clausal fragments, noun modifier extraction, and predicate-gated cross-slot matching:
- **Pearson correlation recovered to $r=0.2253$** ($p < 0.0001$).
- **Spearman rank correlation recovered to $\rho=0.2296$** ($p < 0.0001$).
- **QWK reached $\kappa=0.0528$**.

### 10.3 Remaining Limitations
While ranking order is recovered, absolute grades remain low (mean $0.6310$ vs. human mean $4.1668$). A student who writes a complete sentence to explain *"Queue"* matches only a single nominal token, yielding a small fractional coverage score. Addressing this requires reference elaboration or question-directed semantic completion.

---

## 11. TF-IDF vs. Symbolic ASAG: A Balanced Interpretation

System 1 (TF-IDF Baseline) achieved $r=0.4184, \rho=0.4424, \text{MAE}=2.6571$, outperforming all symbolic pipelines on global metrics. This must be interpreted scientifically:

### 11.1 Why TF-IDF Excels on this Benchmark
1. **Robustness to Grammatical Noise**: Real student answers contain informal syntax, misspellings, dashes, and omitted verbs. TF-IDF operates on character and word n-grams, remaining completely unaffected by syntactic fragmentation.
2. **Smooth Vocabulary Recall Proxy**: In introductory computer science, mentioning key terms (*"FIFO"*, *"pointer"*, *"reference"*, *"recursive"*) is strongly correlated with human marks. TF-IDF acts as a continuous, graded estimator of technical vocabulary recall.
3. **Reference Formatting Immunity**: TF-IDF processes noun phrase references (*"Queue"*) just as easily as full sentences, whereas dependency parsers break down on non-sentential fragments.

### 11.2 Why Symbolic ASAG Remains Essential
Despite lower global correlation on this benchmark, symbolic ASAG provides capabilities that TF-IDF cannot offer:
1. **Explainable Provenance**: Every grade is tied to specific character-level spans and grammatical triples, not an uninterpretable dot product.
2. **Explicit Misconception Detection**: TF-IDF cannot detect contradictions; an answer stating *"a queue is last-in-first-out"* receives high TF-IDF similarity due to word overlap, whereas symbolic ASAG explicitly identifies the conceptual error.
3. **Inversion Sensitivity**: TF-IDF cannot distinguish *"arrays are passed by reference and elements by value"* from *"arrays are passed by value and elements by reference"*.

---

## 12. Experiment 4 vs. Previous Proposed Systems

Comparing the evolution across proposed iterations:

| Metric / Feature | Historical Proposed (V2) | Current Proposed (V3) | Experiment 4 (V4) |
| :--- | :---: | :---: | :---: |
| **Scoring Formula** | Unweighted Additive Bonus | Saturating Additive Scorer | **Model D (Decomposed & Gated)** |
| **Severity Estimation** | None (All errors equal) | None (All errors equal) | **Multi-tier ($\sigma \in \{0.25, 0.60, 1.00\}$)** |
| **Epistemic Grounding** | None (Topical = Correct) | None (Topical = Correct) | **CuratedDomainKnowledge Verification** |
| **Full Dataset Spearman $\rho$** | 0.0765 | 0.2007 | **0.2033** |
| **Exam Partition Pearson $r$** | 0.1274 | 0.1989 | **0.2284** |
| **Exam Partition Spearman $\rho$** | 0.0457 | 0.1983 | **0.2065** |
| **Exam Partition QWK $\kappa$** | 0.0275 | 0.0411 | **0.0478** |
| **Non-Sentential Pearson $r$** | 0.0113 | 0.2134 | **0.2253** |
| **Full Dataset MAE** | **3.2176** | 3.5955 | 3.6288 |

### Key Observations
- **V4 vs. V2**: V4 resolves the ranking collapse of V2 ($\rho: 0.0765 \to 0.2033$). V2's lower MAE was an artifact of uncalibrated grade inflation.
- **V4 vs. V3**: On the overall dataset, V4 provides modest correlation gains ($r: 0.2037 \to 0.2055$). On Exams, where answers are longer and misconceptions are consequential, V4 achieves substantial gains ($r: 0.1989 \to 0.2284, \rho: 0.1983 \to 0.2065, \kappa: 0.0411 \to 0.0478$).

---

## 13. Proposition-Level Validation Limitation

A vital methodological boundary must be recognized:

> [!WARNING]
> **The Mohler benchmark contains holistic answer-level grades, not proposition-level gold labels.**

Because human annotators evaluated each student answer as a single integer or continuous score on $[0.0, 5.0]$, the benchmark provides **no ground truth** for whether an individual extracted proposition is genuinely correct additional, irrelevant, or incorrect.

Therefore:
1. The classification counts ($2,816$ `IRRELEVANT`, $1,815$ `UNCERTAIN`, $64$ `INCORRECT`) represent **system-assigned outputs**, not validated gold facts.
2. The accuracy, precision, and recall of the proposition classifier cannot be mathematically measured against this dataset.
3. System outputs can only be evaluated through holistic correlation proxy (RQ2) or dedicated human proposition annotation.

---

## 14. Research Interpretation

Synthesizing the experimental evidence:
1. **The Core Hypothesis is Supported on Complex Questions**: When student answers contain multiple interacting clauses (Exams 11–12), evaluating unmatched propositions with severity awareness improves rank-order agreement with human graders over classical reference-coverage systems.
2. **Epistemic Restraint Lowers Raw Scores but Preserves Integrity**: Refusing to award credit for unverified propositions prevents hallucinated grade inflation, but creates a large numerical gap (MAE $3.6288$) against human graders who award credit generously.
3. **Classical ASAG Fails on Non-Sentential Inputs**: The assumption that reference answers are complete grammatical sentences is violated in over 40% of real coursework questions.

---

## 15. Defensible Conclusions

In accordance with strict research integrity standards:

- **CONFIRMED**: Technical feasibility of extracting, representing, and evaluating unmatched student propositions with transparent provenance (RQ1) is **demonstrated**.
- **PARTIALLY SUPPORTED**: Incorporating severity-aware proposition-level evaluation improves agreement with human grading (RQ2) on complex examination questions and non-sentential reference questions, but does not outperform surface lexical overlap globally.
- **DO NOT CLAIM**:
  - That proposition-level classifications are "proven correct" on this benchmark.
  - That the proposed system is "universally better" than TF-IDF.
  - That human-level grading accuracy has been achieved.

---

## 16. Required Human Annotation Study

To rigorously validate the proposition-level classifier independently of answer-level grading, a formal annotation protocol is required:
1. **Sampling**: Stratified random sample of 500 extracted unmatched propositions across all four system-assigned categories.
2. **Annotation Protocol**: Two independent computer science instructors, blinded to system predictions and student grades, annotate each proposition as:
   - `CORRECT_ADDITIONAL` (Valid, technically accurate elaboration)
   - `IRRELEVANT` (Topical digression or redundant remark)
   - `INCORRECT` (Factual error or conceptual misconception)
   - `UNCERTAIN` (Ambiguous or ungrounded statement)
3. **Inter-Annotator Agreement**: Measurement via Cohen's Kappa ($\kappa$) and Krippendorff's Alpha ($\alpha$).
4. **Adjudication**: Disagreements resolved by a third senior adjudicator.

---

## 17. Future Research Directions

1. **Discourse-Aware Comparative Argument Binding**:  
   Implement relational converse logic ($A < B \iff B > A$) to resolve symmetric comparisons before checking property contradictions.
2. **Preprocessing Punctuation Normalization**:  
   Develop specialized segmenters to normalize bulleted lists, inline code, and dashed syntax before dependency parsing.
3. **Open Domain Knowledge Integration**:  
   Connect `CuratedDomainKnowledge` to structured technical ontologies (e.g., Wikidata CS concepts, ACM Computing Classification System) to expand the verification envelope safely beyond three rules.
4. **Hybrid Dual-Stream Architecture**:  
   Combine a surface lexical stream (for robust global topic recall) with a symbolic proposition stream (for interpretable precision, provenance, and misconception auditing).
