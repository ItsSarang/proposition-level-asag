"""
Unit tests for ASAG Backend Services (ASAGAnalysisService and GradingService).

Verifies that the backend services faithfully execute the V5 ASAG pipeline:
1. Primary key contradiction (Example A):
   - Phase 03 Relations formats negation into predicate ('never identifies') with NEGATIVE polarity.
   - Phase 04 Match correctly reflects structural slot alignment.
   - Phase 05 Entailment correctly returns CONTRADICTS with 1.0 confidence.
   - Phase 07 Score yields 0.0/5.0 with CORE_CONTRADICTION invalidation.
2. Local variable paraphrase (Example B):
   - Phase 06 Additional recovers core paraphrase via copula-adjective bridge.
   - Phase 07 Score yields substantial credit (>= 3.5/5.0).
"""

import pytest
from backend.services.analysis_service import ASAGAnalysisService
from backend.services.grading_service import GradingService


@pytest.fixture(scope="module")
def analysis_service():
    return ASAGAnalysisService()


@pytest.fixture(scope="module")
def grading_service():
    return GradingService()


def test_backend_analysis_primary_key_contradiction(analysis_service):
    """Verify backend analysis accurately reflects contradiction in relations, entailment, and scoring."""
    q = "What is the purpose of a primary key in a relational database?"
    ref = "A primary key uniquely identifies each record in a table."
    stu = "A primary key never identifies each record in a table."

    result = analysis_service.analyze(question=q, reference_answer=ref, student_answer=stu)

    # Phase 03: Relations
    stu_props = result["phase_03_relations"]["student_propositions"]
    assert len(stu_props) >= 1
    p0 = stu_props[0]
    assert "never" in p0["predicate"].lower()
    assert p0["polarity"] == "NEGATIVE"

    # Phase 04: Match
    matched_pairs = result["phase_04_match"]["matched_pairs"]
    assert len(matched_pairs) >= 1
    assert matched_pairs[0]["triple_score"] >= 0.90

    # Phase 05: Entailment
    entail_evals = result["phase_05_entailment"]["entailment_evaluations"]
    assert len(entail_evals) >= 1
    assert entail_evals[0]["status"] == "CONTRADICTS"
    assert entail_evals[0]["confidence"] == 1.0
    assert "never" in entail_evals[0]["evidence"].lower() or "negation" in entail_evals[0]["evidence"].lower()

    # Phase 07: Score
    score_phase = result["phase_07_score"]
    assert score_phase["final_grade"] == 0.0
    assert any(
        t.get("severity_level") == "CORE_CONTRADICTION"
        for t in score_phase["itemized_trace"]
    )


def test_backend_analysis_local_variable_paraphrase(analysis_service):
    """Verify backend analysis recovers copula-adjective paraphrase and awards credit."""
    q = "What is the scope of a local variable in a function?"
    ref = "A local variable is accessible only within the function or block in which it is declared."
    stu = "A local variable has local scope and can only be accessed inside the specific block or function where it is defined."

    result = analysis_service.analyze(question=q, reference_answer=ref, student_answer=stu)

    # Phase 06: Additional & Core Recovery
    add_phase = result["phase_06_additional"]
    assert add_phase["recovered_core_count"] >= 1
    assert any(
        item.get("reason") == "COPULA_ADJECTIVE_VERB_BRIDGE"
        for item in add_phase["recovered_core_items"]
    )

    # Phase 07: Score
    score_phase = result["phase_07_score"]
    assert score_phase["final_grade"] >= 3.5
    assert score_phase["base_score_effective"] >= 0.70


def test_backend_grading_service_v5_execution(grading_service):
    """Verify GradingService accurately grades Examples A and B under model V5."""
    # Example A: Contradiction -> 0.0
    res_a = grading_service.grade(
        question="What is the purpose of a primary key in a relational database?",
        reference_answer="A primary key uniquely identifies each record in a table.",
        student_answer="A primary key never identifies each record in a table.",
        model_id="V5",
    )
    assert res_a["grade"] == 0.0

    # Example B: Correct Paraphrase -> >= 3.5
    res_b = grading_service.grade(
        question="What is the scope of a local variable in a function?",
        reference_answer="A local variable is accessible only within the function or block in which it is declared.",
        student_answer="A local variable has local scope and can only be accessed inside the specific block or function where it is defined.",
        model_id="V5",
    )
    assert res_b["grade"] >= 3.5
