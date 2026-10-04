# Additional-Information Scoring Investigation Report (Phase 4A Development)

**Document Identity**: `evaluation/scoring_development/additional_information_scoring_report.md`  
**Phase**: PHASE 4A — CONTROLLED ADDITIONAL-INFORMATION SCORING STUDY  
**Target Component**: Proposition-Level Grade Aggregation & Contradiction Penalty Modeling  
**Evaluation Scope**: Synthetic / Controlled Development Cases & Monotonicity Sanity Properties (Zero Mohler Benchmark Evaluation)  
**Test Suite Status**: 10 passed in `scoring_sanity_tests.py`, 468 total suite passing, 0 failures, 0 regressions  

---

## 1. Research Motivation

The central research hypothesis of this investigation states:
> *"Can an interpretable proposition-level extension of a classical semantic/dependency-based ASAG system evaluate unmatched student information as correct additional, irrelevant, or incorrect information, and does incorporating this evaluation improve agreement with human grading?"*

While the proposition classification pipeline (Phases 1–9) successfully categorizes unmatched propositions into `CORRECT_ADDITIONAL`, `IRRELEVANT`, `INCORRECT`, and `UNCERTAIN` with auditable evidence, the downstream question of **how these evaluations should affect the final numerical grade** remains an open research problem.

In particular, qualitative error analysis revealed an important calibration asymmetry in the existing production scorer:
- **Reference**: *"A primary key uniquely identifies each record in a table."*
- **Student**: *"A primary key uniquely identifies each record in a table and can contain duplicate values."*
- **Observed Behavior**: The classifier correctly identifies that *"can contain duplicate values"* contradicts the reference defining property (`VALUE_CONFLICT` on `uniqueness`, evidence strength $0.90$). However, under the current production scorer, the final grade remains **$4.33 / 5.0$** (an unweighted $0.67$-point deduction).

An answer asserting that a primary key can contain duplicate values exhibits a fundamental misconception that invalidates the core defining concept just quoted. Simply increasing $M_{\text{neg}}$ would be arbitrary parameter tuning. The purpose of this Phase 4A investigation is to systematically design, implement, and compare candidate scoring mechanisms on controlled cases and mathematical sanity properties before altering production scoring.

---

## 2. Current Scorer Analysis

The current production scoring engine (`BoundedScorer` in `SATURATING` mode, located in `proposed_asag/scoring/bounded_scorer.py`) operates as an additive modulation layer over the Base ASAG score:

### Mathematical Formulation
$$S_{\text{final}} = \text{clip}\left(S_{\text{base}} + \Delta_{\text{pos}} - \Delta_{\text{neg}}, 0.0, 1.0\right)$$

Where:
1. **Base Score ($S_{\text{base}}$)**:
   Measures reference proposition coverage via directional propositional entailment:
   $$S_{\text{base}} = \frac{1}{N_{\text{ref}}} \sum_{j=1}^{N_{\text{ref}}} w(\text{status}_j) \cdot \text{triple\_score}_j$$
   with $w(\text{ENTAILS}) = 1.0$, $w(\text{UNCERTAIN}) = 0.5$, $w(\text{CONTRADICTS}) = 0.0$, and $w(\text{UNMATCHED}) = 0.0$.
2. **Positive Adjustment ($\Delta_{\text{pos}}$)**:
   Applies a non-linear diminishing returns saturation function to the count of `CORRECT_ADDITIONAL` propositions ($n_{\text{correct}}$):
   $$\Delta_{\text{pos}} = M_{\text{pos}} \cdot \left(\frac{r \cdot n_{\text{correct}}}{1.0 + r \cdot n_{\text{correct}}}\right)$$
   Frozen production parameters: $M_{\text{pos}} = 0.30, r = 0.50$.
3. **Negative Adjustment ($\Delta_{\text{neg}}$)**:
   Applies an identical saturating formula to the count of `INCORRECT` propositions ($n_{\text{incorrect}}$):
   $$\Delta_{\text{neg}} = M_{\text{neg}} \cdot \left(\frac{0.50 \cdot n_{\text{incorrect}}}{1.0 + 0.50 \cdot n_{\text{incorrect}}}\right)$$
   Frozen production parameter: $M_{\text{neg}} = 0.40$.
