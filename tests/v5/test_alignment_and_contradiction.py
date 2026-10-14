"""
Task 3 Regression Suite: Proposition Alignment and Contradiction Reliability.

Validates the focused interventions for:
1. Global deterministic greedy 1-to-1 matching without sequential artifacting.
2. Argument double-dipping prevention in argument fulfillment.
3. Prepositional and containment converse relational equivalence.
4. Negative contrasts rejecting non-converse reversals.
5. Incompatible entity qualifier isolation (e.g. primary key vs foreign key).
6. Prepositional target-aware explicit negation contradiction detection.
7. Same-entity property value conflict detection.
"""

import pytest

from base_asag.dependency.parser import DependencyParser
from base_asag.representation.hybrid import RobustPropositionExtractor
from proposed_asag.contradiction.property_contradiction import (
    ContradictionEvidence,
    ContradictionType,
    PropertyContradictionDetector,
)
from proposed_asag.pipeline_v5 import Experiment5Pipeline
from proposed_asag.proposition.canonical_reference import CanonicalReferenceExtractor
from proposed_asag.proposition.core_recovery.core_paraphrase_recovery import (
    CoreParaphraseRecoverer,
)


@pytest.fixture(scope="module")
def parser():
    return DependencyParser()


@pytest.fixture(scope="module")
def extractor():
    return RobustPropositionExtractor()


@pytest.fixture(scope="module")
def recoverer():
    return CoreParaphraseRecoverer()


@pytest.fixture(scope="module")
def detector():
    return PropertyContradictionDetector()


@pytest.fixture(scope="module")
def pipeline():
    return Experiment5Pipeline()


# ============================================================================
# 1. Global Deterministic Greedy 1-to-1 Matching
# ============================================================================
def test_global_deterministic_greedy_matching_precedence(parser, extractor, recoverer):
    """
    Test that global sorting by (-score, r_idx, s_idx) ensures a strongly-matching
    student proposition wins over a weakly-matching student proposition, regardless of
    student proposition order.
    """
    ref_text = "The cache decreases memory latency."
    # stu 0: weak match, stu 1: strong exact paraphrase
    stu_text_weak_first = "The cache minimizes delay. The cache reduces memory latency."
    
    ref_doc = parser.parse_document(ref_text)
    stu_doc = parser.parse_document(stu_text_weak_first)
    
    ref_props = extractor.extract_document(ref_doc, ref_text)
    stu_props = extractor.extract_document(stu_doc, stu_text_weak_first)
    
    res = recoverer.recover(
        unmatched_student_props=stu_props,
        reference_props=ref_props,
        matched_reference_indices=set(),
    )
    
    assert res.recovered_count == 1
    recovered_rec = res.recovered_propositions[0]
    # The stronger proposition (reduces memory latency) should be recovered
    assert "reduce" in recovered_rec.student_proposition.source_text or "reduces" in recovered_rec.student_proposition.source_text
    assert recovered_rec.confidence >= 0.80


# ============================================================================
# 2. Argument Double-Dipping Prevention
# ============================================================================
def test_argument_double_dipping_prevention(parser, extractor, recoverer):
    """
    Test that a single student prepositional argument cannot satisfy multiple
    distinct unfulfilled reference propositions.
    """
    # Student answers with one instrumental argument
    stu_text = "Memory is deallocated using delete."
    # Two reference fragments both looking for 'delete'
    ref_text = "Free memory using delete. Release resources using delete."
    
    stu_doc = parser.parse_document(stu_text)
    ref_doc = parser.parse_document(ref_text)
    
    stu_props = extractor.extract_document(stu_doc, stu_text)
    ref_props = extractor.extract_document(ref_doc, ref_text)
    
    recovered = recoverer.recover_argument_fulfilled_references(
        matched_student_props=stu_props,
        reference_props=ref_props,
        matched_reference_indices=set(),
    )
    
    # At most 1 reference should be fulfilled by the single prep argument
    assert len(recovered) <= 1


# ============================================================================
# 3. Prepositional Converse Equivalence & Negative Contrast
# ============================================================================
def test_prepositional_converse_positive(pipeline):
    """'Block A is above Block B' <=> 'Block B is below Block A' receives full credit."""
    res = pipeline.evaluate(
        question="Describe the positions of the blocks.",
        reference_answer="Block A is above Block B.",
        student_answer="Block B is below Block A.",
    )
    assert res.base_score_effective >= 0.90
    assert res.final_grade >= 4.5


def test_prepositional_converse_negative_contrast(pipeline):
    """Non-converse reversal 'Block B is above Block A' receives zero credit."""
    res = pipeline.evaluate(
        question="Describe the positions of the blocks.",
        reference_answer="Block A is above Block B.",
        student_answer="Block B is above Block A.",
    )
    assert res.base_score_effective == 0.0
    assert res.final_grade == 0.0


