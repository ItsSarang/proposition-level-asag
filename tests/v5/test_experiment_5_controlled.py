"""
Experiment 5 Controlled Sanity & Invariant Test Suite (Part F: R1–R20).

Verifies the mathematical, linguistic, and behavioral invariants across:
- Model D2 soft-gated scoring (R1–R14)
- Contradiction guards (R15–R17)
- Core paraphrase recovery (R18)
- Non-sentential canonical representation (R19–R20)
"""

import pytest
from typing import List

from base_asag.dependency.parser import DependencyParser
from base_asag.representation.hybrid import (
    Modality,
    Polarity,
    PropositionType,
    RobustProposition,
    RobustPropositionExtractor,
)
from evaluation.severity_development.phase4c_severity_estimator import (
    InterpretableSeverityEstimator,
    SeverityLevel,
)
from proposed_asag.classification.robust_classifier import (
    AdditionalInfoClass,
    ClassifiedProposition,
)
from proposed_asag.contradiction.guards import ContradictionGuardPipeline
from proposed_asag.contradiction.property_contradiction import (
    ContradictionEvidence,
    ContradictionType,
    PropertyContradictionDetector,
)
from proposed_asag.pipeline_v5 import Experiment5Pipeline, Experiment5Variant
from proposed_asag.proposition.canonical_reference import CanonicalReferenceExtractor
from proposed_asag.proposition.core_recovery.core_paraphrase_recovery import (
    CoreParaphraseRecoverer,
)
from proposed_asag.scoring.model_d2_scorer import ModelD2Scorer


@pytest.fixture(scope="module")
def parser():
    return DependencyParser()


@pytest.fixture(scope="module")
def hybrid_extractor():
    return RobustPropositionExtractor()


@pytest.fixture(scope="module")
def canon_extractor(parser):
    return CanonicalReferenceExtractor(parser)


@pytest.fixture(scope="module")
def contradiction_detector():
    return PropertyContradictionDetector()


@pytest.fixture(scope="module")
def contradiction_guards():
    return ContradictionGuardPipeline()


@pytest.fixture(scope="module")
def core_recoverer():
    return CoreParaphraseRecoverer()


@pytest.fixture(scope="module")
def model_d2_scorer():
    return ModelD2Scorer()


def _make_classified_prop(
    text: str,
    cls: AdditionalInfoClass,
    sev_type: str = "NONE",
    evidence_strength: float = 0.0,
    score_effect: float = 0.0,
) -> ClassifiedProposition:
    prop = RobustProposition(
        subject="test",
        predicate="test",
        object=None,
        subject_lemma="test",
        predicate_lemma="test",
        object_lemma=None,
        representation_type=PropositionType.TRIPLE,
        polarity=Polarity.POSITIVE,
        modality=Modality.ASSERTED,
        source_text=text,
        char_start=0,
        char_end=len(text),
        sentence_index=0,
        token_indices=(0,),
        dependency_evidence=("ROOT",),
    )
    contra_ev = None
    if cls == AdditionalInfoClass.INCORRECT:
        ctype = ContradictionType.VALUE_CONFLICT if sev_type != "NONE" else ContradictionType.NONE
        prop_name = "uniqueness" if sev_type == "CORE" else ("name" if sev_type == "MINOR" else "traversal")
        contra_ev = ContradictionEvidence(
            is_contradicted=True,
            contradiction_type=ctype,
            conflicting_entity="primary key",
            conflicting_property=prop_name,
            conflicting_value="val",
            evidence_strength=evidence_strength,
            explanation=f"Test contradiction ({sev_type})",
        )

    return ClassifiedProposition(
        proposition=prop,
        classification=cls,
        score_effect=score_effect,
        rationale=f"Classified as {cls.value}",
        relevance_evidence=None,
        contradiction_evidence=contra_ev,
        verification_evidence=None,
    )


# ----------------------------------------------------------------------------
# R1 & R12: Irrelevant information remains neutral
# ----------------------------------------------------------------------------
def test_r1_r12_irrelevant_information_neutral(model_d2_scorer):
    """R1 & R12: Adding irrelevant information produces zero score change."""
    base = 0.60
    clean_res = model_d2_scorer.score(base_score=base, classification_result=[])
    irr_prop = _make_classified_prop("Random off-topic remark.", AdditionalInfoClass.IRRELEVANT)
    irr_res = model_d2_scorer.score(base_score=base, classification_result=[irr_prop])

    delta = abs(irr_res.final_grade - clean_res.final_grade)
    assert delta <= 0.05, f"R1/R12 violated: delta={delta} > 0.05"
    assert irr_res.final_grade == pytest.approx(clean_res.final_grade, abs=1e-4)


