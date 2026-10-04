"""Baseline ASAG Runner (Stage 15.2).

Wraps the TF-IDF + Cosine Similarity Baseline (System 1) for evaluation against
the Mohler ASAG dataset.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from baseline.tfidf_cosine.baseline import TfidfCosineBaseline
from evaluation.dataset.mohler_loader import MohlerRecord
from evaluation.metrics.asag_metrics import normalize_to_grade


@dataclass(frozen=True)
class BaselinePrediction:
    """Individual prediction from the TF-IDF Cosine Baseline."""

    normalized_score: float
    grade: float
    status: str
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "baseline_normalized": self.normalized_score,
            "baseline_grade": self.grade,
            "baseline_status": self.status,
            "baseline_error": self.error_message,
        }


class BaselineRunner:
    """Runner for System 1: TF-IDF + Cosine Similarity Baseline."""

    def __init__(self, baseline: Optional[TfidfCosineBaseline] = None) -> None:
        self.baseline = baseline or TfidfCosineBaseline()

    def evaluate_pair(
        self,
        reference_answer: str,
        student_answer: str,
        max_points: float = 5.0,
    ) -> BaselinePrediction:
        """Compute baseline similarity for a reference and student answer pair."""
        try:
            # Handle empty student answer explicitly
            if not student_answer or not student_answer.strip():
                return BaselinePrediction(
                    normalized_score=0.0,
                    grade=0.0,
                    status="SUCCESS",
                )

            raw_score = self.baseline.similarity(reference_answer, student_answer)
            score_norm = float(round(raw_score, 4))
            grade = normalize_to_grade(score_norm, max_points=max_points)
            return BaselinePrediction(
                normalized_score=score_norm,
                grade=grade,
                status="SUCCESS",
            )
        except Exception as e:
            return BaselinePrediction(
                normalized_score=0.0,
                grade=0.0,
                status="ERROR",
                error_message=str(e),
            )

    def evaluate_record(
        self,
        record: MohlerRecord,
        use_cleaned_text: bool = True,
        max_points: float = 5.0,
    ) -> BaselinePrediction:
        """Evaluate a single MohlerRecord using the baseline system."""
        stu_text = (
            record.student_answer_cleaned if use_cleaned_text else record.student_answer_raw
        )
        return self.evaluate_pair(
            reference_answer=record.reference_answer,
            student_answer=stu_text,
            max_points=max_points,
        )
