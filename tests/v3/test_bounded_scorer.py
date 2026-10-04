"""
Unit tests for Bounded Score Aggregation (Phase 8).
"""

import pytest
from base_asag.representation.hybrid import (
    Modality,
    Polarity,
    PropositionType,
    RobustProposition,
)
from proposed_asag.classification.robust_classifier import (
    AdditionalInfoClass,
    ClassifiedProposition,
)
from proposed_asag.scoring.bounded_scorer import (
    BoundedScorer,
    ScoringStrategy,
)


def make_classified_prop(cls: AdditionalInfoClass, text: str = "example") -> ClassifiedProposition:
    prop = RobustProposition(
        subject="key",
        predicate="identify",
        object="record",
        subject_lemma="key",
        predicate_lemma="identify",
        object_lemma="record",
        representation_type=PropositionType.TRIPLE,
        polarity=Polarity.POSITIVE,
        modality=Modality.ASSERTED,
        source_text=text,
        char_start=0,
        char_end=len(text),
        sentence_index=0,
        token_indices=(0, 1, 2),
        dependency_evidence=("nsubj", "dobj"),
    )
    return ClassifiedProposition(
        proposition=prop,
        classification=cls,
        relevance_evidence=None,
        contradiction_evidence=None,
        score_effect=0.0,
        rationale="test",
    )


def test_sum_strategy_linear():
    """Test that SUM strategy accumulates linear increments."""
    scorer = BoundedScorer(strategy=ScoringStrategy.SUM, linear_bonus_per_item=0.10)
    props = [
        make_classified_prop(AdditionalInfoClass.CORRECT_ADDITIONAL),
        make_classified_prop(AdditionalInfoClass.CORRECT_ADDITIONAL),
    ]
    res = scorer.score(base_score=0.50, classification_result=props)
    assert res.positive_adjustment == pytest.approx(0.20, abs=1e-4)
    assert res.final_score == pytest.approx(0.70, abs=1e-4)


def test_mean_strategy_normalized():
    """Test that MEAN strategy normalizes by unmatched proposition count."""
    scorer = BoundedScorer(strategy=ScoringStrategy.MEAN, linear_bonus_per_item=0.10)
    props = [
        make_classified_prop(AdditionalInfoClass.CORRECT_ADDITIONAL),
        make_classified_prop(AdditionalInfoClass.IRRELEVANT),
        make_classified_prop(AdditionalInfoClass.IRRELEVANT),
        make_classified_prop(AdditionalInfoClass.IRRELEVANT),
    ]
    res = scorer.score(base_score=0.50, classification_result=props)
    # 1 correct out of 4 unmatched -> (1 * 0.10) / 4 = 0.025
    assert res.positive_adjustment == pytest.approx(0.025, abs=1e-4)
    assert res.final_score == pytest.approx(0.525, abs=1e-4)


def test_saturating_strategy_prevents_verbosity_inflation():
    """
    CRUCIAL TEST (Stage 16 Case B):
    17 correct additional propositions must NOT blow up to +1.70 bonus.
    Under SATURATING strategy, maximum positive bonus is strictly capped at max_positive_bonus (0.30).
    """
    scorer = BoundedScorer(strategy=ScoringStrategy.SATURATING, max_positive_bonus=0.30, diminishing_rate=0.50)
    verbose_props = [
        make_classified_prop(AdditionalInfoClass.CORRECT_ADDITIONAL, text=f"clause_{i}")
        for i in range(17)
    ]
    res = scorer.score(base_score=0.25, classification_result=verbose_props)
    # Must remain strictly bounded below 0.30
    assert res.positive_adjustment <= 0.30
    assert res.final_score <= 0.55
    assert res.is_clipped_upper is False


def test_score_bounds_and_clipping():
    """Test that final scores never exceed 1.0 or drop below 0.0."""
    scorer = BoundedScorer(strategy=ScoringStrategy.SUM, linear_bonus_per_item=0.40, linear_penalty_per_item=0.50)

    # Upper clipping test
    props_high = [
        make_classified_prop(AdditionalInfoClass.CORRECT_ADDITIONAL),
        make_classified_prop(AdditionalInfoClass.CORRECT_ADDITIONAL),
    ]
    res_high = scorer.score(base_score=0.90, classification_result=props_high)
    assert res_high.final_score == 1.0
    assert res_high.is_clipped_upper is True

    # Lower clipping test
    props_low = [
        make_classified_prop(AdditionalInfoClass.INCORRECT),
        make_classified_prop(AdditionalInfoClass.INCORRECT),
    ]
    res_low = scorer.score(base_score=0.20, classification_result=props_low)
    assert res_low.final_score == 0.0
    assert res_low.is_clipped_lower is True
