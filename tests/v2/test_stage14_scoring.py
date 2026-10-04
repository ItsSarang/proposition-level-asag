"""
Unit and Integration Tests for Stage 14: Proposed ASAG Scoring.

Verifies:
1. Proposed scoring calculation:
   - No unmatched propositions (proposed_score == base_score)
   - Single CORRECT_ADDITIONAL (bonus applied)
   - Single IRRELEVANT (neutral 0.0 adjustment)
   - Single INCORRECT (penalty deducted)
   - Multiple mixed classifications evaluated simultaneously
2. Strict preservation of Base ASAG normalized score as unperturbed control.
3. Score boundary clipping in [0.0, 1.0] (upper clipping at 1.0, lower clipping at 0.0).
4. Evidence-weighted scoring mode (scaling adjustments by confidence).
5. Configurable weights, penalties, and adjustment caps.
6. Proposition-level adjustment provenance and itemized records.
7. Scale score methods (e.g. 5-point, 10-point, 100-point scales).
8. Pure JSON serializability.
9. Deterministic scoring behavior.
10. End-to-end integration from BaseASAGPipelineResult.
"""

import json
import pytest

from base_asag.pipeline import BaseASAGPipeline
from proposed_asag.classification import (
    AdditionalInformationClassifier,
    AdditionalInformationResult,
    DocumentClassificationResult,
    RelevanceEvidence,
    CompatibilityEvidence,
)
from proposed_asag.scoring import (
    ProposedScorer,
    ProposedScoreResult,
    PropositionAdjustmentRecord,
)


@pytest.fixture(scope="module")
def pipeline() -> BaseASAGPipeline:
    return BaseASAGPipeline()


@pytest.fixture(scope="module")
def classifier() -> AdditionalInformationClassifier:
    return AdditionalInformationClassifier()


@pytest.fixture(scope="module")
def scorer() -> ProposedScorer:
    return ProposedScorer()


@pytest.fixture(scope="module")
def primary_key_context():
    question = "What is the purpose of a primary key?"
    reference = "A primary key uniquely identifies each record in a table."
    return question, reference


# ---------------------------------------------------------------------------
# Test Cases
# ---------------------------------------------------------------------------

def test_no_unmatched_propositions(scorer):
    """Answer with no unmatched propositions produces zero net adjustment."""
    res = scorer.score_propositions(base_score=0.75, classifications=[])

    assert res.base_score == 0.75
    assert res.proposed_score == 0.75
    assert res.raw_proposed_score == 0.75
    assert res.net_adjustment == 0.0
    assert res.positive_adjustment == 0.0
    assert res.negative_adjustment == 0.0
    assert res.correct_additional_count == 0
    assert res.irrelevant_count == 0
    assert res.incorrect_count == 0
    assert res.uncertain_count == 0
    assert res.is_clipped_upper is False
    assert res.is_clipped_lower is False
    assert len(res.adjustment_details) == 0


def test_one_correct_additional(scorer):
    """Single CORRECT_ADDITIONAL increases score by correct_additional_weight."""
    mock_prop = {
        "proposition_id": "stu_prop_1",
        "proposition_index": 1,
        "text": "cannot contain NULL values",
        "classification": "CORRECT_ADDITIONAL",
        "confidence": 0.85,
    }
    res = scorer.score_propositions(base_score=0.50, classifications=[mock_prop])

    assert res.base_score == 0.50
    assert res.positive_adjustment == 0.10
    assert res.negative_adjustment == 0.0
    assert res.net_adjustment == 0.10
    assert res.proposed_score == 0.60
    assert res.raw_proposed_score == 0.60
    assert res.correct_additional_count == 1
    assert len(res.adjustment_details) == 1
    assert res.adjustment_details[0].applied_adjustment == 0.10


def test_one_irrelevant_additional(scorer):
    """Single IRRELEVANT proposition produces 0.0 adjustment by default."""
    mock_prop = {
        "proposition_id": "stu_prop_1",
        "proposition_index": 1,
        "text": "SQL was developed in 1970s",
        "classification": "IRRELEVANT",
        "confidence": 1.0,
    }
    res = scorer.score_propositions(base_score=0.70, classifications=[mock_prop])

    assert res.base_score == 0.70
    assert res.positive_adjustment == 0.0
    assert res.negative_adjustment == 0.0
    assert res.net_adjustment == 0.0
    assert res.proposed_score == 0.70
    assert res.irrelevant_count == 1
    assert res.adjustment_details[0].applied_adjustment == 0.0


