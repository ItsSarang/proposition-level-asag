"""
V3 Enhanced Proposition-Level ASAG Pipeline (System 4 Overhaul).

Implements the multi-component overhaul:
- Hybrid proposition extraction covering non-clausal constructions
- Hungarian algorithm bipartite assignment for optimal global alignment
- Question-aware relevance filtering
- Property and antonym contradiction detection
- Saturating bounded horizontal-asymptote scoring with diminishing returns
"""
from typing import Any, Dict, Optional
from common.types import GradingResult
from proposed_asag.overhauled_pipeline import (
    OverhauledASAGPipeline as _OverhauledASAGPipeline,
    OverhauledASAGResult,
)


class OverhauledASAGPipeline(_OverhauledASAGPipeline):
    """
    V3 Pipeline adapter returning standardized GradingResult.

    Wraps the overhauled proposition-level pipeline to ensure uniform evaluation
    interface while exposing evaluate_raw() for access to detailed bipartite
    assignment and alignment traces.
    """

    def evaluate(
        self,
        question: str,
        reference_answer: str,
        student_answer: str,
    ) -> GradingResult:
        """
        Evaluate a student answer using the V3 enhanced pipeline.

        Parameters
        ----------
        question : str
            Question prompt text.
        reference_answer : str
            Instructor reference answer.
        student_answer : str
            Student response text.

        Returns
        -------
        GradingResult
            Standardized grading result with bounded score and audit trace.
        """
        raw_res: OverhauledASAGResult = super().evaluate(question, reference_answer, student_answer)
        return GradingResult(
            model_version="V3",
            question=question,
            reference_answer=reference_answer,
            student_answer=student_answer,
            normalized_score=raw_res.final_score_normalized,
            grade=raw_res.final_score_scaled,
            max_points=self.scale,
            explanation=f"V3 Enhanced ASAG: Base={raw_res.base_score_normalized:.4f}, NetAdj={raw_res.net_adjustment:.4f}",
            metadata={"raw_result": raw_res},
        )

    def evaluate_raw(
        self,
        question: str,
        reference_answer: str,
        student_answer: str,
    ) -> OverhauledASAGResult:
        """
        Execute evaluation and return the rich native OverhauledASAGResult.
        """
        return super().evaluate(question, reference_answer, student_answer)


__all__ = ["OverhauledASAGPipeline", "OverhauledASAGResult"]
