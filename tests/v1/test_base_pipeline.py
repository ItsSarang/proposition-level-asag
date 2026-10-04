"""
Tests for Stage 10 Base ASAG Integrated Pipeline.

Verifies:
1. Single end-to-end call pipeline.grade(...) executes stages 3-9 in order on raw strings.
2. Identical student answer yields normalized_score = 1.0, 0 missing, all entailed.
3. Partial answer yields intermediate coverage score.
4. Unrelated student answer yields normalized_score = 0.0, all reference relations missing.
5. Contradicted student answer yields 0.0 for the contradicted proposition.
6. Correct answer + extra information (Student B, C, D) preserves unmatched student relations
   without affecting the Base ASAG score.
7. Score bounds strictly within [0.0, 1.0].
8. Scaling utility (scale_score) works accurately for 5.0, 10.0, 100.0 scales.
9. Letter grade mapping utility (map_to_letter_grade) works accurately.
10. Full serialization via to_dict() with all intermediate diagnostic artifacts preserved.
11. Input validation: TypeError on non-string inputs, ValueError on empty reference answer.
12. Graceful handling of empty or whitespace-only student answer (normalized_score = 0.0).
13. Differential reference proposition weights (reference_weights).
14. Pipeline dependency injection (custom preprocessor, parser, matcher, analyzer, scorer).
15. Result immutability (frozen dataclass).
16. Question parsing: question is parsed into ParsedDocument without modifying scoring.
17. No premature Stage 11-14 classification (unmatched relations are unclassified).
"""

import pytest
from dataclasses import FrozenInstanceError

from base_asag.pipeline import BaseASAGPipeline, BaseASAGPipelineResult
from base_asag.dependency.parser import DependencyParser, ParsedDocument
from base_asag.dependency.triples import DependencyTripleExtractor
from base_asag.matching.triple_matcher import TripleMatcher
from base_asag.entailment.analyzer import PropositionalEntailmentAnalyzer
from base_asag.scoring.base_scorer import BaseASAGScorer


@pytest.fixture(scope="module")
def pipeline():
    return BaseASAGPipeline()


# ---------------------------------------------------------------------------
# 1. Single End-to-End Execution
# ---------------------------------------------------------------------------

def test_pipeline_grade_returns_pipeline_result(pipeline):
    """Test that pipeline.grade executes end-to-end and returns a BaseASAGPipelineResult."""
    q = "What is the purpose of a primary key?"
    ref = "A primary key uniquely identifies each record in a table."
    stu = "A primary key uniquely identifies each record in a table."

    result = pipeline.grade(q, ref, stu)

    assert isinstance(result, BaseASAGPipelineResult)
    assert result.question == q
    assert result.reference_answer == ref
    assert result.student_answer == stu
    assert isinstance(result.reference_parsed, ParsedDocument)
    assert isinstance(result.student_parsed, ParsedDocument)
    assert isinstance(result.question_parsed, ParsedDocument)
    assert result.reference_triples is not None
    assert result.student_triples is not None
    assert result.matching_result is not None
    assert len(result.entailment_results) > 0
    assert result.scoring_result is not None


# ---------------------------------------------------------------------------
# 2. Identical Answer Scoring
# ---------------------------------------------------------------------------

def test_pipeline_identical_answer(pipeline):
    """Identical answer should entail all reference propositions with normalized_score = 1.0."""
    q = "What is the purpose of a primary key?"
    ref = "A primary key uniquely identifies each record in a table."
    stu = "A primary key uniquely identifies each record in a table."

    result = pipeline.grade(q, ref, stu)

    assert result.normalized_score == 1.0
    assert result.entailed_count == result.total_reference_propositions
    assert result.missing_count == 0
    assert result.contradicted_count == 0
    assert len(result.unmatched_reference_relations) == 0


# ---------------------------------------------------------------------------
# 3. Partial Coverage Answer Scoring
# ---------------------------------------------------------------------------

def test_pipeline_partial_answer(pipeline):
    """Partial answer addressing only some propositions yields an intermediate score."""
    q = "What is a primary key and when was SQL developed?"
    ref = "A primary key uniquely identifies each record in a table. SQL was developed in the 1970s."
    stu = "A primary key uniquely identifies each record in a table."

    result = pipeline.grade(q, ref, stu)

    assert result.normalized_score == 0.5
    assert result.entailed_count == 1
    assert result.missing_count == 1
    assert len(result.unmatched_reference_relations) == 1


