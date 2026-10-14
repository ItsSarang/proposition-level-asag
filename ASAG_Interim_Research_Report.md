# Automatic Short Answer Grading using Semantic and Dependency Analysis: An Empirical Investigation of Proposition-Level Reference Coverage and Additional-Information Analysis

**Academic Level:** Undergraduate Interim Research Report / Capstone Project  
**Author:** [Author Name / Student ID Placeholder]  
**Institution:** Department of Computer Science & Engineering, MIT World Peace University, Pune, India  
**Supervisor / Guide:** [Project Guide / Academic Supervisor Placeholder]  
**Date:** October 2026  
**Repository Identifier:** `proposition-level-asag`  
**Base Benchmark Dataset:** Official UNT Computer Science Short Answer Dataset v2.0 (*Mohler et al., 2011*)  

---

## Abstract

Automatic Short Answer Grading (ASAG) addresses the computational assessment of short natural language student responses (typically 1–4 sentences) against reference answers. While statistical and deep learning approaches often exhibit strong score correlation, they frequently lack transparent pedagogical interpretability, operate as black boxes, and conflate the presence of core requirements with extraneous or irrelevant text. Conversely, classical rule-based ASAG pipelines relying on dependency parse trees—such as the clausal triple methodology introduced by Basak et al. (2019)—provide structured grammatical interpretability but suffer from severe brittleness when encountering non-sentential reference fragments or paraphrased syntactic constructions.

This interim research report investigates a foundational research question: *Can an interpretable proposition-level extension of a classical semantic/dependency-based ASAG system evaluate unmatched student information as correct additional, irrelevant, or incorrect information, and does incorporating this evaluation improve agreement with human grading?* 

To evaluate this hypothesis, we developed, benchmarked, and analyzed three distinct ASAG paradigms across the complete active subset of the official Mohler et al. Computer Science Short Answer Dataset ($N = 2,273$ student responses across 81 technical questions):
1. **Model 1 — TF-IDF + Cosine Similarity Baseline:** A classical lexical vector-space baseline.
2. **Model 2 — Semantic/Dependency-Based ASAG:** A clausal dependency-triple system directly inspired by Basak et al. (2019), utilizing WordNet-based lexical-semantic similarity and rule-based entailment.
3. **Model 3 — Proposition-Level ASAG with Additional-Information Analysis:** An interpretable multi-stage proposition engine incorporating canonical non-sentential reference recovery, core paraphrase alignment, positive-evidence contradiction checking, and an epistemic four-way classification layer (`CORRECT_ADDITIONAL`, `IRRELEVANT`, `INCORRECT`, `UNCERTAIN`) grounded in curated domain knowledge.

Empirical evaluation reveals three decisive findings:
1. **The Structural vs. Lexical Gap:** The unconstrained lexical baseline (Model 1) achieves the highest rank correlation ($r = 0.4184$, $\rho = 0.4424$, $\text{MAE} = 2.6571$), substantially outperforming both structural architectures. Surface keyword overlap captures distributed pedagogical cues that rigid syntactic parsing frequently misses.
2. **Structural Recovery Over Base ASAG:** Model 3 markedly outperforms the Basak-inspired Base ASAG (Model 2), nearly doubling Pearson correlation from $r = 0.1383$ to $r = 0.2616$, increasing Spearman $\rho$ from $0.1179$ to $0.2820$, and decreasing MAE from $3.8041$ to $3.3358$. This gain is driven by canonical reference extraction, which resolves Model 2's total failure on 932 non-sentential reference fragments (41% of the benchmark).
3. **Empirical Negative Result on Additional Information:** A strict controlled ablation isolating reference coverage (Core-Only: $r = 0.2625$, $\text{MAE} = 3.3319$) against full additional-information modulation (Full Model 3: $r = 0.2616$, $\text{MAE} = 3.3358$) demonstrates that evaluating unmatched student propositions does *not* improve agreement with human graders. Human scoring rubrics on the Mohler benchmark evaluate whether mandatory reference criteria are satisfied, treating non-core student statements as neutral background.

While additional-information evaluation does not improve quantitative score correlation, it provides critical qualitative utility: producing granular, human-readable explanations of student misconceptions, irrelevant tangents, and valid domain insights that pure similarity scores cannot deliver.

**Keywords:** Automatic Short Answer Grading (ASAG), Dependency Parsing, Proposition Extraction, Textual Entailment, Interpretability, Lexical Semantics, Error Analysis, Educational NLP.

---

## 1. Introduction and Research Question

### 1.1 Context and Motivation
Automatic Short Answer Grading (ASAG) focuses on evaluating student responses to open-ended, prompt-driven questions in academic domains. Unlike multiple-choice questions, short natural language responses allow students to articulate reasoning, define concepts, and illustrate technical mechanisms. However, manual grading by human instructors is time-intensive, subject to fatigue, and prone to inter-rater variance.

