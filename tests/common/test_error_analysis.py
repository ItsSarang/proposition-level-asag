"""Unit tests for Stage 16 Diagnostic Error Analysis."""

from pathlib import Path
import json
import pytest
import pandas as pd

from base_asag.pipeline import BaseASAGPipeline
from evaluation.error_analysis.error_analysis import (
    compute_aggregate_proposition_stats,
    find_representative_cases,
    run_diagnostic_analysis,
    trace_pipeline_case,
)
from proposed_asag.scoring.proposed_scorer import ProposedScorer


@pytest.fixture(scope="module")
def repo_root() -> Path:
    p = Path(__file__).resolve()
    while p.parent != p:
        if (p / "pyproject.toml").exists() or (p / "GEMINI.md").exists():
            return p
        p = p.parent
    return Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def predictions_df(repo_root: Path) -> pd.DataFrame:
    csv_path = repo_root / "evaluation" / "results" / "mohler_evaluation_predictions.csv"
    assert csv_path.exists(), "Predictions CSV must exist for error analysis tests."
    return pd.read_csv(csv_path, dtype={"question_id": str})


@pytest.fixture(scope="module")
def pipeline() -> BaseASAGPipeline:
    return BaseASAGPipeline()


@pytest.fixture(scope="module")
def scorer() -> ProposedScorer:
    return ProposedScorer()


def test_compute_aggregate_proposition_stats(predictions_df: pd.DataFrame):
    """Verify calculation of aggregate proposition counts, adjustment distributions, and clipping."""
    stats = compute_aggregate_proposition_stats(predictions_df)

    assert stats["total_records"] == 2273
    assert stats["total_unmatched_propositions"] == 3611

    counts = stats["classification_counts"]
    assert counts["CORRECT_ADDITIONAL"] == 2818
    assert counts["IRRELEVANT"] == 780
    assert counts["INCORRECT"] == 12
    assert counts["UNCERTAIN"] == 1

    adj = stats["answer_adjustment_counts"]
    assert adj["positive_adjustment_answers"] == 1472
    assert adj["negative_adjustment_answers"] == 6
    assert adj["zero_adjustment_answers"] == 795
    assert adj["clipped_upper_count"] == 48
    assert adj["clipped_lower_count"] == 3

    net = stats["net_adjustment_normalized"]
    assert abs(net["mean"] - 0.1229) < 1e-4
    assert net["min"] == -0.2
    assert net["max"] == 1.7


def test_trace_pipeline_case(pipeline: BaseASAGPipeline, scorer: ProposedScorer):
    """Verify trace_pipeline_case returns complete proposition, matching, entailment, and adjustment traces."""
    trace = trace_pipeline_case(
        question="What is a primary key?",
        reference="A primary key uniquely identifies each record in a table.",
        student="A primary key uniquely identifies each record in a table and cannot contain NULL values.",
        pipeline=pipeline,
        scorer=scorer,
        human_score=5.0,
        baseline_grade=3.5,
    )

    assert "question" in trace
    assert "reference_answer" in trace
    assert "student_answer" in trace
    assert "base_grade" in trace
    assert "proposed_grade" in trace
    assert "extracted_reference_propositions" in trace
    assert "extracted_student_propositions" in trace
    assert "matched_propositions" in trace
    assert "proposed_adjustments" in trace
    assert len(trace["proposed_adjustments"]) > 0


def test_find_representative_cases(
    predictions_df: pd.DataFrame,
    pipeline: BaseASAGPipeline,
    scorer: ProposedScorer,
):
    """Verify that all required representative case categories are correctly identified and traced."""
    cases = find_representative_cases(predictions_df, pipeline, scorer)

    expected_keys = [
        "base_asag_quadrant_A_zero_ref_prop",
        "base_asag_quadrant_A_matching_gap",
        "base_asag_quadrant_B_overprediction",
        "base_asag_quadrant_C_concordant_high",
        "base_asag_quadrant_D_concordant_low",
        "proposed_asag_case_A_improves_mae",
        "proposed_asag_case_B_worsens_mae",
        "proposed_asag_case_C_divergence",
        "proposed_asag_case_D_neutral_unmatched",
        "proposed_asag_case_E_correct_additional",
        "proposed_asag_case_F_irrelevant",
        "proposed_asag_case_G_incorrect_polarity",
        "tfidf_vs_base_lexical_superiority",
    ]

    for key in expected_keys:
        assert key in cases, f"Missing expected case key: {key}"
        case_data = cases[key]
        assert "metadata" in case_data
        assert "question" in case_data
        assert "human_score" in case_data
        assert "base_grade" in case_data
        assert "proposed_grade" in case_data


def test_run_diagnostic_analysis_export(repo_root: Path, tmp_path: Path):
    """Verify diagnostic analysis execution and JSON export."""
    csv_path = repo_root / "evaluation" / "results" / "mohler_evaluation_predictions.csv"
    out_json = tmp_path / "test_representative_cases.json"

    payload = run_diagnostic_analysis(csv_path, out_json)
    assert out_json.exists()

    with open(out_json, "r", encoding="utf-8") as f:
        loaded = json.load(f)

    assert "aggregate_proposition_statistics" in loaded
    assert "representative_cases" in loaded
    assert loaded["aggregate_proposition_statistics"]["total_records"] == 2273
