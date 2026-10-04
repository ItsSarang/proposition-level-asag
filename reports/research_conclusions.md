# Stage 17: Research Conclusions and Final Project Synthesis

**Project:** Automatic Short Answer Grading using Semantic and Dependency Analysis  
**Repository:** `proposition-level-asag`  
**Phase:** Stage 17 — Research Conclusions (Final Stage)  
**Date:** October 2026  
**Status:** COMPLETE (End-to-end research synthesis, empirical evaluation against human grades, diagnostic error analysis, and evidence-based conclusions)

---

## 1. Executive Summary

This research investigates the classical problem of Automated Short Answer Grading (ASAG). While classical semantic and dependency-based ASAG approaches (such as the textual entailment framework proposed by Basak, Naskar, & Gelbukh, 2019) assess student answers primarily through **reference answer coverage**, real-world student responses frequently introduce information outside the instructor's reference answer. Such unmatched information may conceptually constitute:
1. **Correct additional information** (valid elaboration, technical details, or alternative formulations),
2. **Irrelevant additional information** (topical digressions or extraneous remarks), or
3. **Incorrect additional information** (misconceptions, erroneous claims, or factual contradictions).

We designed, implemented, and empirically evaluated an open, interpretable, three-system comparative architecture to address the central research question:

> **Research Question:**  
> *"Can an interpretable proposition-level extension of a classical semantic/dependency-based ASAG system evaluate unmatched student information as correct additional, irrelevant, or incorrect information, and does incorporating this evaluation improve agreement with human grading?"*

Across a full benchmark evaluation on the 2,273 active student responses of the official UNT Computer Science Short Answer Dataset v2.0 (Mohler et al., 2011), the experimental results provide **partial and metric-dependent evidence rather than confirmation of the overall research hypothesis**:

1. **Evaluation of Unmatched Information (Feasibility & Classification):**  
   The study demonstrates the technical feasibility of generating interpretable proposition-level classifications for unmatched student information. Across the benchmark, 3,611 unmatched propositions were processed by the proposed proposition-level system. The classifier assigned the `CORRECT_ADDITIONAL` label to 2,818 propositions (78.04%), `IRRELEVANT` to 780 propositions (21.60%), `INCORRECT` to 12 propositions (0.33%), and `UNCERTAIN` to 1 proposition (0.03%) with deterministic reproducibility, character-level span provenance, and zero pipeline runtime failures.  
   However, the correctness of these individual classifications could not be quantitatively validated because the Mohler dataset contains only holistic answer-level grades and no proposition-level human annotations. These classifications therefore represent system outputs rather than verified ground truth.
2. **Effect on Agreement with Human Grading (Scoring Impact):**  
   **PARTIAL AND METRIC-DEPENDENT EVIDENCE:**
   - **Substantial Observed Reduction in Absolute Error:** Incorporating proposition-level adjustments resulted in a substantial observed reduction in absolute error relative to the implemented Base ASAG system across all 2,273 records (Base ASAG MAE $3.7794 \to$ Proposed ASAG MAE $3.2036$, an observed reduction of 0.5758 points or 15.2%; RMSE $4.0179 \to 3.5101$). On the subset of questions where reference answers contain complete propositions ($N = 1,311$), MAE was observed to drop from $3.5115 \to 2.8607$ (a reduction of 0.6508 points or 18.5%).
   - **Rank Correlation:** Proposed ASAG did not improve Spearman rank correlation over Base ASAG across the full benchmark ($\rho = 0.1177 \to 0.0797$). Unweighted additive bonuses rewarded verbose answers containing multiple related technical clauses, which introduced rank-order noise.
   - **Baseline Comparison:** System 1 (TF-IDF Cosine baseline) achieved higher correlation and lower error than both semantic/dependency systems ($r = 0.4184, \rho = 0.4424, \text{MAE} = 2.6571$). Proposed ASAG did not outperform the TF-IDF baseline on the reported metrics. Diagnostic analysis revealed that TF-IDF was robust to sentence fragments and non-clausal instructor references, which severely degraded clause-dependent syntactic parsing.

