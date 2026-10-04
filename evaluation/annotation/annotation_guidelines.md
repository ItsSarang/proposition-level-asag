# Human Proposition-Level Annotation Guidelines

**Project:** Automatic Short Answer Grading using Semantic and Dependency Analysis  
**Phase:** Phase 6 — Human Proposition-Level Annotation Study  
**Document:** Official Annotation Guidelines and Coding Protocol  
**Target:** 500 Stratified Proposition Items from the UNT CS Dataset (*Mohler et al., 2011*)  
**Date:** October 2026  

---

## 1. Research Purpose and Context

### Why This Study is Necessary
In classical Automated Short Answer Grading (ASAG), systems evaluate student answers primarily by computing overlap or entailment against an instructor's reference answer. However, real students frequently introduce facts, clarifications, or claims that **do not appear in the reference answer**.

Our research investigates whether an NLP system can extract these unmatched clauses and evaluate them as:
- **`CORRECT_ADDITIONAL`** (Valid elaboration or technical detail),
- **`IRRELEVANT`** (Off-topic commentary or extraneous remarks),
- **`INCORRECT`** (Conceptual error or factual contradiction), or
- **`UNCERTAIN`** (Vague, ambiguous, or unverified assertion).

### The Evaluation Challenge
The benchmark dataset contains **holistic answer-level scores** awarded by human course instructors (e.g., 4.0 out of 5.0). It does **not** contain proposition-level labels. Therefore, we cannot determine whether the system's proposition classifications are accurate without an independent human validation study.

Your annotations serve as the **ground truth** to measure the precision, recall, and reliability of the proposition classification component.

> [!NOTE]
> **Guideline Status**: The guidelines are sufficiently specified to conduct the pilot. Their practical adequacy will be assessed after both annotators independently complete the pilot and inter-annotator agreement is analyzed.

---

## 2. Strict Blinding Instructions

To preserve scientific objectivity:
1. **You are strictly blinded**:
   - You will not see the system's classification (`system_label`).
   - You will not see the system's severity estimation (`system_severity`).
   - You will not see the system's explanation or confidence (`system_rationale`).
   - You will not see the human grader's overall score (`human_score`).
2. **Independent Judgment**:
   - Evaluate each proposition strictly on its own merits using the supplied question prompt, reference answer, student context, and standard undergraduate computer science knowledge.
   - Do not attempt to guess what score the student received or how the algorithm classified the item.

---

## 3. The Four Primary Labels

For every item, you must assign **exactly one** of the following four mutually exclusive labels:

```
[CORRECT_ADDITIONAL]   [IRRELEVANT]   [INCORRECT]   [UNCERTAIN]
```

### 3.1 `CORRECT_ADDITIONAL`
The proposition contains information that is:
- **Technically correct** according to standard computer science principles,
- **Relevant** to answering the question prompt,
- **Not merely a restatement** of the reference answer, and
- **A valid technical elaboration**, property, qualification, example, or additional fact.
- It does **not** contradict the reference answer or established domain facts.

*Example*:
- **Question**: *"What is the purpose of a primary key?"*
- **Reference**: *"A primary key uniquely identifies each record in a table."*
- **Target Proposition**: `"[primary keys] cannot contain NULL values"`
- **Judgment**: **`CORRECT_ADDITIONAL`** (Accurate, relevant database fact not mentioned in the reference).

---

### 3.2 `IRRELEVANT`
The proposition may be factually true or false, but it **does not materially help answer the question prompt**.
- Includes unrelated technical facts from other domains.
- Includes historical trivia, meta-commentary, or personal remarks.
- Includes redundant filler that adds no substantive content to the answer.

> [!IMPORTANT]
> **Factual truth does NOT imply `CORRECT_ADDITIONAL`**. An assertion can be 100% factually true in computer science, but if it does not address the question prompt, it is **`IRRELEVANT`**.

*Example*:
- **Question**: *"What is the purpose of a primary key?"*
- **Reference**: *"A primary key uniquely identifies each record in a table."*
- **Target Proposition**: `"SQL was developed at IBM in the 1970s"`
- **Judgment**: **`IRRELEVANT`** (Factually true historical fact, but completely irrelevant to the purpose of a primary key).

---

### 3.3 `INCORRECT`
The proposition contains a **factual or conceptual error**, introduces a misconception, or asserts an invalid relationship.
- Explicitly contradicts established domain properties.
- Reverses a required relationship or ordering.
- Claims a false complexity, invalid syntax, or erroneous mechanism.

*Example*:
- **Question**: *"What is the purpose of a primary key?"*
- **Reference**: *"A primary key uniquely identifies each record in a table."*
- **Target Proposition**: `"[primary keys] can contain duplicate values"`
- **Judgment**: **`INCORRECT`** (Directly contradicts the uniqueness definition of primary keys).

---

### 3.4 `UNCERTAIN`
The proposition cannot be confidently determined to be correct, incorrect, or irrelevant based on the provided context and standard computer science knowledge.
- Vague or incomplete phrasing whose intended meaning is ambiguous.
- Depends on an unstated assumption or specific codebase context not given in the prompt.
- Proposition text is syntactically fragmented such that its technical meaning cannot be established.
- Plausible claim that cannot be verified without external instructor-specific course notes.

*Example*:
- **Question**: *"What are the advantages of using prototype programs?"*
- **Reference**: *"To simulate portions of the software product..."*
- **Target Proposition**: `"it may solve it"`
- **Judgment**: **`UNCERTAIN`** (Pronoun references and vague phrasing leave the exact technical assertion unverifiable).

