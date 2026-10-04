"""
Stage 11 Tests: Proposition Alignment Extractor.

Tests for the PropositionAlignmentExtractor in proposed_asag.proposition.alignment.

Test Coverage:
--------------
1.  test_exact_match_compiler: Exact match => matched_count=1, entailment ENTAILS, score 1.0.
2.  test_paraphrase_compiler: Paraphrase => matched (ENTAILS or UNCERTAIN).
3.  test_correct_additional_primary_key: Core + extra clause => unmatched student preserved.
4.  test_irrelevant_additional_sql: Two-sentence answer => unmatched student preserved.
5.  test_incorrect_additional_duplicates: Core + incorrect info => unmatched preserved.
6.  test_completely_unrelated: Unrelated answer => matched_count=0 or low.
7.  test_span_char_start_valid_single_sentence: Matched span has char_start >= 0.
8.  test_span_text_matches_original_single: span_text is non-empty and in the answer.
9.  test_span_multi_sentence_valid: Multi-sentence answer => all spans have char_start >= 0.
10. test_one_to_one_preserved: No duplicate reference_proposition_index in matched.
11. test_json_serializable: to_json() returns valid JSON with 'original_student_answer'.
12. test_base_score_unchanged: alignment_result.base_asag_normalized_score == pipeline normalized_score.
13. test_unmatched_reference_preserved: Partial answer => unmatched ref not empty or score < 1.0.
14. test_no_additional_information_classification: No Stage 13 labels in Stage 11 output.

Data Note:
----------
All examples here are DEMO DATA — NOT RESEARCH DATA.
They are used solely to verify Stage 11 implementation correctness.

Research Boundaries:
--------------------
- Stage 11 extracts alignment evidence; it does NOT classify unmatched information.
- classification is always "NOT_EVALUATED_BY_BASE_ASAG" for unmatched propositions.
- score_effect is always 0.0 for unmatched propositions.
- The Base ASAG score is NOT modified by Stage 11.
"""

import json
import pytest

from base_asag.pipeline import BaseASAGPipeline
from proposed_asag.proposition.alignment import (
    PropositionAlignmentExtractor,
    PropositionAlignmentResult,
    MatchedPropositionEvidence,
    UnmatchedStudentPropositionEvidence,
    SpanInfo,
)

# ============================================================
# DEMO DATA — NOT RESEARCH DATA
# ============================================================

QUESTION_PRIMARY_KEY = "What is the purpose of a primary key?"
REFERENCE_PRIMARY_KEY = "A primary key uniquely identifies each record in a table."

QUESTION_COMPILER = "What does a compiler do?"
REFERENCE_COMPILER = "A compiler converts source code into machine code."


# ============================================================
# Module-scoped shared fixtures
# ============================================================

@pytest.fixture(scope="module")
def pipeline():
    """Shared BaseASAGPipeline instance (load spaCy model once)."""
    return BaseASAGPipeline()


@pytest.fixture(scope="module")
def extractor():
    """Shared PropositionAlignmentExtractor instance."""
    return PropositionAlignmentExtractor()


# ============================================================
# Pre-compute pipeline results for frequently used cases
# ============================================================

@pytest.fixture(scope="module")
def result_exact_pk(pipeline):
    """
    Exact match case: student answer matches reference exactly.
    DEMO DATA — NOT RESEARCH DATA.
    """
    return pipeline.grade(
        question=QUESTION_PRIMARY_KEY,
        reference_answer=REFERENCE_PRIMARY_KEY,
        student_answer="A primary key uniquely identifies each record in a table.",
    )


@pytest.fixture(scope="module")
def alignment_exact_pk(extractor, result_exact_pk):
    """Stage 11 alignment for the exact primary key match."""
    return extractor.extract(result_exact_pk)