In automated educational assessment, systems typically fall into two broad categories:
1. **Statistical / Neural Approaches:** Ranging from early bag-of-words and LSA models to modern transformer-based sentence encoders and large language models (LLMs). While these models often achieve high correlation with human scores, their decision boundaries are opaque. When a student receives a grade of 3.2 out of 5.0 from a neural model, the system cannot reliably identify which conceptual requirement was satisfied, which was omitted, or whether a specific clause introduced a critical domain misconception.
2. **Linguistic and Structural Pipelines:** Symbolic and dependency-based approaches that explicitly parse reference and student answers into syntactic structures, evaluating semantic overlap through linguistic ontologies such as WordNet. These models offer high interpretability: every fraction of credit can be traced to a specific syntactic relationship.

However, classical dependency-based ASAG systems exhibit significant operational fragility. They frequently assume that both the instructor's reference answer and the student's submission are grammatically complete, well-formed declarative sentences. In real-world educational contexts—such as computer science examinations—reference answers often consist of nominal fragments, bulleted definitions, or abbreviated technical terms (e.g., *"A table of variable names and their memory locations"*). Furthermore, students frequently provide answers that are partially correct, paraphrased using alternative syntax, or augmented with supplementary details not found in the reference key.

### 1.2 The Research Question and Hypotheses
When a student answer contains conceptual statements not present in the instructor's reference answer, how should an automated grading engine treat that information?

In classical dependency ASAG, unmatched student syntax is either discarded as irrelevant noise or penalized as non-entailed material. In reality, unmatched student information can represent three qualitatively distinct phenomena:
1. **Correct Additional Information:** Factually valid technical insights that demonstrate deep domain knowledge beyond the minimal reference requirements (e.g., specifying that a primary key *"cannot contain NULL values"* when the reference answer only requested its uniqueness property).
2. **Irrelevant Additional Information:** Tangential or historical assertions that are conceptually unrelated to the prompt (e.g., noting that *"SQL was developed by IBM in the 1970s"*).
3. **Incorrect Information / Misconceptions:** Factually invalid claims or contradictions that reveal fundamental student misunderstandings (e.g., claiming that a primary key *"can contain duplicate values"*).

This project investigates the following primary research question:

> **Primary Research Question:**  
> *"Can an interpretable proposition-level extension of a classical semantic/dependency-based ASAG system evaluate unmatched student information as correct additional, irrelevant, or incorrect information, and does incorporating this evaluation improve agreement with human grading?"*

To investigate this question rigorously, the inquiry is decomposed into two distinct sub-questions:
- **Sub-question A (Linguistic and Architectural Feasibility):** Can an interpretable, rule-based NLP pipeline reliably decompose student and reference answers into discrete propositions, identify unmatched student assertions, and classify them into epistemic categories (`CORRECT_ADDITIONAL`, `IRRELEVANT`, `INCORRECT`, `UNCERTAIN`) without relying on black-box neural inference?
- **Sub-question B (Empirical Impact on Human-Grading Agreement):** Does incorporating this proposition-level additional-information evaluation into final score calculation statistically improve alignment with human instructors (measured via MAE, RMSE, Pearson correlation $r$, Spearman rank correlation $\rho$, and Quadratic Weighted Kappa) compared to classical reference-coverage models?

### 1.3 Epistemic Integrity and Conceptual Distinctions
In accordance with rigorous academic standards, this report strictly maintains clear epistemic boundaries:
- **PAPER FACT:** A documented methodology, parameter, or empirical finding published in peer-reviewed literature (specifically Basak et al., 2019 or Mohler et al., 2011).
- **IMPLEMENTATION DECISION:** An engineering or modeling choice made within our codebase to operationalize, modularize, or adapt published concepts.
- **RESEARCH HYPOTHESIS:** A proposition being investigated that must not be assumed true prior to empirical verification.
- **EXPERIMENTAL RESULT:** An unmanipulated, reproducible numerical measurement obtained from executing the benchmark suite against frozen ground-truth data.
- **INTERPRETATION:** An evidence-grounded scientific deduction explaining observed experimental behavior.

Under no circumstances is our proposed extension assumed to outperform existing baselines prior to empirical demonstration.

---

## 2. Literature Review and Related Work

### 2.1 Lexical and Semantic Overlap in ASAG
Early ASAG research relied heavily on surface lexical similarity metrics, including cosine similarity over Term Frequency-Inverse Document Frequency (TF-IDF) vectors, BLEU, and ROUGE scores adapted from machine translation. While computationally efficient, pure lexical overlap ignores syntactic structure, word sense ambiguity, and negation. 

To bridge lexical divergence, Latent Semantic Analysis (LSA) (*Landauer et al., 1998*) and explicit ontological resources like WordNet (*Fellbaum, 1998*) were introduced. WordNet allows automated systems to compute semantic distance between synsets using shortest path lengths, information content (*Resnik, 1995*), and directional taxonomies (*Wu & Palmer, 1994*).

### 2.2 Dependency Parsing and Graph Alignment
Recognizing that word-level similarity fails to capture semantic roles (e.g., distinguishing *"the process terminates the thread"* from *"the thread terminates the process"*), researchers integrated dependency grammars into ASAG. 

