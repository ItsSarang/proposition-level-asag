"""
Test Suite for Phase 4C Interpretable Contradiction Severity Estimation.

Verifies:
1. Contradiction/severity separation (non-contradictions get NONE).
2. Distinction among MINOR, MODERATE, and CORE_CONTRADICTION.
3. Entity-specificity (preventing entity overgeneralization on confused entities).
4. UNRESOLVED status on entity mismatches.
5. Determinism across multiple invocations.
6. Provenance and transparent explanations.
7. Independence from final scores (non-circularity).
8. Production scorer integrity.
"""

import pytest
from typing import List

from base_asag.representation.hybrid import Modality, Polarity, PropositionType, RobustProposition
from evaluation.severity_development.phase4c_severity_estimator import (
    InterpretableSeverityEstimator,
    SeverityLevel,
)
from proposed_asag.contradiction.property_contradiction import (
    ContradictionEvidence,
    ContradictionType,
)
from proposed_asag.scoring.bounded_scorer import BoundedScorer


@pytest.fixture(scope="module")
def estimator() -> InterpretableSeverityEstimator:
    return InterpretableSeverityEstimator()


def _make_prop(text: str, subj: str = "entity", pred: str = "act", obj: str = "val") -> RobustProposition:
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
    )


# ----------------------------------------------------------------------------
# 1. Contradiction / Severity Separation
# ----------------------------------------------------------------------------
def test_non_contradiction_receives_none_severity(estimator):
    """A proposition that is NOT contradictory must strictly receive severity NONE."""
    stu_prop = _make_prop("A primary key is an indexed column.", "primary key", "index", "column")
    ref_prop = _make_prop("A primary key uniquely identifies records.", "primary key", "identify", "record")

    # Contradiction is False
    ev_none = ContradictionEvidence(
        is_contradicted=False,
        contradiction_type=ContradictionType.NONE,
        conflicting_entity=None,
        conflicting_property=None,
        conflicting_value=None,
        evidence_strength=0.0,
        explanation="No contradiction.",
    )

    res = estimator.estimate(ev_none, stu_prop, [ref_prop], domain="PRIMARY_KEY")
    assert res.severity == SeverityLevel.NONE
    assert res.severity_score == 0.0
    assert not res.evidence.is_contradicted


def test_none_evidence_object_receives_none_severity(estimator):
    """When contradiction_evidence is None, severity must be NONE."""
    stu_prop = _make_prop("A primary key contains numbers.", "primary key", "contain", "number")
    ref_prop = _make_prop("A primary key uniquely identifies records.", "primary key", "identify", "record")

    res = estimator.estimate(None, stu_prop, [ref_prop], domain="PRIMARY_KEY")
    assert res.severity == SeverityLevel.NONE
    assert res.severity_score == 0.0


# ----------------------------------------------------------------------------
# 2. Minor vs Moderate vs Core Classification
# ----------------------------------------------------------------------------
def test_pk_severity_levels(estimator):
    """Verifies correct separation of MINOR, MODERATE, and CORE on Primary Key."""
    ref_prop = _make_prop("A primary key uniquely identifies each record in a table.", "primary key", "identify", "record")

    # Core: Duplicate values
    stu_core = _make_prop("A primary key can contain duplicate values.", "primary key", "contain", "value")
    ev_core = ContradictionEvidence(
        is_contradicted=True,
        contradiction_type=ContradictionType.VALUE_CONFLICT,
        conflicting_entity="primary key",
        conflicting_property="uniqueness",
        conflicting_value="duplicate",
        evidence_strength=0.90,
        explanation="Conflict on uniqueness.",
    )
    res_core = estimator.estimate(ev_core, stu_core, [ref_prop], domain="PRIMARY_KEY")
    assert res_core.severity == SeverityLevel.CORE_CONTRADICTION
    assert res_core.severity_score == 1.00

    # Moderate: Multiple primary keys
    stu_mod = _make_prop("A table can define multiple primary keys simultaneously.", "table", "define", "key")
    ev_mod = ContradictionEvidence(
        is_contradicted=True,
        contradiction_type=ContradictionType.VALUE_CONFLICT,
        conflicting_entity="primary key",
        conflicting_property="multiple primary keys",
        conflicting_value="multiple",
        evidence_strength=0.75,
        explanation="Relational cardinality confusion.",
    )
    res_mod = estimator.estimate(ev_mod, stu_mod, [ref_prop], domain="PRIMARY_KEY")
    assert res_mod.severity == SeverityLevel.MODERATE
    assert res_mod.severity_score == 0.60

    # Minor: Naming convention
    stu_min = _make_prop("A primary key is always named ID in database schemas.", "primary key", "name", "id")
    ev_min = ContradictionEvidence(
        is_contradicted=True,
        contradiction_type=ContradictionType.VALUE_CONFLICT,
        conflicting_entity="primary key",
        conflicting_property="naming",
        conflicting_value="id",
        evidence_strength=0.65,
        explanation="Naming convention error.",
    )
    res_min = estimator.estimate(ev_min, stu_min, [ref_prop], domain="PRIMARY_KEY")
    assert res_min.severity == SeverityLevel.MINOR
    assert res_min.severity_score == 0.25


