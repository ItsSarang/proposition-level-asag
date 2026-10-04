"""
Stage 12 Tests: Proposition-Level Representation.

Tests for PropositionRepresentation, DocumentPropositionRepresentation,
and PropositionRepresentationBuilder in proposed_asag.proposition.representation.

Test Coverage:
--------------
1.  test_simple_proposition_representation: basic fields, types, and properties.
2.  test_matched_proposition_representation: matched proposition provenance.
3.  test_unmatched_proposition_representation: unmatched proposition provenance.
4.  test_correct_additional_demo: Student B representation (NOT classified).
5.  test_irrelevant_additional_demo: Student D representation (NOT classified).
6.  test_incorrect_additional_demo: Student C representation (NOT classified).
7.  test_exact_character_spans: student_answer[char_start:char_end] == prop.text.
8.  test_sentence_index: accurate sentence index mapping.
9.  test_token_indices: accurate sentence-relative token indices.
10. test_subject_predicate_object: core SPO extraction preserved.
11. test_additional_arguments: prepositional arguments (e.g. into machine code, in table).
12. test_positive_polarity: positive claim polarity attributes.
13. test_negative_polarity: negated claim polarity attributes.
14. test_multiple_propositions: multiple propositions in a single sentence.
15. test_multiple_sentences: propositions across multi-sentence documents.
16. test_question_context: question context preserved in representation.
17. test_reference_answer_context: reference answer and propositions preserved.
18. test_semantic_evidence_preservation: Stage 6 slot evidence preserved.
19. test_matching_evidence_preservation: Stage 7 matching evidence preserved.
20. test_entailment_evidence_preservation: Stage 8 entailment evidence preserved.
21. test_json_serialization: to_json() produces valid, parseable JSON.
22. test_no_raw_spacy_objects: public dictionary contains only primitives/dicts/lists.
23. test_base_score_unchanged: Stage 12 does not modify Base ASAG score.
24. test_one_to_one_matching_unchanged: one-to-one reference matching preserved.
25. test_stage11_alignment_regression: perfect parity with Stage 11 alignment counts.

Data Note:
----------
All examples here are DEMO DATA — NOT RESEARCH DATA.
They are used solely to verify Stage 12 implementation correctness.

Research Boundaries:
--------------------
- Stage 12 represents structure; it does NOT classify unmatched information.
- classification is always "NOT_EVALUATED_BY_BASE_ASAG" for unmatched propositions.
- score_effect is always 0.0 for unmatched propositions.
- The Base ASAG score is NOT modified by Stage 12.
"""

import json
from typing import Any, Dict, List
import pytest

from base_asag.pipeline import BaseASAGPipeline
from proposed_asag.proposition.alignment import PropositionAlignmentExtractor
from proposed_asag.proposition.representation import (
    DocumentPropositionRepresentation,
    LinguisticArgument,
    LinguisticStructure,
    MatchingProvenance,
    PropositionContext,
    PropositionRepresentation,
    PropositionRepresentationBuilder,
)


# ============================================================
# DEMO DATA — NOT RESEARCH DATA
# ============================================================

QUESTION_PK = "What is the purpose of a primary key?"
REF_PK = "A primary key uniquely identifies each record in a table."

QUESTION_COMPILER = "What does a compiler do?"
REF_COMPILER = "A compiler translates high-level source code into machine code."


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture(scope="module")
def pipeline():
    return BaseASAGPipeline()


@pytest.fixture(scope="module")
def builder():
    return PropositionRepresentationBuilder()


@pytest.fixture(scope="module")
def extractor():
    return PropositionAlignmentExtractor()


# --- Pipeline & Representation Fixtures ---

@pytest.fixture(scope="module")
def doc_exact_pk(pipeline, builder):
    """Exact primary key match."""
    res = pipeline.grade(
        question=QUESTION_PK,
        reference_answer=REF_PK,
        student_answer="A primary key uniquely identifies each record in a table.",
    )
    return builder.build(res)


@pytest.fixture(scope="module")
def doc_correct_additional(pipeline, builder):
    """Student B: Core correct + correct additional clause."""
    res = pipeline.grade(
        question=QUESTION_PK,
        reference_answer=REF_PK,
        student_answer="A primary key uniquely identifies each record in a table and cannot contain NULL values.",
    )
    return builder.build(res)