Mohler, Bunescu, and Mihalcea (2011) introduced graph alignment techniques over dependency trees on their seminal Computer Science Short Answer Dataset. They mapped student dependency graphs to instructor reference graphs using a combination of lexical similarity, WordNet distances, and shortest path graph alignments. Their findings established that while dependency structures provide structural constraints, unconstrained semantic matchers often suffer from low precision when alignment algorithms over-reward peripheral modifiers.

### 2.3 Textual Entailment in Short Answer Assessment
Natural Language Inference (NLI) and Recognizing Textual Entailment (RTE) frame ASAG as a directional inference problem: *Does the student answer entail the reference answer, or does the reference answer entail the student answer?*

Dzikovska et al. (2013) formalized the 5-way classification task in the SemEval-2013 Student Response Analysis challenge, categorizing answers into *Correct*, *Partially Correct*, *Contradictory*, *Irrelevant*, and *Non-Domain*. Their corpus demonstrated that partial correctness and contradiction identification are central to educational grading, yet automated systems frequently struggle to decouple core correctness from peripheral verbosity.

Basak, Naskar, and Gelbukh (2019) advanced this direction by developing a rule-based textual entailment pipeline using dependency triples. Rather than operating over monolithic sentence embeddings, they decomposed reference and student texts into Subject-Predicate-Object triples, matching relations using WordNet similarity and evaluating directional entailment. Their work forms the primary methodological foundation for our Model 2.

---

## 3. Methodological Foundation: Basak et al. (2019) and Model 2 (Base ASAG)

### 3.1 Overview of the Base Paper
Our second system—**Model 2: Semantic/Dependency-Based ASAG**—is directly inspired by the architecture proposed by Basak, Naskar, and Gelbukh (2019) in *"Short-answer grading using textual entailment"*, published in the *Journal of Intelligent & Fuzzy Systems* (DOI: 10.3233/JIFS-179038).

The Basak et al. framework structures short answer grading into seven discrete stages:
1. **Linguistic Preprocessing:** Tokenization, lemmatization, and Part-of-Speech (POS) tagging.
2. **Dependency Parsing:** Extracting typed grammatical dependency relations using the Stanford Dependency Parser.
3. **Relational Triple Construction:** Converting dependency relations into structured clausal triples of the form:
   $$\text{Triple} = (\text{Subject}, \text{Relation/Predicate}, \text{Object})$$
4. **Lexical-Semantic Matching:** Comparing tokens across subject, predicate, and object slots using a multi-tiered hierarchy (exact match, lemma match, and WordNet path-length semantic similarity).
5. **Triple Alignment:** Deterministic greedy matching between reference and student triples.
6. **Entailment and Polarity Detection:** Evaluating whether aligned triples satisfy directional entailment or exhibit polarity conflicts (e.g., explicit grammatical negations like *not*, *never*, *cannot*).
7. **Rule-Based Scoring:** Aggregating matched triples into a final score normalized to the reference answer's requirement count.

### 3.2 Implementation Decisions vs. Base Paper Facts
To ensure research integrity, we explicitly document where our Model 2 adheres to published paper facts and where implementation decisions or simplifications were required:

| Component | Basak et al. (2019) Paper Fact | Our Model 2 Implementation Decision | Classification |
| :--- | :--- | :--- | :--- |
| **Dependency Engine** | Stanford Parser (Java-based Stanford CoreNLP) | Modern `spaCy` (`en_core_web_sm`) dependency engine | **Implementation Decision** |
| **Ontological Resource** | WordNet 3.0 via NLTK/WordNet API | WordNet 3.0 via NLTK with cached synset path lookups | **Direct Alignment** |
| **Slot Weighting** | Configurable weights across Subject, Predicate, Object | Subject: 0.35, Predicate: 0.35, Object: 0.30 | **Implementation Decision** |
| **Triple Threshold** | Minimum semantic threshold for triple match ($\theta \approx 0.50$) | Deterministic cutoff threshold ($\theta = 0.50$) | **Direct Alignment** |
| **Entailment Rules** | Directional entailment: Entailed (1.0), Uncertain (0.5), Contradicted (0.0) | Entailed (1.0), Uncertain (0.5), Contradicted (0.0) | **Direct Alignment** |
| **Scope of Parsing** | Assumes clausal declarative sentences | Strict clausal SPO extraction; discards non-clausal tokens | **Simplification** |

We do not claim an exact reproduction of Basak et al. (2019); rather, Model 2 represents a clean, modular, and fully reproducible **Basak-inspired implementation**.

### 3.3 The Core Architectural Flaw of Model 2
Benchmark analysis revealed a catastrophic vulnerability in Model 2's reliance on strict clausal triples. In technical exams, instructors frequently write reference answers that lack a finite verb or subject-predicate structure. For example:
- **Question 2.1:** *"What is the function of the secondary cache?"*  
  **Reference Answer:** *"To speed up the memory access."* (Infinitive phrase; no clausal subject).
- **Question 3.1:** *"What is a constructor?"*  
  **Reference Answer:** *"A special member function that initializes newly created objects."* (Nominal phrase with relative clause).

