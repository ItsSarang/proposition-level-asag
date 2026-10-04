"""Base ASAG Runner (Stage 15.2).

Wraps the Basak-inspired Base ASAG Pipeline (System 2) for evaluation against
the Mohler ASAG dataset.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from base_asag.pipeline import BaseASAGPipeline, BaseASAGPipelineResult
from evaluation.dataset.mohler_loader import MohlerRecord
from evaluation.metrics.asag_metrics import normalize_to_grade


@dataclass(frozen=True)
class BaseASAGPrediction:
    """Individual prediction and relational diagnostics from Base ASAG."""

    normalized_score: float
    grade: float
    total_reference_propositions: int
    matched_count: int
    entailed_count: int
    uncertain_count: int
    contradicted_count: int
    missing_count: int
    unmatched_student_count: int
    status: str
    error_message: Optional[str] = None
    pipeline_result: Optional[BaseASAGPipelineResult] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "base_normalized": self.normalized_score,
            "base_grade": self.grade,
            "base_total_ref_props": self.total_reference_propositions,
            "base_matched_count": self.matched_count,
            "base_entailed_count": self.entailed_count,
            "base_uncertain_count": self.uncertain_count,
            "base_contradicted_count": self.contradicted_count,
            "base_missing_count": self.missing_count,
            "base_unmatched_student_count": self.unmatched_student_count,
            "base_status": self.status,
            "base_error": self.error_message,
        }


class BaseASAGRunner:
    """Runner for System 2: Classical Semantic/Dependency Base ASAG Pipeline."""

    def __init__(self, pipeline: Optional[BaseASAGPipeline] = None) -> None:
        self.pipeline = pipeline or BaseASAGPipeline()

    def evaluate_triplet(
        self,
        question: str,
        reference_answer: str,
        student_answer: str,
        max_points: float = 5.0,
    ) -> BaseASAGPrediction:
        """Execute Base ASAG on a question, reference, and student answer triplet."""
        try:
            result = self.pipeline.grade(
                question=question,
                reference_answer=reference_answer,
                student_answer=student_answer,
            )
            score = float(round(result.normalized_score, 4))
            grade = normalize_to_grade(score, max_points=max_points)

            return BaseASAGPrediction(
                normalized_score=score,
                grade=grade,
                total_reference_propositions=result.total_reference_propositions,
                matched_count=result.matched_count,
                entailed_count=result.entailed_count,
                uncertain_count=result.uncertain_count,
                contradicted_count=result.contradicted_count,
                missing_count=result.missing_count,
                unmatched_student_count=result.unmatched_student_count,
                status="SUCCESS",
                pipeline_result=result,
            )
        except Exception as e:
            return BaseASAGPrediction(
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

    def evaluate_record(
        self,
        record: MohlerRecord,
        use_cleaned_text: bool = True,
        max_points: float = 5.0,
    ) -> BaseASAGPrediction:
        """Evaluate a single MohlerRecord using Base ASAG."""
        stu_text = (
            record.student_answer_cleaned if use_cleaned_text else record.student_answer_raw
        )
        return self.evaluate_triplet(
            question=record.question,
            reference_answer=record.reference_answer,
            student_answer=stu_text,
            max_points=max_points,
        )
