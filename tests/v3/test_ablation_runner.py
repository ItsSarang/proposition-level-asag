"""
Tests for Phase 12: Controlled Ablation Study Runner.
"""

import pytest

from evaluation.ablation.run_ablation_study import (
    ABLATION_CONDITIONS,
    AblationStudyRunner,
)
from evaluation.dataset.mohler_loader import MohlerRecord
from proposed_asag.overhauled_pipeline import OverhauledASAGPipeline


def test_ablation_conditions_coverage():
    expected_conditions = [
        "A_BASE_ASAG",
        "B_BASE_PLUS_HYBRID",
        "C_BASE_PLUS_SEMANTIC_V2",
        "D_BASE_PLUS_GLOBAL_MATCHING",
        "E_BASE_PLUS_QUESTION_RELEVANCE",
        "F_BASE_PLUS_PROPERTY_CONTRADICTION",
        "G_FULL_OVERHAULED_SYSTEM",
    ]
    for cond in expected_conditions:
        assert cond in ABLATION_CONDITIONS
        assert "description" in ABLATION_CONDITIONS[cond]


def test_ablation_runner_execution_sample():
    records = [
        MohlerRecord(
            question_id="1.1",
            assignment=1,
            question_index=1,
            is_active=True,
            student_index=0,
            question="What is the role of a prototype program in problem solving?",
            reference_answer="To simulate the behaviour of portions of the desired software product.",
            student_answer_raw="To simulate portions of the desired final product.",
            student_answer_cleaned="To simulate portions of the desired final product.",
            score_me=5.0,
            score_other=5.0,
            score_ave=5.0,
            score_scale="0-5",
        ),
        MohlerRecord(
            question_id="1.1",
            assignment=1,
            question_index=1,
            is_active=True,
            student_index=1,
            question="What is the role of a prototype program in problem solving?",
            reference_answer="To simulate the behaviour of portions of the desired software product.",
            student_answer_raw="A prototype program simulates the behaviors of portions of the desired software product.",
            student_answer_cleaned="A prototype program simulates the behaviors of portions of the desired software product.",
            score_me=5.0,
            score_other=5.0,
            score_ave=5.0,
            score_scale="0-5",
        ),
    ]

    runner = AblationStudyRunner(records)
    res = runner.run_condition("A_BASE_ASAG", limit=2)
    assert res["condition_key"] == "A_BASE_ASAG"
    assert res["sample_count"] == 2
    assert "mae" in res["metrics"]
    assert "rmse" in res["metrics"]
