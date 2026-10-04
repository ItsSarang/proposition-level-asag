"""
Phase 4D Integration Test Suite.

Verifies Properties 1 through 15 and cross-domain behavior for the
end-to-end severity-aware scoring pipeline:
- PROPERTY 1: Correct additional information cannot reduce the score.
- PROPERTY 2: Irrelevant information is neutral.
- PROPERTY 3: Uncertain information receives no factual bonus.
- PROPERTY 4: Minor incorrect information causes a deduction.
- PROPERTY 5: Moderate incorrect information causes a deduction larger than minor.
- PROPERTY 6: Core contradiction causes a larger conceptual effect than minor error.
- PROPERTY 7: Correct additional cannot compensate for a core contradiction.
- PROPERTY 8: Multiple errors do not increase the score.
- PROPERTY 9: Entity-confused propositions do not become core contradictions.
- PROPERTY 10: Unresolved contradictions produce no penalty.
- PROPERTY 11: Final score remains within [0, 1].
- PROPERTY 12: Final grade remains within [0, 5].
- PROPERTY 13: Repeated execution is deterministic.
- PROPERTY 14: Every non-zero adjustment has full provenance.
- PROPERTY 15: No scoring decision depends on manually supplied severity.
"""

from __future__ import annotations

import json
import os
import pytest
from typing import Any, Dict, List

from base_asag.representation.hybrid import Modality, Polarity, PropositionType, RobustProposition
from evaluation.scoring_development.run_phase4d_evaluation import (
    get_phase4d_extended_cases,
    run_phase4d_evaluation,
)
from proposed_asag.classification.robust_classifier import (
    AdditionalInfoClass,
    ClassifiedProposition,
)
from proposed_asag.contradiction.property_contradiction import (
    ContradictionEvidence,
    ContradictionType,
)
from proposed_asag.scoring.severity_aware_scorer import (
    SeverityAwarePipeline,
    SeverityAwareScorer,
)


@pytest.fixture(scope="module")
def evaluation_traces() -> Dict[str, Any]:
    """Load or run Phase 4D evaluation traces."""
    traces_path = "evaluation/scoring_development/phase4d_score_traces.json"
    if os.path.exists(traces_path):
        with open(traces_path, "r", encoding="utf-8") as f:
            traces = json.load(f)
        return traces
    _, _, traces, _ = run_phase4d_evaluation()
    return traces


@pytest.fixture(scope="module")
def pipeline() -> SeverityAwarePipeline:
    return SeverityAwarePipeline()


@pytest.fixture(scope="module")
def scorer() -> SeverityAwareScorer:
    return SeverityAwareScorer()


def _make_prop(text: str, subj: str = "entity", pred: str = "act", obj: str = "val", mods: tuple = ()) -> RobustProposition:
    return RobustProposition(
        subject=subj,
        predicate=pred,
        object=obj,
        subject_lemma=subj,
        predicate_lemma=pred,
        object_lemma=obj,
        representation_type=PropositionType.TRIPLE,
        polarity=Polarity.POSITIVE,
        modality=Modality.ASSERTED,
        source_text=text,
        char_start=0,
        char_end=len(text),
        sentence_index=0,
        token_indices=(0, 1, 2),
        dependency_evidence=("nsubj", "dobj"),
        properties={"subject_modifiers": list(mods)},
    )


# ----------------------------------------------------------------------------
# PROPERTY 1: Correct additional information cannot reduce the score
# ----------------------------------------------------------------------------
@pytest.mark.parametrize("domain_prefix", ["PK", "BST", "CMP"])
def test_property_1_correct_additional_cannot_reduce_score(evaluation_traces, domain_prefix):
    """PROPERTY 1: Adding verified correct information must not reduce score (S_add >= S_base)."""
    base_case = f"{domain_prefix}-01"
    add_case = f"{domain_prefix}-02"
    s_base = evaluation_traces[base_case]["final_score_scaled"]
    s_add = evaluation_traces[add_case]["final_score_scaled"]
    assert s_add >= s_base - 1e-4, f"{domain_prefix} violated Prop 1: s_add {s_add} < s_base {s_base}"


