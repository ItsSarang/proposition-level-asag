# Phase 4B: Scoring Model Development & Stress Testing Report

**Status:** Completed Development Study (FROZEN)  
**Date:** 2026-10-04  
**Author:** NLP / ASAG Research Project  
**Repository State:** 494 tests passing, 0 failures, 0 regressions  

---

## 1. Objective

The objective of Phase 4B is to investigate and stress-test candidate scoring models across an expanded matrix of 33 controlled development cases spanning three distinct computer science concept domains (Primary Key, Binary Search Tree, Compiler) plus mixed-information combinations. 

Phase 4A established that the current additive saturating scorer (Model A) is overly conservative when evaluating serious conceptual contradictions (e.g., deducting only 0.67 points for stating that a primary key can contain duplicate values). Phase 4B systematically evaluates whether alternative scoring formulations—specifically Model B (Proportional Penalty), Model C (Evidence-Weighted Severity), and Model D (Core/Additional Decomposition with Gated Compensation)—behave reasonably, satisfy qualitative monotonicity and severity constraints, avoid over-penalizing peripheral mistakes, and maintain cross-domain consistency without introducing destabilizing side effects.

---

## 2. Frozen Assumptions

During this phase, strict research integrity boundaries were enforced:
1. **No Benchmark Execution:** The official UNT/Mohler CS Short Answer benchmark (2,273 records) was **not** executed. Benchmark metrics (MAE, RMSE, Pearson $r$, Spearman $\rho$, QWK) were **not** used to tune parameters or select candidate scoring models.
2. **Frozen Production Scorer:** Production scoring remains untouched at $M_{\text{pos}} = 0.30$, $M_{\text{neg}} = 0.40$, $r = 0.50$ via `BoundedScorer`.
3. **Frozen Domain Knowledge:** The three existing domain knowledge rules (`PK_NOT_NULL`, `BST_INORDER_SORTED`, `COMPILER_INTERMEDIATE_REP`) remained completely frozen. No new domain rules, WordNet synonym lists, or factual knowledge entries were introduced.
4. **Frozen Prior Experiments:** Experiment 1 (Baseline), Experiment 2 (Proposed ASAG Development), Experiment 3 (Precision Improvement), and Phase 4A remain frozen and unmodified.
5. **No External APIs or LLMs:** No dense embeddings, neural language models, or external knowledge services were utilized. All models are deterministic, transparent mathematical formulations operating on explicit linguistic and proposition-level features.

---

## 3. Models Evaluated

Four candidate scoring formulations were evaluated under identical inputs across all 33 controlled cases:

### Model A: Current Additive Saturating Scorer (Production Baseline)
- **Mathematical Form:**
  $$S_{\text{final}} = \text{clip}\left(S_{\text{base}} + \Delta_{\text{pos}} - \Delta_{\text{neg}}, 0.0, 1.0\right)$$
  $$\Delta_{\text{pos}} = M_{\text{pos}} \cdot \frac{r \cdot n_{\text{correct}}}{1 + r \cdot n_{\text{correct}}}, \quad \Delta_{\text{neg}} = M_{\text{neg}} \cdot \frac{0.5 \cdot n_{\text{incorrect}}}{1 + 0.5 \cdot n_{\text{incorrect}}}$$
- **Parameters:** $M_{\text{pos}} = 0.30$, $M_{\text{neg}} = 0.40$, $r = 0.50$, scale = 5.0.
- **Key Characteristic:** Treats all incorrect propositions identically based purely on count $n_{\text{incorrect}}$, without distinguishing severity or evidence type.

### Model B: Proportional Penalty Scorer (Multiplicative Degradation)
- **Mathematical Form:**
  $$S_{\text{final}} = \text{clip}\left((S_{\text{base}} + \Delta_{\text{pos}}) \cdot \prod_{i=1}^{n_{\text{incorrect}}} (1.0 - p_i), 0.0, 1.0\right)$$
  $$p_i = \text{base\_penalty\_rate} \cdot \sigma_i \quad (\text{where } \text{base\_penalty\_rate} = 0.35)$$
