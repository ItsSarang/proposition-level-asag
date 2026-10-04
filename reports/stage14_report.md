# Stage 14 Report: Proposed ASAG Scoring Mechanism

**Implementation Date:** Stage 14 of the ASAG Research Pipeline  
**Repository:** proposition-level-asag  
**Research Stage:** STAGE 14 — Proposed Grading Mechanism  

---

## 1. Research Hypothesis & Context

The overarching research question of this project is:
> *"Can an interpretable proposition-level extension of a classical semantic/dependency-based ASAG system evaluate unmatched student information as correct additional, irrelevant, or incorrect information, and does incorporating this evaluation improve agreement with human grading?"*

> **IMPORTANT RESEARCH INTEGRITY PRINCIPLE**:
> The proposed grading mechanism is a **RESEARCH HYPOTHESIS**.
> We do NOT claim that this proposed scoring mechanism improves grading performance, achieves superior human agreement, or outperforms Base ASAG or the baseline until actual empirical experiments (Stage 15) demonstrate it.
> The weights, penalties, and adjustment formulas implemented in Stage 14 are **implementation and experimental parameters**; they have **not** been optimized, tuned, or validated against human grades.

In classical ASAG (e.g. Basak et al., 2019), grades reflect **reference proposition coverage**:
- Does the student answer entail the reference answer's dependency triples?
- If the student writes additional content not found in the reference answer, it is discarded without affecting the score (`score_effect = 0.0`).

Stage 14 operationalizes the proposed extension (System 3) by introducing a **transparent, configurable scoring layer** that modulates the grade based on Stage 13 proposition-level additional-information classifications, while strictly preserving the Base ASAG score as an unperturbed control condition.

---

## 2. Stage 14 Objectives

1. **Independent Proposed Scoring Component**: Implement `ProposedScorer` in `proposed_asag/scoring/` without altering or monkey-patching Base ASAG scoring logic (`base_asag/scoring/base_scorer.py`).
2. **Preservation of the Control Condition**: Maintain `base_score` exactly as calculated by Stage 9/10 Base ASAG.
3. **Normalized Internal Bounding**: Bound all internal scores and adjustments strictly in $[0.0, 1.0]$.
4. **Configurable Adjustment Parameters**:
   - `correct_additional_weight`: Positive bonus for `CORRECT_ADDITIONAL` propositions (default $0.10$).
   - `incorrect_additional_penalty`: Deduction magnitude for `INCORRECT` propositions (default $0.20$).
   - `irrelevant_adjustment`: Neutral adjustment for `IRRELEVANT` propositions (default $0.0$).
   - `uncertain_adjustment`: Neutral fallback adjustment for `UNCERTAIN` propositions (default $0.0$).
5. **Dual Modulation Modes**:
   - *Uniform Mode* (default): Fixed discrete step per classified proposition.
   - *Evidence-Weighted Mode* (optional): Adjustment scaled by Stage 13 classification confidence.
6. **Multi-Proposition Aggregation & Bounds Clipping**: Aggregate multiple unmatched propositions additively and clip the final proposed score to $[0.0, 1.0]$ with explicit flags (`is_clipped_upper`, `is_clipped_lower`).
7. **Complete Provenance**: Record an itemized `PropositionAdjustmentRecord` for every proposition detailing text, classification, confidence, applied delta, and reason.
8. **Pure JSON Serialization**: Provide complete `.to_dict()` and `.to_json()` methods.

---

## 3. Scope & Non-Goals

| Component | In Stage 14 Scope? | Details / Rationale |
|---|---|---|
| Proposed Scoring Calculation | **YES** | Additive modulation: $\text{proposed\_score} = \text{clip}(\text{base\_score} + \text{adjustment}, 0, 1)$. |
| Evidence-Weighted Adjustments | **YES** | Optional confidence-weighted delta calculation. |
| Provenance Tracking | **YES** | Itemized `PropositionAdjustmentRecord` for every evaluated proposition. |
| Base ASAG Preservation | **YES** | `base_score` strictly unchanged; Base ASAG code untouched. |
| Modification of Base ASAG | **NO** | `base_asag/scoring/base_scorer.py` remains 100% intact. |
| Parameter Optimization | **NO** | Weights are experimental parameters, NOT tuned to fit test data. |
| Machine Learning / LLMs | **NO** | No regression models, neural networks, embeddings, or LLM scoring. |
| Claims of Human Superiority | **NO** | No claims that proposed scoring improves human correlation (tested in Stage 15). |

