# Qualitative Error Analysis Report: Mohler ASAG Benchmark

**Evaluation Set:** 2,273 Active Student Answers  
**Pipeline:** Frozen Current Proposed ASAG (Phases 1–9) with Repaired Evidence Layer  
**Objective:** Diagnostic investigation of 10 representative failure and success modes on actual Mohler records.

---

## 1. Ten Representative Mohler Case Studies

### Case 1: Correct Answer Scored Correctly
- **Question 1.1:** *"What is the main advantage of developing a prototype of a software product?"*
- **Reference Answer:** *"To simulate the behaviour of portions of the desired software product."*
- **Student Answer (Student 9):** *"Simulating the behavior of only a portion of the desired software product."*
- **Scores:** Human = **5.00** | V0 Baseline = **3.91** | V1 Base ASAG = **5.00** | V3 Current Proposed = **4.92**
- **Extracted Proposition:** `(subject: None, predicate: 'simulating', object: 'behavior', polarity: POSITIVE)`
- **Component Tracing:**
  - Hybrid infinitive/gerund argument extractor correctly identified the non-finite predicate `simulate` and direct object `behavior`.
  - Semantic Matcher V2 verified exact lemma equivalence between `simulate`/`simulating` and `behaviour`/`behavior`.
  - Base reference proposition was completely covered ($\text{score} = 1.0$), resulting in near-perfect grading without penalty.

---

### Case 2: Correct Paraphrase Scored Poorly
- **Question 1.1:** *"What is the main advantage of developing a prototype of a software product?"*
- **Reference Answer:** *"To simulate the behaviour of portions of the desired software product."*
- **Student Answer (Student 1):** *"To simulate portions of the desired final product with a quick and easy program that does a small specific job. It is a way to help see what the problem is and how you may solve it in the final project."*
- **Scores:** Human = **5.00** | V0 Baseline = **2.18** | V1 Base ASAG = **0.00** | V3 Current Proposed = **0.00**
- **Component Tracing:**
  - The student used `portions` as the direct object of `simulate` (*"simulate portions of the desired final product"*) rather than `behavior`.
  - Clausal dependency triple matching required aligned subject, predicate, and object slots; the shift in syntactic direct object caused slot similarity to drop below threshold (0.55).
  - The second explanatory sentence (*"It is a way to help see what the problem is..."*) was evaluated by the evidence layer as `UNCERTAIN` and `IRRELEVANT`, contributing zero base coverage and yielding a final grade of 0.00.

---

### Case 3: Partial Answer Scored Partially
- **Question 1.6:** *"Where are variables declared in a C++ program?"*
- **Reference Answer:** *"Variables can be declared anywhere in a program. They can be declared inside a function (local variables) or outside the functions (global variables)"*
- **Student Answer (Student 0):** *"They can be declared right before they are used, but it is a good practice to declare them at the beginning of the program and label what they are food."*
- **Scores:** Human = **2.00** | V0 Baseline = **1.63** | V1 Base ASAG = **2.50** | V3 Current Proposed = **2.50**
- **Component Tracing:**
  - Reference contains 2 clausal propositions: (1) `Variables declared anywhere`, (2) `Variables declared inside/outside function`.
  - Student matched proposition (1) (`can be declared right before they are used`), receiving a base normalized score of $0.50$ ($2.5/5.0$).
  - Proposition (2) was completely absent, properly bounding credit at half-marks.

---

