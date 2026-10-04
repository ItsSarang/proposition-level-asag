"""Unit and integration tests for the ASAG Evaluation Pipeline (Stage 15.2)."""

from pathlib import Path
import json
import pytest
import numpy as np
import pandas as pd

from evaluation.dataset.mohler_loader import MohlerDataset, MohlerLoader, MohlerRecord
from evaluation.metrics.asag_metrics import (
    EvaluationMetrics,
    compute_all_metrics,
    mean_absolute_error,
    normalize_to_grade,
    pearson_correlation,
    quadratic_weighted_kappa,
    root_mean_squared_error,
    spearman_correlation,
    validate_metric_inputs,
)
from evaluation.runners.base_asag_runner import BaseASAGRunner
from evaluation.runners.baseline_runner import BaselineRunner
from evaluation.runners.evaluation_runner import (
    EvaluationRunResult,
    EvaluationRunner,
    RecordEvaluationResult,
)
from evaluation.runners.proposed_asag_runner import ProposedASAGRunner


# =========================================================================
# 1. Scale Normalization Tests
# =========================================================================

def test_normalize_to_grade_standard_scale():
    """Verify conversion from normalized [0, 1] to 0-5 grade scale."""
    assert normalize_to_grade(0.0) == 0.0
    assert normalize_to_grade(1.0) == 5.0
    assert normalize_to_grade(0.5) == 2.5
    assert normalize_to_grade(0.7) == 3.5
    assert normalize_to_grade(0.2468) == 1.234


def test_normalize_to_grade_custom_max_points():
    """Verify conversion with arbitrary max_points (e.g. 10.0, 100.0)."""
    assert normalize_to_grade(0.5, max_points=10.0) == 5.0
    assert normalize_to_grade(0.75, max_points=100.0) == 75.0


def test_normalize_to_grade_invalid_input():
    """Verify TypeError or ValueError on invalid input."""
    with pytest.raises(ValueError):
        normalize_to_grade(None)


# =========================================================================
# 2. Metric Correctness and Edge Cases
# =========================================================================

def test_metrics_identical_ground_truth():
    """Verify metrics when predictions exactly match ground truth."""
    y = [1.0, 2.0, 3.0, 4.0, 5.0]
    metrics = compute_all_metrics("Perfect", y, y)

    assert metrics.mae == 0.0
    assert metrics.rmse == 0.0
    assert metrics.pearson_r == 1.0
    assert metrics.spearman_rho == 1.0
    assert metrics.qwk == 1.0
    assert metrics.n_samples == 5


def test_metrics_known_toy_values():
    """Verify metrics on known offset values."""
    y_true = [1.0, 2.0, 3.0]
    y_pred = [2.0, 3.0, 4.0]

    assert mean_absolute_error(y_true, y_pred) == 1.0
    assert root_mean_squared_error(y_true, y_pred) == 1.0
    r, _ = pearson_correlation(y_true, y_pred)
    assert r is not None and abs(r - 1.0) < 1e-6
    rho, _ = spearman_correlation(y_true, y_pred)
    assert rho is not None and abs(rho - 1.0) < 1e-6


def test_metrics_constant_prediction_edge_cases():
    """Verify that constant predictions return None for correlations and 0.0 for QWK without crashing."""
    y_true = [1.0, 2.0, 3.0, 4.0, 5.0]
    y_const = [3.0, 3.0, 3.0, 3.0, 3.0]

    metrics = compute_all_metrics("Constant", y_true, y_const)
    assert metrics.mae == 1.2
    assert abs(metrics.rmse - 1.4142) < 1e-3
    assert metrics.pearson_r is None
    assert metrics.pearson_p is None
    assert metrics.spearman_rho is None
    assert metrics.spearman_p is None
    assert metrics.qwk == 0.0