---

## 4. Methodological Formulation

### Mathematical Scoring Formulation

Let $S_{\text{base}} \in [0.0, 1.0]$ denote the Base ASAG normalized score from Stage 9/10, representing reference proposition coverage:

$$S_{\text{base}} = \frac{\sum_{r \in R} w_r \cdot c_r}{\sum_{r \in R} w_r}$$

Let $U = \{u_1, u_2, \dots, u_m\}$ denote the set of unmatched student propositions classified in Stage 13, where each $u_i$ has classification category $C_i \in \{\text{CORRECT\_ADDITIONAL}, \text{IRRELEVANT}, \text{INCORRECT}, \text{UNCERTAIN}\}$ and confidence $\gamma_i \in [0.0, 1.0]$.

For each proposition $u_i$, the individual score adjustment $\Delta_i$ is computed as:

$$\Delta_i = \begin{cases}
+ w_{\text{correct}} \cdot f(\gamma_i), & \text{if } C_i = \text{CORRECT\_ADDITIONAL} \\
- w_{\text{incorrect}} \cdot f(\gamma_i), & \text{if } C_i = \text{INCORRECT} \\
+ w_{\text{irrelevant}} \cdot f(\gamma_i), & \text{if } C_i = \text{IRRELEVANT} \quad (w_{\text{irrelevant}} = 0.0) \\
+ w_{\text{uncertain}} \cdot f(\gamma_i), & \text{if } C_i = \text{UNCERTAIN} \quad (w_{\text{uncertain}} = 0.0)
\end{cases}$$

where the evidence-weighting scaling function $f(\gamma_i)$ is:

$$f(\gamma_i) = \begin{cases}
\gamma_i, & \text{if } \text{evidence\_weighted} = \text{True} \\
1.0, & \text{if } \text{evidence\_weighted} = \text{False (default)}
\end{cases}$$

The aggregated positive and negative adjustments are:

$$\Delta_{\text{pos}} = \min\left( \sum_{i: \Delta_i > 0} \Delta_i, \; \text{cap}_{\text{pos}} \right)$$

$$\Delta_{\text{neg}} = \min\left( \sum_{i: \Delta_i < 0} |\Delta_i|, \; \text{cap}_{\text{neg}} \right)$$

The net adjustment and raw proposed score are:

$$\Delta_{\text{net}} = \Delta_{\text{pos}} - \Delta_{\text{neg}}$$

$$S_{\text{raw}} = S_{\text{base}} + \Delta_{\text{net}}$$

The final proposed score is clipped to valid probability bounds:

$$S_{\text{proposed}} = \max(0.0, \min(1.0, S_{\text{raw}}))$$

Explicit clipping diagnostics record whether truncation occurred:
- $\text{is\_clipped\_upper} = (S_{\text{raw}} > 1.0)$
- $\text{is\_clipped\_lower} = (S_{\text{raw}} < 0.0)$

---

## 5. Architecture & Data Structures

The Stage 14 module is located in `proposed_asag/scoring/`:
- `proposed_asag/scoring/proposed_scorer.py`: Core scoring classes.
- `proposed_asag/scoring/__init__.py`: Package export interface.

```
Stage 10: BaseASAGPipelineResult (base_score)
      ↓
Stage 13: DocumentClassificationResult (unmatched_classifications)
      ↓
Stage 14: ProposedScorer
      ├── score_propositions(base_score, classifications)
      └── ProposedScoreResult
            ├── base_score (unperturbed control)
            ├── proposed_score (clipped [0.0, 1.0])
            ├── raw_proposed_score (unclipped)
            ├── positive_adjustment, negative_adjustment, net_adjustment
            ├── is_clipped_upper, is_clipped_lower
            └── adjustment_details: List[PropositionAdjustmentRecord]
```

### Core Data Models

