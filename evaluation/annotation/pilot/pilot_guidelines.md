# Human Annotation Pilot Guidelines (50-Item Study)

**Project:** Automatic Short Answer Grading using Semantic and Dependency Analysis  
**Phase:** Human Annotation Pilot Validation Study  
**Document:** Official Annotator Instructions, Definitions, and Protocol  
**Scope:** 50-Item Pilot Sample drawn deterministically from the 500-Item Validation Sample  
**Date:** October 2026  

---

## 1. Purpose of the Pilot Study

This 50-item pilot study is an **evaluative validation step** designed to test:
1. Whether the four proposition-level labels can be applied consistently by independent human judges,
2. Whether the provided question, reference, and student context are sufficient to make reliable technical judgments,
3. Whether specific edge cases or ambiguities require clarification in the guidelines before proceeding to the full 500-item study,
4. The level of inter-annotator agreement achieved under strict double-blind conditions.

> [!NOTE]
> **Guideline Status**: The guidelines are sufficiently specified to conduct the pilot. Their practical adequacy will be assessed after both annotators independently complete the pilot and inter-annotator agreement is analyzed.

> [!IMPORTANT]
> **No Model Tuning**: This pilot is strictly for **validation of the annotation protocol**. Annotations will **never** be used to tune, re-train, or modify the frozen ASAG model.

---

## 2. What the Annotator Sees

Each row in your assigned file (`pilot_annotator_1.csv` or `pilot_annotator_2.csv`) provides:
- **`pilot_id`**: Identifier for this pilot item (`PILOT_001` to `PILOT_050`).
- **`question_id`**: Question identifier in the computer science curriculum (e.g., `11.5`).
- **`answer_id`**: Unique student answer identifier.
- **`proposition_id`**: Unique proposition identifier.
- **`question_text`**: The exact question prompt presented to the student.
- **`reference_text`**: The instructor's model reference answer.
- **`student_answer_text`**: The complete text of the student's answer.
- **`proposition_text`**: The specific extracted proposition clause under evaluation.
- **`proposition_context`**: The student answer with the target proposition clearly demarcated by `>>> ... <<<`.
- **`annotator_label`**: Blank field where you enter your decision.
- **`annotator_note`**: Blank field for optional comments, rationales, or observed ambiguities.

### What You Do NOT See (Double-Blind Requirement)
To ensure complete scientific objectivity, you are **blinded** to:
- What the automated ASAG system predicted,
- The system's confidence or severity assessment,
- The system's diagnostic rationale,
- The instructor's overall holistic grade for the student.

Please evaluate each proposition strictly on its own merits.

---

## 3. The Four Categorical Labels

You must assign **exactly one** of the following four labels to each item:

```
CORRECT_ADDITIONAL    IRRELEVANT    INCORRECT    UNCERTAIN
```

### 3.1 `CORRECT_ADDITIONAL`
The proposition contains information that is:
- **Technically correct** according to computer science principles,
- **Relevant** to answering the prompt,
- **Not required to match the reference answer** (i.e. introduces a valid additional technical fact, property, qualification, example, or elaboration beyond the reference),
- Does **not** contradict the reference answer or established domain facts.

*Example*:
- **Question**: *"What is a primary key?"*
- **Reference**: *"A primary key uniquely identifies each record in a table."*
- **Target Proposition**: `"[primary keys] cannot contain null values"`
- **Decision**: **`CORRECT_ADDITIONAL`** (Valid, relevant technical property omitted from the reference).

---

### 3.2 `IRRELEVANT`
The proposition does **not materially help answer the question prompt**, even if the statement itself might happen to be factually true in computer science or general knowledge.
- Unrelated technical facts from other domains.
- Historical trivia, background context, or personal commentary.
- Repetitive filler that adds no substantive content.

> [!WARNING]
> **Factual Truth ≠ Correct Additional**: An assertion can be 100% true, but if it does not address the question prompt, it must be labeled **`IRRELEVANT`**.

*Example*:
- **Question**: *"What is a primary key?"*
- **Reference**: *"A primary key uniquely identifies each record in a table."*
- **Target Proposition**: `"SQL was invented at IBM in the 1970s"`
- **Decision**: **`IRRELEVANT`** (True history, but irrelevant to the purpose of a primary key).

---

### 3.3 `INCORRECT`
The proposition contains a **factual error, conceptual misconception, or invalid relationship**.
- Contradicts a known computer science property or definition.
- Reverses an essential relationship or ordering.
- Asserts an incorrect syntax, algorithmic complexity, or mechanism.

*Example*:
- **Question**: *"What is a primary key?"*
- **Reference**: *"A primary key uniquely identifies each record in a table."*
- **Target Proposition**: `"[primary keys] can contain duplicate rows"`
- **Decision**: **`INCORRECT`** (Directly contradicts the uniqueness requirement).

