"""
V5 Final Proposition-Level ASAG Pipeline (Experiment 5 / Model D2).

Final proposed model of this research project:
1. Core Paraphrase Recovery: Recovers student propositions that paraphrase
   the core reference answer despite syntactic divergence (System Unmatched !=
   Human Additional).
2. Non-Sentential Reference Canonicalization: Handles nominal fragment references
   by synthesizing canonical clausal structures.
3. Contradiction Guards: Eliminates false-positive contradiction triggers from
   lexicon gaps and negation scope anomalies.
4. Model D2 Scoring: Calibrated severity-weighted core invalidation and
   bounded additional information credit.

Research Note:
V5 is the strongest semantic/dependency ASAG model developed in this project
(Pearson r = 0.3444, Spearman rho = 0.3541, MAE = 0.9220).
All parameters and behavior are FROZEN.
"""
from typing import Any, Dict, Optional
from common.types import GradingResult
from proposed_asag.pipeline_v5 import (
    Experiment5Pipeline as _Experiment5Pipeline,
    Experiment5Result,
    Experiment5Variant,
)


class Experiment5Pipeline(_Experiment5Pipeline):
    """
    V5 Pipeline adapter returning standardized GradingResult.

    Coordinates the final Experiment 5 system with core recovery, contradiction
    guards, and Model D2 scoring.
    """

    def evaluate(
        self,
        question: str,
        reference_answer: str,
        student_answer: str,
        domain: Optional[str] = None,
    ) -> GradingResult:
        """
        Evaluate a student answer using the V5 Final ASAG pipeline.

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
            Standardized grading result detailing effective base score and final grade.
        """
        raw_res: Experiment5Result = super().evaluate(
            question, reference_answer, student_answer, domain=domain
        )
        return GradingResult(
            model_version="V5",
            question=question,
            reference_answer=reference_answer,
            student_answer=student_answer,
            normalized_score=raw_res.final_score,
            grade=raw_res.final_grade,
            max_points=5.0,
            explanation=f"V5 Final ASAG: BaseEffective={raw_res.base_score_effective:.4f}, Grade={raw_res.final_grade:.4f}/5.0",
            metadata={"raw_result": raw_res},
        )

    def evaluate_raw(
        self,
        question: str,
        reference_answer: str,
        student_answer: str,
        domain: Optional[str] = None,
    ) -> Experiment5Result:
        """
        Execute evaluation and return native Experiment5Result.
        """
        return super().evaluate(question, reference_answer, student_answer, domain=domain)


__all__ = ["Experiment5Pipeline", "Experiment5Result", "Experiment5Variant"]