- **Parameters:** $\text{base\_penalty\_rate} = 0.35$, $M_{\text{pos}} = 0.30$, $r = 0.50$, scale = 5.0.
- **Key Characteristic:** Compounding degradation proportional to severity $\sigma_i$. Eliminates absolute cliff-edges while penalizing repeated errors multiplicatively.

### Model C: Evidence-Weighted Bounded Severity Penalty Scorer
- **Mathematical Form:**
  $$d_i = \sigma_i \cdot \text{evidence\_strength}_i \cdot \text{weight} \quad (\text{weight} = 0.40)$$
  $$\Delta_{\text{neg}} = M_{\text{neg\_max}} \cdot \frac{\sum d_i}{1 + \sum d_i} \quad (M_{\text{neg\_max}} = 0.70)$$
  $$S_{\text{final}} = \text{clip}\left(S_{\text{base}} + \Delta_{\text{pos}} - \Delta_{\text{neg}}, 0.0, 1.0\right)$$
- **Parameters:** $M_{\text{neg\_max}} = 0.70$, $\text{weight} = 0.40$, scale = 5.0.
- **Key Characteristic:** Additive penalty bounded by a higher asymptote ($0.70$), with raw deductions weighted by both contradiction evidence strength and semantic severity.

### Model D: Core / Additional Decomposition with Gated Compensation
- **Mathematical Form:**
  1. *Core Invalidation Check:* If any additional proposition exhibits $\sigma_i \ge 0.90$ (direct contradiction of a defining core property):
     $$S_{\text{core\_eff}} = S_{\text{base}} \cdot (1.0 - \text{discount}_{\text{core}}) \quad (\text{discount}_{\text{core}} = 0.50)$$
     Otherwise, $S_{\text{core\_eff}} = S_{\text{base}}$.
  2. *Peripheral Additive Deductions:* For propositions with $\sigma_i < 0.90$:
     $$\Delta_{\text{minor}} = \sum_{i: \sigma_i < 0.90} (\text{minor\_weight} \cdot \sigma_i) \quad (\text{minor\_weight} = 0.20)$$
  3. *Gated Bonus:* Correct additional information bonus is capped at $0.50 \cdot S_{\text{core\_eff}}$ and zero if $S_{\text{core\_eff}} = 0.0$:
     $$\Delta_{\text{pos}} = \min\left(\text{raw\_bonus}, 0.50 \cdot S_{\text{core\_eff}}\right)$$
  4. *Final Integration:*
     $$S_{\text{final}} = \text{clip}\left(S_{\text{core\_eff}} + \Delta_{\text{pos}} - \Delta_{\text{minor}}, 0.0, 1.0\right)$$
- **Parameters:** $\text{discount}_{\text{core}} = 0.50$, $\text{minor\_weight} = 0.20$, $M_{\text{pos}} = 0.25$, scale = 5.0.
- **Key Characteristic:** Separates fundamental concept invalidation from peripheral error deductions and strictly prevents bonus compensation for missing or invalidated core content.

---

## 4. Controlled Dataset Design

The Phase 4B development testbed comprises **33 systematically constructed synthetic cases** across four groups:

1. **Primary Key (PK-01 to PK-10, 10 cases):** Evaluates relational database identity, uniqueness, NULL-constraints, schema naming conventions, duplicate value contradictions, and partial matches.
2. **Binary Search Tree (BST-01 to BST-08, 8 cases):** Evaluates ordered data structure concepts, left-child smaller invariant, sorted inorder traversal, AVL rotation remarks, pointer counts, ordering reversals, and partial tree storage.
3. **Compiler (CMP-01 to CMP-08, 8 cases):** Evaluates translation from source to machine code, intermediate representation generation, language creator trivia, LLVM passes, file extension misconceptions, explicit translation negation, and execution model confusion.
4. **Mixed Combinations (MIX-01 to MIX-07, 7 cases):** Evaluates compound conditions combining verified additions, neutral off-topic remarks, minor peripheral errors, and core contradictions in multi-proposition sentences.

