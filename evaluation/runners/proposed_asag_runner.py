"""Proposed ASAG Runner (Stage 15.2).

Wraps the Proposition-Level Proposed ASAG Grading Engine (System 3) for evaluation
against the Mohler ASAG dataset.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from base_asag.pipeline import BaseASAGPipelineResult
from evaluation.metrics.asag_metrics import normalize_to_grade
from proposed_asag.scoring.proposed_scorer import ProposedScoreResult, ProposedScorer


@dataclass(frozen=True)
class ProposedASAGPrediction:
    """Individual prediction and adjustment details from Proposed ASAG."""

    base_normalized: float
    base_grade: float
    proposed_normalized: float
    proposed_grade: float
    raw_proposed_score: float
    correct_additional_count: int
    irrelevant_count: int
    incorrect_count: int
    uncertain_count: int
    positive_adjustment: float
    negative_adjustment: float
    net_adjustment: float
    is_clipped_upper: bool
    is_clipped_lower: bool
    status: str
    error_message: Optional[str] = None
    score_result: Optional[ProposedScoreResult] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "proposed_base_normalized": self.base_normalized,
            "proposed_base_grade": self.base_grade,
            "proposed_normalized": self.proposed_normalized,
            "proposed_grade": self.proposed_grade,
            "proposed_raw_score": self.raw_proposed_score,
            "correct_additional_count": self.correct_additional_count,
            "irrelevant_count": self.irrelevant_count,
            "incorrect_count": self.incorrect_count,
            "uncertain_count": self.uncertain_count,
            "positive_adjustment": self.positive_adjustment,
            "negative_adjustment": self.negative_adjustment,
            "net_adjustment": self.net_adjustment,
            "is_clipped_upper": self.is_clipped_upper,
            "is_clipped_lower": self.is_clipped_lower,
            "proposed_status": self.status,
            "proposed_error": self.error_message,
        }


class ProposedASAGRunner:
    """Runner for System 3: Proposition-Level Extended ASAG."""

    def __init__(self, scorer: Optional[ProposedScorer] = None) -> None:
        self.scorer = scorer or ProposedScorer()

    def evaluate_base_result(
        self,
        base_result: BaseASAGPipelineResult,
        max_points: float = 5.0,
    ) -> ProposedASAGPrediction:
        """Score an existing BaseASAGPipelineResult using Proposed ASAG."""
        try:
            score_res = self.scorer.score_document(base_result)
            base_norm = float(round(score_res.base_score, 4))
            base_grade = normalize_to_grade(base_norm, max_points=max_points)

            prop_norm = float(round(score_res.proposed_score, 4))
            prop_grade = normalize_to_grade(prop_norm, max_points=max_points)

            return ProposedASAGPrediction(
                base_normalized=base_norm,
                base_grade=base_grade,
                proposed_normalized=prop_norm,
                proposed_grade=prop_grade,
                raw_proposed_score=score_res.raw_proposed_score,
                correct_additional_count=score_res.correct_additional_count,
                irrelevant_count=score_res.irrelevant_count,
                incorrect_count=score_res.incorrect_count,
                uncertain_count=score_res.uncertain_count,
                positive_adjustment=score_res.positive_adjustment,
                negative_adjustment=score_res.negative_adjustment,
                net_adjustment=score_res.net_adjustment,
                is_clipped_upper=score_res.is_clipped_upper,
                is_clipped_lower=score_res.is_clipped_lower,
                status="SUCCESS",
                score_result=score_res,
            )
        except Exception as e:
            return ProposedASAGPrediction(
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
