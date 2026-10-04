# Mohler ASAG Dataset Acquisition and Inspection Report (Stage 15.1)

**Project:** Automatic Short Answer Grading using Semantic and Dependency Analysis  
**Repository:** `proposition-level-asag`  
**Phase:** Stage 15.1 — Dataset Acquisition, Setup, and Inspection  
**Date:** October 2026  
**Status:** COMPLETE (Dataset acquired, verified, processed, tested, and documented)

---

## 1. Dataset Provenance and Official Source

### 1.1 Source Repository & Distribution
- **Dataset Name:** UNT Computer Science Short Answer Dataset (Version 2.0)
- **Release Date:** April 22, 2011
- **Original Authors:** Rada Mihalcea and Michael Mohler
- **Institution:** Language and Information Technologies (LIT) Lab, University of North Texas / University of Michigan
- **Official Download URL:** [https://web.eecs.umich.edu/~mihalcea/downloads/ShortAnswerGrading_v2.0.zip](https://web.eecs.umich.edu/~mihalcea/downloads/ShortAnswerGrading_v2.0.zip)
- **Local Raw Storage:** `data/raw/mohler_asag/` (stored unmodified in version control/local repository).

### 1.2 Primary Published Foundations
The dataset was published and analyzed across two foundational ASAG papers:
1. **Mohler, Bunescu & Mihalcea (2011):**  
   "Learning to Grade Short Answer Questions using Semantic Similarity Measures and Dependency Graph Alignments."  
   *Proceedings of the 49th Annual Meeting of the Association for Computational Linguistics (ACL-HLT 2011)*, Portland, Oregon, pp. 752–760.
2. **Mohler & Mihalcea (2009):**  
   "Text-to-text Semantic Similarity for Automatic Short Answer Grading."  
   *Proceedings of the 12th Conference of the European Chapter of the Association for Computational Linguistics (EACL 2009)*, Athens, Greece, pp. 567–575.

---

## 2. Dataset Facts Verified from Downloaded Data

Every claim in this section has been directly verified through programmatic inspection of the raw downloaded files in `data/raw/mohler_asag/data/`.

### 2.1 File Structure and Layout
The archive unpacks into the following layout:
- `data/docs/files`: Manifest of 87 questions (`1.1` to `12.10`).
- `data/raw/questions`: 87 raw questions.
- `data/raw/answers`: 87 raw reference answers.
- `data/raw/x.y`: Raw student answers for question `x.y` (one per line).
- `data/sent/x.y`: Sentence-segmented student answers (LingPipe `<STOP>` tokens).
- `data/scores/x.y/ave`: Official average human score.
- `data/scores/x.y/me`: Scores from Grader 2 (Michael Mohler).
- `data/scores/x.y/other`: Scores from Grader 1 (Course TA).
- `data/parses/stanford.trip/`: Legacy Stanford dependency parses.
- `data/annotations/x.y.z`: Node-level entity alignment files.

### 2.2 Record Counts and Question Partitions
- **Total Questions in Dataset:** 87 questions.
- **Active Questions:** 81 questions.
- **Ignored Questions:** 6 questions prefixed with `#` in `data/docs/files` (`#4.6`, `#4.7`, `#8.5`, `#9.5`, `#9.7`, `#12.3`). Per the author README, these are selection/ordering questions omitted in all published work.
- **Total Student Answers:** 2,442 across all 87 questions.
- **Active Student Answers:** 2,273 across 81 active questions (matching Mohler et al. ACL 2011 exactly: 2,273 answers).
- **Ignored Student Answers:** 169 across the 6 selection/ordering questions.
- **Line Count Consistency:** 0 line count mismatches across all 87 questions between student answers, `ave`, `me`, and `other` score files.

### 2.3 Assignment Breakdown Table
| Assignment / Exam | Total Questions | Active Questions | Total Answers | Active Answers | Mean Ground Score (`ave`) | Grading Scale |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Assignment 01** | 7 | 7 | 203 | 203 | 3.909 | 0–5 |
| **Assignment 02** | 7 | 7 | 210 | 210 | 3.924 | 0–5 |
| **Assignment 03** | 7 | 7 | 217 | 217 | 4.329 | 0–5 |
| **Assignment 04** | 7 | 5 | 210 | 150 | 4.050 | 0–5 |
| **Assignment 05** | 4 | 4 | 112 | 112 | 4.214 | 0–5 |
| **Assignment 06** | 7 | 7 | 182 | 182 | 4.330 | 0–5 |
| **Assignment 07** | 7 | 7 | 182 | 182 | 4.209 | 0–5 |
| **Assignment 08** | 7 | 6 | 189 | 162 | 4.185 | 0–5 |
| **Assignment 09** | 7 | 5 | 189 | 135 | 4.456 | 0–5 |
| **Assignment 10** | 7 | 7 | 168 | 168 | 4.292 | 0–5 |
| **Exam 11** | 10 | 10 | 300 | 300 | 4.177 | 0–10 (norm 0–5) |
| **Exam 12** | 10 | 9 | 280 | 252 | 4.230 | 0–10 (norm 0–5) |
| **Total / Overall** | **87** | **81** | **2,442** | **2,273** | **4.184** | **0–5** |

*Note:* Assignments 1–3 contain 21 questions and 630 answers, matching the subset used in Mohler & Mihalcea (EACL 2009).

### 2.4 Human Graders and Score Scales
- **Graders:** Two human evaluators graded every answer:
  - Grader 1 (`other`): Graduate teaching assistant for the course.
  - Grader 2 (`me`): Michael Mohler.
- **Assignments 1–10 (1,721 active answers):**
  - Both graders scored on a discrete integer 0–5 scale: $\{0, 1, 2, 3, 4, 5\}$.
  - In 100% of cases (1,721 / 1,721 records), `score_ave == (score_me + score_other) / 2.0` exactly ($|ave - (me+other)/2| < 10^{-5}$).
  - Grader 2 (`me`): Mean = 3.944, Std = 1.449.
  - Grader 1 (`other`): Mean = 4.413, Std = 0.934.
  - Inter-grader Pearson correlation $r = 0.5910$.
  - Inter-grader Spearman rank correlation $\rho = 0.5855$.
  - Inter-grader MAE = 0.7263, RMSE = 1.2618.
- **Exams 11–12 (552 active answers):**
  - Graded on a 0–10 integer scale.
  - Normalized by authors to the 0–5 scale reported in `score_ave` using half-point rounding increments $\{0.0, 0.5, 1.0, \dots, 5.0\}$.

### 2.5 Score Distribution (Active 2,273 records)
| Score (`score_ave`) | Count | Percentage | Cumulative |
| :---: | :---: | :---: | :---: |
| **0.0** | 23 | 1.0% | 1.0% |
| **0.5** | 3 | 0.1% | 1.1% |
| **1.0** | 11 | 0.5% | 1.6% |
| **1.5** | 43 | 1.9% | 3.5% |
| **2.0** | 91 | 4.0% | 7.5% |
| **2.5** | 120 | 5.3% | 12.8% |
| **3.0** | 159 | 7.0% | 19.8% |
| **3.5** | 184 | 8.1% | 27.9% |
| **4.0** | 212 | 9.3% | 37.2% |
| **4.5** | 306 | 13.5% | 50.7% |
| **5.0** | 1,121 | 49.3% | 100.0% |

**Key Finding:** The dataset is heavily skewed toward top grades: 49.3% of student answers received a perfect 5.0 score, and 62.8% received $\ge 4.5$.

### 2.6 Text Characteristics and Artifacts
- **Prefixes:** Every single raw line in `data/raw/questions`, `data/raw/answers`, and `data/raw/x.y` begins with the question identifier prefix `f"{clean_id} "`.
- **HTML Artifacts:** 260 student answers contain raw `<br>` HTML tags resulting from the original web submission form.
- **Non-ASCII Characters:** 3 lines across two files (`4.1` lines 10, 25 and `6.1` line 8) contain Windows-1252/mojibake bytes (apostrophes and quotation marks).
- **Missing / Empty Text:** 0 empty questions, 0 empty reference answers, 0 empty student answers.

---

## 3. Source-Reported Facts (Published Literature)

1. **Evaluation Setup in Mohler et al. (ACL 2011):**
   - The authors performed cross-validation leaving one assignment/exam out (12 folds) and question-level leave-one-out cross-validation.
   - Systems were evaluated on Pearson correlation $r$, Spearman rank correlation $\rho$, and Root Mean Squared Error (RMSE) against the average human score (`score_ave`).
2. **Reported Human Agreement:**
   - Mohler et al. reported an inter-annotator Pearson correlation of $r \approx 0.58$ to $0.60$ between the two human graders.
   - This inter-annotator correlation represents the empirical human performance ceiling on this dataset.
3. **No Proposition-Level Ground Truth:**
   - **Crucial Research Fact:** The Mohler ASAG dataset contains **NO proposition-level annotations** (no labels for individual student clauses as correct, irrelevant, or misconception).
   - The ground truth is purely holistic at the answer level.

---

## 4. Implementation Decisions

1. **Non-Destructive Storage:**
   The raw dataset under `data/raw/mohler_asag/` is preserved 100% untouched.
2. **Text Normalization / Cleaning:**
   In `evaluation/dataset/mohler_loader.py`, two text fields are provided for student answers:
   - `student_answer_raw`: The exact text from `data/raw/x.y` with the `x.y ` prefix stripped.
   - `student_answer_cleaned`: The text with `<br>` tags replaced by a space, multiple whitespace collapsed, and stripped. This ensures spaCy receives coherent sentences without HTML noise.
3. **Structured Dataset Products:**
   Four standardized CSV files are generated in `data/processed/mohler_asag/`:
   - `mohler_asag_all.csv`: All 2,442 records across 87 questions.
   - `mohler_asag_active.csv`: The 2,273 active records across 81 questions.
   - `mohler_asag_assignments_1_10.csv`: The 1,721 active assignment records on the uniform 0–5 scale.
   - `mohler_questions.csv`: Summary table of all 87 questions with reference answers and answer counts.
4. **Tooling & Containers:**
   - `MohlerRecord`: Frozen, immutable dataclass representing a single student record.
   - `MohlerDataset`: Immutable container providing convenient filter methods (`filter_active()`, `filter_assignments_1_10()`, `filter_by_question()`, `to_dataframe()`).
   - `MohlerLoader`: Robust loader with fallback for non-ASCII bytes and automated CSV export.
   - `inspect_mohler.py`: Standalone CLI diagnostic script.
   - `test_mohler_dataset.py`: 20 unit tests verifying counts, score arithmetic, cleaning, and roundtrip fidelity.

---

## 5. Scientific Nuances and Experimental Implications for Stage 15

1. **Exam Scale Normalization vs. Uniform Assignment Scale:**
   - Assignments 1–10 (1,721 records) were graded on a clean, uniform 0–5 integer scale.
   - Exams 11–12 (552 records) were originally graded 0–10 and post-hoc rounded to half-points.
   - *Experimental Decision:* We recommend reporting results on both:
     - The standard full active benchmark (2,273 records, matching Mohler 2011).
     - The pure uniform 0–5 subset (Assignments 1–10, 1,721 records) to avoid quantization artifacts.
2. **Evaluation of the Proposition-Level Hypothesis:**
   - Because Mohler provides only holistic answer scores, the proposed extension (Stage 14) will be evaluated on:
     a) Holistic correlation and error metrics against human grades ($r$, $\rho$, MAE, RMSE) compared to Baseline and Base ASAG.
     b) Targeted qualitative error analysis (Stage 16) on specific answers exhibiting correct additional, irrelevant, or incorrect additional content.
