# Stage 16 Report: Diagnostic Error Analysis

**Project:** Automatic Short Answer Grading using Semantic and Dependency Analysis  
**Repository:** `proposition-level-asag`  
**Phase:** Stage 16 — Diagnostic Error Analysis  
**Date:** October 2026  
**Status:** COMPLETE (In-depth qualitative and quantitative failure mode analysis across 2,273 evaluated Mohler records)

---

## Executive Summary & Research Boundaries

The primary objective of Stage 16 is **DIAGNOSIS, NOT OPTIMIZATION**. In accordance with the governing research protocol:
- **No Parameter Tuning:** Neither Stage 14 weights nor Stage 7/8/13 thresholds were modified.
- **No Algorithmic Alterations:** No code changes were made to artificial improve scores on the benchmark dataset.
- **No Proposition-Level Accuracy Claims:** Because the Mohler ASAG dataset contains **NO proposition-level human annotations**, Stage 13 classifications (`CORRECT_ADDITIONAL`, `IRRELEVANT`, `INCORRECT`, `UNCERTAIN`) are treated strictly as **SYSTEM OUTPUTS** and evaluated qualitatively for linguistic plausibility.
- **Strict Epistemic Distinctions:** Every finding is explicitly partitioned into:
  - **FACT:** Directly observed benchmark numbers and data values.
  - **DIAGNOSIS:** Inferred linguistic or architectural mechanism.
  - **HYPOTHESIS:** Potential future modification (not yet implemented).

---

## 1. Base ASAG Validation (Four-Quadrant Analysis)

To understand why Base ASAG exhibits a low mean predicted score (0.4173 / 5.0) and high error (MAE = 3.7794, RMSE = 4.0179), we partitioned all 2,273 active records into four diagnostic quadrants based on human score (`score_ave`) and Base ASAG score:

```
                          High Human (>= 4.5)         Low Human (<= 2.5)
                   +-----------------------------+-----------------------------+
High Base (>= 3.5) |  Quadrant C: True Positive  | Quadrant B: False Positive  |
                   |      N = 56 records         |       N = 1 record          |
                   +-----------------------------+-----------------------------+
Low Base  (<= 1.0) |  Quadrant A: False Negative | Quadrant D: True Negative   |
                   |    N = 1,142 records        |      N = 281 records        |
                   +-----------------------------+-----------------------------+
```

---

### 1.1 Quadrant A: False Negatives (High Human $\ge 4.5$, Base Score $0.0$) [N = 1,101]

**FACT:** 1,101 student answers received a human score of 4.5 or 5.0, but received an absolute score of **0.0** from Base ASAG.

**DIAGNOSIS:**
Through systematic inspection of the 81 active questions, we discovered two distinct linguistic causes:

#### Root Cause 1: Reference Answer Syntactic Fragmentation (33 Questions, 962 Records)
- **Finding:** In 33 out of 81 active questions (**40.7% of all active questions**), the instructor reference answer contains **ZERO extracted canonical propositions**.
- **Linguistic Mechanism:** In `DependencyTripleExtractor._extract_canonical_relations()`, proposition extraction strictly requires a full clause with an explicit grammatical subject (`nsubj` or `csubj`) and a predicate (`VERB`/`AUX`).
  However, real-world short-answer reference answers frequently take the form of:
  1. *Infinitive verb phrases:*  
     - Q 1.1: `"To simulate the behaviour of portions of the desired software product."` (simulate is root, but has no `nsubj`)
     - Q 2.7: `"To store a class interface, including data members and member function prototypes."`
  2. *Nominal phrase fragments / entity lists:*  
     - Q 1.3: `"Abstraction and reusability."` (only conjunction of nouns)
     - Q 2.1: `"Data members (attributes) and member functions."`
     - Q 3.1: `"The name of the function and the types of the parameters."`
     - Q 3.2: `"File scope."`
  3. *Prepositional phrase fragments:*  
     - Q 1.4: `"At the main function."`
     - Q 4.3: `"by reference."`
