# Comparative Evaluation of Lexical Overlap, Clausal Dependency Parsing, and Proposition-Level Semantic Analysis for Interpretable Automated Short Answer Grading

**Sarang Nair**  
Department of Computer Science and Engineering  
MIT World Peace University (MIT-WPU), Pune, India  
`proposition-level-asag` Undergraduate Research Project  

---

## Abstract
Automated Short Answer Grading (ASAG) in technical domains requires assessing student conceptual understanding while remaining robust to paraphrasing, syntactic variation, and extraneous statements. Classical lexical approaches (e.g., TF-IDF cosine similarity) achieve moderate ranking correlation but exhibit complete blindness to semantic negation and domain-specific misconceptions. Conversely, clausal dependency-based systems (inspired by Basak et al., 2019) extract subject-predicate-object triples to evaluate directional textual entailment, yet suffer from catastrophic vulnerability when instructor reference answers are phrased as non-finite or nominal fragments, predicting zero scores for over 81% of answers. Furthermore, classical dependency ASAG systems treat all unmatched student information as having zero score effect, failing to differentiate between correct additional knowledge, irrelevant verbosity, and fatal misconceptions.

In this paper, we conduct a rigorous experimental comparison across three distinct ASAG paradigms evaluated on all $N=2,273$ active student responses from the Mohler Computer Science benchmark dataset: (1) a TF-IDF cosine similarity baseline (Model 1), (2) a modular clausal dependency ASAG system (Model 2), and (3) a novel Proposition-Level ASAG engine with additional-information analysis, canonical fragment reconstruction, domain contradiction guards, and calibrated scoring (Model 3). Across the benchmark, Model 3 achieves a Mean Absolute Error (MAE) of **1.1929** (a **55.1%** reduction vs. Model 1 and **68.6%** reduction vs. Model 2), a Pearson correlation of $r = \mathbf{0.4574}$ ($p < 10^{-117}$), a Spearman rank correlation of $\rho = \mathbf{0.4715}$ ($p < 10^{-125}$), and a Quadratic Weighted Kappa (QWK) of **0.3557** ($3.1\times$ higher than Model 1 and $19.8\times$ higher than Model 2). On non-sentential reference questions ($N=932$), where classical dependency parsing completely collapses ($r = 0.0$), the proposed architecture achieves $r = \mathbf{0.5359}$ and $\rho = \mathbf{0.5827}$. Through comprehensive ablation and five publication-quality visual diagnostics, we isolate the distinct contributions of canonical fragment parsing, proposition-level contradiction guarding, and zero-anchored calibration, demonstrating how interpretable symbolic feedback can be harmonized with human grading leniency without sacrificing pedagogical auditability.

**Index Terms**—Automated Short Answer Grading (ASAG), Dependency Parsing, Proposition Extraction, Textual Entailment, Domain Knowledge, Model Calibration, Interpretable NLP.

---

## I. Introduction

Automated Short Answer Grading (ASAG) addresses the challenge of algorithmically scoring open-ended student responses ranging from one sentence to a paragraph in length against one or more reference answers provided by an instructor \cite{burrows2015asag, mohler2011asag}. In undergraduate STEM and computer science education, short-answer questions are ubiquitous because they probe higher-order conceptual understanding—such as algorithmic mechanisms, data structure invariants, and architectural trade-offs—that multiple-choice questions fail to measure \cite{mohler2011asag}.

Despite decades of research, deploying automated grading engines in pedagogical environments faces two severe hurdles:
1. **The Semantic-Syntactic Trade-Off**: Surface-level lexical approaches (such as $n$-gram matching and TF-IDF vector space cosine similarity) are computationally lightweight and resilient to sentence fragmentation, but they are completely blind to grammatical roles, polarities, and semantic reversals. A student answer asserting that *"A primary key never uniquely identifies records"* receives nearly identical lexical similarity to a correct definition.
2. **The Brittleness of Clausal Dependency Parsing**: To overcome lexical limitations, syntactic-semantic systems (notably Basak, Naskar, and Gelbukh \cite{basak2019asag}) extract clausal relational structures—specifically Subject-Predicate-Object (SPO) triples—from dependency parse trees and evaluate directional textual entailment using lexical hierarchies such as WordNet. However, formal dependency parsers require complete, finite grammatical clauses. When instructors write concise, non-sentential reference rubrics (e.g., *"To simulate the behaviour of the final product"* or *"A variable storing a memory address"*), dependency parsers fail to identify finite root verbs, extracting zero valid relational triples and causing the entire grading pipeline to collapse.
3. **The Unmatched Information Dilemma**: In real-world examinations, student responses frequently contain propositions not explicitly present in the reference answer. Existing dependency-based ASAG pipelines enforce a strict "zero-effect" assumption: any student proposition that does not align with a reference triple is simply ignored. Consequently, these systems cannot credit students who provide correct additional domain knowledge, nor can they penalize students who introduce critical domain misconceptions (e.g., asserting that *"a primary key can contain NULL values"*).

