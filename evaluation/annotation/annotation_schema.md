# Phase 6: Human Annotation Dataset Schema & Data Dictionary

**Package:** `evaluation/annotation/`  
**Purpose:** Dataset schema, column definitions, data types, constraints, and blinding specifications for the proposition-level human validation study.  
**Dataset Size:** 500 stratified, representative propositions from the frozen Experiment 4 benchmark.  
**Date:** October 2026  

---

## 1. File Inventory and Architecture

The Phase 6 human annotation package consists of three primary CSV files:

```
evaluation/annotation/
├── master_annotation_dataset.csv   (Master record with system metadata, provenance, and adjudication slots)
├── annotator_1.csv                 (Strictly blinded annotation interface for Judge 1)
└── annotator_2.csv                 (Strictly blinded annotation interface for Judge 2)
```

### Architectural Principles
1. **Strict Double-Blinding**:
   - `annotator_1.csv` and `annotator_2.csv` contain identical proposition samples and identifiers.
   - Neither annotator file exposes system classifications, system severity scores, system rationales, or human answer-level grades.
   - Column headers in annotator files use strictly neutral names (`annotator_label`, `annotator_notes`).
2. **Deterministic Provenance and Traceability**:
   - Every annotation unit possesses a globally unique `item_id` (`ITEM_001` to `ITEM_500`).
   - Every item maintains structured relational keys linking back to the official active Mohler dataset: `question_id`, `answer_id`, and `proposition_id`.
3. **Reproducibility**:
   - The sample was generated using deterministic seed `42` via `generate_phase6_annotation_sample.py`.

---

## 2. Column Specifications

### 2.1 Blinded Annotator Files (`annotator_1.csv`, `annotator_2.csv`)

These files are provided directly to independent human judges. They contain only the information necessary to judge the semantic validity of the target proposition in context.

| Column Name | Data Type | Nullable? | Description | Example |
| :--- | :--- | :---: | :--- | :--- |
| `item_id` | String (`ITEM_XXX`) | No | Sequential study identifier (1–500). Primary key for annotation tracking. | `ITEM_001` |
| `question_id` | String | No | Official Mohler question identifier (`assignment.question_num`). | `11.5` |
| `answer_id` | String | No | Unique student answer identifier (`ANS_{asgn}_{q}_{student}`). | `ANS_11_5_21` |
| `proposition_id` | String | No | Unique proposition identifier (`PROP_{asgn}_{q}_{student}_{prop_num}`). | `PROP_11_5_21_1` |
| `question_text` | String | No | Complete prompt presented to the student. | *"What is a recursive function?"* |
| `reference_text` | String | No | Complete instructor reference answer. | *"A function that calls itself."* |
| `student_answer_text` | String | No | Complete, cleaned student response text. | *"A function that divides and conquers a problem..."* |
| `proposition_text` | String | No | The specific extracted proposition clause under evaluation. | *"function that divides"* |
| `proposition_context` | String | No | Complete student answer with the target proposition clearly demarcated by `>>> ... <<<`. | *"A >>> function that divides <<< and conquers a problem..."* |
| `annotator_label` | String (Categorical) | Yes (initially empty) | Target label assigned by the annotator. Must be one of: `CORRECT_ADDITIONAL`, `IRRELEVANT`, `INCORRECT`, `UNCERTAIN`. | *(Empty in blank file)* |
| `annotator_notes` | String | Yes (initially empty) | Optional qualitative rationale or edge-case notes from the annotator. | *(Empty in blank file)* |

---

### 2.2 Master Annotation File (`master_annotation_dataset.csv`)

The master file is retained by the lead researcher. It merges the blinded columns with the frozen system predictions from Experiment 4 and reserves fields for multi-annotator adjudication.

| Column Name | Data Type | Nullable? | Source / Description |
| :--- | :--- | :---: | :--- |
| `item_id` | String (`ITEM_XXX`) | No | Shared primary key matching annotator files. |
| `question_id` | String | No | Mohler question identifier. |
| `answer_id` | String | No | Mohler student answer identifier. |
| `proposition_id` | String | No | Unique proposition identifier. |
| `question_text` | String | No | Question prompt. |
| `reference_text` | String | No | Reference answer. |
| `student_answer_text` | String | No | Complete student answer. |
| `proposition_text` | String | No | Target proposition clause. |
| `proposition_context` | String | No | Demarcated student context. |
| `system_label` | String (Categorical) | No | Frozen classification from Experiment 4 (`UNCERTAIN`, `IRRELEVANT`, `INCORRECT`). |
| `system_severity` | String (Categorical) | No | Frozen severity from Experiment 4 (`NONE`, `MINOR`, `MODERATE`, `CORE_CONTRADICTION`, `UNRESOLVED`). |
| `system_rationale` | String | No | Frozen diagnostic explanation from Experiment 4 scorer. |
| `annotator_1_label` | String (Categorical) | Yes | Populated upon receiving completed `annotator_1.csv`. |
| `annotator_1_notes` | String | Yes | Populated from `annotator_1.csv`. |
| `annotator_2_label` | String (Categorical) | Yes | Populated upon receiving completed `annotator_2.csv`. |
| `annotator_2_notes` | String | Yes | Populated from `annotator_2.csv`. |
| `adjudicated_label` | String (Categorical) | Yes | Consensus gold label agreed by annotators or decided by senior referee. |
| `adjudication_notes` | String | Yes | Adjudication rationale detailing resolution of inter-annotator disagreement. |

---

## 3. Allowed Categorical Labels

Annotators must restrict `annotator_label` entries to exactly one of the four standardized categories (case-sensitive):

1. **`CORRECT_ADDITIONAL`**:
   - The proposition provides information that is technically accurate, on-topic, relevant to answering the prompt, and validly elaborates beyond the reference answer without introducing factual errors.
2. **`IRRELEVANT`**:
   - The proposition does not materially help answer the question (e.g. tangential trivia, personal remarks, unrelated background, redundant repetition).
3. **`INCORRECT`**:
   - The proposition contains a conceptual misconception, false technical statement, contradictory property assertion, or invalid causal/structural claim.
4. **`UNCERTAIN`**:
   - The proposition cannot be confidently determined as correct or incorrect given the question, reference, and ordinary computer science knowledge (e.g. vague syntax, ambiguous terminology, missing unstated assumptions).

---

## 4. Blinding Verification Audit

The integrity of the double-blind protocol is verified via automated assertions in `generate_phase6_annotation_sample.py`:
- `annotator_1.csv` and `annotator_2.csv` contain zero occurrences of the strings:
  - `system_label`
  - `system_severity`
  - `system_rationale`
  - `human_score`
  - `human_grade`
- Columns `annotator_label` and `annotator_notes` are verified to be 100% empty across all 500 data rows.
- Annotators cannot infer system classifications from row order (rows are deterministically pseudo-randomized across questions and categories).
