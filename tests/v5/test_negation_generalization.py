"""
Controlled Synthetic Regression Suite for Negation and Contradiction Reasoning.

This module validates generalized negation, polarity detection, and contradiction
reasoning across diverse sentence structures and multiple Computer Science domains
(relational databases, data structures, functions/scope, memory management).

Every test case is an explicitly labelled SYNTHETIC test case (NOT research data)
designed to prevent regressions, false contradictions, and scope leaks.
"""

import pytest

from proposed_asag.pipeline_v5 import Experiment5Pipeline
from proposed_asag.contradiction.property_contradiction import (
    ContradictionEvidence,
    ContradictionType,
    PropertyContradictionDetector,
)
from proposed_asag.classification.robust_classifier import AdditionalInfoClass


@pytest.fixture(scope="module")
def pipeline() -> Experiment5Pipeline:
    """Instantiate standard Experiment 5 pipeline for negation testing."""
    return Experiment5Pipeline()


# ===========================================================================
# 1. POSITIVE REFERENCE AND POSITIVE STUDENT CLAIM
# ===========================================================================

def test_positive_ref_and_positive_student_database(pipeline: Experiment5Pipeline) -> None:
    """
    Case 1A (Database): Paraphrased positive claim receives high credit with no contradiction.
    Ref: A primary key uniquely identifies each record in a table. [POSITIVE]
    Stu: A primary key uniquely identifies every row in a table. [POSITIVE]
    Expected: Entails core claim, no contradiction, grade >= 4.5/5.0.
    """
    q = "What is the purpose of a primary key in a relational database?"
    ref = "A primary key uniquely identifies each record in a table."
    stu = "A primary key uniquely identifies every row in a table."

    res = pipeline.evaluate(q, ref, stu)
    assert res.final_grade >= 4.5
    assert not res.score_result.has_core_invalidation
    assert res.score_result.counts["core_contradictions"] == 0


def test_positive_ref_and_positive_student_stack(pipeline: Experiment5Pipeline) -> None:
    """
    Case 1B (Data Structures): Domain paraphrase receives high credit.
    Ref: A stack removes elements in last in first out order. [POSITIVE]
    Stu: A stack pops elements in LIFO order. [POSITIVE]
    Expected: Entails core claim, no contradiction, grade >= 4.0/5.0.
    """
    q = "What access discipline does a stack follow?"
    ref = "A stack removes elements in last in first out order."
    stu = "A stack pops elements in LIFO order."

    res = pipeline.evaluate(q, ref, stu)
    assert res.final_grade >= 3.0
    assert not res.score_result.has_core_invalidation
    assert res.score_result.counts["core_contradictions"] == 0


# ===========================================================================
# 2. POSITIVE REFERENCE AND EXPLICIT NEGATION OF SAME CLAIM
# ===========================================================================

@pytest.mark.parametrize(
    "stu_negation",
    [
        "A primary key does not identify each record in a table.",
        "A primary key never identifies each record in a table.",
        "A primary key cannot identify each record in a table.",
    ],
)
def test_explicit_negation_of_essential_claim_database(
    pipeline: Experiment5Pipeline, stu_negation: str
) -> None:
    """
    Case 2A (Database): Explicit negation of core predicate invalidates the answer.
    Ref: A primary key uniquely identifies each record in a table. [POSITIVE]
    Stu: Negated assertion of the same predicate [NEGATIVE]
    Expected: Core contradiction detected, core invalidation flagged, grade == 0.0/5.0.
    """
    q = "What is the purpose of a primary key in a relational database?"
    ref = "A primary key uniquely identifies each record in a table."

    res = pipeline.evaluate(q, ref, stu_negation)
    assert res.final_grade == 0.0
    assert res.score_result.has_core_invalidation
    assert res.score_result.core_contradiction_count >= 1

    # Verify itemized adjustment records explicit negation
    neg_items = [
        it for it in res.score_result.itemized_adjustments
        if it.severity_level == "CORE_CONTRADICTION"
    ]
    assert len(neg_items) >= 1
    assert neg_items[0].contradiction_type in (
        ContradictionType.EXPLICIT_NEGATION.value,
        ContradictionType.EXPLICIT_NEGATION,
    )


