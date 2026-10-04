# Automatic Short Answer Grading using Semantic and Dependency Analysis

## Short Description

This repository houses an undergraduate Natural Language Processing (NLP) / Automated Short Answer Grading (ASAG) research project. The primary deliverable is an interpretable ASAG research engine designed for systematic experimentation, evaluation, and empirical comparison against human grading.

The project investigates classical semantic and dependency-based ASAG methodology (inspired by Basak et al., 2019) and explores a proposition-level extension to assess unmatched student information.

---

## Research Question

> **"Can an interpretable proposition-level extension of a classical semantic/dependency-based ASAG system evaluate unmatched student information as correct additional, irrelevant, or incorrect information, and does incorporating this evaluation improve agreement with human grading?"**

*Note:* This statement is a research hypothesis. The proposed extension is an experimental formulation and must not be assumed to improve grading until verified through empirical evidence.

---

## Research Direction

Conventional reference-based ASAG systems compare student responses against model reference answers. However, student answers often contain information outside the reference answer. Such unmatched information can generally fall into three categories:

1. **Correct additional information** (e.g., valid supplementary facts or elaboration)
2. **Irrelevant additional information** (e.g., off-topic or extraneous facts)
3. **Incorrect or misconception-related information** (e.g., erroneous claims or flawed concepts)

This research investigates whether decomposing and evaluating unmatched student information at the proposition level, and integrating this assessment into a rule-based grading framework, enhances agreement with human grades while maintaining high model interpretability.

---

## Three-System Architecture

To rigorously evaluate the research question, three distinct systems are planned:

### 1. System 1 — Simple Baseline
A surface-level text similarity baseline:
```
Student Answer + Reference Answer
       │
       ▼
     TF-IDF
       │
       ▼
Cosine Similarity
       │
       ▼
 Baseline Score
```

### 2. System 2 — Base ASAG
A modular, interpretable implementation inspired by the classical methodology of Basak et al. (2019):
```
Question + Reference Answer + Student Answer
       │
       ▼
 Preprocessing
       │
       ▼
Semantic / Lexical Analysis (WordNet, similarity)
       │
       ▼
Dependency Parsing & Triples Extraction
       │
       ▼
    Triple Matching
       │
       ▼
Textual Entailment / Relevance Analysis
       │
       ▼
  Rule-Based Scoring
       │
       ▼
 Base ASAG Grade
```

### 3. System 3 — Proposed ASAG
The experimental extension incorporating proposition-level evaluation of unmatched information:
```
Question + Reference Answer + Student Answer
       │
       ▼
 Base ASAG Analysis
       │
       ├─────────────────────────┐
       ▼                         ▼
Matched Information       Unmatched Student Information
                                 │
                                 ▼
                     Proposition-Level Analysis
                                 │
                                 ▼
                   Evaluate Unmatched Information
                   ├── Correct Additional
                   ├── Irrelevant Additional
                   └── Incorrect / Misconception
                                 │
                                 ▼
                     Incorporate into Scoring
                                 │
                                 ▼
                        Proposed ASAG Grade
```

*Note on Evidence Verification:* The proposed extension uses a small curated domain-knowledge resource to provide positive evidence for selected additional propositions. Uncovered relevant propositions are classified as UNCERTAIN rather than being assumed correct.

---

## Current Implementation Status

**Status: COMPLETE (Stages 0–17 Finalized)**

All planned research stages have been implemented, tested, benchmarked against human grades, diagnosed, and concluded:

- [x] **Stage 0:** Project setup, research question, repository architecture (`GEMINI.md`, `README.md`).
- [x] **Stage 1 & 2:** System 1 (TF-IDF + Cosine similarity baseline) implemented and tested.
- [x] **Stages 3–10:** System 2 (Base ASAG pipeline inspired by Basak et al., 2019):
  - Preprocessing (spaCy POS/lemmatization)
  - Dependency parsing & clausal triple extraction `(subject, predicate, object)`
  - 4-level semantic/lexical matching hierarchy (exact, lemma, POS compatibility, WordNet path similarity)
  - Deterministic one-to-one greedy triple matching
  - Propositional textual entailment & polarity conflict detection
  - Reference coverage rule-based scoring
- [x] **Stages 11–14:** System 3 (Proposed Proposition-Level Extension):
  - Alignment extraction with character-level span provenance (`SpanInfo`)
  - Clausal proposition representation with linguistic arguments
  - Additional-information classification (`CORRECT_ADDITIONAL`, `IRRELEVANT`, `INCORRECT`, `UNCERTAIN`)
  - Configurable additive grading modulation preserving Base ASAG scores
- [x] **Stage 15.1:** Mohler ASAG dataset acquisition, inspection, and ground truth validation (UNT CS v2.0, 2,273 active records).
- [x] **Stage 15.2:** Unified evaluation pipeline and full benchmark run across all 2,273 active records (zero crashes).
- [x] **Stage 16:** Systematic diagnostic error analysis (Four-Quadrant analysis, aggregate proposition statistics, 7 targeted case studies).
- [x] **Stage 17:** Evidence-based scientific conclusions and synthesis report (`reports/research_conclusions.md`).

---

## Empirical Benchmark Summary

Evaluated on the official **UNT Computer Science Short Answer Dataset (Version 2.0)** (Mohler et al., 2011) across all **81 active questions (2,273 student responses)** against the official human average grade (`score_ave`, scale 0.0–5.0):

