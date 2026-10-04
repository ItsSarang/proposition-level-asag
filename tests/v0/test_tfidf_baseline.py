"""
Unit tests for the TF-IDF + Cosine Similarity Baseline.

Covers:
1. Identical answers produce similarity ~ 1.0
2. Clearly unrelated answers produce much lower similarity than identical answers
3. Similar answers produce higher similarity than unrelated answers
4. Empty or invalid inputs are handled explicitly and predictably
5. Output score bounds [0.0, 1.0]
"""

import pytest
from baseline.tfidf_cosine.baseline import (
    TfidfCosineBaseline,
    compute_tfidf_cosine_similarity,
)


@pytest.fixture
def baseline():
    """Provides a default TfidfCosineBaseline instance."""
    return TfidfCosineBaseline()


def test_identical_answers(baseline):
    """Identical answers should produce a similarity of approximately 1.0."""
    ref = "A primary key uniquely identifies each record in a table."
    student = "A primary key uniquely identifies each record in a table."

    sim = baseline.similarity(ref, student)
    assert pytest.approx(1.0, rel=1e-4) == sim


def test_case_insensitivity(baseline):
    """Identical answers with differing casing should yield ~1.0 under default lowercase=True."""
    ref = "A Primary Key Uniquely Identifies Each Record In A Table."
    student = "a primary key uniquely identifies each record in a table."

    sim = baseline.similarity(ref, student)
    assert pytest.approx(1.0, rel=1e-4) == sim


def test_unrelated_answers_produce_low_similarity(baseline):
    """Clearly unrelated answers should produce zero or near-zero similarity, much lower than identical."""
    ref = "A primary key uniquely identifies each record in a table."
    unrelated = "Photosynthesis is the process by which green plants synthesize nutrients using sunlight."

    sim_identical = baseline.similarity(ref, ref)
    sim_unrelated = baseline.similarity(ref, unrelated)

    assert sim_unrelated == 0.0
    assert sim_unrelated < sim_identical


def test_similar_answers_score_higher_than_unrelated(baseline):
    """Similar answers should produce higher similarity than clearly unrelated answers."""
    ref = "A primary key uniquely identifies each record in a table."
    near_match = "The primary key uniquely identifies each record in the database table."
    unrelated = "Photosynthesis is the process by which green plants synthesize nutrients using sunlight."

    sim_near = baseline.similarity(ref, near_match)
    sim_unrelated = baseline.similarity(ref, unrelated)

    assert sim_near > sim_unrelated
    assert sim_near > 0.0


def test_paraphrased_answer_lexical_limitation(baseline):
    """
    Illustrates lexical baseline behavior:
    Paraphrased answer produces some overlap, but lower than identical due to word substitution.
    """
    ref = "A primary key uniquely identifies each record in a table."
    paraphrased = "A primary key uniquely identifies every row in a table."

    sim_identical = baseline.similarity(ref, ref)
    sim_paraphrase = baseline.similarity(ref, paraphrased)

    assert 0.0 < sim_paraphrase < sim_identical


def test_score_bounded_between_zero_and_one(baseline):
    """Similarity scores must strictly fall within [0.0, 1.0]."""
    test_pairs = [
        ("Database indexing speeds up queries.", "Indexing enhances database query speed."),
        ("Binary search runs in O(log n) time.", "Linear search scans every element."),
        ("Short answer grading evaluates student responses.", "Unrelated sentence about weather."),
    ]
    for ref, stu in test_pairs:
        sim = baseline.similarity(ref, stu)
        assert 0.0 <= sim <= 1.0


def test_invalid_type_handling(baseline):
    """Non-string inputs must explicitly raise TypeError."""
    with pytest.raises(TypeError, match="reference_answer must be a string"):
        baseline.similarity(None, "Valid student answer")

    with pytest.raises(TypeError, match="student_answer must be a string"):
        baseline.similarity("Valid reference answer", 12345)

    with pytest.raises(TypeError, match="student_answer must be a string"):
        baseline.similarity("Valid reference answer", ["token1", "token2"])


def test_empty_string_handling(baseline):
    """Empty strings must explicitly raise ValueError."""
    with pytest.raises(ValueError, match="reference_answer cannot be empty"):
        baseline.similarity("", "Valid student answer")

    with pytest.raises(ValueError, match="student_answer cannot be empty"):
        baseline.similarity("Valid reference answer", "")


def test_whitespace_only_handling(baseline):
    """Whitespace-only strings must explicitly raise ValueError."""
    with pytest.raises(ValueError, match="reference_answer cannot be empty"):
        baseline.similarity("   \t\n  ", "Valid student answer")

    with pytest.raises(ValueError, match="student_answer cannot be empty"):
        baseline.similarity("Valid reference answer", "   ")


def test_punctuation_only_input_returns_zero(baseline):
    """Input containing only punctuation and no alphanumeric tokens returns 0.0 gracefully."""
    ref = "A primary key uniquely identifies each record in a table."
    punct_only = "... !!! ??? ---"

    sim = baseline.similarity(ref, punct_only)
    assert sim == 0.0


def test_convenience_function():
    """compute_tfidf_cosine_similarity matches TfidfCosineBaseline.similarity output."""
    ref = "A primary key uniquely identifies each record in a table."
    student = "A primary key uniquely identifies every row in a table."

    sim_func = compute_tfidf_cosine_similarity(ref, student)
    sim_class = TfidfCosineBaseline().similarity(ref, student)

    assert sim_func == sim_class