4. **Neutral Categories**:
   - `IRRELEVANT`: $\Delta = 0.0$ (no bonus, no penalty).
   - `UNCERTAIN`: $\Delta = 0.0$ (held neutral to enforce $NOT\_SUPPORTED \ne CONTRADICTED$).
5. **Clipping**:
   Enforces strict range bounds in $[0.0, 1.0]$. The scaled score is $S_{\text{scaled}} = S_{\text{final}} \times 5.0$.

### Why Model A Fails to Penalize Serious Misconceptions
Under Model A, the penalty depends **exclusively on the count** ($n_{\text{incorrect}}$), regardless of whether the error is a minor peripheral detail or a fatal contradiction of the core concept.
For $n_{\text{incorrect}} = 1$:
$$\Delta_{\text{neg}} = 0.40 \cdot \frac{0.50 \cdot 1}{1.0 + 0.50 \cdot 1} = 0.40 \cdot \frac{0.50}{1.50} = 0.40 \cdot \frac{1}{3} = 0.1333$$
When $S_{\text{base}} = 1.000$, the final score is:
$$S_{\text{final}} = 1.000 - 0.1333 = 0.8667 \implies 4.3333 / 5.0$$
Because the saturating curve asymptotes at $M_{\text{neg}} = 0.40$ and starts at $\frac{1}{3}$ of that value for the first error, an answer with a perfect core score can never be reduced below $1.0 - 0.40 = 0.60$ ($3.0 / 5.0$), no matter how catastrophic the contradiction.

---

## 3. Controlled Development Cases

To evaluate candidate models without data leakage or benchmark overfitting, we constructed 8 explicitly labeled controlled development cases using the Primary Key domain:

- **Question**: *"What is the purpose of a primary key?"*
- **Reference**: *"A primary key uniquely identifies each record in a table."*

| Case ID | Case Type | Student Answer Text | Rationale & Expected Behavior |
| :--- | :--- | :--- | :--- |
| **Case A** | `CORRECT_CORE_ONLY` | *"A primary key uniquely identifies each record in a table."* | Exact core coverage; no unmatched additions; baseline control ($S=5.00$). |
| **Case B** | `CORRECT_CORE_PLUS_CORRECT_ADD` | *"A primary key uniquely identifies each record in a table and cannot contain NULL values."* | Core coverage + verified CS domain property (`PK_NOT_NULL`); eligible for bonus capped at max ($S=5.00$). |
| **Case C** | `CORRECT_CORE_PLUS_IRRELEVANT_ADD` | *"A primary key uniquely identifies each record in a table. SQL was developed in the 1970s."* | Core coverage + off-topic historical fact; zero adjustment; grade remains equal to core ($S=5.00$). |
| **Case D** | `CORRECT_CORE_PLUS_ONE_INCORRECT` | *"A primary key uniquely identifies each record in a table and can contain duplicate values."* | Core coverage + direct contradiction of defining property `uniqueness`; must produce substantial deduction. |
| **Case E** | `CORRECT_CORE_PLUS_MULTI_INCORRECT` | *"A primary key uniquely identifies each record in a table and can contain duplicate values. The key also contains redundant rows."* | Core coverage + two distinct contradictions of uniqueness; must score lower than or equal to Case D. |
| **Case F1** | `PARTIAL_CORE_ALONE` | *"A primary key determines each record in a table."* | Approximate/incomplete core coverage ($S_{\text{base}} \approx 4.17$); no additions. |
| **Case F2** | `PARTIAL_CORE_PLUS_INCORRECT` | *"A primary key determines each record in a table. It can contain duplicate values."* | Incomplete core + contradiction; must score lower than F1 and lower than or equal to Case D. |
| **Case G** | `CORRECT_CORE_PLUS_UNCERTAIN_ADD` | *"A primary key uniquely identifies each record in a table and is usually indexed using a B-tree."* | Core coverage + unverified topical proposition; held neutral with 0.0 bonus ($S=5.00$). |