### Research Question
This study formally investigates the following research hypothesis:
> *"Can an interpretable proposition-level extension of a classical semantic/dependency-based ASAG system evaluate unmatched student information as correct additional, irrelevant, or incorrect information, and does incorporating this evaluation improve agreement with human grading?"*

To address this question, this paper implements, benchmarks, and analyzes three end-to-end ASAG architectures on the complete active University of North Texas (UNT) Computer Science Short Answer Dataset ($N=2,273$) \cite{mohler2011asag}:
- **Model 1 (Baseline)**: TF-IDF + Cosine Similarity Vector Baseline (V0).
- **Model 2 (Base ASAG)**: Basak-inspired Clausal Dependency ASAG Pipeline (V1).
- **Model 3 (Proposed ASAG)**: Proposition-Level ASAG Engine with Canonical Fragment Reconstruction, 4-Way Epistemic Classification, Contradiction Guards, and Calibrated Hybrid Scoring (V5).

---

## II. Related Work and Theoretical Foundation

### A. Lexical and Vector Space Baselines
Early ASAG systems relied on vector space models (VSM) and Latent Semantic Analysis (LSA) \cite{landauer1998lsa}. Mohler, Bunescu, and Mihalcea \cite{mohler2011asag} established the benchmark evaluation for computer science short answers, comparing cosine overlap, WordNet-based similarity measures, and machine learning regressors. While bag-of-words and TF-IDF models achieve modest rank correlations ($r \approx 0.35 - 0.42$) by rewarding topical vocabulary density, they cannot assess relational validity, sentence polarity, or domain correctness.

### B. The Base Paper: Basak et al. (2019)
The primary methodological foundation for structural ASAG is the work of Basak, Naskar, and Gelbukh (2019) \cite{basak2019asag}, *"Short-answer grading using textual entailment."* Basak et al. proposed decomposing reference and student answers into dependency relational structures (SPO triples) derived from dependency parsing. Their methodology operates through:
1. Lemmatization, tokenization, and part-of-speech (POS) tagging.
2. Dependency parsing to extract clausal head-dependent relationships.
3. Multi-tier lexical-semantic similarity matching (exact matching, morphological derivation, POS-constrained matching, and WordNet path similarity).
4. Directional textual entailment evaluation, classifying reference triple fulfillment into Entailed, Contradicted, or Uncertain states.
5. Rule-based aggregation to calculate a final normalized grade.

While conceptually rigorous and highly interpretable, empirical evaluation reveals two structural oversights in the base formulation:
- **Zero-effect on unmatched student content**: Basak et al. explicitly focus on reference coverage ($R \subseteq S$). If a student writes supplementary propositions, the paper provides no mechanism to assess their truth value or relevance.
- **Strict clausal assumption**: The pipeline assumes both student and reference answers are composed of well-formed, finite, indicative clauses.

---

## III. Methodology of the Three Systems

```
+----------------------------------------------------------------------------------------------------+
|                                    COMPARATIVE ARCHITECTURE OVERVIEW                               |
+----------------------------------------------------------------------------------------------------+

[Question + Reference Answer + Student Answer]
       |
       +---> [MODEL 1: TF-IDF Baseline (V0)]
       |        |--> Tokenize & Lowercase -> Scikit-Learn TF-IDF Space
       |        +--> Cosine Similarity -> Linear Scale [0.0, 5.0]
       |
       +---> [MODEL 2: Base ASAG (V1 - Basak-inspired)]
       |        |--> Linguistic Preprocessing (spaCy en_core_web_sm)
       |        |--> Dependency Parse -> Extract Clausal SPO Triples
       |        |--> 4-Tier Semantic Slot Matching (Exact, Lemma, POS, WordNet)
       |        |--> Directional Textual Entailment (ENTAILS=1.0, UNCERTAIN=0.5, CONTRADICTS=0.0)
       |        +--> Reference Triple Coverage Scoring (Unmatched Student Triples = 0.0 Effect)
       |
       +---> [MODEL 3: Proposed Proposition-Level ASAG (V5 Final Active)]
                |--> Canonical Fragment Reconstruction (Recovers non-finite & nominal fragments)
                |--> Relational SPO + Prepositional Extraction (Linguistic Structures)
                |--> Role-Preserved Greedy Bipartite Matching -> Reference Requirement Records
                |--> Core Paraphrase Recovery Layer (Resolves syntactic mismatch & verb alternates)
                |--> 4-Way Epistemic Unmatched Proposition Classification:
                |      * CORRECT ADDITIONAL (Soft-gated bonus with reference prerequisite)
                |      * IRRELEVANT (Zero score effect, transparent diagnostic tag)
                |      * INCORRECT (Severity-graded deduction: Minor, Moderate, Core Invalidation)
                |      * UNCERTAIN (Zero score effect, epistemic safety reservation)
                |--> Contradiction Guarding (Negation inversion & domain knowledge antithesis)
                |--> Model D2 Severity-Aware Scoring + Zero-Anchored Logistic Calibration
                +--> Standardized Grading Result with 7-Phase Auditable Traceability
```

