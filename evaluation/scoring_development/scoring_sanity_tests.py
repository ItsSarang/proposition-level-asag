"""
Automated Monotonicity and Sanity Property Test Suite (Phase 4A Development).

Tests all 10 predefined mathematical and qualitative scoring properties across
the candidate scoring models:
- Model A: Current Additive Saturating Scorer
- Model B: Proportional Penalty Scorer
- Model C: Evidence-Weighted Bounded Severity Penalty Scorer
- Model D: Core / Additional Decomposition with Gated Compensation
"""

import pytest
from typing import List, Tuple

from proposed_asag.overhauled_pipeline import OverhauledASAGPipeline
from evaluation.scoring_development.experimental_scoring_models import (
    ModelA_CurrentAdditiveScorer,
    ModelB_ProportionalPenaltyScorer,
    ModelC_EvidenceWeightedSeverityScorer,
    ModelD_CoreAdditionalDecompositionScorer,
)


@pytest.fixture(scope="module")
def pipeline() -> OverhauledASAGPipeline:
    return OverhauledASAGPipeline()


@pytest.fixture(scope="module")
def all_models() -> List[Tuple[str, object]]:
    return [
        ("Model A", ModelA_CurrentAdditiveScorer()),
        ("Model B", ModelB_ProportionalPenaltyScorer()),
        ("Model C", ModelC_EvidenceWeightedSeverityScorer()),
        ("Model D", ModelD_CoreAdditionalDecompositionScorer()),
    ]


QUESTION = "What is the purpose of a primary key?"
REFERENCE = "A primary key uniquely identifies each record in a table."

ANSWER_CORE_ONLY = "A primary key uniquely identifies each record in a table."
ANSWER_CORE_CORRECT_ADD = "A primary key uniquely identifies each record in a table and cannot contain NULL values."
ANSWER_CORE_IRRELEVANT_ADD = "A primary key uniquely identifies each record in a table. SQL was developed in the 1970s."
ANSWER_CORE_INCORRECT_ADD = "A primary key uniquely identifies each record in a table and can contain duplicate values."
ANSWER_CORE_MULTI_INCORRECT = "A primary key uniquely identifies each record in a table and can contain duplicate values. The key also contains redundant rows."
ANSWER_PARTIAL_ALONE = "A primary key determines each record in a table."
ANSWER_PARTIAL_INCORRECT = "A primary key determines each record in a table. It can contain duplicate values."
ANSWER_CORE_UNCERTAIN_ADD = "A primary key uniquely identifies each record in a table and is usually indexed using a B-tree."


# ----------------------------------------------------------------------------
# PROPERTY 1: Adding correct information must not reduce the score
# ----------------------------------------------------------------------------
def test_property_1_correct_additional_non_decreasing(pipeline, all_models):
    """Adding verified correct information must not reduce the final score."""
    res_core = pipeline.evaluate(QUESTION, REFERENCE, ANSWER_CORE_ONLY)
    res_add = pipeline.evaluate(QUESTION, REFERENCE, ANSWER_CORE_CORRECT_ADD)

    for name, model in all_models:
        s_core = model.score(res_core.base_score_normalized, res_core.classification_result or []).clipped_score
        s_add = model.score(res_add.base_score_normalized, res_add.classification_result or []).clipped_score
        assert s_add >= s_core - 1e-6, f"{name} violated Property 1: {s_add} < {s_core}"


# ----------------------------------------------------------------------------
# PROPERTY 2: Adding irrelevant information should not substantially change score
# ----------------------------------------------------------------------------
def test_property_2_irrelevant_information_neutral(pipeline, all_models):
    """Adding off-topic/irrelevant information should have neutral effect (|delta| <= 0.05)."""
    res_core = pipeline.evaluate(QUESTION, REFERENCE, ANSWER_CORE_ONLY)
    res_irr = pipeline.evaluate(QUESTION, REFERENCE, ANSWER_CORE_IRRELEVANT_ADD)

    for name, model in all_models:
        s_core = model.score(res_core.base_score_normalized, res_core.classification_result or []).clipped_score
        s_irr = model.score(res_irr.base_score_normalized, res_irr.classification_result or []).clipped_score
        assert abs(s_irr - s_core) <= 0.05, f"{name} violated Property 2: |{s_irr} - {s_core}| > 0.05"