---

## 2. Research Story and Methodological Foundations

The research followed an incremental, hypothesis-driven progression across 17 distinct stages:

```
Existing ASAG Problem (Reference Coverage Limitation)
           │
           ▼
Literature Study & Base Paper Selection (Basak et al., 2019)
           │
           ▼
System 1: Simple Baseline (TF-IDF + Cosine Similarity)
           │
           ▼
System 2: Base ASAG Pipeline (Stages 3–10)
[Preprocessing → Dependency Parsing → Triples Extraction →
 Semantic Similarity → Triple Matching → Entailment → Scoring]
           │
           ▼
Identification of Structural Limitations (Stages 10A, 11)
           │
           ▼
System 3: Proposed Proposition-Level Extension (Stages 11–14)
[Proposition Alignment → Span Representation → 
 Additional-Information Classification → Proposed Scoring]
           │
           ▼
Stage 15: Public Benchmark Evaluation (Mohler et al., 2011; N = 2,273)
           │
           ▼
Stage 16: Diagnostic Error Analysis (Four-Quadrant & Case Studies)
           │
           ▼
Stage 17: Evidence-Based Conclusions & Synthesis
```

### Governing Academic Distinctions
In accordance with the project's research integrity protocol (`GEMINI.md`), all concepts are strictly demarcated:
- **PAPER FACT:** Basak et al. (2019) introduced short-answer grading using dependency triples and textual entailment for reference coverage, evaluated on the Mohler dataset.
- **OUR IMPLEMENTATION DECISION:** To ensure complete transparency, we implemented a modular, deterministic, rule-based hierarchy (exact matching, lemma matching, POS compatibility, and WordNet path similarity) without opaque neural embeddings or external API calls.
- **RESEARCH HYPOTHESIS:** That proposition-level decomposition of unmatched student statements can classify supplementary information as correct, irrelevant, or incorrect, and that integrating these assessments will improve agreement with human graders.
- **EXPERIMENTAL RESULT:** Measured numerical metrics on the 2,273 active records of the UNT CS Short Answer Dataset v2.0.
- **INTERPRETATION:** Causal inferences derived from diagnostic error analysis regarding syntactic fragmentation, verbosity inflation, and lexical overlap.

---

## 3. Comprehensive Benchmark Results

The three ASAG systems were benchmarked against human grader averages (`score_ave`, scale $0.0\text{--}5.0$, mean $4.1839$, std $1.0964$) across all 81 active questions in the UNT CS dataset.

### 3.1 Overall Benchmark Performance (All 81 Active Questions, N = 2,273)

| Metric | System 1: TF-IDF Cosine | System 2: Base ASAG | System 3: Proposed ASAG | Human Inter-Annotator Ceiling\* |
| :--- | :---: | :---: | :---: | :---: |
| **Mean Predicted Grade** | 1.5316 | 0.4173 | 1.0129 | 4.1784 |
| **Mean Absolute Error (MAE) ↓** | **2.6571** | 3.7794 | 3.2036 | 0.7263 |
| **Root Mean Squared Error (RMSE) ↓** | **2.9178** | 4.0179 | 3.5101 | 1.2618 |
| **Pearson Correlation ($r$) ↑** | **0.4184** | 0.1419 | 0.1377 | 0.5910 |
| **Spearman Rank Correlation ($\rho$) ↑** | **0.4424** | 0.1177 | 0.0797 | 0.5855 |
| **Quadratic Weighted Kappa (QWK) ↑** | **0.1151** | 0.0191 | 0.0252 | — |
| **Evaluation Runtime (2,273 records)** | 0.9s | 89.4s | 91.9s | — |
| **Pipeline Failure Count** | **0 (0.0%)** | **0 (0.0%)** | **0 (0.0%)** | — |