# ----------------------------------------------------------------------------
# PROPERTY 2: Irrelevant information is neutral
# ----------------------------------------------------------------------------
@pytest.mark.parametrize("domain_prefix", ["PK", "BST", "CMP"])
def test_property_2_irrelevant_information_neutral(evaluation_traces, domain_prefix):
    """PROPERTY 2: Adding irrelevant information produces neutral adjustment (|delta| <= 0.05)."""
    base_case = f"{domain_prefix}-01"
    irr_case = f"{domain_prefix}-03"
    s_base = evaluation_traces[base_case]["final_score_scaled"]
    s_irr = evaluation_traces[irr_case]["final_score_scaled"]
    assert abs(s_irr - s_base) <= 0.05, f"{domain_prefix} violated Prop 2: delta = |{s_irr} - {s_base}| > 0.05"


# ----------------------------------------------------------------------------
# PROPERTY 3: Uncertain information receives no factual bonus
# ----------------------------------------------------------------------------
@pytest.mark.parametrize("domain_prefix", ["PK", "BST", "CMP"])
def test_property_3_uncertain_information_no_bonus(evaluation_traces, domain_prefix):
    """PROPERTY 3: Unverified/unsupported information receives no factual bonus (S_unc == S_base)."""
    base_case = f"{domain_prefix}-01"
    unc_case = f"{domain_prefix}-04"
    s_base = evaluation_traces[base_case]["final_score_scaled"]
    s_unc = evaluation_traces[unc_case]["final_score_scaled"]
    assert abs(s_unc - s_base) < 1e-4, f"{domain_prefix} violated Prop 3: unc {s_unc} != base {s_base}"


# ----------------------------------------------------------------------------
# PROPERTY 4: Minor incorrect information causes a deduction
# ----------------------------------------------------------------------------
def test_property_4_minor_incorrect_causes_deduction(scorer):
    """PROPERTY 4: Minor incorrect proposition applies bounded deduction (deduction = 0.20 * 0.25)."""
    stu_prop = _make_prop("A primary key is always named ID.", "primary key", "name", "id")
    ref_prop = _make_prop("A primary key uniquely identifies records.", "primary key", "identify", "record")

    ev_minor = ContradictionEvidence(
        is_contradicted=True,
        contradiction_type=ContradictionType.VALUE_CONFLICT,
        conflicting_entity="primary key",
        conflicting_property="naming",
        conflicting_value="id",
        evidence_strength=0.65,
        explanation="Peripheral naming convention misconception.",
    )

    cp = ClassifiedProposition(
        proposition=stu_prop,
        classification=AdditionalInfoClass.INCORRECT,
        relevance_evidence=None,
        contradiction_evidence=ev_minor,
        score_effect=0.0,
        rationale="Peripheral error",
    )

    res = scorer.score(
        base_score=1.0,
        classification_result=[cp],
        reference_propositions=[ref_prop],
        question="What is the purpose of a primary key?",
        domain="PRIMARY_KEY",
    )

    # Base = 1.0 (5.0 pts), minor deduction = 0.20 * 0.25 = 0.05 (0.25 pts) -> final = 4.75 pts
    assert res.final_grade < 5.0, f"Expected final_grade < 5.0, got {res.final_grade}"
    assert abs(res.final_grade - 4.75) < 1e-4, f"Expected 4.75, got {res.final_grade}"
    assert not res.has_core_invalidation


# ----------------------------------------------------------------------------
# PROPERTY 5: Moderate incorrect causes deduction larger than minor
# ----------------------------------------------------------------------------
def test_property_5_moderate_deduction_larger_than_minor(scorer):
    """PROPERTY 5: Moderate error deduction (0.20 * 0.60 = 0.12) > minor deduction (0.05)."""
    stu_minor = _make_prop("A primary key is always named ID.", "primary key", "name", "id")
    stu_mod = _make_prop("A primary key must always be an integer data type.", "primary key", "be", "integer")
    ref_prop = _make_prop("A primary key uniquely identifies records.", "primary key", "identify", "record")

    ev_minor = ContradictionEvidence(
        is_contradicted=True,
        contradiction_type=ContradictionType.VALUE_CONFLICT,
        conflicting_entity="primary key",
        conflicting_property="naming",
        conflicting_value="id",
        evidence_strength=0.65,
        explanation="Naming misconception.",
    )
    ev_mod = ContradictionEvidence(
        is_contradicted=True,
        contradiction_type=ContradictionType.VALUE_CONFLICT,
        conflicting_entity="primary key",
        conflicting_property="data_type_restriction",
        conflicting_value="integer",
        evidence_strength=0.70,
        explanation="Data type misconception.",
    )

    cp_minor = ClassifiedProposition(stu_minor, AdditionalInfoClass.INCORRECT, None, ev_minor, 0.0, "Minor")
    cp_mod = ClassifiedProposition(stu_mod, AdditionalInfoClass.INCORRECT, None, ev_mod, 0.0, "Moderate")

    res_minor = scorer.score(1.0, [cp_minor], [ref_prop], question="What is a primary key?", domain="PRIMARY_KEY")
    res_mod = scorer.score(1.0, [cp_mod], [ref_prop], question="What is a primary key?", domain="PRIMARY_KEY")

    # Minor = 4.75, Moderate = 4.40
    assert res_mod.final_grade < res_minor.final_grade, f"Moderate {res_mod.final_grade} not < minor {res_minor.final_grade}"
    assert abs(res_mod.final_grade - 4.40) < 1e-4