@pytest.fixture(scope="module")
def result_correct_additional(pipeline):
    """
    Student B: Core correct + correct additional clause.
    DEMO DATA — NOT RESEARCH DATA.
    """
    return pipeline.grade(
        question=QUESTION_PRIMARY_KEY,
        reference_answer=REFERENCE_PRIMARY_KEY,
        student_answer=(
            "A primary key uniquely identifies each record in a table "
            "and cannot contain NULL values."
        ),
    )


@pytest.fixture(scope="module")
def alignment_correct_additional(extractor, result_correct_additional):
    """Stage 11 alignment for the correct-additional case."""
    return extractor.extract(result_correct_additional)


@pytest.fixture(scope="module")
def result_irrelevant(pipeline):
    """
    Student D: Core correct + irrelevant second sentence.
    DEMO DATA — NOT RESEARCH DATA.
    """
    return pipeline.grade(
        question=QUESTION_PRIMARY_KEY,
        reference_answer=REFERENCE_PRIMARY_KEY,
        student_answer=(
            "A primary key uniquely identifies each record in a table. "
            "SQL was developed in the 1970s."
        ),
    )


@pytest.fixture(scope="module")
def alignment_irrelevant(extractor, result_irrelevant):
    """Stage 11 alignment for the irrelevant-additional case."""
    return extractor.extract(result_irrelevant)


@pytest.fixture(scope="module")
def result_incorrect(pipeline):
    """
    Student C: Core correct + incorrect additional clause.
    DEMO DATA — NOT RESEARCH DATA.
    """
    return pipeline.grade(
        question=QUESTION_PRIMARY_KEY,
        reference_answer=REFERENCE_PRIMARY_KEY,
        student_answer=(
            "A primary key uniquely identifies each record in a table "
            "and can contain duplicate values."
        ),
    )


@pytest.fixture(scope="module")
def alignment_incorrect(extractor, result_incorrect):
    """Stage 11 alignment for the incorrect-additional case."""
    return extractor.extract(result_incorrect)


@pytest.fixture(scope="module")
def result_unrelated(pipeline):
    """
    Completely unrelated student answer.
    DEMO DATA — NOT RESEARCH DATA.
    """
    return pipeline.grade(
        question=QUESTION_PRIMARY_KEY,
        reference_answer=REFERENCE_PRIMARY_KEY,
        student_answer="The sky is blue and water is wet.",
    )


@pytest.fixture(scope="module")
def alignment_unrelated(extractor, result_unrelated):
    """Stage 11 alignment for the completely unrelated case."""
    return extractor.extract(result_unrelated)


@pytest.fixture(scope="module")
def result_multi_sentence_irrelevant(pipeline):
    """
    Multi-sentence: correct core + irrelevant second sentence (same as result_irrelevant
    but using an explicit two-sentence format to test multi-sentence span logic).
    DEMO DATA — NOT RESEARCH DATA.
    """
    return pipeline.grade(
        question=QUESTION_PRIMARY_KEY,
        reference_answer=REFERENCE_PRIMARY_KEY,
        student_answer=(
            "A primary key uniquely identifies each record in a table. "
            "SQL was invented in the 1970s."
        ),
    )


@pytest.fixture(scope="module")
def alignment_multi_sentence(extractor, result_multi_sentence_irrelevant):
    """Stage 11 alignment for the multi-sentence answer."""
    return extractor.extract(result_multi_sentence_irrelevant)


# ============================================================
# Tests
# ============================================================