*Note:* All cases are synthetic development controls designed to test qualitative scoring mechanics. They are not human-annotated dataset records and must not be interpreted as empirical benchmark results.

---

## 5. Severity Definitions

To evaluate non-uniform penalties without modifying the production classifier, explicit experimental severity categories were annotated for the development testbed:

| Severity Level | Nominal Signal $\sigma_i$ | Conceptual Definition | Representative Example |
| :--- | :---: | :--- | :--- |
| **MINOR** | $0.25$ | A peripheral factual inaccuracy or naming misconception that does not deny or invalidate the core concept. | *"A primary key is always named ID in database schemas."* |
| **MODERATE** | $0.60$ | A notable relational or behavioral error that demonstrates conceptual confusion without directly inverting the defining property. | *"A binary search tree inorder traversal yields random order."* |
| **CORE_CONTRADICTION** | $1.00$ | A statement that directly contradicts or inverts the fundamental defining property of the target entity. | *"A primary key can contain duplicate values."* / *"A binary search tree places larger values in the left subtree."* |
| **NONE** | $0.00$ | Statements classified as `CORRECT_ADDITIONAL`, `IRRELEVANT`, or `UNCERTAIN`. | *"cannot contain NULL values."* / *"SQL was developed in the 1970s."* |

---

## 6. Qualitative Constraints

Before running model comparisons, 12 qualitative scoring constraints (R1–R12) were formally established:

- **R1:** $\text{Score}(\text{Core}) \ge \text{Score}(\text{Core} + \text{Irrelevant})$ (within tolerance $|\Delta| \le 0.05$).
- **R2:** $\text{Score}(\text{Core} + \text{Correct}) \ge \text{Score}(\text{Core})$.
- **R3:** $\text{Score}(\text{Core} + \text{Incorrect}) < \text{Score}(\text{Core})$ (strict deduction).
- **R4:** $\text{Score}(\text{Core} + \text{Core Contradiction}) < \text{Score}(\text{Core} + \text{Minor Incorrect})$.
- **R5:** $\text{Score}(\text{Core} + \text{Multiple Contradictions}) \le \text{Score}(\text{Core} + \text{Single Contradiction})$.
- **R6:** $\text{Score}(\text{Partial Core} + \text{Incorrect}) \le \text{Score}(\text{Partial Core})$.
- **R7:** Incorrect information must **never** compensate for missing or deficient core information.
- **R8:** `UNCERTAIN` propositions must **never** receive positive factual bonuses ($\Delta_{\text{pos}} = 0$).
- **R9:** Positive bonuses must be strictly bounded ($\Delta_{\text{pos}} \le 0.35$; final score $\le 1.0$).
- **R10:** All scores must lie strictly in $[0.0, 1.0]$ normalized and $[0.0, 5.0]$ scaled.
- **R11:** Monotonic severity ordering: $\text{Penalty}(\text{Minor}) \le \text{Penalty}(\text{Moderate}) \le \text{Penalty}(\text{Core Contradiction})$.
- **R12:** Adding irrelevant information must not make an answer substantially worse ($|\Delta| \le 0.05$).

---

## 7. Results by Model

The complete evaluation across all 33 controlled cases is summarized below (all scores scaled to $[0.0, 5.0]$):

