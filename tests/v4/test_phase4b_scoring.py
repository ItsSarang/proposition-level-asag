"""
Test Runner Bridge for Phase 4B Scoring Sanity & Qualitative Constraint Tests.
"""

from evaluation.scoring_development.phase4b_sanity_tests import (
    evaluation_data,
    test_r1_r12_irrelevant_information_neutral,
    test_r2_correct_additional_non_decreasing,
    test_r3_incorrect_strictly_decreases_score,
    test_r4_core_contradiction_harsher_than_minor,
    test_r5_multiple_errors_monotonicity,
    test_r6_r7_partial_core_non_compensating,
    test_r8_uncertain_zero_bonus,
    test_r9_bonus_strictly_bounded,
    test_r10_range_bounds_all_cases,
    test_r11_severity_ordering_consistency,
    test_cross_domain_consistency,
    test_mixed_information_behavior,
    test_determinism_across_models,
)