*\*Note: Human inter-annotator agreement ceiling is computed on Assignments 1–10 ($N = 1,721$) where independent integer grades from Grader 1 and Grader 2 are both available.*

---

### 3.2 Partitioned Performance: Complete Proposition Subset vs. Fragment Subset

A critical finding from Stage 16 diagnostic error analysis was that **33 out of 81 instructor reference answers (40.7%) contain zero extractable finite-clause propositions** (e.g. infinitive phrases like *"To simulate..."* or nominal fragments like *"Abstraction and reusability."*). The table below isolates performance on the subset of questions where the reference answer contains at least one valid proposition ($N = 1,311$ student answers across 48 questions):

| Metric | System 1: TF-IDF | System 2: Base ASAG | System 3: Proposed ASAG | Impact of Proposed Extension |
| :--- | :---: | :---: | :---: | :---: |
| **Mean Pred Grade** | 1.6367 | 0.7231 | 1.3400 | $+0.6169$ points |
| **MAE ↓** | **2.5694** | 3.5115 | 2.8607 | **$-0.6508$ points ($-18.5\%$)** |
| **RMSE ↓** | **2.8423** | 3.7816 | 3.1880 | **$-0.5936$ points ($-15.7\%$)** |
| **Pearson $r$ ↑** | **0.4578** | 0.1991 | 0.2045 | **$+0.0054$** |
| **Spearman $\rho$ ↑** | **0.4746** | 0.1956 | 0.1931 | $-0.0025$ |
| **QWK ↑** | **0.1437** | 0.0343 | 0.0463 | **$+0.0120$ ($+35.0\%$)** |

**Empirical Finding:** When the instructor reference answer provides a syntactically complete proposition, Proposed ASAG achieved a substantial observed reduction in absolute error (MAE dropped by 0.65 points, RMSE by 0.59 points), with a slight change in linear correlation ($r = 0.2045$) and Quadratic Weighted Kappa ($0.0343 \to 0.0463$), while Spearman rank correlation remained essentially unchanged ($0.1956 \to 0.1931$).

---

## 4. Key Discoveries and Scientific Insights

### 4.1 Proposition Extraction Feasibility and Distribution
Across the benchmark, 3,611 unmatched student propositions were processed by the proposed proposition-level system:
- **`CORRECT_ADDITIONAL` (2,818 propositions, 78.04%):** The classifier assigned the `CORRECT_ADDITIONAL` label to 2,818 propositions. In technical computer science questions, student explanations often supply elaborations containing domain concepts present in the question or reference context. Because Stage 13 tests for semantic and domain compatibility against question and reference synset sets, these clauses were assigned this label.
- **`IRRELEVANT` (780 propositions, 21.60%):** The classifier assigned the `IRRELEVANT` label to 780 propositions where student statements showed low semantic affinity to question and reference concepts. These received a neutral score adjustment ($0.0$ effect).
- **`INCORRECT` (12 propositions, 0.33%):** The classifier assigned the `INCORRECT` label to 12 propositions where explicit subject-predicate polarity mismatches or contradictions were detected.
- **`UNCERTAIN` (1 proposition, 0.03%):** The classifier assigned the `UNCERTAIN` label to 1 proposition with borderline evidence.

**Important Data Reality:** Because the Mohler dataset contains no proposition-level human annotations, these classifications represent deterministic system outputs rather than human-verified ground truth.

### 4.2 The Syntactic Fragmentation Barrier in Reference Answers
A major structural insight of this research is that **classical dependency-triple proposition extraction suffers from an architectural mismatch with educational short-answer reference data**:
1. In textbook and examination answer keys, instructors routinely write non-sentential fragments:
   - *Infinitive phrases:* `"To simulate the behaviour of portions of the desired software product."` (Q 1.1)
   - *Nominal lists:* `"Abstraction and reusability."` (Q 1.3), `"Data members and member functions."` (Q 2.1)
   - *Prepositional phrases:* `"At the main function."` (Q 1.4), `"by reference."` (Q 4.3)
