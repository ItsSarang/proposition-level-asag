"""Unified ASAG Evaluation Orchestrator (Stage 15.2).

Coordinates the evaluation of three ASAG systems:
- System 1: TF-IDF + Cosine Baseline
- System 2: Base ASAG (Basak-inspired reference coverage)
- System 3: Proposed ASAG (Proposition-level extension)

against student records from the Mohler ASAG dataset.

Research Boundaries:
--------------------
- Deterministic, reproducible evaluation.
- Explicit scale conversion: predicted_grade = normalized_score * 5.0.
- Human target is preserved unchanged (score_ave).
- Failures are recorded and isolated without crashing or silently altering grades.
- Disaggregated metrics computed on full active, Assignments 1-10, and Exams 11-12.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import time
from typing import Any, Callable, Dict, List, Optional, Sequence
import numpy as np
import pandas as pd

from evaluation.dataset.mohler_loader import MohlerDataset, MohlerRecord
from evaluation.metrics.asag_metrics import EvaluationMetrics, compute_all_metrics
from evaluation.runners.base_asag_runner import BaseASAGPrediction, BaseASAGRunner
from evaluation.runners.baseline_runner import BaselinePrediction, BaselineRunner
from evaluation.runners.proposed_asag_runner import (
    ProposedASAGPrediction,
    ProposedASAGRunner,
)


@dataclass(frozen=True)
class RecordEvaluationResult:
    """Consolidated evaluation record containing predictions from all three systems."""

    question_id: str
    assignment: int
    question_index: int
    student_index: int
    is_active: bool
    question: str
    reference_answer: str
    student_answer: str
    human_score: float
    score_me: float
    score_other: float
    score_scale: str
    baseline_normalized: Optional[float]
    baseline_grade: Optional[float]
    base_normalized: Optional[float]
    base_grade: Optional[float]
    proposed_normalized: Optional[float]
    proposed_grade: Optional[float]
    correct_additional_count: int
    irrelevant_count: int
    incorrect_count: int
    uncertain_count: int
    net_adjustment: float
    status: str
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert record result to a dictionary."""
        return asdict(self)


@dataclass(frozen=True)
class EvaluationRunResult:
    """Complete results from an ASAG evaluation experiment."""

    records: List[RecordEvaluationResult]
    metrics_all: Dict[str, EvaluationMetrics]
    metrics_assignments_1_10: Dict[str, EvaluationMetrics]
    metrics_exams: Dict[str, EvaluationMetrics]
    metrics_by_question: Dict[str, Dict[str, EvaluationMetrics]]
    failures: List[Dict[str, Any]]
    configuration: Dict[str, Any]
    summary: Dict[str, Any]

    def to_dataframe(self) -> pd.DataFrame:
        """Convert individual predictions to a pandas DataFrame."""
        return pd.DataFrame([r.to_dict() for r in self.records])

    def export_results(
        self,
        output_dir: Optional[Path] = None,
    ) -> Dict[str, Path]:
        """Export machine-readable evaluation results (CSV and JSON)."""
        if output_dir is None:
            repo_root = Path(__file__).resolve().parent.parent.parent
            output_dir = repo_root / "evaluation" / "results"
        output_dir.mkdir(parents=True, exist_ok=True)

        # 1. Predictions CSV
        df = self.to_dataframe()
        csv_path = output_dir / "mohler_evaluation_predictions.csv"
        df.to_csv(csv_path, index=False, encoding="utf-8")

        # 2. Summary JSON
        summary_payload = {
            "summary": self.summary,
            "configuration": self.configuration,
            "metrics_all": {k: v.to_dict() for k, v in self.metrics_all.items()},
            "metrics_assignments_1_10": {
                k: v.to_dict() for k, v in self.metrics_assignments_1_10.items()
            },
            "metrics_exams": {k: v.to_dict() for k, v in self.metrics_exams.items()},
            "failures": self.failures,
        }
        json_path = output_dir / "mohler_evaluation_summary.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(summary_payload, f, indent=2)

        return {
            "predictions_csv": csv_path,
            "summary_json": json_path,
        }