| Case ID | Domain | Description | Base | Model A | Model B | Model C | Model D |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **PK-01** | Primary Key | Correct core only | 5.00 | 5.00 | 5.00 | 5.00 | 5.00 |
| **PK-02** | Primary Key | Core + correct additional | 5.00 | 5.00 | 5.00 | 5.00 | 5.00 |
| **PK-03** | Primary Key | Core + irrelevant (SQL 1970s) | 5.00 | 5.00 | 5.00 | 5.00 | 5.00 |
| **PK-04** | Primary Key | Core + unsupported relevant (B-tree) | 5.00 | 5.00 | 5.00 | 5.00 | 5.00 |
| **PK-05** | Primary Key | Core + minor incorrect (always ID) | 5.00 | 4.33 | 4.56 | 4.74 | 4.75 |
| **PK-06** | Primary Key | Core + core contradiction (duplicate) | 5.00 | 4.33 | 3.25 | 4.07 | 2.50 |
| **PK-07** | Primary Key | Core + 2 minor errors | 5.00 | 4.00 | 4.16 | 4.52 | 4.50 |
| **PK-08** | Primary Key | Core + contradiction + irrelevant | 5.00 | 4.33 | 3.25 | 4.07 | 2.50 |
| **PK-09** | Primary Key | Partial core + contradiction | 4.17 | 3.50 | 2.71 | 3.24 | 2.08 |
| **PK-10** | Primary Key | Partial core + minor incorrect | 4.17 | 3.50 | 3.80 | 3.91 | 3.92 |
| **BST-01** | BST | Correct core only | 5.00 | 5.00 | 5.00 | 5.00 | 5.00 |
| **BST-02** | BST | Core + correct additional (inorder) | 5.00 | 5.00 | 5.00 | 5.00 | 5.00 |
| **BST-03** | BST | Core + irrelevant (1946 paper) | 5.00 | 5.00 | 5.00 | 5.00 | 5.00 |
| **BST-04** | BST | Core + unsupported relevant (AVL) | 5.00 | 5.00 | 5.00 | 5.00 | 5.00 |
| **BST-05** | BST | Core + minor incorrect (4 pointers) | 5.00 | 4.33 | 4.56 | 4.74 | 4.75 |
| **BST-06** | BST | Core + direct contradiction (larger left) | 5.00 | 4.33 | 3.25 | 4.07 | 2.50 |
| **BST-07** | BST | Core + 2 contradictions | 5.00 | 4.00 | 2.57 | 3.76 | 1.90 |
| **BST-08** | BST | Partial core + contradiction | 4.17 | 3.50 | 2.71 | 3.24 | 2.08 |
| **CMP-01** | Compiler | Correct core only | 5.00 | 5.00 | 5.00 | 5.00 | 5.00 |
| **CMP-02** | Compiler | Core + correct additional (IR) | 5.00 | 5.00 | 5.00 | 5.00 | 5.00 |
| **CMP-03** | Compiler | Core + irrelevant (Ritchie) | 5.00 | 5.00 | 5.00 | 5.00 | 5.00 |
| **CMP-04** | Compiler | Core + unsupported relevant (LLVM) | 5.00 | 5.00 | 5.00 | 5.00 | 5.00 |
| **CMP-05** | Compiler | Core + minor incorrect (.exe output) | 5.00 | 4.33 | 4.56 | 4.74 | 4.75 |
| **CMP-06** | Compiler | Core + direct contradiction (negation) | 5.00 | 4.33 | 3.25 | 4.11 | 2.50 |
| **CMP-07** | Compiler | Core + 2 incorrect additions | 5.00 | 4.00 | 2.57 | 3.84 | 1.90 |
| **CMP-08** | Compiler | Partial core + incorrect addition | 4.17 | 3.50 | 2.71 | 3.24 | 2.08 |
| **MIX-01** | Mixed | Correct add + irrelevant | 5.00 | 5.00 | 5.00 | 5.00 | 5.00 |
| **MIX-02** | Mixed | Correct add + core contradiction | 5.00 | 4.83 | 3.58 | 4.57 | 2.92 |
| **MIX-03** | Mixed | Correct add + uncertain | 5.00 | 5.00 | 5.00 | 5.00 | 5.00 |
| **MIX-04** | Mixed | Contradiction + irrelevant | 5.00 | 4.33 | 3.25 | 4.07 | 2.50 |
| **MIX-05** | Mixed | Minor incorrect + contradiction | 5.00 | 4.00 | 2.97 | 4.07 | 2.25 |
| **MIX-06** | Mixed | Correct add + minor inc + irrelevant | 5.00 | 4.83 | 5.00 | 5.00 | 5.00 |
| **MIX-07** | Mixed | Correct add + contradiction (BST) | 5.00 | 4.83 | 3.58 | 4.57 | 2.92 |