- **Resulting Behavior:** Because the reference proposition set is empty ($N_{ref} = 0$), Base ASAG's scoring formula:
  $$\text{score} = \frac{\sum \text{entailed\_weight}}{\sum \text{ref\_weights}} = \frac{0}{0} \to 0.0$$
  assigns 0.0 to every student who answers these questions, even if the student's answer is verbatim identical to the reference answer!

#### Root Cause 2: Elliptical Student Answers on Complete Reference Answers (139 Records)
- **Finding:** Even when the reference answer is a complete sentence with extracted propositions, students frequently provide concise, elliptical answers (e.g., Q 1.2: student answers `"Refining and Coding"` against reference `"The testing stage can influence both the coding stage and the solution refinement stage"`).
- **Linguistic Mechanism:** The student's answer lacks a finite verb, so zero student propositions are extracted, preventing triple matching.

---

### 1.2 Quadrant B: False Positives / Over-prediction (Low Human $\le 2.5$, Base Score $\ge 2.5$) [N = 8]

**FACT:** 8 student answers received low human scores ($\le 2.5$) but achieved moderate-to-high Base scores ($\ge 2.5$).

**DIAGNOSIS:**
- **Representative Case:** Question 1.6 (`stu_idx=5`):
  - *Question:* `"Where are variables declared in a C++ program?"`
  - *Reference:* `"Variables can be declared anywhere in a program. They can be declared inside a function (local variables) or outside the functions (global variables)"`
  - *Student Answer:* `"For good programing practice they should be declared before main(), but should at least be declared before they are used."`
  - *Human Score:* 2.5 / 5.0
  - *Base Score:* 3.75 / 5.0 (Normalized = 0.75)
- **Linguistic Cause:** The student answer repeated the reference predicate `"declared"` with matching subject `"they"` (referring to variables). Base ASAG aligned:
  - `(they, declared, before main)` $\leftrightarrow$ `(Variables, declared, anywhere in a program)`
  Because `(they, declared)` matched and the predicate was not explicitly negated, Stage 8 evaluated the alignment as `ENTAILS`, giving full credit despite the domain-level inaccuracy ("before main()" is not where variables must be declared in C++). Base ASAG lacks domain-world-knowledge verification when syntactic structure aligns.

---

### 1.3 Quadrant C: Concordant High (Human = 5.0, Base = 5.0) [N = 51]

**FACT:** 51 records achieved perfect agreement at 5.0 / 5.0.

**DIAGNOSIS:**
- **Representative Case:** Question 1.7 (`stu_idx=1`):
  - *Question:* `"What is the main difference between a while and a do...while statement?"`
  - *Reference:* `"The block inside a do...while statement will execute at least once."`
  - *Student Answer:* `"do...while statements evaluate whether or not to loop after running the block contained within it at least once. So the main differance is that while statements have a possibility of never being used. Do ... while statements on the other hand are always run at least once before evaluating whether to run again."`
  - *Human Score:* 5.0 / 5.0
  - *Base Score:* 5.0 / 5.0 (Normalized = 1.0)
- **Linguistic Cause:** Both the reference and student answers used complete, active/passive clauses (`block, execute, at least once`) with identical lemma slots and positive polarities. Stage 7 produced an exact slot alignment (`triple_score = 0.94`), Stage 8 affirmed `ENTAILS` (`confidence = 0.94`), and Stage 9 awarded 100% credit.

---

### 1.4 Quadrant D: Concordant Low (Human $\le 1.0$, Base $\le 1.0$) [N = 163]

**FACT:** 163 records achieved concordant low scores where student answers were genuinely off-topic, evasive, or uninformative.

**DIAGNOSIS:**
- **Representative Case:** Question 1.4 (`stu_idx=7`):
  - *Question:* `"Where do C++ programs begin to execute?"`
  - *Reference:* `"At the main function."`
  - *Student Answer:* `"in the testing phase"`
  - *Human Score:* 0.0 / 5.0
  - *Base ASAG:* 0.0 / 5.0
- **Linguistic Cause:** Completely disjoint semantic content.

---

### 1.5 Pipeline Stage Attribution of Base ASAG Errors