def test_bst_severity_levels(estimator):
    """Verifies correct separation of MINOR, MODERATE, and CORE on BST."""
    ref_prop = _make_prop("A binary search tree stores smaller values in the left subtree.", "binary search tree", "store", "value")

    # Core: Ordering reversal
    stu_core = _make_prop("A binary search tree places larger values in the left subtree.", "binary search tree", "place", "value")
    ev_core = ContradictionEvidence(
        is_contradicted=True,
        contradiction_type=ContradictionType.VALUE_CONFLICT,
        conflicting_entity="binary search tree",
        conflicting_property="relative_size",
        conflicting_value="larger",
        evidence_strength=0.90,
        explanation="Ordering conflict.",
    )
    res_core = estimator.estimate(ev_core, stu_core, [ref_prop], domain="BST")
    assert res_core.severity == SeverityLevel.CORE_CONTRADICTION
    assert res_core.severity_score == 1.00

    # Moderate: Random inorder traversal
    stu_mod = _make_prop("A binary search tree inorder traversal yields random order.", "binary search tree", "yield", "order")
    ev_mod = ContradictionEvidence(
        is_contradicted=True,
        contradiction_type=ContradictionType.VALUE_CONFLICT,
        conflicting_entity="binary search tree",
        conflicting_property="traversal",
        conflicting_value="random",
        evidence_strength=0.75,
        explanation="Traversal disorder.",
    )
    res_mod = estimator.estimate(ev_mod, stu_mod, [ref_prop], domain="BST")
    assert res_mod.severity == SeverityLevel.MODERATE
    assert res_mod.severity_score == 0.60

    # Minor: Pointer count
    stu_min = _make_prop("A binary search tree always requires four pointers per node.", "binary search tree", "require", "pointer")
    ev_min = ContradictionEvidence(
        is_contradicted=True,
        contradiction_type=ContradictionType.VALUE_CONFLICT,
        conflicting_entity="binary search tree",
        conflicting_property="pointers",
        conflicting_value="four",
        evidence_strength=0.65,
        explanation="Pointer count trivia.",
    )
    res_min = estimator.estimate(ev_min, stu_min, [ref_prop], domain="BST")
    assert res_min.severity == SeverityLevel.MINOR
    assert res_min.severity_score == 0.25