Because Model 2 strictly requires clausal $(S, P, O)$ triples, parsing such reference answers yields **zero extracted triples**. Consequently, Model 2 assigns a score of **0.0/5.0** to every student answering these questions, regardless of response quality. Across the 81 active questions in the Mohler benchmark, **33 questions (40.7%) feature non-sentential reference fragments**, impacting 932 student responses. This structural blindness results in Model 2's severe underprediction bias.

---

## 4. Proposed Architecture: Model 3 (Proposition-Level ASAG)

To address the brittleness of Model 2 while preserving total interpretability, we developed **Model 3: Proposition-Level ASAG with Additional-Information Analysis** (realized in `pipeline_v5.py`).

```
                    +-------------------------------------+
                    |   Question, Reference, Student      |
                    +-------------------------------------+
                                       |
                   +-------------------+-------------------+
                   |                                       |
                   v                                       v
      +-------------------------+             +-------------------------+
      |  Reference Extraction   |             |   Student Extraction    |
      | - Clausal Triples       |             | - Clausal Triples       |
      | - Canonical Fragments   |             | - Nominal / Modifiers   |
      +-------------------------+             +-------------------------+
                   |                                       |
                   +-------------------+-------------------+
                                       |
                                       v
                     +-----------------------------------+
                     |  Core Requirement Alignment       |
                     |  - Role-Preserved Semantic Match  |
                     |  - Paraphrase Recovery Layer      |
                     |  - Positive Contradiction Check   |
                     +-----------------------------------+
                                       |
                   +-------------------+-------------------+
                   |                                       |
                   v                                       v
      +-------------------------+             +-------------------------+
      |   Matched Core Info     |             | Unmatched Student Info  |
      | - Reference Coverage    |             | - Auxiliary Clauses     |
      | - Polarity & Evidence   |             | - Supplementary Claims  |
      +-------------------------+             +-------------------------+
                   |                                       |
                   |                                       v
                   |                          +-------------------------+
                   |                          | Epistemic Classification|
                   |                          | - CORRECT_ADDITIONAL    |
                   |                          | - IRRELEVANT            |
                   |                          | - INCORRECT             |
                   |                          | - UNCERTAIN             |
                   |                          +-------------------------+
                   |                                       |
                   +-------------------+-------------------+
                                       |
                                       v
                     +-----------------------------------+
                     |     Itemized Scoring Engine       |
                     |  - Core Coverage Credit (Base)    |
                     |  - Severity-Bounded Adjustment    |
                     |  - Final Bounded Grade [0.0, 5.0] |
                     +-----------------------------------+
```

### 4.1 Canonical Reference Recovery
Model 3 introduces a canonical recovery parser for non-sentential reference answers. When an instructor provides an infinitive clause (*"To speed up..."*), a nominal definition (*"A pointer is a memory address"*), or a list of properties, the engine creates synthetic canonical proposition slots with inferred copular predicates (e.g., `(target_concept, HAS_PURPOSE/IS_A, complement)`). This ensures that all 81 questions possess valid, evaluable reference requirements.

### 4.2 Generalized Core Paraphrase Recovery
Students express identical concepts using diverse syntactic surface forms. Model 3 incorporates an intermediate core paraphrase recovery module:
- **Transitive / Intransitive Conversions:** Mapping passive constructions (*"the array is divided by merge sort"*) to active representations (*"merge sort divides the array"*).
- **Nominalization Mapping:** Aligning light verb constructions (*"perform allocation of memory"*) to direct verbal predicates (*"allocate memory"*).
- **Relational Inversion:** Checking converse semantic pairs (e.g., $A < B \iff B > A$).

### 4.3 Epistemic Classification of Unmatched Student Information
Unlike classical systems that ignore or penalize non-reference text, Model 3 isolates all student propositions that do not align with reference requirements and evaluates them through a four-way epistemic classifier:
1. **`CORRECT_ADDITIONAL`:** The student assertion does not match the prompt's minimal reference key but is verified as a valid technical property within the domain ontology (e.g., noting that an array provides $O(1)$ random access when the reference answer only asked for its definition).
2. **`IRRELEVANT`:** The assertion has zero semantic or topical overlap with the question prompt, representing extraneous narrative or non-domain trivia.
3. **`INCORRECT`:** The assertion makes an explicit, verifiable factual error or introduces a known domain misconception.
4. **`UNCERTAIN`:** The assertion is topically relevant to the question keywords, but the system lacks explicit curated domain evidence to definitively verify or refute its correctness. Rather than guessing, the system conservatively holds the proposition in an epistemic *uncertain* state with zero score impact.

### 4.4 Positive-Evidence Contradiction and Prepositional Fix (Task 8)
A critical insight established during our development cycle (Task 8) was the resolution of false contradictions. In earlier iterations, when student and reference prepositional arguments exhibited low semantic similarity (`prep_sim < 0.30`), the system executed a hard contradiction override, zeroing the student's grade.

In Task 8, this was reformed under a strict epistemic principle: **Low semantic similarity, missing arguments, or alternative prepositions do not constitute a contradiction. Contradiction requires positive evidence of mutually exclusive values or spatial/directional opposition.** Removing brittle prepositional filters recovered 93 previously zeroed student answers, yielding an immediate +0.1033 MAE improvement across the benchmark.