#### 1. `PropositionAdjustmentRecord`
Encapsulates individual proposition provenance:
- `proposition_id`: Unique identifier (e.g. `"stu_prop_1"`).
- `proposition_index`: Zero-based proposition index.
- `text`: Proposition surface span.
- `classification`: Stage 13 category.
- `confidence`: Confidence score in $[0.0, 1.0]$.
- `raw_parameter_weight`: Configured category parameter ($w_{\text{correct}}$ or $w_{\text{incorrect}}$).
- `evidence_weighted`: Boolean indicating whether confidence scaling was applied.
- `applied_adjustment`: Signed delta ($\Delta_i$).
- `reason`: Explainable human-readable justification.
- `details`: Diagnostic metadata.

#### 2. `ProposedScoreResult`
Complete container for the proposed evaluation:
- `base_score`: Base ASAG normalized score in $[0.0, 1.0]$.
- `proposed_score`: Clipped proposed score in $[0.0, 1.0]$.
- `raw_proposed_score`: Unclipped continuous score.
- `correct_additional_count`, `irrelevant_count`, `incorrect_count`, `uncertain_count`.
- `positive_adjustment`, `negative_adjustment`, `net_adjustment`.
- `is_clipped_upper`, `is_clipped_lower`.
- `adjustment_details`: List of `PropositionAdjustmentRecord`.
- `config`: Dictionary of scoring configuration parameters.
- `summary`: High-level summary metrics.
- `.scale_base_score(max_points)` and `.scale_proposed_score(max_points)` methods.
- `.to_dict()` and `.to_json()` serialization methods.

---

## 6. Demonstration Case Walkthroughs

We evaluate `ProposedScorer` across the canonical demonstration cases:

### Case 1: Student A (Paraphrase)
- **Student**: *"A primary key uniquely identifies every row in a table."*
- **Base Score**: $0.50$ (partial slot match)
- **Unmatched Propositions**: $0$
- **Proposed Evaluation**:
  - Positive adjustment: $0.00$, Negative adjustment: $0.00$, Net: $0.00$
  - **Proposed Score**: $0.5000$ (Scaled 5pt: $2.50$)
  - Clipped: Upper=False, Lower=False

### Case 2: Student B (Correct Additional Information)
- **Student**: *"A primary key uniquely identifies each record in a table and cannot contain NULL values."*
- **Base Score**: $1.00$ (full reference coverage)
- **Unmatched Propositions**: 1 (`cannot contain NULL values` $\rightarrow$ `CORRECT_ADDITIONAL`, conf=$0.75$)
- **Proposed Evaluation (Uniform Mode)**:
  - Positive adjustment: $+0.10$, Negative adjustment: $0.00$, Net: $+0.10$
  - Raw score: $1.1000$
  - **Proposed Score**: $1.0000$ (Scaled 5pt: $5.00$)
  - Clipped: Upper=**True**, Lower=False
  - Detail: `[CORRECT_ADDITIONAL] +0.1000 -> Bonus for correct additional proposition: +0.1000.`
- **Proposed Evaluation (Evidence-Weighted Mode)**:
  - Positive adjustment: $+0.10 \times 0.75 = +0.0750$
  - Raw score: $1.0750 \rightarrow$ Clipped to $1.0000$ (Upper=True)
- *Note on Partial Answers*: If Student B had a base score of $0.50$, the proposed score would rise to $0.60$ (or $0.575$ weighted), demonstrating the reward mechanism.

### Case 3: Student C (Incorrect Additional Information / Misconception)
- **Student**: *"A primary key uniquely identifies each record in a table and can contain duplicate values."*
- **Base Score**: $1.00$ (Base ASAG ignores the second clause)
- **Unmatched Propositions**: 1 (`can contain duplicate values` $\rightarrow$ `INCORRECT`, conf=$0.80$)
- **Proposed Evaluation (Uniform Mode)**:
  - Positive adjustment: $0.00$, Negative adjustment: $0.20$, Net: $-0.20$
  - Raw score: $0.8000$
  - **Proposed Score**: $0.8000$ (Scaled 5pt: $4.00$)
  - Clipped: Upper=False, Lower=False
  - Detail: `[INCORRECT] -0.2000 -> Deduction for incorrect/misconception proposition: -0.2000.`
- **Proposed Evaluation (Evidence-Weighted Mode)**:
  - Negative adjustment: $0.20 \times 0.80 = 0.1600$, Net: $-0.1600$
  - **Proposed Score**: $0.8400$ (Scaled 5pt: $4.20$)