# ----------------------------------------------------------------------------
# R2: Correct additional information never decreases score
# ----------------------------------------------------------------------------
def test_r2_correct_additional_non_decreasing(model_d2_scorer):
    """R2: Adding correct information must not reduce the final grade."""
    base = 0.50
    clean_res = model_d2_scorer.score(base_score=base, classification_result=[])
    ca_prop = _make_classified_prop("Valid technical elaboration.", AdditionalInfoClass.CORRECT_ADDITIONAL)
    ca_res = model_d2_scorer.score(base_score=base, classification_result=[ca_prop])

    assert ca_res.final_grade >= clean_res.final_grade - 1e-4, f"R2 violated: {ca_res.final_grade} < {clean_res.final_grade}"


# ----------------------------------------------------------------------------
# R3: Incorrect additional information decreases score
# ----------------------------------------------------------------------------
def test_r3_incorrect_strictly_decreases_score(model_d2_scorer):
    """R3: Adding verified incorrect information must strictly decrease score."""
    base = 0.80
    clean_res = model_d2_scorer.score(base_score=base, classification_result=[])
    inc_prop = _make_classified_prop("Factual misconception.", AdditionalInfoClass.INCORRECT, sev_type="MODERATE", evidence_strength=0.75)
    inc_res = model_d2_scorer.score(base_score=base, classification_result=[inc_prop])

    assert inc_res.final_grade < clean_res.final_grade, f"R3 violated: {inc_res.final_grade} >= {clean_res.final_grade}"


# ----------------------------------------------------------------------------
# R4: Core contradiction is harsher than minor error
# ----------------------------------------------------------------------------
def test_r4_core_contradiction_harsher_than_minor(model_d2_scorer):
    """R4: Core contradiction deduction is strictly harsher than minor error deduction."""
    base = 0.80
    # Core contradiction: evidence_strength >= 0.90
    core_prop = _make_classified_prop("Core defining contradiction.", AdditionalInfoClass.INCORRECT, sev_type="CORE", evidence_strength=0.95)
    core_res = model_d2_scorer.score(base_score=base, classification_result=[core_prop])

    # Minor error: evidence_strength = 0.35
    minor_prop = _make_classified_prop("Minor peripheral error.", AdditionalInfoClass.INCORRECT, sev_type="MINOR", evidence_strength=0.35)
    minor_res = model_d2_scorer.score(base_score=base, classification_result=[minor_prop])

    assert core_res.final_grade < minor_res.final_grade, f"R4 violated: core {core_res.final_grade} >= minor {minor_res.final_grade}"


# ----------------------------------------------------------------------------
# R5: Multiple errors are monotonically non-increasing
# ----------------------------------------------------------------------------
def test_r5_multiple_errors_monotonicity(model_d2_scorer):
    """R5: Score with two errors must be <= score with one error."""
    base = 0.80
    err1 = _make_classified_prop("Error 1.", AdditionalInfoClass.INCORRECT, sev_type="MODERATE", evidence_strength=0.60)
    err2 = _make_classified_prop("Error 2.", AdditionalInfoClass.INCORRECT, sev_type="MODERATE", evidence_strength=0.60)

    res_1 = model_d2_scorer.score(base_score=base, classification_result=[err1])
    res_2 = model_d2_scorer.score(base_score=base, classification_result=[err1, err2])

    assert res_2.final_grade <= res_1.final_grade + 1e-4, f"R5 violated: {res_2.final_grade} > {res_1.final_grade}"