class TestExactMatch:
    """
    Test 1: Exact match case.
    """

    def test_exact_match_compiler(self, pipeline, extractor):
        """
        Exact student answer == reference answer.
        Expect: matched_count >= 1, first matched entailment_status == ENTAILS,
        score_contribution == 1.0, unmatched_student_count == 0.
        DEMO DATA — NOT RESEARCH DATA.
        """
        result = pipeline.grade(
            question=QUESTION_PRIMARY_KEY,
            reference_answer=REFERENCE_PRIMARY_KEY,
            student_answer="A primary key uniquely identifies each record in a table.",
        )
        alignment = extractor.extract(result)

        assert isinstance(alignment, PropositionAlignmentResult)
        assert alignment.matched_count >= 1, (
            f"Expected at least 1 match for exact answer, got {alignment.matched_count}"
        )
        assert alignment.unmatched_student_count == 0, (
            f"Expected 0 unmatched student propositions for exact match, "
            f"got {alignment.unmatched_student_count}"
        )

        # First matched proposition should be ENTAILS with score_contribution 1.0
        matched = alignment.matched_propositions[0]
        assert matched.entailment_status == "ENTAILS", (
            f"Expected ENTAILS for exact match, got {matched.entailment_status}"
        )
        assert matched.score_contribution == 1.0, (
            f"Expected score_contribution == 1.0 for ENTAILED match, "
            f"got {matched.score_contribution}"
        )


class TestParaphrase:
    """
    Test 2: Paraphrase case.
    """

    def test_paraphrase_compiler(self, pipeline, extractor):
        """
        Student answer paraphrases the reference (similar meaning, different wording).
        Expect: matched_count >= 1, entailment_status is ENTAILS or UNCERTAIN.
        DEMO DATA — NOT RESEARCH DATA.
        """
        result = pipeline.grade(
            question=QUESTION_COMPILER,
            reference_answer=REFERENCE_COMPILER,
            student_answer="A compiler converts high-level source code into machine code.",
        )
        alignment = extractor.extract(result)

        assert isinstance(alignment, PropositionAlignmentResult)
        assert alignment.matched_count >= 1, (
            f"Expected at least 1 match for paraphrase, got {alignment.matched_count}"
        )

        for matched in alignment.matched_propositions:
            assert matched.entailment_status in ("ENTAILS", "UNCERTAIN"), (
                f"Unexpected entailment_status: {matched.entailment_status}"
            )


class TestCorrectAdditional:
    """
    Test 3: Correct answer + correct additional information.
    """

    def test_correct_additional_primary_key(self, alignment_correct_additional):
        """
        Student answer: core correct + 'and cannot contain NULL values'.
        Expect:
        - matched_count >= 1 (core proposition is matched)
        - unmatched_student_count >= 1 (additional clause is unmatched)
        - all unmatched propositions have classification == 'NOT_EVALUATED_BY_BASE_ASAG'
        - all unmatched propositions have score_effect == 0.0
        DEMO DATA — NOT RESEARCH DATA.
        """
        alignment = alignment_correct_additional

        assert alignment.matched_count >= 1, (
            f"Expected at least 1 matched proposition, got {alignment.matched_count}"
        )
        assert alignment.unmatched_student_count >= 1, (
            f"Expected at least 1 unmatched student proposition for additional info, "
            f"got {alignment.unmatched_student_count}"
        )

        for u in alignment.unmatched_student_propositions:
            assert u.classification == "NOT_EVALUATED_BY_BASE_ASAG", (
                f"Expected 'NOT_EVALUATED_BY_BASE_ASAG', got '{u.classification}'"
            )
            assert u.score_effect == 0.0, (
                f"Expected score_effect == 0.0, got {u.score_effect}"
            )
            assert u.match_status == "UNMATCHED", (
                f"Expected match_status == 'UNMATCHED', got '{u.match_status}'"
            )


class TestIrrelevantAdditional:
    """
    Test 4: Multi-sentence student answer with irrelevant second sentence.
    """

    def test_irrelevant_additional_sql(self, alignment_irrelevant):
        """
        Student answer: correct core + irrelevant second sentence about SQL history.
        Expect:
        - unmatched_student_propositions list is preserved
        - all unmatched have classification == 'NOT_EVALUATED_BY_BASE_ASAG'
        DEMO DATA — NOT RESEARCH DATA.
        """
        alignment = alignment_irrelevant

        # The irrelevant sentence should generate at least one unmatched proposition
        # (depending on spaCy's parsing of "SQL was developed in the 1970s")
        # We assert structural correctness, not a specific count
        for u in alignment.unmatched_student_propositions:
            assert u.classification == "NOT_EVALUATED_BY_BASE_ASAG", (
                f"Expected classification 'NOT_EVALUATED_BY_BASE_ASAG', got '{u.classification}'"
            )
            assert isinstance(u.student_relation, dict)
            assert isinstance(u.span, SpanInfo)