# ----------------------------------------------------------------------------
# PROPERTY 3: Adding a verified incorrect proposition should not increase score
# ----------------------------------------------------------------------------
def test_property_3_incorrect_information_non_increasing(pipeline, all_models):
    """Adding verified incorrect information must not increase the score."""
    res_core = pipeline.evaluate(QUESTION, REFERENCE, ANSWER_CORE_ONLY)
    res_inc = pipeline.evaluate(QUESTION, REFERENCE, ANSWER_CORE_INCORRECT_ADD)

    for name, model in all_models:
        s_core = model.score(res_core.base_score_normalized, res_core.classification_result or []).clipped_score
        s_inc = model.score(res_inc.base_score_normalized, res_inc.classification_result or []).clipped_score
        assert s_inc <= s_core + 1e-6, f"{name} violated Property 3: {s_inc} > {s_core}"


# ----------------------------------------------------------------------------
# PROPERTY 4: Adding more serious incorrect information should not increase score
# ----------------------------------------------------------------------------
def test_property_4_multiple_incorrect_non_increasing(pipeline, all_models):
    """Cumulative incorrect additions must not score higher than a single incorrect addition."""
    res_one_inc = pipeline.evaluate(QUESTION, REFERENCE, ANSWER_CORE_INCORRECT_ADD)
    res_multi_inc = pipeline.evaluate(QUESTION, REFERENCE, ANSWER_CORE_MULTI_INCORRECT)

    for name, model in all_models:
        s_one = model.score(res_one_inc.base_score_normalized, res_one_inc.classification_result or []).clipped_score
        s_multi = model.score(res_multi_inc.base_score_normalized, res_multi_inc.classification_result or []).clipped_score
        assert s_multi <= s_one + 1e-6, f"{name} violated Property 4: multi {s_multi} > one {s_one}"


# ----------------------------------------------------------------------------
# PROPERTY 5: Serious incorrect additions must produce a strict deduction
# ----------------------------------------------------------------------------
def test_property_5_serious_contradiction_produces_strict_deduction(pipeline, all_models):
    """An answer with a serious contradiction of a defining property must score strictly lower than the correct core alone."""
    res_core = pipeline.evaluate(QUESTION, REFERENCE, ANSWER_CORE_ONLY)
    res_inc = pipeline.evaluate(QUESTION, REFERENCE, ANSWER_CORE_INCORRECT_ADD)

    for name, model in all_models:
        s_core = model.score(res_core.base_score_normalized, res_core.classification_result or []).clipped_score
        s_inc = model.score(res_inc.base_score_normalized, res_inc.classification_result or []).clipped_score
        assert s_inc < s_core, f"{name} violated Property 5: incorrect {s_inc} not strictly lower than {s_core}"


# ----------------------------------------------------------------------------
# PROPERTY 6: Incorrect additions must not compensate for incomplete core
# ----------------------------------------------------------------------------
def test_property_6_incorrect_cannot_compensate_partial_core(pipeline, all_models):
    """When core content is incomplete, adding an incorrect proposition must not increase the grade."""
    res_partial = pipeline.evaluate(QUESTION, REFERENCE, ANSWER_PARTIAL_ALONE)
    res_partial_inc = pipeline.evaluate(QUESTION, REFERENCE, ANSWER_PARTIAL_INCORRECT)

    for name, model in all_models:
        s_part = model.score(res_partial.base_score_normalized, res_partial.classification_result or []).clipped_score
        s_part_inc = model.score(res_partial_inc.base_score_normalized, res_partial_inc.classification_result or []).clipped_score
        assert s_part_inc <= s_part + 1e-6, f"{name} violated Property 6: {s_part_inc} > {s_part}"