# ----------------------------------------------------------------------------
# PROPERTY 6: Core contradiction causes larger effect than minor/moderate
# ----------------------------------------------------------------------------
@pytest.mark.parametrize("domain_prefix", ["PK", "BST", "CMP"])
def test_property_6_core_contradiction_larger_than_minor(evaluation_traces, domain_prefix):
    """PROPERTY 6: Core contradiction causes larger penalty than minor error (S_core < S_base)."""
    base_case = f"{domain_prefix}-01"
    core_case = f"{domain_prefix}-06"
    s_base = evaluation_traces[base_case]["final_score_scaled"]
    s_core = evaluation_traces[core_case]["final_score_scaled"]

    # Invalidation discounts core by 50% (final = 2.50)
    assert s_core < s_base, f"Core contradiction {s_core} did not reduce score from {s_base}"
    assert abs(s_core - 2.50) < 1e-4, f"Expected 2.50 for single core invalidation, got {s_core}"


# ----------------------------------------------------------------------------
# PROPERTY 7: Correct additional cannot compensate for core contradiction
# ----------------------------------------------------------------------------
def test_property_7_correct_additional_cannot_compensate_core_contradiction(evaluation_traces):
    """PROPERTY 7: Positive bonus cannot override core contradiction (MIX-02 and MIX-07 < Base)."""
    mix02 = evaluation_traces["MIX-02"]["final_score_scaled"]
    pk01 = evaluation_traces["PK-01"]["final_score_scaled"]
    assert mix02 < pk01, f"MIX-02 ({mix02}) compensated for core contradiction against PK-01 ({pk01})"
    assert abs(mix02 - 2.9167) < 1e-3

    mix07 = evaluation_traces["MIX-07"]["final_score_scaled"]
    bst01 = evaluation_traces["BST-01"]["final_score_scaled"]
    assert mix07 < bst01, f"MIX-07 ({mix07}) compensated for core contradiction against BST-01 ({bst01})"
    assert abs(mix07 - 2.9167) < 1e-3


# ----------------------------------------------------------------------------
# PROPERTY 8: Multiple errors do not increase the score
# ----------------------------------------------------------------------------
def test_property_8_multiple_errors_monotonicity(evaluation_traces):
    """PROPERTY 8: Multiple errors do not increase score (S_multi <= S_single)."""
    # BST-06 (1 core) vs BST-07 (multi)
    bst06 = evaluation_traces["BST-06"]["final_score_scaled"]
    bst07 = evaluation_traces["BST-07"]["final_score_scaled"]
    assert bst07 <= bst06 + 1e-4, f"BST-07 {bst07} > BST-06 {bst06}"

    # BST-06 (1 core) vs BST-CORE-MULTI (2 core)
    bst_multi = evaluation_traces["BST-CORE-MULTI"]["final_score_scaled"]
    assert bst_multi <= bst06 + 1e-4, f"BST-CORE-MULTI {bst_multi} > BST-06 {bst06}"


# ----------------------------------------------------------------------------
# PROPERTY 9: Entity-confused propositions do not become core contradictions
# ----------------------------------------------------------------------------
def test_property_9_entity_confusion_not_core_contradiction(evaluation_traces):
    """PROPERTY 9: Foreign key / interpreter / binary tree are not core contradictions."""
    pk_adv = evaluation_traces["PK-ADV-01"]
    assert not pk_adv["has_core_invalidation"], "PK-ADV-01 falsely triggered core invalidation"
    assert pk_adv["final_score_scaled"] == 5.0, f"Expected 5.0, got {pk_adv['final_score_scaled']}"