# ----------------------------------------------------------------------------
# R6: Core contradiction cannot be compensated away by unlimited correct additions
# ----------------------------------------------------------------------------
def test_r6_core_contradiction_non_compensating(model_d2_scorer):
    """R6: Core contradiction invalidates core credit, bounded additions cannot restore full score."""
    base = 1.00
    core_err = _make_classified_prop("Core invalidation.", AdditionalInfoClass.INCORRECT, sev_type="CORE", evidence_strength=0.95)
    ca_props = [
        _make_classified_prop(f"Addition {i}", AdditionalInfoClass.CORRECT_ADDITIONAL)
        for i in range(10)
    ]

    res = model_d2_scorer.score(base_score=base, classification_result=[core_err] + ca_props)
    # Full score would be 5.0; with core invalidation, score must remain well below 5.0
    assert res.final_grade <= 3.5, f"R6 violated: grade={res.final_grade} exceeds maximum under core invalidation"


# ----------------------------------------------------------------------------
# R7: Partial core answer + severe contradiction remains below clean partial answer
# ----------------------------------------------------------------------------
def test_r7_partial_core_contradiction_below_clean(model_d2_scorer):
    """R7: Partial answer with contradiction must score below clean partial answer."""
    base = 0.50
    clean_res = model_d2_scorer.score(base_score=base, classification_result=[])
    core_err = _make_classified_prop("Core invalidation.", AdditionalInfoClass.INCORRECT, sev_type="CORE", evidence_strength=0.95)
    contra_res = model_d2_scorer.score(base_score=base, classification_result=[core_err])

    assert contra_res.final_grade < clean_res.final_grade, f"R7 violated: {contra_res.final_grade} >= {clean_res.final_grade}"


# ----------------------------------------------------------------------------
# R8: Uncertain information produces no positive bonus
# ----------------------------------------------------------------------------
def test_r8_uncertain_zero_bonus(model_d2_scorer):
    """R8: Uncertain propositions must award zero factual bonus."""
    base = 0.50
    clean_res = model_d2_scorer.score(base_score=base, classification_result=[])
    unc_props = [
        _make_classified_prop(f"Uncertain {i}", AdditionalInfoClass.UNCERTAIN)
        for i in range(5)
    ]
    unc_res = model_d2_scorer.score(base_score=base, classification_result=unc_props)

    assert unc_res.final_grade == pytest.approx(clean_res.final_grade, abs=1e-4)
    assert unc_res.positive_adjustment == 0.0


# ----------------------------------------------------------------------------
# R9: Positive bonus remains strictly bounded
# ----------------------------------------------------------------------------
def test_r9_bonus_strictly_bounded(model_d2_scorer):
    """R9: Positive bonus must never exceed max_positive_bonus."""
    base = 1.00
    ca_props = [
        _make_classified_prop(f"Addition {i}", AdditionalInfoClass.CORRECT_ADDITIONAL)
        for i in range(50)
    ]
    res = model_d2_scorer.score(base_score=base, classification_result=ca_props)

    assert res.positive_adjustment <= model_d2_scorer.max_positive_bonus + 1e-4


# ----------------------------------------------------------------------------
# R10: Final score remains strictly in [0, 5]
# ----------------------------------------------------------------------------
@pytest.mark.parametrize("base", [0.0, 0.25, 0.50, 0.75, 1.0])
def test_r10_range_bounds_all_cases(model_d2_scorer, base):
    """R10: Output grade must be bounded in [0.0, 5.0] across diverse configurations."""
    # Test high penalty
    heavy_pen = [
        _make_classified_prop(f"Err {i}", AdditionalInfoClass.INCORRECT, sev_type="CORE", evidence_strength=0.95)
        for i in range(5)
    ]
    res_pen = model_d2_scorer.score(base_score=base, classification_result=heavy_pen)
    assert 0.0 <= res_pen.final_grade <= 5.0
    assert 0.0 <= res_pen.final_score <= 1.0

    # Test high bonus
    heavy_bonus = [
        _make_classified_prop(f"Add {i}", AdditionalInfoClass.CORRECT_ADDITIONAL)
        for i in range(20)
    ]
    res_bon = model_d2_scorer.score(base_score=base, classification_result=heavy_bonus)
    assert 0.0 <= res_bon.final_grade <= 5.0
    assert 0.0 <= res_bon.final_score <= 1.0