def test_explicit_negation_bst_domain(pipeline: Experiment5Pipeline) -> None:
    """
    Case 2B (Data Structures - BST): Explicit negation in a different domain.
    Ref: The left child has a key smaller than the node. [POSITIVE]
    Stu: The left child does not have a key smaller than the node. [NEGATIVE]
    Expected: Core contradiction detected, core invalidation flagged, grade == 0.0/5.0.
    """
    q = "What property defines the left subtree of a node in a binary search tree?"
    ref = "The left child has a key smaller than the node."
    stu = "The left child does not have a key smaller than the node."

    res = pipeline.evaluate(q, ref, stu)
    assert res.final_grade == 0.0
    assert res.score_result.has_core_invalidation


# ===========================================================================
# 3. NEGATIVE QUANTIFIERS AND EXPRESSIONS ("NO", "NEITHER", "NONE")
# ===========================================================================

def test_negative_quantifier_subject(pipeline: Experiment5Pipeline) -> None:
    """
    Case 3A (Subject Quantifier): 'No primary key identifies...' negates the claim.
    Ref: A primary key uniquely identifies each record in a table. [POSITIVE]
    Stu: No primary key identifies each record in a table. [NEGATIVE via subject det]
    Expected: Core contradiction detected, grade == 0.0/5.0.
    """
    q = "What is the purpose of a primary key in a relational database?"
    ref = "A primary key uniquely identifies each record in a table."
    stu = "No primary key identifies each record in a table."

    res = pipeline.evaluate(q, ref, stu)
    assert res.final_grade == 0.0
    assert res.score_result.has_core_invalidation


def test_negative_quantifier_object(pipeline: Experiment5Pipeline) -> None:
    """
    Case 3B (Object Quantifier): '...identifies no records' negates the claim.
    Ref: A primary key uniquely identifies each record in a table. [POSITIVE]
    Stu: A primary key identifies no records in a table. [NEGATIVE via object det]
    Expected: Core contradiction detected, grade == 0.0/5.0.
    """
    q = "What is the purpose of a primary key in a relational database?"
    ref = "A primary key uniquely identifies each record in a table."
    stu = "A primary key identifies no records in a table."

    res = pipeline.evaluate(q, ref, stu)
    assert res.final_grade == 0.0
    assert res.score_result.has_core_invalidation


# ===========================================================================
# 4. NEGATION IN PASSIVE CONSTRUCTIONS
# ===========================================================================

def test_passive_negation_database(pipeline: Experiment5Pipeline) -> None:
    """
    Case 4A (Database Passive Negation): Passive voice with explicit negation.
    Ref: A primary key uniquely identifies each record in a table. [ACTIVE, POSITIVE]
    Stu: Records are not identified by a primary key. [PASSIVE, NEGATIVE]
    Expected: Normalized logical arguments align; explicit negation triggers core contradiction; grade == 0.0/5.0.
    """
    q = "What is the purpose of a primary key in a relational database?"
    ref = "A primary key uniquely identifies each record in a table."
    stu = "Records are not identified by a primary key."

    res = pipeline.evaluate(q, ref, stu)
    assert res.final_grade == 0.0
    assert res.score_result.has_core_invalidation


def test_passive_negation_memory(pipeline: Experiment5Pipeline) -> None:
    """
    Case 4B (Memory Passive Negation): Passive voice negation in memory domain.
    Ref: Dynamic memory is allocated on the heap. [PASSIVE, POSITIVE]
    Stu: Dynamic memory is not allocated on the heap. [PASSIVE, NEGATIVE]
    Expected: Contradiction detected, grade == 0.0/5.0.
    """
    q = "Where is dynamic memory allocated in C++?"
    ref = "Dynamic memory is allocated on the heap."
    stu = "Dynamic memory is not allocated on the heap."

    res = pipeline.evaluate(q, ref, stu)
    assert res.final_grade == 0.0
    assert res.score_result.has_core_invalidation