def test_compiler_severity_levels(estimator):
    """Verifies correct separation of MINOR, MODERATE, and CORE on Compiler."""
    ref_prop = _make_prop("A compiler translates source code into machine code.", "compiler", "translate", "code")

    # Core: Explicit negation of translate
    stu_core = _make_prop("A compiler does not translate source code.", "compiler", "translate", "code")
    ev_core = ContradictionEvidence(
        is_contradicted=True,
        contradiction_type=ContradictionType.EXPLICIT_NEGATION,
        conflicting_entity="compiler",
        conflicting_property="translate",
        conflicting_value="negative",
        evidence_strength=0.85,
        explanation="Explicit negation.",
    )
    res_core = estimator.estimate(ev_core, stu_core, [ref_prop], domain="COMPILER")
    assert res_core.severity == SeverityLevel.CORE_CONTRADICTION
    assert res_core.severity_score == 1.00

    # Moderate: Interprets line by line
    stu_mod = _make_prop("A compiler interprets code line by line at runtime.", "compiler", "interpret", "code")
    ev_mod = ContradictionEvidence(
        is_contradicted=True,
        contradiction_type=ContradictionType.VALUE_CONFLICT,
        conflicting_entity="compiler",
        conflicting_property="line by line",
        conflicting_value="interpreter",
        evidence_strength=0.75,
        explanation="Execution model confusion.",
    )
    res_mod = estimator.estimate(ev_mod, stu_mod, [ref_prop], domain="COMPILER")
    assert res_mod.severity == SeverityLevel.MODERATE
    assert res_mod.severity_score == 0.60

    # Minor: .exe file extension
    stu_min = _make_prop("A compiler always generates output files with exe extension.", "compiler", "generate", "file")
    ev_min = ContradictionEvidence(
        is_contradicted=True,
        contradiction_type=ContradictionType.VALUE_CONFLICT,
        conflicting_entity="compiler",
        conflicting_property="extension",
        conflicting_value="exe",
        evidence_strength=0.65,
        explanation="Platform extension trivia.",
    )
    res_min = estimator.estimate(ev_min, stu_min, [ref_prop], domain="COMPILER")
    assert res_min.severity == SeverityLevel.MINOR
    assert res_min.severity_score == 0.25


# ----------------------------------------------------------------------------
# 3. Entity Specificity & Confused Entities (Adversarial)
# ----------------------------------------------------------------------------
def test_foreign_key_entity_confusion_not_core_pk_contradiction(estimator):
    """
    A statement predicated of 'foreign key' must not receive CORE_CONTRADICTION
    merely because vocabulary overlaps with primary key.
    """
    ref_prop = _make_prop("A primary key uniquely identifies records.", "primary key", "identify", "record")
    stu_prop = _make_prop("A foreign key can contain duplicate values.", "foreign key", "contain", "value")

    ev = ContradictionEvidence(
        is_contradicted=True,
        contradiction_type=ContradictionType.VALUE_CONFLICT,
        conflicting_entity="foreign key",
        conflicting_property="uniqueness",
        conflicting_value="duplicate",
        evidence_strength=0.90,
        explanation="Foreign key duplicates.",
    )

    res = estimator.estimate(ev, stu_prop, [ref_prop], domain="PRIMARY_KEY")
    assert res.severity == SeverityLevel.UNRESOLVED
    assert not res.evidence.entity_grounded
    assert "foreign key" in res.explanation.lower()


def test_general_binary_tree_not_core_bst_contradiction(estimator):
    """
    General binary tree must not be conflated with binary search tree.
    """
    ref_prop = _make_prop("A binary search tree stores smaller values in left subtree.", "binary search tree", "store", "value")
    stu_prop = _make_prop("A general binary tree must store smaller values in the left subtree.", "binary tree", "store", "value")

    ev = ContradictionEvidence(
        is_contradicted=True,
        contradiction_type=ContradictionType.VALUE_CONFLICT,
        conflicting_entity="binary tree",
        conflicting_property="ordering",
        conflicting_value="smaller",
        evidence_strength=0.85,
        explanation="Ordering constraint on general tree.",
    )

    res = estimator.estimate(ev, stu_prop, [ref_prop], domain="BST")
    assert res.severity == SeverityLevel.UNRESOLVED
    assert not res.evidence.entity_grounded