---

## 8. Severity Analysis

The critical design question was whether scoring models can distinguish error severity rather than penalizing all incorrect statements uniformly:

1. **Model A:** Produced an identical deduction of **$-0.67$ points** ($5.00 \to 4.33$) for both a minor naming convention error (PK-05) and a fundamental uniqueness violation (PK-06). Because Model A only counts $n_{\text{incorrect}}$, it is mathematically incapable of distinguishing minor from catastrophic errors.
2. **Model B:** Scaled deductions smoothly according to $\sigma_i$. Minor error ($\sigma=0.25$) incurred $-0.44$ points ($5.00 \to 4.56$); core contradiction ($\sigma=1.00$) incurred $-1.75$ points ($5.00 \to 3.25$).
3. **Model C:** Scaled deductions via evidence strength and severity into bounded saturation. Minor error incurred $-0.26$ points ($5.00 \to 4.74$); core contradiction incurred $-0.93$ points ($5.00 \to 4.07$).
4. **Model D:** Structurally separated severity into two distinct channels:
   - For $\sigma < 0.90$ (minor/moderate): applied small bounded additive penalties ($-0.25$ points for minor $\to 4.75/5$; $-0.60$ points for moderate $\to 4.40/5$).
   - For $\sigma \ge 0.90$ (core contradiction): triggered a $50\%$ core understanding invalidation discount ($5.00 \to 2.50/5$).

---

## 9. Primary Key Analysis

In the Primary Key domain:
- **Baseline Alignment:** PK-01 achieved full base score (5.00). PK-02 correctly triggered the `PK_NOT_NULL` verification rule.
- **Off-Topic Statements:** PK-03 (SQL 1970s) was classified as `IRRELEVANT` with zero score modification across all models ($5.00 \to 5.00$).
- **Unverified Statements:** PK-04 (B-tree indexing) was classified as `UNCERTAIN` and correctly received 0.0 bonus points across all models.
- **Partial Core Combinations:** In PK-09, partial matching scored $4.17/5.0$. Adding a duplicate value contradiction reduced the score to $3.50$ (Model A), $2.71$ (Model B), $3.24$ (Model C), and $2.08$ (Model D). In Model D, core invalidation discounted the earned partial credit by $50\%$ ($4.17 \to 2.08$), reflecting that an incomplete explanation containing an explicit contradiction demonstrates severe conceptual misunderstanding.

---

## 10. BST Analysis

In the Binary Search Tree domain:
- **Rule Verification:** BST-02 successfully verified `BST_INORDER_SORTED` from *"BST inorder traversal yields sorted order"*.
- **Direct Value Conflict:** BST-06 (*"places larger values in the left subtree"*) triggered `ContradictionType.VALUE_CONFLICT` on the `relative_size` property set (`smaller` vs `larger`), producing high evidence strength ($0.90$).
- **Multiple Errors (BST-07):** Stating that larger values go in the left subtree AND inorder traversal yields random order resulted in:
  - Model A: $4.00/5.0$ (flat saturating penalty for 2 errors)
  - Model B: $2.57/5.0$ (multiplicative compounding: $(1 - 0.35)(1 - 0.21) \approx 0.51$)
  - Model C: $3.76/5.0$ (saturating additive sum of deductions)
  - Model D: $1.90/5.0$ ($50\%$ core discount to $2.50$, minus $0.60$ for moderate disorder)

---

## 11. Compiler Analysis

