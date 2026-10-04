"""
V2 Proposition-Level ASAG Pipeline (Historical System 3, Stages 11-14).

Extends Base ASAG by extracting unmatched student propositions, categorizing them
into a 4-way taxonomy (CORRECT_ADDITIONAL, IRRELEVANT, INCORRECT, UNCERTAIN),
and applying an additive linear scoring modulation:
- CORRECT_ADDITIONAL: +0.10 bonus
- INCORRECT: -0.20 penalty
- IRRELEVANT / UNCERTAIN: neutral (0.0)

Research Note:
This represents the historical proposed system benchmarked in Stage 15.2.
While reducing MAE, this linear scoring formulation inflated grades on lengthy
answers with filler text, motivating the bounded and severity-aware mechanisms
in subsequent versions.
"""
from typing import Any, Dict, Optional
from base_asag.pipeline import BaseASAGPipeline
from common.types import GradingResult
from proposed_asag.classification.additional_info import AdditionalInformationClassifier
from proposed_asag.proposition.alignment import PropositionAlignmentExtractor
from proposed_asag.proposition.representation import PropositionRepresentationBuilder
from proposed_asag.scoring.proposed_scorer import ProposedScoreResult, ProposedScorer


class V2Pipeline:
    """
    V2 Pipeline adapter coordinating proposition alignment, classification, and scoring.
    """

    def __init__(self, scale: float = 5.0, **kwargs: Any) -> None:
        """
        Initialize V2Pipeline components with default experimental weights.

        Parameters
        ----------
        scale : float, default=5.0
            Maximum point scale for scaled grades.
        """
        self.scale = float(scale)
        self.base_pipeline = BaseASAGPipeline()
        self.alignment_extractor = PropositionAlignmentExtractor()
        self.repr_builder = PropositionRepresentationBuilder()
        self.classifier = AdditionalInformationClassifier()
        self.scorer = ProposedScorer()

    def evaluate(self, question: str, reference_answer: str, student_answer: str) -> GradingResult:
        """
        Evaluate a student answer using the V2 proposition-level pipeline.

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
            Standardized grading result detailing base score and additive net adjustments.
        """
        base_res = self.base_pipeline.grade(question, reference_answer, student_answer)
        score_res: ProposedScoreResult = self.scorer.score_document(base_res)
        grade = float(round(score_res.proposed_score * self.scale, 4))
        return GradingResult(
            model_version="V2",
            question=question,
            reference_answer=reference_answer,
            student_answer=student_answer,
            normalized_score=score_res.proposed_score,
            grade=grade,
            max_points=self.scale,
            explanation=f"V2 Proposed ASAG: Base={score_res.base_score:.4f}, NetAdj={score_res.net_adjustment:.4f}",
            metadata={
                "base_score": score_res.base_score,
                "net_adjustment": score_res.net_adjustment,
                "score_result": score_res,
            },
        )


__all__ = ["V2Pipeline"]