| Metric | System 1: TF-IDF Cosine Baseline | System 2: Base ASAG (Basak-inspired) | System 3: Proposed ASAG (Untuned) | Human Grader Agreement (Ceiling)\* |
| :--- | :---: | :---: | :---: | :---: |
| **Mean Absolute Error (MAE) ↓** | **2.6571** | 3.7794 | 3.2036 | 0.7263 |
| **Root Mean Squared Error (RMSE) ↓** | **2.9178** | 4.0179 | 3.5101 | 1.2618 |
| **Pearson Correlation ($r$) ↑** | **0.4184** | 0.1419 | 0.1377 | 0.5910 |
| **Spearman Correlation ($\rho$) ↑** | **0.4424** | 0.1177 | 0.0797 | 0.5855 |
| **Quadratic Weighted Kappa (QWK) ↑** | **0.1151** | 0.0191 | 0.0252 | — |

*\*Note: Human agreement ceiling is computed on Assignments 1–10 ($N = 1,721$) where two human graders assigned independent grades.*

### Key Empirical Findings
1. **Proposition Classification Feasibility:** The classifier processed 3,611 unmatched student propositions and assigned labels: `CORRECT_ADDITIONAL` (78.0%), `IRRELEVANT` (21.6%), `INCORRECT` (0.33%), and `UNCERTAIN` (0.03%) with character-level span provenance and zero pipeline crashes. Because the Mohler dataset contains no proposition-level human annotations, these classifications represent system outputs rather than verified ground truth.
2. **Substantial Observed Error Reduction:** Proposed ASAG yielded a substantial observed reduction in absolute error relative to Base ASAG across the full benchmark (MAE $3.78 \to 3.20$, a 15.2% reduction; RMSE $4.02 \to 3.51$), and an 18.5% reduction ($3.51 \to 2.86$) on questions where reference answers contain complete propositions.
3. **Verbosity Sensitivity:** Unweighted additive scoring rewarded rambling answers that introduced peripheral domain terms, degrading Spearman rank correlation ($\rho = 0.118 \to 0.080$).
4. **Syntactic Fragmentation Barrier:** In 33 of 81 questions (40.7%), instructor reference answers were non-sentential fragments (e.g. *"Abstraction and reusability."*), yielding zero extracted propositions and collapsing Base ASAG coverage to 0.0. TF-IDF bag-of-words similarity proved robust to fragments, explaining why it outperformed both dependency-based systems ($r = 0.4184, \rho = 0.4424$).
5. **Research Hypothesis Evidence:** The experiment provides partial and metric-dependent evidence rather than confirmation of the overall research hypothesis.

For full details, see the comprehensive [Research Conclusions Report](reports/research_conclusions.md) and [Diagnostic Error Analysis Report](evaluation/error_analysis/stage16_report.md).

---

## Repository Structure & Reports

```
proposition-level-asag/
├── baseline/                  # System 1: TF-IDF + Cosine similarity baseline
├── base_asag/                 # System 2: Classical dependency-based ASAG pipeline
├── proposed_asag/             # System 3: Proposition-level extension (Stages 11–14)
├── evaluation/
│   ├── dataset/               # Mohler dataset loaders and inspect CLI
│   ├── metrics/               # MAE, RMSE, Pearson r, Spearman rho, QWK
│   ├── runners/               # Unified execution runners for all 3 systems
│   ├── experiments/           # Benchmark CLI runner
│   ├── results/               # CSV predictions and summary metrics
│   ├── error_analysis/        # Stage 16 diagnostic analyzer & report
│   └── stage15_2_report.md    # Initial benchmark report
├── reports/
│   ├── stage10a_base_validation_report.md
│   ├── stage11_report.md      # Proposition alignment provenance
│   ├── stage12_report.md      # Proposition-level representations
│   ├── stage13_report.md      # Additional-information classification
│   ├── stage14_report.md      # Proposed grading mechanism
│   └── research_conclusions.md # Stage 17 final synthesis & conclusions
└── tests/                     # 311 passing unit tests across all stages
```

---

## Development Stages Overview

All 18 defined stages are complete:

- [x] **Stage 0:** Project structure + `GEMINI.md` + `README.md`
- [x] **Stage 1:** TF-IDF + cosine similarity baseline
- [x] **Stage 2:** Baseline validation on DEMO dataset
- [x] **Stage 3:** Base ASAG linguistic preprocessing
- [x] **Stage 4:** Dependency parsing & root repair
- [x] **Stage 5:** Dependency triples extraction
- [x] **Stage 6:** Semantic & lexical relationships (WordNet hierarchy)
- [x] **Stage 7:** Triple matching (deterministic greedy alignment)
- [x] **Stage 8:** Textual entailment & polarity analysis
- [x] **Stage 9:** Base ASAG scoring (reference coverage)
- [x] **Stage 10:** Base ASAG pipeline integration
- [x] **Stage 11:** Matched vs unmatched proposition alignment
- [x] **Stage 12:** Proposition-level representation & span tracking
- [x] **Stage 13:** Additional-information classification
- [x] **Stage 14:** Proposed grading mechanism
- [x] **Stage 15:** Benchmark evaluation against human grades (Mohler dataset)
- [x] **Stage 16:** Qualitative and diagnostic error analysis
- [x] **Stage 17:** Evidence-based research conclusions

---

## Research Integrity Note

- **Demo Data vs. Research Data:** Any small synthetic or demo examples used during early stages are strictly for code verification and pipeline sanity testing. They are explicitly labelled `DEMO DATA — NOT RESEARCH DATA` and must never be treated as empirical evidence or benchmark statistics.
- **No Fabricated Evidence:** Experimental results, dataset metrics, performance figures, and paper claims are never fabricated or simulated.
- **Verified Claims:** Claims regarding performance improvements or methodological reproduction will only be made when supported by transparent, reproducible experiments on public ASAG benchmark datasets.
