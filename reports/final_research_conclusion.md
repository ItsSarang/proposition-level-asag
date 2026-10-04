# Final Research Conclusion & Synthesis Report

**Project:** Automatic Short Answer Grading using Semantic and Dependency Analysis  
**Repository:** `proposition-level-asag`  
**Degree / Context:** Undergraduate NLP / Automated Short Answer Grading (ASAG) Research Project  
**Author / Implementation:** Antigravity / Gemini CLI (Pair Programming Assistant)  
**Date:** October 4, 2026  
**Status:** COMPLETE, VERIFIED & FROZEN  
**Benchmark Scope:** $N = 2,273$ active student records across 81 active questions (Official Mohler ASAG Benchmark)

---

## 1. Research Question & Formal Answer

### Research Question
> *"Can an interpretable proposition-level extension of a classical semantic/dependency-based ASAG system evaluate unmatched student information as correct additional, irrelevant, or incorrect information, and does incorporating this evaluation improve agreement with human grading?"*

### Formal Research Answer
Based on the full experimental trajectory (V0 through V5) evaluated across all 2,273 active records of the Mohler benchmark:

1. **Technical Feasibility**: **YES.** It is technically feasible to isolate unmatched student information, represent it as structured clausal and relational propositions, categorize it across an interpretable four-way taxonomy (`CORRECT_ADDITIONAL`, `IRRELEVANT`, `INCORRECT`, `UNCERTAIN`), and integrate these evaluations into a severity-aware scoring mechanism with complete transparent explanation traces—without relying on black-box neural networks.
2. **Agreement with Human Grading**: **CONDITIONALLY YES, WITHIN THE PARADIGM.** Incorporating proposition-level evaluation improves agreement with human grading *relative to classical Base ASAG and previous iterations (V1–V4)*, provided that:
   - System-unmatched information is rigorously screened for **core paraphrases** before being treated as additional information.
   - Non-sentential reference fragments are **canonicalized** into evaluate-able proposition structures.
   - Contradiction detection is **guarded** against structural false positives (converse relations, coordinate terms, contrastive subjects).
3. **Global Paradigm Baseline**: **NO.** While V5 is the strongest semantic/dependency ASAG model developed in this project, it **does not outperform simple bag-of-words surface similarity (TF-IDF)** on the overall benchmark ($r = 0.2428$ vs $0.4184$). The semantic/dependency paradigm provides deep interpretability and fine-grained pedagogical feedback, but surface overlap remains a stronger global predictor of human grades on this benchmark.

---

## 2. Hypothesis Resolution Summary

| Hypothesis | Description | Benchmark Evidence | Status |
| :--- | :--- | :--- | :---: |
| **H1: Core Paraphrase Recovery** | Recovering core paraphrases from unmatched propositions restores sentential rank correlation. | On sentential references ($N=1,341$), Spearman $\rho$ improves from $0.1924$ (V4) to $\mathbf{0.2590}$ (V5), surpassing Base ASAG ($0.1968$). | **SUPPORTED BY RESULTS** |
| **H2: Contradiction Guarding** | Filtering raw contradictions prevents spurious severe penalties without masking misconceptions. | 47 false contradictions guarded; controlled tests verify 0 regressions on genuine contradictions; small positive benchmark gain ($r: 0.2424 \to 0.2428$). | **SUPPORTED BY EVIDENCE** |
| **H3: Soft Gating Scorer** | Replacing the hard zero floor with Model D2 soft gating independently improves grading accuracy. | Ablation variant V5-C (Model D2 alone on uncorrected upstream outputs) yields metrics **identical to V4** ($r = 0.2055$, $\text{MAE} = 3.6288$). Soft scoring cannot compensate for upstream alignment failure. | **NOT INDEPENDENTLY SUPPORTED** |

---

## 3. Comprehensive Trajectory of Systems (V0 through V5)

The project executed a methodical, evidence-driven research progression across six complete systems:

```
Overall Pearson Correlation (r):
V0: TF-IDF Cosine Baseline      [====================] 0.4184
V1: Base ASAG (Basak-inspired)   [======] 0.1379
V2: Historical Proposed ASAG    [======] 0.1342
V3: Multi-tier + Hungarian ASAG [==========] 0.2037
V4: Severity-Aware Proposed     [==========] 0.2055
V5: Full Experiment 5           [============] 0.2428

Sentential Subset Spearman Rank Correlation (rho):
V0: TF-IDF Cosine Baseline      [==================] 0.3591
V1: Base ASAG (Basak-inspired)   [==========] 0.1968
V2: Historical Proposed ASAG    [==========] 0.1917
V3: Multi-tier + Hungarian ASAG [==========] 0.1975
V4: Severity-Aware Proposed     [==========] 0.1924
V5: Full Experiment 5           [=============] 0.2590
```

### Full Benchmark Performance Table ($N = 2,273$)

