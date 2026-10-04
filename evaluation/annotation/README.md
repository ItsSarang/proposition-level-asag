# Phase 6: Human Proposition-Level Annotation Package

This directory contains the dataset, blinding infrastructure, guidelines, and schemas for the **Human Proposition-Level Annotation Validation Study** of the `proposition-level-asag` research project.

---

## 1. Why Proposition Annotation is Needed

The official benchmark dataset (UNT Computer Science Short Answer Dataset v2.0, *Mohler et al., 2011*) contains only **holistic answer-level human grades** (e.g. 4.5 / 5.0). It does **not** contain proposition-level annotations.

Consequently, while the ASAG pipeline can technically decompose answers into propositions and assign labels (`CORRECT_ADDITIONAL`, `IRRELEVANT`, `INCORRECT`, `UNCERTAIN`), we cannot quantitatively measure the precision, recall, or accuracy of these classifications against ground truth without a dedicated human annotation study.

This annotation package provides the materials required for independent human judges to evaluate extracted propositions directly.

> [!IMPORTANT]
> **Validation Only**: This annotation study is an **evaluative validation study**. It must **not** be used to tune or modify the frozen Experiment 4 pipeline.

---

## 2. Directory Contents

```
evaluation/annotation/
├── README.md                            (This file: study overview and execution instructions)
├── annotation_guidelines.md             (Official guidelines, label definitions, decision tree, edge cases)
├── annotation_schema.md                 (Field descriptions, data types, constraints, blinding rules)
├── annotation_sampling_report.md        (Methodology report, eligibility audit, stratification statistics)
├── master_annotation_dataset.csv        (Master file containing system labels, severities, rationales, and adjudication slots)
├── annotator_1.csv                      (Strictly blinded annotation file for Judge 1)
├── annotator_2.csv                      (Strictly blinded annotation file for Judge 2)
└── generate_phase6_annotation_sample.py (Deterministic sampling script, seed=42)
```

---

## 3. What is Being Annotated

- **Target Units**: 500 proposition clauses extracted from student responses in the frozen Experiment 4 benchmark.
- **Context Provided to Annotators**:
  - The Question Prompt (`question_text`)
  - The Official Reference Answer (`reference_text`)
  - The Full Cleaned Student Answer (`student_answer_text`)
  - The Demarcated Context (`proposition_context`), showing the proposition highlighted in place: `>>> target proposition <<<`
  - The Isolated Proposition Clause (`proposition_text`)
- **What Annotators Do NOT See**:
  - Annotators **never** see the system classification, severity score, or rationale.
  - Annotators **never** see the human grader's overall score.

---

## 4. The Four Classification Labels

Annotators assign exactly one label per proposition:

1. **`CORRECT_ADDITIONAL`**: The proposition is technically correct, relevant to answering the prompt, and validly elaborates beyond the reference answer without contradicting facts.
2. **`IRRELEVANT`**: The proposition does not materially help answer the prompt (e.g. unrelated trivia, personal remarks, off-topic tangents).
3. **`INCORRECT`**: The proposition contains a factual or conceptual error, reverses a required relationship, or introduces a misconception.
4. **`UNCERTAIN`**: The proposition cannot be confidently determined to be correct or incorrect given standard CS knowledge and context (e.g. ambiguous syntax, unstated assumptions).

---

## 5. How the Sample Was Selected

- **Source Population**: 4,695 unmatched propositions across 2,273 active student answers in Experiment 4.
- **Eligibility Audit**: 4,660 propositions (99.25%) were verified clean; 35 (0.75%) were excluded due to unambiguous extraction defects (truncated formulas, lone punctuation, or encoding corruption).
- **Deterministic Sampling (Seed 42)**:
  - 100% of all eligible detected contradictions (`INCORRECT`, $N=64$) were included across all severity levels (15 Core, 42 Moderate, 2 Minor, 5 Unresolved).
  - 218 `UNCERTAIN` and 218 `IRRELEVANT` propositions were sampled using round-robin stratification across all 81 active questions.
- **Coverage**: 100% of active questions (81 / 81), 72.8% coursework assignments (Assignments 1–10), and 27.2% exams (Exams 11–12).

---

## 6. Future Inter-Annotator Agreement Analysis

Once `annotator_1.csv` and `annotator_2.csv` are completed by human judges:
1. Inter-rater reliability will be calculated using:
   - **Cohen's Kappa ($\kappa$)** (chance-corrected pairwise agreement),
   - **Krippendorff's Alpha ($\alpha$)** (nominal reliability coefficient),
   - **Raw Percentage Agreement**.
2. Items with disagreements (`annotator_1_label != annotator_2_label`) will be adjudicated by a third senior reviewer to establish `adjudicated_label` in `master_annotation_dataset.csv`.
3. Per-class precision, recall, and F1 scores of the Experiment 4 system classifications will be evaluated against the adjudicated gold labels (incorporating post-stratification survey weights).
