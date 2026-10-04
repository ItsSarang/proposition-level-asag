# Experiment 4: Additional Information Analysis Report

**Experiment Name**: Experiment 4 — Severity-Aware Proposed ASAG  
**Dataset**: UNT Computer Science Short Answer Dataset v2.0 (*Mohler et al., 2011*)  
**Evaluated Records**: $N=2,273$ active student answers across 81 active questions  
**Scope**: Quantitative audit of unmatched student propositions, epistemic classifications, severity estimations, and score adjustments.

---

## 1. Prevalence of Unmatched Information

In short-answer grading, student answers routinely contain propositions that do not align directly with instructor reference triples. Classical ASAG systems simply discard these propositions with zero score effect.

Across the 2,273 active student answers in the Mohler benchmark:
- **Answers containing unmatched propositions**: 2,114 answers (**93.00%**)
- **Answers without unmatched propositions**: 159 answers (**7.00%**)
- **Total unmatched propositions extracted**: 4,695 propositions
- **Average unmatched propositions per answer**: 2.06 propositions across all records (2.22 per answer with unmatched propositions)

This confirms the central premise of the research project: unmatched student propositions are not an edge case; they are present in over 93% of real student answers.

---

## 2. Epistemic Classification Distribution

The 4,695 unmatched student propositions were evaluated using the frozen four-way epistemic classifier (`RobustAdditionalInfoClassifier` with `QuestionAwareRelevanceAnalyzer`, `PropertyContradictionDetector`, and `PropositionEvidenceVerifier`):

| Classification Category | Proposition Count | Proportion of Unmatched (%) | Description / Role in Pipeline |
| :--- | :---: | :---: | :--- |
| **CORRECT_ADDITIONAL** | 0 | 0.00% | Epistemically verified domain truths from curated knowledge base |
| **IRRELEVANT** | 2,816 | 59.98% | Off-topic, peripheral, or question-irrelevant student assertions |
| **UNCERTAIN** | 1,815 | 38.66% | On-topic/relevant propositions lacking formal domain verification |
| **INCORRECT** | 64 | 1.36% | Property contradictions, antonym conflicts, or direct value clashes |
| **Total Unmatched** | **4,695** | **100.00%** | All propositions extracted beyond the reference alignment |

### Epistemic Grounding and the Zero `CORRECT_ADDITIONAL` Count
A critical methodological finding is the count of 0 `CORRECT_ADDITIONAL` propositions across the full benchmark. This is not an execution failure or software bug; it is the direct consequence of the **epistemic restraint principle** introduced in Phase 9:
1. Under Phase 9 guidelines, an unmatched student assertion is **never assumed correct merely because it is grammatically sound or topical**.
2. To award bonus points, a proposition must be verified against an explicit, audited domain rule in `CuratedDomainKnowledge`.
3. Under the frozen benchmark rules, only three domain rules were active:
   - `PK_NOT_NULL` (Primary keys cannot contain null values)
   - `BST_INORDER_SORTED` (Inorder traversal of a BST yields sorted order)
   - `COMPILER_INTERMEDIATE_REP` (Compilers generate an intermediate representation)
4. None of the 81 questions in the Mohler dataset had student answers that introduced these three specific facts as unmatched secondary clauses.
5. In accordance with epistemic conservatism, all 1,815 topical propositions that lacked formal rule verification defaulted to **`UNCERTAIN`** ($38.66\%$) rather than being guessed as correct.
6. In Model D scoring, `UNCERTAIN` propositions receive an adjustment of $0.0$, strictly preventing speculative grade inflation.

---

## 3. Severity Distribution of Detected Contradictions

Among the 64 propositions classified as `INCORRECT`, the `InterpretableSeverityEstimator` assigned severity levels based on conceptual distance, defining property conflicts, and contradiction confidence:

| Severity Level | Severity Score ($\sigma$) | Count | Proportion of Incorrect (%) | Proportion of All Unmatched (%) |
| :--- | :---: | :---: | :---: | :---: |
| **CORE_CONTRADICTION** | 1.00 | 15 | 23.44% | 0.32% |
| **MODERATE** | 0.60 | 42 | 65.62% | 0.89% |
| **MINOR** | 0.25 | 2 | 3.12% | 0.04% |
| **UNRESOLVED** | 0.00 | 5 | 7.81% | 0.11% |
| **NONE (Non-Incorrect)** | 0.00 | 4,631 | — | 98.64% |
| **Total Incorrect** | — | **64** | **100.00%** | **1.36%** |

### Breakdown of Severity Logic
- **CORE_CONTRADICTION ($N=15$)**: Triggered when a contradiction directly clashes with a defining conceptual property (such as the `relative_size` property of binary search tree nodes) or represents a high-confidence ($w \ge 0.90$) direct clash with the core assertion of the reference answer. These trigger a structural $50\%$ multiplicative discount on the student's core score ($S_{\text{core\_effective}} = S_{\text{base}} \times 0.50$).
- **MODERATE ($N=42$)**: Triggered by unclassified property value conflicts or secondary conceptual incompatibilities ($\sigma = 0.60$). Each imposes a minor penalty deduction of $\Delta = 0.20 \times 0.60 = 0.1200$ (normalized).
- **MINOR ($N=2$)**: Triggered by weak or peripheral discrepancies ($\sigma = 0.25$). Imposes a penalty deduction of $\Delta = 0.20 \times 0.25 = 0.0500$ (normalized).
- **UNRESOLVED ($N=5$)**: Contradiction detected by the classifier but unresolved by the domain lexicon or property ontology; receives zero deduction ($\Delta = 0.0$).

---

## 4. Score Adjustments and Grade Impact

Model D decouples the core reference match from secondary proposition modulation:
$$\text{Grade} = \min\left(1.0, \max\left(0.0, S_{\text{core\_effective}} + \text{pos\_adj} - \text{minor\_pen}\right)\right) \times 5.0$$

Across all 2,273 active records:
- **Answers receiving positive adjustments**: 0 answers (**0.00%**)
- **Answers receiving negative adjustments**: 44 answers (**1.94%**)
- **Answers receiving zero net adjustments**: 2,229 answers (**98.06%**)
- **Mean negative adjustment (when negative)**: $-0.1236$ normalized ($-0.6180$ points on the $[0, 5]$ scale)
- **Mean net adjustment across all answers**: $-0.0024$ normalized ($-0.0120$ points on the $[0, 5]$ scale)

### Summary of Impact
Because no positive bonus was awarded in the absence of verified domain rules, Experiment 4 operated purely as a **quality-gated penalty mechanism**. It reduced the scores of 44 student answers containing detected misconceptions by an average of over 0.6 grade points. As shown in the metrics report, on Exam questions (where students write longer, more complex answers that contain genuine misconceptions), this severity-aware deduction led to an improvement in Pearson correlation ($0.2284$ vs $0.1989$) and Spearman rank correlation ($0.2065$ vs $0.1983$) over the prior unweighted system.
