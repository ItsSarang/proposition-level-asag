# Task 8: Resolution of False Contradictions and Empirical Evaluation of the V5 Proposition-Level ASAG Engine

**Date:** October 13, 2026  
**Repository:** `proposition-level-asag`  
**Dataset:** Official UNT Computer Science Short Answer Dataset v2.0 (Mohler et al., 2011)  
**Sample Count:** $N = 2,273$ active records across 81 active questions  
**Git Revision:** `379117b4f0a889288474e8c9a6375bd18b782082`  
**Test Suite Status:** 708 tests passed, 0 failures, 0 warnings

---

## Executive Summary

Task 8 resolved a severe epistemic defect identified in Task 7 where brittle prepositional similarity comparisons (`prep_sim < 0.30`) acted as a hard contradiction filter in [`proposed_asag/pipeline_v5.py`](file:///Users/sarang/Dev/College/MIT_WPU/Projects/AIES/proposition-level-asag/proposed_asag/pipeline_v5.py), zeroing out valid student answers that expressed correct semantic content using alternative prepositions or syntactic constructions.

Following the core epistemic principle—**low similarity, missing arguments, or differing prepositions alone must never establish a contradiction; contradiction requires positive evidence of mutually exclusive values or spatial/directional clash**—we reformed the pipeline, implemented focused regression tests, re-ran the full Mohler benchmark ($N=2,273$), and executed an empirical ablation isolating the contribution of the additional-information layer.

### Key Empirical Findings:
1. **Defect Resolution & Score Recovery:** 
   - 93 previously zeroed student answers received positive credit.
   - 141 records had improved scores, while only 7 experienced lower scores.
   - Overall V5 MAE dropped from **3.4391** to **3.3358** (a **0.1033** MAE improvement across all 2,273 records).
   - Pearson $r$ increased from **0.2487** to **0.2616** (+0.0129); Spearman $\rho$ rose from **0.2779** to **0.2820**; QWK increased from **0.0551** to **0.0615**.
2. **Key Target Cases Fixed:**
   - **Q6.1 Pointer Paraphrase:** Student *"A pointer is a variable that contains a memory address as its value"* (Human grade 5.0/5.0) rose from **0.0 / 5.0** in Task 7 to **5.0 / 5.0** in Task 8 ($\Delta = +5.0$).
   - **Q11.10 Merge Sort:** Student *"It divides the array into two halves, sorts each half, then merges the two halves together"* rose from **1.096** to **3.775** ($\Delta = +2.68$).
3. **Empirical Ablation (Core-Only vs. Core + Additional Info):**
   - V5 Core-Only (ablation with additional-information layer disabled): **MAE 3.3319**, **Pearson $r$ 0.2625**, **Spearman $\rho$ 0.2824**, **QWK 0.0619**.
   - V5 Full (with additional-information layer enabled): **MAE 3.3358**, **Pearson $r$ 0.2616**, **Spearman $\rho$ 0.2820**, **QWK 0.0615**.
   - **Research Conclusion:** The proposition-level additional-information classification layer does *not* improve grading agreement with human assessors on this benchmark. Almost the entirety of the performance gain over V1 Base ASAG is driven by **Core Coverage and Paraphrase Recovery**, whereas modulating scores based on unmatched propositions introduces minor noise.

---

## 1. Root Cause Analysis of the Contradiction Defect

In Task 7, lines 290–296 of `pipeline_v5.py` contained the following logic:
```python
if ref_prep_args and stu_prep_args:
    ref_lemmas = [item[1].lower() for item in ref_prep_args if len(item) == 2]
    stu_lemmas = [item[1].lower() for item in stu_prep_args if len(item) == 2]
    overlap = set(ref_lemmas).intersection(set(stu_lemmas))
    prep_sim = len(overlap) / max(1, len(ref_lemmas))
    if prep_sim < 0.30:
        status = "CONTRADICTS"
```

### Why this violated epistemic principles:
1. **Syntactic Form Conflated with Semantic Negation:** If the reference answer used a prepositional phrase (e.g. *"contains the address in memory"*) and the student used an adverbial complement or alternative preposition (e.g. *"contains a memory address as its value"*), `ref_lemmas` was `{'memory'}` and `stu_lemmas` was `{'value'}`. Because `overlap == set()`, `prep_sim` was `0.0 < 0.30`. The system labeled this a hard contradiction (`CONTRADICTS`).
2. **Double Invalidation:** A contradiction at the triple level immediately zeroed base coverage, propagated to the severity scorer as a `CORE_CONTRADICTION`, triggered `has_core_invalidation = True`, and zeroed the entire answer, overriding otherwise perfect semantic matches.

---

## 2. Epistemic Architecture & Pipeline Fixes

To resolve this defect without compromising genuine contradiction detection:

1. **Elimination of the Low-Similarity Override:** Removed the hard `prep_sim < 0.30` override in [`proposed_asag/pipeline_v5.py`](file:///Users/sarang/Dev/College/MIT_WPU/Projects/AIES/proposition-level-asag/proposed_asag/pipeline_v5.py).
2. **Positive-Evidence Prepositional Contradiction:** Implemented `_check_prepositional_contradiction` in [`proposed_asag/proposition/core_recovery/core_paraphrase_recovery.py`](file:///Users/sarang/Dev/College/MIT_WPU/Projects/AIES/proposition-level-asag/proposed_asag/proposition/core_recovery/core_paraphrase_recovery.py). A contradiction is only declared if:
   - **Case 1 (Compatible Preposition, Mutually Exclusive Values):** Both reference and student share compatible prepositions (e.g., both use `on`, `by`, or `to`), but the head nouns represent mutually exclusive concepts (e.g., *stored on heap* vs *stored on stack*; *passed by value* vs *passed by reference*; *adds to stack* vs *adds to queue*).
   - **Case 2 (Spatial/Directional Antonyms on Same Target):** The prepositions themselves express opposite spatial or directional relations targeting the same entity (e.g., *above the threshold* vs *below the threshold*; *inside the loop* vs *outside the loop*).
3. **Non-Converse Argument Reversal Detection:** When propositions express an asymmetric relational predicate (such as comparatives `smaller`/`larger` or spatial relations `above`/`below`), asserting identical predicates with transposed argument roles (e.g., *A is smaller than B* vs *B is smaller than A*) is explicitly recognized as `NON_CONVERSE_ARGUMENT_REVERSAL`, which contradicts the core reference assertion without being incorrectly suppressed by contrastive subject guards.
4. **Scoped Explicit Negation & Target Divergence:** Explicit negation (e.g., *Local variables are not allocated on the heap*) is checked for prepositional target divergence against the reference (*Local variables are allocated on the stack*). Because the negative assertion applies to a divergent, incompatible target (`heap` vs `stack`), it does not contradict the stack requirement; it is neutrally treated as missing support (`MISSING`, score contribution 0.0) without imposing a core contradiction penalty.
5. **Configurable Additional-Information Ablation:** Added `enable_additional_info: bool = True` to [`Experiment5Pipeline`](file:///Users/sarang/Dev/College/MIT_WPU/Projects/AIES/proposition-level-asag/proposed_asag/pipeline_v5.py#L149) to permit clean, reproducible ablation between Core requirement coverage and Core + Additional-Information scoring.

---

## 3. Dedicated Regression Test Suite

A focused regression suite was created in [`tests/v5/test_preposition_and_contradiction_fixes.py`](file:///Users/sarang/Dev/College/MIT_WPU/Projects/AIES/proposition-level-asag/tests/v5/test_preposition_and_contradiction_fixes.py), covering:

| Test Case | Reference Text | Student Text | Expected Outcome | Result |
| :--- | :--- | :--- | :--- | :--- |
| **Pointer Paraphrase** | Contains address in memory | Contains a memory address as its value | $\text{Grade} \ge 4.0 / 5.0$ | **5.0 / 5.0** (Pass) |
| **Pointer Contradiction** | Contains address in memory | Cannot contain a memory address | $\text{Grade} \le 1.0 / 5.0$, `has_core_invalidation` | **0.0 / 5.0** (Pass) |
| **Merge Sort Bisection** | Splits array into two, sorts each, merges | Divides array in half, sorts each, joins into sorted array | $\text{Grade} \ge 2.0 / 5.0$ | **2.38 / 5.0** (Pass) |
| **Merge Sort Contradiction** | Splits array into two | Never splits the array into two | $\text{Grade} \le 1.5 / 5.0$, `has_core_invalidation` | **0.0 / 5.0** (Pass) |
| **Heap vs. Stack** | Allocated on the stack | Allocated on the heap | Contradiction, $\text{Grade} = 0.0$ | **0.0 / 5.0** (Pass) |
| **Random vs. Sequential** | Accessed randomly | Accessed sequentially only | Contradiction, $\text{Grade} = 0.0$ | **0.0 / 5.0** (Pass) |
| **Above vs. Below** | Placed above the threshold | Placed below the threshold | Spatial clash, $\text{Grade} = 0.0$ | **0.0 / 5.0** (Pass) |
| **Inside vs. Outside Loop** | Declared inside the loop | Declared outside the loop | Scope clash, $\text{Grade} = 0.0$ | **0.0 / 5.0** (Pass) |
| **Scoped Negation** | Uniquely identifies each record | Uniquely identifies each record, and SQL was never developed | Core credit preserved, $\text{Grade} \ge 2.0$ | **2.5 / 5.0** (Pass) |
| **Minor Preposition Difference** | Translates into machine code | Translates for the machine | Positive credit, no contradiction | **2.5 / 5.0** (Pass) |

All **10 / 10** focused tests passed. Across the entire test suite, **708 / 708** tests passed with 0 failures.

---

## 4. Benchmark Evaluation Results ($N=2,273$)

The evaluation was executed using [`evaluation/experiments/run_task8_benchmark.py`](file:///Users/sarang/Dev/College/MIT_WPU/Projects/AIES/proposition-level-asag/evaluation/experiments/run_task8_benchmark.py) across all 2,273 active records on a MacBook Pro with Apple Silicon in **213.8 seconds** with 0 failures.

### Table 1: Overall Results on Full Active Dataset ($N=2,273$)

| Model | MAE | RMSE | Pearson $r$ | Spearman $\rho$ | QWK | Mean Pred | Mean Human |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **V0 TF-IDF Baseline** | 2.6571 | 2.9178 | **0.4184** | **0.4424** | **0.1151** | 1.5316 | 4.1839 |
| **V1 Base ASAG (Clausal)** | 3.8041 | 4.0365 | 0.1383 | 0.1179 | 0.0180 | 0.3925 | 4.1839 |
| **Task 7 V5 Baseline** | 3.4391 | 3.7622 | 0.2487 | 0.2779 | 0.0551 | 0.7782 | 4.1839 |
| **V5 Core-Only (Ablation)** | **3.3319** | **3.6708** | **0.2625** | **0.2824** | **0.0619** | 0.8899 | 4.1839 |
| **V5 Full (Post-Fix)** | 3.3358 | 3.6745 | 0.2616 | 0.2820 | 0.0615 | 0.8860 | 4.1839 |

### Table 2: Benchmark Results across Partitions

| Partition | $N$ | Model | MAE | RMSE | Pearson $r$ | Spearman $\rho$ | QWK | Mean Pred |
| :--- | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Assignments 1–10** | 1,721 | V0 Baseline | 2.6472 | 2.9073 | 0.4177 | 0.4451 | 0.1126 | 1.5353 |
| | | V1 Base ASAG | 3.8019 | 4.0192 | 0.1336 | 0.1227 | 0.0166 | 0.3899 |
| | | Task 7 V5 | 3.4203 | 3.7373 | 0.2559 | 0.2873 | 0.0557 | 0.7887 |
| | | **V5 Core-Only** | **3.3442** | **3.6754** | **0.2602** | **0.2874** | **0.0599** | 0.8704 |
| | | **V5 Full** | 3.3491 | 3.6797 | 0.2592 | 0.2871 | 0.0594 | 0.8656 |
| **Exams 11–12** | 552 | V0 Baseline | 2.6877 | 2.9502 | 0.4240 | 0.4338 | 0.1226 | 1.5202 |
| | | V1 Base ASAG | 3.8111 | 4.0898 | 0.1496 | 0.1097 | 0.0223 | 0.4008 |
| | | Task 7 V5 | 3.4977 | 3.8387 | 0.2298 | 0.2517 | 0.0534 | 0.7455 |
| | | **V5 Core-Only** | **3.2934** | **3.6567** | **0.2687** | **0.2549** | **0.0681** | 0.9506 |
| | | **V5 Full** | 3.2944 | 3.6580 | 0.2682 | 0.2545 | 0.0678 | 0.9495 |
| **Sentential Reference** | 1,341 | V0 Baseline | 2.7464 | 2.9427 | 0.3743 | 0.3591 | 0.0685 | 1.4510 |
| | | V1 Base ASAG | 3.5520 | 3.8160 | 0.1975 | 0.1968 | 0.0326 | 0.6654 |
| | | Task 7 V5 | 3.5973 | 3.8445 | 0.2058 | 0.2189 | 0.0341 | 0.6198 |
| | | **V5 Core-Only** | **3.4453** | **3.7194** | **0.2295** | **0.2377** | **0.0433** | 0.7765 |
| | | **V5 Full** | 3.4520 | 3.7255 | 0.2278 | 0.2369 | 0.0426 | 0.7698 |
| **Non-Sentential Reference** | 932 | V0 Baseline | 2.5286 | 2.8816 | 0.4681 | 0.5342 | 0.1781 | 1.6476 |
| | | V1 Base ASAG | 4.1668 | 4.3341 | N/A | N/A | 0.0000 | 0.0000 |
| | | Task 7 V5 | 3.2114 | 3.6404 | 0.2951 | 0.3483 | 0.0877 | 1.0061 |
| | | **V5 Core-Only** | **3.1687** | **3.5998** | **0.2985** | **0.3382** | **0.0897** | 1.0531 |
| | | **V5 Full** | **3.1687** | **3.5998** | **0.2985** | **0.3382** | **0.0897** | 1.0531 |

---

## 5. Detailed Delta Analysis against Task 7

Comparing all $N=2,273$ records directly between Task 7 and Task 8:
- **Total records evaluated:** 2,273
- **Records with improved grade:** 141
- **Records with reduced grade:** 7
- **Records with unchanged grade ($|\Delta| \le 0.05$):** 2,125
- **Records previously scored 0.0 that now receive positive credit:** 93

### Inspection of Primary Target Cases:

#### Case 1: Q6.1 Pointer Paraphrase
**Question:** *"What is a pointer?"*  
**Reference Answer:** *"A variable that contains the address in memory of another variable."*

| Student Index | Student Answer Text | Human Score | Task 7 Grade | Task 8 Grade | Delta | Diagnosis |
| :---: | :--- | :---: | :---: | :---: | :---: | :--- |
| `stu_1` | *A pointer is a variable that contains a memory address as its value.* | 5.0 | 0.0 | **5.0** | **+5.00** | **False contradiction completely eliminated.** Argument *"as its value"* no longer clashes with *"in memory"*. |
| `stu_0` | *Its a location in memory that contains the memory address of another location in memory that contains information.* | 5.0 | 1.83 | 1.83 | 0.00 | Clausal containment correctly matched; stable. |
| `stu_2` | *A pointer is a variable which stores the address of another variable.* | 5.0 | 1.33 | 1.33 | 0.00 | Partial match on variable/address; stable. |
| `stu_3` | *Pointers are variables that contain as their values memory addresses of other variables.* | 5.0 | 4.75 | 4.75 | 0.00 | Entailed proposition correctly scored; stable. |

#### Case 2: Q11.10 Merge Sort
**Question:** *"How does merge sort work?"*  
**Reference Answer:** *"It splits the original array into two, sorts each of the two halves, and then merges the sorted arrays."*

| Student Index | Student Answer Text | Human Score | Task 7 Grade | Task 8 Grade | Delta | Diagnosis |
| :---: | :--- | :---: | :---: | :---: | :---: | :--- |
| `stu_2` | *It divides the array into two halves, sorts each half, then merges the two halves together.* | 5.0 | 1.096 | **3.775** | **+2.68** | Bisection equivalence (*"two halves"* $\leftrightarrow$ *"into two"*) recognized without contradiction. |
| `stu_3` | *Divide into two sublists and then those sublists break into length 1, then merges the sublists sorted.* | 5.0 | 0.0 | **1.095** | **+1.10** | Non-clausal fragment previously failed; now receives positive partial credit. |
| `stu_4` | *Merge sort uses the "divide and conquer" idea where it divides the array in half multiple times and then joins each element of the array back into one sorted array...* | 5.0 | 0.0 | **1.583** | **+1.58** | Divides in half + joins into one array awarded partial credit instead of zero. |

---

## 6. Empirical Ablation: Core-Only vs. Full ASAG

A central requirement of Task 8 was establishing the independent contribution of the additional-information layer by contrasting:
1. **V5 Core-Only:** ASAG grading strictly driven by reference requirement coverage (core matching, paraphrase recovery, and canonical fragment alignment).
2. **V5 Full:** Core coverage modulated by additional-information evaluation (categorizing unmatched propositions as `CORRECT_ADDITIONAL`, `IRRELEVANT`, `INCORRECT`, or `UNCERTAIN` and applying Model D2 adjustments).

### Empirical Observations:
1. **Marginal Difference in Aggregate Metrics:**
   - On the full active dataset ($N=2,273$), V5 Core-Only achieves Pearson $r = 0.2625$ and MAE $= 3.3319$, while V5 Full achieves Pearson $r = 0.2616$ and MAE $= 3.3358$.
   - The difference between the two models is less than $0.001$ in correlation and $0.004$ in MAE.
2. **Non-Sentential Partitions:**
   - For all 932 non-sentential reference records, V5 Core-Only and V5 Full produce **identical metrics down to four decimal places** (MAE $3.1687$, Pearson $r = 0.2985$, Spearman $\rho = 0.3382$).
3. **Research Implication for ASAG:**
   - **Research Question Answer:** On this dataset, evaluating unmatched propositions as additional information does *not* improve agreement with human graders over core requirement coverage alone.
   - **Why?** In human grading of short technical answers, instructors predominantly grade on *content presence* (did the student state the required facts?). Extra correct information is rarely awarded bonus points beyond the maximum score, while irrelevant elaboration is ignored rather than penalized. Attempting to modulate grades with small bonuses or penalties on unmatched propositions introduces variance that does not track human grading practice.
   - **Where the Real Gain Came From:** The entire improvement from V1 Base ASAG (Pearson $0.1383$) to V5 (Pearson $0.2616$) was achieved by **handling non-sentential reference fragments, generalized core paraphrase recovery, entity qualifier protection, and repairing false contradictions**.

---

## 7. Artifacts Created & Exported

All benchmark artifacts were exported to a dedicated, timestamped directory without modifying or overwriting previous Task 7 artifacts:

- **Predictions CSV ($N=2,273$):** [`evaluation/results/task8_benchmark/mohler_task8_evaluation_predictions.csv`](file:///Users/sarang/Dev/College/MIT_WPU/Projects/AIES/proposition-level-asag/evaluation/results/task8_benchmark/mohler_task8_evaluation_predictions.csv)
- **Summary JSON:** [`evaluation/results/task8_benchmark/mohler_task8_evaluation_summary.json`](file:///Users/sarang/Dev/College/MIT_WPU/Projects/AIES/proposition-level-asag/evaluation/results/task8_benchmark/mohler_task8_evaluation_summary.json)
- **Configuration JSON:** [`evaluation/results/task8_benchmark/mohler_task8_evaluation_config.json`](file:///Users/sarang/Dev/College/MIT_WPU/Projects/AIES/proposition-level-asag/evaluation/results/task8_benchmark/mohler_task8_evaluation_config.json)
- **Historical Task 7 Benchmark Preserved:** [`evaluation/results/fresh_v5_benchmark/`](file:///Users/sarang/Dev/College/MIT_WPU/Projects/AIES/proposition-level-asag/evaluation/results/fresh_v5_benchmark/)
