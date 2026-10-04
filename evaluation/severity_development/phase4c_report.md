# Phase 4C: Interpretable Contradiction Severity Analysis Report

**Status:** Completed Development Study (FROZEN)  
**Date:** 2026-10-04  
**Author:** NLP / ASAG Research Project  
**Repository State:** 506 tests passing, 0 failures, 0 regressions  

---

## 1. Objective

The objective of Phase 4C is to investigate whether contradiction severity can be estimated using interpretable linguistic and structural evidence already available in the ASAG pipeline, without an LLM.

Phase 4B demonstrated that treating every `INCORRECT` proposition identically is inadequate. Differentiating peripheral misconceptions (e.g., naming conventions) from fundamental conceptual contradictions (e.g., permitting duplicate primary keys) allowed Model D to achieve superior qualitative behavior. However, severity labels in Phase 4B were manual experimental annotations. Phase 4C systematically assesses whether deterministic pipeline features can automatically categorize verified contradictions into `MINOR`, `MODERATE`, and `CORE_CONTRADICTION`, while isolating non-contradictions and entity-confusion near-misses.

---

## 2. Research Motivation

In automated short answer grading, not all incorrect student statements carry equal pedagogical weight:
1. **Peripheral Misconceptions (MINOR):** A student writing *"A primary key is always named ID in database schemas"* demonstrates an operational schema styling bias, but understands that a primary key exists to identify records.
2. **Operational/Behavioral Misconceptions (MODERATE):** A student stating *"A table can define multiple primary keys simultaneously"* understands key identification but misunderstands relational cardinality rules.
3. **Core Defining Invariant Inversions (CORE_CONTRADICTION):** A student stating *"A primary key can contain duplicate values"* directly inverts the foundational property being tested. Awarding $4.33/5.00$ to such an answer (as Model A does) represents a serious grading failure.

The unresolved research question is:
> *Can contradiction severity be estimated using interpretable evidence already available in the ASAG pipeline, without an LLM?*

---

## 3. Frozen Assumptions

Strict research integrity boundaries were enforced throughout Phase 4C:
1. **No Benchmark Execution:** The official UNT/Mohler CS Short Answer benchmark (2,273 active records) was **not** run or evaluated.
2. **Frozen Production Scorer:** Production scoring remains frozen at $M_{\text{pos}} = 0.30$, $M_{\text{neg}} = 0.40$, $r = 0.50$ via `BoundedScorer`. Model D was not integrated into production.
3. **Frozen Domain Knowledge:** The 3 curated domain rules (`PK_NOT_NULL`, `BST_INORDER_SORTED`, `COMPILER_INTERMEDIATE_REP`) remained completely frozen. No new domain rules, WordNet mappings, or factual assertions were added.
4. **Frozen Prior Experiments:** Experiment 1, Experiment 2, Experiment 3, Phase 4A, and Phase 4B artifacts remain untouched and preserved.
5. **No External APIs or LLMs:** All features and decision logic are deterministic, rule-grounded, and fully inspectable.

---

## 4. Contradiction vs Severity Distinction

A mandatory architectural separation is enforced:
$$\text{Linguistic Extraction} \longrightarrow \text{Contradiction Detection} \longrightarrow \text{Severity Estimation} \longrightarrow \text{Scoring}$$

- **Contradiction Detection** evaluates *epistemic conflict*: Does the proposition contradict reference assertions or domain knowledge?
- **Severity Estimation** evaluates *pedagogical significance*: Given an established contradiction, how severely does it undermine the core concept being assessed?

Under this design, non-contradictory statements (`CORRECT_ADDITIONAL`, `IRRELEVANT`, `UNCERTAIN`) receive a severity of `NONE` ($0.0$). A proposition with high question relevance or high lexical similarity can **never** be assigned severity unless contradiction detection has independently verified an epistemic clash.

---

## 5. Severity Definitions

The development categories are defined operationally:

| Severity Level | Nominal Score $\sigma$ | Operational Definition | Representative Controlled Example |
| :--- | :---: | :--- | :--- |
| **MINOR** | $0.25$ | An incorrect statement regarding peripheral conventions, naming, syntax style, or implementation trivia that does not invalidate the central concept. | *"A primary key is always named ID in database schemas."* |
| **MODERATE** | $0.60$ | An incorrect statement conflicting with operational behavior, cardinality, arity, or secondary attributes without inverting the defining invariant. | *"A binary search tree inorder traversal yields random order."* |
| **CORE_CONTRADICTION** | $1.00$ | A statement that directly contradicts or inverts the fundamental defining property of the target entity under evaluation. | *"A primary key can contain duplicate values."* / *"A binary search tree places larger values in the left subtree."* |
| **UNRESOLVED** | $0.00$ | Statements exhibiting entity confusion (predicated of an adjacent or confused entity) or lacking evidence to determine severity. | *"A foreign key can contain duplicate values."* (Entity mismatch). |
| **NONE** | $0.00$ | Statements that are not contradictory. | *"A primary key uniquely identifies each record."* |

---

## 6. Available Evidence Inventory

An audit of the ASAG pipeline revealed 10 extractable signals (documented in [phase4c_feature_inventory.md](file:///Users/sarang/Dev/College/MIT_WPU/Projects/AIES/proposition-level-asag/evaluation/severity_development/phase4c_feature_inventory.md)):
1. `core_proposition_link`: Relational slot alignment between the student triple and reference triples.
2. `defining_property_target`: Whether `conflicting_property` matches curated domain invariants (`uniqueness`, `nullability`, `relative_size`, `sort_order`, `translation`).
3. `contradiction_type`: Categorical form (`VALUE_CONFLICT`, `EXPLICIT_NEGATION`, `ANTONYM_CONFLICT`).
4. `contradiction_evidence_strength`: Confidence score of the contradiction rule ($\in [0.55, 0.90]$).
5. `entity_concept_grounding`: Verification that the subject matches the target entity rather than a confused entity.
6. `question_topical_centrality`: Lexical and synset overlap with question prompt tokens.
7. `reference_coverage_weight`: Reciprocal of total reference proposition count ($1 / |P_{\text{ref}}|$).
8. `argument_displacement_depth`: Core triple vs subordinate/prepositional attachment.
9. `domain_knowledge_invalidation`: Direct negation of curated domain rules.
10. `modality_and_hedging`: Linguistic certainty markers (`ASSERTED` vs `POSSIBLE` vs `UNCERTAIN`).

---

## 7. Candidate Severity Signals Analysis

- **Signal A (Core Proposition Link):** Strong indicator of core relevance, but alone insufficient: a student can mention the core subject/verb while only making a peripheral naming error.
- **Signal B (Defining Property Contradiction):** The most diagnostic signal for `CORE_CONTRADICTION`. If the conflict targets `uniqueness` (PK), `relative_size` (BST), or `translation` (Compiler), core invalidation is unambiguous.
- **Signal C (Contradiction Evidence Strength):** **Evidence strength does not equal severity.** A detector can be 100% confident about a minor naming error ($0.90$ strength). Using confidence alone as a proxy for severity is a critical design flaw (demonstrated in Ablation A).
- **Signal D (Question Relevance):** Measures topic focus, not truth or severity. A completely false statement can have high question relevance.
- **Signal E (Reference Role):** When a reference answer contains multiple propositions, contradicting the defining clause carries higher diagnostic significance than contradicting an auxiliary clause.
- **Signal F (Domain Evidence Source):** Property value conflicts and explicit predicate negations provide high-certainty structural anchors for severity.

---

## 8. Controlled Dataset

A dataset of **51 controlled development cases** was constructed across three domains:
- **Primary Key (17 cases):** 5 Core, 5 Moderate, 5 Minor, 2 Adversarial (Entity confusion & non-contradiction).
- **Binary Search Tree (17 cases):** 5 Core, 5 Moderate, 5 Minor, 2 Adversarial (General binary tree confusion & application statement).
- **Compiler (17 cases):** 5 Core, 5 Moderate, 5 Minor, 2 Adversarial (Interpreter confusion & tooling remark).

*Source Label:* `SYNTHETIC_DEVELOPMENT`. These cases represent systematic unit benchmarks for development, not human experimental data.

---

## 9. Severity Estimator Architecture

The `InterpretableSeverityEstimator` operates via a deterministic 4-stage pipeline:
```
1. Epistemic Contradiction Gate: If not is_contradicted -> Severity = NONE (0.0)
   ↓
2. Entity Concept Grounding: Check subject against target vs confused entity sets
   ↓
3. Core Invariant & Defining Property Match: Check conflicting_property & core predicate negation
   ↓
4. Peripheral & Behavioral Cue Filtering: Check naming/extension cues vs relational cues
   ↓
Decision & Structured Provenance
```

---

## 10. Decision Logic

1. **Gate 1:** If `contradiction_evidence is None` or `is_contradicted == False` $\implies$ return `NONE` ($\sigma = 0.0$).
2. **Gate 2 (Entity Confusion):** If proposition discusses a confused adjacent entity (e.g. *foreign key*, *general binary tree*, *interpreter*) $\implies$ return `UNRESOLVED` ($\sigma = 0.0$).
3. **Rule 1 (Core Contradiction):** If `entity_grounded == True` AND (`defining_property_target == True` OR direct negation of core reference predicate) $\implies$ return `CORE_CONTRADICTION` ($\sigma = 1.00$).
4. **Rule 2 (Minor Error):** If proposition targets peripheral cues (naming, extensions, formatting, dates, syntax styles, storage/pointer trivia) $\implies$ return `MINOR` ($\sigma = 0.25$).
5. **Rule 3 (Moderate Error):** If proposition targets operational attributes (traversal order, arity, complexity, secondary constraints) or contextual antonyms $\implies$ return `MODERATE` ($\sigma = 0.60$).
6. **Fallback:** If high-confidence core link exists $\implies$ `CORE_CONTRADICTION`; otherwise `MODERATE`.

---

## 11. Controlled Results

The estimator achieved **100% accuracy (51 / 51 cases correct)** across the controlled development dataset:

- **CORE_CONTRADICTION:** 15 / 15 correctly identified.
- **MODERATE:** 15 / 15 correctly identified.
- **MINOR:** 15 / 15 correctly identified.
- **UNRESOLVED:** 3 / 3 correctly identified.
- **NONE:** 3 / 3 correctly identified.

All predictions, true labels, and itemized rationales are exported in [phase4c_severity_results.csv](file:///Users/sarang/Dev/College/MIT_WPU/Projects/AIES/proposition-level-asag/evaluation/severity_development/phase4c_severity_results.csv).

---

## 12. Confusion Matrix

The confusion matrix on the 51 development cases (Rows = True Development Label, Columns = Predicted Label):

| Category | Predicted CORE | Predicted MODERATE | Predicted MINOR | Predicted UNRESOLVED | Predicted NONE | Total |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **CORE_CONTRADICTION** | **15** | 0 | 0 | 0 | 0 | 15 |
| **MODERATE** | 0 | **15** | 0 | 0 | 0 | 15 |
| **MINOR** | 0 | 0 | **15** | 0 | 0 | 15 |
| **UNRESOLVED** | 0 | 0 | 0 | **3** | 0 | 3 |
| **NONE** | 0 | 0 | 0 | 0 | **3** | 3 |
| **Total** | 15 | 15 | 15 | 3 | 3 | 51 |

---

## 13. Macro Precision, Recall, and F1

| Class | Precision | Recall | F1 Score | Support |
| :--- | :---: | :---: | :---: | :---: |
| **CORE_CONTRADICTION** | 1.0000 | 1.0000 | **1.0000** | 15 |
| **MODERATE** | 1.0000 | 1.0000 | **1.0000** | 15 |
| **MINOR** | 1.0000 | 1.0000 | **1.0000** | 15 |
| **UNRESOLVED** | 1.0000 | 1.0000 | **1.0000** | 3 |
| **NONE** | 1.0000 | 1.0000 | **1.0000** | 3 |
| **Macro Average** | **1.0000** | **1.0000** | **1.0000** | 51 |

*Note:* This perfect metric reflects satisfaction of predefined controlled development criteria on synthetic cases. It does not imply 100% performance on noisy human responses.

---

## 14. Ablation Study

To evaluate which evidence sources actually contribute to severity estimation, five variants were evaluated:

| Variant | Formulation | Accuracy | Macro F1 | Core F1 | Key Failure Mode |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **Variant A** | Evidence Strength Only | 0.8431 | 0.7132 | 0.9091 | Conflates high detection confidence with severity; cannot distinguish minor from moderate. |
| **Variant B** | Contradiction + Core Link | 0.8431 | 0.7142 | 0.9375 | Over-escalates minor errors that share subject tokens with reference. |
| **Variant C** | Contradiction + Defining Property | 0.8039 | 0.6899 | 0.8387 | Successfully separates core, but fails to distinguish minor from moderate errors. |
| **Variant D** | Contradiction + Reference Role | 0.3922 | 0.3434 | 0.5263 | Severe over-penalization; labels all linked contradictions as core. |
| **Variant E** | **Full Proposed Estimator** | **1.0000** | **1.0000** | **1.0000** | Balances entity grounding, defining invariants, and peripheral cue filtering. |

**Ablation Finding:** Evidence strength alone (Variant A) or reference role alone (Variant D) produces severe distortion. Only the combination of **entity grounding + defining property targeting + peripheral cue filtering** yields balanced severity estimation.

---

## 15. Adversarial Cases

The testbed included adversarial near-miss cases designed to expose failure modes:
1. **PK-ADV-02 (*"A primary key is usually placed early in a table schema"*):** Hedged stylistic statement. Evaluated as non-contradictory $\implies$ received `NONE` ($\sigma = 0.0$).
2. **BST-ADV-02 (*"A binary search tree is often used in computer memory systems"*):** Vague true application fact. Evaluated as non-contradictory $\implies$ received `NONE` ($\sigma = 0.0$).
3. **CMP-ADV-02 (*"A compiler is usually written in C++ or Rust"*):** Tooling convention fact. Evaluated as non-contradictory $\implies$ received `NONE` ($\sigma = 0.0$).

In all adversarial non-contradictions, the epistemic gate successfully prevented spurious severity assignment.

---

## 16. Entity-Specificity Analysis

A known defect in ASAG systems is entity overgeneralization. Phase 4C explicitly tested entity confusion:
1. **PK-ADV-01 (*"A foreign key can contain duplicate values"*):** True of foreign keys. The estimator detected that the proposition discusses `foreign key` rather than `primary key` $\implies$ returned `UNRESOLVED` ($\sigma = 0.0$).
2. **BST-ADV-01 (*"A general binary tree must store smaller values in the left subtree"*):** General binary trees do not enforce BST ordering. The estimator detected entity mismatch on `binary tree` $\implies$ returned `UNRESOLVED`.
3. **CMP-ADV-01 (*"An interpreter compiles source code into machine files"*):** The claim is predicated of `interpreter`. The estimator detected entity confusion $\implies$ returned `UNRESOLVED`.

**Finding:** The entity grounding gate successfully prevented entity-confused statements from being penalized as core contradictions of the target entity.

---

## 17. Failure Modes & Edge Cases

While the estimator performed cleanly on the controlled dataset, two potential failure modes were identified during development:
1. **Shared Subject Token False Linking:** In an earlier iteration, any explicit negation sharing the subject lemma (e.g., *"A primary key cannot consist of composite columns"*) was misclassified as a core negation because "primary key" matched the reference subject. This was resolved by requiring the *predicate* of the student proposition to match the *predicate* of the reference proposition.
2. **Multi-Word Peripheral Phrases:** Peripheral cues containing multiple words (e.g., *"first column"*, *"root directory"*) failed token-set matching when split into individual tokens. Phrase-level substring matching in the raw proposition text resolved this.

---

## 18. Interpretability Analysis

Every decision produced by `InterpretableSeverityEstimator` contains structured evidence:
```json
{
  "severity": "CORE_CONTRADICTION",
  "severity_score": 1.0,
  "evidence": {
    "is_contradicted": true,
    "contradiction_type": "VALUE_CONFLICT",
    "evidence_strength": 0.9,
    "entity_grounded": true,
    "entity_name": "primary key",
    "core_link": false,
    "defining_property_target": true,
    "conflicting_property": "uniqueness",
    "is_peripheral": false,
    "is_relational_confusion": false,
    "question_centrality": 0.4286,
    "reference_coverage_weight": 1.0,
    "rationale_reasons": [
      "Entity successfully grounded to target 'PRIMARY_KEY'.",
      "Contradiction targets defining domain property: 'uniqueness'."
    ]
  },
  "explanation": "CORE_CONTRADICTION: Directly contradicts core defining property 'uniqueness' of target entity 'PRIMARY_KEY'."
}
```
Students and instructors receive explicit rationales explaining why a statement was penalized as a core contradiction rather than an incidental mistake.

---

## 19. Circularity & Design-Bias Analysis

To avoid research circularity:
1. **No Grade Dependency:** The severity estimator has zero access to student scores, base scores, or Model D outputs. Severity is strictly an upstream feature input to grading.
2. **Design Bias Acknowledgment:** The 51 controlled cases and the estimator rules were authored within the same research project. High performance on this controlled benchmark demonstrates *internal logical coherence of the rules*, but does not prove generalization to uncurated student answers.

---

## 20. Limitations

1. **Curated Property Lexicon:** Defining property detection currently relies on `DEFINING_PROPERTIES` and `INCOMPATIBLE_VALUE_SETS`. Concepts outside the three investigated domains require corresponding property definitions.
2. **Lexical Cue Dependency:** Minor error detection utilizes peripheral cues (`name`, `extension`, `year`, `bytes`, etc.). While effective for common student misconceptions, novel phrasing might bypass peripheral filtering into moderate severity.
3. **Pronominal Coreference:** If a student writes *"It can contain duplicate values"*, coreference must resolve *"It"* to the target entity. In isolated propositions without document context, entity grounding requires upstream coreference resolution.

---

## 21. Stability Assessment for Development Use

The experimental severity estimator successfully separated the controlled development categories under the tested cases. The estimator is deterministic, fast (<1ms per proposition), and free of runtime dependencies on external services. It is sufficiently stable for development use in controlled experimental studies.

---

## 22. Suitability as Input to Model D

Phase 4B established that Model D requires a binary or tiered severity input ($\sigma \ge 0.90 \implies$ core invalidation; $\sigma < 0.90 \implies$ minor/moderate deduction). The estimator provides exactly this signal:
- `CORE_CONTRADICTION` maps to $\sigma = 1.00$ (triggering Model D's 50% core discount).
- `MODERATE` maps to $\sigma = 0.60$ (triggering a 0.60-point bounded deduction).
- `MINOR` maps to $\sigma = 0.25$ (triggering a 0.25-point bounded deduction).
- `UNRESOLVED` / `NONE` maps to $\sigma = 0.00$ (0.0 deduction).

The results provide development evidence supporting the feasibility of feeding automated severity estimates into Model D.

---

## 23. What Remains Unvalidated

1. **Open-Domain Generalization:** Performance on open-ended student responses from uncurated questions outside Primary Key, BST, and Compiler has not been validated.
2. **Human Severity Agreement:** The severity levels are development categories; agreement between this automated estimator and human instructor severity ratings has not yet been experimentally evaluated.
3. **Benchmark Score Impact:** The effect of replacing manual severity annotations with this automated estimator on the full Mohler benchmark has not been evaluated.

---

## 24. Explicit Statement: Production Scorer Untouched

**Production scoring parameters and code remain strictly unchanged.**  
`BoundedScorer` continues to run with $M_{\text{pos}} = 0.30$, $M_{\text{neg}} = 0.40$, and $r = 0.50$. Neither Model D nor the severity estimator has been integrated into the production evaluation pipeline.

---

## 25. Explicit Statement: No Mohler Benchmark Used

**No Mohler benchmark evaluation was performed in Phase 4C.**  
Zero records of the 2,273 active Mohler dataset were processed or evaluated. All metrics reported represent performance on the 51 synthetic development control cases.

---

## 26. Explicit Statement: Frozen Experiments Untouched

Experiment 1 (Baseline), Experiment 2 (Proposed ASAG Development), Experiment 3 (Precision Improvement), Phase 4A (Scoring Study), and Phase 4B (Scoring Development & Stress Testing) artifacts remain untouched and preserved in their respective frozen directories.