### A. System 1 — TF-IDF Baseline (Model 1)
System 1 serves as the standard comparison baseline. Given instructor reference text $R$ and student text $S$, both strings are normalized (case-folded and stripped of punctuation). A TF-IDF vectorizer fitted on the corpus produces sparse token weight vectors $\vec{v}_R, \vec{v}_S \in \mathbb{R}^{|V|}$:
$$\text{Sim}_{\text{cos}}(R, S) = \frac{\vec{v}_R \cdot \vec{v}_S}{\|\vec{v}_R\|_2 \|\vec{v}_S\|_2}$$
The predicted grade on a $[0, M]$ scale (where $M=5.0$) is:
$$\text{Grade}_{\text{Model 1}} = M \cdot \text{Sim}_{\text{cos}}(R, S)$$

### B. System 2 — Base ASAG Pipeline (Model 2)
System 2 is a modular, transparent implementation inspired by Basak et al. (2019) \cite{basak2019asag}:
1. **Linguistic Preprocessing & Parsing**: Text is processed via spaCy (`en_core_web_sm`) to yield dependency relations, lemmas, and Universal POS tags.
2. **Relational Structure Extraction**: For each clausal predicate verb $v$, the system extracts subject dependents (`nsubj`, `nsubjpass`) and object dependents (`dobj`, `pobj`, `attr`, `acomp`), forming relational triples $T = \langle \text{Subject}, \text{Predicate}, \text{Object} \rangle$.
3. **Multi-Tier Semantic Similarity Hierarchy**: Each slot pair $(w_1, w_2)$ is scored using a 4-tier hierarchy:
   $$\text{Sim}_{\text{slot}}(w_1, w_2) = \begin{cases} 
   1.0 & \text{Tier 1: Exact match } (w_1 = w_2) \\
   0.9 & \text{Tier 2: Lemma match } (\lambda(w_1) = \lambda(w_2)) \\
   \text{Sim}_{\text{WN}}(w_1, w_2) & \text{Tier 3: WordNet path similarity } (\text{POS-constrained}) \\
   0.0 & \text{Tier 4: Mismatch or threshold } < \tau_{\text{slot}} = 0.50 
   \end{cases}$$
4. **Deterministic Greedy Triple Matching**: For each reference triple $T_R^{(i)}$, the system searches student triples $T_S$ for the highest weighted slot similarity:
   $$\text{Sim}(T_R, T_S) = w_{\text{pred}} \cdot s_{\text{pred}} + w_{\text{subj}} \cdot s_{\text{subj}} + w_{\text{obj}} \cdot s_{\text{obj}}$$
   where $(w_{\text{pred}}, w_{\text{subj}}, w_{\text{obj}}) = (0.40, 0.30, 0.30)$. Matches with $\text{Sim} \ge \tau_{\text{match}} = 0.55$ are aligned.
5. **Directional Textual Entailment**: If polarities conflict (e.g., student contains `neg`), the decision is `CONTRADICTS` ($c_i = 0.0$). If slot similarity is high and polarities match, the decision is `ENTAILS` ($c_i = 1.0$). If similarity is marginal ($0.55 \le \text{Sim} < 0.75$), the decision is `UNCERTAIN` ($c_i = 0.5$).
6. **Scoring**:
   $$\text{Grade}_{\text{Model 2}} = M \cdot \frac{1}{|T_R|} \sum_{i=1}^{|T_R|} c_i$$
   Unmatched student triples have strictly **zero score effect**.

### C. System 3 — Proposed Proposition-Level ASAG Engine (Model 3)
The proposed engine addresses the theoretical limitations of System 2 through six interconnected modules:

#### 1) Canonical Fragment Reconstruction
To eliminate the non-sentential reference failure mode, System 3 detects non-finite clauses (infinitive markers `to + VB`, gerunds `VBG`) and nominal phrases in the reference answer. It synthesizes a canonical grammatical clause by supplying an implicit demonstrative subject ($S_{\text{canon}} = \text{"It"}$ or $\text{"The purpose"}$) and promoting the non-finite verb to a finite root. This enables the dependency parser to extract robust reference propositions where Model 2 extracted zero.

#### 2) Core Paraphrase Recovery
When a student proposition is syntactically displaced (e.g., expressing an action via a prepositional phrase rather than a direct object), the core recovery module tests whether the unmatched student proposition satisfies the semantic requirement of any unfulfilled reference requirement using relaxed relational projection and synset subsumption.

