"""
Regression Test Suite for Task 8: Preposition & Contradiction Epistemic Fixes.

Verifies the resolution of false contradiction defects in V5 ASAG:
1. Pointer paraphrase (Q6.1): "contains memory address as its value" receives full/high credit,
   while "cannot store a memory address" receives a hard contradiction penalty.
2. Merge sort (Q11.10): "divides in half ... merges" receives substantial credit,
   while "never splits the array" receives a contradiction penalty.
3. Prepositional & locative mutually exclusive opposites:
   - "stored on heap" vs "stored on stack" -> Contradiction.
   - "accessed randomly" vs "accessed sequentially only" -> Contradiction.
4. Spatial opposites:
   - "above threshold" vs "below threshold" -> Contradiction.
   - "inside the loop" vs "outside the loop" -> Contradiction.
5. Scoped negation & multi-clause preservation:
   - Negative clause does not zero out an unrelated valid core requirement.
   - Core credit preserved under neutral or minor preposition differences.
"""

import pytest
from proposed_asag.pipeline_v5 import Experiment5Pipeline, RequirementStatus


@pytest.fixture(scope="module")
def pipeline():
    return Experiment5Pipeline()


# ============================================================================
# 1. Pointer Paraphrase (Mohler Q6.1) Contrastive Pair
# ============================================================================

def test_pointer_valid_paraphrase_high_credit(pipeline):
    """
    Q6.1: Valid student answer using 'as its value' must receive full/high credit (>= 4.0/5.0),
    not zeroed out due to preposition similarity differences.
    """
    q = "What is a pointer?"
    ref = "A variable that contains the address in memory of another variable."
    stu_valid = "A pointer is a variable that contains a memory address as its value."

    res = pipeline.evaluate(q, ref, stu_valid)
    assert res.final_grade >= 4.0, f"Expected >= 4.0, got {res.final_grade}"
    assert res.base_score_effective >= 0.80
    assert res.score_result.has_core_invalidation is False


def test_pointer_contradicted_low_credit(pipeline):
    """
    Q6.1: Contradicted student answer explicitly denying pointer functionality
    must receive a hard contradiction penalty (<= 1.0/5.0).
    """
    q = "What is a pointer?"
    ref = "A variable that contains the address in memory of another variable."
    stu_contradicted = "A pointer is a variable that cannot contain a memory address."

    res = pipeline.evaluate(q, ref, stu_contradicted)
    assert res.final_grade <= 1.0, f"Expected <= 1.0, got {res.final_grade}"
    assert res.score_result.has_core_invalidation is True
    assert res.score_result.counts.get("core_contradictions", 0) >= 1


# ============================================================================
# 2. Merge Sort (Mohler Q11.10) Contrastive Pair
# ============================================================================

def test_merge_sort_valid_paraphrase_substantial_credit(pipeline):
    """
    Q11.10: Merge sort paraphrase with 'divides in half' and 'joins into sorted array'
    must receive substantial partial/full credit (>= 2.0/5.0), resolving the Task 7 defect.
    """
    q = "How does merge sort work?"
    ref = "It splits the original array into two, sorts each of the two halves, and then merges the sorted arrays."
    stu_valid = "Merge sort divides the array in half, sorts each half, and then joins them into one sorted array."

    res = pipeline.evaluate(q, ref, stu_valid)
    assert res.final_grade >= 2.0, f"Expected >= 2.0, got {res.final_grade}"
    assert res.base_score_effective > 0.30
    assert res.score_result.has_core_invalidation is False


def test_merge_sort_contradicted_low_credit(pipeline):
    """
    Q11.10: Contradicted assertion denying splitting receives contradiction penalty.
    """
    q = "How does merge sort work?"
    ref = "It splits the original array into two, sorts each of the two halves, and then merges the sorted arrays."
    stu_contradicted = "Merge sort never splits the array into two."

    res = pipeline.evaluate(q, ref, stu_contradicted)
    assert res.final_grade <= 1.5, f"Expected <= 1.5, got {res.final_grade}"
    assert res.score_result.has_core_invalidation is True


# ============================================================================
# 3. Prepositional & Locative Opposites
# ============================================================================

def test_prepositional_opposite_heap_vs_stack(pipeline):
    """
    'stored on the heap' vs 'stored on the stack' constitutes positive evidence
    of a mutually exclusive storage conflict -> Contradiction / zero grade.
    """
    q = "Where are local variables stored?"
    ref = "Local variables are stored on the stack."
    stu = "Local variables are stored on the heap."

    res = pipeline.evaluate(q, ref, stu)
    assert res.final_grade == 0.0
    assert res.base_score_effective == 0.0
    assert res.score_result.has_core_invalidation is True


def test_prepositional_opposite_random_vs_sequential(pipeline):
    """
    'accessed randomly' vs 'accessed sequentially only' constitutes positive evidence
    of an incompatible access pattern -> Contradiction / zero grade.
    """
    q = "How are elements accessed in an array?"
    ref = "Elements can be accessed randomly."
    stu = "Elements are accessed sequentially only."

    res = pipeline.evaluate(q, ref, stu)
    assert res.final_grade == 0.0
    assert res.base_score_effective == 0.0
    assert res.score_result.has_core_invalidation is True


# ============================================================================
# 4. Spatial Opposites
# ============================================================================

def test_spatial_opposite_above_vs_below(pipeline):
    """
    'above the threshold' vs 'below the threshold' constitutes a directional spatial clash.
    """
    q = "Where are high-priority tasks placed?"
    ref = "High-priority tasks are placed above the threshold."
    stu = "High-priority tasks are placed below the threshold."

    res = pipeline.evaluate(q, ref, stu)
    assert res.final_grade == 0.0
    assert res.base_score_effective == 0.0
    assert res.score_result.has_core_invalidation is True


def test_spatial_opposite_inside_vs_outside_loop(pipeline):
    """
    'declared inside the loop' vs 'declared outside the loop' constitutes a spatial/scope clash.
    """
    q = "Where is the loop counter declared?"
    ref = "The counter is declared inside the loop."
    stu = "The counter is declared outside the loop."

    res = pipeline.evaluate(q, ref, stu)
    assert res.final_grade == 0.0
    assert res.base_score_effective == 0.0
    assert res.score_result.has_core_invalidation is True


# ============================================================================
# 5. Scoped Negation & Multi-Clause Partial Credit Preservation
# ============================================================================

def test_scoped_negation_multi_clause_preserves_core_credit(pipeline):
    """
    A multi-clause answer where one clause correctly satisfies a core requirement
    and another clause makes an additional assertion must preserve partial credit for the core requirement.
    """
    q = "What is the purpose of a primary key?"
    ref = "A primary key uniquely identifies each record in a table."
    # Student satisfies the primary key requirement, but adds an incorrect additional fact about SQL
    stu = "A primary key uniquely identifies each record in a table, and SQL was never developed for databases."

    res = pipeline.evaluate(q, ref, stu)
    # Core credit is preserved; grade is not zeroed out completely
    assert res.base_score_effective >= 0.80
    assert res.final_grade >= 2.0


def test_neutral_preposition_difference_no_false_contradiction(pipeline):
    """
    Low preposition similarity without mutually exclusive opposites must NOT trigger a contradiction.
    """
    q = "What does a compiler do?"
    ref = "A compiler translates source code into machine code."
    # Student uses 'for the processor' instead of 'into machine code'
    stu = "A compiler translates source code for the machine."

    res = pipeline.evaluate(q, ref, stu)
    # Must receive positive credit, not a contradiction
    assert res.base_score_effective > 0.0
    assert res.score_result.has_core_invalidation is False