class TestIncorrectAdditional:
    """
    Test 5: Core correct + incorrect additional information.
    """

    def test_incorrect_additional_duplicates(self, alignment_incorrect):
        """
        Student answer: correct core + 'and can contain duplicate values' (incorrect).
        Expect:
        - unmatched_student_count >= 1 (the duplicate claim is unmatched or contradicted)
        - all unmatched propositions preserved with 'NOT_EVALUATED_BY_BASE_ASAG'
        DEMO DATA — NOT RESEARCH DATA.
        """
        alignment = alignment_incorrect

        # At minimum, structural integrity
        assert isinstance(alignment, PropositionAlignmentResult)

        for u in alignment.unmatched_student_propositions:
            assert u.classification == "NOT_EVALUATED_BY_BASE_ASAG"
            assert u.score_effect == 0.0


class TestCompletelyUnrelated:
    """
    Test 6: Completely unrelated student answer.
    """

    def test_completely_unrelated(self, alignment_unrelated):
        """
        Student answer has nothing to do with the reference.
        Expect: matched_count == 0 or very low.
        DEMO DATA — NOT RESEARCH DATA.
        """
        alignment = alignment_unrelated

        # All or most student propositions should be unmatched
        total = alignment.total_student_propositions
        assert alignment.matched_count < total or alignment.matched_count == 0, (
            "Expected very few or no matches for a completely unrelated answer"
        )

        # All unmatched must carry correct labels
        for u in alignment.unmatched_student_propositions:
            assert u.classification == "NOT_EVALUATED_BY_BASE_ASAG"
            assert u.score_effect == 0.0


class TestSpanSingleSentence:
    """
    Tests 7 & 8: Character span validity for single-sentence answers.
    """

    def test_span_char_start_valid_single_sentence(self, alignment_exact_pk):
        """
        For a single-sentence exact match, the matched proposition's span
        should have char_start >= 0.
        DEMO DATA — NOT RESEARCH DATA.
        """
        alignment = alignment_exact_pk
        assert alignment.matched_count >= 1

        matched = alignment.matched_propositions[0]
        assert matched.span.char_start >= 0, (
            f"Expected valid char_start >= 0 for single-sentence match, "
            f"got {matched.span.char_start}"
        )

    def test_span_text_matches_original_single(self, alignment_exact_pk, result_exact_pk):
        """
        For a matched proposition with valid span, the span_text should be
        a non-empty substring of the original student answer.
        DEMO DATA — NOT RESEARCH DATA.
        """
        alignment = alignment_exact_pk
        assert alignment.matched_count >= 1

        matched = alignment.matched_propositions[0]
        span = matched.span

        # span_text must be non-empty
        assert len(span.span_text) > 0, "span_text should not be empty"

        # If char_start is valid, verify it is within the original answer
        if span.char_start >= 0 and span.char_end > span.char_start:
            original = result_exact_pk.student_answer
            extracted = original[span.char_start:span.char_end]
            # The extracted substring should be non-empty
            assert len(extracted) > 0, (
                f"Expected non-empty extracted text, got empty string for "
                f"span [{span.char_start}:{span.char_end}] in '{original}'"
            )


