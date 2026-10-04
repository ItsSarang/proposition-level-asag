# Stage 12 Report: Proposition-Level Representation

**Implementation Date:** Stage 12 of the ASAG Research Pipeline  
**Repository:** proposition-level-asag  
**Research Stage:** STAGE 12 — Proposition-Level Representation  

---

## 1. Research Motivation

The overarching research question of this project is:
> *"Can an interpretable proposition-level extension of a classical semantic/dependency-based ASAG system evaluate unmatched student information as correct additional, irrelevant, or incorrect information, and does incorporating this evaluation improve agreement with human grading?"*

In Stage 11, the pipeline established the ability to identify *which* student propositions were matched vs unmatched and recorded character-level provenance. However, raw character strings and flat dependency tuples are insufficient on their own for semantic classification. To evaluate whether unmatched information represents correct additional knowledge, an irrelevant tangent, or a misconception (Stage 13), the system requires an explicit, structured representation of each proposition's linguistic constituents, semantic arguments, polarity, and context.

Stage 12 establishes this interpretable structural foundation.

---

## 2. Stage 12 Objective

The objective of Stage 12 is to construct a **unified proposition-level representation** (`PropositionRepresentation`) that organizes and enriches each extracted proposition with:
1. Exact surface text and character span in the original student answer.
2. Canonical clause-level dependency structure (subject, predicate, object, lemma forms).
3. Syntactic arguments and modifiers (compound nouns, adjectival modifiers, adverbial modifiers, prepositional phrases).
4. Detailed token-level linguistics (lemmas, coarse Universal POS, fine-grained Penn Treebank tags, dependency labels, head pointers).
5. Grammatical and lexical polarity (POSITIVE vs NEGATED) from Stage 8.
6. Complete matching and entailment provenance from Stages 6, 7, 8, 9, and 11.
7. Evaluation context (prompt question and model reference answer).
8. Pure JSON serializability without leaking internal parser or runtime objects.

---

## 3. Relationship to Stage 11

Stage 12 directly consumes the output of Stage 11 (`PropositionAlignmentResult`) alongside the pipeline result (`BaseASAGPipelineResult`) from Stage 10:

```
Stage 10: BaseASAGPipelineResult
      ↓
Stage 11: PropositionAlignmentResult (Spans, Matched/Unmatched Sets)
      ↓
Stage 12: DocumentPropositionRepresentation / PropositionRepresentation
      ↓
Stage 13: (future) Additional-Information Classifier
      ↓
Stage 14: (future) Proposed Grading Mechanism
```

- **Reuses Stage 11 Spans:** Character offsets, token index sets, and original text slices are reused directly, preserving the conjoined clause span isolation established in Stage 11.
- **Reuses Stage 11 Diagnostics:** Rejection reasons, best candidate scores, and candidate reference indices are carried over into `MatchingProvenance`.
- **Common Abstraction:** While Stage 11 separates `MatchedPropositionEvidence` and `UnmatchedStudentPropositionEvidence` into distinct classes, Stage 12 unifies them into a single `PropositionRepresentation` equipped with `is_matched` and `is_unmatched` status fields.

---

## 4. Proposition Representation Design

> **OUR IMPLEMENTATION DECISION**: Rather than maintaining separate, disparate classes for matched and unmatched propositions, Stage 12 adopts a single, unified `PropositionRepresentation` model with explicit status attributes.

This ensures that downstream processing in Stage 13 can iterate through propositions uniformly, inspecting shared structural properties (subject, predicate, object, polarity, prepositional phrases) regardless of whether the proposition was matched by the Base ASAG.

---

## 5. Data Model

The Stage 12 data model consists of six strongly typed dataclasses in `proposed_asag/proposition/representation.py`:

### 1. `LinguisticArgument`
Represents an individual syntactic argument or modifier:
- `role`: `"subject"`, `"predicate"`, `"object"`, or `"prepositional_argument"`.
- `text`, `lemma`, `pos`, `tag`, `dep`.
- `token_index`, `head_token_index`.
- `modifiers`: Surface texts of dependent compound nouns, determiners, or adjectives.

### 2. `LinguisticStructure`
Detailed token-level and dependency-level linguistic attributes of a proposition:
- `tokens`: List of surface tokens in the proposition span.
- `token_indices`: Sentence-relative indices in sorted order.
- `lemmas`: Lemmatized forms.
- `pos_tags`: Universal POS tags.
- `detailed_tags`: Penn Treebank POS tags.
- `dependency_labels`: Syntactic dependency relations.
- `heads`, `head_indices`: Head tokens and indices.
- `arguments`: List of `LinguisticArgument` objects.