### Case 4: Correct Additional Information (Auditable Domain Evidence)
- **Question 10.6:** *"What is the inorder traversal of a binary tree?"*
- **Reference Answer:** *"Traverse the left subtree, then the root, then the right subtree."*
- **Student Answer (Student 1):** *"The inorder traversal of a binary tree visits the node of a binary tree in order according to their data values."*
- **Scores:** Human = **2.50** | V0 Baseline = **1.16** | V1 Base ASAG = **0.00** | V3 Current Proposed = **0.50**
- **Unmatched Proposition:** `'traversal of a binary tree visits the node'` (modifiers: `inorder`, `tree`, `binary`, `node`, `value`)
- **Matched Rule:** `BST_INORDER_SORTED` [Cormen et al., 2009, Theorem 12.1]
- **Classification:** `CORRECT_ADDITIONAL` (`EvidenceStatus.SUPPORTED`)
- **Component Tracing:**
  - Base ASAG scored 0.0 because the reference answer defines recursive traversal steps (`left, root, right`) rather than traversal outputs.
  - The evidence verifier recognized the student's assertion about inorder traversal ordering, verified it against `BST_INORDER_SORTED`, and awarded a structured positive adjustment (+0.50).

---

### Case 5: Incorrect Additional Information (Value Conflict)
- **Question 4.3:** *"What are the main differences between passing an array and passing an individual array element to a function?"*
- **Reference Answer:** *"by reference."*
- **Student Answer (Student 10):** *"Specify array name without brackets. Array size is normally passed as another argument so the function can process the specific number of elements in the array. Arrays are passed by reference. Individual array elements passed by value. Functions that take arrays as arguments."*
- **Scores:** Human = **5.00** | V0 Baseline = **2.34** | V1 Base ASAG = **0.00** | V3 Current Proposed = **0.88**
- **Unmatched Proposition:** `'elements passed by value'`
- **Detected Contradiction:** `VALUE_CONFLICT`: Incompatible property value on `pass_mechanism`: student claims `value` while reference specifies `reference`.
- **Classification:** `INCORRECT` (`EvidenceStatus.CONTRADICTED`)
- **Component Tracing:**
  - In C++, entire arrays are passed by reference, while individual array elements are passed by value. The student answer was factually correct.
  - However, the reference answer was a 2-word fragment: *"by reference."*
  - The property contradiction detector compared the student's clause `elements passed by value` against the sole reference fragment `by reference` and incorrectly flagged a value conflict on pass mechanism.

---

### Case 6: Irrelevant Additional Information
- **Question 1.1:** *"What is the main advantage of developing a prototype of a software product?"*
- **Reference Answer:** *"To simulate the behaviour of portions of the desired software product."*
- **Student Answer (Student 0):** *"High risk problems are address in the prototype program to make sure that the program is feasible. A prototype may also be used to show a company that the software can be possibly programmed."*
- **Scores:** Human = **3.50** | V0 Baseline = **1.09** | V1 Base ASAG = **0.00** | V3 Current Proposed = **0.00**
- **Unmatched Propositions:**
  - `'program is feasible'` $\rightarrow$ Lexical relevance = 0.04 (< 0.35) $\rightarrow$ `IRRELEVANT`
  - `'software can be possibly programmed'` $\rightarrow$ Lexical relevance = 0.18 (< 0.35) $\rightarrow$ `IRRELEVANT`
- **Component Tracing:**
  - Neither proposition matched question focus terms or reference keywords.
  - Classified as `IRRELEVANT` (`EvidenceStatus.OFF_TOPIC`), correctly prevented from receiving positive credit.

---

### Case 7: Unsupported but Relevant Information
- **Question 1.1:** *"What is the main advantage of developing a prototype of a software product?"*
- **Reference Answer:** *"To simulate the behaviour of portions of the desired software product."*
- **Student Answer (Student 0):** *"...A prototype may also be used to show a company that the software can be possibly programmed."*
- **Unmatched Proposition:** `'prototype may also be used'`
- **Evidence Decision:** `EvidenceStatus.UNVERIFIED`
- **Classification:** `UNCERTAIN`
- **Component Tracing:**
  - Proposition is topically relevant to software prototyping ($0.42 \ge 0.35$).
  - However, no curated domain knowledge rule exists in the frozen 3-rule set to verify assertions about company demonstrations.
  - Correctly held as `UNCERTAIN` rather than assumed true, avoiding unearned grade inflation.

---