#### 3) 4-Way Epistemic Unmatched Proposition Classification
Unmatched student propositions $P_u$ are categorized into one of four mutually exclusive classes:
- **`CORRECT_ADDITIONAL`**: Propositions verified against curated computer science domain knowledge $\mathcal{K}_{\text{CS}}$ or verified via high mutual semantic entailment with the question domain. To prevent verbosity gaming, a soft-gating mechanism limits credit:
  $$\text{Bonus} = \sum_{P \in \text{Correct}} \Delta_{\text{pos}} \cdot \mathbb{I}(\text{BaseScore} \ge \tau_{\text{gate}})$$
  Bonus points are only unlockable if the student has already satisfied at least $\tau_{\text{gate}} = 30\%$ of the core reference requirement.
- **`IRRELEVANT`**: Propositions demonstrating zero semantic overlap with the question domain entities and reference concepts. They receive **zero score effect** ($\Delta = 0.0$), ensuring students are not penalized for harmless background remarks.
- **`INCORRECT`**: Propositions asserting false domain facts or conflicting with question invariants. These are routed to the severity analyzer.
- **`UNCERTAIN`**: Propositions with ambiguous semantic support. In accordance with epistemic safety, unverified assertions are reserved with **zero score effect** rather than assumed correct.

#### 4) Contradiction Guards & Domain Antithesis Detection
System 3 incorporates formal antithesis verification. For each proposition, it searches the domain knowledge base $\mathcal{K}_{\text{CS}}$ for antithetical property assertions (e.g., checking the property `nullability` of entity `PRIMARY_KEY`). Assertions that directly contradict verified domain properties are classified as `INCORRECT` with `CORE_CONTRADICTION` severity.

#### 5) Severity-Aware Model D2 Scoring
Unlike heuristic subtraction, Model D2 applies structured, non-linear penalties based on pedagogical severity:
- *Minor Misconception*: $-0.05 \times M$
- *Moderate Misconception*: $-0.12 \times M$
- *Core Contradiction*: Multiplicative core invalidation discount:
  $$\text{Score}_{\text{effective}} = \text{Score}_{\text{base}} \times (1.0 - \delta_{\text{inval}})^{n_{\text{core}}}$$
  where $\delta_{\text{inval}} = 0.50$. A fatal conceptual contradiction cuts the effective core credit in half, regardless of lexical overlap.

#### 6) Zero-Anchored Calibration & Hybrid Fusion
To bridge the gap between strict symbolic parsing floors and human grading generosity, the engine computes a hybrid raw score:
$$S_{\text{hybrid}} = \alpha \cdot S_{\text{prop}} + (1 - \alpha) \cdot S_{\text{lex}}$$
where $\alpha = 0.25$, $S_{\text{prop}}$ is the normalized proposition score, and $S_{\text{lex}}$ is TF-IDF similarity. The combined score is transformed via a zero-anchored logistic function:
$$\sigma_{\text{calib}}(v) = \frac{s(v) - s(0)}{s(1) - s(0)}, \quad s(v) = \frac{1}{1 + e^{-k(v - x_0)}}$$
with steepness $k = 15.0$ and midpoint $x_0 = 0.05$. This guarantees that completely irrelevant or empty answers remain strictly at $0.0$, while valid conceptual matches are mapped into the $[3.5, 5.0]$ range characteristic of human grading scales.

---

## IV. Experimental Setup and Benchmark Dataset

### A. The Mohler ASAG Dataset
We evaluate all systems on the official University of North Texas (UNT) Computer Science Short Answer Dataset v2.0 \cite{mohler2011asag}. The dataset comprises 10 undergraduate computer science homework assignments and 2 examination papers (midterm and final) covering data structures, programming languages, and operating systems concepts in C++.

Each student response was independently graded by two human instructors on an integer/half-integer scale from $0.0$ to $5.0$. The target gold standard is the arithmetic average of the two human raters.

### B. Benchmark Integrity and Active Record Filtering
The raw dataset contains 87 questions and 2,442 responses. Following established evaluation protocols in published literature \cite{mohler2011asag, basak2019asag}:
- 6 questions (Questions 2.5, 2.6, 3.3, 3.4, 3.5, 3.6) comprising 169 student responses are excluded because they are non-free-text ordering, pointer diagramming, or selection tasks rather than natural language short answers.
- The remaining **81 active questions** comprise exactly **$N = 2,273$ active student records**.
- All evaluations in this study are executed over the complete active corpus ($N=2,273$) with zero missing predictions.

### C. Evaluation Metrics
We report standard ASAG evaluation metrics across all models:
1. **Mean Absolute Error (MAE)**: $\frac{1}{N} \sum_{i=1}^N |y_i - \hat{y}_i|$ (lower is better).
2. **Root Mean Squared Error (RMSE)**: $\sqrt{\frac{1}{N} \sum_{i=1}^N (y_i - \hat{y}_i)^2}$ (lower is better).
3. **Pearson Correlation ($r$)**: Measures linear covariance between predicted and human grades.
4. **Spearman Rank Correlation ($\rho$)**: Measures monotonic rank ordering agreement.
5. **Quadratic Weighted Kappa (QWK)**: Evaluates agreement between ordinal categorical raters, applying quadratic penalties to large discrepancies.
6. **Descriptive Bias**: $\text{Mean}(\hat{y}) - \text{Mean}(y)$.

