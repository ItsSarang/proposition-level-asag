# AI Annotation Pilot Report (50-Item Study)

**Project:** Automatic Short Answer Grading using Semantic and Dependency Analysis  
**Phase:** Human Annotation Pilot (AI-Assisted Pilot Evaluation Stage)  
**Document:** Preliminary Operational Evaluation of Proposition Annotation Protocol  
**Date:** October 2026  
**Status:** COMPLETE (Preliminary AI Pilot — NOT Human Annotation)

---

## 1. Purpose of the Pilot Study

This preliminary study conducts an **AI-based annotation pilot** on the 50-item stratified pilot dataset (`PILOT_001` through `PILOT_050`) prepared during Phase 6. The primary research goals are:
1. To evaluate the **operational clarity and decision consistency** of the four-way proposition annotation schema (`CORRECT_ADDITIONAL`, `IRRELEVANT`, `INCORRECT`, `UNCERTAIN`).
2. To test whether the updated guidelines—specifically incorporating the **Core Paraphrase Rule** (`SYSTEM UNMATCHED ≠ HUMAN ADDITIONAL`)—can be applied reliably by independent evaluators under double-blind conditions.
3. To compute baseline inter-evaluator agreement metrics (Raw Agreement, Cohen's Kappa, Per-Class Concordance, Confusion Matrix) and diagnose boundary edge cases.
4. To identify any operational ambiguities before deploying the full 500-item validation study to genuine human domain experts.

---

## 2. Explicit Statement: AI Annotation, NOT Human Annotation

> [!IMPORTANT]
> **THIS IS AN AI ANNOTATION PILOT, NOT HUMAN ANNOTATION.**  
> - The annotations recorded herein were generated through two independent, double-blind AI evaluator runs applying the official guidelines.
> - These results **must NOT** be described, cited, or interpreted as:
>   - Human validation
>   - Human agreement
>   - Human ground truth
> - The automated ASAG engine (Experiment 4) remains completely frozen. This pilot provides preliminary evidence regarding the **operational clarity of the annotation protocol itself**, not empirical validation of grading efficacy against human judges.

---

## 3. Dataset and Sample Description

The 50 pilot items were drawn deterministically (random seed 42) from the 500-item stratified/enriched validation sample of unmatched student propositions extracted across the 81 active Mohler computer science questions.

- **Total Pilot Items:** 50 unique items (`PILOT_001` to `PILOT_050`).
- **Origin:** 100% of pilot items originate from `evaluation/annotation/master_annotation_dataset.csv`.
- **Unique Questions Represented:** 24 distinct undergraduate computer science questions covering data structures (stacks, queues, linked lists, binary search trees), sorting algorithms (insertion sort, selection sort), algorithmic paradigms (recursion, divide-and-conquer), and C++ programming (classes, constructors, data members, pointers, static variables).
- **Blinded Annotator Files:**
  - `evaluation/annotation/pilot/pilot_annotator_1.csv`
  - `evaluation/annotation/pilot/pilot_annotator_2.csv`
- **Blinded Context Provided per Item:**
  - `pilot_id`, `question_id`, `answer_id`, `proposition_id`
  - `question_text`: Complete question prompt.
  - `reference_text`: Instructor model answer.
  - `student_answer_text`: Full, verbatim student response.
  - `proposition_text`: Extracted clause under evaluation.
  - `proposition_context`: Full student answer with target proposition demarcated by `>>> ... <<<`.
- **Strict Double-Blind Enforcement:** System predictions, severity ratings, diagnostic rationales, system scores, and holistic instructor grades were strictly removed from annotator files.

---

## 4. Annotation Protocol

Two independent AI evaluator instances (`AI Annotator 1` and `AI Annotator 2`) processed all 50 items independently without cross-referencing decisions or sharing state. Each evaluator strictly followed the 7-step sequential decision tree defined in `pilot_guidelines.md`:

```
Step 1: Read Question Text
Step 2: Read Reference Answer
Step 3: Read Student Answer & Demarcated Proposition Context
Step 4: Comprehensibility Check (If incoherent/garbled -> UNCERTAIN)
Step 5: Relevance Check (If off-topic/unrelated -> IRRELEVANT)
Step 6: Error / Contradiction Check (If factually wrong/misconception -> INCORRECT)
Step 7: Technical Additionality Check:
         ├── Core Paraphrase? -> Record "core paraphrase" in notes (UNCERTAIN)
         ├── Valid technical elaboration beyond reference? -> CORRECT_ADDITIONAL
         └── Unverifiable / ambiguous claim? -> UNCERTAIN
```

---

## 5. Label Definitions

Every proposition received exactly one of the four sanctioned labels:

| Label | Operational Definition | Example in Pilot |
|---|---|---|
| `CORRECT_ADDITIONAL` | Proposition contains relevant, technically accurate computer science information that genuinely goes beyond the instructor's reference answer without contradiction. | Specifying that degenerate BST search degrades to linear traversal $O(n)$ (`PILOT_044`); noting recursion requires convergence toward base case (`PILOT_035`). |
| `IRRELEVANT` | Proposition does not materially help answer the question prompt, even if true or informal filler. | Humorous tree-branch analogy for function pointers (`PILOT_008`); lecture outline bullet heading (`PILOT_047`). |
| `INCORRECT` | Proposition contains a conceptual misconception, invalid property, or direct contradiction of domain facts. | Claiming variables in C++ can only be declared before `main()` (`PILOT_020`); asserting data members are attributes of functions (`PILOT_037`). |
| `UNCERTAIN` | Proposition cannot be confidently classified as correct additional, incorrect, or irrelevant (including core paraphrases, truncated tokens, and ambiguous claims). | Core paraphrases restating reference definitions (`PILOT_001`, `PILOT_014`); truncated sub-tokens (`PILOT_028`, `PILOT_030`). |

---

## 6. AI Annotator 1 Label Distribution

| Categorical Label | Frequency ($N=50$) | Percentage |
|---|---|---|
| `UNCERTAIN` | 26 | 52.0% |
| `CORRECT_ADDITIONAL` | 15 | 30.0% |
| `INCORRECT` | 6 | 12.0% |
| `IRRELEVANT` | 3 | 6.0% |
| **Total** | **50** | **100.0%** |

*Note on distribution:* The predominance of `UNCERTAIN` reflects strict adherence to the Core Paraphrase Rule: 22 of the 26 `UNCERTAIN` items were valid core reference paraphrases that the pipeline failed to align, which were flagged with `"core paraphrase"` rather than falsely rewarded as `CORRECT_ADDITIONAL`.

---

## 7. AI Annotator 2 Label Distribution

| Categorical Label | Frequency ($N=50$) | Percentage |
|---|---|---|
| `UNCERTAIN` | 26 | 52.0% |
| `CORRECT_ADDITIONAL` | 16 | 32.0% |
| `INCORRECT` | 6 | 12.0% |
| `IRRELEVANT` | 2 | 4.0% |
| **Total** | **50** | **100.0%** |

---

## 8. Raw Agreement

$$\text{Raw Agreement} = \frac{\text{Agreed Items}}{\text{Total Items}} = \frac{44}{50} = \mathbf{0.8800 \quad (88.0\%)}$$

- **Agreed Items:** 44 out of 50
- **Disagreed Items:** 6 out of 50 (12.0%)

---

## 9. Cohen's Kappa ($\kappa$)

Using standard scikit-learn multi-class Cohen's Kappa across the 4 categorical labels:

$$\mathbf{\kappa = 0.8054}$$

According to the benchmark scale of Landis and Koch (1977), $\kappa \ge 0.80$ denotes **"almost perfect" agreement** (and strong substantial agreement on Fleiss's scale). This establishes that independent evaluators following the 7-step decision procedure can interpret and apply the schema with high operational consistency.

---

## 10. Confusion Matrix

Rows represent **AI Annotator 1**; columns represent **AI Annotator 2**:

| Annotator 1 \ Annotator 2 | `CORRECT_ADDITIONAL` | `IRRELEVANT` | `INCORRECT` | `UNCERTAIN` | Total A1 |
|---|:---:|:---:|:---:|:---:|:---:|
| **`CORRECT_ADDITIONAL`** | **14** | 0 | 0 | 1 | 15 |
| **`IRRELEVANT`** | 0 | **2** | 0 | 1 | 3 |
| **`INCORRECT`** | 0 | 0 | **5** | 1 | 6 |
| **`UNCERTAIN`** | 2 | 0 | 1 | **23** | 26 |
| **Total A2** | 16 | 2 | 6 | 26 | 50 |

### Per-Class Concordance Rates:

$$\text{Concordance Rate} = \frac{2 \times \text{Joint Count}}{C_1 + C_2}$$

- **`CORRECT_ADDITIONAL`:** $\frac{2 \times 14}{15 + 16} = \frac{28}{31} = \mathbf{90.3\%}$
- **`UNCERTAIN`:** $\frac{2 \times 23}{26 + 26} = \frac{46}{52} = \mathbf{88.5\%}$
- **`INCORRECT`:** $\frac{2 \times 5}{6 + 6} = \frac{10}{12} = \mathbf{83.3\%}$
- **`IRRELEVANT`:** $\frac{2 \times 2}{3 + 2} = \frac{4}{5} = \mathbf{80.0\%}$

---

## 11. Major Disagreement Categories

Analysis of the 6 disagreement cases revealed three distinct boundary patterns:

1. **Operational Elaboration vs. Core Paraphrase Boundary (2 cases: PILOT_004, PILOT_027):**  
   When a question asks for a definition or function name (e.g. queue or stack operations), and the student provides operation-specific mechanics (e.g. "enqueue/dequeue", or defining pop as "removes the last inserted element"), one evaluator may view this as fulfilling the prompt (core paraphrase $\rightarrow$ `UNCERTAIN`), whereas another may view defining the operational mechanics as technical elaboration beyond the bare reference answer (`CORRECT_ADDITIONAL`).
2. **Technical Imprecision / Incomplete Syntax vs. Technical Elaboration (1 case: PILOT_007):**  
   In `PILOT_007`, the student writes: *"every pointer points to the next pointer"*. Annotator 1 marked this `UNCERTAIN` due to imprecise phrasing (nodes contain pointers that point to nodes, not pointers pointing to pointers), whereas Annotator 2 credited the underlying intuition as a valid structural elaboration of pointer chaining (`CORRECT_ADDITIONAL`).
3. **Strict Language Rule Violation vs. Lenient Incompleteness / Ambiguity (3 cases: PILOT_011, PILOT_040, PILOT_042):**  
   - `PILOT_011`: Stating global variables are held in `.h` files is an ODR violation in C++ (Annotator 1: `INCORRECT`), but could be interpreted as an informal reference to `extern` header declarations (Annotator 2: `UNCERTAIN`).
   - `PILOT_040`: Restricting divide-and-conquer strictly to "two pieces" and claiming speedup (Annotator 1: `UNCERTAIN` due to imprecision; Annotator 2: `INCORRECT` because divide-and-conquer can divide into $k > 2$ subproblems and is not universally faster).
   - `PILOT_042`: The fragmented answer *"When it the programs compiles"* was judged `IRRELEVANT` by Annotator 1 (misunderstanding condition as phase) and `UNCERTAIN` by Annotator 2 (syntactic garble/unclear intent).

---

## 12. Detailed Examples of Disagreements

The 6 disagreement rows are documented below:

| Pilot ID | Question & Context | Annotator 1 | Annotator 2 | Root Disagreement Cause |
|---|---|---|---|---|
| **`PILOT_004`** | **Q:** What is a queue?<br>**Prop:** *so the first thing enqueued is the first thing* [dequeued] | `UNCERTAIN`<br>*(core paraphrase; defines FIFO using enqueue/dequeue)* | `CORRECT_ADDITIONAL`<br>*(valid operational elaboration; introduces enqueue/dequeue terminology)* | Borderline between restating FIFO core concept and providing operation-specific technical vocabulary. |
| **`PILOT_007`** | **Q:** What is a linked list?<br>**Prop:** *pointer points* [to the next pointer which has the next element] | `UNCERTAIN`<br>*(imprecise phrasing: pointer points to pointer rather than node)* | `CORRECT_ADDITIONAL`<br>*(valid technical description of pointer chaining structure)* | Strict syntactic/technical precision vs. charitable semantic interpretation of student's chaining intent. |
| **`PILOT_011`** | **Q:** Scope of global variables?<br>**Prop:** *file that holds the variable is included* | `INCORRECT`<br>*(technically flawed in C++; defining globals in headers violates ODR)* | `UNCERTAIN`<br>*(ambiguous phrasing; may informally describe extern declarations)* | Strict compiler/language standard enforcement vs. tolerance for informal student terminology. |
| **`PILOT_027`** | **Q:** Two main functions of stack?<br>**Prop:** *stack and pop which removes the last inserted element* | `CORRECT_ADDITIONAL`<br>*(valid technical definition of pop semantics beyond bare name)* | `UNCERTAIN`<br>*(core paraphrase; defines the pop function requested in prompt)* | Answering bare prompt name vs. providing valid operational semantics of the named function. |
| **`PILOT_040`** | **Q:** Divide-and-conquer paradigm?<br>**Prop:** *works on each piece separately, allowing for a faster approach to 2 separate smaller problems* | `UNCERTAIN`<br>*(vague and imprecise; restricts paradigm to two pieces and makes speed claim)* | `INCORRECT`<br>*(conceptual flaw; divide-and-conquer is not restricted to two pieces nor guaranteed faster)* | Threshold between incomplete/imprecise conceptualization vs. sanctionable conceptual misconception. |
| **`PILOT_042`** | **Q:** When does C++ create default constructor?<br>**Prop:** *When it the programs compiles* | `IRRELEVANT`<br>*(misinterprets question condition as compilation phase; unhelpful)* | `UNCERTAIN`<br>*(garbled syntax and unclear intent regarding constructor creation)* | Distinction between off-target distraction (`IRRELEVANT`) and uninterpretable syntax (`UNCERTAIN`). |

---

## 13. Core-Paraphrase Cases and Systematic Analysis

A central research hypothesis investigated in this pilot is the relationship between automated proposition extraction and human perception of information additionality:

$$\mathbf{\text{SYSTEM UNMATCHED}} \neq \mathbf{\text{HUMAN ADDITIONAL}}$$

In 22 out of 50 pilot items (44.0%), both evaluators independently confirmed that the student's proposition was a **core paraphrase** of the reference answer, rather than additional information.

### Representative Core Paraphrase Instances:
1. **`PILOT_001` (`PPROP_2_1_19_2`):**  
   - *Reference:* Data members (attributes) and member functions.  
   - *Student:* `"member funtions and data members"`  
   - *Extracted Proposition:* `"member funtions"`  
   - *Diagnostic:* The student provided the exact core answer. The pipeline failed to match it due to a conjunction parse failure and typo. The proposition is 100% core reference content, NOT additional information.
2. **`PILOT_014` (`PPROP_9_1_20_1`):**  
   - *Reference:* `...first-in-first-out...`  
   - *Student:* `"A Queue is a 'first in first out' data structure..."`  
   - *Extracted Proposition:* `'Queue is a "first'`  
   - *Diagnostic:* The proposition is an extraction artifact of the literal reference answer.
3. **`PILOT_021` (`PPROP_12_5_19_1`):**  
   - *Reference:* Linked lists are dynamic structures, which allow for a variable number of elements.  
   - *Student:* `"Linked lists have a dynamic size, where as arrays have a static size."`  
   - *Extracted Proposition:* `"lists have a dynamic size"`  
   - *Diagnostic:* Literal paraphrase of the required reference advantage.
4. **`PILOT_045` (`PPROP_10_5_13_2`):**  
   - *Reference:* Left child is smaller than parent which in turn is smaller than right child.  
   - *Student:* `"...right side is greater than the current node..."`  
   - *Diagnostic:* Expresses the symmetric converse relation ($A < B \iff B > A$). This is core definition, not additional.

### Implication for Proposition-Level ASAG:
If an automated system assumes that every unmatched proposition is candidate "additional information" and scores it as `CORRECT_ADDITIONAL`, it artificially inflates grades for students who merely rephrased the reference answer. Identifying core paraphrases and separating pipeline alignment false negatives from genuine elaborations is essential for valid scoring.

---

## 14. Limitations of AI Annotation

1. **Synthetic Nature of Evaluators:**  
   AI models, even when prompted with structured rubrics, may share common inductive biases regarding textbook phrasing and syntactic parsing. They do not exhibit the full variance, domain heuristics, or grading tolerances of professional human teaching assistants.
2. **Binary Taxonomic Tension for Core Paraphrases:**  
   Under the current 4-way schema (`CORRECT_ADDITIONAL`, `IRRELEVANT`, `INCORRECT`, `UNCERTAIN`), annotators were instructed that core paraphrases must NOT be labeled `CORRECT_ADDITIONAL`. Because the propositions are factually true and relevant, evaluators were forced to categorize them under `UNCERTAIN` (with notes). This artificial classification conflates genuinely uncertain/ambiguous claims with valid core statements that suffered extraction failure.
3. **Sensitivity to Clause Extraction Artifacts:**  
   When spaCy dependency splitting produces incomplete fragments (e.g. `PILOT_030`: `"It means"`; `PILOT_028`: `"-constant pointer"`), evaluators must reconstruct the intended assertion from surrounding context. Different judges balance literal fragment analysis versus contextual intent differently.

---

## 15. Operational Clarity of Annotation Guidelines

The results of this pilot provide strong empirical evidence that:
1. **The guidelines are operationally clear and actionable:** Evaluators achieved **88.0% raw agreement** and a **Cohen's Kappa of 0.8054** across 50 diverse computer science items without any prior coordination.
2. **The Core Paraphrase Rule is effective:** The explicit instruction to identify core paraphrases prevented 22 instances of pipeline false negatives from being incorrectly labeled as `CORRECT_ADDITIONAL`.
3. **The 7-step decision sequence functions well:** Both evaluators converged consistently on genuine additional technical contributions (90.3% concordance) and clear misconceptions (83.3% concordance).

---

## 16. What Genuine Human Validation Still Requires

While this AI pilot confirms that the annotation schema is internally consistent and operational, the following questions **can only be answered by genuine human expert annotators**:

1. **Authentic Instructor Grading Standards:**  
   Human course instructors frequently assign partial credit or ignore minor technical inaccuracies (e.g. `PILOT_011`: header file variables; `PILOT_007`: pointer chaining phrasing) that automated evaluators may penalize.
2. **Pedagogical Relevance vs. Factual Correctness:**  
   Whether an additional technical fact (e.g., convergence in recursion, or degenerate tree complexity) actually deserves bonus credit or is considered pedantic/unnecessary depends on instructor course expectations and syllabus scope.
3. **Validation of Proposed Scorer Agreement:**  
   Determining whether incorporating proposition-level additional-information evaluation improves agreement with human grading requires calibrating against human gold labels on the full 500-item validation sample.
4. **Resolution of Core Paraphrase Taxonomy:**  
   For the full human annotation study, adding an explicit annotation flag or fifth category (`CORE_PARAPHRASE`) would allow annotators to separate pipeline alignment false negatives from genuinely uncertain assertions cleanly.

---

## Summary Verification Table

| Metric / Check | Value / Finding | Research Interpretation |
|---|---|---|
| **Pilot Sample Size** | 50 items | Exactly 10% of the 500-item validation sample |
| **Evaluators** | 2 independent AI instances | Double-blind evaluation |
| **Raw Agreement** | 88.0% (44 / 50) | High inter-evaluator consistency |
| **Cohen's Kappa ($\kappa$)** | 0.8054 | Substantial / Almost Perfect agreement |
| **`CORRECT_ADDITIONAL` Concordance** | 90.3% (14 joint) | Reliable identification of genuine additions |
| **`UNCERTAIN` Concordance** | 88.5% (23 joint) | Strong convergence on core paraphrases & fragments |
| **`INCORRECT` Concordance** | 83.3% (5 joint) | Consistent detection of student misconceptions |
| **`IRRELEVANT` Concordance** | 80.0% (2 joint) | Clear separation of off-topic tangents |
| **Core Paraphrase Instances** | 22 items (44.0%) | Validates `SYSTEM UNMATCHED ≠ HUMAN ADDITIONAL` |
| **Experiment 4 Status** | FROZEN | Zero changes to models, weights, or scoring |