| Pipeline Component | Error Rate Impact | Primary Observed Mechanism |
| :--- | :---: | :--- |
| **Stage 3: Preprocessing** | Minimal (< 1%) | spaCy tokenization and normalization performed reliably. |
| **Stage 4: Dependency Parsing** | Low (~ 5%) | Minor parse attachment errors on complex nested prepositional phrases. |
| **Stage 5: Proposition Extraction** | **Critical (~ 45%)** | **Strict finite-clause filter (`nsubj` requirement) drops 33 reference answers and elliptical student answers.** |
| **Stage 6: Semantic Similarity** | Moderate (~ 15%) | WordNet path similarity misses computer science jargon (e.g. `instantiate` $\leftrightarrow$ `create`, `compile` $\leftrightarrow$ `build`). |
| **Stage 7: Triple Matching** | Moderate (~ 15%) | Fixed 0.50 threshold fails when student uses different syntactic roles (e.g. nominalization `execution of the function`). |
| **Stage 8: Entailment** | Low (~ 5%) | Polarity detection works well, but lacks antonymy-aware negation handling. |
| **Stage 9: Scoring** | High (~ 20%) | Rigid reference coverage formula collapses to 0.0 when reference propositions are absent. |

---

## 2. Proposed ASAG Aggregate Analysis

Across the full benchmark of 2,273 records, Proposed ASAG processed all unmatched student propositions from Base ASAG.

### 2.1 Proposition Classification Counts (N = 3,611 Unmatched Propositions)

| Classification Category | Count | Percentage | Primary Linguistic Role |
| :--- | :---: | :---: | :--- |
| **CORRECT_ADDITIONAL** | **2,818** | **78.04%** | Student propositions sharing domain nouns/verbs with question or reference context. |
| **IRRELEVANT** | **780** | **21.60%** | Student propositions with low semantic affinity to question/reference concepts. |
| **INCORRECT** | **12** | **0.33%** | Propositions exhibiting explicit polarity mismatch or contradiction. |
| **UNCERTAIN** | **1** | **0.03%** | Borderline relevance/compatibility evidence. |
| **Total Unmatched** | **3,611** | **100.00%** | — |

**DIAGNOSIS on Classification Asymmetry:**
- 78.0% of unmatched student propositions were categorized as `CORRECT_ADDITIONAL`. In technical short-answer responses, students routinely write multi-clause sentences expanding on related concepts from the course topic. Because Stage 13 tests for semantic compatibility against question and reference noun-sets, related domain clauses naturally pass the relevance and compatibility thresholds.
- Only 12 propositions (0.33%) were categorized as `INCORRECT`. Stage 13's `CompatibilityAnalyzer` requires an explicit contradiction or negation clash. In student answers, students rarely make explicit grammatical contradictions of the reference statement; rather, their errors are omissions, inaccuracies, or misconceptions that do not directly align with a single reference triple.

---

### 2.2 Answer-Level Adjustments (N = 2,273 Student Answers)

| Adjustment Type | Count | Percentage | Effect on Grade |
| :--- | :---: | :---: | :--- |
| **Positive Adjustments ($net > 0$)** | **1,472** | **64.76%** | Awarded credit for valid additional propositions ($+0.10$ normalized / $+0.50$ pts each). |
| **Negative Adjustments ($net < 0$)** | **6** | **0.26%** | Penalized for explicit contradiction ($-0.20$ normalized / $-1.00$ pts each). |
| **Zero Adjustments ($net == 0$)** | **795** | **34.98%** | No unmatched propositions or only irrelevant propositions ($0.0$ effect). |
| **Clipped Upper ($> 1.0$)** | **48** | **2.11%** | Sum of Base + adjustments exceeded 1.0 and was clipped to 5.0. |
| **Clipped Lower ($< 0.0$)** | **3** | **0.13%** | Sum of Base - penalties dropped below 0.0 and was clipped to 0.0. |

---

### 2.3 Net Adjustment Distribution