In the Compiler domain:
- **Rule Verification:** CMP-02 verified `COMPILER_INTERMEDIATE_REP` from *"generates an intermediate representation"*.
- **Explicit Negation Contradiction:** CMP-06 (*"does not translate source code"*) triggered `ContradictionType.EXPLICIT_NEGATION` with evidence strength $0.85$.
- **Model Responses on Explicit Negation:**
  - Model A: $4.33/5.0$
  - Model B: $3.25/5.0$
  - Model C: $4.11/5.0$
  - Model D: $2.50/5.0$

---

## 12. Mixed-Information Analysis

The 7 mixed cases evaluated complex multi-proposition interactions:
- **MIX-01 (Correct + Irrelevant):** All models produced $5.00/5.0$, confirming that irrelevant remarks do not dilute verified bonus points.
- **MIX-02 (Correct Add + Core Contradiction):**
  - Model A produced **$4.83/5.0$**: the $+0.10$ correct bonus offset the $-0.27$ penalty, leaving the student with an almost perfect grade despite stating that primary keys accept duplicate values!
  - Model B produced **$3.58/5.0$**: bonus added first, then degraded by $35\%$.
  - Model C produced **$4.57/5.0$**: bonus and penalty offset additively.
  - Model D produced **$2.92/5.0$**: core understanding was halved to $2.50$; gated bonus was restricted to $0.42$, strictly preventing the student from buying back full credit.
- **MIX-05 (Minor Incorrect + Core Contradiction):** Demonstrates compound penalty ordering without cliff-edge anomalies: Model B produced $2.97$, Model D produced $2.25$.

---

## 13. Model A Comparison

| Criterion | Evaluation under Model A |
| :--- | :--- |
| **Severity Differentiation** | **Failed.** Identical $-0.67$ penalty for minor vs core contradictions. |
| **Resistance to Compensation** | **Failed.** In MIX-02, correct additional info masked a core contradiction ($4.83/5$). |
| **Monotonicity** | Satisfied ($n=1 \to 4.33$, $n=2 \to 4.00$). |
| **Interpretability** | Transparent but simplistic (flat count-based saturating curve). |

**Assessment:** Model A is inadequate for handling nuanced student feedback because it cannot distinguish trivial misconceptions from fundamental conceptual contradictions.

---

## 14. Model B Analysis

| Criterion | Evaluation under Model B |
| :--- | :--- |
| **Severity Differentiation** | **Satisfied.** Continuous scaling via $p_i = 0.35 \cdot \sigma_i$. |
| **Resistance to Compensation** | **Satisfied.** Multiplicative factor degrades all accumulated credit. |
| **Compound Penalty Behavior** | Smooth, but can become harsh on answers containing multiple minor mistakes (e.g. $(1 - 0.0875)^4 \approx 0.69 \to 3.47/5$ despite full core coverage). |
| **Interpretability** | Moderate; percentage-based degradation is mathematically clean but less intuitive for students requesting point-by-point rubrics. |

---

## 15. Model C Analysis

| Criterion | Evaluation under Model C |
| :--- | :--- |
| **Severity Differentiation** | **Satisfied.** Deductions scale with $\sigma_i$ and $\text{ev\_strength}_i$. |
| **Penalty Magnitude** | **Too conservative.** Core contradiction only reduces score from $5.00$ to $4.07$ (a $0.93$-point deduction). |
| **Saturating Ceiling** | With $M_{\text{neg\_max}} = 0.70$, even catastrophic multiple contradictions cannot lower the score below $1.50/5.0$ on a full-core answer. |
| **Interpretability** | High provenance tracing, but formulaic saturation obscures individual point deductions. |

---

## 16. Model D Analysis

