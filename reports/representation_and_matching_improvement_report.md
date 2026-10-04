# Base ASAG Representation and Matching Improvement Report

## 1. Executive Summary

During the post-benchmark error audit of the frozen Mohler dataset evaluation (2,273 records), rigid subject-predicate-object ($S$-$P$-$O$) relational representation was diagnosed as a primary source of alignment failure on high-scoring student answers (e.g. Question 1.1 Student 1: Human Grade 5.0, Proposed Grade 0.0).

In classical dependency-based ASAG, answers containing nominalized verbal predicates (e.g., *"simulate the behaviour of portions..."*) vs direct verb constructions (*"simulates portions..."*), prepositional argument shifts, and argument modifiers caused strict slot-by-slot matching to fail ($0.20$ slot similarity), rejecting genuine semantic paraphrases.

This phase implemented a general, interpretable, dependency-grounded representation improvement:
1. **Extended Relational Representation:** Enriched `DependencyRelation` with non-collapsing syntactic slots: `indirect_object`, `prepositional_arguments` (nested chains up to depth 3), `predicate_modifiers` (adverbials), `subject_modifiers` (compounds/amods), and `object_modifiers`.
2. **Root Non-Finite Gating Fix:** Resolved an extraction shadowing bug in `RobustPropositionExtractor` where non-finite root predicates were dropped when embedded subordinate clauses possessed explicit subjects.
3. **Cross-Slot Argument Matching with Syntactic Displacement Penalty:** In `TripleMatcher` and `ConfigurableTripleMatcher`, direct objects are flexibly aligned against prepositional arguments and modifier heads with a deterministic $0.90$ syntactic displacement factor, gated strictly by predicate alignment ($S_{\text{pred}} \ge 0.50$).
4. **Controlled Test Suite:** Implemented `tests/test_extended_representation.py` covering all 10 required controlled evaluation cases.
5. **Non-Regression:** All **442 / 442 unit and integration tests pass with zero regressions** (30.11s), while frozen benchmark files remain 100% untouched.

---

## 2. Problem Re-statement & Representative Audit Failure (Q1.1 S1)

### The Case
- **Question:** *"What is the role of a prototype program in problem solving?"*
- **Reference Answer:** *"To simulate the behaviour of portions of the desired software product."*
- **Student S1:** *"A prototype program simulates portions of the desired final product so that you can see how the program does the job before building the entire product."*
- **Human Grade:** 5.0 / 5.0
- **Frozen Benchmark Prediction:** 0.0 / 5.0 (Error: 5.0)

### Root Cause Analysis
1. **Syntactic Nominalization Mismatch:**
   - In the reference answer, the predicate *simulate* takes direct object *behaviour* (lemma `behaviour`), while the core patient *portions* is embedded as a prepositional complement (*"of portions"*).
   - In the student answer, the student uses the active verb *simulates* taking direct object *portions* (lemma `portion`).
2. **Strict Slot Rejection:**
   - The strict matcher evaluated `ref.object` (`behaviour`) directly against `stu.object` (`portions`).
   - Lexical-semantic similarity was $0.20$.
   - The composite triple score was $0.644$, below the $0.70$ threshold, causing the triple to be rejected as UNMATCHED ($0.0$).
3. **Loss of Provenance:**
   - Prepositional phrases (*"of portions"*, *"of product"*) and modifiers (*"desired"*, *"final"*) were completely stripped from `DependencyRelation` during extraction and bridging.

---

## 3. Classical ASAG Representation Deficiencies Identified

The post-benchmark audit identified three core deficiencies in standard dependency ASAG:

| Deficiency | Mechanism in Classical ASAG | Consequence |
|---|---|---|
| **Rigid Slot Boundary** | `object` is strictly compared to `object` | Nominalized verbal constructions (*"simulate behaviour of X"*) fail to match direct verbal constructions (*"simulate X"*). |
| **Relational Information Loss** | Stripping all prepositional attachments and compound modifiers from `DependencyRelation` | Auxiliary arguments (*"into machine code"*, *"by reference"*, *"from source files"*) disappear from relational evaluation. |
| **Root Verb Extraction Shadowing** | Fallback extractor was gated behind `len(canonical_relations) == 0` | If an embedded relative clause had an explicit subject, the sentence root verb (infinitive/imperative) was dropped entirely. |

