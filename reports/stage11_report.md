# Stage 11 Report: Proposition Alignment Extractor

**Implementation Date:** Stage 11 of the ASAG Research Pipeline  
**Repository:** proposition-level-asag  
**Research Stage:** STAGE 11 — Identify Matched vs Unmatched Student Information

---

## 1. Objective

Stage 11 implements the first step of the proposed ASAG extension.
Its purpose is to extract full, interpretable provenance for every student proposition —
both those successfully aligned to the reference answer and those that were not.

This creates the data foundation for Stage 13, which will classify unmatched student
information as CORRECT_ADDITIONAL, IRRELEVANT, or INCORRECT_ADDITIONAL.

> **IMPLEMENTATION DECISION**: Stage 11 consumes the existing BaseASAGPipelineResult
> from Stage 10 without re-running any NLP pipeline component.

---

## 2. Stage 11 Scope

### What Stage 11 DOES:

- Reads the `BaseASAGPipelineResult` from Stage 10.
- Builds a flat index of all student canonical relations in sentence order.
- Associates each student relation with its global index (matching Stage 7 indexing).
- For matched relations: extracts full diagnostic evidence (Stage 7 match scores,
  Stage 8 entailment status, Stage 9 score contribution, character span).
- For unmatched relations: records the best rejected candidate and rejection reason.
- Computes character-level spans for all propositions in the original student answer.
- Organizes all evidence into `PropositionAlignmentResult`.

### What Stage 11 does NOT do:

- Does NOT re-run Stage 3–9 components.
- Does NOT modify or recalculate the Base ASAG score.
- Does NOT classify unmatched student information.
- Does NOT add bonus or penalty for additional information.
- Does NOT implement CORRECT_ADDITIONAL, IRRELEVANT, or INCORRECT_ADDITIONAL.

> **RESEARCH BOUNDARY**: The `classification` field for all unmatched propositions
> is always `"NOT_EVALUATED_BY_BASE_ASAG"` in Stage 11.

---

## 3. Relationship to Base ASAG

Stage 11 is the **first module of the proposed extension** (System 3).
It sits immediately after Stage 10 (the complete Base ASAG pipeline) and reads
the already-computed result.

```
Stage 10: BaseASAGPipeline.grade()
              ↓
              BaseASAGPipelineResult
              ↓
Stage 11: PropositionAlignmentExtractor.extract()
              ↓
              PropositionAlignmentResult
              ↓
Stage 13: (future) Additional-Information Classifier
```

The Base ASAG score is **preserved exactly** in `PropositionAlignmentResult.base_asag_normalized_score`.

---

## 4. Proposition Alignment Design

The extractor builds a **flat index** of all student canonical relations:

```python
all_student_relations = []
for sent_triples in student_triples.sentences:
    all_student_relations.extend(sent_triples.canonical_relations)
```

This flat index is the same ordering used by Stage 7 (`student_index` in
`MatchedRelation` and `CandidateAlignment`). This allows Stage 11 to directly
look up which student relations were matched (by index) without any ambiguity.

A parallel `student_rel_to_sent_index` dictionary maps each flat student relation
index → its sentence index, which is needed for span computation.

---

## 5. Matched Proposition Representation

Each `MatchedPropositionEvidence` contains:

| Field | Source | Description |
|---|---|---|
| `student_proposition_index` | Stage 7 `student_index` | Flat index into student relations |
| `reference_proposition_index` | Stage 7 `reference_index` | Flat index into reference relations |
| `student_relation` | Stage 5 `DependencyRelation.to_dict()` | Student matched relation |
| `reference_relation` | Stage 5 `DependencyRelation.to_dict()` | Reference matched relation |
| `span` | Stage 11 `_compute_span()` | Character span in original answer |
| `subject_similarity` | Stage 7 | Slot-level similarity |
| `predicate_similarity` | Stage 7 | Slot-level similarity |
| `object_similarity` | Stage 7 | Slot-level similarity (None if intransitive) |
| `triple_score` | Stage 7 | Weighted composite score |
| `match_method` | Stage 7 | e.g. `exact_triple`, `lemma_triple` |
| `alignment_threshold` | Stage 7 config | Threshold used |
| `entailment_status` | Stage 8 `EntailmentResult.relation` | ENTAILS/CONTRADICTS/UNCERTAIN |
| `entailment_confidence` | Stage 8 | Confidence in [0,1] |
| `score_contribution` | Stage 9 | 1.0 (ENTAILS), 0.5 (UNCERTAIN), 0.0 otherwise |
| `slot_evidence` | Stage 6 via Stage 7 | Semantic evidence per slot |
| `diagnostic_reasons` | Stage 8 | Human-readable explanation |
| `polarity_reference` | Stage 8 | POSITIVE or NEGATED |
| `polarity_student` | Stage 8 | POSITIVE or NEGATED |

