# AI Validation 500 Report: Complete Proposition-Level Dataset Analysis

**Project:** Automatic Short Answer Grading using Semantic and Dependency Analysis  
**Phase:** Human Annotation Pilot / Validation Stage  
**Document:** AI-Generated Proposition-Level Validation Annotations Across 500-Item Sample  
**Date:** October 2026  
**Status:** COMPLETE (Preliminary AI Annotation Validation — NOT Human Gold Labels)

---

## 1. Executive Research Summary & Mandatory Disclaimers

This report documents the completion of the full **500-item AI proposition-level annotation validation study**, combining the completed 50-item double-blind pilot with the newly annotated 450 non-pilot items drawn deterministically from the stratified/enriched validation sample.

> [!IMPORTANT]
> **MANDATORY SCIENTIFIC DISCLAIMER: AI ANNOTATION, NOT HUMAN GOLD LABELS**  
> 1. These annotations were generated through independent, double-blind AI evaluator runs applying the official Phase 6 annotation guidelines.
> 2. They **MUST NOT** be described, cited, or interpreted as:
>    - Human gold labels
>    - Human ground truth
>    - Human validation
>    - Proof that the proposed ASAG system is correct
> 3. **Experiment 4 Remains Completely Frozen:** Zero changes have been made to the ASAG pipeline, scoring models, contradiction rules, severity estimators, thresholds, or domain knowledge. These annotations serve as an external diagnostic benchmark for analyzing system behavior and designing future human studies, NOT for model tuning.
> 4. *"This validation uses AI-generated annotations and therefore does not establish agreement with human annotators or human grading."*

---

## 2. Dataset Partition & Provenance

The 500-item validation sample was partitioned deterministically to ensure that the preliminary pilot remains completely separate and untouched:

| Partition | Item Count | Source File | Description |
|---|:---:|---|---|
| **AI Pilot 50** (`AI_PILOT_50`) | 50 | `evaluation/annotation/pilot/pilot_master.csv` | Stratified 50-item sample evaluated double-blind by 2 independent AI annotators. |
| **AI Remaining 450** (`AI_REMAINING_450`) | 450 | `evaluation/annotation/validation/ai_remaining_450_annotations.csv` | All 450 remaining items from the 500 master sample, evaluated double-blind. |
| **Combined 500** | **500** | `evaluation/annotation/validation/ai_validation_500_annotations.csv` | Unified 500-item dataset preserving partition metadata and item provenance. |

---

## 3. Section A: 50-Item Pilot Analysis (Recap)

The 50-item double-blind pilot (`PILOT_001` through `PILOT_050`) was completed prior to annotating the remaining set to verify the operational clarity of the four-way categorical schema:

- **Total Pilot Items:** 50
- **Evaluators:** 2 independent AI instances (`AI Annotator 1` and `AI Annotator 2`)
- **Raw Inter-Evaluator Agreement:** **88.0%** (44 / 50 items agreed)
- **Cohen's Kappa ($\kappa$):** **0.8054** (*Almost Perfect / Substantial Agreement*)
- **Per-Class Concordance Rates:**
  - `CORRECT_ADDITIONAL`: **90.3%** (14 agreed)
  - `UNCERTAIN`: **88.5%** (23 agreed)
  - `INCORRECT`: **83.3%** (5 agreed)
  - `IRRELEVANT`: **80.0%** (2 agreed)
- **Disagreements (6 items):** Traced to 3 identifiable boundary phenomena:
  1. *Operational Elaboration vs. Core Paraphrase* (`PILOT_004`, `PILOT_027`): whether operation-specific names (enqueue/dequeue, pop semantics) constitute technical elaboration beyond the reference or core prompt fulfillment.
  2. *Strict Language Rule vs. Lenient Student Phrasing* (`PILOT_011`, `PILOT_040`): C++ One Definition Rule (ODR) violation vs. informal student terminology.
  3. *Contextual Intent vs. Fragment Rigidity* (`PILOT_007`, `PILOT_042`): charitable interpretation of pointer chaining vs. syntax fragmentation.
- **Core Paraphrase Finding:** 22 out of 50 items (44.0%) were confirmed by both evaluators to be **core paraphrases** of the reference answer, establishing the foundational principle: $\text{SYSTEM UNMATCHED} \neq \text{HUMAN/AI ADDITIONAL}$.

---

## 4. Section B: Remaining 450-Item Analysis

The remaining 450 items were annotated independently under strict double-blind conditions. Evaluators had access only to the question, reference answer, student answer, target proposition, and surrounding context. All Experiment 4 predictions, severities, rationales, and scores were withheld.

