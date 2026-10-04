"""
V4 Severity-Aware Proposition ASAG Pipeline (Experiment 4 / Model D).

Integrates contradiction severity estimation into scoring:
- Core defining contradictions apply a multiplicative invalidation discount
  to the base coverage score (e.g. 0.50 discount factor).
- Minor contradictions apply bounded linear deductions.
- Additional information bonus is gated: no bonus is granted if core propositions
  are invalidated.
- Domain knowledge rules ground computer science concept verifications.

Research Note:
This model corresponds to the frozen Experiment 4 benchmark. Parameters and
scoring behavior are frozen.
"""
from typing import Any, Dict, Optional
from common.types import GradingResult
from proposed_asag.scoring.severity_aware_scorer import (
    SeverityAwarePipeline as _SeverityAwarePipeline,
    SeverityAwareEvaluationResult,
)


class SeverityAwarePipeline(_SeverityAwarePipeline):
    """
    V4 Pipeline adapter returning standardized GradingResult.

    Wraps the Experiment 4 severity-aware grading engine, exposing both unified
    .evaluate() returning GradingResult and .evaluate_raw() returning
    SeverityAwareEvaluationResult.
    """

    def evaluate(
        self,
        question: str,
        reference_answer: str,
        student_answer: str,
        domain: Optional[str] = None,
    ) -> GradingResult:
        """
        Evaluate a student answer using the V4 severity-aware pipeline.

        Parameters
        ----------
        question : str
            Question prompt text.
        reference_answer : str
            Instructor reference answer.
        student_answer : str
            Student response text.
        domain : Optional[str], default=None
            Optional domain context (e.g. 'computer_science').

        Returns
        -------
        GradingResult
            Standardized grading result detailing base score, effective core, and final grade.
        """
        raw_res: SeverityAwareEvaluationResult = super().evaluate(
            question, reference_answer, student_answer, domain=domain
        )
        score_res = raw_res.score_result
        return GradingResult(
            model_version="V4",
            question=question,
            reference_answer=reference_answer,
            student_answer=student_answer,
            normalized_score=score_res.final_score,
            grade=score_res.final_grade,
            max_points=5.0,
            explanation=f"V4 Severity-Aware ASAG: Base={score_res.base_score:.4f}, EffectiveCore={score_res.core_effective_score:.4f}, Grade={score_res.final_grade:.2f}/5.0",
            metadata={"raw_result": raw_res, "score_result": score_res},
        )

    def evaluate_raw(
        self,
        question: str,
        reference_answer: str,
        student_answer: str,
        domain: Optional[str] = None,
    ) -> SeverityAwareEvaluationResult:
        """
        Execute evaluation and return native SeverityAwareEvaluationResult.
        """
        return super().evaluate(question, reference_answer, student_answer, domain=domain)


__all__ = ["SeverityAwarePipeline", "SeverityAwareEvaluationResult"]
