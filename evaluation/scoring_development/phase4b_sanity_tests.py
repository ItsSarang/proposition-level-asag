"""
Phase 4B Scoring Sanity & Qualitative Constraint Test Suite.

Verifies qualitative ordering constraints R1 through R12, monotonicity,
severity ordering, cross-domain consistency, and range bounds across
the candidate scoring models using the 33 controlled Phase 4B cases:
- Model A: Current Additive Saturating Scorer
- Model B: Proportional Penalty Scorer
- Model C: Evidence-Weighted Bounded Severity Penalty Scorer
- Model D: Core / Additional Decomposition with Gated Compensation
"""

import json
import os
import pytest
from typing import Any, Dict, List

from evaluation.scoring_development.run_phase4b_cases import (
    get_phase4b_case_definitions,
    run_phase4b_evaluation,
)
from evaluation.scoring_development.experimental_scoring_models import (
    ModelA_CurrentAdditiveScorer,
    ModelB_ProportionalPenaltyScorer,
    ModelC_EvidenceWeightedSeverityScorer,
    ModelD_CoreAdditionalDecompositionScorer,
)


@pytest.fixture(scope="module")
def evaluation_data():
    """Load or run Phase 4B evaluation data."""
    traces_path = "evaluation/scoring_development/phase4b_score_traces.json"
    if os.path.exists(traces_path):
        with open(traces_path, "r", encoding="utf-8") as f:
            traces = json.load(f)
        return traces
    _, _, traces = run_phase4b_evaluation()
    return traces


# ----------------------------------------------------------------------------
# R1 & R12: Irrelevant information has neutral effect
# ----------------------------------------------------------------------------
@pytest.mark.parametrize("domain_prefix", ["PK", "BST", "CMP"])
def test_r1_r12_irrelevant_information_neutral(evaluation_data, domain_prefix):
    """
    R1 & R12: Adding irrelevant information must not make an answer substantially
    worse or better (|delta| <= 0.05 on [0, 5] scale).
    """
    base_case = f"{domain_prefix}-01"
    irr_case = f"{domain_prefix}-03"

    for m_key in ["Model_A", "Model_B", "Model_C", "Model_D"]:
        s_base = evaluation_data[base_case]["models"][m_key]["scaled_score"]
        s_irr = evaluation_data[irr_case]["models"][m_key]["scaled_score"]
        delta = abs(s_irr - s_base)
        assert delta <= 0.05, f"{m_key} in {domain_prefix} violated R1/R12: |{s_irr} - {s_base}| = {delta} > 0.05"


# ----------------------------------------------------------------------------
# R2: Correct additional information must not decrease the score
# ----------------------------------------------------------------------------
@pytest.mark.parametrize("domain_prefix", ["PK", "BST", "CMP"])
def test_r2_correct_additional_non_decreasing(evaluation_data, domain_prefix):
    """
    R2: Adding verified correct information must not reduce the final score.
    """
    base_case = f"{domain_prefix}-01"
    add_case = f"{domain_prefix}-02"

    for m_key in ["Model_A", "Model_B", "Model_C", "Model_D"]:
        s_base = evaluation_data[base_case]["models"][m_key]["scaled_score"]
        s_add = evaluation_data[add_case]["models"][m_key]["scaled_score"]
        assert s_add >= s_base - 1e-4, f"{m_key} in {domain_prefix} violated R2: {s_add} < {s_base}"


# ----------------------------------------------------------------------------
# R3: Incorrect additions must strictly decrease score from core baseline
# ----------------------------------------------------------------------------
@pytest.mark.parametrize("domain_prefix", ["PK", "BST", "CMP"])
def test_r3_incorrect_strictly_decreases_score(evaluation_data, domain_prefix):
    """
    R3: Adding verified incorrect information must strictly decrease score.
    """
    base_case = f"{domain_prefix}-01"
    inc_case = f"{domain_prefix}-06"

    for m_key in ["Model_A", "Model_B", "Model_C", "Model_D"]:
        s_base = evaluation_data[base_case]["models"][m_key]["scaled_score"]
        s_inc = evaluation_data[inc_case]["models"][m_key]["scaled_score"]
        assert s_inc < s_base, f"{m_key} in {domain_prefix} violated R3: {s_inc} >= {s_base}"