| Criterion | Evaluation under Model D |
| :--- | :--- |
| **Severity Differentiation** | **Satisfied.** Binary gating between core invalidation ($\sigma \ge 0.90$) and peripheral deductions ($\sigma < 0.90$). |
| **Resistance to Compensation** | **Satisfied.** Gated bonus cap explicitly prevents bonus compensation when core understanding is impaired. |
| **Harshness on Minor Errors** | **Avoided.** Deducts exactly $0.25$ points for minor errors ($\sigma=0.25$) and $0.60$ points for moderate errors ($\sigma=0.60$), reserving the $50\%$ discount strictly for core contradictions. |
| **Interpretability** | **Highest.** Produces distinct rubrics: Core Understanding vs Fact Bonus vs Peripheral Misconception Deductions. |

---

## 17. Constraint Satisfaction Matrix

| Constraint | Description | Model A | Model B | Model C | Model D |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **R1** | Core $\ge$ Core + Irrelevant ($|\Delta| \le 0.05$) | PASS | PASS | PASS | PASS |
| **R2** | Core + Correct $\ge$ Core | PASS | PASS | PASS | PASS |
| **R3** | Core + Incorrect $<$ Core | PASS | PASS | PASS | PASS |
| **R4** | Core Contradiction $<$ Minor Incorrect | **FAIL** | PASS | PASS | PASS |
| **R5** | Multiple Contradictions $\le$ Single Contradiction | PASS | PASS | PASS | PASS |
| **R6** | Partial Core + Incorrect $\le$ Partial Core | PASS | PASS | PASS | PASS |
| **R7** | Incorrect Cannot Compensate Core Deficit | **FAIL** | PASS | PASS | PASS |
| **R8** | UNCERTAIN Info Receives Zero Bonus | PASS | PASS | PASS | PASS |
| **R9** | Positive Bonus Strictly Bounded | PASS | PASS | PASS | PASS |
| **R10** | Range Bounds $[0.0, 1.0]$ and $[0.0, 5.0]$ | PASS | PASS | PASS | PASS |
| **R11** | Severity Monotonicity: Minor $\le$ Moderate $\le$ Core | **FAIL** | PASS | PASS | PASS |
| **R12** | Irrelevant Addition Neutral ($|\Delta| \le 0.05$) | PASS | PASS | PASS | PASS |
| **Total** | **Satisfied Constraints (out of 12)** | **9 / 12** | **12 / 12** | **12 / 12** | **12 / 12** |

---

## 18. Failure Cases

1. **Model A Failure (R4 & R11):** In PK-05 vs PK-06, Model A gave identical $4.33/5.0$ scores to an answer with an incidental schema naming remark and an answer stating primary keys allow duplicates.
2. **Model A Failure (R7):** In MIX-02, a student who gave a correct core, correctly mentioned NULLs, and stated that duplicates are allowed received $4.83/5.0$. The correct bonus almost completely neutralized the core contradiction.
3. **Model B Potential Vulnerability (Harshness on Verbose Answers):** In an answer containing 3 or 4 peripheral misconceptions, Model B's compounding penalty $\prod(1 - p_i)$ can reduce an otherwise fully correct core answer below $3.0/5.0$.
4. **Model C Failure (Insufficient Penalty for Core Invalidation):** In PK-06, BST-06, and CMP-06, Model C awarded over $4.0/5.0$ despite direct contradictions of the defining entity invariant.

---

## 19. Interpretability Analysis

- **Model D** provides the clearest pedagogical explanations:
  - *Core Coverage:* 100% matched ($5.0/5.0$).
  - *Core Invalidation:* Triggered by direct contradiction on property `uniqueness` ($-50\%$ understanding discount $\to 2.50/5.0$).
  - *Fact Bonus:* Gated at $+0.42$ points.
  - *Net Final:* $2.92/5.0$.
- **Model B** explains scores as percentage reductions (e.g., "Score reduced by $35\%$ due to contradiction on uniqueness"), which is transparent mathematically but less aligned with criteria-referenced grading rubrics.
- **Model A** obscures severity behind an unweighted saturating curve.

---

## 20. Cross-Domain Consistency

