# Phase 6: Annotation Sampling Report

**Project:** Automatic Short Answer Grading using Semantic and Dependency Analysis  
**Phase:** Phase 6 — Human Proposition-Level Annotation Dataset Preparation  
**Document:** Sampling Methodology and Population Audit Report  
**Source Benchmark:** Frozen Experiment 4 Output on the UNT CS Dataset (*Mohler et al., 2011*)  
**Random Seed:** `42` (Deterministic, Fully Reproducible)  
**Date:** October 2026  

---

## 1. Executive Summary

This report documents the sampling methodology, eligibility audit, and stratification protocol used to construct the Phase 6 Human Proposition-Level Validation Dataset. 

From an initial population of **4,695 unmatched propositions** extracted across 2,273 active student answers in the frozen Experiment 4 benchmark:
- **4,660 propositions** (**99.25%**) were verified as syntactically clean and **ELIGIBLE** for human annotation.
- **35 propositions** (**0.75%**) were excluded due to unambiguous extraction defects (truncated notations, isolated symbols, or decoding artifacts).
- A stratified, representative sample of **exactly 500 propositions** was deterministically drawn using random seed `42`.
- The sample achieves **100% coverage of all 81 active questions** and all 12 coursework assignments and exams, while deliberately enriching the rare `INCORRECT` class (all 64 detected misconceptions included) to provide statistical validation power for contradiction severity analysis.

---

## 2. Source Population Overview

The source population consists of all proposition clauses identified by the Experiment 4 pipeline as unmatched against the instructor reference answers:
- **Dataset**: UNT Computer Science Short Answer Dataset v2.0 (*Mohler et al., 2011*)
- **Active Student Answers**: $2,273$ answers
- **Active Questions**: $81$ questions (Assignments 1–10, Exams 11–12)
- **Answers with Unmatched Information**: $2,114$ answers ($93.00\%$)
- **Total Unmatched Propositions Extracted**: $4,695$ propositions
- **Mean Propositions per Answer**: $2.06$ overall ($2.22$ per answer with unmatched content)
- **Length Distribution**: Character lengths range from $1$ to $172$ characters; word counts range from $1$ to $33$ words.

---

## 3. Eligibility Audit and Ineligible Counts

Before sampling, all $4,695$ proposition candidates underwent an automated structural audit. An item was deemed **ELIGIBLE** only if it constituted an understandable grammatical clause or meaningful technical phrase whose text could be unambiguously located within the student answer context.

| Audit Status | Count | Proportion (%) | Scientific Role |
| :--- | :---: | :---: | :--- |
| **ELIGIBLE** | **4,660** | **99.25%** | Candidate pool for human annotation sampling |
| **INELIGIBLE** | **35** | **0.75%** | Excluded from sampling due to extraction defects |
| **Total Population** | **4,695** | **100.00%** | Full set of Experiment 4 unmatched propositions |

---

## 4. Exclusion Reasons Breakdown

The 35 excluded propositions fell into three unambiguous defect categories:

| Exclusion Reason | Count | % of Ineligible | Description & Representative Examples |
| :--- | :---: | :---: | :--- |
| **UNINTERPRETABLE_FRAGMENT** | **15** | 42.86% | Lone punctuation marks (`")"`, `"["`, `"="`), isolated single auxiliary verbs (`"is"`, `"can"`, `"do"`), or isolated abbreviations (`"Re"`, `"Ex"`) lacking any propositional content. |
| **TRUNCATED_TEXT** | **13** | 37.14% | Syntactically severed tokens or complexity formulas lacking closing delimiters (e.g. `"O(n"`, `"O(log n"`, `"O(nlog(n"`, trailing hyphens like `"-Do"`, `"Inheritance-"`). |
| **OTHER_EXTRACTION_ARTIFACT** | **7** | 20.00% | Character encoding corruption from raw legacy dataset text (e.g. `â€œInstructâ€ `, `doesnâ€™t need`, `points`). |
| **EMPTY_TEXT** | **0** | 0.00% | Zero empty proposition strings were found in the dataset. |
| **MISSING_CONTEXT** | **0** | 0.00% | All propositions matched valid active student records. |
| **DUPLICATE_ARTIFACT** | **0** | 0.00% | Zero identical extraction duplicates within the same answer. |
| **INVALID_SPAN** | **0** | 0.00% | All non-fragment propositions had $\ge 30\%$ token overlap with the student text. |

> [!NOTE]
> **Integrity Guard**: No proposition was excluded because its system classification appeared questionable or because its human answer grade was high/low. Difficult or controversial propositions (e.g. inverted BST ordering statements) were strictly retained as **ELIGIBLE**.

---

## 5. Sampling Methodology

The sampling design balances two competing research objectives:
1. **Representativeness**: Broad benchmark coverage across all 81 questions, coursework assignments, and exams.
2. **Statistical Power on Rare Classes**: Providing sufficient sample size to evaluate the contradiction detector and severity estimator, where population incidence is naturally low ($1.37\%$).

### Sampling Procedure
1. **Seed**: Python `random.seed(42)`.
2. **INCORRECT Class Enrichment (Targeted Inclusion)**:  
   All 64 eligible `INCORRECT` propositions were included in the sample. This guarantees that human annotators will evaluate every single detected misconception across all four severity levels (15 Core, 42 Moderate, 2 Minor, 5 Unresolved).