def test_one_incorrect_additional(scorer):
    """Single INCORRECT proposition reduces score by incorrect_additional_penalty."""
    mock_prop = {
        "proposition_id": "stu_prop_1",
        "proposition_index": 1,
        "text": "can contain duplicate values",
        "classification": "INCORRECT",
        "confidence": 0.90,
    }
    res = scorer.score_propositions(base_score=0.80, classifications=[mock_prop])

    assert res.base_score == 0.80
    assert res.positive_adjustment == 0.0
    assert res.negative_adjustment == 0.20
    assert res.net_adjustment == -0.20
    assert res.proposed_score == 0.60
    assert res.raw_proposed_score == 0.60
    assert res.incorrect_count == 1
    assert res.adjustment_details[0].applied_adjustment == -0.20


def test_multiple_classifications(scorer):
    """Multiple classifications are combined additively."""
    mock_props = [
        {"proposition_id": "p1", "text": "fact 1", "classification": "CORRECT_ADDITIONAL", "confidence": 0.8},
        {"proposition_id": "p2", "text": "fact 2", "classification": "CORRECT_ADDITIONAL", "confidence": 0.8},
        {"proposition_id": "p3", "text": "fact 3", "classification": "IRRELEVANT", "confidence": 1.0},
        {"proposition_id": "p4", "text": "fact 4", "classification": "INCORRECT", "confidence": 0.9},
    ]
    # base_score = 0.50, 2 correct (+0.20), 1 irrelevant (0.0), 1 incorrect (-0.20) -> net = 0.0
    res = scorer.score_propositions(base_score=0.50, classifications=mock_props)

    assert res.base_score == 0.50
    assert res.positive_adjustment == 0.20
    assert res.negative_adjustment == 0.20
    assert res.net_adjustment == 0.0
    assert res.proposed_score == 0.50
    assert res.correct_additional_count == 2
    assert res.irrelevant_count == 1
    assert res.incorrect_count == 1
    assert len(res.adjustment_details) == 4


def test_score_upper_bound_clipping(scorer):
    """Raw proposed score exceeding 1.0 is clipped to 1.0 with is_clipped_upper=True."""
    mock_prop = {
        "proposition_id": "p1",
        "text": "valid bonus",
        "classification": "CORRECT_ADDITIONAL",
        "confidence": 1.0,
    }
    # base_score = 0.95 + 0.10 = 1.05 -> clipped to 1.0
    res = scorer.score_propositions(base_score=0.95, classifications=[mock_prop])

    assert res.base_score == 0.95
    assert res.raw_proposed_score == 1.05
    assert res.proposed_score == 1.0
    assert res.is_clipped_upper is True
    assert res.is_clipped_lower is False


def test_score_lower_bound_clipping(scorer):
    """Raw proposed score below 0.0 is clipped to 0.0 with is_clipped_lower=True."""
    mock_prop = {
        "proposition_id": "p1",
        "text": "severe error",
        "classification": "INCORRECT",
        "confidence": 1.0,
    }
    # base_score = 0.10 - 0.20 = -0.10 -> clipped to 0.0
    res = scorer.score_propositions(base_score=0.10, classifications=[mock_prop])

    assert res.base_score == 0.10
    assert res.raw_proposed_score == -0.10
    assert res.proposed_score == 0.0
    assert res.is_clipped_lower is True
    assert res.is_clipped_upper is False