### Case 4: Student D (Irrelevant Additional Information)
- **Student**: *"A primary key uniquely identifies each record in a table. SQL was developed in the 1970s."*
- **Base Score**: $1.00$
- **Unmatched Propositions**: 1 (`SQL was developed` $\rightarrow$ `IRRELEVANT`, conf=$1.0$)
- **Proposed Evaluation**:
  - Positive adjustment: $0.00$, Negative adjustment: $0.00$, Net: $0.00$
  - **Proposed Score**: $1.0000$ (Scaled 5pt: $5.00$)
  - Clipped: Upper=False, Lower=False
  - Detail: `[IRRELEVANT] +0.0000 -> Irrelevant proposition: neutral adjustment (+0.0000).`

### Summary Comparison Across the 3 Systems

| Student Answer | System 1 (TF-IDF Cosine) | System 2 (Base ASAG) | System 3 (Proposed ASAG, 5pt Scale) |
|---|---|---|---|
| **Student A** (Paraphrase) | 0.8478 | 2.50 / 5.00 | **2.50 / 5.00** (Net: 0.0) |
| **Student B** (Correct Addition) | 0.8920 | 5.00 / 5.00 | **5.00 / 5.00** (Net: +0.10, upper-clipped) |
| **Student C** (Incorrect Addition) | 0.8710 | 5.00 / 5.00 | **4.00 / 5.00** (Net: -0.20 deduction) |
| **Student D** (Irrelevant Addition) | 0.7650 | 5.00 / 5.00 | **5.00 / 5.00** (Net: 0.0 neutral) |

Base ASAG is unable to differentiate between Student B, Student C, and Student D (assigning $5.00 / 5.00$ to all three). Proposed ASAG successfully penalizes Student C for introducing a factual misconception while maintaining neutral treatment for Student D and rewarding Student B.

---

## 7. Preservation of Research Invariants

1. **Base ASAG Control Invariance**:
   - `score_res.base_score == pipe_res.normalized_score` across all tests.
   - `base_asag/scoring/base_scorer.py` remains completely untouched.
2. **Probability Bound Guarantee**:
   - For all inputs $S_{\text{base}} \in [0, 1]$ and all adjustments, $S_{\text{proposed}} \in [0.0, 1.0]$.
3. **No External Hallucinations**:
   - Scoring relies strictly on Stage 13 classifications and configuration parameters.
   - No LLMs, embeddings, sentence-transformers, or hardcoded rules are involved.

---

## 8. Test Suite & Verification Results

A dedicated test suite was implemented in `tests/test_stage14_scoring.py`, containing 17 comprehensive unit and integration tests:

| Test Name | Purpose | Result |
|---|---|---|
| `test_no_unmatched_propositions` | Verifies zero net adjustment when no unmatched propositions exist | **PASSED** |
| `test_one_correct_additional` | Verifies score increase from single `CORRECT_ADDITIONAL` | **PASSED** |
| `test_one_irrelevant_additional` | Verifies neutral 0.0 adjustment from single `IRRELEVANT` | **PASSED** |
| `test_one_incorrect_additional` | Verifies score deduction from single `INCORRECT` | **PASSED** |
| `test_multiple_classifications` | Verifies additive combination of mixed propositions | **PASSED** |
| `test_score_upper_bound_clipping` | Verifies raw score $> 1.0$ is clipped to 1.0 with `is_clipped_upper=True` | **PASSED** |
| `test_score_lower_bound_clipping` | Verifies raw score $< 0.0$ is clipped to 0.0 with `is_clipped_lower=True` | **PASSED** |
| `test_evidence_weighted_mode` | Verifies confidence scaling in evidence-weighted mode | **PASSED** |
| `test_base_score_invariance` | Verifies exact equivalence between Base ASAG score and Proposed result | **PASSED** |
| `test_configurable_weights_and_penalties` | Verifies parameter overrides (custom weights, penalties, neutral values) | **PASSED** |
| `test_optional_adjustment_caps` | Verifies positive and negative adjustment caps | **PASSED** |
| `test_scaled_scores` | Verifies 5-point and 100-point score scaling methods | **PASSED** |
| `test_json_serializability` | Tests `.to_json()` and round-trip `json.loads()` validation | **PASSED** |
| `test_deterministic_scoring` | Asserts identical output across consecutive runs | **PASSED** |
| `test_provenance_and_adjustment_records` | Verifies diagnostic rationale in itemized adjustment records | **PASSED** |
| `test_end_to_end_from_pipeline` | Tests execution directly from `BaseASAGPipelineResult` | **PASSED** |
| `test_invalid_parameters` | Asserts `ValueError` on negative weights or invalid base scores | **PASSED** |

