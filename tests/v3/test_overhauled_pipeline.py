"""
Comprehensive Tests for the Overhauled ASAG Pipeline (System 4).
"""

import pytest

from proposed_asag.overhauled_pipeline import OverhauledASAGPipeline, OverhauledASAGResult
from proposed_asag.scoring.bounded_scorer import ScoringStrategy


@pytest.fixture(scope="module")
def pipeline():
    return OverhauledASAGPipeline(
        use_hybrid_representation=True,
        semantic_matcher_version="v2",
        matching_strategy="global",
        use_question_relevance=True,
        use_property_contradiction=True,
        scoring_strategy=ScoringStrategy.SATURATING,
        enable_proposed_scoring=True,
        scale=5.0,
    )


def test_exact_match(pipeline):
    q = "What is the purpose of a primary key?"
    r = "A primary key uniquely identifies each record in a table."
    s = "A primary key uniquely identifies each record in a table."

    res = pipeline.evaluate(q, r, s)
    assert isinstance(res, OverhauledASAGResult)
    assert res.base_score_scaled == 5.0
    assert res.final_score_scaled == 5.0
    assert res.matched_propositions_count >= 1
    assert res.correct_additional_count == 0
    assert len(res.explanation_trace.matched_items) >= 1


def test_correct_addition_primary_key(pipeline):
    q = "What is the purpose of a primary key?"
    r = "A primary key uniquely identifies each record in a table."
    s = "A primary key uniquely identifies each record in a table and cannot contain NULL values."

    res = pipeline.evaluate(q, r, s)
    assert res.matched_propositions_count >= 1
    assert res.correct_additional_count >= 1
    assert res.positive_adjustment > 0.0
    assert res.final_score_scaled >= res.base_score_scaled
    assert len(res.explanation_trace.correct_additional_items) >= 1


def test_irrelevant_addition_sql(pipeline):
    q = "What is the purpose of a primary key?"
    r = "A primary key uniquely identifies each record in a table."
    s = "A primary key uniquely identifies each record in a table. SQL was developed in the 1970s."

    res = pipeline.evaluate(q, r, s)
    assert res.matched_propositions_count >= 1
    assert res.irrelevant_count >= 1
    assert len(res.explanation_trace.irrelevant_items) >= 1


def test_contradictory_addition_duplicates(pipeline):
    q = "What is the purpose of a primary key?"
    r = "A primary key uniquely identifies each record in a table."
    s = "A primary key uniquely identifies each record in a table and can contain duplicate values."

    res = pipeline.evaluate(q, r, s)
    assert res.matched_propositions_count >= 1
    assert res.incorrect_count >= 1
    assert res.negative_adjustment > 0.0
    assert len(res.explanation_trace.contradictory_items) >= 1


def test_nominal_fragment_recovery(pipeline):
    # Reference answer is a non-finite infinitive clause that yields 0 triples in Base ASAG
    q = "What is the role of a prototype?"
    r = "To simulate portions of software."
    s = "To simulate portions of software."

    res = pipeline.evaluate(q, r, s)
    # Hybrid proposition extractor recovers the proposition and scores it
    assert res.reference_propositions_count >= 1
    assert res.matched_propositions_count >= 1
    assert res.base_score_scaled == 5.0