---

## 4. The Fundamental Principle: Reference Absence

Annotators must adhere strictly to the following epistemic rule:

```
Reference Absence ≠ Incorrect
Reference Absence ≠ Correct Additional
```

1. **"Not in the reference answer" does NOT mean `INCORRECT`**:  
   Instructors write concise reference answers that cover only the minimum core concept. Students frequently provide valid, sophisticated technical details that the instructor did not include. If an unmatched statement is factually accurate and relevant, it must be labeled **`CORRECT_ADDITIONAL`**, never `INCORRECT`.
2. **"Not in the reference answer" does NOT mean `CORRECT_ADDITIONAL`**:  
   Just because a statement is not in the reference does not mean it is a valid addition. It may be an off-topic tangent (**`IRRELEVANT`**), a serious misconception (**`INCORRECT`**), or too vague to judge (**`UNCERTAIN`**).

---

## 5. Standard Decision Procedure

When evaluating each proposition, follow this sequential decision tree:

```
STEP 1: Comprehensibility Check
Is the target proposition understandable within the student answer context?
  ├── NO  ──► UNCERTAIN
  └── YES ──► Proceed to Step 2

STEP 2: Relevance Check
Does the proposition materially relate to the topic and question prompt?
  ├── NO  ──► IRRELEVANT
  └── YES ──► Proceed to Step 3

STEP 3: Error & Contradiction Check
Does the proposition contain a factual error, invalid property, or misconception?
  ├── YES ──► INCORRECT
  └── NO  ──► Proceed to Step 4

STEP 4: Verifiability & Substance Check
Can the correctness of the proposition be reasonably verified from standard CS knowledge?
  ├── YES ──► CORRECT_ADDITIONAL
  └── NO  ──► UNCERTAIN
```

---

## 6. Edge Cases and Protocol Guidance

### 6.1 Core Paraphrase vs. Correct Additional Information
> **Critical Research Principle: SYSTEM UNMATCHED ≠ HUMAN ADDITIONAL**

A proposition that simply rephrases information already contained in the reference answer is **CORE information**, not genuinely additional information. The automated ASAG system may have marked it as "unmatched" due to syntactic displacement or parser limitations, but human annotators must not confuse system matching failures with genuine student elaborations.

Annotators must distinguish:
- **Core Paraphrase**: Conveys the same essential information as the reference answer, expressed differently (e.g., Reference: *"A function that calls itself"*, Proposition: *"invokes its own function body"*). It is core content, not additional technical content.
- **Correct Additional**: Relevant, technically accurate information that goes *beyond* the reference/core answer (e.g., Reference: *"A function that calls itself"*, Proposition: *"requires a base case to terminate recursion"*).

**Protocol for Core Paraphrases**:
- Do **NOT** label a core paraphrase as `CORRECT_ADDITIONAL` merely because the ASAG system marked it as unmatched.
- When a proposition simply expresses the core reference concept in different words, write **`core paraphrase`** in `annotator_notes`.
- If the proposition provides valid supplementary technical details beyond the reference, label it **`CORRECT_ADDITIONAL`**.
- If a proposition is pure redundant filler repeating what the student already stated twice, mark **`IRRELEVANT`**.
- Recording *"core paraphrase"* in the notes enables researchers to analyze these instances later as pipeline extraction/matching false negatives rather than misclassifications of additional information.

### 6.2 Symmetric and Comparative Relations (e.g., Binary Search Trees)
Pay close attention to directional relationships:
- If a reference states: *"left child is smaller than parent"*, and the student states: *"parent is greater than left child"*, this is **conceptually identical and 100% correct** ($A < B \iff B > A$).
- Do **not** mark converse statements as `INCORRECT` merely because the words *"smaller"* and *"greater"* are antonyms! Verify whether the underlying mathematical relationship holds. If it holds, mark **`CORRECT_ADDITIONAL`**.

### 6.3 Mixed Sentences (Partially Correct, Partially Incorrect)
If a student writes a complex sentence where one clause is correct and another clause introduces a misconception:
- Focus specifically on the **bracketed proposition clause** indicated by `>>> ... <<<`.
- If the bracketed clause itself contains the error, mark **`INCORRECT`**.
- If the bracketed clause is correct, but an adjacent unbracketed clause was flawed, evaluate the bracketed proposition on its own merit.

### 6.4 Bulleted Lists and Informal Formatting
Students often use dashes, hyphens, or newline breaks instead of punctuation:
- Inspect `proposition_context` to understand how the clause fits into the student's bulleted structure.
- Do not penalize informal punctuation if the conceptual assertion is clear and sound.

---

## 7. Submission and Data Hygiene

1. Open your assigned file (`annotator_1.csv` or `annotator_2.csv`) in a spreadsheet editor (e.g. Excel, LibreOffice Calc) or code editor.
2. For each row:
   - Read `question_text`, `reference_text`, and `student_answer_text`.
   - Locate the demarcated target proposition in `proposition_context`.
   - Enter your chosen label into the `annotator_label` column. Exactly one of:
     `CORRECT_ADDITIONAL`, `IRRELEVANT`, `INCORRECT`, `UNCERTAIN`.
   - (Optional) Enter brief comments into `annotator_notes` if the item is tricky or represents a borderline edge case.
3. Save the completed file in UTF-8 CSV format with identical column names and ordering.
4. Do not alter `item_id`, `question_id`, `answer_id`, or `proposition_id`.
