"""
Controlled Regression Test Suite for Core Coverage and Partial-Credit Reliability (Task 4).

Validates:
1. Fragment reference answers (prepositional roots, content words, noun-prep complements)
   receive appropriate full credit when fulfilled by student answers.
2. Prevention of proposition over-fragmentation in clausal reference answers (e.g.,
   destructor definitions do not create spurious 50% entity-property requirements).
3. Interpretable Reference Requirement Representation (ReferenceRequirementRecord)
   distinguishing SUPPORTED, PARTIALLY_SUPPORTED, MISSING, CONTRADICTED, and UNCERTAIN.
4. Predictable partial credit for multi-requirement reference answers (1 of 2 requirements -> ~50% credit).
5. Partial credit accompanied by irrelevant information preserves partial credit.
6. Partial credit accompanied by contradiction penalizes without discarding unrelated correct requirements.
7. Full JSON serialization of requirement records.
"""

import json
import pytest

from proposed_asag.pipeline_v5 import (
    Experiment5Pipeline,
    ReferenceRequirementRecord,
    RequirementStatus,
)


@pytest.fixture(scope="module")
def pipeline():
    return Experiment5Pipeline()


# ============================================================================
# 1. Non-Sentential Fragment Reference Fulfillment
# ============================================================================

def test_prepositional_root_fragment_fulfillment(pipeline):
    """Prepositional root reference fragment is fulfilled by student prepositional assertion."""
    q = "Where are local variables stored?"
    ref = "On the stack."
    stu = "Local variables are stored on the stack."

    res = pipeline.evaluate(q, ref, stu)

    assert res.final_grade >= 4.5, f"Expected grade >= 4.5/5, got {res.final_grade}"
    assert len(res.reference_requirements) == 1
    req = res.reference_requirements[0]
    assert req.status == RequirementStatus.SUPPORTED
    assert req.fulfillment_method == "RELATIONAL_FRAGMENT_FULFILLMENT"
    assert req.confidence >= 0.70
    assert req.score_contribution >= 0.90


def test_content_word_fragment_fulfillment(pipeline):
    """Single content word reference fragment is fulfilled by student compound assertion."""
    q = "What data structure operates on a LIFO basis?"
    ref = "A stack."
    stu = "A stack data structure."

    res = pipeline.evaluate(q, ref, stu)

    assert res.final_grade >= 4.5, f"Expected grade >= 4.5/5, got {res.final_grade}"
    assert len(res.reference_requirements) == 1
    req = res.reference_requirements[0]
    assert req.status == RequirementStatus.SUPPORTED
    assert req.fulfillment_method == "RELATIONAL_FRAGMENT_FULFILLMENT"
    assert req.confidence >= 0.70


def test_noun_prep_complement_fragment_fulfillment(pipeline):
    """Noun with prepositional complement reference fragment is fulfilled by student clause."""
    q = "What is the top node of a tree?"
    ref = "Root of tree."
    stu = "The top node is the root of the tree."

    res = pipeline.evaluate(q, ref, stu)

    assert res.final_grade >= 3.5, f"Expected grade >= 3.5/5, got {res.final_grade}"
    assert len(res.reference_requirements) >= 1
    req = res.reference_requirements[0]
    assert req.status == RequirementStatus.SUPPORTED


# ============================================================================
# 2. Clausal Sentence Over-Fragmentation Prevention
# ============================================================================

def test_clausal_sentence_no_spurious_modifier_propositions(pipeline):
    """Relative clause reference answer does not produce spurious noun-modifier requirements."""
    q = "What is a destructor in C++?"
    ref = "A member function that deallocates memory."
    stu = "A function that frees memory."

    res = pipeline.evaluate(q, ref, stu)

    # Must produce exactly 1 clausal requirement proposition, not 2
    assert len(res.reference_requirements) == 1, (
        f"Expected exactly 1 requirement proposition, got {len(res.reference_requirements)}: "
        f"{[r.reference_text for r in res.reference_requirements]}"
    )
    assert res.reference_requirements[0].status == RequirementStatus.SUPPORTED
    assert res.final_grade >= 4.5, f"Expected high grade for complete paraphrase, got {res.final_grade}"


def test_primary_key_clausal_single_requirement(pipeline):
    """Primary key clausal reference answer extracts single relational requirement."""
    q = "What is the purpose of a primary key in a relational database?"
    ref = "A primary key uniquely identifies each record in a table."
    stu = "A primary key uniquely identifies every row in a table."

    res = pipeline.evaluate(q, ref, stu)

    assert len(res.reference_requirements) == 1
    assert res.reference_requirements[0].status == RequirementStatus.SUPPORTED
    assert res.final_grade >= 4.5


# ============================================================================
# 3. Multi-Requirement Partial Credit & Status Tracking
# ============================================================================