@pytest.fixture(scope="module")
def doc_irrelevant_additional(pipeline, builder):
    """Student D: Core correct + irrelevant sentence."""
    res = pipeline.grade(
        question=QUESTION_PK,
        reference_answer=REF_PK,
        student_answer="A primary key uniquely identifies each record in a table. SQL was developed in the 1970s.",
    )
    return builder.build(res)


@pytest.fixture(scope="module")
def doc_incorrect_additional(pipeline, builder):
    """Student C: Core correct + incorrect clause."""
    res = pipeline.grade(
        question=QUESTION_PK,
        reference_answer=REF_PK,
        student_answer="A primary key uniquely identifies each record in a table and can contain duplicate values.",
    )
    return builder.build(res)


@pytest.fixture(scope="module")
def doc_compiler_paraphrase(pipeline, builder):
    """Compiler paraphrase: translates -> converts."""
    res = pipeline.grade(
        question=QUESTION_COMPILER,
        reference_answer=REF_COMPILER,
        student_answer="A compiler converts high-level source code into machine code.",
    )
    return builder.build(res)


@pytest.fixture(scope="module")
def doc_compiler_with_args(pipeline, builder):
    """Compiler with multiple prepositional arguments."""
    res = pipeline.grade(
        question=QUESTION_COMPILER,
        reference_answer=REF_COMPILER,
        student_answer="A compiler translates high-level source code into machine code and checks the program for syntax errors.",
    )
    return builder.build(res)


@pytest.fixture(scope="module")
def doc_negated_pk(pipeline, builder):
    """Direct negation of the core fact."""
    res = pipeline.grade(
        question=QUESTION_PK,
        reference_answer=REF_PK,
        student_answer="A primary key does not identify each record in a table.",
    )
    return builder.build(res)


# ============================================================
# Test Classes
# ============================================================

class TestSimplePropositionRepresentation:
    """1. Basic proposition representation tests."""

    def test_simple_proposition_representation(self, doc_exact_pk):
        assert isinstance(doc_exact_pk, DocumentPropositionRepresentation)
        assert doc_exact_pk.total_student_propositions >= 1
        assert doc_exact_pk.matched_count >= 1
        assert doc_exact_pk.unmatched_count == 0

        prop = doc_exact_pk.propositions[0]
        assert isinstance(prop, PropositionRepresentation)
        assert prop.proposition_id == "stu_prop_0"
        assert prop.proposition_index == 0
        assert prop.sentence_index == 0
        assert prop.is_matched is True
        assert prop.is_unmatched is False
        assert len(prop.text) > 0


class TestMatchedPropositionRepresentation:
    """2. Matched proposition representation tests."""

    def test_matched_proposition_representation(self, doc_exact_pk):
        prop = doc_exact_pk.matched_propositions[0]
        assert prop.is_matched is True
        assert prop.matching.match_status == "MATCHED"
        assert prop.matching.classification == "MATCHED_BY_BASE_ASAG"
        assert prop.matching.score_effect == 1.0
        assert prop.matching.reference_proposition_index == 0
        assert prop.matching.triple_score == 1.0
        assert prop.matching.entailment_status == "ENTAILS"
        assert prop.matching.score_contribution == 1.0
        assert prop.matching.reference_relation is not None
        assert "subject" in prop.matching.reference_relation


class TestUnmatchedPropositionRepresentation:
    """3. Unmatched proposition representation tests."""

    def test_unmatched_proposition_representation(self, doc_correct_additional):
        assert doc_correct_additional.unmatched_count >= 1
        prop = doc_correct_additional.unmatched_propositions[0]

        assert prop.is_unmatched is True
        assert prop.is_matched is False
        assert prop.matching.match_status == "UNMATCHED"
        assert prop.matching.classification == "NOT_EVALUATED_BY_BASE_ASAG"
        assert prop.matching.score_effect == 0.0
        assert prop.matching.reference_proposition_index is None
        assert prop.matching.triple_score is None
        assert prop.matching.score_contribution == 0.0
        assert prop.matching.rejection_reason is not None
        assert len(prop.matching.rejection_reason) > 0


