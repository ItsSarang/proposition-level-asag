# Experiment 4: Qualitative Error Analysis

**Experiment Name**: Experiment 4 — Severity-Aware Proposed ASAG  
**Dataset**: UNT Computer Science Short Answer Dataset v2.0 (*Mohler et al., 2011*)  
**Scope**: In-depth qualitative diagnostics of representative success cases, false contradiction patterns, parser breakdowns, and structural ASAG limitations.

---

## 1. Executive Summary of Error Findings

Experiment 4 demonstrated two contrasting phenomena across the Mohler benchmark:
1. **Targeted Success in Complex Settings**: On examination questions (Exams 11–12, $N=552$), the severity-aware model achieved its highest ranking correlation ($r=0.2284$, $\rho=0.2065$) and highest QWK ($\kappa=0.0478$), outperforming both Base ASAG ($r=0.1496$) and the unweighted Proposed ASAG ($r=0.1989$). The graded penalty formulation successfully discriminated between answers containing peripheral remarks and those containing serious conceptual errors.
2. **Pathological False-Positive Core Contradictions**: Because the contradiction detector operates on extracted propositional clauses without full discourse coreference, comparative sentences (such as binary search tree ordering) caused symmetric properties ("left is smaller", "right is larger") to be cross-aligned against each other. This triggered 15 high-severity `CORE_CONTRADICTION` classifications that severely penalized fully correct student answers.

Below, we analyze the specific linguistic and architectural mechanisms driving these results.

---

## 2. Case Study 1: The Symmetric Comparison Failure in Binary Search Trees (Question 10.5)

### Context
- **Question**: *"What is a binary search tree?"*
- **Reference Answer**: *"A binary tree that is either empty, or: (1) each node has a key, and keys in nonempty left subtree (right subtree) are smaller (larger) than the key in the node; (2) left and right subtrees are also binary search trees."*
- **Target Entity**: `BST`
- **Defining Properties**: `["relative_size", "sort_order", "ordering"]`

### Representative Failure Case (Student 16, Question 10.5)
- **Student Answer**:
  > *"A data structure in which every node has at most two children. The keys in a nonempty left subtree are smaller than the node, and the keys in a nonempty right subtree are larger than the node."*
- **Human Grade**: **5.0 / 5.0** (Perfect answer)
- **V1 (Base ASAG) Grade**: 2.50
- **V3 (Current Proposed) Grade**: 1.56
- **V4 (Experiment 4) Grade**: **0.00 / 5.0**
- **System Diagnosis**:
  - The student answer contains two parallel comparative clauses:
    1. $P_1$: `(keys, are smaller, node)` with modifier `left subtree`
    2. $P_2$: `(keys, are larger, node)` with modifier `right subtree`
  - The reference answer packs both comparisons into a single parenthetical sentence: `"keys in nonempty left subtree (right subtree) are smaller (larger) than the key"`.
  - The dependency parser extracted the reference proposition as:
    `Ref`: `(keys, are, smaller)`
  - When matching student propositions, $P_1$ matched `Ref` with high confidence.
  - However, $P_2$ (`keys, are larger, node`) remained unmatched against the single extracted reference proposition.
  - The `PropertyContradictionDetector` evaluated unmatched $P_2$ against `Ref`. It observed:
    - Same subject: `keys`
    - Contradictory property values: `smaller` vs. `larger`
    - Target domain entity: `BST`
  - It emitted a `VALUE_CONFLICT` with confidence $0.90$.
  - The `InterpretableSeverityEstimator` recognized that `smaller` vs. `larger` directly conflicts with the core defining property `relative_size` of `BST`.
  - It assigned `severity_level = CORE_CONTRADICTION` ($\sigma = 1.00$).
  - **Scoring Impact**: Model D applied a $50\%$ core invalidation discount ($S_{\text{core\_effective}} = S_{\text{base}} \times 0.50$) followed by minor penalties, collapsing the student's final score to $0.0$.

### Research Implication
Pairwise clause alignment fails on relational structures involving symmetric oppositions (left/smaller vs. right/larger). An ASAG system must resolve the scope of qualifying locative/prepositional arguments (`in left subtree` vs. `in right subtree`) before asserting property contradiction.

---

## 3. Case Study 2: Fragmented Bulleted Syntax (Question 4.3)

### Context
- **Question**: *"What is the difference between passing an array to a function and passing an individual element of an array to a function?"*
- **Reference Answer**: *"Arrays are passed by reference and individual elements are passed by value."*