def test_evidence_weighted_mode():
    """Evidence-weighted mode scales adjustments by confidence scores."""
    unweighted_scorer = ProposedScorer(evidence_weighted=False)
    weighted_scorer = ProposedScorer(evidence_weighted=True)

    mock_props = [
        {"proposition_id": "p1", "text": "bonus", "classification": "CORRECT_ADDITIONAL", "confidence": 0.70},
        {"proposition_id": "p2", "text": "penalty", "classification": "INCORRECT", "confidence": 0.50},
    ]

    res_unw = unweighted_scorer.score_propositions(base_score=0.50, classifications=mock_props)
    res_w = weighted_scorer.score_propositions(base_score=0.50, classifications=mock_props)

    # Unweighted: pos = 0.10, neg = 0.20, net = -0.10, score = 0.40
    assert res_unw.positive_adjustment == 0.10
    assert res_unw.negative_adjustment == 0.20
    assert res_unw.net_adjustment == -0.10
    assert res_unw.proposed_score == 0.40

    # Weighted: pos = 0.10 * 0.70 = 0.07, neg = 0.20 * 0.50 = 0.10, net = -0.03, score = 0.47
    assert res_w.positive_adjustment == 0.07
    assert res_w.negative_adjustment == 0.10
    assert res_w.net_adjustment == -0.03
    assert res_w.proposed_score == 0.47


def test_base_score_invariance(pipeline, scorer, primary_key_context):
    """Base ASAG score is preserved exactly across all evaluated answers."""
    question, reference = primary_key_context
    test_answers = [
        "A primary key uniquely identifies every row in a table.",
        "A primary key uniquely identifies each record in a table and cannot contain NULL values.",
        "A primary key uniquely identifies each record in a table and can contain duplicate values.",
        "A primary key uniquely identifies each record in a table. SQL was developed in the 1970s.",
    ]

    for ans in test_answers:
        pipe_res = pipeline.grade(student_answer=ans, reference_answer=reference, question=question)
        score_res = scorer.score(pipe_res)

        assert score_res.base_score == pipe_res.normalized_score
        assert score_res.summary["base_score"] == pipe_res.normalized_score


def test_configurable_weights_and_penalties():
    """Custom weights, penalties, and neutral adjustments apply correctly."""
    custom_scorer = ProposedScorer(
        correct_additional_weight=0.05,
        incorrect_additional_penalty=0.35,
        irrelevant_adjustment=-0.02,
        uncertain_adjustment=0.01,
    )

    mock_props = [
        {"proposition_id": "p1", "text": "t1", "classification": "CORRECT_ADDITIONAL", "confidence": 1.0},
        {"proposition_id": "p2", "text": "t2", "classification": "INCORRECT", "confidence": 1.0},
        {"proposition_id": "p3", "text": "t3", "classification": "IRRELEVANT", "confidence": 1.0},
        {"proposition_id": "p4", "text": "t4", "classification": "UNCERTAIN", "confidence": 1.0},
    ]

    # pos = 0.05 + 0.01 = 0.06; neg = 0.35 + 0.02 = 0.37; net = -0.31
    res = custom_scorer.score_propositions(base_score=0.50, classifications=mock_props)
    assert res.positive_adjustment == 0.06
    assert res.negative_adjustment == 0.37
    assert res.net_adjustment == -0.31
    assert res.proposed_score == 0.19


def test_optional_adjustment_caps():
    """Adjustment caps restrict maximum positive and negative adjustments."""
    capped_scorer = ProposedScorer(
        correct_additional_weight=0.10,
        incorrect_additional_penalty=0.20,
        max_positive_adjustment=0.15,
        max_negative_adjustment=0.25,
    )

    # 3 correct additions (+0.30 capped to 0.15), 2 incorrect (-0.40 capped to 0.25)
    mock_props = [
        {"proposition_id": "p1", "text": "t1", "classification": "CORRECT_ADDITIONAL", "confidence": 1.0},
        {"proposition_id": "p2", "text": "t2", "classification": "CORRECT_ADDITIONAL", "confidence": 1.0},
        {"proposition_id": "p3", "text": "t3", "classification": "CORRECT_ADDITIONAL", "confidence": 1.0},
        {"proposition_id": "p4", "text": "t4", "classification": "INCORRECT", "confidence": 1.0},
        {"proposition_id": "p5", "text": "t5", "classification": "INCORRECT", "confidence": 1.0},
    ]

    res = capped_scorer.score_propositions(base_score=0.50, classifications=mock_props)
    assert res.positive_adjustment == 0.15
    assert res.negative_adjustment == 0.25
    assert res.net_adjustment == -0.10
    assert res.proposed_score == 0.40