def test_metrics_validation_errors():
    """Verify input validation handles empty, mismatched, or NaN inputs."""
    with pytest.raises(ValueError, match="cannot be empty"):
        validate_metric_inputs([], [])

    with pytest.raises(ValueError, match="Length mismatch"):
        validate_metric_inputs([1.0, 2.0], [1.0])

    with pytest.raises(ValueError, match="NaN"):
        validate_metric_inputs([1.0, float("nan")], [1.0, 2.0])

    with pytest.raises(ValueError, match="infinite"):
        validate_metric_inputs([1.0, float("inf")], [1.0, 2.0])


# =========================================================================
# 3. Individual Runner Tests
# =========================================================================

def test_baseline_runner_evaluation():
    """Verify BaselineRunner computes valid normalized and scaled predictions."""
    runner = BaselineRunner()
    pred = runner.evaluate_pair(
        reference_answer="A primary key uniquely identifies each record.",
        student_answer="A primary key uniquely identifies rows in a table.",
        max_points=5.0,
    )
    assert pred.status == "SUCCESS"
    assert 0.0 <= pred.normalized_score <= 1.0
    assert 0.0 <= pred.grade <= 5.0
    assert pred.grade == float(round(pred.normalized_score * 5.0, 4))


def test_baseline_runner_empty_student_answer():
    """Verify BaselineRunner handles empty student answers gracefully."""
    runner = BaselineRunner()
    pred = runner.evaluate_pair(
        reference_answer="A primary key uniquely identifies each record.",
        student_answer="",
        max_points=5.0,
    )
    assert pred.status == "SUCCESS"
    assert pred.normalized_score == 0.0
    assert pred.grade == 0.0


def test_base_asag_runner_evaluation():
    """Verify BaseASAGRunner computes valid predictions and diagnostics."""
    runner = BaseASAGRunner()
    pred = runner.evaluate_triplet(
        question="What is a primary key?",
        reference_answer="A primary key uniquely identifies each record in a table.",
        student_answer="A primary key uniquely identifies each record in a table.",
        max_points=5.0,
    )
    assert pred.status == "SUCCESS"
    assert pred.normalized_score > 0.0
    assert pred.grade > 0.0
    assert pred.pipeline_result is not None


def test_proposed_asag_runner_evaluation():
    """Verify ProposedASAGRunner evaluates a Base result and provides adjustment tallies."""
    base_runner = BaseASAGRunner()
    prop_runner = ProposedASAGRunner()

    base_pred = base_runner.evaluate_triplet(
        question="What is a primary key?",
        reference_answer="A primary key uniquely identifies each record.",
        student_answer="A primary key uniquely identifies each record and cannot be null.",
        max_points=5.0,
    )
    assert base_pred.pipeline_result is not None

    prop_pred = prop_runner.evaluate_base_result(base_pred.pipeline_result, max_points=5.0)
    assert prop_pred.status == "SUCCESS"
    assert 0.0 <= prop_pred.proposed_normalized <= 1.0
    assert 0.0 <= prop_pred.proposed_grade <= 5.0
    assert isinstance(prop_pred.correct_additional_count, int)
    assert isinstance(prop_pred.net_adjustment, float)


# =========================================================================
# 4. Unified EvaluationRunner and Schema Tests
# =========================================================================

@pytest.fixture(scope="module")
def sample_dataset() -> MohlerDataset:
    raw_ds = MohlerLoader.load_processed_csv().filter_active()
    return MohlerDataset(raw_ds.records[:5])


def test_evaluation_runner_schema(sample_dataset: MohlerDataset):
    """Verify RecordEvaluationResult contains all required fields with proper types."""
    runner = EvaluationRunner()
    rec_res = runner.evaluate_record(sample_dataset[0])

    assert isinstance(rec_res, RecordEvaluationResult)
    assert rec_res.question_id == sample_dataset[0].question_id
    assert rec_res.human_score == sample_dataset[0].score_ave
    assert rec_res.baseline_normalized is not None
    assert rec_res.baseline_grade is not None
    assert rec_res.base_normalized is not None
    assert rec_res.base_grade is not None
    assert rec_res.proposed_normalized is not None
    assert rec_res.proposed_grade is not None
    assert rec_res.status == "SUCCESS"

    d = rec_res.to_dict()
    assert "baseline_normalized" in d
    assert "baseline_grade" in d
    assert "base_normalized" in d
    assert "base_grade" in d
    assert "proposed_normalized" in d
    assert "proposed_grade" in d
    assert "correct_additional_count" in d
    assert "irrelevant_count" in d
    assert "incorrect_count" in d
    assert "uncertain_count" in d
    assert "net_adjustment" in d