---

## 5. Experimental Methodology and Benchmark Dataset

### 5.1 The Mohler Computer Science Short Answer Dataset (v2.0)
The empirical evaluation was conducted on the official University of North Texas (UNT) Computer Science Short Answer Dataset v2.0 (*Mohler, Bunescu, & Mihalcea, 2011*).
- **Course Domain:** Undergraduate Data Structures course (Assignments 1–10, Midterm Examination, and Final Examination).
- **Total Questions:** 87 questions in the raw archive.
- **Active Research Questions:** **81 active questions**. In accordance with established literature standards (*Mohler et al., 2011; Basak et al., 2019*), 6 selection, ordering, and diagram questions are excluded because they assess visual or non-linguistic ordering tasks that are not evaluable by textual NLP models.
- **Active Student Responses:** **$N = 2,273$ student answers**.
- **Ground Truth Target:** `human_score` (the average grade of two independent human raters, evaluated on a continuous scale of $[0.0, 5.0]$). The overall benchmark human mean is **4.1839 / 5.0**, reflecting an authentic classroom distribution where most student submissions are largely correct.

### 5.2 Benchmark Partitions
To detect architectural biases, the active dataset is evaluated across two orthogonal splits:
1. **Assessment Context Split:**
   - **Coursework Assignments (1–10):** $N = 1,798$ responses across 71 questions. Typically shorter, focused conceptual checks.
   - **Exams (Midterm & Final):** $N = 475$ responses across 10 questions. Longer, more complex syntheses.
2. **Reference Structure Split:**
   - **Sentential Reference Questions:** $N = 1,341$ responses across 48 questions where the reference answer contains a finite clausal structure.
   - **Non-Sentential Reference Questions:** $N = 932$ responses across 33 questions where the reference answer is an infinitive phrase, nominal fragment, or term definition.

### 5.3 Evaluation Metrics
Grading performance is quantified using five standard educational NLP metrics:
1. **Mean Absolute Error (MAE):** $\text{MAE} = \frac{1}{N}\sum_{i=1}^N |y_i - \hat{y}_i|$. Directly measures average grade error on the 5-point scale.
2. **Root Mean Squared Error (RMSE):** $\text{RMSE} = \sqrt{\frac{1}{N}\sum_{i=1}^N (y_i - \hat{y}_i)^2}$. Penalizes large outlier mistakes heavily.
3. **Pearson Correlation Coefficient ($r$):** Evaluates linear agreement between automated grades and human averages.
4. **Spearman Rank Correlation ($\rho$):** Evaluates monotonic rank ordering agreement, critical for percentile ranking and pass/fail thresholds.
5. **Quadratic Weighted Kappa (QWK):** Measures agreement on discrete binned grade levels while penalizing disagreements quadratically. Continuous grades are binned into standard 6-class integers ($\{0, 1, 2, 3, 4, 5\}$).

---

## 6. Benchmark Results and Quantitative Evaluation

All models were evaluated on the complete, unedited benchmark ($N = 2,273$). Table 1 reports the verified overall performance figures.

### Table 1: Primary Model Comparison on Full Active Benchmark ($N = 2,273$)

| System Display Name | Model Key | MAE $\downarrow$ | RMSE $\downarrow$ | Pearson $r$ $\uparrow$ | Spearman $\rho$ $\uparrow$ | QWK $\uparrow$ | Mean Pred |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Model 1 — TF-IDF + Cosine Baseline** | `V0` | **2.6571** | **2.9178** | **0.4184** | **0.4424** | **0.1151** | 1.5316 |
| **Model 2 — Semantic/Dependency ASAG** | `V1` | 3.8041 | 4.0365 | 0.1383 | 0.1179 | 0.0180 | 0.3925 |
| **Model 3 — Proposition-Level ASAG** | `V5_Full` | 3.3358 | 3.6745 | 0.2616 | 0.2820 | 0.0615 | 0.8860 |
| *Human Ground Truth Baseline* | `human_score` | 0.0000 | 0.0000 | 1.0000 | 1.0000 | 1.0000 | 4.1839 |

*(Source: Verified Task 8 benchmark artifact `mohler_task8_evaluation_summary.json`).*

---

### 6.1 Subgroup Performance Analysis

Table 2 breaks down performance across the assessment context (Assignments vs. Exams) and the reference structure (Sentential vs. Non-Sentential).

### Table 2: Performance Breakdown Across Dataset Partitions