### Case 8: False Evidence Support (Ontological Generalization Error)
- **Question 10.6:** *"What is the inorder traversal of a binary tree?"*
- **Reference Answer:** *"Traverse the left subtree, then the root, then the right subtree."*
- **Student Answer (Student 1):** *"The inorder traversal of a binary tree visits the node of a binary tree in order according to their data values."*
- **Component Tracing:**
  - The question asks about a **general binary tree**. In general binary trees, inorder traversal does NOT visit nodes in sorted order of their data values (that holds ONLY for binary *search* trees).
  - The student made a conceptual mistake by attributing BST properties to general binary trees.
  - The evidence rule `BST_INORDER_SORTED` matched because the rule allowed `"tree"` and `"binary"` in the entity tokens.
  - **Diagnosis:** The entity matcher must strictly require the compound specifier `"search"` when verifying BST-specific ordering properties.

---

### Case 9: False Contradiction (Antonym Co-occurrence in Acronyms)
- **Question 8.1:** *"What is a stack?"*
- **Reference Answer:** *"A data structure that can store elements, which has the property that the last item added will be the first to be removed (or last-in-first-out)"*
- **Student Answer (Student 5):** *"a stack is a data structure that uses push to insert an item and pop to remove ad item. The stack use a last in first out structure for inserting and removing items."*
- **Scores:** Human = **5.00** | V0 Baseline = **1.86** | V1 Base ASAG = **0.00** | V3 Current Proposed = **0.00**
- **Detected Contradiction:** `ANTONYM_CONFLICT: Lexical antonymy conflict: 'last' directly opposes reference concept 'first'.`
- **Classification:** `INCORRECT`
- **Component Tracing:**
  - The student correctly stated the LIFO principle (*"last in first out"*).
  - The reference states *"last item added will be the first to be removed"*.
  - The property contradiction detector matched the token `'last'` in the student clause against `'first'` in the reference and flagged an antonym conflict.
  - Because `first` and `last` inherently co-occur in the domain acronym LIFO, the antonym detector fired a false contradiction, penalizing a correct student.

---

### Case 10: Extraction/Parsing Failure on Non-Sentential Reference Fragments
- **Question 1.3:** *"What are the advantages of modular programming?"*
- **Reference Answer:** *"Abstraction and reusability."*
- **Student Answer (Student 0):** *"Modular programs are easier to code and debug."*
- **Scores:** Human = **3.00** | V0 Baseline = **1.54** | V1 Base ASAG = **0.00** | V3 Current Proposed = **0.00**
- **Component Tracing:**
  - The instructor reference answer is a two-word nominal fragment without a subject or predicate.
  - Base ASAG's dependency triple extractor requires a finite verb ROOT; it extracted 0 reference propositions, permanently capping the maximum possible score at 0.00.
  - The student provided alternative, legitimate advantages of modular programming (*"easier to code and debug"*), but because the reference was non-sentential and unelaborated, semantic alignment failed completely.

---

## 2. Summary of Failure Mode Frequencies

| Failure Mode Category | Primary Contributing Component | Benchmark Impact |
| :--- | :--- | :--- |
| **Non-sentential Reference Blindness** | Dependency triple extractor in Base ASAG | Affected 33/81 questions (41.0% of records). Base ASAG scores 0.0 everywhere. |
| **Antonym Co-occurrence False Contradictions** | Antonym contradiction detector | Flagged correct answers containing domain polar pairs (e.g. LIFO `first`/`last`, pass-by `value`/`reference`). |
| **Syntactic Head Divergence in Paraphrases** | Dependency slot alignment (S-P-O matching) | Students expressing meaning via different syntactic objects (e.g. `simulate portions` vs `simulate behavior`) failed slot matching. |
| **Curated Rule Knowledge Gaps** | Domain evidence verifier (3 rules only) | 1,672 valid technical elaborations were held as `UNCERTAIN` because curated rules were limited to 3 proof-of-concept topics. |
| **Ontological Concept Blurring** | Entity matcher in domain knowledge | Confused general binary trees with binary search trees due to partial token overlap. |