### 3. `PropositionContext`
Contextual prompt and reference information:
- `question`: Prompt question text.
- `reference_answer`: Reference answer text.
- `total_reference_propositions`: Count of reference propositions.
- `reference_propositions`: List of serialized reference relations.

### 4. `MatchingProvenance`
Evidence connecting the proposition to the Base ASAG pipeline:
- `match_status`: `"MATCHED"` or `"UNMATCHED"`.
- `classification`: `"MATCHED_BY_BASE_ASAG"` or `"NOT_EVALUATED_BY_BASE_ASAG"`.
- `score_effect`: Base ASAG score contribution (1.0, 0.5, or 0.0).
- `alignment_threshold`: Threshold used in Stage 7 (e.g. 0.50).
- Matched fields: `reference_proposition_index`, `reference_relation`, `triple_score`, `match_method`, `subject_similarity`, `predicate_similarity`, `object_similarity`, `slot_evidence`, `entailment_status`, `entailment_confidence`, `diagnostic_reasons`.
- Unmatched fields: `best_candidate_reference_index`, `best_candidate_score`, `best_candidate_relation`, `rejection_reason`.

### 5. `PropositionRepresentation`
The unified proposition model:
- `proposition_id`: Unique identifier (e.g. `"stu_prop_0"`).
- `proposition_index`, `sentence_index`.
- `text`: Extracted span slice from the original student answer.
- `span`: `SpanInfo` provenance.
- `relation`: Enriched dictionary containing SPO, lemmas, modifiers, and prepositional arguments.
- `polarity`: `"POSITIVE"` or `"NEGATED"`.
- `is_negated`: Boolean flag.
- `negation_tokens`: List of triggering tokens (e.g. `["not"]`).
- `polarity_evidence`: Human-readable explanation.
- `linguistics`: `LinguisticStructure`.
- `matching`: `MatchingProvenance`.
- `context`: `PropositionContext`.

### 6. `DocumentPropositionRepresentation`
Top-level container for all proposition representations in an evaluated answer:
- `student_answer`, `question`, `reference_answer`.
- `base_asag_normalized_score`: Preserved unchanged from Stage 9.
- `total_student_propositions`, `matched_count`, `unmatched_count`.
- `propositions`, `matched_propositions`, `unmatched_propositions`.
- `unmatched_reference_propositions`.
- `context`: Shared `PropositionContext`.
- Methods: `get_proposition(id_or_index)`, `to_dict()`, `to_json()`.

---

## 6. Provenance

Every proposition is strictly traceable back to the raw, unedited student answer:
- `student_answer[span.char_start:span.char_end]` accurately recovers `prop.text`.
- `sentence_index` indicates which sentence generated the proposition.
- `token_indices` link the proposition to exact token positions within the sentence.
- Zero fabrication of character spans or tokens.

---

## 7. Matched Propositions

For matched student propositions:
- `match_status = "MATCHED"`
- `classification = "MATCHED_BY_BASE_ASAG"`
- Preserves reference proposition link (`reference_proposition_index`, `reference_relation`).
- Preserves Stage 6 slot similarities and semantic evidence.
- Preserves Stage 7 composite `triple_score` and `match_method`.
- Preserves Stage 8 `entailment_status` (`ENTAILS`, `CONTRADICTS`, `UNCERTAIN`) and `confidence`.
- Preserves Stage 9 `score_contribution` (`1.0`, `0.5`, or `0.0`).

---

## 8. Unmatched Propositions

For unmatched student propositions:
- `match_status = "UNMATCHED"`
- `classification = "NOT_EVALUATED_BY_BASE_ASAG"` (Stage 11/12 invariant).
- `score_effect = 0.0` (Stage 11/12 invariant).
- Preserves `best_candidate_reference_index`, `best_candidate_score`, and `best_candidate_relation`.
- Preserves the diagnostic `rejection_reason` (distinguishing between below-threshold alignment and one-to-one competition loss).

> **RESEARCH INTEGRITY**: Stage 12 does NOT classify unmatched propositions. An unmatched proposition is never assumed to be incorrect.

---

## 9. Polarity