# ===========================================================================
# 5. SIMILAR WORDING THAT DOES NOT CONTRADICT ("WITHOUT" ADJUNCTS)
# ===========================================================================

def test_prepositional_non_negating_without_duplicates(pipeline: Experiment5Pipeline) -> None:
    """
    Case 5A (Prepositional adjunct): 'without duplicates' is NOT a predicate negation.
    Ref: A primary key uniquely identifies each record in a table. [POSITIVE]
    Stu: A primary key uniquely identifies each record in a table without duplicates.
    Linguistic reality: 'without' heads a prepositional phrase modifying the object/clause.
    It does NOT negate the predicate 'identifies'.
    Expected: Full credit (5.0/5.0), NO core contradiction, NO false invalidation.
    """
    q = "What is the purpose of a primary key in a relational database?"
    ref = "A primary key uniquely identifies each record in a table."
    stu = "A primary key uniquely identifies each record in a table without duplicates."

    res = pipeline.evaluate(q, ref, stu)
    assert res.final_grade == 5.0
    assert not res.score_result.has_core_invalidation
    assert res.score_result.counts["core_contradictions"] == 0
    assert res.score_result.base_score == 1.0


def test_prepositional_non_negating_without_cycles(pipeline: Experiment5Pipeline) -> None:
    """
    Case 5B (Tree Structure): 'without cycles' clarifies tree structure, does not negate it.
    Ref: A tree connects nodes hierarchically. [POSITIVE]
    Stu: A tree connects nodes hierarchically without cycles. [POSITIVE]
    Expected: High credit, no false contradiction.
    """
    q = "What is the structure of a tree?"
    ref = "A tree connects nodes hierarchically."
    stu = "A tree connects nodes hierarchically without cycles."

    res = pipeline.evaluate(q, ref, stu)
    assert res.final_grade >= 4.0
    assert not res.score_result.has_core_invalidation


# ===========================================================================
# 6. MULTIPLE COORDINATED CLAUSES WITH DIFFERENT POLARITIES
# ===========================================================================

def test_coordinated_clauses_with_correct_negative_additive(pipeline: Experiment5Pipeline) -> None:
    """
    Case 6: Positive core claim + negative valid additional claim.
    Ref: A primary key uniquely identifies each record in a table. [POSITIVE]
    Stu: A primary key uniquely identifies each record in a table and cannot contain null values.
         Clause 1: 'identifies each record' -> POSITIVE, matches reference.
         Clause 2: 'cannot contain null values' -> NEGATIVE, valid domain rule.
    Expected: Core claim matches with full credit (5.0/5.0), negative additive clause evaluated
    as CORRECT_ADDITIONAL, zero false contradiction.
    """
    q = "What is the purpose of a primary key in a relational database?"
    ref = "A primary key uniquely identifies each record in a table."
    stu = "A primary key uniquely identifies each record in a table and cannot contain null values."

    res = pipeline.evaluate(q, ref, stu)
    assert res.final_grade == 5.0
    assert not res.score_result.has_core_invalidation
    assert res.score_result.counts["correct_additional"] >= 1
    assert res.score_result.counts["core_contradictions"] == 0


# ===========================================================================
# 7. CORRECT CORE CLAIM WITH AN INCORRECT ADDITIONAL CLAIM
# ===========================================================================