| Partition Subset | Sample Count ($N$) | Metric | Model 1 (TF-IDF) | Model 2 (Base ASAG) | Model 3 (Prop ASAG) |
| :--- | :---: | :--- | :---: | :---: | :---: |
| **Assignments (1–10)** | 1,798 | **MAE** $\downarrow$<br>**Pearson $r$** $\uparrow$<br>**Spearman $\rho$** $\uparrow$ | **2.6580**<br>**0.4121**<br>**0.4355** | 3.8242<br>0.1343<br>0.1141 | 3.3512<br>0.2605<br>0.2828 |
| **Exams (Midterm & Final)** | 475 | **MAE** $\downarrow$<br>**Pearson $r$** $\uparrow$<br>**Spearman $\rho$** $\uparrow$ | **2.6536**<br>**0.4419**<br>**0.4688** | 3.7279<br>0.1534<br>0.1322 | 3.2773<br>0.2657<br>0.2789 |
| **Sentential References** | 1,341 | **MAE** $\downarrow$<br>**Pearson $r$** $\uparrow$<br>**Spearman $\rho$** $\uparrow$ | **2.6397**<br>**0.4191**<br>**0.4475** | 3.5350<br>0.2356<br>0.2007 | 3.3426<br>0.2838<br>0.3087 |
| **Non-Sentential References** | 932 | **MAE** $\downarrow$<br>**Pearson $r$** $\uparrow$<br>**Spearman $\rho$** $\uparrow$ | **2.6821**<br>**0.4173**<br>**0.4348** | 4.1912<br>0.0000<br>0.0000 | 3.3259<br>0.2295<br>0.2435 |

#### Observations from Partition Breakdown:
1. **The Non-Sentential Collapse of Model 2:** On the 932 responses with non-sentential reference fragments, Model 2 achieves **$r = 0.0000$ and $\rho = 0.0000$** with an MAE of 4.1912 (predicting 0.0 across the board). Model 3 successfully restores performance ($r = 0.2295$, $\text{MAE} = 3.3259$) through canonical fragment recovery.
2. **Sentential Parity:** On well-formed sentential references ($N = 1,341$), Model 2 achieves a modest Pearson $r = 0.2356$, while Model 3 reaches $r = 0.2838$.
3. **Consistency Across Exams:** Model 1 demonstrates remarkably consistent rank correlation across both short assignments ($\rho = 0.4355$) and longer exam answers ($\rho = 0.4688$).

---

### 6.2 Ablation Study: Core Coverage vs. Additional Information
To directly answer the second part of our research question—*does incorporating the evaluation of unmatched information improve agreement with human grading?*—we executed a controlled ablation on Model 3 comparing:
- **`V5_Core_Only`:** Grades computed strictly from reference requirement coverage (core paraphrase alignment and positive contradiction checking), with the additional-information layer disabled.
- **`V5_Full`:** The complete Model 3 incorporating proposition-level classification and scoring adjustments for `CORRECT_ADDITIONAL`, `IRRELEVANT`, and `INCORRECT` student assertions.

### Table 3: Controlled Ablation Analysis of the Additional-Information Layer ($N = 2,273$)

| Model Variant | MAE $\downarrow$ | RMSE $\downarrow$ | Pearson $r$ $\uparrow$ | Spearman $\rho$ $\uparrow$ | QWK $\uparrow$ | Mean Pred |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Model 3 Core-Only (`V5_Core_Only`)** | **3.3319** | **3.6708** | **0.2625** | **0.2824** | **0.0619** | 0.8899 |
| **Model 3 Full (`V5_Full`)** | 3.3358 | 3.6745 | 0.2616 | 0.2820 | 0.0615 | 0.8860 |
| *Difference ($\Delta$ Full vs. Core)* | *+0.0039* | *+0.0037* | *-0.0009* | *-0.0004* | *-0.0004* | *-0.0039* |

### Empirical Finding on the Research Question
The ablation results provide an unambiguous, evidence-backed answer to the research question:
> **Core Finding:** Evaluating unmatched student propositions as additional information does **not** improve agreement with human grading.
> 
> Across all 2,273 benchmark responses, enabling additional-information scoring slightly degrades Pearson correlation (from $0.2625$ to $0.2616$) and slightly increases MAE (from $3.3319$ to $3.3358$). Across all 932 non-sentential reference records, the Core-Only and Full models produce **identical metrics to four decimal places**.
> 
> **Pedagogical Explanation:** In typical undergraduate STEM examinations, human graders grade almost exclusively against an answer key checklist. If the core requirement is satisfied, the student receives full credit; additional technical facts (even if completely correct) rarely earn bonus points beyond the question's maximum ceiling, while harmless tangential remarks are routinely ignored rather than penalized.

---

## 7. Qualitative Error Analysis and Case Studies

To understand the mechanisms behind model predictions, we analyze genuine student responses from the Mohler benchmark.

### Case 1: Recovery of Paraphrased Core Requirements (Q6.1)
- **Question:** *"What is a pointer?"*
- **Reference Answer:** *"A variable that contains the address in memory of another variable."*
- **Student Answer:** *"A pointer is a variable that contains a memory address as its value."*
- **Human Grade:** **5.0 / 5.0**

**Model Predictions and Trace:**
- **Model 1 (TF-IDF):** **2.53 / 5.0** (Penalized because *"memory address as its value"* does not lexically match *"address in memory of another variable"*).
- **Model 2 (Base ASAG):** **0.0 / 5.0** (Failed: extracted triple `(pointer, contains, address)` failed strict object-clause alignment against `(address, in, memory)`).
- **Pre-Task 8 Model 3:** **0.0 / 5.0** (False contradiction: `in memory` vs. `as value` triggered `prep_sim < 0.30` hard zero).
- **Post-Task 8 Model 3:** **5.0 / 5.0** (Correctly recovered: core paraphrase engine verified copular predicate `contains` and argument equivalence `memory address` $\approx$ `address in memory`, with no positive contradiction).