All 8 cases are stored with full linguistic and diagnostic metadata in:
`evaluation/scoring_development/controlled_additional_scoring_cases.csv`.

---

## 4. Desired Qualitative Grading Constraints

Before evaluating candidate formulations, we established strict qualitative ordering constraints that any pedagogically sound ASAG engine must satisfy:

1. **Ordering Constraint 1 (Core Equivalence)**:
   $$S(\text{Case A}) \approx S(\text{Case B}) \approx S(\text{Case C}) \approx S(\text{Case G})$$
   A student with a fully correct core should not be penalized for harmless off-topic statements or unverified topical elaborations, nor should correct additions exceed the maximum scale ($5.0/5.0$).
2. **Ordering Constraint 2 (Strict Contradiction Penalty)**:
   $$S(\text{Case A}) > S(\text{Case D})$$
   An answer containing a direct contradiction of a defining property must score strictly lower than the clean core answer.
3. **Ordering Constraint 3 (Cumulative Deficit Monotonicity)**:
   $$S(\text{Case D}) \ge S(\text{Case E})$$
   Adding multiple serious misconceptions must never increase the grade and should reflect cumulative deficit.
4. **Ordering Constraint 4 (Partial Core Ordering)**:
   $$S(\text{Case F1}) > S(\text{Case F2})$$
   When the core answer is partial, adding an incorrect statement must decrease the grade.
5. **Ordering Constraint 5 (Deficit Consistency)**:
   $$S(\text{Case F2}) \le S(\text{Case D})$$
   A student who has both an incomplete core AND a fatal contradiction cannot score higher than a student who at least articulated the correct core.

---

## 5. Candidate Scoring Models

Four isolated scoring models were implemented in `evaluation/scoring_development/experimental_scoring_models.py`:

### Model A: Current Additive Saturating Scorer (Baseline Control)
- **Concept**: Additive shifts bounded by horizontal asymptotes:
  $$S_{\text{final}} = \text{clip}\left(S_{\text{base}} + \Delta_{\text{pos}} - \Delta_{\text{neg}}, 0.0, 1.0\right)$$
  $$\Delta_{\text{pos}} = 0.30 \cdot \frac{0.50 \cdot n_{\text{correct}}}{1 + 0.50 \cdot n_{\text{correct}}}, \quad \Delta_{\text{neg}} = 0.40 \cdot \frac{0.50 \cdot n_{\text{incorrect}}}{1 + 0.50 \cdot n_{\text{incorrect}}}$$

### Model B: Proportional Penalty Scorer (Multiplicative Degradation)
- **Concept**: Incorrect additional information degrades the earned credit multiplicatively rather than subtracting a flat quantity. Misconceptions reduce the validity of the stated answer:
  $$S_{\text{final}} = \text{clip}\left((S_{\text{base}} + \Delta_{\text{pos}}) \cdot \prod_{i=1}^{n_{\text{incorrect}}} (1.0 - p_i), 0.0, 1.0\right)$$
  where $p_i = p_{\text{base}} \cdot \sigma_i$ ($p_{\text{base}} = 0.35$, $\sigma_i$ is severity).

### Model C: Evidence-Weighted Bounded Severity Penalty Scorer
- **Concept**: Additive deductions scale directly with contradiction evidence strength ($E_i$) and semantic severity ($\sigma_i$):
  $$d_i = \sigma_i \cdot E_i \cdot w_{\text{pen}}$$
  $$\Delta_{\text{neg}} = M_{\text{neg\_max}} \cdot \left(\frac{\sum_i d_i}{1.0 + \sum_i d_i}\right)$$
  $$S_{\text{final}} = \text{clip}\left(S_{\text{base}} + \Delta_{\text{pos}} - \Delta_{\text{neg}}, 0.0, 1.0\right)$$
  Parameters: $w_{\text{pen}} = 0.40, M_{\text{neg\_max}} = 0.70$.

