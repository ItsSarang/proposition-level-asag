"""
Tests for Phase 11: Systematic Diagnostic Error Analysis Module.
"""

import pytest

from evaluation.error_analysis.overhaul_error_analysis import (
    ErrorCategory,
    ErrorDiagnosis,
    OverhaulErrorAnalyzer,
)


def test_diagnose_reference_representation_issue():
    analyzer = OverhaulErrorAnalyzer()

    diagnoses = analyzer.diagnose_record(
        question_id="1.4",
        student_index=0,
        question="How are elements in an array stored in memory?",
        reference_answer="Contiguously.",
        student_answer="Elements are stored sequentially next to each other.",
        human_score=5.0,
        system_score=0.0,
        reference_props_count=0,
        student_props_count=1,
        matched_props_count=0,
        unmatched_props_count=1,
        is_reference_nominal=True,
    )

    categories = [d.category for d in diagnoses]
    assert ErrorCategory.DATASET_REFERENCE_REPRESENTATION_ISSUE in categories
    assert diagnoses[0].severity == "HIGH"


def test_diagnose_extraction_failure():
    analyzer = OverhaulErrorAnalyzer()

    diagnoses = analyzer.diagnose_record(
        question_id="2.1",
        student_index=1,
        question="What is recursion?",
        reference_answer="A function that calls itself.",
        student_answer="When a method repeatedly executes its own internal body block until done.",
        human_score=4.0,
        system_score=0.0,
        reference_props_count=1,
        student_props_count=0,  # 0 propositions from valid text
        matched_props_count=0,
        unmatched_props_count=0,
    )

    categories = [d.category for d in diagnoses]
    assert ErrorCategory.EXTRACTION_FAILURE in categories


def test_diagnose_verbosity_inflation():
    analyzer = OverhaulErrorAnalyzer()

    diagnoses = analyzer.diagnose_record(
        question_id="3.2",
        student_index=5,
        question="What is a queue?",
        reference_answer="A first-in first-out data structure.",
        student_answer="Queues are blue and nice and were built in 1990 and have nice colors.",
        human_score=0.5,
        system_score=3.2,
        reference_props_count=1,
        student_props_count=4,
        matched_props_count=0,
        unmatched_props_count=4,
        positive_adjustment=0.35,  # inflated bonus
    )

    categories = [d.category for d in diagnoses]
    assert ErrorCategory.SCORING_AGGREGATION_FAILURE in categories


def test_diagnose_summary_aggregation():
    analyzer = OverhaulErrorAnalyzer()

    d1 = ErrorDiagnosis(
        category=ErrorCategory.EXTRACTION_FAILURE,
        severity="HIGH",
        question_id="1.1",
        student_index=0,
        question="Q",
        reference_answer="R",
        student_answer="S",
        human_score=4.0,
        system_score=1.0,
        error_delta=3.0,
        evidence={},
        explanation="Extraction failed",
    )

    d2 = ErrorDiagnosis(
        category=ErrorCategory.EXTRACTION_FAILURE,
        severity="MEDIUM",
        question_id="1.2",
        student_index=1,
        question="Q2",
        reference_answer="R2",
        student_answer="S2",
        human_score=3.0,
        system_score=2.0,
        error_delta=1.0,
        evidence={},
        explanation="Extraction failed 2",
    )

    summary = analyzer.analyze_diagnoses_summary([d1, d2])
    assert summary["total_diagnoses"] == 2
    assert summary["category_counts"][ErrorCategory.EXTRACTION_FAILURE.value] == 2
    assert summary["average_error_deltas"][ErrorCategory.EXTRACTION_FAILURE.value] == 2.0
    assert len(summary["representative_samples"][ErrorCategory.EXTRACTION_FAILURE.value]) == 2
