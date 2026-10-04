"""
Unit tests for scoring stability and verbosity stress mechanisms.
"""

import pytest
from evaluation.experiments.run_scoring_stability import (
    make_mock_proposition,
    score_model_a_base_only,
    score_model_b_unbounded_linear,
    score_model_c_bounded_saturating,
    score_model_d_decomposed_core,
)
from proposed_asag.classification.robust_classifier import AdditionalInfoClass


def test_irrelevant_propositions_have_zero_effect_all_models():
    base = 0.60
    props = [
        make_mock_proposition(f"irr_{i}", AdditionalInfoClass.IRRELEVANT)
        for i in range(15)
    ]
    res_a = score_model_a_base_only(base, props)
    res_b = score_model_b_unbounded_linear(base, props)
    res_c = score_model_c_bounded_saturating(base, props)
    res_d = score_model_d_decomposed_core(base, props)

    assert res_a["final_score"] == pytest.approx(0.60)
    assert res_b["final_score"] == pytest.approx(0.60)
    assert res_c["final_score"] == pytest.approx(0.60)
    assert res_d["final_score"] == pytest.approx(0.60)


def test_saturating_model_has_strict_horizontal_asymptote():
    base = 0.50
    # Inject 50 correct propositions
    props = [
        make_mock_proposition(f"correct_{i}", AdditionalInfoClass.CORRECT_ADDITIONAL)
        for i in range(50)
    ]
    res_c = score_model_c_bounded_saturating(base, props, max_bonus=0.30)
    res_d = score_model_d_decomposed_core(base, props, max_bonus=0.30)

    # Max score cannot exceed base + max_bonus = 0.50 + 0.30 = 0.80
    assert res_c["final_score"] <= 0.80
    assert res_c["final_score"] > 0.75  # Close to asymptote
    assert res_d["final_score"] <= 0.80
    assert res_d["final_score"] > 0.75

    # In contrast, linear model hits upper bound 1.0 (5.0 * 0.10 = +5.0)
    res_b = score_model_b_unbounded_linear(base, props)
    assert res_b["final_score"] == 1.0


def test_diminishing_marginal_returns():
    base = 0.40
    p1 = [make_mock_proposition("c1", AdditionalInfoClass.CORRECT_ADDITIONAL)]
    p2 = [
        make_mock_proposition("c1", AdditionalInfoClass.CORRECT_ADDITIONAL),
        make_mock_proposition("c2", AdditionalInfoClass.CORRECT_ADDITIONAL),
    ]
    p3 = [
        make_mock_proposition("c1", AdditionalInfoClass.CORRECT_ADDITIONAL),
        make_mock_proposition("c2", AdditionalInfoClass.CORRECT_ADDITIONAL),
        make_mock_proposition("c3", AdditionalInfoClass.CORRECT_ADDITIONAL),
    ]

    s0 = score_model_c_bounded_saturating(base, [])["final_score"]
    s1 = score_model_c_bounded_saturating(base, p1)["final_score"]
    s2 = score_model_c_bounded_saturating(base, p2)["final_score"]
    s3 = score_model_c_bounded_saturating(base, p3)["final_score"]

    gain_1 = s1 - s0
    gain_2 = s2 - s1
    gain_3 = s3 - s2

    # Strictly diminishing returns: gain_1 > gain_2 > gain_3
    assert gain_1 > gain_2 > gain_3 > 0.0


def test_contradiction_penalty_bounded_and_non_negative():
    base = 0.20
    # Inject 20 contradictory propositions
    props = [
        make_mock_proposition(f"contra_{i}", AdditionalInfoClass.INCORRECT)
        for i in range(20)
    ]
    res_c = score_model_c_bounded_saturating(base, props, max_penalty=0.40)
    res_d = score_model_d_decomposed_core(base, props, max_penalty=0.40)

    # Score cannot plunge below 0.0
    assert res_c["final_score"] == 0.0
    assert res_d["final_score"] == 0.0
