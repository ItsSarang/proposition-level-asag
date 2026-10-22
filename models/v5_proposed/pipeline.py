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
V5 is the final proposed semantic/dependency ASAG model developed in this project.
TF-IDF (V0) remains stronger than the semantic/dependency models on the primary
full active benchmark; see the frozen Experiment 5 results for the exact evaluation
metrics. All parameters and behavior are FROZEN.
"""
from typing import Any, Dict, Optional, Union
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
    guards, Model D2 scoring, and calibrated hybrid proposition-lexical fusion.
    """

    def __init__(
        self,
        variant: Union[Experiment5Variant, str] = Experiment5Variant.V5,
        enable_core_recovery: Optional[bool] = None,
        enable_canonical_fragments: Optional[bool] = None,
        enable_contradiction_guards: Optional[bool] = None,
        scoring_model: Optional[str] = None,
        enable_additional_info: bool = True,
        enable_hybrid_lexical: bool = True,
        enable_calibration: bool = True,
        hybrid_alpha: float = 0.25,
        calibration_params: Optional[Dict[str, float]] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            variant=variant,
            enable_core_recovery=enable_core_recovery,
            enable_canonical_fragments=enable_canonical_fragments,
            enable_contradiction_guards=enable_contradiction_guards,
            scoring_model=scoring_model,
            enable_additional_info=enable_additional_info,
            enable_hybrid_lexical=enable_hybrid_lexical,
            enable_calibration=enable_calibration,
            hybrid_alpha=hybrid_alpha,
            calibration_params=calibration_params,
        )

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
        if raw_res.metadata.get("enable_hybrid_lexical"):
            lex_sim = raw_res.metadata.get("lexical_similarity", 0.0)
            explanation = (
                f"V5 Proposition-Level ASAG: BaseEffective={raw_res.base_score_effective:.4f}, "
                f"Lexical={lex_sim:.4f}, Grade={raw_res.final_grade:.2f}/5.0"
            )
        else:
            explanation = f"V5 Proposition-Level ASAG: BaseEffective={raw_res.base_score_effective:.4f}, Grade={raw_res.final_grade:.4f}/5.0"

        return GradingResult(
            model_version="V5",
            question=question,
            reference_answer=reference_answer,
            student_answer=student_answer,
            normalized_score=raw_res.final_score,
            grade=raw_res.final_grade,
            max_points=5.0,
            explanation=explanation,
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