| System | System Description | MAE $\downarrow$ | RMSE $\downarrow$ | Pearson $r$ $\uparrow$ | Spearman $\rho$ $\uparrow$ | QWK $\uparrow$ | Exact 0.0 % |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **V0** | TF-IDF Cosine Similarity Baseline | **2.6571** | **2.9178** | **0.4184** | **0.4424** | **0.1151** | **8.49%** |
| **V1** | Base ASAG (Clausal SPO Triples + Direct Slot) | 3.8050 | 4.0373 | 0.1379 | 0.1181 | 0.0180 | 81.43% |
| **V2** | Historical Proposed (Uncalibrated Additive Bonus) | 3.2176 | 3.5179 | 0.1342 | 0.0765 | 0.0239 | 29.83% |
| **V3** | Current Proposed (Semantic V2 + Hungarian Bipartite) | 3.5955 | 3.8862 | 0.2037 | 0.2007 | 0.0396 | 70.08% |
| **V4** | Experiment 4 (Severity-Aware Scorer Model D) | 3.6288 | 3.9270 | 0.2055 | 0.2033 | 0.0380 | 76.29% |
| **V5** | **Experiment 5 (Full Integrated System)** | **3.4711** | **3.7637** | **0.2428** | **0.2404** | **0.0472** | **60.58%** |

---

## 4. Key Scientific Insights & Discoveries

### Discovery 1: "System Unmatched $\neq$ Human Additional"
The initial hypothesis of early ASAG literature assumed that information in a student answer not aligned with the reference answer represents "additional information" (either extra knowledge or misconceptions). 
Our diagnostic pilot and 500-item AI annotation exercise revealed that **$24.4\%$ of system-unmatched propositions were actually core paraphrases** that classical triple matchers failed to align due to syntactic variation (passives, converse predicates, unanchored purpose clauses). Treating core paraphrases as "additional" artificially suppressed core coverage and caused rank degradation.

### Discovery 2: The Non-Sentential Reference Blindspot
In the Mohler benchmark, $40.7\%$ of reference answers ($33/81$ questions, $N=932$ student answers) are non-sentential fragments (e.g., *"By reference"*, *"File scope"*, *"deallocates memory"*). Classical clausal dependency parsers fail to extract triples from verbless fragments, causing Base ASAG to predict 0.0 across all 932 answers. Resolving this via `CanonicalReferenceExtractor` transformed a completely failed subset into an evaluate-able sub-corpus ($r = 0.2525$).

### Discovery 3: Structural Alignment Precedes Score Function Refinement
Ablation analysis conclusively showed that modifying the scoring function alone (Model D2 soft gating in V5-C) produced zero improvement ($r = 0.2055$). Performance gains are almost entirely driven by upstream structural representation and recovery (V5-A: $r = 0.2424$). If two concepts are not aligned semantically, no mathematical score curve can repair the loss.

---

## 5. Explicit Evidence Against Overclaiming (Scientific Boundaries)

To maintain absolute academic integrity, the following boundaries must be clearly articulated in all presentations and reports:

1. **TF-IDF Remains Stronger Globally**:
   Surface unigram TF-IDF cosine similarity ($r = 0.4184$) outperforms V5 ($r = 0.2428$). Human graders in introductory computer science award substantial credit for keyword mentions even when formal grammar is absent. Dependency systems strictly require relational coherence and thus penalize keyword-only responses that humans accept.
2. **Floor Compression is Mitigated, Not Eliminated**:
   While V5 reduced exact zero grades from $76.29\%$ to $60.58\%$, the predicted mean ($0.7263$) remains far below the lenient human grader mean ($4.1839$). The system remains conservative and under-predicts grades on noisy, informal text.
3. **Proposition-Level Human Gold Validation is Incomplete**:
   The four-way proposition classification taxonomy was validated diagnostically using a 500-item AI annotation exercise. Formal human proposition-level gold annotations were not collected due to scope constraints. The holistic grades are human gold; the proposition labels are AI diagnostic references.
4. **Non-Sentential Fragments Remain Partially Unsolved**:
   While error dropped dramatically on non-sentential questions, $67.70\%$ of records on this subset still receive exact 0.0 grades, showing that template-based canonicalization leaves edge cases unaddressed.

---

## 6. Recommendations for Final Presentation & Defense

When presenting this undergraduate thesis / research project:

1. **Frame the Research Story Chronologically**:
   Follow the story arc from classical Base ASAG limitations (D1–D4), through the diagnostic AI annotation insights, to the targeted interventions in Experiment 5.
2. **Emphasize Interpretability over Raw Black-Box Performance**:
   Highlight that while dense embedding models or LLMs can achieve higher Pearson correlations, they provide zero causal explanation. Our system generates a fully itemized, deterministic explanation trace showing exactly which proposition matched, which core was recovered, which contradiction was guarded, and why points were awarded or withheld.
3. **Highlight the Reversal of Sentential Rank Degradation**:
   The key experimental result of Experiment 5 is that recovering core paraphrases successfully restored rank correlation on full sentential questions ($\rho: 0.1924 \to 0.2590$), soundly beating Base ASAG.
4. **Be Candid About Limitations**:
   Transparently discuss the TF-IDF comparison, the 51.34% false negative floor rate, and the Q7.4 hyphenation regression. Academically rigorous error analysis is a sign of mature research integrity.

---

## 7. Project Readiness Sign-Off

- **Models**: FROZEN (No further modifications).
- **Benchmarks**: FROZEN (All $N = 2,273$ records logged and exported).
- **Test Suite**: 571 tests passing (100% pass rate, 0 regressions).
- **Documentation & Reports**: COMPLETE.

The project is **officially complete and ready to move to final report writing and defense presentation preparation.**