# ---------------------------------------------------------------------------
# 4. Unrelated Student Answer Scoring
# ---------------------------------------------------------------------------

def test_pipeline_unrelated_answer(pipeline):
    """Completely unrelated answer should receive normalized_score = 0.0."""
    q = "What is the purpose of a primary key?"
    ref = "A primary key uniquely identifies each record in a table."
    stu = "Photosynthesis requires sunlight and water."

    result = pipeline.grade(q, ref, stu)

    assert result.normalized_score == 0.0
    assert result.entailed_count == 0
    assert result.missing_count == result.total_reference_propositions
    assert len(result.matched_relations) == 0


# ---------------------------------------------------------------------------
# 5. Contradicted Student Answer Scoring
# ---------------------------------------------------------------------------

def test_pipeline_contradicted_answer(pipeline):
    """Negated/contradicted student answer should be penalized (0.0 for that proposition)."""
    q = "What is the purpose of a primary key?"
    ref = "A primary key uniquely identifies each record in a table."
    stu = "A primary key never identifies each record in a table."

    result = pipeline.grade(q, ref, stu)

    assert result.contradicted_count >= 1
    assert result.normalized_score == 0.0


# ---------------------------------------------------------------------------
# 6. Extra Student Information Preservation & Neutrality (Students B, C, D)
# ---------------------------------------------------------------------------

def test_pipeline_extra_student_information_neutrality(pipeline):
    """
    In Base ASAG, unmatched student relations must be preserved in diagnostics
    with ZERO score modification (neither bonus nor penalty).
    """
    q = "What is the purpose of a primary key?"
    ref = "A primary key uniquely identifies each record in a table."

    # Identical base answer
    stu_base = "A primary key uniquely identifies each record in a table."
    # Student B: Correct extra info
    stu_b = "A primary key uniquely identifies each record in a table and cannot contain NULL values."
    # Student C: Incorrect extra info
    stu_c = "A primary key uniquely identifies each record in a table and can contain duplicate values."
    # Student D: Irrelevant extra info
    stu_d = "A primary key uniquely identifies each record in a table. SQL was developed in the 1970s."

    res_base = pipeline.grade(q, ref, stu_base)
    res_b = pipeline.grade(q, ref, stu_b)
    res_c = pipeline.grade(q, ref, stu_c)
    res_d = pipeline.grade(q, ref, stu_d)

    # Base score must be identical for all (1.0) because the reference proposition is entailed
    assert res_base.normalized_score == 1.0
    assert res_b.normalized_score == 1.0
    assert res_c.normalized_score == 1.0
    assert res_d.normalized_score == 1.0

    # Extra information must appear in unmatched_student_relations
    assert len(res_base.unmatched_student_relations) == 0
    assert len(res_b.unmatched_student_relations) > 0
    assert len(res_c.unmatched_student_relations) > 0
    assert len(res_d.unmatched_student_relations) > 0

    assert res_b.unmatched_student_count > 0
    assert res_c.unmatched_student_count > 0
    assert res_d.unmatched_student_count > 0


# ---------------------------------------------------------------------------
# 7. Score Bounds
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "stu",
    [
        "A primary key uniquely identifies each record in a table.",
        "A primary key uniquely identifies each record.",
        "A primary key never identifies each record.",
        "Completely irrelevant statement about biology.",
        "",
        "Table record identify key primary.",
    ],
)
def test_pipeline_score_bounds(pipeline, stu):
    """Normalized score must be strictly within [0.0, 1.0] across all scenarios."""
    q = "What is the purpose of a primary key?"
    ref = "A primary key uniquely identifies each record in a table."

    result = pipeline.grade(q, ref, stu)
    assert 0.0 <= result.normalized_score <= 1.0


# ---------------------------------------------------------------------------
# 8. Score Scaling Utility
# ---------------------------------------------------------------------------