The 3 concept domains exhibited consistent behavior across all candidate models:
- **Core Contradiction:** Produced identical normalized penalties across Primary Key (duplicate values), BST (ordering reversal), and Compiler (translation negation):
  - Model A: exactly $4.33/5.0$ ($-0.67$) across all 3 domains.
  - Model B: exactly $3.25/5.0$ ($-1.75$) across all 3 domains.
  - Model D: exactly $2.50/5.0$ ($-2.50$) across all 3 domains.
  - Model C: $4.07$ on PK and BST, $4.11$ on Compiler (slight variation due to explicit negation evidence strength $0.85$ vs value conflict $0.90$).
- **Minor Error:** Produced identical penalties across all 3 domains:
  - Model A: $4.33/5.0$ ($-0.67$).
  - Model B: $4.56/5.0$ ($-0.44$).
  - Model C: $4.74/5.0$ ($-0.26$).
  - Model D: $4.75/5.0$ ($-0.25$).

This confirms that model differences stem from the scoring formulations themselves, not domain-specific artifacts.

---

## 21. Automated Test Results

The automated sanity test suite (`evaluation/scoring_development/phase4b_sanity_tests.py` bridged via `tests/test_phase4b_scoring.py`) executed 26 targeted tests verifying constraints R1–R12, range bounds, monotonicity, and determinism.

- **Existing Tests (before Phase 4B):** 468 passed.
- **New Phase 4B Tests:** 26 passed.
- **Total Passing Tests:** **494 passed**.
- **Failures:** 0.
- **Regressions:** 0.

---

## 22. Candidate Model Recommendation

Under the controlled development criteria and qualitative constraints:
1. **Model D (Core/Additional Decomposition with Gated Compensation)** exhibited the most desirable qualitative behavior:
   - Satisfied all 12 predefined constraints ($12/12$).
   - Successfully distinguished core contradictions ($2.50/5.0$) from minor mistakes ($4.75/5.0$).
   - Prevented correct additional information from compensating for core conceptual deficits.
   - Maintained strict cross-domain consistency.
   - Generated the most interpretable proposition-level pedagogical traces.
2. **Model B (Proportional Penalty)** represents a strong secondary candidate:
   - Satisfied all 12 constraints ($12/12$).
   - Smoothly degrades credit without discrete thresholds.
   - However, it carries a known risk of over-penalizing verbose answers with multiple minor errors.

*Recommendation:* Retain **Model D** as the primary candidate and **Model B** as the secondary candidate for future experimental consideration.

---

## 23. Remaining Uncertainties

1. **Severity Assignment in Production:** In Phase 4B, severity labels (`MINOR`, `MODERATE`, `CORE_CONTRADICTION`) were experimental annotations on synthetic cases. The production pipeline cannot yet infer semantic severity across open-domain concepts automatically without an expanded ontology or explicit rubric model.
2. **Discrete vs Continuous Gating:** Model D employs a discrete threshold ($\sigma \ge 0.90$) for core invalidation. In borderline cases, continuous functions (such as Model B's proportional degradation) may exhibit less threshold sensitivity.
3. **Generalization to Non-Clausal Answers:** The behavior of these models on fragmented student answers (frequent in human benchmarks) remains to be investigated under real benchmark conditions.

---

## 24. Explicit Statement: No Mohler Benchmark Used

**No Mohler benchmark evaluation was performed in Phase 4B.**  
Neither the 2,273 active records nor any subset of the UNT CS Short Answer Dataset was evaluated or inspected during this development phase. All 33 cases examined are synthetic development controls. No claims are made regarding empirical correlation with human grades or benchmark performance.

---

## 25. Explicit Statement: Production Scoring Unchanged

**Production scoring parameters and code remain strictly unchanged.**  
The production system continues to run `BoundedScorer` with $M_{\text{pos}} = 0.30$, $M_{\text{neg}} = 0.40$, and $r = 0.50$. All candidate models evaluated in this study reside exclusively in `evaluation/scoring_development/` as research development prototypes.