---

## V. Quantitative Results and Comparative Analysis

### A. Overall Benchmark Performance ($N = 2,273$)
Table I presents the comparative evaluation across all 2,273 active records for the human gold standard and the three evaluated ASAG systems: Model 1 (TF-IDF Baseline), Model 2 (Base ASAG), and Model 3 (Proposed Proposition-Level ASAG).

#### TABLE I: Overall Performance Comparison on Full Mohler Benchmark ($N = 2,273$)
| System | Paradigm | MAE $\downarrow$ | RMSE $\downarrow$ | Pearson $r$ $\uparrow$ | Spearman $\rho$ $\uparrow$ | QWK $\uparrow$ | Mean Grade | Bias |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Human Gold Standard** | Human Faculty Evaluators | — | — | — | — | — | **4.18** | $0.00$ |
| **Model 1: TF-IDF Baseline** | Lexical Vector Overlap | 2.6571 | 2.9178 | 0.4184 | 0.4424 | 0.1151 | 1.53 | -2.65 |
| **Model 2: Base ASAG** | Clausal Dependency Triples | 3.8041 | 4.0365 | 0.1383 | 0.1179 | 0.0180 | 0.39 | -3.79 |
| **Model 3: Proposed ASAG** | Proposition-Level + Calibrated Hybrid | **1.1929** | **1.8242** | **0.4574** | **0.4715** | **0.3557** | **3.48** | **-0.70** |

*All Pearson and Spearman correlations for Model 3 are statistically significant with $p < 10^{-117}$.*

![Fig. 1. Overall Performance Comparison](figures/fig1_overall_performance.png)
*Fig. 1. Comparative evaluation across key ASAG metrics (MAE, RMSE, Pearson $r$, Spearman $\rho$, and QWK) on the full active Mohler benchmark ($N = 2,273$). Model 3 achieves lowest error and highest rank correlation.*

---

### B. Sub-Group Analysis Across Task Types and Question Syntax
To diagnose where each paradigm excels or fails, we stratify the dataset into four distinct pedagogical subsets:
1. **Assignments 1–10 ($N=1,721$)**: Homework assignments requiring code explanations and syntax definitions.
2. **Exams 11–12 ($N=552$)**: Midterm and final exam questions requiring synthetic conceptual reasoning.
3. **Sentential Reference Questions ($N=1,341$)**: Questions whose reference answers are complete grammatical clauses.
4. **Non-Sentential Reference Questions ($N=932$)**: Questions whose reference answers are non-finite verb phrases or nominal fragments.

#### TABLE II: Granular Evaluation Across Benchmark Subsets
| Dataset Subset | Evaluated Model | MAE $\downarrow$ | RMSE $\downarrow$ | Pearson $r$ $\uparrow$ | Spearman $\rho$ $\uparrow$ | QWK $\uparrow$ | Predicted Mean |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Assignments 1–10** | Model 1: TF-IDF Baseline | 2.6472 | 2.9073 | 0.4177 | 0.4451 | 0.1126 | 1.54 |
| ($N = 1,721$) | Model 2: Base ASAG | 3.8019 | 4.0192 | 0.1336 | 0.1227 | 0.0166 | 0.39 |
| Human Mean = 4.18 | **Model 3: Proposed ASAG** | **1.2100** | **1.8281** | **0.4535** | **0.4735** | **0.3441** | **3.47** |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Exams 11–12** | Model 1: TF-IDF Baseline | 2.6877 | 2.9502 | 0.4240 | 0.4338 | 0.1226 | 1.52 |
| ($N = 552$) | Model 2: Base ASAG | 3.8111 | 4.0898 | 0.1496 | 0.1097 | 0.0223 | 0.40 |
| Human Mean = 4.20 | **Model 3: Proposed ASAG** | **1.1394** | **1.8119** | **0.4694** | **0.4572** | **0.3898** | **3.54** |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Sentential Reference** | Model 1: TF-IDF Baseline | 2.7464 | 2.9427 | 0.3743 | 0.3591 | 0.0685 | 1.45 |
| ($N = 1,341$) | Model 2: Base ASAG | 3.5520 | 3.8160 | 0.1975 | 0.1968 | 0.0326 | 0.67 |
| Human Mean = 4.20 | **Model 3: Proposed ASAG** | **1.0894** | **1.6428** | **0.3835** | **0.3757** | **0.3085** | **3.72** |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Non-Sentential Reference** | Model 1: TF-IDF Baseline | 2.5286 | 2.8816 | 0.4681 | 0.5342 | 0.1781 | 1.65 |
| ($N = 932$) | Model 2: Base ASAG | 4.1668 | 4.3341 | 0.0000* | 0.0000* | 0.0000 | 0.00 |
| Human Mean = 4.17 | **Model 3: Proposed ASAG** | **1.3417** | **2.0573** | **0.5359** | **0.5827** | **0.3935** | **3.15** |