def test_evaluation_runner_deterministic_ordering(sample_dataset: MohlerDataset):
    """Verify evaluation is deterministic across multiple invocations."""
    runner = EvaluationRunner()
    run1 = runner.evaluate_dataset(sample_dataset)
    run2 = runner.evaluate_dataset(sample_dataset)

    assert len(run1.records) == len(run2.records) == 5
    for r1, r2 in zip(run1.records, run2.records):
        assert r1.question_id == r2.question_id
        assert r1.student_index == r2.student_index
        assert r1.baseline_grade == r2.baseline_grade
        assert r1.base_grade == r2.base_grade
        assert r1.proposed_grade == r2.proposed_grade


def test_evaluation_runner_subset_filtering():
    """Verify metrics calculation partitions active records, assignments 1-10, and exams."""
    raw_ds = MohlerLoader.load_processed_csv()
    # Pick 2 assignment records and 2 exam records
    a_recs = [r for r in raw_ds if r.is_active and r.assignment <= 10][:2]
    e_recs = [r for r in raw_ds if r.is_active and r.assignment > 10][:2]
    mixed_ds = MohlerDataset(a_recs + e_recs)

    runner = EvaluationRunner()
    run_res = runner.evaluate_dataset(mixed_ds)

    assert run_res.summary["total_evaluated_records"] == 4
    assert run_res.summary["assignments_1_10_records"] == 2
    assert run_res.summary["exams_records"] == 2

    # Check metrics dictionaries exist for each partition
    assert "baseline" in run_res.metrics_all
    assert "base_asag" in run_res.metrics_all
    assert "proposed_asag" in run_res.metrics_all

    assert "baseline" in run_res.metrics_assignments_1_10
    assert "baseline" in run_res.metrics_exams


def test_evaluation_runner_failure_recording():
    """Verify failures are recorded and isolated without crashing the evaluation run."""
    class FailingBaseRunner(BaseASAGRunner):
        def evaluate_triplet(self, question, reference_answer, student_answer, max_points=5.0):
            raise RuntimeError("Simulated pipeline failure")

    runner = EvaluationRunner(base_asag_runner=FailingBaseRunner())
    rec = MohlerRecord(
        question_id="1.1",
        assignment=1,
        question_index=1,
        is_active=True,
        student_index=0,
        question="What is X?",
        reference_answer="X is Y.",
        student_answer_raw="X is Z.",
        student_answer_cleaned="X is Z.",
        score_me=4.0,
        score_other=4.0,
        score_ave=4.0,
        score_scale="0-5",
    )

    rec_res = runner.evaluate_record(rec)
    assert rec_res.status == "FAILURE"
    assert "Simulated pipeline failure" in (rec_res.error_message or "")
    assert rec_res.base_grade is None
    assert rec_res.proposed_grade is None
    # Baseline still succeeded
    assert rec_res.baseline_grade is not None


def test_results_export_and_roundtrip(sample_dataset: MohlerDataset, tmp_path: Path):
    """Verify machine-readable CSV and JSON result exports."""
    runner = EvaluationRunner()
    run_res = runner.evaluate_dataset(sample_dataset)

    exported = run_res.export_results(output_dir=tmp_path)
    csv_path = exported["predictions_csv"]
    json_path = exported["summary_json"]

    assert csv_path.exists()
    assert json_path.exists()

    df = pd.read_csv(csv_path)
    assert len(df) == 5
    assert "human_score" in df.columns
    assert "baseline_grade" in df.columns
    assert "base_grade" in df.columns
    assert "proposed_grade" in df.columns

    with open(json_path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    assert "metrics_all" in payload
    assert "summary" in payload
    assert "configuration" in payload
    assert payload["summary"]["total_evaluated_records"] == 5
