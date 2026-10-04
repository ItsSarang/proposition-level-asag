"""
Pytest Test Bridge for Phase 4D Severity-Aware Integration & Invariant Tests.
"""

from evaluation.scoring_development.phase4d_integration_tests import (
    evaluation_traces,
    pipeline,
    scorer,
    test_property_1_correct_additional_cannot_reduce_score,
    test_property_2_irrelevant_information_neutral,
    test_property_3_uncertain_information_no_bonus,
    test_property_4_minor_incorrect_causes_deduction,
    test_property_5_moderate_deduction_larger_than_minor,
    test_property_6_core_contradiction_larger_than_minor,
    test_property_7_correct_additional_cannot_compensate_core_contradiction,
    test_property_8_multiple_errors_monotonicity,
    test_property_9_entity_confusion_not_core_contradiction,
    test_property_10_unresolved_contradiction_produces_no_penalty,
    test_property_11_12_score_and_grade_ranges,
    test_property_13_repeated_execution_is_deterministic,
    test_property_14_every_adjustment_has_provenance,
    test_property_15_no_manual_severity_in_execution_path,
)