class TestDemonstrationRepresentations:
    """4, 5, 6. Controlled demonstration cases (MUST NOT BE CLASSIFIED)."""

    def test_correct_additional_demo(self, doc_correct_additional):
        """Student B demonstration representation."""
        matched = doc_correct_additional.matched_propositions
        unmatched = doc_correct_additional.unmatched_propositions

        assert len(matched) == 1
        assert len(unmatched) == 1

        # Research constraint: must NOT be labeled CORRECT_ADDITIONAL
        assert unmatched[0].classification == "NOT_EVALUATED_BY_BASE_ASAG"
        assert unmatched[0].score_effect == 0.0
        assert unmatched[0].relation["predicate"] == "contain"

    def test_irrelevant_additional_demo(self, doc_irrelevant_additional):
        """Student D demonstration representation."""
        matched = doc_irrelevant_additional.matched_propositions
        unmatched = doc_irrelevant_additional.unmatched_propositions

        assert len(matched) == 1
        assert len(unmatched) == 1

        # Research constraint: must NOT be labeled IRRELEVANT
        assert unmatched[0].classification == "NOT_EVALUATED_BY_BASE_ASAG"
        assert unmatched[0].score_effect == 0.0
        assert unmatched[0].relation["subject"] == "SQL"

    def test_incorrect_additional_demo(self, doc_incorrect_additional):
        """Student C demonstration representation."""
        matched = doc_incorrect_additional.matched_propositions
        unmatched = doc_incorrect_additional.unmatched_propositions

        assert len(matched) == 1
        assert len(unmatched) == 1

        # Research constraint: must NOT be labeled INCORRECT
        assert unmatched[0].classification == "NOT_EVALUATED_BY_BASE_ASAG"
        assert unmatched[0].score_effect == 0.0
        assert unmatched[0].relation["predicate"] == "contain"

    def test_no_additional_info_classification_applied(
        self,
        doc_exact_pk,
        doc_correct_additional,
        doc_irrelevant_additional,
        doc_incorrect_additional,
    ):
        """Verify no Stage 13 labels exist anywhere in Stage 12 outputs."""
        forbidden = {"CORRECT_ADDITIONAL", "IRRELEVANT", "INCORRECT", "INCORRECT_ADDITIONAL"}
        for doc in [doc_exact_pk, doc_correct_additional, doc_irrelevant_additional, doc_incorrect_additional]:
            for p in doc.propositions:
                assert p.classification not in forbidden
                assert p.matching.classification not in forbidden


class TestSpanAndProvenance:
    """7, 8, 9. Character span and provenance tests."""

    def test_exact_character_spans(self, doc_correct_additional):
        """Verify student_answer[char_start:char_end] reproduces the exact proposition text."""
        raw_answer = doc_correct_additional.student_answer

        for prop in doc_correct_additional.propositions:
            st = prop.span.char_start
            en = prop.span.char_end
            assert st >= 0
            assert en > st
            slice_text = raw_answer[st:en]
            assert slice_text == prop.text
            assert slice_text == prop.span.span_text

    def test_sentence_index(self, doc_irrelevant_additional):
        """Verify sentence_index accurately reflects document sentence segmentation."""
        p0 = doc_irrelevant_additional.propositions[0]
        p1 = doc_irrelevant_additional.propositions[1]

        assert p0.sentence_index == 0
        assert p1.sentence_index == 1

    def test_token_indices(self, doc_exact_pk):
        """Verify token indices match the proposition tokens in the parsed sentence."""
        prop = doc_exact_pk.propositions[0]
        assert len(prop.linguistics.token_indices) > 0
        assert prop.linguistics.token_indices == sorted(prop.linguistics.token_indices)
        assert len(prop.linguistics.tokens) == len(prop.linguistics.token_indices)


class TestLinguisticArguments:
    """10, 11. Core relations, arguments, and modifiers."""

    def test_subject_predicate_object(self, doc_exact_pk):
        """Verify core SPO relation fields."""
        prop = doc_exact_pk.propositions[0]
        rel = prop.relation

        assert rel["subject"] == "key"
        assert rel["predicate"] == "identifies"
        assert rel["object"] == "record"
        assert rel["subject_lemma"] == "key"
        assert rel["predicate_lemma"] == "identify"
        assert rel["object_lemma"] == "record"
        assert rel["relation_type"] == "SPO"

    def test_additional_arguments(self, doc_compiler_with_args):
        """Verify prepositional arguments attached to predicate or object."""
        props = doc_compiler_with_args.propositions
        assert len(props) == 2

        # Proposition 0: compiler translates code [into machine code]
        p0 = props[0]
        p0_preps = [a for a in p0.linguistics.arguments if a.role == "prepositional_argument"]
        assert len(p0_preps) >= 1
        assert any("into" in a.text for a in p0_preps)

        # Proposition 1: compiler checks program [for syntax errors]
        p1 = props[1]
        p1_preps = [a for a in p1.linguistics.arguments if a.role == "prepositional_argument"]
        assert len(p1_preps) >= 1
        assert any("for" in a.text and "errors" in a.text for a in p1_preps)

    def test_modifiers(self, doc_exact_pk):
        """Verify subject, object, and adverbial modifiers are extracted."""
        prop = doc_exact_pk.propositions[0]
        assert "primary" in prop.relation.get("subject_modifiers", [])
        assert "uniquely" in prop.relation.get("adverbial_modifiers", [])