# ----------------------------------------------------------------------------
# R11: Severity ordering remains consistent
# ----------------------------------------------------------------------------
def test_r11_severity_ordering_consistency(model_d2_scorer):
    """R11: NONE < MINOR < MODERATE < CORE_CONTRADICTION penalty ordering."""
    base = 0.80
    res_clean = model_d2_scorer.score(base_score=base, classification_result=[])

    p_minor = _make_classified_prop("A primary key is always named ID.", AdditionalInfoClass.INCORRECT, sev_type="MINOR", evidence_strength=0.30)
    p_mod = _make_classified_prop("Moderate.", AdditionalInfoClass.INCORRECT, sev_type="MODERATE", evidence_strength=0.70)
    p_core = _make_classified_prop("Core.", AdditionalInfoClass.INCORRECT, sev_type="CORE", evidence_strength=0.95)

    res_minor = model_d2_scorer.score(base_score=base, classification_result=[p_minor])
    res_mod = model_d2_scorer.score(base_score=base, classification_result=[p_mod])
    res_core = model_d2_scorer.score(base_score=base, classification_result=[p_core])

    assert res_clean.final_grade > res_minor.final_grade > res_mod.final_grade > res_core.final_grade


# ----------------------------------------------------------------------------
# R13: Repeated execution is deterministic
# ----------------------------------------------------------------------------
def test_r13_deterministic_execution(model_d2_scorer):
    """R13: Repeated scoring on identical inputs produces bitwise identical grades."""
    base = 0.65
    props = [
        _make_classified_prop("A", AdditionalInfoClass.CORRECT_ADDITIONAL),
        _make_classified_prop("B", AdditionalInfoClass.IRRELEVANT),
        _make_classified_prop("C", AdditionalInfoClass.INCORRECT, sev_type="MODERATE", evidence_strength=0.60),
    ]

    res1 = model_d2_scorer.score(base_score=base, classification_result=props)
    res2 = model_d2_scorer.score(base_score=base, classification_result=props)

    assert res1.final_grade == res2.final_grade
    assert res1.net_adjustment == res2.net_adjustment
    assert res1.positive_adjustment == res2.positive_adjustment
    assert res1.negative_adjustment == res2.negative_adjustment


# ----------------------------------------------------------------------------
# R14: Every score adjustment has provenance
# ----------------------------------------------------------------------------
def test_r14_every_adjustment_has_provenance(model_d2_scorer):
    """R14: Non-zero adjustments must record complete itemized provenance."""
    base = 0.70
    props = [
        _make_classified_prop("Add", AdditionalInfoClass.CORRECT_ADDITIONAL),
        _make_classified_prop("Err", AdditionalInfoClass.INCORRECT, sev_type="MODERATE", evidence_strength=0.65),
    ]

    res = model_d2_scorer.score(base_score=base, classification_result=props)
    assert len(res.itemized_adjustments) == 2
    for item in res.itemized_adjustments:
        assert item.proposition_text != ""
        assert item.classification in ("CORRECT_ADDITIONAL", "INCORRECT")
        assert item.rationale != ""


# ----------------------------------------------------------------------------
# R15: A < B and B > A are not contradictory (Converse guard)
# ----------------------------------------------------------------------------
def test_r15_converse_relations_not_contradictory(parser, hybrid_extractor, contradiction_detector, contradiction_guards):
    """R15: A < B and B > A must be recognized as equivalent, suppressing false contradiction."""
    ref_text = "left child is smaller than parent node"
    stu_text = "parent node is greater than left child"

    ref_doc = parser.parse_document(ref_text)
    stu_doc = parser.parse_document(stu_text)

    ref_props = hybrid_extractor.extract_document(ref_doc, ref_text)
    stu_props = hybrid_extractor.extract_document(stu_doc, stu_text)

    raw_ev = contradiction_detector.detect_contradiction(stu_props[0], ref_props)
    assert raw_ev.is_contradicted is True, "Pre-condition: raw detector flags value conflict on smaller vs greater"

    guarded_ev = contradiction_guards.guard_contradiction(
        raw_evidence=raw_ev,
        student_prop=stu_props[0],
        reference_props=ref_props,
        question="What is the relation between parent and child?",
    )
    assert guarded_ev.is_contradicted is False, f"R15 violated: converse was not guarded ({guarded_ev.explanation})"
    assert "Converse" in guarded_ev.explanation or "CONVERSE" in guarded_ev.explanation