2. `DependencyTripleExtractor` requires an explicit grammatical subject (`nsubj` or `csubj`) to form a canonical triple `(subject, predicate, object)`. Consequently, for 33 out of 81 questions, **zero reference propositions were extracted**.
3. Under the standard reference coverage formula:
   $$\text{Coverage} = \frac{\sum \text{Entailed Weights}}{\sum \text{Reference Weights}} = \frac{0}{0} \to 0.0$$
   Base ASAG defaulted to 0.0 for all 962 students answering these questions, even when the student's answer was verbatim identical to the reference answer.
4. **Why TF-IDF Outperformed Base ASAG:** TF-IDF represents text as unconstrained bag-of-words vectors. It requires no finite verbs or subject attachments; if a student writes `"abstraction"` and `"reusability"`, TF-IDF immediately scores high cosine similarity. This explains why TF-IDF achieved $r = 0.4184$ while Base ASAG achieved $r = 0.1419$.

### 4.3 The Verbosity Inflation Pathology (Rank Correlation Degradation)
While Proposed ASAG reduced MAE by awarding credit for supplementary propositions, it degraded Spearman rank correlation across the full dataset ($\rho = 0.1177 \to 0.0797$). 
Diagnostic trace analysis of Case B (Question 2.6, Student 1) revealed the exact mechanism:
- A student wrote a rambling, informal 143-word essay comparing function definitions to "the brain taking in input".
- Because the essay repeatedly used domain nouns (`programmer`, `function`, `variable`), Stage 13 assigned the `CORRECT_ADDITIONAL` label to **17 separate clauses**.
- At $+0.10$ normalized ($+0.50$ points) per proposition, Stage 14 added $+1.70$ normalized ($+8.50$ unclipped points), inflating the student's grade to the maximum of $5.0 / 5.0$, whereas human graders awarded only $2.5 / 5.0$.
- **Lesson:** Additive scoring without answer-length normalization or diminishing marginal returns disproportionately inflates grades for verbose answers, scrambling relative student rankings.

### 4.4 Negation and Lexical Antonymy Conflict
Stage 16 identified a subtle semantic pathology in Case G (Question 7.2, Student 9):
- *Reference Answer:* `"The linked lists can be of variable length."`
- *Student Answer:* `"A linked list is not fixed in size..."` (Human Grade: $5.0 / 5.0$)
- *System Behavior:* Stage 13 classified `(linked list, fixed, not in size)` as **`INCORRECT`** and deducted points.
- *Cause:* Stage 13 checked for surface negation (`"not"`). Because the student predicate was negated while the reference predicate was affirmative, Stage 13 diagnosed a contradiction. However, in English semantics, *"not fixed"* is an exact paraphrase of *"variable"* via lexical antonymy (*fixed* $\leftrightarrow$ *variable*).
- **Lesson:** Rule-based contradiction detection must perform antonym lookups before treating polarity divergence as factual opposition.

---

## 5. System Comparison & Architectural Evaluation