class EvaluationRunner:
    """Unified evaluator orchestrating Baseline, Base ASAG, and Proposed ASAG."""

    def __init__(
        self,
        baseline_runner: Optional[BaselineRunner] = None,
        base_asag_runner: Optional[BaseASAGRunner] = None,
        proposed_asag_runner: Optional[ProposedASAGRunner] = None,
        use_cleaned_text: bool = True,
        max_points: float = 5.0,
    ) -> None:
        self.baseline_runner = baseline_runner or BaselineRunner()
        self.base_asag_runner = base_asag_runner or BaseASAGRunner()
        self.proposed_asag_runner = proposed_asag_runner or ProposedASAGRunner()
        self.use_cleaned_text = bool(use_cleaned_text)
        self.max_points = float(max_points)

    def evaluate_record(self, record: MohlerRecord) -> RecordEvaluationResult:
        """Evaluate a single MohlerRecord through all three ASAG systems."""
        stu_text = (
            record.student_answer_cleaned if self.use_cleaned_text else record.student_answer_raw
        )

        status = "SUCCESS"
        errors: List[str] = []

        # System 1: Baseline (TF-IDF Cosine)
        try:
            b_pred = self.baseline_runner.evaluate_pair(
                reference_answer=record.reference_answer,
                student_answer=stu_text,
                max_points=self.max_points,
            )
        except Exception as e:
            b_pred = BaselinePrediction(
                normalized_score=0.0,
                grade=0.0,
                status="ERROR",
                error_message=str(e),
            )
        if b_pred.status != "SUCCESS":
            status = "PARTIAL_FAILURE"
            errors.append(f"Baseline error: {b_pred.error_message}")

        # System 2: Base ASAG
        try:
            base_pred = self.base_asag_runner.evaluate_triplet(
                question=record.question,
                reference_answer=record.reference_answer,
                student_answer=stu_text,
                max_points=self.max_points,
            )
        except Exception as e:
            base_pred = BaseASAGPrediction(
                normalized_score=0.0,
                grade=0.0,
                total_reference_propositions=0,
                matched_count=0,
                entailed_count=0,
                uncertain_count=0,
                contradicted_count=0,
                missing_count=0,
                unmatched_student_count=0,
                status="ERROR",
                error_message=str(e),
                pipeline_result=None,
            )
        if base_pred.status != "SUCCESS":
            status = "FAILURE" if status == "SUCCESS" else "MULTIPLE_FAILURES"
            errors.append(f"Base ASAG error: {base_pred.error_message}")

        # System 3: Proposed ASAG
        if base_pred.pipeline_result is not None:
            try:
                prop_pred = self.proposed_asag_runner.evaluate_base_result(
                    base_result=base_pred.pipeline_result,
                    max_points=self.max_points,
                )
            except Exception as e:
                prop_pred = ProposedASAGPrediction(
                    base_normalized=0.0,
                    base_grade=0.0,
                    proposed_normalized=0.0,
                    proposed_grade=0.0,
                    raw_proposed_score=0.0,
                    correct_additional_count=0,
                    irrelevant_count=0,
                    incorrect_count=0,
                    uncertain_count=0,
                    positive_adjustment=0.0,
                    negative_adjustment=0.0,
                    net_adjustment=0.0,
                    is_clipped_upper=False,
                    is_clipped_lower=False,
                    status="ERROR",
                    error_message=str(e),
                    score_result=None,
                )
            if prop_pred.status != "SUCCESS":
                status = "PARTIAL_FAILURE" if status == "SUCCESS" else "MULTIPLE_FAILURES"
                errors.append(f"Proposed ASAG error: {prop_pred.error_message}")
        else:
            # Cannot run proposed ASAG without base ASAG result
            prop_pred = None
            status = "FAILURE"
            errors.append("Proposed ASAG skipped due to Base ASAG pipeline failure.")

        return RecordEvaluationResult(
            question_id=record.question_id,
            assignment=record.assignment,
            question_index=record.question_index,
            student_index=record.student_index,
            is_active=record.is_active,
            question=record.question,
            reference_answer=record.reference_answer,
            student_answer=stu_text,
            human_score=record.score_ave,
            score_me=record.score_me,
            score_other=record.score_other,
            score_scale=record.score_scale,
            baseline_normalized=b_pred.normalized_score if b_pred.status == "SUCCESS" else None,
            baseline_grade=b_pred.grade if b_pred.status == "SUCCESS" else None,
            base_normalized=base_pred.normalized_score if base_pred.status == "SUCCESS" else None,
            base_grade=base_pred.grade if base_pred.status == "SUCCESS" else None,
            proposed_normalized=(
                prop_pred.proposed_normalized if prop_pred and prop_pred.status == "SUCCESS" else None
            ),
            proposed_grade=(
                prop_pred.proposed_grade if prop_pred and prop_pred.status == "SUCCESS" else None
            ),
            correct_additional_count=prop_pred.correct_additional_count if prop_pred else 0,
            irrelevant_count=prop_pred.irrelevant_count if prop_pred else 0,
            incorrect_count=prop_pred.incorrect_count if prop_pred else 0,
            uncertain_count=prop_pred.uncertain_count if prop_pred else 0,
            net_adjustment=prop_pred.net_adjustment if prop_pred else 0.0,
            status=status,
            error_message="; ".join(errors) if errors else None,
        )

    def _compute_subset_metrics(
        self,
        records: Sequence[RecordEvaluationResult],
    ) -> Dict[str, EvaluationMetrics]:
        """Compute evaluation metrics for valid predictions across all three systems."""
        # Filter to successfully predicted records
        valid_records = [
            r for r in records
            if r.baseline_grade is not None
            and r.base_grade is not None
            and r.proposed_grade is not None
        ]

        if not valid_records:
            return {}

        y_true = [r.human_score for r in valid_records]
        y_baseline = [r.baseline_grade for r in valid_records]
        y_base = [r.base_grade for r in valid_records]
        y_proposed = [r.proposed_grade for r in valid_records]

        return {
            "baseline": compute_all_metrics(
                system_name="TF-IDF + Cosine Baseline",
                y_true=y_true,
                y_pred=y_baseline,
            ),
            "base_asag": compute_all_metrics(
                system_name="Base ASAG (System 2)",
                y_true=y_true,
                y_pred=y_base,
            ),
            "proposed_asag": compute_all_metrics(
                system_name="Proposed ASAG (System 3)",
                y_true=y_true,
                y_pred=y_proposed,
            ),
        }

    def evaluate_dataset(
        self,
        dataset: MohlerDataset,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        progress_interval: int = 100,
    ) -> EvaluationRunResult:
        """Run complete evaluation across all records in the provided dataset."""
        t0 = time.time()
        results: List[RecordEvaluationResult] = []
        failures: List[Dict[str, Any]] = []

        total_records = len(dataset)

        for idx, record in enumerate(dataset):
            rec_res = self.evaluate_record(record)
            results.append(rec_res)

            if rec_res.status != "SUCCESS":
                failures.append({
                    "question_id": rec_res.question_id,
                    "student_index": rec_res.student_index,
                    "status": rec_res.status,
                    "error_message": rec_res.error_message,
                })

            if progress_callback and (idx + 1) % progress_interval == 0:
                progress_callback(idx + 1, total_records)

        duration = float(round(time.time() - t0, 2))

        # Compute metrics across partitions
        active_results = [r for r in results if r.is_active]
        a1_10_results = [r for r in active_results if r.assignment <= 10]
        exam_results = [r for r in active_results if r.assignment > 10]

        metrics_all = self._compute_subset_metrics(active_results)
        metrics_a1_10 = self._compute_subset_metrics(a1_10_results)
        metrics_exams = self._compute_subset_metrics(exam_results)

        # Question-level metrics
        by_question: Dict[str, Dict[str, EvaluationMetrics]] = {}
        unique_qids = sorted(list({r.question_id for r in active_results}))
        for qid in unique_qids:
            q_recs = [r for r in active_results if r.question_id == qid]
            by_question[qid] = self._compute_subset_metrics(q_recs)

        configuration = {
            "use_cleaned_text": self.use_cleaned_text,
            "max_points": self.max_points,
            "proposed_scorer_config": {
                "correct_additional_weight": self.proposed_asag_runner.scorer.correct_additional_weight,
                "incorrect_additional_penalty": self.proposed_asag_runner.scorer.incorrect_additional_penalty,
                "irrelevant_adjustment": self.proposed_asag_runner.scorer.irrelevant_adjustment,
                "uncertain_adjustment": self.proposed_asag_runner.scorer.uncertain_adjustment,
                "evidence_weighted": self.proposed_asag_runner.scorer.evidence_weighted,
                "max_positive_adjustment": self.proposed_asag_runner.scorer.max_positive_adjustment,
                "max_negative_adjustment": self.proposed_asag_runner.scorer.max_negative_adjustment,
            },
        }

        summary = {
            "total_evaluated_records": len(results),
            "active_records_evaluated": len(active_results),
            "assignments_1_10_records": len(a1_10_results),
            "exams_records": len(exam_results),
            "total_failures": len(failures),
            "duration_seconds": duration,
            "seconds_per_record": float(round(duration / max(1, total_records), 4)),
        }

        return EvaluationRunResult(
            records=results,
            metrics_all=metrics_all,
            metrics_assignments_1_10=metrics_a1_10,
            metrics_exams=metrics_exams,
            metrics_by_question=by_question,
            failures=failures,
            configuration=configuration,
            summary=summary,
        )