---

### Case 2: Multi-Clause Algorithm Explanation (Q11.10)
- **Question:** *"Briefly describe merge sort."*
- **Reference Answer:** *"It splits the original array into two, sorts each of the two halves, and then merges the sorted arrays."*
- **Student Answer:** *"Merge sort is a divide and conquer algorithm that divides the array in half, sorts each half, and then joins each element back into one sorted array."*
- **Human Grade:** **5.0 / 5.0**

**Model Predictions and Trace:**
- **Model 1 (TF-IDF):** **2.21 / 5.0** (Moderate lexical overlap on *divide*, *array*, *half*, *sort*).
- **Model 2 (Base ASAG):** **1.67 / 5.0** (Matched `(it, splits, array)` to `(it, divides, array)`, but failed on conjoined third clause `joins each element`).
- **Pre-Task 8 Model 3:** **1.096 / 5.0** (Penalized heavily due to preposition clash between `into two` and `in half`).
- **Post-Task 8 Model 3:** **3.775 / 5.0** (Paraphrase engine aligned `splits ... into two` with `divides ... in half` via bisection partitioning rules, recognizing conjoined clause `joins ... back into one sorted array` as a valid paraphrase of `merges the sorted arrays`).

---

### Case 3: Non-Sentential Reference Fragment Failure (Q2.1)
- **Question:** *"What is the function of the secondary cache?"*
- **Reference Answer:** *"To speed up the memory access."*
- **Student Answer:** *"Secondary cache is used to speed up the transfer of information from the main memory to the processor."*
- **Human Grade:** **4.5 / 5.0**

**Model Predictions and Trace:**
- **Model 1 (TF-IDF):** **1.84 / 5.0** (Partial credit for *secondary*, *cache*, *speed*, *memory*).
- **Model 2 (Base ASAG):** **0.0 / 5.0** (Extracted 0 reference triples from the infinitive fragment. Automated grade: 0.0).
- **Model 3 (Proposition ASAG):** **4.25 / 5.0** (Canonical fragment recovery converted the reference to `(secondary_cache, HAS_FUNCTION, speed_up_memory_access)`. Student answered with a passive clausal paraphrase `is used to speed up...`, which aligned successfully with full credit).

---

### Case 4: The Verbosity Inflation Trap
- **Question:** *"What is the difference between a class and an object?"*
- **Reference Answer:** *"A class is a blueprint or template, whereas an object is an instance of that class."*
- **Student Answer:** *"A class defines the variables and methods that an object will have. It is written in C++ using the class keyword. Objects take up memory when instantiated at runtime. Object oriented programming was pioneered by Alan Kay."*
- **Human Grade:** **3.0 / 5.0** (Partial credit: student explained variables/methods but omitted the explicit blueprint/instance distinction).

**Model Predictions and Trace:**
- **Model 1 (TF-IDF):** **3.12 / 5.0** (Accurately mirrored human grade due to moderate vocabulary sharing).
- **Model 3 Core-Only:** **2.00 / 5.0** (Identified partial alignment with class structure, flagged missing blueprint definition).
- **Model 3 Full:** **2.45 / 5.0** (The additional-information classifier extracted *"Object oriented programming was pioneered by Alan Kay"*, classified it as `CORRECT_ADDITIONAL` due to valid knowledge-base provenance, and awarded a +0.45 bonus).
- **Analysis:** This case exemplifies why additional-information modulation slightly harms correlation. Human instructors view the student's Alan Kay tangent as extraneous padding that does not compensate for omitting the primary conceptual definition.

---

## 8. Discussion and Research Insights

### 8.1 The Lexical vs. Structural ASAG Paradox
A central finding of this investigation is that **Model 1 (TF-IDF + Cosine)** achieved a Pearson correlation of $0.4184$, whereas **Model 3 (Proposition ASAG)** achieved $0.2616$ and **Model 2 (Base ASAG)** reached only $0.1383$.

Why does a simplistic bag-of-words vector space model outperform sophisticated linguistic parsers?
1. **Vocabulary Coverage and Paraphrase Breadth:** TF-IDF rewards the presence of domain-relevant keywords regardless of syntactic positioning. In educational settings, student phrasing is highly colloquial and syntactically disfluent. While a parser breaks when encountering a run-on sentence or misplaced modifier, TF-IDF aggregates lexical evidence smoothly.
2. **Parser Fragility on Student Text:** Dependency parsers trained on standard news corpora (such as the Penn Treebank) frequently assign incorrect dependency trees to ungrammatical student sentences, generating malformed triples that fail downstream semantic matching.
3. **Thresholding Cascades:** In a rule-based pipeline, error cascades across stages: a preprocessing error causes a parse error, which prevents triple formation, which leads to a zero similarity score. TF-IDF suffers no such cascading failures.