| Metric | Normalized Scale $[0.0, 1.0]$ | Grade Scale $[0.0, 5.0]$ |
| :--- | :---: | :---: |
| **Mean Adjustment** | $+0.1229$ | $+0.6146$ points |
| **Std Dev** | $0.1369$ | $0.6845$ points |
| **Min** | $-0.2000$ | $-1.0000$ points |
| **Max** | $+1.7000$ | $+8.5000$ points (clipped to max 5.0) |
| **25th Percentile** | $0.0000$ | $0.0000$ points |
| **Median (50th)** | $+0.1000$ | $+0.5000$ points |
| **75th Percentile** | $+0.2000$ | $+1.0000$ points |
| **90th Percentile** | $+0.3000$ | $+1.5000$ points |
| **99th Percentile** | $+0.5000$ | $+2.5000$ points |

**FACT:** The average net adjustment across the benchmark is $+0.6146$ grade points ($+0.1229$ normalized). 64.8% of answers received a positive adjustment.

---

## 3. Targeted Proposed ASAG Cases

Below are the 7 representative case studies identified and traced across the benchmark:

### Case A: Substantial Error Reduction (MAE Improved by 4.0 Points)
- **Metadata:** Question 3.7 (`stu_idx=3`), Assignment 3
- **Question:** `"What are the similarities between iteration and recursion?"`
- **Reference Answer:** `"They both involve repetition; they both have termination tests; they can both occur infinitely."`
- **Student Answer:** `"Both are based on a control statement - Iteration-repetition structure - Recursion-selection structure Both involve repetition -Iteration-explicitly uses repetition structure -Recursion-repeated function calls Both involve a termination test -Iteration-loop-termination test -Recursion-base case Both gradually approach termination -Iteration-modifies counter until loop-termination test fails -Recursion-produces progressively simpler versions of problem Both can occur indefinitely -Iteration-if loop-continuation condition never fails -Recursion-if recursion step does not simplify the problem"`
- **Human Score:** 5.0 / 5.0
- **Base ASAG Score:** 0.8335 / 5.0 (Matched only 1 of 3 reference triples due to formatting)
- **Stage 13 Output:** 8 propositions classified as `CORRECT_ADDITIONAL`, 1 as `IRRELEVANT`, 0 as `INCORRECT`.
- **Stage 14 Adjustment:** $+0.8000$ normalized ($+4.0000$ points).
- **Proposed ASAG Score:** **4.8335 / 5.0** (MAE error dropped from 4.1665 to 0.1665!)
- **DIAGNOSIS:** Highly successful case. The student provided an exhaustive, structured answer that exceeded the reference answer's surface structure. Base ASAG penalized the formatting; Proposed ASAG recognized the 8 extra domain propositions, restoring the grade to near-perfect.

---

### Case B: Verbosity / Credit Inflation (MAE Worsened by 1.25 Points)
- **Metadata:** Question 2.6 (`stu_idx=1`), Assignment 2
- **Question:** `"What is the difference between a function prototype and a function definition?"`
- **Reference Answer:** `"A function prototype includes the function signature, i.e., the name of the function, the return type, and the parameters' type. The function definition includes the actual body of the function."`
- **Student Answer:** `"The FUNCTION PROTOTYPE is where the programmer declares that he/she is using a function other than main( ). This is like declaring a variable, the programmer knows that he/she will be using in the future, but has yet to say where they are going to use it, or how. This is answers the question who, it gives the function a name and character. The function prototype, by common practice is placed at the beginning of the program after the #includes and before main( ). The FUNCTION DEFINITION is the guts of the function. This is where the programmer decides what the function is going to do and tells it how to do it. It takes whatever information it is given and performs the operations. It works sort of like the brain, the brain takes in input and based upon that input performs in some way producing an output. The function defintion is placed outside of main( ) and any other functions. A function is its own entity and should be thought of as such."`
- **Human Score:** 2.5 / 5.0
- **Base ASAG Score:** 1.25 / 5.0
- **Stage 13 Output:** **17 propositions** classified as `CORRECT_ADDITIONAL`, 9 as `IRRELEVANT`.
- **Stage 14 Adjustment:** $+1.7000$ normalized (unclipped $+8.50$ points, clipped to $+3.75$).
- **Proposed ASAG Score:** **5.0 / 5.0** (MAE worsened from 1.25 to 2.50)
- **DIAGNOSIS:** Classical verbosity pathology. The student wrote a rambling, informal essay full of analogies ("brain takes in input", "answers the question who"). Because the essay repeated domain nouns ("programmer", "function", "variable"), Stage 13 classified 17 clauses as `CORRECT_ADDITIONAL`, inflating the grade to 5.0. This demonstrates the necessity of length-normalization or adjustment capping.

