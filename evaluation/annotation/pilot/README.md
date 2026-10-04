# Human Proposition-Level Annotation Pilot (50-Item Study)

This directory contains the dataset, blinding setup, and instructions for the **50-Item Human Annotation Pilot Study** of the `proposition-level-asag` research project.

---

## 1. Study Overview

- **Purpose**: A small-scale pilot study to test the clarity of the annotation guidelines, evaluate the usability of the demarcated context interface, and measure initial inter-annotator agreement before proceeding to the full 500-item study.
- **Sample Size**: Exactly **50 proposition items**.
- **Source**: Drawn deterministically from the existing **500-item stratified/enriched validation sample** (`evaluation/annotation/master_annotation_dataset.csv`).
- **Random Seed**: `42` (Deterministic and fully reproducible).
- **Annotators**: Two independent human computer science judges working under strict double-blind conditions.
- **Model Status**: **Experiment 4 remains completely frozen**. No model tuning, parameter optimization, or pipeline modifications will occur based on pilot results.

---

## 2. File Structure

```
evaluation/annotation/pilot/
├── README.md                  (This file: pilot overview and protocol)
├── pilot_guidelines.md        (Official coding guidelines, label definitions, decision tree)
├── pilot_sampling_report.md   (Detailed sampling methodology, category/question distributions)
├── pilot_master.csv           (Master dataset containing system predictions, severities, and adjudication slots)
├── pilot_annotator_1.csv      (Strictly blinded annotation file for Judge 1)
├── pilot_annotator_2.csv      (Strictly blinded annotation file for Judge 2)
└── generate_pilot_sample.py   (Deterministic sampling script, seed=42)
```

---

## 3. Double-Blind Protocol

To ensure research integrity:
1. **Annotator Blindness**:
   - `pilot_annotator_1.csv` and `pilot_annotator_2.csv` contain **zero** system classifications, severities, rationales, confidence scores, or human answer grades.
   - Annotators do not know which items were predicted as `INCORRECT` or `UNCERTAIN`.
2. **Context Provided**:
   - Question Prompt (`question_text`)
   - Instructor Reference Answer (`reference_text`)
   - Full Student Answer (`student_answer_text`)
   - Demarcated Context (`proposition_context`), highlighting the proposition in place: `>>> target proposition <<<`
   - Isolated Proposition Clause (`proposition_text`)
3. **Empty Annotation Fields**:
   - `annotator_label` and `annotator_note` are 100% blank and must be populated by the human judges.

---

## 4. The Four Categorical Labels

Annotators assign exactly one label to each proposition:

1. **`CORRECT_ADDITIONAL`**: Technically accurate, relevant to the question, not required to match the reference answer, valid technical elaboration beyond the reference.
2. **`IRRELEVANT`**: Unrelated or unnecessary to answering the question, even if factually true.
3. **`INCORRECT`**: Contains a factual error, conceptual misconception, invalid property, or contradiction.
4. **`UNCERTAIN`**: Cannot be confidently classified given the context and standard undergraduate computer science knowledge.

> [!IMPORTANT]
> **Reference Absence Rule**: A proposition is **not** automatically `INCORRECT` merely because it is omitted from the reference answer. Conversely, reference absence does **not** automatically imply `CORRECT_ADDITIONAL`.

---

## 5. Next Steps

1. Independent annotators complete `pilot_annotator_1.csv` and `pilot_annotator_2.csv`.
2. Inter-annotator agreement metrics (raw agreement, Cohen's Kappa $\kappa$) will be calculated via `pilot_agreement.py`.
3. The guidelines are sufficiently specified to conduct the pilot. Their practical adequacy will be assessed after both annotators independently complete the pilot and inter-annotator agreement is analyzed.
4. If specific edge cases or ambiguities are discovered, the guidelines will be refined before launching the full 500-item annotation study.
