"""
Unit tests for Property-Level Contradiction Detection (Phase 5).
"""

import pytest
from base_asag.representation.hybrid import (
    Modality,
    Polarity,
    PropositionType,
    RobustProposition,
)
from proposed_asag.contradiction.property_contradiction import (
    ContradictionEvidence,
    ContradictionType,
    PropertyContradictionDetector,
)


@pytest.fixture(scope="module")
def detector():
    return PropertyContradictionDetector()


def make_prop(subj, pred, obj, polarity=Polarity.POSITIVE, text=""):
    return RobustProposition(
        subject=subj,
        predicate=pred,
        object=obj,
        subject_lemma=subj.lower() if subj else None,
        predicate_lemma=pred.lower() if pred else "",
        object_lemma=obj.lower() if obj else None,
        representation_type=PropositionType.TRIPLE,
        polarity=polarity,
        modality=Modality.ASSERTED,
        source_text=text or f"{subj} {pred} {obj}",
        char_start=0,
        char_end=len(text) if text else 10,
        sentence_index=0,
        token_indices=(0, 1, 2),
        dependency_evidence=("nsubj", "dobj"),
    )


def test_property_conflict_duplicate_vs_unique(detector):
    """Test value conflict: 'duplicate values' vs 'uniquely identify'."""
    ref = [make_prop("key", "identify", "record", text="primary keys uniquely identify each record")]
    stu = [make_prop("key", "contain", "duplicate", text="primary keys can contain duplicate values")]

    evidence = detector.detect_contradiction(stu[0], ref)
    assert evidence.is_contradicted is True
    assert evidence.contradiction_type == ContradictionType.VALUE_CONFLICT
    assert evidence.conflicting_property == "uniqueness"


def test_antonym_equivalence_not_fixed_vs_variable(detector):
    """
    CRUCIAL TEST (Stage 16 Case G):
    'not fixed in size' should NOT be flagged as a contradiction of 'variable length'.
    Negated antonym is semantically equivalent!
    """
    ref = [make_prop("list", "have", "length", text="linked lists can be of variable length")]
    stu = [make_prop("list", "be", "size", polarity=Polarity.NEGATIVE, text="linked list is not fixed in size")]

    evidence = detector.detect_contradiction(stu[0], ref)
    assert evidence.is_contradicted is False
    assert evidence.contradiction_type == ContradictionType.NONE


def test_explicit_negation_conflict(detector):
    """Test direct negation on matching predicate: 'does not convert' vs 'converts'."""
    ref = [make_prop("compiler", "convert", "code", polarity=Polarity.POSITIVE)]
    stu = [make_prop("compiler", "convert", "code", polarity=Polarity.NEGATIVE)]

    evidence = detector.detect_contradiction(stu[0], ref)
    assert evidence.is_contradicted is True
    assert evidence.contradiction_type == ContradictionType.EXPLICIT_NEGATION


def test_unsupported_is_not_contradicted(detector):
    """
    Enforce: NOT_SUPPORTED != CONTRADICTED.
    A proposition about recursion base cases does not contradict an iteration definition.
    """
    ref = [make_prop("iteration", "use", "loop", text="iteration uses a repetition structure")]
    stu = [make_prop("recursion", "have", "case", text="recursion relies on a base case")]

    evidence = detector.detect_contradiction(stu[0], ref)
    assert evidence.is_contradicted is False
    assert evidence.contradiction_type == ContradictionType.NONE


def test_unrelated_information_not_contradicted(detector):
    """Irrelevant information (e.g. historical facts) is not a contradiction."""
    ref = [make_prop("key", "identify", "record", text="primary key uniquely identifies records")]
    stu = [make_prop("sql", "develop", "system", text="SQL was developed in 1970")]

    evidence = detector.detect_contradiction(stu[0], ref)
    assert evidence.is_contradicted is False
    assert evidence.contradiction_type == ContradictionType.NONE