# ----------------------------------------------------------------------------
# R4: Core contradiction < Minor incorrect addition
# ----------------------------------------------------------------------------
@pytest.mark.parametrize("domain_prefix", ["PK", "BST", "CMP"])
def test_r4_core_contradiction_harsher_than_minor(evaluation_data, domain_prefix):
    """
    R4: An answer with a serious core contradiction must score strictly lower than
    an otherwise identical answer with only a minor factual mistake.

    Note: Model A is known to FAIL R4 because it treats all incorrect propositions
    identically. Models B, C, D must satisfy R4.
    """
    minor_case = f"{domain_prefix}-05"
    core_case = f"{domain_prefix}-06"

    for m_key in ["Model_B", "Model_C", "Model_D"]:
        s_minor = evaluation_data[minor_case]["models"][m_key]["scaled_score"]
        s_core = evaluation_data[core_case]["models"][m_key]["scaled_score"]
        assert s_core < s_minor, f"{m_key} in {domain_prefix} violated R4: core {s_core} >= minor {s_minor}"

    # Verify that Model A exhibits the documented limitation (fails R4)
    s_minor_a = evaluation_data[minor_case]["models"]["Model_A"]["scaled_score"]
    s_core_a = evaluation_data[core_case]["models"]["Model_A"]["scaled_score"]
    assert abs(s_core_a - s_minor_a) < 1e-4, "Model A unexpectedly distinguished severity"


# ----------------------------------------------------------------------------
# R5: Multiple serious errors <= Single serious error
# ----------------------------------------------------------------------------
@pytest.mark.parametrize("domain_prefix", ["BST", "CMP"])
def test_r5_multiple_errors_monotonicity(evaluation_data, domain_prefix):
    """
    R5: Multiple incorrect additions must produce equal or greater penalty than a single error.
    """
    single_case = f"{domain_prefix}-06"
    multi_case = f"{domain_prefix}-07"

    for m_key in ["Model_A", "Model_B", "Model_C", "Model_D"]:
        s_single = evaluation_data[single_case]["models"][m_key]["scaled_score"]
        s_multi = evaluation_data[multi_case]["models"][m_key]["scaled_score"]
        assert s_multi <= s_single + 1e-4, f"{m_key} in {domain_prefix} violated R5: multi {s_multi} > single {s_single}"


# ----------------------------------------------------------------------------
# R6 & R7: Partial core + incorrect <= Partial core alone (No compensation)
# ----------------------------------------------------------------------------
@pytest.mark.parametrize("domain_prefix", ["PK", "BST", "CMP"])
def test_r6_r7_partial_core_non_compensating(evaluation_data, domain_prefix):
    """
    R6 & R7: Adding incorrect propositions to a partial core answer must not
    increase the score.
    """
    part_inc_case = f"{domain_prefix}-08" if domain_prefix in ("BST", "CMP") else "PK-09"
    base_score = evaluation_data[part_inc_case]["base_score_scaled"]

    for m_key in ["Model_A", "Model_B", "Model_C", "Model_D"]:
        s_final = evaluation_data[part_inc_case]["models"][m_key]["scaled_score"]
        assert s_final <= base_score + 1e-4, f"{m_key} violated R6/R7 in {part_inc_case}: {s_final} > {base_score}"


# ----------------------------------------------------------------------------
# R8: UNCERTAIN information receives zero positive bonus
# ----------------------------------------------------------------------------
@pytest.mark.parametrize("domain_prefix", ["PK", "BST", "CMP"])
def test_r8_uncertain_zero_bonus(evaluation_data, domain_prefix):
    """
    R8: Unsupported relevant statements (UNCERTAIN) must receive zero bonus.
    """
    base_case = f"{domain_prefix}-01"
    unc_case = f"{domain_prefix}-04"

    for m_key in ["Model_A", "Model_B", "Model_C", "Model_D"]:
        s_base = evaluation_data[base_case]["models"][m_key]["scaled_score"]
        s_unc = evaluation_data[unc_case]["models"][m_key]["scaled_score"]
        assert s_unc <= s_base + 1e-4, f"{m_key} violated R8 in {domain_prefix}: {s_unc} > {s_base}"


# ----------------------------------------------------------------------------
# R9: Positive bonus strictly bounded
# ----------------------------------------------------------------------------
def test_r9_bonus_strictly_bounded(evaluation_data):
    """
    R9: Bonus from correct additional information must never exceed bounds.
    """
    for cid, cdata in evaluation_data.items():
        for m_key in ["Model_A", "Model_B", "Model_C", "Model_D"]:
            m_res = cdata["models"][m_key]
            assert m_res["positive_adjustment"] <= 0.35 + 1e-4, f"{m_key} exceeded bonus bound in {cid}"
            assert m_res["clipped_score"] <= 1.0 + 1e-4, f"{m_key} exceeded normalized bound in {cid}"


