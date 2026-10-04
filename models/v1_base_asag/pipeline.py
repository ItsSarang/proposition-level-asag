"""
V1 Base ASAG Pipeline (Basak et al. 2019-inspired).

Implements the classical semantic and dependency clausal triple ASAG pipeline.
Extracts Subject-Predicate-Object triples, evaluates role-preserved slot
similarity, computes propositional entailment polarity, and scores student
answers strictly by reference proposition coverage.

Research Note:
This is a Basak et al. (2019)-inspired implementation. It does NOT evaluate or
reward unmatched student information (score effect = 0.0), serving as the
strict baseline/control system for proposition-level extensions.
"""
from typing import Any, Dict, Optional
from base_asag.pipeline import BaseASAGPipeline as _BaseASAGPipeline, BaseASAGPipelineResult
from common.types import GradingResult


class BaseASAGPipeline(_BaseASAGPipeline):
    """
    V1 Pipeline adapter supporting both classical .grade() and unified .evaluate().

    Evaluates answers strictly by reference proposition entailment coverage:
    - ENTAILS: 1.0 weight
    - UNCERTAIN: 0.5 weight
    - CONTRADICTS / MISSING: 0.0 weight
    """

    def evaluate(
        self,
        question: str,
        reference_answer: str,
        student_answer: str,
        scale: float = 5.0,
    ) -> GradingResult:
        """
        Evaluate a student answer against the reference using Base ASAG methodology.

        Parameters
        ----------
        question : str
            Question prompt text.
        reference_answer : str
            Ground truth reference answer.
        student_answer : str
            Student response text.
        scale : float, default=5.0
            Maximum point scale for scaled grades.

        Returns
        -------
        GradingResult
            Standardized grading result with normalized score and diagnostic explanation.
        """
        base_res: BaseASAGPipelineResult = self.grade(
            question=question,
            reference_answer=reference_answer,
            student_answer=student_answer,
        )
        grade = base_res.scale_score(max_points=scale)
        return GradingResult(
            model_version="V1",
            question=question,
            reference_answer=reference_answer,
            student_answer=student_answer,
            normalized_score=base_res.normalized_score,
            grade=grade,
            max_points=scale,
            explanation=f"V1 Base ASAG: Normalized={base_res.normalized_score:.4f}, Grade={grade:.4f}/{scale}",
            metadata={"base_result": base_res},
        )


__all__ = ["BaseASAGPipeline", "BaseASAGPipelineResult"]