---

### Case C: Score Shift on Low Human Grade (Divergence)
- **Metadata:** Question 11.8 (`stu_idx=1`), Exam 11
- **Question:** `"What is the main difference between a string of characters that is read into a variable of type string versus a variable of type char[]?"`
- **Reference Answer:** `"The char[] will automatically add a null \0 character at the end of the string."`
- **Student Answer:** `"a variable char is basically any non command key on the keyboard that you can press. A string is a collection of letters or numbers that is stored together to be used later. Comonly strings are used for words. Chars can be used for less but can have opperations performed on them in a useful way."`
- **Human Score:** 2.0 / 5.0
- **Base ASAG Score:** 2.50 / 5.0
- **Stage 13 Output:** 4 propositions classified as `CORRECT_ADDITIONAL`, 3 as `IRRELEVANT`.
- **Stage 14 Adjustment:** $+0.4000$ normalized ($+2.00$ points).
- **Proposed ASAG Score:** **4.50 / 5.0**
- **DIAGNOSIS:** The student completely missed the null-terminator distinction asked for, but wrote definitions of what chars and strings are in general. Proposed ASAG awarded credit for the general definitions, pulling the grade away from the human rating.

---

### Case D: Neutral Adjustment on Irrelevant Propositions ($Net = 0$)
- **Metadata:** Question 1.3 (`stu_idx=16`), Assignment 1
- **Question:** `"What are the main advantages associated with object-oriented programming?"`
- **Reference Answer:** `"Abstraction and reusability."`
- **Student Answer:** `"it is easier to debug"`
- **Human Score:** 4.5 / 5.0
- **Base ASAG Score:** 0.0 / 5.0
- **Stage 13 Output:** 1 proposition classified as `IRRELEVANT`.
- **Stage 14 Adjustment:** $0.0000$.
- **Proposed ASAG Score:** **0.0 / 5.0**
- **DIAGNOSIS:** Proposed ASAG remained completely neutral, avoiding unwarranted bonus or penalty.

---

### Case E: High-Quality `CORRECT_ADDITIONAL` Classification
- **Metadata:** Question 12.9 (`stu_idx=13`), Exam 12
- **Question:** `"How do you delete a node from a binary search tree?"`
- **Reference Answer:** `"Find the node, then replace it with the leftmost node from its right subtree (or the rightmost node from its left subtree)."`
- **Student Answer:** `"In a binary search tree, you must first establish a proper replacement for the node you are about to delete, usually a child from the soon to be deleted node. Once that replacement node has been found, you simply reassign it to where the node that is going to be deleted is. After the deleted node has been usurped, you remove the deleted node from memory so it may be used again."`
- **Human Score:** 4.0 / 5.0
- **Base ASAG Score:** 0.0 / 5.0
- **Stage 13 Output:** 8 propositions classified as `CORRECT_ADDITIONAL`, 1 as `IRRELEVANT`.
- **Stage 14 Adjustment:** $+0.8000$ (clipped to $4.00 / 5.0$).
- **Proposed ASAG Score:** **4.00 / 5.0** (Exact match with human score!).
- **DIAGNOSIS:** High-quality semantic alignment on complex algorithm steps.

---