---

### 3.4 `UNCERTAIN`
The proposition **cannot be confidently classified** as correct, incorrect, or irrelevant given the provided context and standard undergraduate computer science knowledge.
- Ambiguous wording or unclear pronoun reference where multiple interpretations are equally plausible.
- The assertion depends on an unstated assumption or specific codebase implementation not provided in the prompt.
- Proposition text is syntactically fragmented such that its technical meaning cannot be reliably recovered.
- Plausible technical claim that cannot be verified without external instructor-specific course notes.

*Example*:
- **Question**: *"What are the advantages of prototypes?"*
- **Reference**: *"To simulate portions of the software product..."*
- **Target Proposition**: `"it may solve it"`
- **Decision**: **`UNCERTAIN`** (Vague syntax and dangling pronouns make the technical assertion unverifiable).

---

## 4. Fundamental Rule: Reference Absence

Annotators must adhere strictly to the following principle:

$$\text{Reference Absence} \neq \text{INCORRECT}$$
$$\text{Reference Absence} \neq \text{CORRECT\_ADDITIONAL}$$

1. **Absence from Reference Does NOT Imply `INCORRECT`**:  
   Instructors write concise reference answers focusing only on core concepts. Students frequently supply accurate, sophisticated technical details that the instructor omitted. An accurate, relevant addition must be labeled **`CORRECT_ADDITIONAL`**, never `INCORRECT`.
2. **Absence from Reference Does NOT Imply `CORRECT_ADDITIONAL`**:  
   An unmentioned statement may be an off-topic tangent (**`IRRELEVANT`**), a conceptual error (**`INCORRECT`**), or too vague to judge (**`UNCERTAIN`**).

---

## 5. Annotator Decision Procedure

Follow this 7-step sequence when evaluating each row:

```
1. Read the Question Text: What specific concept or mechanism is being tested?
2. Read the Reference Answer: What core facts did the instructor explicitly require?
3. Read the Student Answer & Demarcated Context: How did the student express their response?
4. Is the demarcated proposition understandable in context?
   └── NO ──► UNCERTAIN
5. Does the proposition materially help answer the question?
   └── NO ──► IRRELEVANT
6. Does the proposition contain a factual error, contradiction, or misconception?
   └── YES ──► INCORRECT
7. Is the proposition technically accurate and additional to the required reference?
   ├── YES ──► CORRECT_ADDITIONAL
   └── NO (unverifiable or ambiguous) ──► UNCERTAIN
```

---

## 6. Edge Cases and Protocol Guidance

1. **Symmetric Relational Comparisons (e.g. Binary Search Trees)**:  
   Mathematical converses are equivalent:
   - *"Left child is smaller than parent"* $\iff$ *"Parent is greater than left child"*.
   - If a student asserts that a parent node is greater than its left child, this is **conceptually identical and correct**. Do **not** mark it `INCORRECT` merely because the words *"smaller"* and *"greater"* are antonyms!
2. **Core Paraphrase vs. Correct Additional Information**:  
   > **Critical Research Principle: SYSTEM UNMATCHED ≠ HUMAN ADDITIONAL**
   
   A proposition that simply rephrases information already contained in the reference answer is **CORE information**, not genuinely additional information. The automated ASAG system may have marked it as "unmatched" due to syntactic displacement or parser limitations, but human annotators must not confuse system matching failures with genuine student elaborations.
   
   Annotators must distinguish:
   - **Core Paraphrase**: Conveys the same essential information as the reference answer, expressed differently (e.g., Reference: *"A function that calls itself"*, Proposition: *"invokes its own function body"*). It is core content, not additional technical content.
   - **Correct Additional**: Relevant, technically accurate information that goes *beyond* the reference/core answer (e.g., Reference: *"A function that calls itself"*, Proposition: *"requires a base case to terminate recursion"*).
   
   **Protocol for Core Paraphrases**:
   - Do **NOT** label a core paraphrase as `CORRECT_ADDITIONAL` merely because the ASAG system marked it as unmatched.
   - When a proposition simply expresses the core reference concept in different words, write **`core paraphrase`** in `annotator_note`.
   - If the proposition provides valid supplementary technical details beyond the reference, label it **`CORRECT_ADDITIONAL`**.
   - Recording *"core paraphrase"* in the notes enables researchers to analyze these instances later as pipeline extraction/matching false negatives rather than misclassifications of additional information.
3. **Bulleted and Fragmented Text**:  
   Inspect `proposition_context` to understand how the clause fits into the student's bulleted or dashed list. Do not penalize informal punctuation if the underlying computer science assertion is clear.
4. **Independent Work**:  
   Annotators must complete their assigned files without consulting each other or external AI tools. Disagreements will be reviewed and reconciled during a later adjudication phase.