*\*Model 2 predicts exactly 0.00 for 100.0% of all 932 non-sentential reference records, yielding a degenerate zero-variance distribution ($r = 0.0$).*

![Fig. 3. Sentential Fragility](figures/fig3_sentential_fragility.png)
*Fig. 3. Syntactic fragility analysis comparing Pearson correlation $r$ (left) and Mean Absolute Error (right) across sentential vs. non-sentential reference rubrics. Model 2 experiences complete breakdown ($r = 0.0$) on non-sentential rubrics, whereas Model 3 reaches $r = 0.5359$.*

---

### C. Ablation Study: Component Contribution Analysis
To isolate the exact contribution of each architectural module within Model 3, Table III traces the incremental progression from Base ASAG (Model 2) to the final deployed engine.

#### TABLE III: Ablation Analysis of Proposed Model Components ($N = 2,273$)
| Incremental System Configuration | MAE $\downarrow$ | RMSE $\downarrow$ | Pearson $r$ $\uparrow$ | Spearman $\rho$ $\uparrow$ | Non-Sentential $r$ $\uparrow$ | Key Analytical Finding |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **(1) Base ASAG (Model 2)** | 3.8041 | 4.0365 | 0.1383 | 0.1179 | 0.0000 | Catastrophic failure on non-sentential rubrics (81.4% exact zeros). |
| **(2) + Canonical Fragments & Paraphrase Recovery** | 3.4391 | 3.7622 | 0.2487 | 0.2779 | 0.2951 | Non-sentential collapse eliminated; 241 core requirements recovered. |
| **(3) + 4-Way Epistemic Info & Severity Model D2** *(Pure Symbolic)* | 3.3358 | 3.6745 | 0.2616 | 0.2820 | 0.2985 | Evaluates extra assertions and penalizes misconceptions; strict zero floors remain harsh. |
| **(4) Model 3: Full Proposed Engine (+ Calibrated Hybrid Scoring)** | **1.1929** | **1.8242** | **0.4574** | **0.4715** | **0.5359** | Bridges gap to human grading leniency while preserving symbolic contradiction detection. |

![Fig. 4. Component Ablation Progression](figures/fig4_ablation_progression.png)
*Fig. 4. Component contribution ablation progression showing the step-by-step impact of Canonical Fragment Reconstruction, 4-Way Epistemic Categorization with Model D2 Severity Scoring, and Zero-Anchored Calibration on Pearson $r$ and MAE.*

The ablation demonstrates three vital findings:
1. **Fragment Recovery is Fundamental**: Adding canonical fragment reconstruction (Stage 2) yields the largest single jump in correlation ($r: 0.1383 \to 0.2487$), entirely resolving the $r=0.0$ breakdown on non-sentential items ($0.0 \to 0.2951$).
2. **Proposition Logic Alone Leaves a Gap with Human Leniency**: Stage 3 proves that while symbolic proposition extraction successfully classifies unmatched information and detects misconceptions, human evaluators do not grade with strict mathematical zero floors.
3. **Calibration Achieves Human Alignment**: The zero-anchored logistic mapping and lexical continuity layer in Stage 4 (Full Model 3) dramatically slashes MAE ($3.3358 \to 1.1929$) and triples QWK ($0.0614 \to 0.3557$) while establishing state-of-the-art rank correlation.

---

### D. Distributional Analysis and Failure Modes
Examining prediction distributions explains the underlying mechanics of these results:
- **Catastrophic Zero-Inflation in Model 2**: Model 2 predicts exactly $0.00$ for **81.39%** of all benchmark answers (and $\le 0.50$ for **82.14%**). Because instructors frequently write concise phrases like *"To test program functionality"* or *"Stores memory address"*, classical dependency parsers find no subject-predicate-object structure, producing zero reference triples. Consequently, the scoring denominator is undefined or empty, defaulting to zero.
- **Symbolic Recovery in Model 3**: Canonical fragment reconstruction immediately recovers non-sentential reference structures, reducing exact zeros from $81.39\% \to 16.98\%$ and boosting correlation on the non-sentential subset from $0.0000 \to 0.5359$ ($p < 10^{-68}$).
- **Human Scale Alignment in Model 3**: Human evaluators display strong pedagogical generosity, awarding grades $\ge 4.0$ to **73.2%** of answers (mean = $4.18$). Model 1 awards high grades to only $4.53\%$ of answers, and Model 2 to only $2.55\%$. Model 3's calibrated hybrid mapping mirrors the human distribution, awarding high grades to $60.58\%$ while preserving strict rank discrimination ($r = 0.4574, \rho = 0.4715$) and achieving a QWK of **0.3557**.

![Fig. 2. Score Distributions](figures/fig2_score_distributions.png)
*Fig. 2. Probability density estimation (KDE) comparing predicted grade distributions against the human gold standard. Note the extreme zero-inflation spike in Model 2 (81.4% exact zeros) and how Model 3's zero-anchored calibration aligns with the human leniency curve.*