Stage 12 reuses the Stage 8 `PolarityDetector` to assign explicit polarity to every proposition:
- `polarity`: `"POSITIVE"` or `"NEGATED"`.
- `is_negated`: Boolean negation indicator.
- `negation_tokens`: Explicit trigger tokens (e.g. `"not"`, `"cannot"`, `"never"`, `"no"`).
- `polarity_evidence`: Explanatory description.

For example:
- *"A primary key uniquely identifies records"* → `POSITIVE`, `is_negated=False`, `negation_tokens=[]`.
- *"cannot contain NULL values"* → `NEGATED`, `is_negated=True`, `negation_tokens=["not"]`.
- *"does not identify records"* → `NEGATED`, `is_negated=True`, `negation_tokens=["not"]`.

---

## 10. Semantic & Matching Evidence Reuse

Stage 12 does NOT recompute semantic similarity, re-run triple matching, or re-execute entailment logic:
- Slot evidence dictionaries from Stage 6 are preserved intact.
- Greedy one-to-one matching results from Stage 7 are preserved intact.
- Entailment decisions and confidence scores from Stage 8 are preserved intact.
- Reference coverage scoring from Stage 9 is preserved intact.

---

## 11. Serialization

All Stage 12 classes implement `.to_dict()` and produce clean, nested dictionaries consisting exclusively of Python standard primitive types (`str`, `int`, `float`, `bool`, `list`, `dict`, `None`).
- No raw spaCy `Doc`, `Span`, or `Token` objects are exposed.
- No `DependencyRelation`, `MatchedRelation`, or `EntailmentResult` instances leak into the dictionary output.
- `DocumentPropositionRepresentation.to_json(indent=2)` generates formatted, parseable JSON.

---

## 12. Tests

The Stage 12 test suite in `tests/test_stage12_representation.py` covers 28 unit and integration tests across 12 test classes:

| Test Class | Test Name | Description |
|:---|:---|:---|
| `TestSimplePropositionRepresentation` | `test_simple_proposition_representation` | Validates basic attributes, IDs, sentence indices, and status flags. |
| `TestMatchedPropositionRepresentation` | `test_matched_proposition_representation` | Validates matched proposition provenance, reference link, and score contribution. |
| `TestUnmatchedPropositionRepresentation` | `test_unmatched_proposition_representation` | Validates unmatched status, `NOT_EVALUATED_BY_BASE_ASAG`, and rejection reasons. |
| `TestDemonstrationRepresentations` | `test_correct_additional_demo` | Student B demo representation without classification. |
| | `test_irrelevant_additional_demo` | Student D demo representation without classification. |
| | `test_incorrect_additional_demo` | Student C demo representation without classification. |
| | `test_no_additional_info_classification_applied` | Verifies no Stage 13 labels exist in any Stage 12 output. |
| `TestSpanAndProvenance` | `test_exact_character_spans` | Asserts `raw_answer[char_start:char_end] == prop.text`. |
| | `test_sentence_index` | Verifies correct multi-sentence index mapping. |
| | `test_token_indices` | Verifies sentence-relative token indices align with tokens. |
| `TestLinguisticArguments` | `test_subject_predicate_object` | Verifies core SPO relation fields and lemmas. |
| | `test_additional_arguments` | Verifies prepositional phrase arguments (into machine code, for syntax errors). |
| | `test_modifiers` | Verifies compound, amod, and advmod modifiers. |
| `TestPolarityRepresentation` | `test_positive_polarity` | Verifies positive polarity attributes. |
| | `test_negative_polarity` | Verifies negated polarity attributes and trigger tokens. |
| `TestMultiplePropositionsAndSentences` | `test_multiple_propositions` | Verifies multiple propositions within a single conjoined sentence. |
| | `test_multiple_sentences` | Verifies propositions across multi-sentence documents. |
| `TestContextPreservation` | `test_question_context` | Verifies question prompt preservation. |
| | `test_reference_answer_context` | Verifies reference answer and reference relations preservation. |
| `TestEvidencePreservation` | `test_semantic_evidence_preservation` | Verifies Stage 6 slot evidence preservation. |
| | `test_matching_evidence_preservation` | Verifies Stage 7 matching scores and thresholds preservation. |
| | `test_entailment_evidence_preservation` | Verifies Stage 8 entailment decisions and reasons preservation. |
| `TestSerializationAndNoSpacy` | `test_json_serialization` | Verifies `to_json()` produces valid, parseable JSON. |
| | `test_no_raw_spacy_objects` | Verifies strict purity of dictionary output (primitives only). |
| `TestInvarianceAndRegression` | `test_base_score_unchanged` | Verifies Base ASAG normalized score is preserved exactly. |
| | `test_one_to_one_matching_unchanged` | Verifies one-to-one reference matching constraints are maintained. |
| | `test_stage11_alignment_regression` | Verifies exact count and status parity with Stage 11 alignment. |
| | `test_get_proposition_lookup` | Verifies retrieval by proposition ID and integer index. |