class TestPolarityRepresentation:
    """12, 13. Positive and negative polarity tests."""

    def test_positive_polarity(self, doc_exact_pk):
        prop = doc_exact_pk.propositions[0]
        assert prop.polarity == "POSITIVE"
        assert prop.is_negated is False
        assert len(prop.negation_tokens) == 0
        assert "positive" in prop.polarity_evidence.lower()

    def test_negative_polarity(self, doc_correct_additional, doc_negated_pk):
        # 1. Unmatched negative proposition: cannot contain NULL values
        unmatched_neg = doc_correct_additional.unmatched_propositions[0]
        assert unmatched_neg.polarity == "NEGATED"
        assert unmatched_neg.is_negated is True
        assert len(unmatched_neg.negation_tokens) > 0
        assert any("not" in t or "cannot" in t for t in unmatched_neg.negation_tokens)

        # 2. Matched contradictory negative proposition: does not identify
        matched_neg = doc_negated_pk.matched_propositions[0]
        assert matched_neg.polarity == "NEGATED"
        assert matched_neg.is_negated is True
        assert matched_neg.matching.entailment_status == "CONTRADICTS"


class TestMultiplePropositionsAndSentences:
    """14, 15. Single-sentence conjoined and multi-sentence documents."""

    def test_multiple_propositions(self, doc_correct_additional):
        """Multiple propositions within a single conjoined sentence."""
        assert doc_correct_additional.total_student_propositions == 2
        p0 = doc_correct_additional.propositions[0]
        p1 = doc_correct_additional.propositions[1]

        assert p0.sentence_index == 0
        assert p1.sentence_index == 0
        assert p0.proposition_id != p1.proposition_id
        # Verify non-overlapping spans
        assert p0.span.char_end <= p1.span.char_start

    def test_multiple_sentences(self, doc_irrelevant_additional):
        """Propositions spanning multiple distinct sentences."""
        assert doc_irrelevant_additional.total_student_propositions == 2
        p0 = doc_irrelevant_additional.propositions[0]
        p1 = doc_irrelevant_additional.propositions[1]

        assert p0.sentence_index == 0
        assert p1.sentence_index == 1
        assert p0.text != p1.text


class TestContextPreservation:
    """16, 17. Question and reference context preservation."""

    def test_question_context(self, doc_exact_pk):
        assert doc_exact_pk.question == QUESTION_PK
        assert doc_exact_pk.context.question == QUESTION_PK
        for prop in doc_exact_pk.propositions:
            assert prop.context.question == QUESTION_PK

    def test_reference_answer_context(self, doc_exact_pk):
        assert doc_exact_pk.reference_answer == REF_PK
        assert doc_exact_pk.context.reference_answer == REF_PK
        assert doc_exact_pk.context.total_reference_propositions >= 1
        assert len(doc_exact_pk.context.reference_propositions) >= 1
        ref_p0 = doc_exact_pk.context.reference_propositions[0]
        assert "subject" in ref_p0
        assert "predicate" in ref_p0


class TestEvidencePreservation:
    """18, 19, 20. Semantic, matching, and entailment evidence preservation."""

    def test_semantic_evidence_preservation(self, doc_compiler_paraphrase):
        """Verify Stage 6 slot evidence is preserved on matched propositions."""
        prop = doc_compiler_paraphrase.matched_propositions[0]
        slot_ev = prop.matching.slot_evidence
        assert isinstance(slot_ev, dict)
        assert "subject" in slot_ev
        assert "predicate" in slot_ev
        assert "similarity_score" in slot_ev["predicate"]

    def test_matching_evidence_preservation(self, doc_compiler_paraphrase):
        """Verify Stage 7 matching scores and thresholds are preserved."""
        prop = doc_compiler_paraphrase.matched_propositions[0]
        assert prop.matching.triple_score is not None
        assert prop.matching.triple_score > 0.0
        assert prop.matching.alignment_threshold == 0.50
        assert prop.matching.match_method is not None

    def test_entailment_evidence_preservation(self, doc_compiler_paraphrase):
        """Verify Stage 8 entailment decisions and reasons are preserved."""
        prop = doc_compiler_paraphrase.matched_propositions[0]
        assert prop.matching.entailment_status in ("ENTAILS", "UNCERTAIN")
        assert prop.matching.entailment_confidence is not None
        assert isinstance(prop.matching.diagnostic_reasons, list)


