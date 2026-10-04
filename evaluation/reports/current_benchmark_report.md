# Current Controlled Mohler Benchmark Evaluation Report

**Date:** October 3, 2026  
**Dataset:** Official UNT CS Short Answer Dataset v2.0 (*Mohler et al., 2011*)  
**Active Records Evaluated:** 2,273 (81 active questions; selection/ordering questions omitted in published literature)  
**Execution Time:** 237.03 seconds  
**Failures / Exceptions:** 0  
**Implementation State:** Frozen Evidence-Grounded Additional Information Layer (Phases 1–9)  

---

## 1. Executive Summary & Frozen Evaluation Protocol

Per the research protocol, the ASAG research engine was **strictly frozen** prior to this evaluation. No scoring weights, thresholds, domain rules, or baseline implementations were altered.

### Frozen System Specifications:
- **Baseline (System 1 / V0):** TF-IDF vectorization with cosine similarity.
- **Base ASAG (System 2 / V1):** Basak-inspired clausal dependency triple extraction and greedy matching.
- **Historical Proposed (System 3 / V2):** Stage 14 linear additive modulation layer.
- **Current Proposed (System 4 / V3):** Complete overhauled pipeline comprising:
  - Hybrid Proposition Representation (clausal S-P-O + fragments + infinitives + properties)
  - Multi-tier Semantic Matching V2 with curated domain lexical equivalences
  - Global bipartite matching (Hungarian algorithm)
  - Question-aware relevance analysis
  - Property & antonym contradiction detection
  - **Repaired Evidence Verification Layer** with strictly 3 proof-of-concept rules:
    - `PK_NOT_NULL`
    - `BST_INORDER_SORTED`
    - `COMPILER_INTERMEDIATE_REP`
  - Bounded horizontal-asymptote scoring ($M_{\text{pos}}=0.30, M_{\text{neg}}=0.40, r=0.50$, saturating strategy)

---

## 2. Comparative Benchmark Results

Evaluation was performed on the active subset ($N=2,273$), as well as standard curriculum partitions: Assignments 1–10 ($N=1,721$) and Exams 11–12 ($N=552$).

### A. Full Active Dataset ($N=2,273$)

| System | MAE ↓ | RMSE ↓ | Pearson $r$ ↑ | Spearman $\rho$ ↑ | QWK ↑ | Mean Pred | Mean Human |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **V0: TF-IDF Baseline** | **2.6571** | **2.9178** | **0.4184** | **0.4424** | **0.1151** | 1.5316 | 4.1839 |
| **V1: Base ASAG** | 3.8050 | 4.0373 | 0.1379 | 0.1181 | 0.0180 | 0.3917 | 4.1839 |
| **V2: Historical Proposed** | 3.2176 | 3.5179 | 0.1342 | 0.0765 | 0.0239 | 0.9990 | 4.1839 |
| **V3: Current Proposed (Repaired)** | 3.5955 | 3.8862 | 0.2037 | 0.2007 | 0.0396 | 0.6042 | 4.1839 |

### B. Assignments 1–10 ($N=1,721$)

| System | MAE ↓ | RMSE ↓ | Pearson $r$ ↑ | Spearman $\rho$ ↑ | QWK ↑ | Mean Pred | Mean Human |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **V0: TF-IDF Baseline** | **2.6472** | **2.9073** | **0.4177** | **0.4451** | **0.1126** | 1.5353 | 4.1784 |
| **V1: Base ASAG** | 3.8030 | 4.0204 | 0.1331 | 0.1229 | 0.0165 | 0.3887 | 4.1784 |
| **V2: Historical Proposed** | 3.2361 | 3.5192 | 0.1365 | 0.0850 | 0.0226 | 0.9740 | 4.1784 |
| **V3: Current Proposed (Repaired)** | 3.6109 | 3.8899 | 0.2053 | 0.1989 | 0.0391 | 0.5808 | 4.1784 |

### C. Exams 11–12 ($N=552$)

