"""
Validation Test Suite for Base ASAG (Stage 10A).

This module validates the complete Base ASAG pipeline against a controlled,
multi-category diagnostic test suite stored in tests/data/base_asag_validation.json.

Evaluates:
1. Exact matches across representative CS definition questions.
2. Simple lexical paraphrases (inflections, synonyms, determiner changes).
3. Complex paraphrases (structural and relational paraphrasing, including the compiler case).
4. Voice alternation (active-to-passive and passive-to-active transformations).
5. Negation handling (explicit student negation, double negation, polarity contradictions).
6. Coordination (conjoined predicates and compound clauses).
7. Relative clauses and participial modifiers.
8. Partial answers (incomplete propositions or missing reference coverage).
9. Additional student information (correct, irrelevant, and incorrect extra propositions).
10. The three required compiler validation cases:
    - Case 1: Exact/near match
    - Case 2: Lexical/complex paraphrase
    - Case 3: Incorrect answer

Dataset status:
ENGINEERING / DIAGNOSTIC DATA — NOT EMPIRICAL HUMAN RESEARCH DATA.
"""

import json
from pathlib import Path
from typing import Any, Dict, List
import pytest

from base_asag.pipeline import BaseASAGPipeline, BaseASAGPipelineResult


VALIDATION_DATA_PATH = (
    Path(__file__).parent / "data" / "base_asag_validation.json"
    if (Path(__file__).parent / "data" / "base_asag_validation.json").exists()
    else Path(__file__).parents[1] / "data" / "base_asag_validation.json"
)