3. **Question-Stratified Round-Robin for UNCERTAIN and IRRELEVANT**:  
   The remaining 436 slots were split equally between `UNCERTAIN` ($N=218$) and `IRRELEVANT` ($N=218$). To prevent geographic clustering in early questions (such as Q1.1/Q1.2), items were sampled using a round-robin traversal across all 81 questions.
4. **Final Shuffle and Renumbering**:  
   The combined 500 items were deterministically shuffled (`random.seed(42)`) and assigned sequential identifiers `ITEM_001` through `ITEM_500`.

---

## 6. Sample Size and Category Distribution

### Population vs. Sample Comparison

| System-Assigned Classification | Population Count | Population Proportion (%) | Sample Count | Sample Proportion (%) | Sampling Treatment |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **CORRECT_ADDITIONAL** | 0 | 0.00% | 0 | 0.00% | Frozen system output (none existed in benchmark) |
| **UNCERTAIN** | 1,813 | 38.91% | 218 | 43.60% | Round-robin stratified across 81 questions |
| **IRRELEVANT** | 2,783 | 59.72% | 218 | 43.60% | Round-robin stratified across 81 questions |
| **INCORRECT** | 64 | 1.37% | 64 | 12.80% | 100% census of all eligible detected contradictions |
| **Total** | **4,660** | **100.00%** | **500** | **100.00%** | Comprehensive validation dataset |

### Breakdown of Sampled `INCORRECT` Propositions by Severity

| Severity Level | Eligible Population | Sample Count | Inclusion Rate (%) |
| :--- | :---: | :---: | :---: |
| **CORE_CONTRADICTION** | 15 | 15 | 100.0% |
| **MODERATE** | 42 | 42 | 100.0% |
| **MINOR** | 2 | 2 | 100.0% |
| **UNRESOLVED** | 5 | 5 | 100.0% |
| **Total INCORRECT** | **64** | **64** | **100.0%** |

---

## 7. Question and Assignment Coverage

The Phase 6 sampling achieved complete coverage of the active Mohler benchmark:
- **Questions Represented**: **81 out of 81 questions** (**100.0%**)
- **Coursework Assignments (1–10)**: **364 items** (**72.8%**)
- **Examinations (Exams 11–12)**: **136 items** (**27.2%**)

### Item Distribution across Assignments and Exams

| Assignment / Exam Partition | Topic Domain | Sample Count | % of Sample |
| :--- | :--- | :---: | :---: |
| **Assignment 1** | Software Engineering & C++ Prototypes | 42 | 8.4% |
| **Assignment 2** | Pointers, Arrays, and Function Returns | 43 | 8.6% |
| **Assignment 3** | Indexing, Pointer Arithmetic, and Functions | 42 | 8.4% |
| **Assignment 4** | Multidimensional Arrays & Pass-by-Reference | 36 | 7.2% |
| **Assignment 5** | Recursion & Big-O Algorithmic Analysis | 24 | 4.8% |
| **Assignment 6** | Dynamic Memory & Operator Overloading | 28 | 5.6% |
| **Assignment 7** | Linked Lists & Node Pointers | 33 | 6.6% |
| **Assignment 8** | Stacks, Infix-to-Postfix, & Memory Storage | 26 | 5.2% |
| **Assignment 9** | Queues & Breadth-First Data Structures | 31 | 6.2% |
| **Assignment 10** | Binary Search Trees & Tree Traversals | 59 | 11.8% |
| **Exam 11** | Midterm Exam: Classes, Access Specifiers, Trees | 76 | 15.2% |
| **Exam 12** | Final Exam: Comprehensive CS Data Structures | 60 | 12.0% |
| **Total Sample** | Full Active Curriculum | **500** | **100.0%** |

---

## 8. Blinding Audit Confirmation

The generated files were verified via automated programmatic assertion:
1. `annotator_1.csv` and `annotator_2.csv` contain **0 occurrences** of the tokens:
   - `system_label`
   - `system_severity`
   - `system_rationale`
   - `human_score`
   - `human_grade`
2. Neutral column names are used exclusively (`annotator_label`, `annotator_notes`).
3. All 500 rows in both annotator files have empty label and notes cells.
4. Identifiers (`item_id`, `question_id`, `answer_id`, `proposition_id`) allow exact 1-to-1 linkage in `master_annotation_dataset.csv`.

---

## 9. Sampling Limitations

1. **Category Enrichment**:  
   Because `INCORRECT` cases were enriched from $1.37\%$ in the population to $12.80\%$ in the sample, raw sample accuracy must not be confused with population-level prevalence. When computing global performance metrics, researchers must apply post-stratification survey weights ($w_{\text{inc}} = 0.0137 / 0.1280 \approx 0.107$).
2. **Zero Population `CORRECT_ADDITIONAL`**:  
   The system never emitted `CORRECT_ADDITIONAL` during Experiment 4 due to narrow domain rule coverage. Consequently, human annotators may assign `CORRECT_ADDITIONAL` to propositions that the system labeled `UNCERTAIN` or `IRRELEVANT`. This divergence is expected and serves as the primary metric for measuring the system's epistemic conservatism.