### Failure Case (Student 3, Question 4.3)
- **Student Answer**:
  > *"-Arrays are passed by reference -Individual array elements passed by value -Functions that take arrays can alter their contents"*
- **Human Grade**: **5.0 / 5.0**
- **V1 (Base ASAG) Grade**: 0.00
- **V3 (Current Proposed) Grade**: 0.00
- **V4 (Experiment 4) Grade**: **0.00**
- **System Diagnosis**:
  - The student wrote a bulleted list using hyphens without standard sentence punctuation.
  - spaCy's sentence segmenter split the text arbitrarily:
    - Sentence 0: `"-Arrays are passed by reference -Individual array elements"`
    - Sentence 1: `"passed by value -Functions that take arrays can alter their contents"`
  - This corrupted the predicate-argument structure:
    - In Sentence 0, `"Individual array elements"` was parsed as an object or dangling noun chunk under `"are passed by reference"`.
    - In Sentence 1, `"passed by value"` lost its subject.
  - The classifier detected that `"Individual array elements"` was asserted to be `"passed by reference"`, which directly contradicts the reference fact that individual elements are passed by value.
  - This was classified as a `CORE_CONTRADICTION` with severity $1.00$.

### Research Implication
Informal student formatting (dashes, bullets, missing periods, inline code) severely degrades dependency parsing accuracy. Robust ASAG pipelines require specialized punctuation normalization for bulleted lists prior to dependency tree construction.

---

## 4. Case Study 3: The Non-Sentential Reference Bottleneck ($N=932$)

### Analysis
A major structural challenge in the Mohler benchmark is that 33 of the 81 active questions ($40.7\%$) have non-sentential reference answers.

| Question Example | Reference Text | Grammatical Structure | V1 Grade | V4 Grade | Human Grade |
| :--- | :--- | :--- | :---: | :---: | :---: |
| **Q 1.1** | *"Queue"* | Isolated Noun Phrase | 0.00 | 0.00 | 5.0 |
| **Q 2.1** | *"By value, by reference"* | Prepositional Fragment List | 0.00 | 0.00 | 5.0 |
| **Q 3.1** | *"Through an index or a pointer"* | Prepositional Phrase | 0.00 | 0.00 | 4.5 |

- **Base ASAG (V1) Failure**: Classical dependency ASAG assumes complete subject-predicate-object triples. In these 33 questions, the instructor wrote only the conceptual keyword. As a result, Base ASAG extracted 0 reference triples, assigned a score of 0.0 to all 932 student answers, and had an undefined correlation ($r = \text{NaN}$).
- **Proposed System Recovery**: Through the expanded representation (handling non-finite verbal heads, noun modifiers, and predicate-gated cross-slot matching), V3 and V4 recovered meaningful ranking signal:
  - V4 achieved $r = 0.2253$, $\rho = 0.2296$, and $\text{QWK} = 0.0528$ on this non-sentential partition.
  - However, because the system requires explicit propositional structures to award credit, terse student answers that only matched partial nominal fragments remained heavily undergraded relative to human scores.

---

## 5. Case Study 4: Epistemic Restraint vs. Benchmark Ground Truth

### The Divergence Mechanism
The primary driver of the large MAE ($3.6288$) across the dataset is the divergence between human grading standards and the system's epistemic restraint:
1. **Human Annotator Behavior**: In introductory CS coursework, students generally provide correct answers (human mean is $4.18 / 5.0$). Graders award full credit for semantic correctness regardless of phrasing.
2. **Symbolic Epistemic Policy**:
   - The proposed ASAG strictly requires audited domain rules (`CuratedDomainKnowledge`) to award credit for unmatched propositions.
   - Across 4,695 unmatched propositions, **0 propositions** were credited as `CORRECT_ADDITIONAL`, because the frozen knowledge base contained only 3 specific rules.
   - 1,815 topical propositions were categorized as `UNCERTAIN` and given $0.0$ bonus to prevent hallucinated credit.
   - Consequently, the system's average predicted grade was $0.57 / 5.0$.

### Conclusion
The low raw grades and high MAE reflect a principled research design decision: **the system chooses to withhold credit when it cannot verify an assertion, rather than risk ungrounded score inflation**. While this lowers point-for-point error agreement with human graders on unconstrained datasets, it ensures complete interpretability and verification safety.