| Dimension | System 1: TF-IDF Cosine | System 2: Base ASAG (Basak-inspired) | System 3: Proposed ASAG (Proposition Extension) |
| :--- | :--- | :--- | :--- |
| **Theoretical Foundation** | Vector Space Model (Salton et al.) | Dependency Parsing & Textual Entailment (Basak et al., 2019) | Proposition Representation & Additional-Info Modulation |
| **Interpretability** | **Low** (Vector angle only; cannot explain which concept is wrong) | **High** (Proposition slot alignments, polarity evidence, coverage fractions) | **Highest** (Full character span provenance, candidate rejection reasons, additional-info labels) |
| **Actionable Feedback** | None (cannot indicate missing concepts) | Explains which reference propositions were missed or contradicted | Explains which reference concepts were met, plus categorizes extra facts as valid or irrelevant |
| **Syntactic Sensitivity** | Insensitive (functions well on fragments) | **Very High** (collapses on non-clausal fragments) | **Very High** (benefits from extra clauses, but vulnerable to fragments) |
| **Domain Jargon** | High (exact technical term overlap) | Moderate (limited by WordNet coverage) | Moderate (limited by WordNet coverage) |
| **Verbosity Robustness** | Moderate (cosine norm penalizes length) | High (extra student sentences ignored) | **Low** (additive adjustments reward rambling unless length-normalized) |
| **Mean Absolute Error** | **2.6571** | 3.7794 | 3.2036 (15.2% observed reduction over Base) |
| **Pearson Correlation** | **0.4184** | 0.1419 | 0.1377 (0.2045 on complete reference answers) |

---

## 6. Answers to the Core Research Question

### Research Sub-Question 1:
> *"Can an interpretable proposition-level extension of a classical semantic/dependency-based ASAG system evaluate unmatched student information as correct additional, irrelevant, or incorrect information?"*

**CONCLUSION:**  
The study demonstrates the technical feasibility of generating interpretable proposition-level classifications for unmatched student information.
1. **Proposition Provenance:** Stages 11 and 12 successfully isolated 3,611 unmatched propositions with exact character-level spans and sentence-relative token indices.
2. **Interpretable Taxonomy:** The Stage 13 classifier processed all 3,611 unmatched propositions and assigned classifications (`CORRECT_ADDITIONAL`: 2,818; `IRRELEVANT`: 780; `INCORRECT`: 12; `UNCERTAIN`: 1) based on transparent lexical, semantic, and polarity criteria without opaque black-box components.
3. **Robustness:** Across 2,273 student responses covering 81 computer science questions, the proposition alignment and classification pipeline operated deterministically with zero unhandled exceptions.
4. **Important Validation Limitation:** The correctness of these individual proposition classifications could not be quantitatively validated because the Mohler dataset contains only holistic answer-level grades and no proposition-level human annotations.

---

### Research Sub-Question 2:
> *"Does incorporating this evaluation improve agreement with human grading?"*

**CONCLUSION: PARTIAL AND METRIC-DEPENDENT EVIDENCE (NUANCED / NOT CONFIRMATION OF THE HYPOTHESIS)**  
The experimental results demonstrate that the effect of incorporating unmatched-information evaluation is nuanced and metric-dependent:
1. **Regarding Absolute Prediction Error (MAE / RMSE): YES (Observed Error Reduction).**  
   The proposed system produced a substantial observed reduction in absolute and squared error relative to the implemented Base ASAG system. Across the entire active benchmark, MAE was reduced from $3.7794$ to $3.2036$ (a reduction of 0.5758 points, or 15.2%). On questions where reference answers contain complete propositions ($N = 1,311$), MAE dropped from $3.5115$ to $2.8607$ (a reduction of 0.6508 points, or 18.5%), and RMSE dropped from $3.7816$ to $3.1880$.
2. **Regarding Linear Correlation ($r$) and Agreement (QWK): Mixed / Marginal.**  
   On complete proposition questions, Pearson $r$ changed marginally ($0.1991 \to 0.2045$) and Quadratic Weighted Kappa showed an increase ($0.0343 \to 0.0463$). Across all questions, Pearson $r$ changed from $0.1419$ to $0.1377$.
3. **Regarding Rank Ordering ($\rho$ Across All Questions): NO (Degradation).**  
   The proposed system did not improve Spearman rank correlation over Base ASAG ($\rho = 0.1177 \to 0.0797$). Unweighted additive proposition adjustments rewarded verbose responses that introduced peripheral domain terms, perturbing relative student rank orderings.