def test_pipeline_scale_score(pipeline):
    """Test score scaling to custom point scales."""
    q = "What is the purpose of a primary key?"
    ref = "A primary key uniquely identifies each record in a table."
    stu = "A primary key uniquely identifies each record in a table."

    result = pipeline.grade(q, ref, stu)
    assert result.scale_score(5.0) == 5.0
    assert result.scale_score(10.0) == 10.0
    assert result.scale_score(100.0) == 100.0

    # Partial score scaling
    q_p = "What is photosynthesis and where does it occur?"
    ref_p = "Plants convert sunlight into energy. Chloroplasts store chlorophyll."
    stu_p = "Plants convert sunlight into energy."
    result_p = pipeline.grade(q_p, ref_p, stu_p)
    assert result_p.scale_score(10.0) == round(result_p.normalized_score * 10.0, 4)


# ---------------------------------------------------------------------------
# 9. Letter Grade Mapping Utility
# ---------------------------------------------------------------------------

def test_pipeline_map_to_letter_grade(pipeline):
    """Test mapping score to traditional letter grades."""
    q = "What is the purpose of a primary key?"
    ref = "A primary key uniquely identifies each record in a table."

    res_perfect = pipeline.grade(q, ref, "A primary key uniquely identifies each record in a table.")
    assert res_perfect.map_to_letter_grade() == "A"

    res_zero = pipeline.grade(q, ref, "Unrelated answer.")
    assert res_zero.map_to_letter_grade() == "F"


# ---------------------------------------------------------------------------
# 10. Full Serialization via to_dict()
# ---------------------------------------------------------------------------

def test_pipeline_to_dict_structure(pipeline):
    """Verify that to_dict includes all input, intermediate, and scoring keys."""
    q = "What is the purpose of a primary key?"
    ref = "A primary key uniquely identifies each record in a table."
    stu = "A primary key uniquely identifies each record in a table and cannot contain NULL values."

    result = pipeline.grade(q, ref, stu)
    data = result.to_dict()

    assert data["question"] == q
    assert data["reference_answer"] == ref
    assert data["student_answer"] == stu
    assert data["normalized_score"] == 1.0
    assert "total_reference_propositions" in data
    assert "entailed_count" in data
    assert "uncertain_count" in data
    assert "contradicted_count" in data
    assert "missing_count" in data
    assert "unmatched_student_count" in data
    assert "scoring_result" in data
    assert "matching_result" in data
    assert "entailment_results" in data
    assert "unmatched_reference_relations" in data
    assert "unmatched_student_relations" in data
    assert len(data["unmatched_student_relations"]) > 0


# ---------------------------------------------------------------------------
# 11. Input Validation and Error Handling
# ---------------------------------------------------------------------------

def test_pipeline_invalid_types(pipeline):
    """TypeError should be raised for non-string inputs."""
    with pytest.raises(TypeError, match="question must be a string"):
        pipeline.grade(123, "Ref", "Stu")  # type: ignore

    with pytest.raises(TypeError, match="reference_answer must be a string"):
        pipeline.grade("Q", None, "Stu")  # type: ignore

    with pytest.raises(TypeError, match="student_answer must be a string"):
        pipeline.grade("Q", "Ref", ["Stu"])  # type: ignore


def test_pipeline_empty_reference_answer(pipeline):
    """ValueError should be raised for empty or whitespace-only reference answer."""
    with pytest.raises(ValueError, match="reference_answer cannot be empty"):
        pipeline.grade("What is a primary key?", "", "A primary key.")

    with pytest.raises(ValueError, match="reference_answer cannot be empty"):
        pipeline.grade("What is a primary key?", "   \n\t ", "A primary key.")


def test_pipeline_empty_student_answer(pipeline):
    """Empty student answer should return normalized_score = 0.0 gracefully."""
    q = "What is the purpose of a primary key?"
    ref = "A primary key uniquely identifies each record in a table."

    result_empty = pipeline.grade(q, ref, "")
    assert result_empty.normalized_score == 0.0
    assert result_empty.missing_count == result_empty.total_reference_propositions
    assert result_empty.entailed_count == 0

    result_whitespace = pipeline.grade(q, ref, "   \t\n ")
    assert result_whitespace.normalized_score == 0.0
    assert result_whitespace.missing_count == result_whitespace.total_reference_propositions


