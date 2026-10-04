# Human Annotation Pilot: Sampling Report (50-Item Study)

**Project:** Automatic Short Answer Grading using Semantic and Dependency Analysis  
**Phase:** Human Annotation Pilot Validation Study  
**Document:** Sampling Methodology and Representation Report  
**Source Dataset:** 500-Item Stratified/Enriched Validation Sample (`evaluation/annotation/master_annotation_dataset.csv`)  
**Random Seed:** `42` (Deterministic, Fully Reproducible)  
**Date:** October 2026  

---

## 1. Executive Summary

This report documents the selection methodology and distributional properties of the **50-item pilot dataset** created for the human annotation study.

The pilot sample was drawn **exclusively from the pre-existing 500-item stratified/enriched validation sample** (`master_annotation_dataset.csv`). The underlying 500-item validation sample was preserved unmodified, and the wider 4,695-proposition population was not resampled.

### Key Sampling Statistics
- **Source Dataset**: `evaluation/annotation/master_annotation_dataset.csv`
- **Source Sample Size**: $N = 500$
- **Pilot Sample Size**: $N = 50$ (exactly $10.0\%$ of the validation sample)
- **Random Seed**: `42`
- **Questions Covered**: **40 unique questions** across all 12 curriculum units
- **Coursework vs. Exam Ratio**: 38 Assignment items ($76.0\%$) and 12 Exam items ($24.0\%$)
- **System-Category Coverage**: Mirrors the 500-item sample proportions (`IRRELEVANT`: 44%, `UNCERTAIN`: 42%, `INCORRECT`: 14%), while ensuring coverage across all four contradiction severity tiers.

---

## 2. Selection Methodology

The pilot items were selected using deterministic stratification:
1. **Target Allocation**:
   - `INCORRECT`: 7 items ($14.0\%$ of pilot, matching the $12.8\%$ proportion in the 500-item master).
   - `UNCERTAIN`: 21 items ($42.0\%$ of pilot, matching $43.6\%$ in master).
   - `IRRELEVANT`: 22 items ($44.0\%$ of pilot, matching $43.6\%$ in master).
   - `CORRECT_ADDITIONAL`: 0 items ($0.0\%$, adhering to the frozen Experiment 4 output where no system predictions existed).
2. **Severity Stratification for `INCORRECT`**:  
   To ensure that the pilot validates human agreement on varying degrees of conceptual error, the 7 `INCORRECT` items were stratified across all four severity tiers:
   - 2 `CORE_CONTRADICTION` items (high-impact defining property conflicts),
   - 3 `MODERATE` items (secondary property value clashes),
   - 1 `MINOR` item (peripheral formatting/naming discrepancy),
   - 1 `UNRESOLVED` item (unclassified contradiction).
3. **Diverse Question Stratification**:  
   For `UNCERTAIN` and `IRRELEVANT` propositions, candidates were sampled using round-robin question traversal across diverse computer science topics.
4. **Deterministic Ordering**:  
   The selected items were deterministically shuffled (`Random(42)`) and assigned sequential identifiers `PILOT_001` through `PILOT_050`.

---

## 3. Category Distribution Comparison

The table below demonstrates that the 50-item pilot faithfully reflects the distribution of the 500-item validation sample:

| System-Assigned Category | 500-Item Master Count | Master Proportion (%) | 50-Item Pilot Count | Pilot Proportion (%) |
| :--- | :---: | :---: | :---: | :---: |
| **IRRELEVANT** | 218 | 43.60% | **22** | **44.00%** |
| **UNCERTAIN** | 218 | 43.60% | **21** | **42.00%** |
| **INCORRECT** | 64 | 12.80% | **7** | **14.00%** |
| **CORRECT_ADDITIONAL** | 0 | 0.00% | **0** | **0.00%** |
| **Total** | **500** | **100.00%** | **50** | **100.00%** |

### Breakdown of Pilot `INCORRECT` Items by Severity

| Severity Level | 500-Item Master | 50-Item Pilot Count | % of Pilot Incorrect |
| :--- | :---: | :---: | :---: |
| **CORE_CONTRADICTION** | 15 | **2** | 28.57% |
| **MODERATE** | 42 | **3** | 42.86% |
| **MINOR** | 2 | **1** | 14.29% |
| **UNRESOLVED** | 5 | **1** | 14.29% |
| **Total Incorrect** | **64** | **7** | **100.00%** |

---

## 4. Question, Assignment, and Exam Coverage

The 50 pilot items span **40 unique questions** across all 12 coursework assignments and exams:

| Assignment / Exam Unit | Topic Area | Items in Pilot | Proportion (%) |
| :--- | :--- | :---: | :---: |
| **Assignment 1** | Software Engineering & C++ Prototypes | 3 | 6.0% |
| **Assignment 2** | Pointers, Arrays, and Function Returns | 5 | 10.0% |
| **Assignment 3** | Indexing, Pointer Arithmetic, and Functions | 4 | 8.0% |
| **Assignment 4** | Multidimensional Arrays & Pass-by-Reference | 3 | 6.0% |
| **Assignment 5** | Recursion & Big-O Algorithmic Analysis | 2 | 4.0% |
| **Assignment 6** | Dynamic Memory Allocation & Classes | 3 | 6.0% |
| **Assignment 7** | Linked Lists & Node Operations | 4 | 8.0% |
| **Assignment 8** | Stacks, Memory Frames, & Infix-to-Postfix | 5 | 10.0% |
| **Assignment 9** | Queues & Breadth-First Structures | 5 | 10.0% |
| **Assignment 10** | Binary Search Trees & Tree Traversals | 4 | 8.0% |
| **Exam 11** | Midterm Examination: Classes, Trees, Recursion | 5 | 10.0% |
| **Exam 12** | Final Examination: Comprehensive CS Concepts | 7 | 14.0% |
| **Total** | Full Curriculum | **50** | **100.0%** |

- **Assignments 1–10 (Coursework)**: **38 items** (**76.0%**)
- **Exams 11–12 (Midterm / Final)**: **12 items** (**24.0%**)

This distribution matches the real-world coursework/exam ratio of the Mohler benchmark (75.7% coursework vs. 24.3% exams).

---

## 5. Double-Blind Verification Confirmation

The pilot files were checked via automated programmatic assertions:
1. `pilot_annotator_1.csv` and `pilot_annotator_2.csv` contain zero system predictions, severities, rationales, or human grades.
2. Columns `annotator_label` and `annotator_note` are 100% empty across all 50 data rows.
3. Both annotator files share identical `pilot_id` keys (`PILOT_001` to `PILOT_050`) and row ordering.
4. `pilot_master.csv` preserves system predictions and provenance for later adjudication without exposing them to annotators.