3. **Score Distribution Ceiling:**
   - 49.3% of answers have score 5.0. Systems that over-predict high scores might appear artificially accurate on raw accuracy but will be penalized on rank correlation and discrimination.

---

## 6. Schema Specification

The processed CSV files (`data/processed/mohler_asag/`) follow this exact schema:

| Column | Type | Description |
| :--- | :---: | :--- |
| `question_id` | `str` | Identifier formatted as `"x.y"` (e.g. `"1.1"`). |
| `assignment` | `int` | Assignment or exam number (1 to 12). |
| `question_index` | `int` | Question number within assignment (1 to 10). |
| `is_active` | `bool` | `True` for active ASAG questions; `False` for `#` selection/ordering questions. |
| `student_index` | `int` | 0-based answer index for the question. |
| `question` | `str` | Cleaned question text without prefix. |
| `reference_answer` | `str` | Cleaned instructor reference answer without prefix. |
| `student_answer_raw` | `str` | Raw student answer text with prefix removed. |
| `student_answer_cleaned` | `str` | Cleaned student answer text with HTML tags removed. |
| `score_me` | `float` | Michael Mohler's grade (0–5 for A1-10; 0–10 for exams). |
| `score_other` | `float` | Course TA's grade (0–5 for A1-10; 0–10 for exams). |
| `score_ave` | `float` | Official average grade on 0–5 scale. |
| `score_scale` | `str` | `'0-5'` or `'0-10_normalized_to_0-5'`. |

---

## 7. Verification Summary

- **Raw download verified:** 1,445,111 bytes zip archive from University of Michigan.
- **Processed files generated:** All 4 CSV files exported and verified.
- **Roundtrip fidelity:** 100% (all 2,442 records match identically).
- **Unit test suite:** 20 new tests in `tests/test_mohler_dataset.py`, 100% passing.
- **Total repository tests:** 286 tests passing with zero regressions.