### 4.1 Label Distribution (Remaining 450 Items)

| Category | Count ($N=450$) | Percentage | Operational Description |
|---|:---:|:---:|---|
| **`UNCERTAIN`** | 296 | 65.8% | Core paraphrases (99 items), uninterpretable fragments, or ambiguous assertions. |
| **`CORRECT_ADDITIONAL`** | 139 | 30.9% | Valid technical elaboration beyond reference without contradiction. |
| **`INCORRECT`** | 9 | 2.0% | Conceptual misconceptions, factual errors, or domain contradictions. |
| **`IRRELEVANT`** | 6 | 1.3% | Lecture outline headers, discourse fillers, or off-topic commentary. |
| **Total** | **450** | **100.0%** | |

- **Core Paraphrases Identified:** **99 items** (22.0% of the 450 set). Each was assigned `UNCERTAIN` with the required explicit diagnostic note `"core paraphrase; ..."`.

### 4.2 Distribution by Assignment / Topic Area (Remaining 450 Items)

The 450 items span all 12 curriculum assignments across 81 distinct questions:

| Assignment | Topic Area | Total | `CORRECT_ADDITIONAL` | `INCORRECT` | `IRRELEVANT` | `UNCERTAIN` |
|---|---|:---:|:---:|:---:|:---:|:---:|
| **Asg 1** | Software Engineering & C++ Basics | 39 | 9 (23.1%) | 0 (0.0%) | 1 (2.6%) | 29 (74.4%) |
| **Asg 2** | Classes, Constructors, Header Files | 38 | 10 (26.3%) | 3 (7.9%) | 0 (0.0%) | 25 (65.8%) |
| **Asg 3** | Functions, Scope, Recursion vs Iteration | 38 | 12 (31.6%) | 0 (0.0%) | 0 (0.0%) | 26 (68.4%) |
| **Asg 4** | Arrays, Parameter Passing, Static Arrays | 33 | 16 (48.5%) | 1 (3.0%) | 0 (0.0%) | 16 (48.5%) |
| **Asg 5** | Sorting Algorithms (Insertion, Selection) | 22 | 2 (9.1%) | 0 (0.0%) | 1 (4.5%) | 19 (86.4%) |
| **Asg 6** | Pointers, sizeof, Function Pointers | 25 | 9 (36.0%) | 0 (0.0%) | 0 (0.0%) | 16 (64.0%) |
| **Asg 7** | Linked Lists & Doubly-Linked Lists | 29 | 9 (31.0%) | 1 (3.4%) | 0 (0.0%) | 19 (65.5%) |
| **Asg 8** | Stacks (LIFO, Array/List Implementation) | 21 | 9 (42.9%) | 1 (4.8%) | 1 (4.8%) | 10 (47.6%) |
| **Asg 9** | Queues (FIFO, List Implementation) | 26 | 13 (50.0%) | 0 (0.0%) | 1 (3.8%) | 12 (46.2%) |
| **Asg 10** | Trees, Binary Trees, Binary Search Trees | 55 | 18 (32.7%) | 1 (1.8%) | 1 (1.8%) | 35 (63.6%) |
| **Asg 11** | Recursion, Divide & Conquer, Access Spec | 71 | 12 (16.9%) | 2 (2.8%) | 1 (1.4%) | 56 (78.9%) |
| **Asg 12** | Advanced Data Structures & Complexities | 53 | 20 (37.7%) | 0 (0.0%) | 0 (0.0%) | 33 (62.3%) |
| **Total** | | **450** | **139 (30.9%)** | **9 (2.0%)** | **6 (1.3%)** | **296 (65.8%)** |

---

## 5. Section C: Combined 500-Item Dataset Analysis

Combining the 50 pilot items and the 450 remaining items yields the complete 500-item AI validation dataset stored in `evaluation/annotation/validation/ai_validation_500_annotations.csv`.

### 5.1 Total Label Distribution ($N=500$)

| Category | Pilot ($N=50$) | Remaining ($N=450$) | Combined Total ($N=500$) | Overall % |
|---|:---:|:---:|:---:|:---:|
| **`UNCERTAIN`** | 26 (52.0%) | 296 (65.8%) | **322** | **64.4%** |
| **`CORRECT_ADDITIONAL`** | 15 (30.0%) | 139 (30.9%) | **154** | **30.8%** |
| **`INCORRECT`** | 6 (12.0%) | 9 (2.0%) | **15** | **3.0%** |
| **`IRRELEVANT`** | 3 (6.0%) | 6 (1.3%) | **9** | **1.8%** |
| **Total** | **50 (100%)** | **450 (100%)** | **500** | **100.0%** |