# ----------------------------------------------------------------------------
# R16: public/private/protected coordinate categories are not automatically contradictory
# ----------------------------------------------------------------------------
def test_r16_coordinate_terms_not_contradictory(parser, hybrid_extractor, contradiction_detector, contradiction_guards):
    """R16: Coordinate categorical terms in non-conflicting context must be guarded."""
    ref_text = "Members are private."
    stu_text = "Members can be public."

    ref_doc = parser.parse_document(ref_text)
    stu_doc = parser.parse_document(stu_text)

    ref_props = hybrid_extractor.extract_document(ref_doc, ref_text)
    stu_props = hybrid_extractor.extract_document(stu_doc, stu_text)

    raw_ev = contradiction_detector.detect_contradiction(stu_props[0], ref_props)
    assert raw_ev.is_contradicted is True, "Pre-condition: WordNet flags public and private as antonyms"

    guarded_ev = contradiction_guards.guard_contradiction(
        raw_evidence=raw_ev,
        student_prop=stu_props[0],
        reference_props=ref_props,
        question="What access specifiers exist in C++?",
    )
    assert guarded_ev.is_contradicted is False, f"R16 violated: coordinate terms were not guarded ({guarded_ev.explanation})"


# ----------------------------------------------------------------------------
# R17: Array fixed-size vs linked-list dynamic-size preserves subject binding
# ----------------------------------------------------------------------------
def test_r17_contrastive_subjects_preserve_binding(parser, hybrid_extractor, contradiction_detector, contradiction_guards):
    """R17: Distinct entities in comparison prompt must not cross-contradict."""
    ref_text = "Arrays have fixed size."
    stu_text = "Linked lists have dynamic size."

    ref_doc = parser.parse_document(ref_text)
    stu_doc = parser.parse_document(stu_text)

    ref_props = hybrid_extractor.extract_document(ref_doc, ref_text)
    stu_props = hybrid_extractor.extract_document(stu_doc, stu_text)

    raw_ev = contradiction_detector.detect_contradiction(stu_props[0], ref_props)
    assert raw_ev.is_contradicted is True, "Pre-condition: fixed vs dynamic triggers value conflict"

    guarded_ev = contradiction_guards.guard_contradiction(
        raw_evidence=raw_ev,
        student_prop=stu_props[0],
        reference_props=ref_props,
        question="What is the difference between an array and a linked list?",
    )
    assert guarded_ev.is_contradicted is False, f"R17 violated: contrastive subject was not guarded ({guarded_ev.explanation})"


# ----------------------------------------------------------------------------
# R18: Core paraphrase can be recovered only with sufficient evidence
# ----------------------------------------------------------------------------
def test_r18_core_paraphrase_recovery_evidence_gating(parser, hybrid_extractor, core_recoverer):
    """R18: Paraphrase is recovered with strong evidence; weak/unrelated proposition is retained as unmatched."""
    ref_text = "A primary key uniquely identifies each record in a table."
    ref_doc = parser.parse_document(ref_text)
    ref_props = hybrid_extractor.extract_document(ref_doc, ref_text)

    # Legitimate paraphrase
    good_stu = "The primary key uniquely distinguishes records."
    good_doc = parser.parse_document(good_stu)
    good_props = hybrid_extractor.extract_document(good_doc, good_stu)

    res_good = core_recoverer.recover(
        unmatched_student_props=good_props,
        reference_props=ref_props,
        matched_reference_indices=set(),
        question="What is a primary key?",
    )
    assert res_good.recovered_count >= 1, "R18: legitimate paraphrase must be recovered"

    # Weak / unrelated proposition
    bad_stu = "SQL databases were created in the 1970s."
    bad_doc = parser.parse_document(bad_stu)
    bad_props = hybrid_extractor.extract_document(bad_doc, bad_stu)

    res_bad = core_recoverer.recover(
        unmatched_student_props=bad_props,
        reference_props=ref_props,
        matched_reference_indices=set(),
        question="What is a primary key?",
    )
    assert res_bad.recovered_count == 0, "R18: unrelated proposition must NOT be recovered as core paraphrase"
    assert len(res_bad.unmatched_propositions) == len(bad_props)