# ---------------------------------------------------------------------------
# 12. Question Parsing & Handling
# ---------------------------------------------------------------------------

def test_pipeline_question_handling(pipeline):
    """Question prompt is preprocessed and parsed, preserving ASAG input schema."""
    q = "What is the purpose of a primary key?"
    ref = "A primary key uniquely identifies each record in a table."
    stu = "A primary key uniquely identifies each record in a table."

    result = pipeline.grade(q, ref, stu)
    assert result.question_parsed is not None
    assert result.question_parsed.original_text == q

    # Empty question prompt should also be handled without error
    result_no_q = pipeline.grade("", ref, stu)
    assert result_no_q.question_parsed is None
    assert result_no_q.normalized_score == 1.0


# ---------------------------------------------------------------------------
# 13. Reference Proposition Weights
# ---------------------------------------------------------------------------

def test_pipeline_reference_weights(pipeline):
    """Custom importance weights should be applied across reference propositions."""
    q = "What is a primary key and when was SQL developed?"
    ref = "A primary key uniquely identifies each record in a table. SQL was developed in the 1970s."
    stu = "A primary key uniquely identifies each record in a table."

    # Give 80% weight to proposition 1, 20% to proposition 2
    res_weighted = pipeline.grade(q, ref, stu, reference_weights=[0.8, 0.2])
    res_unweighted = pipeline.grade(q, ref, stu)

    assert res_weighted.normalized_score == 0.8
    assert res_unweighted.normalized_score == 0.5


# ---------------------------------------------------------------------------
# 14. Component Dependency Injection
# ---------------------------------------------------------------------------

def test_pipeline_dependency_injection():
    """Custom component instances and thresholds can be injected into BaseASAGPipeline."""
    custom_parser = DependencyParser(model_name="en_core_web_sm")
    custom_extractor = DependencyTripleExtractor()
    custom_matcher = TripleMatcher(alignment_threshold=0.60)
    custom_analyzer = PropositionalEntailmentAnalyzer(entailment_threshold=0.75)
    custom_scorer = BaseASAGScorer(uncertain_weight=0.40)

    custom_pipeline = BaseASAGPipeline(
        parser=custom_parser,
        extractor=custom_extractor,
        matcher=custom_matcher,
        analyzer=custom_analyzer,
        scorer=custom_scorer,
    )

    assert custom_pipeline.matcher.alignment_threshold == 0.60
    assert custom_pipeline.analyzer.entailment_threshold == 0.75
    assert custom_pipeline.scorer.uncertain_weight == 0.40

    res = custom_pipeline.grade(
        "What is a key?",
        "A primary key uniquely identifies each record in a table.",
        "A primary key uniquely identifies each record in a table.",
    )
    assert res.normalized_score == 1.0


# ---------------------------------------------------------------------------
# 15. Immutability
# ---------------------------------------------------------------------------

def test_pipeline_result_immutability(pipeline):
    """BaseASAGPipelineResult is frozen and cannot be modified after construction."""
    res = pipeline.grade(
        "Question",
        "A primary key uniquely identifies each record in a table.",
        "A primary key uniquely identifies each record in a table.",
    )

    with pytest.raises(FrozenInstanceError):
        res.normalized_score = 0.5  # type: ignore


# ---------------------------------------------------------------------------
# 16. Research Boundary: No Premature Classification
# ---------------------------------------------------------------------------

def test_pipeline_no_premature_classification(pipeline):
    """
    Verify that unmatched student relations are NOT classified with Stage 13 labels
    (e.g., 'correct_additional', 'irrelevant', 'incorrect').
    """
    q = "What is the purpose of a primary key?"
    ref = "A primary key uniquely identifies each record in a table."
    stu = "A primary key uniquely identifies each record in a table and cannot contain NULL values."

    result = pipeline.grade(q, ref, stu)

    assert len(result.unmatched_student_relations) > 0
    # In Base ASAG, unmatched relations remain raw DependencyRelation objects
    for rel in result.unmatched_student_relations:
        assert not hasattr(rel, "classification")
        assert not hasattr(rel, "is_correct_additional")
        assert not hasattr(rel, "is_incorrect")