### Model D: Core / Additional Decomposition with Gated Compensation
- **Concept**: Explicitly partitions the score into Core Coverage and Additional Evaluation:
  1. **Core Invalidation Gate**: If an incorrect addition directly contradicts a core defining property of the entity ($\sigma \ge 0.90$, e.g. `uniqueness` on primary key), it invalidates core understanding:
     $$S_{\text{core\_eff}} = S_{\text{base}} \cdot (1.0 - \text{discount}_{\text{core}})$$
     with $\text{discount}_{\text{core}} = 0.50$.
  2. **Minor Deductions**: Peripheral incorrect additions apply mild additive deductions ($w_{\text{minor}} = 0.20$).
  3. **Gated Compensation**: Correct additional bonuses are capped by effective core understanding ($\min(\text{bonus}, S_{\text{core\_eff}} \cdot 0.50)$), preventing peripheral bonuses from compensating for absent core concepts.
  $$S_{\text{final}} = \text{clip}\left(S_{\text{core\_eff}} + \Delta_{\text{pos}} - \Delta_{\text{minor}}, 0.0, 1.0\right)$$

---

## 6. Parameter Exploration Grid

To adhere strictly to Section 6, parameters were defined prior to execution without referencing the Mohler benchmark. A small, justified 4-point sensitivity grid was evaluated across Cases D and E:

| Model | Parameter Explored | Grid Values | Case D Grade (/5) | Case E Grade (/5) | Observation |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **Model A** | $M_{\text{neg}}$ (Max Negative Penalty) | 0.20<br>0.30<br>0.40<br>0.50 | 4.67<br>4.50<br>4.33<br>4.17 | 4.50<br>4.25<br>4.00<br>3.75 | Even at $M_{\text{neg}}=0.50$, single-error penalty is capped at $\frac{1}{3} \times 0.50 = 0.1667$, leaving the grade above 4.15/5.0. |
| **Model B** | $p_{\text{incorrect}}$ (Multiplicative Rate) | 0.20<br>0.30<br>0.35<br>0.50 | 4.00<br>3.50<br>3.25<br>2.50 | 3.20<br>2.45<br>2.11<br>1.25 | Smooth, proportional response. Scales naturally with compounding errors ($p^2$). |
| **Model C** | $w_{\text{pen}}$ (Base Penalty Weight) | 0.20<br>0.30<br>0.40<br>0.50 | 4.47<br>4.26<br>4.07<br>3.91 | 4.07<br>3.77<br>3.53<br>3.34 | Evidence strength modulates deduction, but additive saturation prevents deep single-error deductions. |
| **Model D** | $\text{discount}_{\text{core}}$ (Invalidation Discount) | 0.30<br>0.40<br>0.50<br>0.60 | 3.50<br>3.00<br>2.50<br>2.00 | 3.50<br>3.00<br>2.50<br>2.00 | Discretely drops credit when a defining misconception is affirmed. Multiple identical violations do not double-penalize the same core concept. |

---

## 7. Controlled Experimental Results

The four candidate models were evaluated on the 8 controlled cases. Output grades scaled to $[0.0, 5.0]$:

| Case ID | Case Description | Base ASAG | Model A (Additive) | Model B (Proportional) | Model C (Evidence-Wt) | Model D (Decomposition) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Case A** | Correct core only | 5.00 | 5.00 | 5.00 | 5.00 | 5.00 |
| **Case B** | Core + correct additional (`PK_NOT_NULL`) | 5.00 | 5.00 (clip) | 5.00 (clip) | 5.00 (clip) | 5.00 (clip) |
| **Case C** | Core + irrelevant additional (`SQL developed 1970s`) | 5.00 | 5.00 | 5.00 | 5.00 | 5.00 |
| **Case D** | Core + one incorrect additional (`can duplicate`) | 5.00 | **4.33** | **3.25** | **4.07** | **2.50** |
| **Case E** | Core + two incorrect additions (`duplicate` + `redundant`) | 5.00 | **4.00** | **2.11** | **3.53** | **2.50** |
| **Case F1** | Partial core alone (`determines records`) | 4.17 | 4.17 | 4.17 | 4.17 | 4.17 |
| **Case F2** | Partial core + incorrect additional | 4.17 | **3.50** | **2.71** | **3.24** | **2.08** |
| **Case G** | Core + uncertain additional (`indexed with B-tree`) | 5.00 | 5.00 | 5.00 | 5.00 | 5.00 |