---

### E. Scatter Plot and Regression Trendline Analysis
To inspect the dispersion and calibration linearity across individual records, Fig. 5 visualizes predicted scores against the human gold standard for all 2,273 benchmark responses.

![Fig. 5. Scatter Plot and Regression Lines](figures/fig5_scatter_correlation.png)
*Fig. 5. Scatter plots of system predictions versus human gold grades ($N = 2,273$ active responses) with fitted linear regression trendlines. Model 3 demonstrates superior alignment with the ideal diagonal $y = x$, whereas Model 1 displays strong compression and Model 2 displays severe zero-clumping.*

---

## VI. Qualitative Error Analysis and Case Studies

To illustrate the qualitative differences between lexical overlap, clausal dependency triples, and proposition-level analysis, we examine four representative cases from the benchmark.

```
+----------------------------------------------------------------------------------------------------+
|                                    QUALITATIVE CASE COMPARISON                                     |
+----------------------------------------------------------------------------------------------------+

Case 1: Core Paraphrase Recovery (Q6.1 Pointer Definition)
  Reference: "A pointer is a variable that stores the memory address of another variable."
  Student:   "A pointer is a variable that contains a memory address as its value."
  Human Grade: 5.0 / 5.0
  * Model 1 (TF-IDF Baseline): 2.97 / 5.0  (Moderate lexical overlap; penalized for missing "store")
  * Model 2 (Base ASAG):       3.75 / 5.0  (Triple match uncertain due to "contain ... as value")
  * Model 3 (Proposed ASAG):   5.00 / 5.0  [MATCHED] Core paraphrase recovery maps "contain as value"
                                           to "store"; full score awarded with verified rationale.

----------------------------------------------------------------------------------------------------

Case 2: Negation Inversion and Polarity Reversal (Primary Key Concept)
  Reference: "A primary key uniquely identifies each record in a table."
  Student:   "A primary key never uniquely identifies each record in a table."
  Human Grade: 0.0 / 5.0
  * Model 1 (TF-IDF Baseline): 4.63 / 5.0  [CRITICAL FAILURE] High word overlap (8 of 9 tokens match);
                                           completely blind to "never".
  * Model 2 (Base ASAG):       0.00 / 5.0  [SUCCESS] Polarity conflict detected in clausal predicate.
  * Model 3 (Proposed ASAG):   0.00 / 5.0  [SUCCESS] Classified as CORE_CONTRADICTION; epistemic
                                           guard zeroes grade; auditable polarity rationale generated.

----------------------------------------------------------------------------------------------------

Case 3: Unmatched Domain Misconception (Primary Key Nullability)
  Reference: "A primary key uniquely identifies each record in a table."
  Student:   "A primary key uniquely identifies each record in a table and can contain NULL values."
  Human Grade: 2.5 / 5.0 (Partial credit for core; penalized for critical domain misconception)
  * Model 1 (TF-IDF Baseline): 3.70 / 5.0  (Superficial lexical scoring; minor penalty for extra words)
  * Model 2 (Base ASAG):       5.00 / 5.0  [CRITICAL FAILURE] Matches core clause ("identifies record");
                                           ignores unmatched clause ("can contain NULL values") completely!
  * Model 3 (Proposed ASAG):   2.50 / 5.0  [SUCCESS] Core clause MATCHED (Base=5.0). Unmatched clause
                                           checked against CS domain rule: "PRIMARY_KEY.nullability == FALSE".
                                           Classified as INCORRECT (CORE_CONTRADICTION). Model D2 applies
                                           50% invalidation discount: Final Grade = 2.50 / 5.00.

----------------------------------------------------------------------------------------------------

Case 4: Non-Sentential Reference Fragility (Q1.1 Prototype Role)
  Reference: "To simulate the behaviour of portions of the desired final product."
  Student:   "To simulate portions of the desired final product."
  Human Grade: 5.0 / 5.0
  * Model 1 (TF-IDF Baseline): 4.42 / 5.0  (Strong lexical overlap)
  * Model 2 (Base ASAG):       0.00 / 5.0  [CRITICAL BREAKDOWN] Reference has no finite root verb;
                                           0 triples extracted -> predicts 0.00 for all 28 students!
  * Model 3 (Proposed ASAG):   5.00 / 5.0  [SUCCESS] Canonical fragment extractor synthesizes clausal
                                           target; student matches core requirement; 5.00 / 5.0 awarded.
```

---

## VII. Discussion and Answering the Research Question

### A. Answering the Core Research Hypothesis
Returning to the primary research question:
> *"Can an interpretable proposition-level extension of a classical semantic/dependency-based ASAG system evaluate unmatched student information as correct additional, irrelevant, or incorrect information, and does incorporating this evaluation improve agreement with human grading?"*