def test_scaled_scores(scorer):
    """scale_base_score and scale_proposed_score correctly scale to target ranges."""
    mock_prop = {
        "proposition_id": "p1",
        "text": "error",
        "classification": "INCORRECT",
        "confidence": 1.0,
    }
    # base_score = 0.80 -> proposed = 0.60
    res = scorer.score_propositions(base_score=0.80, classifications=[mock_prop])

    assert res.scale_base_score(5.0) == 4.0
    assert res.scale_proposed_score(5.0) == 3.0
    assert res.scale_base_score(100.0) == 80.0
    assert res.scale_proposed_score(100.0) == 60.0


def test_json_serializability(scorer):
    """ProposedScoreResult cleanly serializes to and parses from JSON."""
    mock_prop = {
        "proposition_id": "p1",
        "text": "fact",
        "classification": "CORRECT_ADDITIONAL",
        "confidence": 0.85,
    }
    res = scorer.score_propositions(base_score=0.60, classifications=[mock_prop])

    json_str = res.to_json(indent=2)
    assert isinstance(json_str, str)

    parsed = json.loads(json_str)
    assert parsed["base_score"] == 0.60
    assert parsed["proposed_score"] == 0.70
    assert parsed["net_adjustment"] == 0.10
    assert len(parsed["adjustment_details"]) == 1
    assert parsed["adjustment_details"][0]["applied_adjustment"] == 0.10


def test_deterministic_scoring(scorer):
    """Repeated scoring on identical input yields identical outputs."""
    mock_props = [
        {"proposition_id": "p1", "text": "fact", "classification": "CORRECT_ADDITIONAL", "confidence": 0.85},
        {"proposition_id": "p2", "text": "err", "classification": "INCORRECT", "confidence": 0.90},
    ]

    res1 = scorer.score_propositions(base_score=0.70, classifications=mock_props).to_dict()
    res2 = scorer.score_propositions(base_score=0.70, classifications=mock_props).to_dict()

    assert res1 == res2


def test_provenance_and_adjustment_records(scorer):
    """Itemized PropositionAdjustmentRecord contains complete diagnostic rationale."""
    mock_prop = {
        "proposition_id": "stu_prop_99",
        "proposition_index": 3,
        "text": "unrelated history",
        "classification": "IRRELEVANT",
        "confidence": 0.95,
        "details": {"reason": "Low overlap"},
    }
    res = scorer.score_propositions(base_score=0.80, classifications=[mock_prop])

    adj = res.adjustment_details[0]
    assert adj.proposition_id == "stu_prop_99"
    assert adj.proposition_index == 3
    assert adj.text == "unrelated history"
    assert adj.classification == "IRRELEVANT"
    assert adj.confidence == 0.95
    assert adj.applied_adjustment == 0.0
    assert "Irrelevant proposition" in adj.reason


def test_end_to_end_from_pipeline(pipeline, scorer, primary_key_context):
    """Scorer accepts raw BaseASAGPipelineResult and executes full Stage 10-14 pipeline."""
    question, reference = primary_key_context
    answer_c = "A primary key uniquely identifies each record in a table and can contain duplicate values."

    pipe_res = pipeline.grade(student_answer=answer_c, reference_answer=reference, question=question)
    score_res = scorer.score(pipe_res)

    assert score_res.base_score == pipe_res.normalized_score
    assert score_res.incorrect_count == 1
    assert score_res.negative_adjustment == 0.20
    assert score_res.proposed_score == round(pipe_res.normalized_score - 0.20, 4)


def test_invalid_parameters():
    """Negative weights or penalties and invalid base scores raise ValueError."""
    with pytest.raises(ValueError, match="correct_additional_weight must be non-negative"):
        ProposedScorer(correct_additional_weight=-0.1)

    with pytest.raises(ValueError, match="incorrect_additional_penalty must be non-negative"):
        ProposedScorer(incorrect_additional_penalty=-0.2)

    scorer = ProposedScorer()
    with pytest.raises(ValueError, match="base_score must be normalized in"):
        scorer.score_propositions(base_score=1.5, classifications=[])

    with pytest.raises(ValueError, match="base_score must be normalized in"):
        scorer.score_propositions(base_score=-0.1, classifications=[])