---

## 4. Proposed General Representation Extension

To solve these deficiencies without sacrificing interpretability or introducing opaque neural models:

### 1. Extended `DependencyRelation` Data Model
```python
@dataclass(frozen=True)
class DependencyRelation:
    subject: str
    predicate: str
    object: Optional[str]
    subject_lemma: str
    predicate_lemma: str
    object_lemma: Optional[str]
    relation_type: str
    source_dependency_relations: Tuple[str, ...]
    subject_index: int
    predicate_index: int
    object_index: Optional[int] = None
    # Extended syntactic arguments (100% backward-compatible defaults)
    indirect_object: Optional[str] = None
    indirect_object_lemma: Optional[str] = None
    prepositional_arguments: Tuple[Tuple[str, str], ...] = ()
    predicate_modifiers: Tuple[str, ...] = ()
    subject_modifiers: Tuple[str, ...] = ()
    object_modifiers: Tuple[str, ...] = ()
```

### 2. Dependency Hierarchy Preservation
Instead of unsafe collapsing (e.g. turning *"in a table"* into a direct object), prepositional arguments are preserved as structured `(prep_lemma, pobj_lemma)` tuples, with nested chains traced up to depth 3 (e.g. `(('of', 'portion'), ('of', 'product'))`).

---

## 5. Algorithmic Specification: Representation & Matching

### Phase A: Syntactic Argument Extraction
1. **Prepositional Collection:** `_collect_prep_arguments(parsed_sentence, head_tok, visited, depth)` traverses directed dependency arcs for `prep` and `agent` relations, capturing the governing preposition and dependent nominal object `(prep, pobj)`.
2. **Modifier Collection:** `_collect_modifiers` captures `compound`, `amod`, and `nmod` dependents of the subject and object heads.
3. **Adverbial Collection:** `_collect_predicate_modifiers` captures `advmod` and `npadvmod` dependents of the verb.

### Phase B: Cross-Slot Argument Matching (`TripleMatcher.compare_slots`)
When `enable_cross_slot=True` is active:
1. **Predicate Gating Safeguard:**
   Cross-slot argument matching is **strictly gated** by predicate semantic alignment:
   $$\text{Predicate Gate:} \quad S_{\text{pred}} \ge 0.50$$
   If the verbal predicates do not share compatible semantics, no cross-slot argument displacement is permitted.
2. **Non-Finite Subject Alignment:**
   When the reference answer is an infinitive fragment without grammatical agent (placeholder `"it"`, `"to"`, etc.) and the predicate aligns, an explicit student subject is admitted ($S_{\text{subj}} = 1.0$).
3. **Subject Modifier Refinement:**
   If $S_{\text{subj}} < 0.70$, modifiers attached to the subject (e.g. *"primary key"* vs *"key attribute"*) are compared with a $0.90$ modifier displacement factor.
4. **Direct Object vs Prepositional Argument Alignment:**
   - **Check 1 (Student Direct Object $\leftrightarrow$ Reference Preposition):**
     $$\forall (p_{\text{ref}}, o_{\text{ref}}) \in \text{ref.prep\_args}: \quad S_{\text{cand}} = 0.90 \times \text{Sim}(o_{\text{ref}}, \text{stu.object})$$
   - **Check 2 (Reference Direct Object $\leftrightarrow$ Student Preposition):**
     $$\forall (p_{\text{stu}}, o_{\text{stu}}) \in \text{stu.prep\_args}: \quad S_{\text{cand}} = 0.90 \times \text{Sim}(\text{ref.object}, o_{\text{stu}})$$
   - **Check 3 (Object Modifiers):**
     Compound/adjectival modifiers of the object are evaluated against the head noun with a $0.90$ factor.
5. **Effective Slot Score:**
   $$S_{\text{obj\_eff}} = \max(S_{\text{direct}}, S_{\text{cross\_cand}})$$
   Direct object matching always takes precedence when direct similarity is high. Cross-slot alignment is only utilized when direct matching fails due to syntactic displacement.

---

## 6. Implementation Details