# ----------------------------------------------------------------------------
# R19: Non-sentential reference fragment produces supported canonical representation
# ----------------------------------------------------------------------------
@pytest.mark.parametrize(
    "fragment,expected_pred,expected_obj",
    [
        ("deallocates memory", "deallocates", "memory"),
        ("dynamic size", "has_property", "dynamic"),
        ("random access", "has_property", "random"),
        ("root of tree", "of", "tree"),
        ("At the main function.", "At", "function"),
    ],
)
def test_r19_supported_canonical_representation(canon_extractor, fragment, expected_pred, expected_obj):
    """R19: Common non-sentential reference fragments produce supported canonical propositions."""
    props = canon_extractor.extract_document(original_text=fragment)
    assert len(props) >= 1, f"R19 violated: no proposition extracted for '{fragment}'"

    found = any(
        (p.predicate == expected_pred or p.predicate_lemma == expected_pred)
        and (p.object == expected_obj or p.object_lemma == expected_obj)
        for p in props
    )
    assert found, f"R19 violated: expected ({expected_pred}, {expected_obj}) in {[p.to_tuple() for p in props]}"


# ----------------------------------------------------------------------------
# R20: Unsupported fragment does not generate a fabricated proposition
# ----------------------------------------------------------------------------
@pytest.mark.parametrize("empty_or_noise", ["", "   ", "...", "???", "\t\n"])
def test_r20_unsupported_fragment_no_hallucination(canon_extractor, empty_or_noise):
    """R20: Unsupported noise or empty fragments must return empty list (no hallucinations)."""
    props = canon_extractor.extract_document(original_text=empty_or_noise)
    assert len(props) == 0, f"R20 violated: fabricated {len(props)} propositions for noise '{empty_or_noise}'"


# ----------------------------------------------------------------------------
# R21: Complete clausal sentence does not generate spurious unanchored verb fragments
# ----------------------------------------------------------------------------
def test_r21_clausal_sentence_no_spurious_verb_fragments(canon_extractor):
    """R21: A finite clause with subject must not produce duplicate unanchored verb fragments."""
    text = "A primary key uniquely identifies each record in a table."
    props = canon_extractor.extract_document(original_text=text)
    assert len(props) == 1, f"Expected exactly 1 clausal proposition, got {len(props)}: {[p.source_text for p in props]}"
    assert props[0].subject == "key"
    assert props[0].predicate == "identifies"
    assert props[0].object == "record"


# ----------------------------------------------------------------------------
# R22: Explicit contradiction of core reference claim produces zero grade
# ----------------------------------------------------------------------------
def test_r22_explicit_contradiction_of_essential_claim_zero_grade():
    """R22: Explicit negation of the essential reference claim invalidates core credit (Grade 0.0)."""
    pipeline = Experiment5Pipeline()
    q = "What is the purpose of a primary key in a relational database?"
    ref = "A primary key uniquely identifies each record in a table."
    stu = "A primary key never identifies each record in a table."

    result = pipeline.evaluate(q, ref, stu)

    assert result.base_score_effective == 0.0, f"Expected effective base score 0.0, got {result.base_score_effective}"
    assert result.final_grade == 0.0, f"Expected final grade 0.0, got {result.final_grade}"
    assert result.score_result.has_core_invalidation is True
    assert result.score_result.core_contradiction_count >= 1
    assert any(
        item.classification == "INCORRECT" and item.severity_level == "CORE_CONTRADICTION"
        for item in result.score_result.itemized_adjustments
    )


# ----------------------------------------------------------------------------
# R23: Contrast cases for contradiction vs valid answers
# ----------------------------------------------------------------------------
def test_r23_contrast_cases_for_contradiction_and_valid_answers():
    """R23: Explicit contradiction receives 0.0 while correct and additive answers receive full credit."""
    pipeline = Experiment5Pipeline()
    q = "What is the purpose of a primary key in a relational database?"
    ref = "A primary key uniquely identifies each record in a table."

    # 1. Exact / clean correct answer
    res_clean = pipeline.evaluate(q, ref, "A primary key uniquely identifies each record in a table.")
    assert res_clean.final_grade == 5.0
    assert res_clean.score_result.core_contradiction_count == 0

    # 2. Correct answer + valid additional information
    res_valid_add = pipeline.evaluate(
        q, ref, "A primary key uniquely identifies each record in a table and cannot contain NULL values."
    )
    assert res_valid_add.final_grade == 5.0
    assert res_valid_add.score_result.core_contradiction_count == 0

    # 3. Correct answer + irrelevant additional information
    res_irrel = pipeline.evaluate(
        q, ref, "A primary key uniquely identifies each record in a table. SQL was created in 1970."
    )
    assert res_irrel.final_grade == 5.0
    assert res_irrel.score_result.core_contradiction_count == 0

    # 4. Explicit contradiction of core claim
    res_contra = pipeline.evaluate(q, ref, "A primary key never identifies each record in a table.")
    assert res_contra.final_grade == 0.0
    assert res_contra.score_result.core_contradiction_count == 1
    assert res_contra.score_result.has_core_invalidation is True