---

## 6. Unmatched Student Proposition Representation

Each `UnmatchedStudentPropositionEvidence` contains:

| Field | Value | Description |
|---|---|---|
| `student_proposition_index` | Computed | Flat index in all student relations |
| `student_relation` | `DependencyRelation.to_dict()` | The unmatched relation |
| `span` | Stage 11 | Character span in original answer |
| `match_status` | `"UNMATCHED"` | Always |
| `classification` | `"NOT_EVALUATED_BY_BASE_ASAG"` | Always in Stage 11 |
| `score_effect` | `0.0` | Always — no bonus or penalty |
| `best_candidate_reference_index` | From candidate alignments | Index of closest rejected ref |
| `best_candidate_score` | From candidate alignments | Score of closest rejected ref |
| `best_candidate_relation` | From candidate alignments | The rejected reference relation |
| `rejection_reason` | Computed | Why the match was rejected |

> **RESEARCH INTEGRITY**: `score_effect = 0.0` for all unmatched propositions is a
> Stage 11 invariant. No scoring bonus or penalty is applied. This preserves the
> Base ASAG score exactly.

---

## 7. Provenance / Span Design

### Problem

1. `ParsedToken.char_offset` is the character offset within the **normalized sentence text**, not within the original multi-sentence student answer.
2. In coordinated verb phrases (e.g. *"A primary key uniquely identifies each record in a table and cannot contain NULL values"*), the second conjunct (`cannot contain NULL values`) inherits the subject (`key`) from the first conjunct. A naive span taking `min(subject, predicate, object)` would stretch the second proposition's span across the conjunction back to the first clause's subject, causing severe overlap.

### Solution (OUR IMPLEMENTATION DECISION)

```python
# 1. Locate sentence in full original student answer
sent_start_in_answer = student_answer_original.find(sent_original)
if sent_start_in_answer == -1:
    # Fallback: whitespace-resilient regex search if normalization collapsed spaces
    pattern = r"\s+".join(re.escape(w) for w in sent_original.split())
    match = re.search(pattern, student_answer_original)
    if match:
        sent_start_in_answer = match.start()

# 2. Conjoined clause isolation:
# If subject was inherited from an earlier clause (tokens[pred].dep == "conj"
# and tokens[subj].head_index != pred_idx), do NOT include the earlier clause's
# subject in the conjoined clause's span.
# Instead, include the predicate, its auxiliaries/negations (can, not),
# and the object and its modifiers (NULL, values).
```

This yields:
- Proposition 1 (matched): `[2:45]` → `"primary key uniquely identifies each record"`
- Proposition 2 (unmatched): `[61:87]` → `"cannot contain NULL values"`
- Non-overlapping, clean spans directly usable by an explainable interface.

---

## 8. Serialization Design

All data structures implement `.to_dict()` returning a fully JSON-serializable
Python dictionary. No spaCy objects, DependencyRelation objects, MatchedRelation
objects, or EntailmentResult objects appear in the public result.

`PropositionAlignmentResult.to_json(indent=2)` produces a complete JSON string
suitable for logging, notebook display, or research reporting.

---

## 9. Notebook Note

The interactive notebook at `notebooks/asag_interactive_demo.ipynb` could be updated
to add a new cell demonstrating Stage 11:

```python
from proposed_asag.proposition.alignment import PropositionAlignmentExtractor

extractor = PropositionAlignmentExtractor()
alignment = extractor.extract(result)

print(f"Matched: {alignment.matched_count}, Unmatched: {alignment.unmatched_student_count}")
print(alignment.to_json())
```

> **NOTE**: The `.ipynb` notebook update was skipped in this stage to avoid
> complex notebook file editing. The notebook can be updated interactively.

---

## 10. Test Cases

The 21 tests in `tests/test_stage11_alignment.py`:

| # | Test | Description |
|---|---|---|
| 1 | `test_exact_match_compiler` | Exact match → matched=1, ENTAILS, score_contribution=1.0 |
| 2 | `test_paraphrase_compiler` | Paraphrase → matched, ENTAILS or UNCERTAIN |
| 3 | `test_correct_additional_primary_key` | Core+extra → matched≥1, unmatched≥1, NOT_EVALUATED |
| 4 | `test_irrelevant_additional_sql` | Two-sentence → unmatched preserved, classification correct |
| 5 | `test_incorrect_additional_duplicates` | Core+wrong info → unmatched preserved |
| 6 | `test_completely_unrelated` | Unrelated answer → very few/no matches |
| 7 | `test_span_char_start_valid_single_sentence` | Span char_start ≥ 0 for single sentence |
| 8 | `test_span_text_matches_original_single` | span_text is non-empty, within original answer |
| 9 | `test_span_multi_sentence_valid` | Multi-sentence → at least some valid spans |
| 10 | `test_one_to_one_preserved` | No duplicate reference_proposition_index values |
| 11 | `test_json_serializable` | to_json() returns valid JSON with 'original_student_answer' |
| 12 | `test_base_score_unchanged` | base_asag_normalized_score == pipeline normalized_score |
| 13 | `test_unmatched_reference_preserved` | Partial answer → unmatched ref preserved or score < 1.0 |
| 14 | `test_no_additional_information_classification` | No Stage 13 labels in Stage 11 output |
| 15 | `test_conjoined_clause_span_isolation` | Conjoined clauses isolated: "cannot contain NULL values" [61:87] |
| 16 | `test_compiler_span_exact_substring` | Exact proposition span extraction on compiler sentence |
| 17 | `test_one_to_one_competition_rejection` | Rejection reason explicitly cites one-to-one matching constraints |
| 18 | `test_polarity_and_contradiction_evidence` | Negation preserves CONTRADICTS, 0.0 contribution, NEGATED polarity |
| 19 | `test_empty_student_answer` | Robust handling of empty student answer |
| 20 | `test_whitespace_student_answer` | Robust handling of whitespace-only student answer |
| 21 | `test_whitespace_resilience_in_span` | Resilience to collapsed internal whitespace in student answer |

---

## 11. Test Results

```
tests/test_stage11_alignment.py ..................... [100%]
21 passed in 2.98s

Full suite:
203 passed in 6.35s
```

**Tests before Stage 11**: 182  
**Tests after Stage 11**: 203  
**New tests added**: 21  

All pre-existing 182 tests continue to pass without regression.

---

## 12. Limitations

1. **Span Approximation**: `char_offset` is relative to the normalized sentence text.
   For multi-sentence answers, the sentence is mapped into the original answer using
   exact substring or whitespace-resilient regex search. If normalization changes characters
   (beyond whitespace and punctuation), offsets could be slightly shifted.
2. **Identical sentence collision**: For multi-sentence answers, `str.find()` locates the
   first occurrence. If two identical sentences occur in the same answer, the second sentence
   could map to the first sentence's offset.
3. **No classification**: Stage 11 does not evaluate the content of unmatched propositions.
   Whether they represent correct, irrelevant, or incorrect information is unknown
   until Stage 13 is implemented.
4. **Entailment coverage**: If Stage 8 produced no `EntailmentResult` for a matched
   relation (e.g. due to an edge case), the entailment_status is reported as
   `"NO_ENTAILMENT_RESULT"`. This is conservative and transparent.

---

## 13. Future Use by Proposed Extension (Stage 13)

Stage 11 is the direct input to Stage 13.

`PropositionAlignmentResult.unmatched_student_propositions` provides Stage 13 with:
- The full `DependencyRelation` representation of each unmatched proposition.
- Its character span in the original answer for context.
- The best rejected candidate alignment (for reasoning about near-misses).
- The current placeholder classification `"NOT_EVALUATED_BY_BASE_ASAG"`.

Stage 13 will replace `"NOT_EVALUATED_BY_BASE_ASAG"` with one of:
- `"CORRECT_ADDITIONAL"` — verified by external knowledge or entailment
- `"IRRELEVANT"` — no relevance to the question
- `"INCORRECT_ADDITIONAL"` — contradicts verified knowledge

> **RESEARCH HYPOTHESIS**: Incorporating this classification into the grade
> (Stage 14) may improve agreement with human grading. This remains experimental
> and must not be assumed to work until experiments demonstrate it.

---

## 14. Future Use by Explainable Interface

The `PropositionAlignmentResult.to_json()` output could power an explainable
grading interface that:

- Shows which parts of the student answer were matched (with highlighted spans).
- Identifies matched propositions and their entailment status (ENTAILS/UNCERTAIN/CONTRADICTS).
- Lists unmatched student propositions as "additional information not evaluated".
- Highlights unmatched reference propositions as "missing from the answer".

> **NOTE**: A web interface is secondary to the research objectives and should only
> be developed after the core ASAG research pipeline is complete and validated.

---

## Confirmation Checklist

| Item | Status |
|---|---|
| No additional-info classification (CORRECT_ADDITIONAL etc.) | ✅ Not implemented |
| No scoring change | ✅ Base ASAG score preserved exactly |
| No frontend | ✅ No web components added |
| Base ASAG intact | ✅ No base_asag/ files modified |
| No pipeline.py modification | ✅ Not modified |
| Does not re-run Stage 7 matching | ✅ Consumes pipeline_result.matching_result |
| JSON serializable | ✅ All to_dict() and to_json() verified |
| 21 Stage 11 tests pass | ✅ 21/21 |
| 182 prior tests still pass | ✅ 203 total, all pass |