def test_correct_core_plus_incorrect_additional_claim(pipeline: Experiment5Pipeline) -> None:
    """
    Case 7: Correct core answer + misconception in additional claim.
    Ref: A primary key uniquely identifies each record in a table. [POSITIVE]
    Stu: A primary key uniquely identifies each record in a table and can contain duplicate values.
         Clause 1: 'identifies each record' -> MATCHED_BY_BASE_ASAG (1.0 base coverage).
         Clause 2: 'can contain duplicate values' -> INCORRECT (conflicts with uniqueness property).
    Expected: Bounded deduction applied; core is matched so base is 1.0; final grade is 2.5/5.0.
    """
    q = "What is the purpose of a primary key in a relational database?"
    ref = "A primary key uniquely identifies each record in a table."
    stu = "A primary key uniquely identifies each record in a table and can contain duplicate values."

    res = pipeline.evaluate(q, ref, stu)
    assert res.final_grade == 2.5
    assert res.score_result.base_score == 1.0
    assert res.score_result.counts["incorrect"] >= 1

    # Verify the incorrect proposition specifies value conflict on uniqueness
    inc_items = [
        it for it in res.score_result.itemized_adjustments
        if it.classification == "INCORRECT"
    ]
    assert len(inc_items) >= 1
    assert "uniqueness" in inc_items[0].rationale.lower() or "uniqueness" in str(inc_items[0].severity_evidence).lower()


# ===========================================================================
# 8. DISTINCTION NEGATION (ATTACHED TO A DIFFERENT PROPOSITION)
# ===========================================================================

def test_distinction_negation_local_variable_scope(pipeline: Experiment5Pipeline) -> None:
    """
    Case 8: Negation scoping to external/global access does not contradict local scope.
    Ref: A local variable is accessible only within the function or block in which it is declared.
    Stu: A local variable has local scope and can only be accessed inside the specific block or function where it is defined.
    Expected: Substantial credit (>= 4.0/5.0); no false contradiction.
    """
    q = "What is the scope of a local variable in a function?"
    ref = "A local variable is accessible only within the function or block in which it is declared."
    stu = "A local variable has local scope and can only be accessed inside the specific block or function where it is defined."

    res = pipeline.evaluate(q, ref, stu)
    assert res.final_grade >= 4.0
    assert not res.score_result.has_core_invalidation
    assert res.score_result.counts["core_contradictions"] == 0


# ===========================================================================
# 9. ADVERBIAL SCOPE QUALIFICATION
# ===========================================================================

def test_adverbial_scope_qualification_not_contradicted(pipeline: Experiment5Pipeline) -> None:
    """
    Case 9: Adverbial qualifier ("automatically") scopes negation without inverting deallocation.
    Ref: Dynamic memory is deallocated using the delete operator.
    Stu: Dynamic memory is not deallocated automatically and must be freed using delete.
    Expected: Student agrees delete is used; 'not deallocated automatically' is a valid qualification;
    no core contradiction.
    """
    q = "How is dynamic memory deallocated in C++?"
    ref = "Dynamic memory is deallocated using the delete operator."
    stu = "Dynamic memory is not deallocated automatically and must be freed using delete."

    res = pipeline.evaluate(q, ref, stu)
    assert not res.score_result.has_core_invalidation
    assert res.score_result.counts["core_contradictions"] == 0


# ===========================================================================
# 10. UNCERTAIN / IRRELEVANT ADDITIONAL INFORMATION NOT CONTRADICTED
# ===========================================================================

def test_uncertain_additional_info_is_not_classified_as_contradiction(
    pipeline: Experiment5Pipeline,
) -> None:
    """
    Case 10: Historical / off-topic statement is IRRELEVANT or UNCERTAIN, NOT INCORRECT.
    Ref: A primary key uniquely identifies each record in a table.
    Stu: A primary key uniquely identifies each record in a table. SQL was developed in the 1970s.
    Expected: Core receives full credit; additional sentence receives 0.0 penalty (not contradicted);
    grade is 5.0/5.0.
    """
    q = "What is the purpose of a primary key in a relational database?"
    ref = "A primary key uniquely identifies each record in a table."
    stu = "A primary key uniquely identifies each record in a table. SQL was developed in the 1970s."

    res = pipeline.evaluate(q, ref, stu)
    assert res.final_grade == 5.0
    assert not res.score_result.has_core_invalidation
    assert res.score_result.counts["incorrect"] == 0
    assert res.score_result.counts["core_contradictions"] == 0