def load_validation_cases() -> List[Dict[str, Any]]:
    """Load validation test cases from JSON file."""
    if not VALIDATION_DATA_PATH.exists():
        pytest.fail(f"Validation dataset not found at {VALIDATION_DATA_PATH}")
    with open(VALIDATION_DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("test_cases", [])


@pytest.fixture(scope="module")
def pipeline() -> BaseASAGPipeline:
    """Provides a shared BaseASAGPipeline instance."""
    return BaseASAGPipeline()


def test_validation_suite_loaded():
    """Verify validation suite JSON loads properly with all required metadata."""
    assert VALIDATION_DATA_PATH.exists()
    with open(VALIDATION_DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "test_cases" in data
    assert "dataset_type" in data
    assert "NOT EMPIRICAL HUMAN RESEARCH DATA" in data["dataset_type"]
    assert len(data["test_cases"]) >= 20

    required_keys = {
        "id", "category", "description", "question",
        "reference_answer", "student_answer",
        "expected_min_score", "expected_max_score",
        "expected_matched_count", "expected_missing_count",
        "expected_unmatched_student_count"
    }
    for tc in data["test_cases"]:
        assert required_keys.issubset(tc.keys()), f"Missing keys in {tc.get('id')}"


# ==============================================================================
# THREE REQUIRED COMPILER VALIDATION TEST CASES
# ==============================================================================

def test_compiler_case_1_exact_match(pipeline: BaseASAGPipeline):
    """
    Compiler Case 1: Exact or near match on compiler definition.

    Question: What does a compiler do?
    Reference: A compiler translates high-level source code into machine code.
    Student: A compiler translates source code into machine code.

    Expected:
    - Matched reference relations: 1
    - Missing reference relations: 0
    - Unmatched student relations: 0
    - Normalized score: 1.0 (Full credit)
    - Scale score (0-5): 5.0
    """
    q = "What does a compiler do?"
    ref = "A compiler translates high-level source code into machine code."
    stu = "A compiler translates source code into machine code."

    res = pipeline.grade(q, ref, stu)

    assert res.matched_count == 1
    assert res.missing_count == 0
    assert len(res.unmatched_student_relations) == 0
    assert res.normalized_score == 1.0
    assert res.scale_score(5.0) == 5.0
    assert res.entailment_results[0].relation == "ENTAILS"


def test_compiler_case_2_complex_paraphrase(pipeline: BaseASAGPipeline):
    """
    Compiler Case 2: Lexical and complex paraphrase with participial modifier.

    Question: What does a compiler do?
    Reference: A compiler translates high-level source code into machine code.
    Student: A compiler converts programs written in a high-level language into machine code.

    Expected:
    - Main clause ('compiler', 'converts', 'programs') aligns to reference ('compiler', 'translates', 'code')
    - Matched reference relations: 1 (MUST NOT BE 0)
    - Missing reference relations: 0 (MUST NOT BE 1)
    - Unmatched student relations: 1 ('programs', 'written', None)
    - Normalized score: in [0.5, 1.0] (partial or full credit, MUST NOT BE 0.0)
    - Scale score (0-5): >= 2.5
    """
    q = "What does a compiler do?"
    ref = "A compiler translates high-level source code into machine code."
    stu = "A compiler converts programs written in a high-level language into machine code."

    res = pipeline.grade(q, ref, stu)

    assert res.matched_count == 1, (
        f"Expected matched_count=1, got {res.matched_count}. "
        f"Relations: ref={[r.to_tuple() for r in res.reference_triples.canonical_relations]}, "
        f"stu={[r.to_tuple() for r in res.student_triples.canonical_relations]}"
    )
    assert res.missing_count == 0, f"Expected missing_count=0, got {res.missing_count}"
    assert len(res.unmatched_student_relations) == 1, (
        f"Expected 1 unmatched student relation ('programs written'), got {len(res.unmatched_student_relations)}"
    )
    assert res.normalized_score >= 0.5, (
        f"Expected normalized_score >= 0.5, got {res.normalized_score}"
    )
    assert res.scale_score(5.0) >= 2.5


def test_compiler_case_direct_paraphrase_intervening_modifiers(pipeline: BaseASAGPipeline):
    """
    Compiler Case: Direct semantic paraphrase with intervening modifiers ('high-level source code').

    Question: What does a compiler do?
    Reference: A compiler translates high-level source code into machine code.
    Student: A compiler converts high-level source code into machine code.

    Expected:
    - Reference canonical proposition: ('compiler', 'translates', 'code')
    - Student canonical proposition: ('compiler', 'converts', 'code')
    - Matched reference relations: 1 (MUST NOT BE 0)
    - Missing reference relations: 0 (MUST NOT BE 1)
    - Unmatched student relations: 0
    - Normalized score: 0.5 (evaluated as UNCERTAIN due to WordNet path distance between translate and convert)
    - Scale score (0-5): 2.5
    """
    q = "What does a compiler do?"
    ref = "A compiler translates high-level source code into machine code."
    stu = "A compiler converts high-level source code into machine code."

    res = pipeline.grade(q, ref, stu)

    ref_props = [r.to_tuple() for r in res.reference_triples.canonical_relations]
    stu_props = [r.to_tuple() for r in res.student_triples.canonical_relations]
    assert ("compiler", "translates", "code") in ref_props
    assert ("compiler", "converts", "code") in stu_props

    assert res.matched_count == 1, (
        f"Expected matched_count=1, got {res.matched_count}. "
        f"Relations: ref={ref_props}, stu={stu_props}"
    )
    assert res.missing_count == 0, f"Expected missing_count=0, got {res.missing_count}"
    assert len(res.unmatched_student_relations) == 0, (
        f"Expected 0 unmatched student relations, got {len(res.unmatched_student_relations)}"
    )
    assert res.normalized_score == 0.5, (
        f"Expected normalized_score == 0.5, got {res.normalized_score}"
    )
    assert res.scale_score(5.0) == 2.5


def test_compiler_case_3_incorrect_answer(pipeline: BaseASAGPipeline):
    """
    Compiler Case 3: Incorrect answer (negated or completely unrelated).

    Question: What does a compiler do?
    Reference: A compiler translates high-level source code into machine code.
    Student: A compiler does not translate source code into machine code.

    Expected:
    - Entailment decision: CONTRADICTS
    - Normalized score: 0.0 (Zero credit)
    """
    q = "What does a compiler do?"
    ref = "A compiler translates high-level source code into machine code."
    stu_neg = "A compiler does not translate source code into machine code."

    res_neg = pipeline.grade(q, ref, stu_neg)
    assert res_neg.normalized_score == 0.0
    assert any(d.relation == "CONTRADICTS" for d in res_neg.entailment_results)

    # Completely unrelated
    stu_unrel = "A compiler is used to browse websites on the internet."
    res_unrel = pipeline.grade(q, ref, stu_unrel)
    assert res_unrel.normalized_score == 0.0
    assert res_unrel.missing_count == 1


# ==============================================================================
# PARAMETRIZED VALIDATION SUITE OVER ALL CASES
# ==============================================================================

ALL_CASES = load_validation_cases()


@pytest.mark.parametrize("tc", ALL_CASES, ids=[tc["id"] for tc in ALL_CASES])
def test_validation_case_execution(pipeline: BaseASAGPipeline, tc: Dict[str, Any]):
    """Execute each validation test case and check core ASAG properties."""
    res = pipeline.grade(
        question=tc["question"],
        reference_answer=tc["reference_answer"],
        student_answer=tc["student_answer"],
    )

    # Check score bounds
    assert tc["expected_min_score"] <= res.normalized_score <= tc["expected_max_score"], (
        f"[{tc['id']}] Score {res.normalized_score:.4f} not in "
        f"[{tc['expected_min_score']}, {tc['expected_max_score']}]"
    )

    # Check matched count
    assert res.matched_count == tc["expected_matched_count"], (
        f"[{tc['id']}] Expected matched_count={tc['expected_matched_count']}, got {res.matched_count}"
    )

    # Check missing count
    assert res.missing_count == tc["expected_missing_count"], (
        f"[{tc['id']}] Expected missing_count={tc['expected_missing_count']}, got {res.missing_count}"
    )

    # Check unmatched student relations count
    assert len(res.unmatched_student_relations) == tc["expected_unmatched_student_count"], (
        f"[{tc['id']}] Expected unmatched_student={tc['expected_unmatched_student_count']}, "
        f"got {len(res.unmatched_student_relations)}: {[r.to_tuple() for r in res.unmatched_student_relations]}"
    )


# ==============================================================================
# UNMATCHED INFORMATION INVARIANCE IN BASE ASAG
# ==============================================================================

def test_unmatched_information_zero_score_effect(pipeline: BaseASAGPipeline):
    """
    Verify that extra student propositions (correct, irrelevant, or incorrect)
    do NOT alter the Base ASAG score on the core reference propositions.
    """
    q = "What is the purpose of a primary key?"
    ref = "A primary key uniquely identifies each record in a table."

    base_stu = "A primary key uniquely identifies each record in a table."
    extra_correct = "A primary key uniquely identifies each record in a table and cannot contain NULL values."
    extra_irrelevant = "A primary key uniquely identifies each record in a table. SQL was developed in the 1970s."
    extra_incorrect = "A primary key uniquely identifies each record in a table. It can contain duplicate values."

    r_base = pipeline.grade(q, ref, base_stu)
    r_corr = pipeline.grade(q, ref, extra_correct)
    r_irrel = pipeline.grade(q, ref, extra_irrelevant)
    r_inc = pipeline.grade(q, ref, extra_incorrect)

    # Base ASAG score must be identical (1.00) across all variants
    assert r_base.normalized_score == 1.0
    assert r_corr.normalized_score == 1.0
    assert r_irrel.normalized_score == 1.0
    assert r_inc.normalized_score == 1.0

    # Unmatched student relations must be captured and preserved
    assert len(r_base.unmatched_student_relations) == 0
    assert len(r_corr.unmatched_student_relations) >= 1
    assert len(r_irrel.unmatched_student_relations) >= 1
    assert len(r_inc.unmatched_student_relations) >= 1


def test_deterministic_reproducibility(pipeline: BaseASAGPipeline):
    """Verify that repeated evaluation of identical inputs produces identical results."""
    q = "What does a compiler do?"
    ref = "A compiler translates high-level source code into machine code."
    stu = "A compiler converts programs written in a high-level language into machine code."

    r1 = pipeline.grade(q, ref, stu)
    r2 = pipeline.grade(q, ref, stu)

    assert r1.normalized_score == r2.normalized_score
    assert r1.matched_count == r2.matched_count
    assert r1.missing_count == r2.missing_count
    assert len(r1.unmatched_student_relations) == len(r2.unmatched_student_relations)
    assert r1.to_dict() == r2.to_dict()