def test_interpreter_not_core_compiler_contradiction(estimator):
    """
    An assertion about an interpreter must not be escalated to core compiler contradiction.
    """
    ref_prop = _make_prop("A compiler translates source code into machine code.", "compiler", "translate", "code")
    stu_prop = _make_prop("An interpreter compiles source code into machine files.", "interpreter", "compile", "file")

    ev = ContradictionEvidence(
        is_contradicted=True,
        contradiction_type=ContradictionType.VALUE_CONFLICT,
        conflicting_entity="interpreter",
        conflicting_property="translation",
        conflicting_value="compile",
        evidence_strength=0.85,
        explanation="Interpreter compilation claim.",
    )

    res = estimator.estimate(ev, stu_prop, [ref_prop], domain="COMPILER")
    assert res.severity == SeverityLevel.UNRESOLVED
    assert not res.evidence.entity_grounded


# ----------------------------------------------------------------------------
# 4. Determinism & Provenance
# ----------------------------------------------------------------------------
def test_severity_estimation_is_strictly_deterministic(estimator):
    """Multiple invocations on identical inputs must yield identical results."""
    ref_prop = _make_prop("A primary key uniquely identifies records.", "primary key", "identify", "record")
    stu_prop = _make_prop("A primary key can contain duplicate values.", "primary key", "contain", "value")

    ev = ContradictionEvidence(
        is_contradicted=True,
        contradiction_type=ContradictionType.VALUE_CONFLICT,
        conflicting_entity="primary key",
        conflicting_property="uniqueness",
        conflicting_value="duplicate",
        evidence_strength=0.90,
        explanation="Conflict on uniqueness.",
    )

    res1 = estimator.estimate(ev, stu_prop, [ref_prop], domain="PRIMARY_KEY")
    res2 = estimator.estimate(ev, stu_prop, [ref_prop], domain="PRIMARY_KEY")

    assert res1.severity == res2.severity
    assert res1.severity_score == res2.severity_score
    assert res1.explanation == res2.explanation
    assert res1.evidence.to_dict() == res2.evidence.to_dict()


def test_provenance_contains_structured_rationale(estimator):
    """Result must contain itemized reasons and structured evidence."""
    ref_prop = _make_prop("A primary key uniquely identifies records.", "primary key", "identify", "record")
    stu_prop = _make_prop("A primary key can contain duplicate values.", "primary key", "contain", "value")

    ev = ContradictionEvidence(
        is_contradicted=True,
        contradiction_type=ContradictionType.VALUE_CONFLICT,
        conflicting_entity="primary key",
        conflicting_property="uniqueness",
        conflicting_value="duplicate",
        evidence_strength=0.90,
        explanation="Conflict on uniqueness.",
    )

    res = estimator.estimate(ev, stu_prop, [ref_prop], domain="PRIMARY_KEY")
    ev_dict = res.evidence.to_dict()

    assert "is_contradicted" in ev_dict
    assert "entity_grounded" in ev_dict
    assert "defining_property_target" in ev_dict
    assert len(ev_dict["rationale_reasons"]) > 0


# ----------------------------------------------------------------------------
# 5. Non-Circularity & Production Scorer Integrity
# ----------------------------------------------------------------------------
def test_non_circularity_severity_independent_of_scoring(estimator):
    """
    Severity estimator must function completely independently of scoring models,
    without importing or calling BoundedScorer or final grade values.
    """
    ref_prop = _make_prop("A compiler translates source code.", "compiler", "translate", "code")
    stu_prop = _make_prop("A compiler does not translate source code.", "compiler", "translate", "code")

    ev = ContradictionEvidence(
        is_contradicted=True,
        contradiction_type=ContradictionType.EXPLICIT_NEGATION,
        conflicting_entity="compiler",
        conflicting_property="translate",
        conflicting_value="negative",
        evidence_strength=0.85,
        explanation="Negation.",
    )

    # Estimator does not take any score argument
    res = estimator.estimate(ev, stu_prop, [ref_prop], domain="COMPILER")
    assert res.severity == SeverityLevel.CORE_CONTRADICTION


def test_production_scorer_remains_frozen():
    """Verify that BoundedScorer parameters remain strictly at production defaults."""
    scorer = BoundedScorer()
    assert scorer.max_positive_bonus == 0.30
    assert scorer.max_negative_penalty == 0.40
    assert scorer.diminishing_rate == 0.50