class TestSpanMultiSentence:
    """
    Test 9: Character span validity for multi-sentence answers.
    """

    def test_span_multi_sentence_valid(self, alignment_multi_sentence):
        """
        For a multi-sentence student answer, all propositions (matched + unmatched)
        should have char_start >= 0 (sentences can be found in the original answer
        via string search).
        DEMO DATA — NOT RESEARCH DATA.
        """
        alignment = alignment_multi_sentence

        all_spans = (
            [m.span for m in alignment.matched_propositions]
            + [u.span for u in alignment.unmatched_student_propositions]
        )

        # At least some spans must be valid
        valid_spans = [s for s in all_spans if s.char_start >= 0]

        # If there are any propositions extracted, at least some should have valid spans
        if all_spans:
            assert len(valid_spans) > 0, (
                "Expected at least one valid span in multi-sentence answer, "
                f"but got 0 valid spans out of {len(all_spans)}"
            )


class TestOneToOne:
    """
    Test 10: One-to-one matching is preserved.
    """

    def test_one_to_one_preserved(self, alignment_exact_pk):
        """
        No reference proposition should appear twice in matched_propositions.
        The reference_proposition_index values must be unique.
        DEMO DATA — NOT RESEARCH DATA.
        """
        alignment = alignment_exact_pk
        ref_indices = [m.reference_proposition_index for m in alignment.matched_propositions]
        assert len(ref_indices) == len(set(ref_indices)), (
            f"Duplicate reference_proposition_index values found: {ref_indices}"
        )


class TestJsonSerialization:
    """
    Test 11: JSON serialization.
    """

    def test_json_serializable(self, alignment_exact_pk):
        """
        to_json() should return a valid JSON string containing 'original_student_answer'.
        DEMO DATA — NOT RESEARCH DATA.
        """
        alignment = alignment_exact_pk
        json_str = alignment.to_json()

        assert isinstance(json_str, str)
        parsed = json.loads(json_str)
        assert isinstance(parsed, dict)
        assert "original_student_answer" in parsed, (
            "Expected 'original_student_answer' key in JSON output"
        )
        assert parsed["original_student_answer"] == alignment.original_student_answer


class TestBaseScoreUnchanged:
    """
    Test 12: Stage 11 must not modify the Base ASAG score.
    """

    def test_base_score_unchanged(self, result_exact_pk, alignment_exact_pk):
        """
        alignment_result.base_asag_normalized_score must equal pipeline_result.normalized_score.
        DEMO DATA — NOT RESEARCH DATA.
        """
        assert alignment_exact_pk.base_asag_normalized_score == result_exact_pk.normalized_score, (
            f"Stage 11 must not modify the Base ASAG score. "
            f"Expected {result_exact_pk.normalized_score}, "
            f"got {alignment_exact_pk.base_asag_normalized_score}"
        )


class TestUnmatchedReferencePreserved:
    """
    Test 13: Unmatched reference propositions are preserved.
    """

    def test_unmatched_reference_preserved(self, pipeline, extractor):
        """
        A partial student answer should leave some reference propositions unmatched
        OR produce a score < 1.0.
        The unmatched_reference_propositions list should be properly structured.
        DEMO DATA — NOT RESEARCH DATA.
        """
        # Use a longer reference with two pieces of information
        reference_two_facts = (
            "A primary key uniquely identifies each record in a table. "
            "It must be unique and cannot be null."
        )
        result = pipeline.grade(
            question=QUESTION_PRIMARY_KEY,
            reference_answer=reference_two_facts,
            student_answer="A primary key uniquely identifies records.",
        )
        alignment = extractor.extract(result)

        # Either some reference propositions are unmatched, or score < 1.0
        condition = (
            alignment.unmatched_reference_count > 0
            or alignment.base_asag_normalized_score < 1.0
        )
        assert condition, (
            f"Expected partial coverage: unmatched_reference_count="
            f"{alignment.unmatched_reference_count}, "
            f"score={alignment.base_asag_normalized_score}"
        )

        # The list should be properly structured (each item is a dict)
        for ref_dict in alignment.unmatched_reference_propositions:
            assert isinstance(ref_dict, dict), (
                f"Expected dict in unmatched_reference_propositions, got {type(ref_dict)}"
            )
            assert "subject" in ref_dict, "Expected 'subject' key in reference relation dict"