# ----------------------------------------------------------------------------
# R24: Copula-adjective to passive verb alternation recovery
# ----------------------------------------------------------------------------
def test_r24_copula_adjective_verb_bridge(parser, hybrid_extractor, canon_extractor, core_recoverer):
    """R24: 'X is accessible' alternates semantically with 'X can be accessed'."""
    ref_text = "A local variable is accessible only within the function or block in which it is declared."
    stu_text = "A local variable can only be accessed inside the function or block where it is defined."

    ref_doc = parser.parse_document(ref_text)
    stu_doc = parser.parse_document(stu_text)

    ref_props = canon_extractor.extract_document(ref_doc, ref_text)
    stu_props = hybrid_extractor.extract_document(stu_doc, stu_text)

    # ref_props[0] is 'variable is accessible'
    # stu_props[0] is 'variable accessed None'
    score, ev = core_recoverer._check_copula_adjective_verb_bridge(stu_props[0], ref_props[0])
    assert score >= 0.70, f"Expected copula-verb score >= 0.70, got {score}: {ev}"
    assert ev.get("copula_adjective") == "accessible"
    assert ev.get("verbal_predicate") == "access"


# ----------------------------------------------------------------------------
# R25: Domain equivalence recovery for declare <-> define
# ----------------------------------------------------------------------------
def test_r25_declare_define_domain_equivalence_recovery(core_recoverer):
    """R25: 'declare' and 'define' are recognized as equivalent in variable scoping contexts."""
    sim = core_recoverer._compare_lemmas("declare", "define", pos="VERB")
    assert sim >= 0.75, f"Expected similarity >= 0.75, got {sim}"

    sim_rev = core_recoverer._compare_lemmas("define", "declare", pos="VERB")
    assert sim_rev >= 0.75, f"Expected symmetric similarity >= 0.75, got {sim_rev}"


# ----------------------------------------------------------------------------
# R26: Example B correct paraphrase receives substantial credit
# ----------------------------------------------------------------------------
def test_r26_example_b_correct_paraphrase_substantial_credit():
    """R26: Correct paraphrase with syntactic alternation and lexical variation receives >= 3.5/5.0."""
    pipeline = Experiment5Pipeline()
    q = "What is the scope of a local variable in a function?"
    ref = "A local variable is accessible only within the function or block in which it is declared."
    stu = "A local variable has local scope and can only be accessed inside the specific block or function where it is defined."

    result = pipeline.evaluate(q, ref, stu)

    assert result.final_grade >= 3.5, f"Expected final grade >= 3.5/5.0, got {result.final_grade}"
    assert result.base_score_effective >= 0.70, f"Expected effective base coverage >= 0.70, got {result.base_score_effective}"
    assert result.recovered_core_count >= 1, f"Expected at least 1 recovered core paraphrase, got {result.recovered_core_count}"
    assert result.score_result.core_contradiction_count == 0


# ----------------------------------------------------------------------------
# R27: Contrast cases for Example B copula-adjective and scoping
# ----------------------------------------------------------------------------
def test_r27_example_b_contrast_cases(parser, hybrid_extractor, canon_extractor, core_recoverer):
    """R27: Unrelated actions must not falsely bridge to copula-adjective propositions."""
    ref_text = "A local variable is accessible only within the function."
    unrelated_stu = "A local variable was destroyed."

    ref_doc = parser.parse_document(ref_text)
    stu_doc = parser.parse_document(unrelated_stu)

    ref_props = canon_extractor.extract_document(ref_doc, ref_text)
    stu_props = hybrid_extractor.extract_document(stu_doc, unrelated_stu)

    score, ev = core_recoverer._check_copula_adjective_verb_bridge(stu_props[0], ref_props[0])
    assert score == 0.0 or score < core_recoverer.recovery_threshold, (
        f"Unrelated action 'destroyed' should not bridge to 'accessible': got score={score}"
    )