Full results are recorded in `evaluation/scoring_development/scoring_model_comparison.csv`.

---

## 8. Monotonicity and Sanity Property Verification

All candidate models were formally verified against the 10 predefined mathematical and qualitative properties in `evaluation/scoring_development/scoring_sanity_tests.py`:

```
============================= test session starts ==============================
rootdir: /Users/sarang/Dev/College/MIT_WPU/Projects/AIES/proposition-level-asag
collected 10 items

evaluation/scoring_development/scoring_sanity_tests.py::test_property_1_correct_additional_non_decreasing PASSED [ 10%]
evaluation/scoring_development/scoring_sanity_tests.py::test_property_2_irrelevant_information_neutral PASSED [ 20%]
evaluation/scoring_development/scoring_sanity_tests.py::test_property_3_incorrect_information_non_increasing PASSED [ 30%]
evaluation/scoring_development/scoring_sanity_tests.py::test_property_4_multiple_incorrect_non_increasing PASSED [ 40%]
evaluation/scoring_development/scoring_sanity_tests.py::test_property_5_serious_contradiction_produces_strict_deduction PASSED [ 50%]
evaluation/scoring_development/scoring_sanity_tests.py::test_property_6_incorrect_cannot_compensate_partial_core PASSED [ 60%]
evaluation/scoring_development/scoring_sanity_tests.py::test_property_7_uncertain_no_positive_bonus PASSED [ 70%]
evaluation/scoring_development/scoring_sanity_tests.py::test_property_8_bonus_strictly_bounded PASSED [ 80%]
evaluation/scoring_development/scoring_sanity_tests.py::test_property_9_range_bounds PASSED [ 90%]
evaluation/scoring_development/scoring_sanity_tests.py::test_property_10_determinism PASSED [100%]

============================== 10 passed in 3.13s ==============================
```

All 4 models satisfy all 10 sanity properties. Determinism, mathematical bounds $[0.0, 1.0]$, and monotonicity are preserved across all formulations.

---

## 9. Itemized Scoring Traces

Below are the complete diagnostic traces for key representative controlled cases:

### Trace 1: Case D (Core + One Direct Contradiction)
- **Question**: *"What is the purpose of a primary key?"*
- **Reference**: *"A primary key uniquely identifies each record in a table."*
- **Student**: *"A primary key uniquely identifies each record in a table and can contain duplicate values."*
- **Base Score**: $1.0000$ (Scaled: $5.0000/5.0$)
- **Unmatched Proposition**: `"can contain duplicate values"`
  - **Classification**: `INCORRECT`
  - **Evidence Type**: `VALUE_CONFLICT` (mutual exclusion in `uniqueness`: `unique` vs `duplicate`)
  - **Evidence Strength**: $0.9000$
  - **Severity**: $1.0000$ (Core Defining Property Contradiction)
- **Model Outcomes**:
  - **Model A**: Raw $0.8667$, Clipped $0.8667$, Scaled **$4.33 / 5.0$** (Deduction: $-0.67$)
  - **Model B**: Raw $0.6500$, Clipped $0.6500$, Scaled **$3.25 / 5.0$** (Deduction: $-1.75$)
  - **Model C**: Raw $0.8147$, Clipped $0.8147$, Scaled **$4.07 / 5.0$** (Deduction: $-0.93$)
  - **Model D**: Raw $0.5000$, Clipped $0.5000$, Scaled **$2.50 / 5.0$** (Deduction: $-2.50$, Core Invalidation)