### Test Execution Summary
- **Stage 14 Suite**: 17 passed in 3.55s
- **Full Repository Suite**: 266 passed in 8.50s (0 failures, 0 regressions across Stages 1–14)

---

## 9. Sample JSON Output

```json
{
  "base_score": 1.0,
  "proposed_score": 0.8,
  "raw_proposed_score": 0.8,
  "correct_additional_count": 0,
  "irrelevant_count": 0,
  "incorrect_count": 1,
  "uncertain_count": 0,
  "positive_adjustment": 0.0,
  "negative_adjustment": 0.2,
  "net_adjustment": -0.2,
  "is_clipped_upper": false,
  "is_clipped_lower": false,
  "adjustment_details": [
    {
      "proposition_id": "stu_prop_1",
      "proposition_index": 1,
      "text": "can contain duplicate values",
      "classification": "INCORRECT",
      "confidence": 0.8,
      "raw_parameter_weight": 0.2,
      "evidence_weighted": false,
      "applied_adjustment": -0.2,
      "reason": "Deduction for incorrect/misconception proposition: -0.2000.",
      "details": {
        "relevance_score": 0.8667,
        "contradiction_type": "MODIFIER_CONFLICT"
      }
    }
  ],
  "config": {
    "correct_additional_weight": 0.1,
    "incorrect_additional_penalty": 0.2,
    "irrelevant_adjustment": 0.0,
    "uncertain_adjustment": 0.0,
    "evidence_weighted": false,
    "max_positive_adjustment": null,
    "max_negative_adjustment": null
  },
  "summary": {
    "base_score": 1.0,
    "proposed_score": 0.8,
    "net_adjustment": -0.2,
    "correct_additional_count": 0,
    "irrelevant_count": 0,
    "incorrect_count": 1,
    "uncertain_count": 0,
    "total_evaluated_propositions": 1,
    "is_clipped_upper": false,
    "is_clipped_lower": false
  }
}
```

---

## 10. Assumptions & Methodological Decisions

1. **Experimental Parameter Nature**:
   The default parameters ($w_{\text{correct}} = 0.10$, $w_{\text{incorrect}} = 0.20$) are heuristic baseline values intended for demonstration and comparative analysis. They have not been fit to an empirical dataset.
2. **Additive Adjustment Structure**:
   Adjustments operate additively on the Base ASAG score. An additive formulation is intuitive, transparent, and allows human educators to understand exactly how much credit or penalty was attributed to each sentence or clause.
3. **Dual Weighting Modes**:
   Both uniform step adjustment and confidence-weighted adjustment are supported. We make no empirical claims regarding which mode is superior; this will be evaluated experimentally in Stage 15.

---

## 11. Limitations & Scientific Nuance

1. **Uncalibrated Parameters**:
   The default weights ($0.10$ bonus, $0.20$ penalty) are illustrative. In practical educational settings, the appropriate penalty for a misconception or reward for extra information depends on question type, rubrics, and instructor grading policies.
2. **Upper Bound Truncation Effect**:
   When a student already attains a perfect Base ASAG score ($S_{\text{base}} = 1.0$), correct additional information cannot increase the score further due to normalization clipping ($S_{\text{proposed}} = 1.0$). The bonus is reflected in `raw_proposed_score` ($1.10$) and `is_clipped_upper = True`, but the bounded score remains $1.0$.

---

## 12. Readiness for Stage 15

With Stage 14 complete, the three systems are fully implemented:
1. **System 1**: TF-IDF + Cosine Similarity Baseline (Stage 1)
2. **System 2**: Base ASAG Pipeline (Stages 3–10)
3. **System 3**: Proposed ASAG Pipeline with Proposition-Level Additional Information Classification and Scoring (Stages 11–14)

The pipeline is now ready for **STAGE 15 — Evaluation Against Human Grades**, where these three systems will be experimentally evaluated and compared on public benchmark datasets.