4. **Regarding Comparison to Bag-of-Words Baselines: NO.**  
   The proposed system did not outperform the TF-IDF cosine baseline on the reported metrics ($r = 0.4184, \rho = 0.4424, \text{MAE} = 2.6571$). Bag-of-words lexical similarity was unaffected by the syntactic fragmentation that severely degraded the clausal dependency parser on short-answer reference keys.

---

## 7. Threats to Validity and Study Limitations

1. **Dataset-Specific Fragment Bias:**  
   The UNT Computer Science Short Answer Dataset contains 40.7% non-clausal reference answers. While representative of authentic classroom answer keys, this structural characteristic severely penalized the clause-based dependency parser.
2. **Absence of Clause-Level Human Annotations:**  
   The Mohler dataset provides only holistic, answer-level grades. While the aggregate impact of Stage 13 classifications on final grades was measured, individual proposition classification accuracy could only be evaluated qualitatively via inspection of representative cases.
3. **Human Grade Distribution Skew (Ceiling Effect):**  
   62.8% of student answers in the dataset received a human grade of $\ge 4.5 / 5.0$ (mean $4.18 / 5.0$). This severe ceiling compression makes rank-order metrics ($\rho$) exceptionally sensitive to minor point fluctuations.
4. **Lexical Semantic Resources:**  
   WordNet 3.0 path similarity lacks coverage for modern computer science terminology (e.g. *dereference, instantiate, destructor*), causing false-negative rejections in slot alignment.
5. **Uniform Scoring Weights:**  
   Stage 14 adjustments ($+0.10$ bonus, $-0.20$ penalty) were fixed a priori for testing. They were not calibrated using cross-validation to avoid data snooping.

---

## 8. Recommendations for Future Research: Concrete Directions

Based on the empirical findings of this project, future investigations should focus on four concrete directions:

1. **Non-Clausal and Fragment Proposition Extraction:**  
   Extend the dependency extraction engine to parse infinitive verb phrases (`"To simulate..."`), nominal lists (`"Abstraction and reusability."`), and prepositional phrases into virtual triples (e.g. `(IMPLICIT_PURPOSE, simulate, behaviour)`). This modification would address the 0.0 score collapse across 40.7% of questions.
2. **Length-Normalized / Non-Linear Adjustment Functions:**  
   Replace the uniform linear adjustment with a length-normalized formula featuring diminishing marginal returns:
   $$\Delta_{\text{score}} = w_{\text{add}} \cdot \frac{N_{\text{correct\_add}}}{1 + \lambda \cdot N_{\text{correct\_add}}}$$
   This would award credit for concise, relevant additions while capping rewards for rambling responses, preventing the verbosity inflation observed in Case B.
3. **Antonym-Aware Polarity Resolution:**  
   Integrate lexical antonymy lookups (e.g. via WordNet antonym pointers) before asserting contradiction from negation mismatches (resolving *"not fixed"* $\leftrightarrow$ *"variable"*).
4. **Hybrid Lexical-Propositional Scoring:**  
   Combine the structural interpretability of proposition matching with the fragment-robust vocabulary matching of TF-IDF or dense embeddings, leveraging the complementary strengths of both paradigms.

---

## 9. Final Research Statement

The project demonstrates the technical feasibility of an interpretable proposition-level extension. On the Mohler benchmark, the extension produced lower MAE and RMSE than the implemented Base ASAG system, but lower Spearman correlation and did not outperform the TF-IDF baseline. 

Because proposition-level human annotations are absent, the correctness of the individual additional-information classifications cannot be directly validated. Therefore, the experiment provides partial and metric-dependent evidence rather than confirmation of the overall research hypothesis.

The investigation highlights important empirical findings and limitations of the current implementation: while incorporating proposition-level evaluations yielded a substantial observed reduction in absolute error relative to Base ASAG, unweighted additive scoring introduced verbosity sensitivity that degraded rank correlation, and clausal dependency parsing proved vulnerable to non-sentential reference fragments. These findings provide concrete directions for future research in interpretable educational NLP.