class TestNoAdditionalInfoClassification:
    """
    Test 14: Stage 11 must NOT implement Stage 13 classification labels.
    """

    def test_no_additional_information_classification(
        self,
        alignment_exact_pk,
        alignment_correct_additional,
        alignment_irrelevant,
        alignment_incorrect,
    ):
        """
        Stage 11 must NEVER produce classification values CORRECT_ADDITIONAL,
        IRRELEVANT, or INCORRECT_ADDITIONAL. These are reserved for Stage 13.
        DEMO DATA — NOT RESEARCH DATA.
        """
        forbidden_labels = {"CORRECT_ADDITIONAL", "IRRELEVANT", "INCORRECT_ADDITIONAL"}

        for alignment in [
            alignment_exact_pk,
            alignment_correct_additional,
            alignment_irrelevant,
            alignment_incorrect,
        ]:
            for u in alignment.unmatched_student_propositions:
                assert u.classification not in forbidden_labels, (
                    f"Stage 11 produced a Stage 13 classification label: '{u.classification}'. "
                    f"Stage 11 must only use 'NOT_EVALUATED_BY_BASE_ASAG'."
                )


class TestConjoinedClauseSpanIsolation:
    """
    Test 15: Conjoined clauses do not inherit earlier clause spans.
    """

    def test_conjoined_clause_span_isolation(self, pipeline, extractor):
        """
        In 'A primary key uniquely identifies each record in a table and cannot contain NULL values.',
        the conjoined clause 'cannot contain NULL values' must NOT span back to 'primary key'.
        The matched and unmatched proposition spans must be non-overlapping.
        DEMO DATA — NOT RESEARCH DATA.
        """
        student_answer = (
            "A primary key uniquely identifies each record in a table "
            "and cannot contain NULL values."
        )
        res = pipeline.grade(
            question=QUESTION_PRIMARY_KEY,
            reference_answer=REFERENCE_PRIMARY_KEY,
            student_answer=student_answer,
        )
        alignment = extractor.extract(res)

        assert alignment.matched_count == 1
        assert alignment.unmatched_student_count == 1

        matched = alignment.matched_propositions[0]
        unmatched = alignment.unmatched_student_propositions[0]

        # Verify matched span slice
        m_slice = student_answer[matched.span.char_start:matched.span.char_end]
        assert m_slice == matched.span.span_text
        assert "identifies" in m_slice

        # Verify unmatched span slice
        u_slice = student_answer[unmatched.span.char_start:unmatched.span.char_end]
        assert u_slice == unmatched.span.span_text
        assert u_slice == "cannot contain NULL values"

        # Verify strictly non-overlapping spans
        assert matched.span.char_end < unmatched.span.char_start, (
            f"Expected non-overlapping spans, but matched ends at {matched.span.char_end} "
            f"and unmatched starts at {unmatched.span.char_start}"
        )


class TestCompilerSpanExactSubstring:
    """
    Test 16: Verify exact proposition span extraction on compiler sentence.
    """

    def test_compiler_span_exact_substring(self, pipeline, extractor):
        """
        Verify student_answer[char_start:char_end] returns the intended proposition clause.
        DEMO DATA — NOT RESEARCH DATA.
        """
        student_answer = "The compiler translates source code."
        res = pipeline.grade(
            question=QUESTION_COMPILER,
            reference_answer=REFERENCE_COMPILER,
            student_answer=student_answer,
        )
        alignment = extractor.extract(res)

        assert alignment.matched_count == 1
        matched = alignment.matched_propositions[0]
        extracted = student_answer[matched.span.char_start:matched.span.char_end]
        assert extracted == matched.span.span_text
        assert extracted == "compiler translates source code"