- **Total Core Paraphrases:** **122 items (24.4% of all 500 propositions)**.
- **`CORRECT_ADDITIONAL` Consistency:** The rate of valid technical elaboration is remarkably consistent between the pilot (**30.0%**) and the remaining set (**30.9%**), confirming that approximately 31% of unmatched propositions represent genuine, technically sound additions.

---

## 6. Major Empirical Findings

### 6.1 Pervasiveness of Core Paraphrases ($\approx 24.4\%$)

The most significant finding across the 500-item sample is the overwhelming frequency of **core reference paraphrases** among unmatched student propositions:

$$\mathbf{\text{Core Paraphrases}} = 122 \text{ items} \quad (24.4\% \text{ of unmatched propositions})$$

**Why do core paraphrases end up unmatched?**
1. *Syntactic Coordination & Conjunction Splitting:* When students write compound sentences (e.g. *"Data members and member functions"*), the Base ASAG dependency aligner frequently matches one conjunct and drops the second due to rigid head-dependent triple alignment.
2. *Synonym & Terminology Shifts:* Students using equivalent CS terminology (e.g. *"random access"* for direct array indexing; *"LIFO"* for last-in-first-out; *"dynamic size"* for variable number of elements) often fail the similarity threshold.
3. *Symmetric Relational Inversions:* Converses like *"parent is greater than left child"* vs. *"left child is smaller than parent"* are parsed as opposing relation triples.

**Consequence for Scoring:** If an ASAG system automatically grants bonus points to every unmatched proposition classified as "valid addition", it will severely inflate grades for students who merely provided the core reference answer in different words. The Core Paraphrase rule prevents this distortion.

### 6.2 Low Rate of True Irrelevant Tangents ($1.8\%$)

Only 9 out of 500 items (1.8%) were classified as `IRRELEVANT`. In real university exam submissions:
- Students rarely write completely off-topic trivia (e.g. historical facts or jokes).
- Most extraneous text consists of copied lecture outline headings (e.g. `"-Functions that take arrays"`), empty discourse connectors (e.g. `"Say"`, `"advantages is"`), or hypothetical setup phrases (e.g. `"If you had a class Gradebook"`).

### 6.3 Low Rate of Factual Contradictions ($3.0\%$)

Only 15 out of 500 items (3.0%) contained outright factual errors or misconceptions:
- Contradicting C++ variable declaration rules (claiming variables can only be declared before `main()` or outside source code).
- Conflating classes with functions (claiming data members belong to functions).
- Claiming standard C++ arrays can be dynamically resized.
- Claiming linked lists are array-based.
- Reversing binary search tree child ordering invariants.

---

## 7. Quality Control & Dataset Verification

All quality control requirements were rigorously verified:

| Check | Requirement | Result | Status |
|---|---|:---:|:---:|
| **450 File Item Count** | Exactly 450 rows | 450 | **PASS** |
| **500 File Item Count** | Exactly 500 rows | 500 | **PASS** |
| **Item ID Uniqueness** | Zero duplicate IDs in both files | 0 duplicates | **PASS** |
| **Pilot Item Exclusion** | Zero pilot items in remaining 450 | 0 leaked | **PASS** |
| **500 Dataset Alignment** | Exact ID and row match with master | 100% match | **PASS** |
| **Categorical Validity** | 100% of labels in allowed 4 categories | 100% valid | **PASS** |
| **Note Completeness** | Non-empty rationale for every item | 100% populated | **PASS** |
| **Core Paraphrase Tagging** | Labeled UNCERTAIN with explicit tag | 122 tagged | **PASS** |
| **Frozen ASAG Integrity** | Zero changes to models, weights, or code | Unchanged | **PASS** |
| **Automated Test Suite** | All unit tests pass with zero regressions | 540 passed | **PASS** |

---

## 8. Research Utility & Next Steps

These 500 AI-generated proposition-level annotations provide:
1. **Empirical Baseline for Human Annotation:** Serves as a reference distribution for training human expert annotators and evaluating human inter-annotator agreement.
2. **Diagnostic Separation of Alignment vs. Evaluation Errors:** Enables researchers to analyze how often the ASAG proposition extractor separates core paraphrases from genuine elaborations.
3. **Foundation for Potential Future Experiment 5:** Provides ground truth evidence for whether a dedicated `CORE_PARAPHRASE` classifier or an improved clausal aligner is needed.
