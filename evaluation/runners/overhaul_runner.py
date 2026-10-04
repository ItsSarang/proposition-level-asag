"""
Overhauled ASAG Runner (System 4).

Wraps the Overhauled Proposed ASAG Grading Engine for evaluation against
the Mohler ASAG dataset and comparative benchmarking.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from evaluation.metrics.asag_metrics import normalize_to_grade
from proposed_asag.overhauled_pipeline import OverhauledASAGPipeline, OverhauledASAGResult


@dataclass(frozen=True)
class OverhaulASAGPrediction:
    """Individual prediction and diagnostic details from Overhauled ASAG (System 4)."""
    normalized_score: float
    grade: float
    base_normalized: float
    base_grade: float
    positive_adjustment: float
    negative_adjustment: float
    net_adjustment: float
    is_clipped_upper: bool
    is_clipped_lower: bool
    correct_additional_count: int
    irrelevant_count: int
    incorrect_count: int
    uncertain_count: int
    matched_propositions_count: int
    reference_propositions_count: int
    unmatched_student_propositions_count: int
    status: str
    error_message: Optional[str] = None
    pipeline_result: Optional[OverhauledASAGResult] = None
    direct_matches_count: int = 0
    cross_slot_matches_count: int = 0
    student_propositions_count: int = 0
    entailment_decisions: tuple = ()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overhaul_normalized": round(self.normalized_score, 4),
            "overhaul_grade": round(self.grade, 4),
            "overhaul_base_normalized": round(self.base_normalized, 4),
            "overhaul_base_grade": round(self.base_grade, 4),
            "overhaul_pos_adj": round(self.positive_adjustment, 4),
            "overhaul_neg_adj": round(self.negative_adjustment, 4),
            "overhaul_net_adj": round(self.net_adjustment, 4),
            "overhaul_clipped_upper": self.is_clipped_upper,
            "overhaul_clipped_lower": self.is_clipped_lower,
            "overhaul_correct_additional": self.correct_additional_count,
            "overhaul_irrelevant": self.irrelevant_count,
            "overhaul_incorrect": self.incorrect_count,
            "overhaul_uncertain": self.uncertain_count,
            "overhaul_matched_count": self.matched_propositions_count,
            "overhaul_ref_props_count": self.reference_propositions_count,
            "overhaul_unmatched_student_count": self.unmatched_student_propositions_count,
            "overhaul_direct_matches_count": self.direct_matches_count,
            "overhaul_cross_slot_matches_count": self.cross_slot_matches_count,
            "overhaul_student_propositions_count": self.student_propositions_count,
            "overhaul_entailment_decisions": list(self.entailment_decisions),
            "overhaul_status": self.status,
            "overhaul_error": self.error_message,
        }


class OverhaulASAGRunner:
    """Runner for System 4: Overhauled Proposed ASAG."""

    def __init__(self, pipeline: Optional[OverhauledASAGPipeline] = None) -> None:
        self.pipeline = pipeline or OverhauledASAGPipeline()

    def evaluate_triplet(
        self,
        question: str,
        reference_answer: str,
        student_answer: str,
        max_points: float = 5.0,
    ) -> OverhaulASAGPrediction:
        """Evaluate a single question-reference-student answer triplet."""
        try:
            res = self.pipeline.evaluate(
                question=question,
                reference_answer=reference_answer,
                student_answer=student_answer,
            )
            return OverhaulASAGPrediction(
                normalized_score=res.final_score_normalized,
                grade=normalize_to_grade(res.final_score_normalized, max_points=max_points),
                base_normalized=res.base_score_normalized,
                base_grade=normalize_to_grade(res.base_score_normalized, max_points=max_points),
                positive_adjustment=res.positive_adjustment,
                negative_adjustment=res.negative_adjustment,
                net_adjustment=res.net_adjustment,
                is_clipped_upper=res.is_clipped_upper,
                is_clipped_lower=res.is_clipped_lower,
                correct_additional_count=res.correct_additional_count,
                irrelevant_count=res.irrelevant_count,
                incorrect_count=res.incorrect_count,
                uncertain_count=res.uncertain_count,
                matched_propositions_count=res.matched_propositions_count,
                reference_propositions_count=res.reference_propositions_count,
                unmatched_student_propositions_count=res.unmatched_student_propositions_count,
                status="SUCCESS",
                pipeline_result=res,
                direct_matches_count=res.direct_matches_count,
                cross_slot_matches_count=res.cross_slot_matches_count,
                student_propositions_count=res.student_propositions_count,
                entailment_decisions=tuple(res.entailment_decisions),
            )
        except Exception as e:
            return OverhaulASAGPrediction(
                normalized_score=0.0,
                grade=0.0,
                base_normalized=0.0,
                base_grade=0.0,
                positive_adjustment=0.0,
                negative_adjustment=0.0,
                net_adjustment=0.0,
                is_clipped_upper=False,
                is_clipped_lower=False,
                correct_additional_count=0,
                irrelevant_count=0,
                incorrect_count=0,
                uncertain_count=0,
                matched_propositions_count=0,
                reference_propositions_count=0,
                unmatched_student_propositions_count=0,
                status="ERROR",
                error_message=str(e),
                pipeline_result=None,
                direct_matches_count=0,
                cross_slot_matches_count=0,
                student_propositions_count=0,
                entailment_decisions=(),
            )