| Component | File | Changes Made |
|---|---|---|
| **Data Model & Extraction** | `base_asag/dependency/triples.py` | Added 6 extended attributes to `DependencyRelation`, updated `to_dict()`, added `_collect_prep_arguments`, `_collect_modifiers`, `_collect_predicate_modifiers`, and updated `_extract_canonical_relations`. |
| **Hybrid Representation** | `base_asag/representation/hybrid.py` | Fixed root non-finite gating in `extract_sentence`; updated `_canonical_to_robust` and `_extract_infinitive_arguments` to populate extended arguments. |
| **Slot Matching** | `base_asag/matching/triple_matcher.py` | Added `enable_cross_slot: bool = False` to `TripleMatcher`; implemented predicate-gated cross-slot matching in `compare_slots`. |
| **Global Matching** | `base_asag/matching/global_matcher.py` | Added `enable_cross_slot: bool = False` to `ConfigurableTripleMatcher`, passing configuration to internal matcher. |
| **Pipeline Bridge** | `proposed_asag/overhauled_pipeline.py` | Updated `robust_prop_to_relation` to propagate extended arguments; configured `enable_cross_slot=True` in `OverhauledASAGPipeline`; passed parsed document context to `evaluate_matching_result`. |
| **Controlled Test Suite** | `tests/test_extended_representation.py` | Created 12 comprehensive unit and integration tests covering the 10 controlled cases. |

---

## 7. Controlled Test Suite Results (10 Required Cases)

All 10 controlled cases specified in the phase definition were implemented and validated:

| # | Case Description | Question / Reference | Student Input | Result | Status |
|---|---|---|---|---|---|
| **1** | **Exact match** | What is a primary key? / Identifies record | Identifies record | Scaled: 5.00 / 5.0 (ENTAILS, 1.00) | PASSED |
| **2** | **Simple paraphrase** | What does compiler do? / Translates source into machine language | Converts source into machine code | Scaled: 4.67 / 5.0 (ENTAILS, 0.93) | PASSED |
| **3** | **Passive vs active** | What generates machine code? / Compiler generates machine code | Machine code is generated by compiler | Scaled: 4.92 / 5.0 (ENTAILS, 0.98) | PASSED |
| **4** | **Prepositional argument variation (Q1.1 S1)** | Role of prototype program? / To simulate behaviour of portions of desired product | Prototype simulates portions of desired final product... | Scaled: 4.68 / 5.0 (ENTAILS, 0.94) | PASSED |
| **5** | **Modifier variation** | Function return? / Boolean value | Boolean result | Scaled: 1.79 / 5.0 (UNCERTAIN, 0.71) | PASSED |
| **6** | **Conjoined information** | OS startup? / System allocates memory | Allocates memory and initializes drivers | Scaled: 5.00 / 5.0, 1 unmatched stu | PASSED |
| **7** | **Word order / adverbs** | Quicksort? / Quickly partitions array | Partitions array quickly | Scaled: 5.00 / 5.0 (ENTAILS, 1.00) | PASSED |
| **8** | **Additional student prop** | Primary key purpose? / Uniquely identifies record | Uniquely identifies record and cannot contain NULL | Scaled: 5.00 / 5.0, 1 unmatched stu | PASSED |
| **9** | **Genuine semantic mismatch** | What is a stack? / Operates on LIFO basis | A compiler translates source code | Scaled: 0.00 / 5.0 (No match) | PASSED |
| **10** | **Genuine contradiction** | Constraint on primary key? / Cannot contain NULL | Can contain NULL | Scaled: 0.00 / 5.0 (CONTRADICTS, 1.00) | PASSED |

---

## 8. Q1.1 S1 Before vs After Diagnostic Trace

### Before Improvement (Frozen Benchmark)
```json
{
  "question": "What is the role of a prototype program in problem solving?",
  "reference_answer": "To simulate the behaviour of portions of the desired software product.",
  "student_answer": "A prototype program simulates portions of the desired final product so that you can see how the program does the job before building the entire product.",
  "ref_relation": {"subject": "it", "predicate": "simulate", "object": "behaviour"},
  "stu_relation": {"subject": "program", "predicate": "simulates", "object": "portions"},
  "direct_object_similarity": 0.20,
  "triple_score": 0.644,
  "match_status": "UNMATCHED",
  "base_score_normalized": 0.0,
  "final_score_scaled": 0.0
}
```