### Trace 2: Case E (Core + Multiple Contradictions)
- **Student**: *"A primary key uniquely identifies each record in a table and can contain duplicate values. The key also contains redundant rows."*
- **Base Score**: $1.0000$ (Scaled: $5.0000/5.0$)
- **Unmatched Propositions**:
  1. `"can contain duplicate values"`: `INCORRECT`, `VALUE_CONFLICT` ($E=0.90, \sigma=1.00$)
  2. `"key also contains redundant rows"`: `INCORRECT`, `VALUE_CONFLICT` ($E=0.90, \sigma=1.00$)
- **Model Outcomes**:
  - **Model A**: Raw $0.8000$, Clipped $0.8000$, Scaled **$4.00 / 5.0$**
  - **Model B**: Raw $0.4225$, Clipped $0.4225$, Scaled **$2.11 / 5.0$**
  - **Model C**: Raw $0.7070$, Clipped $0.7070$, Scaled **$3.53 / 5.0$**
  - **Model D**: Raw $0.5000$, Clipped $0.5000$, Scaled **$2.50 / 5.0$**

### Trace 3: Case G (Core + Uncertain Additional Information)
- **Student**: *"A primary key uniquely identifies each record in a table and is usually indexed using a B-tree."*
- **Base Score**: $1.0000$ (Scaled: $5.0000/5.0$)
- **Unmatched Proposition**: `"is usually indexed using a B-tree"`
  - **Classification**: `UNCERTAIN`
  - **Verification Evidence**: `UNVERIFIED` (topical to databases, but unlisted in curated domain rules)
  - **Contradiction**: `NONE`
  - **Applied Adjustment**: $+0.0000$ (Zero bonus)
- **Model Outcomes**:
  - All models: Scaled **$5.00 / 5.0$** (Unverified statements receive zero bonus, preserving epistemic safety).

---

## 10. Cross-Cutting Model Comparison

| Evaluation Dimension | Model A (Current Additive) | Model B (Proportional Penalty) | Model C (Evidence-Weighted) | Model D (Core Decomposition) |
| :--- | :---: | :---: | :---: | :---: |
| **Mathematical Nature** | Additive with saturation | Multiplicative degradation | Additive with evidence gating | Partitioned core/periphery |
| **Case D Penalty Magnitude** | Very Mild ($-0.67$ pts) | Substantial ($-1.75$ pts) | Mild ($-0.93$ pts) | Decisive ($-2.50$ pts) |
| **Case E Cumulative Behavior** | Flattens quickly ($-1.00$ pts) | Compounding ($-2.89$ pts) | Modest increase ($-1.47$ pts) | Plateau at invalidation cap |
| **Partial Core Handling** | Can over-penalize low scores | Scales with base ($S_{\text{base}} \times \prod$) | Can over-penalize low scores | Cleanly bounds bonus & penalty |
| **Interpretability of Deductions** | Low (count only) | High (percentage penalty) | High (evidence $\times$ severity) | Highest (conceptual invalidation) |
| **Risk of Over-Penalization** | Minimal (too conservative) | Moderate on long answers | Low | Low (discrete trigger) |

---

## 11. Advantages and Disadvantages of Each Model

### Model A (Current Additive Saturating)
- **Advantages**: Extremely safe; mathematically bounded in $[0, 1]$; zero risk of negative scores; thoroughly tested in Phase 8.
- **Disadvantages**: Mathematically incapable of penalizing serious misconceptions adequately. A student asserting that a primary key permits duplicate records retains $4.33/5.0$.

### Model B (Proportional Penalty)
- **Advantages**: Proportional scaling is mathematically elegant. When $S_{\text{base}}=0.0$, the final score remains $0.0$. Penalties compound naturally across multiple errors without arbitrary step-functions.
- **Disadvantages**: Multiplicative cascading on verbose student answers with several minor errors can overly deflate scores ($0.65 \times 0.65 \times 0.65 = 0.27$).