# ----------------------------------------------------------------------------
# PROPERTY 10: Unresolved contradictions produce no penalty
# ----------------------------------------------------------------------------
def test_property_10_unresolved_contradiction_produces_no_penalty(evaluation_traces):
    """PROPERTY 10: Unresolved contradiction produces zero score penalty."""
    pk_adv = evaluation_traces["PK-ADV-01"]
    base_scaled = evaluation_traces["PK-01"]["final_score_scaled"]
    assert abs(pk_adv["final_score_scaled"] - base_scaled) < 1e-4


# ----------------------------------------------------------------------------
# PROPERTY 11 & 12: Final score in [0, 1] and final grade in [0, 5]
# ----------------------------------------------------------------------------
def test_property_11_12_score_and_grade_ranges(evaluation_traces):
    """PROPERTIES 11 & 12: All final scores in [0, 1] and final grades in [0, 5]."""
    for cid, trace in evaluation_traces.items():
        s_norm = trace["final_score_normalized"]
        s_scaled = trace["final_score_scaled"]
        assert 0.0 <= s_norm <= 1.0, f"{cid} normalized score {s_norm} out of [0, 1]"
        assert 0.0 <= s_scaled <= 5.0, f"{cid} scaled grade {s_scaled} out of [0, 5]"


# ----------------------------------------------------------------------------
# PROPERTY 13: Determinism
# ----------------------------------------------------------------------------
def test_property_13_repeated_execution_is_deterministic(pipeline):
    """PROPERTY 13: Multiple invocations on the same input yield identical scores."""
    q = "What is the purpose of a primary key?"
    ref = "A primary key uniquely identifies each record in a table."
    stu = "A primary key uniquely identifies each record in a table and cannot contain NULL values."

    res1 = pipeline.evaluate(q, ref, stu)
    res2 = pipeline.evaluate(q, ref, stu)

    assert res1.score_result.final_score == res2.score_result.final_score
    assert res1.score_result.final_grade == res2.score_result.final_grade
    assert len(res1.score_result.itemized_adjustments) == len(res2.score_result.itemized_adjustments)


# ----------------------------------------------------------------------------
# PROPERTY 14: Provenance
# ----------------------------------------------------------------------------
def test_property_14_every_adjustment_has_provenance(evaluation_traces):
    """PROPERTY 14: Every itemized adjustment record has full provenance."""
    for cid, trace in evaluation_traces.items():
        for it in trace["itemized_adjustments"]:
            assert it["proposition_text"]
            assert it["classification"]
            assert it["rationale"]
            if it["adjustment_value"] != 0.0 and it["classification"] == "INCORRECT":
                assert it["severity_level"] in ("CORE_CONTRADICTION", "MODERATE", "MINOR")
                assert it["severity_evidence"] is not None


# ----------------------------------------------------------------------------
# PROPERTY 15: No dependency on manual severity in execution path
# ----------------------------------------------------------------------------
def test_property_15_no_manual_severity_in_execution_path(pipeline):
    """PROPERTY 15: End-to-end pipeline operates without manual severity inputs."""
    # Run a student answer with a core contradiction
    q = "What is the purpose of a primary key?"
    ref = "A primary key uniquely identifies each record in a table."
    stu = "A primary key uniquely identifies each record in a table and can contain duplicate values."

    # pipeline.evaluate signature accepts: question, reference_answer, student_answer, domain=None
    # NO severity parameter exists in evaluate()
    res = pipeline.evaluate(q, ref, stu)

    # Prove that severity was automatically estimated
    assert res.score_result.has_core_invalidation
    assert res.score_result.core_contradiction_count == 1
    assert res.score_result.final_grade == 2.50

    # Inspect itemized trace: severity was computed automatically as CORE_CONTRADICTION
    contra_items = [it for it in res.score_result.itemized_adjustments if it.classification == "INCORRECT"]
    assert len(contra_items) == 1
    assert contra_items[0].severity_level == "CORE_CONTRADICTION"
    assert contra_items[0].severity_score == 1.00
    assert contra_items[0].severity_evidence["defining_property_target"] is True