# ----------------------------------------------------------------------------
# PROPERTY 7: UNCERTAIN information must not receive positive factual bonus
# ----------------------------------------------------------------------------
def test_property_7_uncertain_no_positive_bonus(pipeline, all_models):
    """Unverified/uncertain statements must not receive bonus points merely because they are topical."""
    res_core = pipeline.evaluate(QUESTION, REFERENCE, ANSWER_CORE_ONLY)
    res_unc = pipeline.evaluate(QUESTION, REFERENCE, ANSWER_CORE_UNCERTAIN_ADD)

    for name, model in all_models:
        s_core = model.score(res_core.base_score_normalized, res_core.classification_result or []).clipped_score
        s_unc = model.score(res_unc.base_score_normalized, res_unc.classification_result or []).clipped_score
        assert s_unc <= s_core + 1e-6, f"{name} violated Property 7: uncertain received bonus {s_unc} > {s_core}"


# ----------------------------------------------------------------------------
# PROPERTY 8: Correct additional information bonuses must be bounded
# ----------------------------------------------------------------------------
def test_property_8_bonus_strictly_bounded(pipeline, all_models):
    """Correct additional information must not produce unbounded bonuses."""
    res_add = pipeline.evaluate(QUESTION, REFERENCE, ANSWER_CORE_CORRECT_ADD)

    for name, model in all_models:
        s_res = model.score(res_add.base_score_normalized, res_add.classification_result or [])
        assert s_res.positive_adjustment <= 0.35, f"{name} violated Property 8: pos_adj={s_res.positive_adjustment} > 0.35"
        assert s_res.clipped_score <= 1.0, f"{name} violated Property 8: score={s_res.clipped_score} > 1.0"


# ----------------------------------------------------------------------------
# PROPERTY 9: Scores must strictly lie in [0.0, 1.0] and [0.0, max_points]
# ----------------------------------------------------------------------------
def test_property_9_range_bounds(pipeline, all_models):
    """Scores must strictly lie in [0.0, 1.0] and scaled in [0.0, 5.0]."""
    test_answers = [
        ANSWER_CORE_ONLY,
        ANSWER_CORE_CORRECT_ADD,
        ANSWER_CORE_IRRELEVANT_ADD,
        ANSWER_CORE_INCORRECT_ADD,
        ANSWER_CORE_MULTI_INCORRECT,
        ANSWER_PARTIAL_ALONE,
        ANSWER_PARTIAL_INCORRECT,
        ANSWER_CORE_UNCERTAIN_ADD,
    ]

    for ans in test_answers:
        res = pipeline.evaluate(QUESTION, REFERENCE, ans)
        for name, model in all_models:
            s_res = model.score(res.base_score_normalized, res.classification_result or [])
            assert 0.0 <= s_res.clipped_score <= 1.0, f"{name} produced out-of-bounds normalized score: {s_res.clipped_score}"
            assert 0.0 <= s_res.scaled_score <= 5.0, f"{name} produced out-of-bounds scaled score: {s_res.scaled_score}"


# ----------------------------------------------------------------------------
# PROPERTY 10: Scoring must be strictly deterministic
# ----------------------------------------------------------------------------
def test_property_10_determinism(pipeline, all_models):
    """Multiple evaluations of identical inputs must yield identical numerical scores."""
    res1 = pipeline.evaluate(QUESTION, REFERENCE, ANSWER_CORE_INCORRECT_ADD)
    res2 = pipeline.evaluate(QUESTION, REFERENCE, ANSWER_CORE_INCORRECT_ADD)

    for name, model in all_models:
        s1 = model.score(res1.base_score_normalized, res1.classification_result or [])
        s2 = model.score(res2.base_score_normalized, res2.classification_result or [])
        assert s1.clipped_score == s2.clipped_score, f"{name} is non-deterministic: {s1.clipped_score} != {s2.clipped_score}"
        assert s1.scaled_score == s2.scaled_score, f"{name} is non-deterministic: {s1.scaled_score} != {s2.scaled_score}"