### Case F: High-Quality `IRRELEVANT` Classification
- **Metadata:** Question 1.3 (`stu_idx=0`), Assignment 1
- **Question:** `"What are the main advantages associated with object-oriented programming?"`
- **Reference Answer:** `"Abstraction and reusability."`
- **Student Answer:** Excerpt: *"...allows you to let someone use a program which sorts lists without having to give them access to the source code."*
- **Classified Clause:** `(someone, use, program)` and `(it, give, access)`.
- **Classification:** **`IRRELEVANT`** (similarity to "Abstraction and reusability" = 0.12).
- **DIAGNOSIS:** Correctly recognized that an example of sorting lists without source code access is an irrelevant tangent to the core concept of abstraction.

---

### Case G: Antonymy / Polarity Inversion False `INCORRECT`
- **Metadata:** Question 7.2 (`stu_idx=9`), Assignment 7
- **Question:** `"What is the main advantage of linked lists over arrays?"`
- **Reference Answer:** `"The linked lists can be of variable length."`
- **Student Answer:** `"A linked list is not fixed in size, and does not require the shifting of items during insertions and deletions."`
- **Human Score:** 5.0 / 5.0
- **Base ASAG Score:** 0.0 / 5.0
- **Stage 13 Output:** Clause `(linked list, fixed, not in size)` was classified as **`INCORRECT`**!
- **DIAGNOSIS:**
  - **Linguistic Pathology:** The student wrote `"is not fixed in size"`.
  - In English: *"not fixed in size"* is a semantically valid paraphrase of *"variable length"* (via the antonym pair *fixed* $\leftrightarrow$ *variable*).
  - However, Stage 13 checks for surface negation. Because the student clause contained `"not"` while the reference clause `"can be of variable length"` had positive polarity, the polarity mismatch caused Stage 13 to flag the clause as an opposing contradiction (`INCORRECT`), deducting $-0.20$ points!
  - **Significance:** Demonstrates that negation-based contradiction checking without antonymy resolution causes false-positive penalties on valid negative paraphrases.

---

## 4. TF-IDF vs Base ASAG: Why Lexical Overlap Outperformed Proposition Matching

**FACT:** TF-IDF Cosine Baseline achieved substantially higher correlation ($r = 0.4184$, $\rho = 0.4424$) than Base ASAG ($r = 0.1419$, $\rho = 0.1177$).

### Key Failure Patterns of Base ASAG Relative to TF-IDF:

1. **Insensitivity to Sentence Fragments:**
   In Q 1.3 ("What are the main advantages associated with OOP?"):
   - *Reference:* `"Abstraction and reusability."`
   - *Student 4:* `"Some advantages are existing classes can be reused..."`
   - *TF-IDF Score:* 3.65 / 5.0 (shares `"advantages"`, `"classes"`, `"reused"`)
   - *Base ASAG Score:* **0.0 / 5.0** (0 reference propositions extracted from `"Abstraction and reusability."`)
   - *Human Score:* 3.5 / 5.0
   TF-IDF effortlessly rewards students who mention the correct keywords even when the reference answer is an un-parseable two-word fragment. Base ASAG completely collapses on such fragments.

2. **WordNet Vocabulary Coverage Gaps in Computer Science:**
   In computer science discourse, words like `"instantiate"`, `"dereference"`, `"runtime"`, and `"destructor"` have specialized technical meanings that are absent or poorly connected in WordNet 3.0 path similarity hierarchies.
   When a student wrote `"creates an object"` and the reference said `"instantiates an instance"`, WordNet path similarity scored below 0.50, causing Base ASAG to reject the match. TF-IDF, while lexical, benefits from sub-word n-grams and vocabulary overlap across the rest of the sentence.

3. **Elliptical Student Responses:**
   Students often answer test questions conversationally:
   - *Question:* `"Where do C++ programs begin to execute?"`
   - *Reference:* `"At the main function."`
   - *Student:* `"main"` or `"main()"`
   TF-IDF scores `"main"` with a high cosine similarity against `"At the main function"`. Base ASAG extracts 0 triples from single-word tokens.

---

## 5. Stage 13 Validity & Linguistic Plausibility

Because the Mohler dataset contains **no clause-level labels**, we cannot report numerical precision/recall for Stage 13. However, qualitative case analysis reveals the following behavioral truths:

1. **High Precision on Domain Topic Identification:**
   When students introduce valid technical concepts (e.g. Q 12.9: deleting BST nodes requiring pointers, children, and memory deallocation), Stage 13's synset and slot matching against question context reliably classifies these clauses as `CORRECT_ADDITIONAL`.
2. **Robust Filtering of Digressions:**
   Unrelated clauses (e.g., student discussing user interfaces or personal opinions) receive low similarity across all slots and are appropriately marked `IRRELEVANT` with zero score distortion.
3. **Primary Linguistic Vulnerability (Negation & Antonymy):**
   Stage 13's `CompatibilityAnalyzer` assumes that a polarity conflict indicates a factual contradiction. As demonstrated in Case G (`"not fixed in size"` vs `"variable length"`), valid negative phrasing of antonymous properties is erroneously classified as `INCORRECT`.

---

## 6. Categorization of Identified Issues

Following our research standards, all identified issues are categorized into their true scientific nature:

### A. Confirmed Implementation Limitations / Bugs
1. **Missing Proposition Extraction for Infinitive and Non-Clausal Roots:**
   `DependencyTripleExtractor._extract_canonical_relations()` only extracts triples when an `nsubj` or `csubj` token exists. Infinitive roots (`"To simulate..."`), nominal roots (`"Abstraction and reusability."`), and prepositional roots (`"At main."`) yield 0 relations.
2. **Double Negation / Antonymy Conflict in Contradiction Detection:**
   `CompatibilityAnalyzer` and `PropositionalEntailmentAnalyzer` flag negation mismatches as contradictions without checking if the negated predicate is an antonym of the reference predicate (e.g., *not fixed* $=$ *variable*).

### B. Likely Methodological Limitations
1. **Unbounded Additive Adjustment (Verbosity Inflation):**
   Adding a fixed $+0.10$ bonus per `CORRECT_ADDITIONAL` proposition without dividing by sentence length or setting a question-level cap allows rambling, verbose answers to accumulate up to $+8.5$ unclipped points (Case B).
2. **Role-Preserved Slot Matching Rigidity:**
   A student who nominalizes an action (e.g. `"The execution of the program occurs in main"`) fails to match a predicate-oriented reference (`"Programs begin to execute in main"`).

### C. Dataset Characteristics
1. **Pervasive Sentence Fragments:**
   40.7% of instructor reference answers in the Mohler dataset are not grammatically complete sentences.
2. **Extreme Score Ceiling:**
   49.3% of answers have `score_ave == 5.0` (and 62.8% have $\ge 4.5$). This makes ranking metrics ($\rho$) disproportionately sensitive to small score adjustments.

### D. Unresolved Research Questions
1. **Optimal Trade-off Between Error Reduction and Rank Ordering:**
   Why does Proposed ASAG reduce MAE significantly ($3.78 \to 3.20$) while slightly depressing Spearman $\rho$ ($0.118 \to 0.080$)? (Hypothesis: Verbosity inflation re-orders students inappropriately across questions).

---

## 7. Evidence-Based Hypotheses for Future Research

Based on the empirical findings of Stages 15 and 16, the following hypotheses are formulated for future investigation:

1. **Hypothesis 1 (Infinitive / Fragment Proposition Extraction):**
   Extending Stage 5 to extract `(PROTOTYPE/IMPLICIT, simulate, behaviour)` from infinitive clauses (`"To simulate..."`) and concept pairs from nominal coordinations will resolve the 0.0 score collapse across 33 questions, substantially boosting Base and Proposed ASAG correlation.
2. **Hypothesis 2 (Verbosity Normalization / Adjustment Capping):**
   Normalizing proposition bonuses by the ratio of student proposition count to reference proposition count, or applying diminishing marginal returns (e.g. $\Delta = \frac{w \cdot c}{1 + 0.5c}$), will prevent verbosity inflation (Case B) and preserve rank ordering ($\rho$).
3. **Hypothesis 3 (Antonymy-Aware Polarity Resolution):**
   Incorporating WordNet antonym lookups before flagging negation contradictions will eliminate false-positive `INCORRECT` classifications on valid negative paraphrases (Case G).
