"""
Test Runner Bridge for Phase 4A Scoring Development Tests.
"""

from evaluation.scoring_development.scoring_sanity_tests import (
    pipeline,
    all_models,
    test_property_1_correct_additional_non_decreasing,
    test_property_2_irrelevant_information_neutral,
    test_property_3_incorrect_information_non_increasing,
    test_property_4_multiple_incorrect_non_increasing,
    test_property_5_serious_contradiction_produces_strict_deduction,
    test_property_6_incorrect_cannot_compensate_partial_core,
    test_property_7_uncertain_no_positive_bonus,
    test_property_8_bonus_strictly_bounded,
    test_property_9_range_bounds,
    test_property_10_determinism,
)