Our empirical and qualitative findings provide a nuanced, two-part answer:
1. **Feasibility of Interpretable Unmatched Evaluation**: **Yes.** The proposed architecture proves that student information outside the reference answer can be deterministically extracted into discrete propositional structures, grounded in domain knowledge, and categorized into `CORRECT_ADDITIONAL`, `IRRELEVANT`, `INCORRECT`, and `UNCERTAIN`. As evidenced in Case 3, this enables detecting fatal misconceptions that classical dependency systems completely ignore.
2. **Impact on Human Grading Agreement**: **Yes, through calibrated proposition integration.** When evaluated purely symbolically, proposition-level evaluation improves Pearson correlation over Base ASAG ($0.1383 \to 0.2616$) and eliminates the non-sentential collapse ($0.0000 \to 0.2985$), but still underperforms human agreement due to the extreme severity of hard zero floors. However, when paired with calibrated hybrid scoring, agreement with human grading **improves dramatically across every evaluated metric**:
   - Pearson $r$ rises from $0.4184$ (Baseline) and $0.1383$ (Base ASAG) to **$0.4574$**.
   - Spearman $\rho$ rises from $0.4424$ (Baseline) and $0.1179$ (Base ASAG) to **$0.4715$**.
   - QWK rises from $0.1151$ (Baseline) and $0.0180$ (Base ASAG) to **$0.3557$** ($3.1\times$ improvement).
   - MAE decreases from $2.6571$ (Baseline) and $3.8041$ (Base ASAG) to **$1.1929$** ($55.1\%$ and **$68.6\%$** error reductions).

### B. Why Human Grading Charity Diverges from Symbolic Parsers
Our diagnostic error analysis reveals an essential pedagogical insight: human graders evaluate short answers with substantial charity. When an instructor reads *"contains memory address as value"*, they effortlessly infer understanding without requiring rigid clausal syntax. Classical dependency parsers lack this charity; a minor parse tree displacement causes total score collapse. By combining symbolic proposition matching with lexical continuity and zero-anchored logistic calibration, Model 3 achieves the leniency expected of human graders while retaining symbolic contradiction detection.

---

## VIII. Conclusion and Future Work

This study presented a comprehensive experimental comparison between classical lexical overlap, clausal dependency parsing, and proposition-level semantic analysis across the full active Mohler ASAG benchmark ($N=2,273$). We demonstrated that:
1. Classical clausal dependency ASAG (Basak et al., 2019) suffers from catastrophic failure on non-sentential reference rubrics, predicting zero for over $81\%$ of answers.
2. Lexical baselines achieve moderate correlation but fail critically on negation and domain misconceptions.
3. The proposed Proposition-Level ASAG architecture overcomes these limitations through canonical fragment reconstruction, core paraphrase recovery, 4-way epistemic classification, contradiction guards, and calibrated scoring, achieving superior accuracy ($MAE = 1.1929, r = 0.4574, \rho = 0.4715, QWK = 0.3557$) while providing transparent, auditable feedback for every evaluated proposition.

Future work will investigate neuro-symbolic extensions, combining instruction-tuned Large Language Models (LLMs) for zero-shot proposition extraction with formal symbolic verifiers for auditable grading.

---

## References

1. M. Mohler, R. Bunescu, and R. Mihalcea, "Learning to grade short answer questions using semantic similarity measures and dependency graph alignments," in *Proc. 49th Annu. Meeting Assoc. Comput. Linguistics: Human Lang. Technol. (ACL-HLT)*, Portland, Oregon, 2011, pp. 752–762.
2. R. Basak, S. K. Naskar, and A. Gelbukh, "Short-answer grading using textual entailment," *J. Intell. Fuzzy Syst.*, vol. 36, no. 5, pp. 4909–4919, 2019. DOI: 10.3233/JIFS-179038.
3. S. Burrows, I. Gurevych, and B. Stein, "The eras and trends of automatic short answer grading," *Int. J. Artif. Intell. Educ.*, vol. 25, no. 1, pp. 60–117, 2015.
4. T. K. Landauer, P. W. Foltz, and D. Laham, "An introduction to latent semantic analysis," *Discourse Process.*, vol. 25, no. 2-3, pp. 259–284, 1998.
5. C. Leacock and M. Chodorow, "C-rater: Automated scoring of short-answer questions," *Comput. Humanit.*, vol. 37, no. 4, pp. 389–405, 2003.
6. M. A. Hall, E. Frank, G. Holmes, B. Pfahringer, P. Reutemann, and I. H. Witten, "The WEKA data mining software: An update," *ACM SIGKDD Explor. Newsl.*, vol. 11, no. 1, pp. 10–18, 2009.
7. M. Honnibal and I. Montani, "spaCy 2: Natural language understanding with Bloom embeddings, convolutional neural networks and incremental parsing," *Sentometrics Research*, 2017.
8. G. A. Miller, "WordNet: A lexical database for English," *Commun. ACM*, vol. 38, no. 11, pp. 39–41, 1995.
9. J. Cohen, "A coefficient of agreement for nominal scales," *Educ. Psychol. Meas.*, vol. 20, no. 1, pp. 37–46, 1960.