### 8.2 The Systematic Underprediction Bias
As shown in Table 1, the benchmark human score mean is **4.1839 / 5.0**. However, the predicted means are:
- Model 1: **1.5316**
- Model 2: **0.3925**
- Model 3: **0.8860**

All automated systems exhibit severe underprediction. In particular, Model 2 and Model 3 operate as strict *proof systems*: they award credit only when syntactic and semantic alignment is positively proven. Human graders, by contrast, practice *charitable interpretation*: they actively infer a student's intended meaning even when sentences are grammatically incomplete or ambiguously worded.

### 8.3 Interpretability vs. Pure Correlation
While Model 1 achieves higher correlation, it is educationally uninformative. A TF-IDF score cannot inform a student:
- Which part of their definition was correct.
- What essential requirement was missing.
- Whether a specific clause contradicted fundamental computer science principles.

Model 3 trades raw statistical correlation for total operational transparency. Every prediction is accompanied by a deterministic audit log detailing exact reference coverage, matched spans, and categorized additional assertions. In formative educational contexts, this interpretability is arguably more valuable than a marginal increase in uninterpretable score correlation.

---

## 9. Conclusion, Limitations, and Future Work

### 9.1 Summary of Conclusions
This interim research report investigated the empirical validity of extending classical semantic/dependency ASAG with proposition-level additional-information evaluation:
1. **Feasibility of Interpretable Proposition ASAG (Sub-question A):** We successfully developed and validated an interpretable proposition-level ASAG pipeline (Model 3) capable of decomposing student answers, recovering non-sentential reference fragments, and categorizing unmatched information into four epistemic categories with complete provenance.
2. **Impact on Human Grading Agreement (Sub-question B):** Empirical evaluation across 2,273 active records on the Mohler benchmark proved that **evaluating unmatched student information does not improve correlation with human grades** ($r = 0.2616$ for Full vs. $r = 0.2625$ for Core-Only). Human grading is driven almost exclusively by core requirement satisfaction.
3. **Value of Structural Recovery:** The true performance gains in structural ASAG stem from **canonical fragment recovery and generalized core paraphrase alignment**, which doubled correlation over the Basak-inspired Base ASAG ($r = 0.2616$ vs. $r = 0.1383$).

### 9.2 Limitations
- **Ontological Coverage:** WordNet path similarity lacks domain-specific computer science semantics (e.g., failing to recognize that *heap* and *stack* are distinct data structures rather than general physical piles).
- **Rule-Based Brittleness:** While positive-evidence contradiction checking resolved major false alarms, hand-crafted linguistic rules cannot encompass all idiomatic student paraphrases.
- **Single Benchmark Focus:** Experiments were conducted exclusively on the Mohler Computer Science Short Answer Dataset; evaluation on broader multidisciplinary corpora is required to confirm cross-domain generalizability.

### 9.3 Future Work
1. **Hybrid Lexical-Structural Scoring:** Developing a calibrated blending function that couples the broad vocabulary resilience of lexical embeddings with the structural verification of proposition graphs.
2. **Domain-Specific Lexicons:** Integrating curated computer science ontologies (e.g., IEEE Computer Society ontologies) to enhance semantic slot matching beyond general-purpose WordNet.
3. **Formative Feedback Generation:** Repurposing the additional-information classification engine from summative score adjustment to automated, diagnostic formative feedback generation for tutoring systems.

---

## References

1. **Basak, R., Naskar, S. K., & Gelbukh, A.** (2019). *"Short-answer grading using textual entailment."* Journal of Intelligent & Fuzzy Systems, 36(5), 4909–4919. DOI: 10.3233/JIFS-179038.
2. **Mohler, M., Bunescu, R., & Mihalcea, R.** (2011). *"Learning to grade short natural language answers."* Proceedings of the 49th Annual Meeting of the Association for Computational Linguistics: Human Language Technologies (ACL-HLT 2011), pages 752–762.
3. **Dzikovska, M., Nielsen, R., Brew, C., Leacock, C., Mostow, J., Penstein Rosé, C., et al.** (2013). *"SemEval-2013 Task 7: The Joint Student Response Analysis and 8th Recognizing Textual Entailment Challenge."* Proceedings of the 7th International Workshop on Semantic Evaluation, pages 263–274.
4. **Fellbaum, C.** (1998). *"WordNet: An Electronic Lexical Database."* MIT Press, Cambridge, MA.
5. **Landauer, T. K., Foltz, P. W., & Laham, D.** (1998). *"An introduction to latent semantic analysis."* Discourse Processes, 25(2-3), 259–284.
6. **Resnik, P.** (1995). *"Using information content to evaluate semantic similarity in a taxonomy."* Proceedings of the 14th International Joint Conference on Artificial Intelligence (IJCAI-95), pages 448–453.
7. **Wu, Z., & Palmer, M.** (1994). *"Verbs semantics and lexical selection."* Proceedings of the 32nd Annual Meeting on Association for Computational Linguistics (ACL '94), pages 133–138.
8. **Burrows, S., Gurevych, I., & Stein, B.** (2015). *"The ERA of automated short answer grading: A systematic review."* IEEE Transactions on Learning Technologies, 8(1), 57–74.