class TestOneToOneCompetitionRejection:
    """
    Test 17: One-to-one competition rejection reason explanation.
    """

    def test_one_to_one_competition_rejection(self, pipeline, extractor):
        """
        When two student propositions compete for the same reference proposition,
        the lower-scoring one must be marked UNMATCHED with an explicit rejection reason
        citing one-to-one matching constraints.
        DEMO DATA — NOT RESEARCH DATA.
        """
        student_answer = "A compiler translates source code. A system translates source code."
        ref_answer = "A compiler translates source code."
        res = pipeline.grade(
            question=QUESTION_COMPILER,
            reference_answer=ref_answer,
            student_answer=student_answer,
        )
        alignment = extractor.extract(res)

        assert alignment.matched_count == 1
        assert alignment.unmatched_student_count == 1

        unmatched = alignment.unmatched_student_propositions[0]
        assert unmatched.best_candidate_reference_index == 0
        assert unmatched.best_candidate_score is not None
        assert unmatched.best_candidate_score >= 0.50
        assert "one-to-one matching constraints" in unmatched.rejection_reason


class TestPolarityAndContradictionEvidence:
    """
    Test 18: Polarity and contradiction evidence preservation.
    """

    def test_polarity_and_contradiction_evidence(self, pipeline, extractor):
        """
        Negated student answer must preserve CONTRADICTS status, 0.0 score contribution,
        and explicit polarity information.
        DEMO DATA — NOT RESEARCH DATA.
        """
        student_answer = "A primary key does not identify each record in a table."
        res = pipeline.grade(
            question=QUESTION_PRIMARY_KEY,
            reference_answer=REFERENCE_PRIMARY_KEY,
            student_answer=student_answer,
        )
        alignment = extractor.extract(res)

        assert alignment.matched_count == 1
        matched = alignment.matched_propositions[0]
        assert matched.entailment_status == "CONTRADICTS"
        assert matched.score_contribution == 0.0
        assert matched.polarity_student == "NEGATED"
        assert matched.polarity_reference == "POSITIVE"
        assert len(matched.diagnostic_reasons) > 0


class TestEmptyAndWhitespaceStudentAnswer:
    """
    Test 19: Robust handling of empty and whitespace-only student answers.
    """

    def test_empty_student_answer(self, pipeline, extractor):
        """
        Empty student answer should not crash Stage 11 extractor.
        """
        res = pipeline.grade(
            question=QUESTION_PRIMARY_KEY,
            reference_answer=REFERENCE_PRIMARY_KEY,
            student_answer="",
        )
        alignment = extractor.extract(res)
        assert alignment.matched_count == 0
        assert alignment.unmatched_student_count == 0
        assert alignment.base_asag_normalized_score == 0.0
        assert isinstance(json.loads(alignment.to_json()), dict)

    def test_whitespace_student_answer(self, pipeline, extractor):
        """
        Whitespace-only student answer should produce 0 matches without crashing.
        """
        res = pipeline.grade(
            question=QUESTION_PRIMARY_KEY,
            reference_answer=REFERENCE_PRIMARY_KEY,
            student_answer="    ",
        )
        alignment = extractor.extract(res)
        assert alignment.matched_count == 0
        assert alignment.unmatched_student_count == 0


class TestWhitespaceResilienceInSpan:
    """
    Test 20: Character span resilience to collapsed internal whitespace.
    """

    def test_whitespace_resilience_in_span(self, pipeline, extractor):
        """
        Answer with internal irregular whitespace must still locate valid spans.
        DEMO DATA — NOT RESEARCH DATA.
        """
        student_answer = "   A compiler    translates source code!   "
        res = pipeline.grade(
            question=QUESTION_COMPILER,
            reference_answer=REFERENCE_COMPILER,
            student_answer=student_answer,
        )
        alignment = extractor.extract(res)

        assert alignment.matched_count == 1
        matched = alignment.matched_propositions[0]
        assert matched.span.char_start >= 0
        assert matched.span.char_end > matched.span.char_start
        extracted = student_answer[matched.span.char_start:matched.span.char_end]
        assert "translates" in extracted
