"""
Unit tests for Global vs Greedy Proposition Matching (Phase 4).
"""

import pytest
from base_asag.dependency.triples import DependencyRelation
from base_asag.matching.global_matcher import ConfigurableTripleMatcher
from base_asag.matching.triple_matcher import TripleMatcher


def make_relation(subj: str, pred: str, obj: str, idx: int = 0) -> DependencyRelation:
    """Helper to create a DependencyRelation."""
    return DependencyRelation(
        subject=subj,
        predicate=pred,
        object=obj,
        subject_lemma=subj.lower(),
        predicate_lemma=pred.lower(),
        object_lemma=obj.lower() if obj else None,
        relation_type="SPO" if obj else "SP",
        source_dependency_relations=("nsubj", "dobj") if obj else ("nsubj",),
        subject_index=0,
        predicate_index=1,
        object_index=2 if obj else None,
    )


def test_greedy_backward_compatibility():
    """Verify that ConfigurableTripleMatcher in greedy mode matches TripleMatcher results."""
    ref = [make_relation("compiler", "convert", "code")]
    stu = [make_relation("compiler", "convert", "code")]

    greedy_matcher = ConfigurableTripleMatcher(matching_strategy="greedy")
    base_matcher = TripleMatcher()

    res_greedy = greedy_matcher.match(ref, stu)
    res_base = base_matcher.match(ref, stu)

    assert len(res_greedy.matched_relations) == len(res_base.matched_relations)
    assert res_greedy.matched_relations[0].triple_score == res_base.matched_relations[0].triple_score


def test_global_matching_resolves_greedy_collision():
    """
    Demonstrate that global matching optimizes total bipartite alignment where
    a greedy choice would cause a collision and drop a valid relation.

    Setup:
    Reference 0: "key", "identify", "record"
    Reference 1: "key", "contain", "value"

    Student 0: "key", "identify", "row"  (matches Ref 0 strongly ~0.80, Ref 1 moderately ~0.60)
    Student 1: "key", "identify", "record" (matches Ref 0 perfectly 1.0, Ref 1 low ~0.20)
    """
    ref0 = make_relation("key", "identify", "record")
    ref1 = make_relation("key", "contain", "value")

    # Stu 0 matches ref1 with "contain"
    stu0 = make_relation("key", "contain", "value")
    # Stu 1 matches ref0 with "identify"
    stu1 = make_relation("key", "identify", "record")

    matcher_global = ConfigurableTripleMatcher(matching_strategy="global", threshold=0.50)
    res_global = matcher_global.match([ref0, ref1], [stu0, stu1])

    assert len(res_global.matched_relations) == 2
    assert len(res_global.unmatched_reference_relations) == 0
    assert len(res_global.unmatched_student_relations) == 0


def test_global_matching_threshold_enforcement():
    """Test that candidate pairs below the threshold remain unmatched in global matching."""
    ref = [make_relation("compiler", "convert", "code")]
    stu = [make_relation("dog", "bark", "loudly")]

    matcher_global = ConfigurableTripleMatcher(matching_strategy="global", threshold=0.50)
    res = matcher_global.match(ref, stu)

    assert len(res.matched_relations) == 0
    assert len(res.unmatched_reference_relations) == 1
    assert len(res.unmatched_student_relations) == 1


def test_global_empty_inputs():
    """Test that empty inputs are handled cleanly without exceptions."""
    matcher = ConfigurableTripleMatcher(matching_strategy="global")
    res1 = matcher.match([], [make_relation("a", "b", "c")])
    assert len(res1.matched_relations) == 0
    assert len(res1.unmatched_student_relations) == 1

    res2 = matcher.match([make_relation("a", "b", "c")], [])
    assert len(res2.matched_relations) == 0
    assert len(res2.unmatched_reference_relations) == 1


def test_invalid_strategy_raises_error():
    """Test that invalid strategy strings raise ValueError."""
    with pytest.raises(ValueError):
        ConfigurableTripleMatcher(matching_strategy="invalid_strategy")