### Model C (Evidence-Weighted Severity Penalty)
- **Advantages**: Directly integrates contradiction confidence and conflict types into the penalty calculation. Distinguishes direct property conflicts from peripheral antonymy.
- **Disadvantages**: Because it relies on additive saturation, a single high-confidence contradiction still only achieves $\frac{1}{1 + 0.36} \approx 26\%$ of the maximum penalty, leaving Case D above $4.0/5.0$.

### Model D (Core / Additional Decomposition with Gated Compensation)
- **Advantages**: Best aligns with pedagogical grading. Recognizes that reciting a textbook definition while simultaneously asserting an opposing falsehood proves lack of core understanding. Prevents unearned compensation while leaving non-core errors to mild deductions.
- **Disadvantages**: Requires defining the core invalidation discount parameter ($\text{discount}_{\text{core}} = 0.50$). Introduces a piecewise conceptual distinction between core and peripheral contradictions.

---

## 12. Assessment: Which Model Best Satisfies the Constraints?

Based on the predefined qualitative constraints:
1. **Model D** best resolves the core research defect identified in the audit. It directly models the fact that stating *"a primary key can contain duplicate values"* invalidates the core assertion of uniqueness, reducing the grade to $2.50/5.0$ instead of leaving it at $4.33/5.0$.
2. **Model B** represents the strongest continuous/multiplicative alternative, smoothly reducing Case D to $3.25/5.0$ and Case E to $2.11/5.0$ without threshold branching.
3. **Model A** fails Constraint 2 in terms of pedagogical sufficiency (deduction is too small).
4. **Model C** improves over Model A by incorporating evidence strength, but remains too conservative under single-error saturation.

**Interim Research Conclusion**:
Model D and Model B provide the most compelling formulations. However, per research discipline, **no production code will be modified** until human annotation data or advisor review is conducted.

---

## 13. Remaining Uncertainties

1. **Human Grader Severity Calibration**:
   Different human instructors vary in how severely they penalize contradictory additions. Some instructors award partial credit (e.g. $2.5/5.0$ or $3.0/5.0$) for correct recall of the syntax/definition, while others award zero credit ($0.0/5.0$) for fatal contradictions.
2. **Multi-Proposition Reference Decomposition**:
   When references contain multiple core propositions, defining which proposition is contradicted requires fine-grained proposition-to-proposition mapping.
3. **Implicit vs Explicit Property Negation**:
   Resolving whether an incorrect proposition contradicts a "core defining property" versus a "secondary property" currently relies on `INCOMPATIBLE_VALUE_SETS` domain structures. Expanding this without overfitting requires curated knowledge.

---

## 14. Confirmation: Zero Mohler Benchmark Evaluation

As strictly mandated by the Phase 4A research instructions:
- The full 2,273-record Mohler benchmark was **NOT** executed during this phase.
- No parameters were tuned or optimized against benchmark records.
- All evaluations were conducted exclusively on the explicitly defined controlled development dataset.

---

## 15. Confirmation: Untouched Frozen Experiment Artifacts

The integrity of all prior research artifacts was strictly preserved:
1. **Experiment 1 (Current Benchmark)**:
   - `evaluation/results/current_mohler_results.csv`: **UNTOUCHED**
   - `evaluation/results/current_mohler_summary.json`: **UNTOUCHED**
   - `evaluation/results/current_mohler_propositions.json`: **UNTOUCHED**
2. **Experiment 2 (Representation Improvement)**:
   - `evaluation/results/experiment_2_representation/experiment_2_results.csv`: **UNTOUCHED**
   - `evaluation/results/experiment_2_representation/experiment_2_summary.json`: **UNTOUCHED**
   - `evaluation/results/experiment_2_representation/experiment_2_propositions.json`: **UNTOUCHED**
   - `evaluation/results/experiment_2_representation/experiment_2_report.md`: **UNTOUCHED**
3. **Production Scoring & Domain Rules**:
   - `proposed_asag/scoring/bounded_scorer.py`: **UNTOUCHED** ($M_{\text{pos}}=0.30, M_{\text{neg}}=0.40, r=0.50$).
   - `proposed_asag/evidence/domain_knowledge.py`: **UNTOUCHED** (exactly the 3 curated rules).