| System | MAE ↓ | RMSE ↓ | Pearson $r$ ↑ | Spearman $\rho$ ↑ | QWK ↑ | Mean Pred | Mean Human |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **V0: TF-IDF Baseline** | **2.6877** | **2.9502** | **0.4240** | **0.4338** | **0.1226** | 1.5201 | 4.2011 |
| **V1: Base ASAG** | 3.8111 | 4.0898 | 0.1496 | 0.1097 | 0.0223 | 0.4008 | 4.2011 |
| **V2: Historical Proposed** | 3.1599 | 3.5138 | 0.1274 | 0.0457 | 0.0275 | 1.0770 | 4.2011 |
| **V3: Current Proposed (Repaired)** | 3.5476 | 3.8747 | 0.1989 | 0.1983 | 0.0411 | 0.6770 | 4.2011 |

---

## 3. Comparison with Previously Recorded Results

| Metric | TF-IDF Baseline | Base ASAG | Historical Proposed | Previous Overhaul (Pre-Repair) | Current Proposed (Frozen Post-Repair) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **MAE** | 2.6571 | 3.7794 | 3.2036 | 3.3476 | 3.5955 |
| **RMSE** | 2.9178 | 4.0179 | 3.5101 | 3.6476 | 3.8862 |
| **Pearson $r$** | 0.4184 | 0.1419 | 0.1377 | 0.2201 | 0.2037 |
| **Spearman $\rho$** | 0.4424 | 0.1177 | 0.0797 | 0.2108 | 0.2007 |
| **QWK** | 0.1151 | 0.0191 | 0.0252 | 0.0424 | 0.0396 |

### Observations:
1. **Correlation Stability:** Current Proposed maintains strong correlation ($\rho = 0.2007, r = 0.2037$), substantially outperforming Base ASAG ($\rho = 0.1181$) and Historical Proposed ($\rho = 0.0765$).
2. **Elimination of Unearned Credit:** In the pre-repair overhaul, MAE was lower (3.3476) because thousands of unverified propositions received `CORRECT_ADDITIONAL` solely due to topical keyword overlap, inflating student grades closer to the high human mean (4.1839). With the repaired evidence layer, unverified topical propositions are held as `UNCERTAIN`, preventing artificial score inflation.
3. **Baseline Superiority:** The TF-IDF cosine baseline remains clearly superior in overall correlation ($r=0.4184, \rho=0.4424$) and error ($MAE=2.6571$), reflecting the fundamental lexical distribution of student answers in the Mohler corpus.

---

## 4. Evidence-Layer Proposition Classification Breakdown

All counts represent **system outputs** produced by the deterministic pipeline, NOT human ground-truth labels.

- **Total Student Answers Evaluated:** 2,273
- **Answers Containing Unmatched Propositions:** 2,041 (89.8%)
- **Total Unmatched Propositions Extracted:** 4,349

### Classification Counts:
- **`CORRECT_ADDITIONAL`:** **1** proposition (0.02%)
- **`INCORRECT`:** **40** propositions (0.92%)
- **`IRRELEVANT`:** **2,636** propositions (60.61%)
- **`UNCERTAIN`:** **1,672** propositions (38.45%)

### Auditable Domain Evidence Breakdown:
- **Propositions Supported by Curated Evidence:** **1**
  - `BST_INORDER_SORTED`: **1** (*Question 10.6, Student 1*)
  - `PK_NOT_NULL`: **0**
  - `COMPILER_INTERMEDIATE_REP`: **0**

### Epistemic Implications:
Because the benchmark questions primarily cover data structures and programming concepts outside the 3 curated proof-of-concept rules, 1,672 topical propositions were conservatively held as `UNCERTAIN` rather than awarded unearned bonus points. This confirms that the evidence verifier strictly respects its knowledge boundaries.

---

## 5. Score Effect Analysis

The bounded saturating scorer separates Base ASAG reference coverage from proposition-level adjustments:

$$\text{Final Proposed Score} = \text{Base Score} + \Delta_{\text{positive}} - \Delta_{\text{negative}}$$