class TestSerializationAndNoSpacy:
    """21, 22. Serialization and purity of public representations."""

    def test_json_serialization(self, doc_correct_additional):
        """Verify to_json() produces fully valid JSON."""
        json_str = doc_correct_additional.to_json()
        assert isinstance(json_str, str)
        parsed = json.loads(json_str)
        assert isinstance(parsed, dict)
        assert parsed["total_student_propositions"] == 2
        assert len(parsed["propositions"]) == 2

    def test_no_raw_spacy_objects(self, doc_correct_additional):
        """Verify no raw spaCy or internal objects leak into the dictionary representation."""
        data_dict = doc_correct_additional.to_dict()

        def assert_plain_types(obj, path="root"):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    assert isinstance(k, str), f"Non-string key at {path}: {k}"
                    assert_plain_types(v, f"{path}.{k}")
            elif isinstance(obj, list):
                for idx, v in enumerate(obj):
                    assert_plain_types(v, f"{path}[{idx}]")
            else:
                assert isinstance(obj, (int, float, str, bool, type(None))), (
                    f"Unexpected complex object at {path}: {type(obj)} ({obj})"
                )

        assert_plain_types(data_dict)


class TestInvarianceAndRegression:
    """23, 24, 25. Score invariance, one-to-one matching, and Stage 11 parity."""

    def test_base_score_unchanged(self, pipeline, builder):
        """Verify Stage 12 preserves the Base ASAG score exactly across multiple cases."""
        cases = [
            (QUESTION_PK, REF_PK, "A primary key uniquely identifies each record in a table."),
            (QUESTION_PK, REF_PK, "A primary key uniquely identifies each record in a table and cannot contain NULL values."),
            (QUESTION_PK, REF_PK, "The sky is blue."),
            (QUESTION_COMPILER, REF_COMPILER, "A compiler converts high-level source code into machine code."),
        ]
        for q, ref, stu in cases:
            res = pipeline.grade(q, ref, stu)
            doc_repr = builder.build(res)
            assert doc_repr.base_asag_normalized_score == res.normalized_score

    def test_one_to_one_matching_unchanged(self, pipeline, builder):
        """Verify no duplicate reference assignments occur in matched representations."""
        res = pipeline.grade(
            question=QUESTION_COMPILER,
            reference_answer="A compiler translates source code.",
            student_answer="A compiler translates source code. A system translates source code.",
        )
        doc_repr = builder.build(res)
        assert doc_repr.matched_count == 1
        assert doc_repr.unmatched_count == 1
        ref_indices = [p.matching.reference_proposition_index for p in doc_repr.matched_propositions]
        assert len(ref_indices) == len(set(ref_indices))

    def test_stage11_alignment_regression(self, pipeline, builder, extractor):
        """Verify exact parity between Stage 11 alignment counts and Stage 12 representation."""
        res = pipeline.grade(
            question=QUESTION_PK,
            reference_answer=REF_PK,
            student_answer="A primary key uniquely identifies each record in a table and cannot contain NULL values.",
        )
        stage11_res = extractor.extract(res)
        stage12_res = builder.build(res, stage11_res)

        assert stage12_res.total_student_propositions == stage11_res.total_student_propositions
        assert stage12_res.matched_count == stage11_res.matched_count
        assert stage12_res.unmatched_count == stage11_res.unmatched_student_count
        assert stage12_res.base_asag_normalized_score == stage11_res.base_asag_normalized_score

    def test_get_proposition_lookup(self, doc_correct_additional):
        """Verify get_proposition retrieval by ID string and integer index."""
        p_by_id = doc_correct_additional.get_proposition("stu_prop_0")
        p_by_idx = doc_correct_additional.get_proposition(0)
        assert p_by_id is not None
        assert p_by_idx is not None
        assert p_by_id.proposition_id == p_by_idx.proposition_id

        assert doc_correct_additional.get_proposition("nonexistent") is None
        assert doc_correct_additional.get_proposition(999) is None