def test_multi_requirement_full_credit(pipeline):
    """Student providing both requirements receives full grade (5.0/5.0)."""
    q = "What are characteristics of arrays?"
    ref = "An array has fixed size and provides random access."
    stu = "An array has fixed size and provides random access."

    res = pipeline.evaluate(q, ref, stu)

    assert len(res.reference_requirements) == 2
    assert res.reference_requirements[0].status == RequirementStatus.SUPPORTED
    assert res.reference_requirements[1].status == RequirementStatus.SUPPORTED
    assert res.final_grade >= 4.8


def test_multi_requirement_partial_credit_first_req(pipeline):
    """Student providing only the 1st requirement receives ~50% partial credit."""
    q = "What are characteristics of arrays?"
    ref = "An array has fixed size and provides random access."
    stu = "An array has fixed size."

    res = pipeline.evaluate(q, ref, stu)

    assert len(res.reference_requirements) == 2
    req0 = res.reference_requirements[0]
    req1 = res.reference_requirements[1]

    assert req0.status == RequirementStatus.SUPPORTED
    assert req1.status == RequirementStatus.MISSING
    assert req0.score_contribution > 0.40
    assert req1.score_contribution == 0.0

    # Expected grade: ~2.35 - 2.5 out of 5.0
    assert 2.0 <= res.final_grade <= 2.6, f"Expected partial grade ~2.35-2.5, got {res.final_grade}"


def test_multi_requirement_partial_credit_second_req(pipeline):
    """Student providing only the 2nd requirement receives ~50% partial credit."""
    q = "What are characteristics of arrays?"
    ref = "An array has fixed size and provides random access."
    stu = "An array provides random access."

    res = pipeline.evaluate(q, ref, stu)

    assert len(res.reference_requirements) == 2
    req0 = res.reference_requirements[0]
    req1 = res.reference_requirements[1]

    assert req0.status == RequirementStatus.MISSING
    assert req1.status == RequirementStatus.SUPPORTED
    assert req0.score_contribution == 0.0
    assert req1.score_contribution > 0.40

    assert 2.0 <= res.final_grade <= 2.6, f"Expected partial grade ~2.35-2.5, got {res.final_grade}"


def test_multi_requirement_partial_with_irrelevant_info(pipeline):
    """Partial answer with irrelevant information preserves partial credit without penalty."""
    q = "What are characteristics of arrays?"
    ref = "An array has fixed size and provides random access."
    stu = "An array has fixed size. Python was invented in the 1990s."

    res = pipeline.evaluate(q, ref, stu)

    assert len(res.reference_requirements) == 2
    assert res.reference_requirements[0].status == RequirementStatus.SUPPORTED
    assert res.reference_requirements[1].status == RequirementStatus.MISSING

    # Grade should remain in the partial credit band (~2.35)
    assert 2.0 <= res.final_grade <= 2.6, f"Expected neutral irrelevant effect, got {res.final_grade}"


def test_multi_requirement_partial_with_contradiction(pipeline):
    """Partial answer with 1 supported and 1 contradicted requirement applies penalty but keeps supported trace."""
    q = "What are characteristics of arrays?"
    ref = "An array has fixed size and provides random access."
    stu = "An array has fixed size and provides sequential access only."

    res = pipeline.evaluate(q, ref, stu)

    assert len(res.reference_requirements) == 2
    req0 = res.reference_requirements[0]
    req1 = res.reference_requirements[1]

    assert req0.status == RequirementStatus.SUPPORTED
    assert req1.status == RequirementStatus.CONTRADICTED
    assert req0.score_contribution > 0.40
    assert req1.score_contribution == 0.0

    # Contradiction reduces score below partial credit (e.g. 1.25/5.0)
    assert 0.5 <= res.final_grade <= 1.8, f"Expected penalized partial grade, got {res.final_grade}"


def test_multi_requirement_all_missing(pipeline):
    """Completely missing requirements receive Grade 0.0 with both marked MISSING."""
    q = "What are characteristics of arrays?"
    ref = "An array has fixed size and provides random access."
    stu = "Linked lists use pointers to connect nodes."

    res = pipeline.evaluate(q, ref, stu)

    assert len(res.reference_requirements) == 2
    for req in res.reference_requirements:
        assert req.status == RequirementStatus.MISSING
        assert req.score_contribution == 0.0
    assert res.final_grade == 0.0


# ============================================================================
# 4. JSON Serialization & Provenance Integrity
# ============================================================================

def test_reference_requirement_serialization(pipeline):
    """ReferenceRequirementRecord objects serialize cleanly to valid JSON."""
    q = "What are characteristics of arrays?"
    ref = "An array has fixed size and provides random access."
    stu = "An array has fixed size."

    res = pipeline.evaluate(q, ref, stu)
    res_dict = res.to_dict()

    assert "reference_requirements" in res_dict
    assert len(res_dict["reference_requirements"]) == 2

    # Verify JSON serializability
    json_str = json.dumps(res_dict)
    assert isinstance(json_str, str)
    parsed = json.loads(json_str)

    reqs = parsed["reference_requirements"]
    assert reqs[0]["status"] == "SUPPORTED"
    assert reqs[1]["status"] == "MISSING"
    assert "score_contribution" in reqs[0]
    assert "explanation" in reqs[0]
    assert "requirement_proposition" in reqs[0]