- **Mean Base Grade (0–5 scale):** 0.6076
- **Mean Net Adjustment (0–5 scale):** -0.0022
- **Mean Final Grade (0–5 scale):** 0.6042
- **Positive Adjustments:** 1 answer
- **Negative Adjustments:** 37 answers
- **Zero Adjustments:** 2,235 answers

The slight negative mean adjustment reflects the fact that 40 student propositions were flagged for factual contradictions/misconceptions (e.g. `VALUE_CONFLICT` or `ANTONYM_CONFLICT`), while only 1 proposition matched the 3 curated positive domain rules.

---

## 6. Special Diagnostic: Non-Sentential Reference Fragility

A critical diagnostic from earlier phases was re-evaluated: **33 of the 81 active questions (40.7%)** have non-sentential reference fragments (e.g. *"To simulate the behaviour..."*, *"by reference."*, *"Abstraction and reusability."*).

### Subgroup Comparison:

| Subgroup | System | $N$ | MAE | RMSE | Pearson $r$ | Spearman $\rho$ | QWK | Mean Pred | Mean Human |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Sentential References** | **V0: Baseline** | 1,341 | **2.7464** | **2.9427** | **0.3743** | **0.3591** | **0.0685** | 1.4510 | 4.1957 |
| | **V1: Base ASAG** | 1,341 | 3.5535 | 3.8176 | 0.1969 | 0.1968 | 0.0325 | 0.6639 | 4.1957 |
| | **V2: Historical Proposed** | 1,341 | 2.8837 | 3.2052 | 0.2038 | 0.1917 | 0.0450 | 1.3630 | 4.1957 |
| | **V3: Current Proposed** | 1,341 | 3.6412 | 3.8784 | 0.1953 | 0.1975 | 0.0323 | 0.5694 | 4.1957 |
| **Non-Sentential References** | **V0: Baseline** | 932 | **2.5286** | **2.8816** | **0.4681** | **0.5342** | **0.1781** | 1.6476 | 4.1668 |
| | **V1: Base ASAG** | 932 | 4.1668 | 4.3341 | N/A | N/A | 0.0000 | 0.0000 | 4.1668 |
| | **V2: Historical Proposed** | 932 | 3.6980 | 3.9243 | 0.0113 | -0.0459 | 0.0010 | 0.4753 | 4.1668 |
| | **V3: Current Proposed** | 932 | 3.5298 | 3.8976 | 0.2134 | 0.2201 | 0.0499 | 0.6541 | 4.1668 |

### Diagnostic Findings:
1. **Base ASAG Degeneracy:** On the 932 records with non-sentential references, Base ASAG extracted 0 reference propositions, resulting in a predicted score of exactly 0.0 for every single answer (Pearson correlation undefined, MAE = 4.1668).
2. **Current Proposed Robustness:** Because Current Proposed incorporates hybrid proposition extraction (handling infinitives and nominal fragments), it achieves $r=0.2134$ and $\rho=0.2201$ on this challenging subset where Base ASAG failed completely.
3. **Baseline Stability:** TF-IDF cosine similarity is unaffected by clausal syntax, performing strongly on non-sentential fragments ($r=0.4681, \rho=0.5342$).

---

## 7. Neutral Research Status Statement

> "The current evidence layer has passed the controlled robustness gate and has now been evaluated on the Mohler benchmark. The benchmark results indicate that enforcing auditable domain knowledge verification successfully prevents unearned score inflation and preserves rank correlation ($\rho = 0.2007$ vs. $0.0765$ for historical proposed). However, because only 3 curated domain rules were active, the vast majority of topical unmatched propositions (1,672) were conservatively classified as UNCERTAIN. These results provide evidence that proposition-level additional information can be evaluated without unbounded hallucination or false credit leaks, but they do NOT demonstrate improved overall agreement with human grading over simple lexical baselines (TF-IDF $r=0.4184$ vs. $0.2037$), subject to the absence of proposition-level human annotations."