**Test Results:**
- Stage 12 Suite: **28 passed** in 3.23s
- Full Suite (Stages 1–12): **231 passed** in 6.62s (0 failures, 0 errors, 0 skipped)

---

## 13. What Stage 12 Does NOT Do

- Does **NOT** classify unmatched propositions as `CORRECT_ADDITIONAL`, `IRRELEVANT`, or `INCORRECT`.
- Does **NOT** modify or recalculate the Base ASAG score.
- Does **NOT** apply any bonus or penalty for additional information.
- Does **NOT** perform question-answer semantic inference.
- Does **NOT** call external LLM APIs, neural embeddings, or transformer models.
- Does **NOT** implement frontend UI or web application logic.

---

## 14. Limitations

1. **Syntactic Attachment Ambiguities:** Prepositional phrases are extracted based on dependency trees produced by spaCy (`prep` relations attached to the predicate or object). In complex sentences with attachment ambiguity (e.g. PP attaching to noun vs verb), the extraction reflects spaCy's statistical parse.
2. **First-Occurrence Multi-Sentence Offset Mapping:** For multi-sentence inputs, sentence spans map into the full answer string using exact substring or regex search. If identical sentences appear multiple times in a single answer, subsequent occurrences would locate the first occurrence.
3. **Lexical Semantic Metric Invariance:** Stage 12 does not resolve known WordNet limitations (e.g. low path similarity for `translate ↔ convert`). It transparently records whatever semantic evidence Stage 6 produced.

---

## 15. Relationship to Future Stage 13

Stage 12 provides the exact structured input required for **Stage 13 (Additional-Information Classification)**.

When Stage 13 evaluates an unmatched student proposition (`is_unmatched == True`), it will have access to:
- The exact clause text (`prop.text`) and original span (`prop.span`).
- The canonical predicate, subject, and object (`prop.relation`).
- Any prepositional phrases or modifiers (`prop.relation["prepositional_arguments"]`).
- The polarity of the claim (`prop.polarity`, `prop.is_negated`).
- The prompt question and reference answer context (`prop.context`).
- The best candidate rejected alignment from Stage 7 (`prop.matching.best_candidate_score`).

Stage 13 will then evaluate whether the proposition is:
1. `CORRECT_ADDITIONAL` (valid domain knowledge relevant to the question).
2. `IRRELEVANT` (unrelated to the question/topic).
3. `INCORRECT_ADDITIONAL` (factually contradictory or a misconception).

---

## 16. Relationship to Future Website Visualization

The `DocumentPropositionRepresentation.to_json()` structure contains all information needed for a future explainable ASAG interface:
- Highlighting exact student text spans (`prop.span.char_start`, `prop.span.char_end`).
- Showing matched propositions alongside their reference counterpart and entailment decision.
- Displaying unmatched propositions alongside their extracted arguments, modifiers, and polarity.
- Displaying slot-level semantic evidence (exact match, lemma match, WordNet similarity).

---

## Confirmation Checklist

| Item | Status |
|:---|:---:|
| Unified representation for matched and unmatched propositions | ✅ Implemented |
| No additional-information classification (`CORRECT_ADDITIONAL`, etc.) | ✅ Enforced (`NOT_EVALUATED_BY_BASE_ASAG`) |
| No Base ASAG scoring changes (`score_effect = 0.0` for unmatched) | ✅ Verified |
| Exact character span and provenance preservation | ✅ Verified |
| Polarity preservation from Stage 8 | ✅ Verified |
| Prepositional and modifier argument extraction | ✅ Implemented & Verified |
| Context preservation (question & reference answer) | ✅ Verified |
| JSON serialization & zero raw spaCy objects | ✅ Verified |
| Stage 12 tests pass | ✅ 28/28 passed |
| Full test suite passes without regression | ✅ 231/231 passed |