### After Improvement (Development Branch)
```json
{
  "question": "What is the role of a prototype program in problem solving?",
  "reference_answer": "To simulate the behaviour of portions of the desired software product.",
  "student_answer": "A prototype program simulates portions of the desired final product so that you can see how the program does the job before building the entire product.",
  "ref_relation": {
    "subject": "it",
    "predicate": "simulate",
    "object": "behaviour",
    "prepositional_arguments": [["of", "portion"], ["of", "product"]],
    "object_modifiers": ["desired", "software"]
  },
  "stu_relation": {
    "subject": "program",
    "predicate": "simulates",
    "object": "portions",
    "prepositional_arguments": [["of", "product"]],
    "subject_modifiers": ["prototype"]
  },
  "predicate_similarity": 1.0,
  "subject_similarity": 1.0,
  "cross_slot_match": "stu.object('portions') <-> ref.prep('of portion') via exact_lemma",
  "effective_object_similarity": 0.90,
  "triple_score": 0.935,
  "entailment_status": "ENTAILS",
  "base_score_normalized": 0.935,
  "final_score_scaled": 4.68,
  "human_grade": 5.0,
  "absolute_error": 0.32
}
```
**Impact:** On this specific benchmark failure case, predicted grade improved from $0.00$ to $4.68$ (error reduced from $5.00$ to $0.32$).

---

## 9. Non-Regression Verification

The full pytest test suite was executed across all test files:
- **Baseline Test Count:** 430 passed
- **New Tests Added:** 12 passed (`tests/test_extended_representation.py`)
- **Total Test Count:** **442 passed in 30.11s**
- **Failures:** 0
- **Errors:** 0
- **Regressions:** 0

All existing tests covering:
- Stage 1–2 Baseline
- Stage 3 Preprocessing
- Stage 4 Dependency Parsing
- Stage 5 Dependency Triples
- Stage 6 Semantic Relations
- Stage 7 Triple Matching
- Stage 8 Entailment Analysis
- Stage 9 Base Scoring
- Stage 10 Integration Pipeline
- Stage 11–14 Proposition Layer
- Stage 15 Evaluation Harness
- Bug 1 Antonym Contradiction Repair
- Bug 2 BST Grounding Repair
continue to pass 100%.

---

## 10. Strict Adherence to Research Constraints & Boundaries

1. **Frozen Benchmark Integrity:**
   `evaluation/results/current_mohler_results.csv`, `current_mohler_summary.json`, and `current_mohler_propositions.json` remain untouched (timestamps Oct 3 21:41).
2. **Scoring Parameters Untouched:**
   $M_{\text{pos}} = 0.30$, $M_{\text{neg}} = 0.40$, $r = 0.50$, and saturation scoring were not altered.
3. **Domain Knowledge Untouched:**
   No new domain rules were added; the 3 proof-of-concept rules remain frozen.
4. **Classical NLP Discipline:**
   No neural embeddings, LLMs, or external APIs were introduced. All improvements are deterministic, dependency-grounded, and auditable.
5. **Full Backward Compatibility:**
   Default configuration of `TripleMatcher` preserves classical strict S-P-O matching.

---

## 11. Known Limitations

1. **Syntactic Attachment Ambiguity:**
   In complex nested prepositional phrases (e.g. preposition attaching to verb vs object noun), statistical parsers may vary in attachment decisions. Our depth-3 prepositional chain traversal mitigates this, but cannot fully resolve parser ambiguity.
2. **Syntactic Displacement Factor Tuning:**
   The $0.90$ displacement discount is currently fixed by heuristic rather than learned. While empirically sound and conservative, it is a design parameter.
3. **Discontinuous Clausal Arguments:**
   Non-contiguous clausal expressions (e.g. split infinitives or parenthetical insertions) remain subject to token span boundaries.

---

## 12. Next Steps

1. Review and accept the Base ASAG Representation and Matching Improvement report.
2. Maintain all research freezes on scoring parameters and domain rules.
3. Proceed to authorized comparative evaluation when instructed.