# ============================================================================
# 4. Containment Converse Equivalence & Negative Contrast
# ============================================================================
def test_containment_converse_positive(pipeline):
    """'The array contains elements' <=> 'Elements are in the array' receives full credit."""
    res = pipeline.evaluate(
        question="What does an array store?",
        reference_answer="The array contains elements.",
        student_answer="Elements are in the array.",
    )
    assert res.base_score_effective >= 0.90
    assert res.final_grade >= 4.5


def test_containment_converse_negative_contrast(pipeline):
    """Inverted containment 'The array is in elements' receives zero credit."""
    res = pipeline.evaluate(
        question="What does an array store?",
        reference_answer="The array contains elements.",
        student_answer="The array is in elements.",
    )
    assert res.base_score_effective == 0.0
    assert res.final_grade == 0.0


# ============================================================================
# 5. Comparative Converse Equivalence & Negative Contrast
# ============================================================================
def test_comparative_converse_positive(pipeline):
    """'The stack is smaller than the queue' <=> 'The queue is larger than the stack' receives full credit."""
    res = pipeline.evaluate(
        question="Compare the sizes of the stack and the queue.",
        reference_answer="The stack is smaller than the queue.",
        student_answer="The queue is larger than the stack.",
    )
    assert res.base_score_effective >= 0.90
    assert res.final_grade >= 4.5


def test_comparative_converse_negative_contrast(pipeline):
    """Reversed comparative 'The queue is smaller than the stack' receives zero credit."""
    res = pipeline.evaluate(
        question="Compare the sizes of the stack and the queue.",
        reference_answer="The stack is smaller than the queue.",
        student_answer="The queue is smaller than the stack.",
    )
    assert res.base_score_effective == 0.0
    assert res.final_grade == 0.0


# ============================================================================
# 6. Incompatible Entity Qualifier Isolation (Primary vs Foreign Key)
# ============================================================================
def test_incompatible_entity_qualifier_isolation(pipeline):
    """
    Student answering about a foreign key having duplicate values must NOT
    match the primary key reference answer, and must receive 0.0.
    """
    res = pipeline.evaluate(
        question="What is a primary key?",
        reference_answer="A primary key contains unique values.",
        student_answer="A foreign key can contain duplicate values.",
    )
    assert res.base_score_effective == 0.0
    assert res.final_grade == 0.0


def test_incompatible_entity_qualifier_no_cross_contradiction(parser, extractor, detector):
    """
    A foreign key containing duplicate values is NOT a factual contradiction of
    a primary key containing unique values because the entities are distinct.
    """
    ref_doc = parser.parse_document("A primary key contains unique values.")
    stu_doc = parser.parse_document("A foreign key can contain duplicate values.")
    
    ref_props = extractor.extract_document(ref_doc, "A primary key contains unique values.")
    stu_props = extractor.extract_document(stu_doc, "A foreign key can contain duplicate values.")
    
    ev = detector.detect_contradiction(stu_props[0], ref_props)
    assert ev.is_contradicted is False


# ============================================================================
# 7. Prepositional Target-Aware Negation & Contradiction Detection
# ============================================================================
def test_explicit_negation_different_preposition_target(pipeline):
    """
    'Local variables are not allocated on the heap' does NOT contradict
    'Local variables are allocated on the stack'. It should receive 0 credit
    neutrally (UNCERTAIN) without contradiction penalty.
    """
    res = pipeline.evaluate(
        question="Where are local variables stored?",
        reference_answer="Local variables are allocated on the stack.",
        student_answer="Local variables are not allocated on the heap.",
    )
    assert res.base_score_effective == 0.0
    assert res.final_grade == 0.0
    # Verify no core contradiction penalty was applied
    assert res.score_result.has_core_invalidation is False
    assert res.score_result.counts.get("core_contradictions", 0) == 0


def test_explicit_negation_same_preposition_target(detector, parser, extractor):
    """
    'Local variables are not allocated on the stack' DOES directly contradict
    'Local variables are allocated on the stack'.
    """
    ref_doc = parser.parse_document("Local variables are allocated on the stack.")
    stu_doc = parser.parse_document("Local variables are not allocated on the stack.")
    
    ref_props = extractor.extract_document(ref_doc, "Local variables are allocated on the stack.")
    stu_props = extractor.extract_document(stu_doc, "Local variables are not allocated on the stack.")
    
    ev = detector.detect_contradiction(stu_props[0], ref_props)
    assert ev.is_contradicted is True
    assert ev.contradiction_type == ContradictionType.EXPLICIT_NEGATION


def test_property_value_conflict_same_entity(detector, parser, extractor):
    """
    Asserting that a primary key contains duplicate values directly contradicts
    the requirement that a primary key contains unique values.
    """
    ref_doc = parser.parse_document("A primary key contains unique values.")
    stu_doc = parser.parse_document("A primary key can contain duplicate values.")
    
    ref_props = extractor.extract_document(ref_doc, "A primary key contains unique values.")
    stu_props = extractor.extract_document(stu_doc, "A primary key can contain duplicate values.")
    
    ev = detector.detect_contradiction(stu_props[0], ref_props)
    assert ev.is_contradicted is True
    assert ev.contradiction_type == ContradictionType.VALUE_CONFLICT