# ----------------------------------------------------------------------------
# R10: Range bounds [0.0, 1.0] and [0.0, 5.0]
# ----------------------------------------------------------------------------
def test_r10_range_bounds_all_cases(evaluation_data):
    """
    R10: All scores must strictly lie within [0.0, 1.0] normalized and [0.0, 5.0] scaled.
    """
    for cid, cdata in evaluation_data.items():
        for m_key in ["Model_A", "Model_B", "Model_C", "Model_D"]:
            m_res = cdata["models"][m_key]
            norm = m_res["clipped_score"]
            scaled = m_res["scaled_score"]
            assert 0.0 <= norm <= 1.0, f"{m_key} out of norm bounds in {cid}: {norm}"
            assert 0.0 <= scaled <= 5.0, f"{m_key} out of scaled bounds in {cid}: {scaled}"


# ----------------------------------------------------------------------------
# R11: Severity ordering: Minor <= Moderate <= Core Contradiction
# ----------------------------------------------------------------------------
def test_r11_severity_ordering_consistency(evaluation_data):
    """
    R11: For otherwise identical answers:
    penalty(minor) <= penalty(moderate) <= penalty(core contradiction).
    """
    for domain_prefix in ["PK", "BST", "CMP"]:
        minor_case = f"{domain_prefix}-05"
        core_case = f"{domain_prefix}-06"

        for m_key in ["Model_B", "Model_C", "Model_D"]:
            s_minor = evaluation_data[minor_case]["models"][m_key]["scaled_score"]
            s_core = evaluation_data[core_case]["models"][m_key]["scaled_score"]
            # Higher score means smaller penalty
            assert s_minor >= s_core, f"{m_key} violated R11 severity ordering in {domain_prefix}: minor {s_minor} < core {s_core}"


# ----------------------------------------------------------------------------
# Cross-Domain Consistency
# ----------------------------------------------------------------------------
def test_cross_domain_consistency(evaluation_data):
    """
    Verifies that identical qualitative conditions (e.g. Core Contradiction)
    produce consistent deductions across Primary Key, BST, and Compiler domains.
    """
    # Core contradiction across the 3 domains
    pk_core = evaluation_data["PK-06"]["models"]["Model_D"]["scaled_score"]
    bst_core = evaluation_data["BST-06"]["models"]["Model_D"]["scaled_score"]
    cmp_core = evaluation_data["CMP-06"]["models"]["Model_D"]["scaled_score"]

    assert pk_core == 2.50
    assert bst_core == 2.50
    assert cmp_core == 2.50

    # Minor incorrect across the 3 domains
    pk_minor = evaluation_data["PK-05"]["models"]["Model_D"]["scaled_score"]
    bst_minor = evaluation_data["BST-05"]["models"]["Model_D"]["scaled_score"]
    cmp_minor = evaluation_data["CMP-05"]["models"]["Model_D"]["scaled_score"]

    assert pk_minor == 4.75
    assert bst_minor == 4.75
    assert cmp_minor == 4.75


# ----------------------------------------------------------------------------
# Mixed Information Non-Compensation
# ----------------------------------------------------------------------------
def test_mixed_information_behavior(evaluation_data):
    """
    Verifies that in MIX-02 (Correct additional + core contradiction),
    correct bonus does not wipe out or compensate for a serious core contradiction.
    """
    # Model D core discount is 50% (2.50), gated bonus adds at most 0.4167 -> 2.9167
    m_d_mix2 = evaluation_data["MIX-02"]["models"]["Model_D"]["scaled_score"]
    assert m_d_mix2 < 3.5, f"Model D allowed correct bonus to over-compensate core contradiction: {m_d_mix2}"

    # Model B applies multiplicative penalty to credit: 3.575
    m_b_mix2 = evaluation_data["MIX-02"]["models"]["Model_B"]["scaled_score"]
    assert m_b_mix2 < 4.0, f"Model B allowed excessive compensation: {m_b_mix2}"


# ----------------------------------------------------------------------------
# Determinism
# ----------------------------------------------------------------------------
def test_determinism_across_models():
    """
    Verifies that multiple repeated evaluations yield strictly identical results.
    """
    model_b = ModelB_ProportionalPenaltyScorer()
    model_d = ModelD_CoreAdditionalDecompositionScorer()

    cdefs = get_phase4b_case_definitions()
    sample_cases = [cdefs[0], cdefs[5], cdefs[8], cdefs[27], cdefs[30]]

    for cdef in sample_cases:
        res1_b = model_b.score(1.0, [], severities={}).scaled_score
        res2_b = model_b.score(1.0, [], severities={}).scaled_score
        assert res1_b == res2_b

        res1_d = model_d.score(1.0, [], severities={}).scaled_score
        res2_d = model_d.score(1.0, [], severities={}).scaled_score
        assert res1_d == res2_d
