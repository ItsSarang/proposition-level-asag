"""
Severity-Aware Scorer Module (Phase 4D Integration).

Connects the ASAG pipeline components into an end-to-end experimental scoring pipeline:
Student Answer -> Base ASAG -> Matched / Unmatched Propositions ->
Additional-Information Classification -> Contradiction Detection ->
Automatic Severity Estimation -> Model D Scoring -> Final Grade.

CRITICAL ARCHITECTURAL CONSTRAINTS:
1. Isolated experimental candidate: does NOT replace or modify BoundedScorer.
2. Automatic Severity: severity is derived automatically from ContradictionEvidence
   and RobustProposition structures; never passed manually in the execution path.
3. Model D Formulation: exact parameters preserved from Phase 4B:
   - M_pos = 0.25
   - core_invalidation_discount = 0.50
   - minor_penalty_weight = 0.20
   - diminishing_rate = 0.50
   - max_points = 5.0
   - sigma_core_threshold = 0.90
4. Epistemic Safety:
   - Non-contradictions (CORRECT_ADDITIONAL, IRRELEVANT, UNCERTAIN) never receive severity.
   - UNCERTAIN propositions receive zero bonus and zero penalty.
   - UNRESOLVED contradictions (e.g. adjacent entity confusion) receive zero deduction.
   - Full provenance is recorded for every non-zero adjustment.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Union

from base_asag.representation.hybrid import RobustProposition
from evaluation.severity_development.phase4c_severity_estimator import (
    InterpretableSeverityEstimator,
    SeverityEvidence,
    SeverityEstimationResult,
    SeverityLevel,
)
from proposed_asag.classification.robust_classifier import (
    AdditionalInfoClass,
    ClassifiedProposition,
    RobustClassificationResult,
)
from proposed_asag.contradiction.property_contradiction import (
    ContradictionEvidence,
    ContradictionType,
)
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from proposed_asag.overhauled_pipeline import (
        OverhauledASAGPipeline,
        OverhauledASAGResult,
    )


@dataclass(frozen=True)
class SeverityItemizedAdjustment:
    """Detailed adjustment provenance for an individual proposition."""
    proposition_text: str
    classification: str
    severity_level: str
    severity_score: float
    contradiction_type: str
    evidence_strength: float
    adjustment_value: float  # Signed (+ for bonus, - for penalty)
    rationale: str
    severity_evidence: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "proposition_text": self.proposition_text,
            "classification": self.classification,
            "severity_level": self.severity_level,
            "severity_score": round(self.severity_score, 4),
            "contradiction_type": self.contradiction_type,
            "evidence_strength": round(self.evidence_strength, 4),
            "adjustment_value": round(self.adjustment_value, 4),
            "rationale": self.rationale,
            "severity_evidence": self.severity_evidence,
        }


@dataclass(frozen=True)
class SeverityAwareScoreResult:
    """Result of scoring evaluation under the severity-aware Model D formulation."""
    model_name: str
    base_score: float
    core_effective_score: float
    has_core_invalidation: bool
    core_contradiction_count: int
    positive_adjustment: float
    negative_adjustment: float
    net_adjustment: float
    raw_score: float
    final_score: float  # Normalized to [0.0, 1.0]
    final_grade: float  # Scaled to [0.0, max_points]
    is_clipped_upper: bool
    is_clipped_lower: bool
    counts: Dict[str, int]
    itemized_adjustments: List[SeverityItemizedAdjustment]
    explanation: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "base_score": round(self.base_score, 4),
            "core_effective_score": round(self.core_effective_score, 4),
            "has_core_invalidation": self.has_core_invalidation,
            "core_contradiction_count": self.core_contradiction_count,
            "positive_adjustment": round(self.positive_adjustment, 4),
            "negative_adjustment": round(self.negative_adjustment, 4),
            "net_adjustment": round(self.net_adjustment, 4),
            "raw_score": round(self.raw_score, 4),
            "final_score": round(self.final_score, 4),
            "final_grade": round(self.final_grade, 4),
            "is_clipped_upper": self.is_clipped_upper,
            "is_clipped_lower": self.is_clipped_lower,
            "counts": self.counts,
            "itemized_adjustments": [a.to_dict() for a in self.itemized_adjustments],
            "explanation": self.explanation,
            "metadata": self.metadata,
        }


def _extract_props(
    classification_result: Union[RobustClassificationResult, Sequence[ClassifiedProposition]]
) -> List[ClassifiedProposition]:
    if isinstance(classification_result, RobustClassificationResult):
        return list(classification_result.classified_propositions)
    return list(classification_result)


class SeverityAwareScorer:
    """
    Isolated Experimental Scorer: Severity-Aware Model D with Automatic Estimation.

    Core Formulation (Phase 4B Model D):
    1. Core Invalidation Gate:
       Direct contradictions of core defining properties (severity >= sigma_core_threshold)
       discount effective core understanding:
       S_core_effective = S_base * ((1.0 - core_invalidation_discount) ** core_contradiction_count)
    2. Gated Compensation:
       Correct additional propositions receive diminishing positive bonuses:
       raw_bonus = M_pos * (r * n_correct / (1 + r * n_correct))
       pos_adj = min(raw_bonus, 0.50 * S_core_effective)  (strictly 0.0 if S_core_effective == 0)
    3. Peripheral Deductions:
       Minor and moderate contradictions apply bounded additive deductions:
       deduction_i = minor_penalty_weight * severity_score_i
    4. Epistemic Safety:
       Non-contradictions (CORRECT_ADDITIONAL, IRRELEVANT, UNCERTAIN) and UNRESOLVED contradictions
       (e.g., adjacent entity confusion) receive 0.0 penalty.
    """

    def __init__(
        self,
        max_positive_bonus: float = 0.25,
        core_invalidation_discount: float = 0.50,
        minor_penalty_weight: float = 0.20,
        diminishing_rate: float = 0.50,
        max_points: float = 5.0,
        sigma_core_threshold: float = 0.90,
        severity_estimator: Optional[InterpretableSeverityEstimator] = None,
    ) -> None:
        self.max_positive_bonus = max_positive_bonus
        self.core_invalidation_discount = core_invalidation_discount
        self.minor_penalty_weight = minor_penalty_weight
        self.diminishing_rate = diminishing_rate
        self.max_points = max_points
        self.sigma_core_threshold = sigma_core_threshold
        self.severity_estimator = severity_estimator or InterpretableSeverityEstimator()

    def score(
        self,
        base_score: float,
        classification_result: Union[RobustClassificationResult, Sequence[ClassifiedProposition]],
        reference_propositions: Optional[Sequence[RobustProposition]] = None,
        question: str = "",
        domain: Optional[str] = None,
    ) -> SeverityAwareScoreResult:
        """
        Compute final grade by combining base score with automatically estimated
        proposition severities under the Model D formulation.
        """
        props = _extract_props(classification_result)
        ref_props = list(reference_propositions or [])

        n_correct = 0
        n_irrelevant = 0
        n_uncertain = 0
        n_incorrect = 0
        n_matched = 0

        core_contradiction_count = 0
        minor_penalties: List[float] = []
        items: List[SeverityItemizedAdjustment] = []

        for p in props:
            cls = p.classification
            if cls == AdditionalInfoClass.MATCHED_BY_BASE_ASAG:
                n_matched += 1
                items.append(SeverityItemizedAdjustment(
                    proposition_text=p.proposition.source_text,
                    classification=cls.value,
                    severity_level="NONE",
                    severity_score=0.0,
                    contradiction_type="NONE",
                    evidence_strength=1.0,
                    adjustment_value=0.0,
                    rationale="MATCHED: Matched to reference proposition by Base ASAG; included in base coverage.",
                ))

            elif cls == AdditionalInfoClass.CORRECT_ADDITIONAL:
                n_correct += 1
                # Deferred until pos_adj is computed

            elif cls == AdditionalInfoClass.IRRELEVANT:
                n_irrelevant += 1
                items.append(SeverityItemizedAdjustment(
                    proposition_text=p.proposition.source_text,
                    classification=cls.value,
                    severity_level="NONE",
                    severity_score=0.0,
                    contradiction_type="NONE",
                    evidence_strength=0.0,
                    adjustment_value=0.0,
                    rationale="IRRELEVANT: Neutral off-topic proposition produces zero score effect.",
                ))

            elif cls == AdditionalInfoClass.UNCERTAIN:
                n_uncertain += 1
                items.append(SeverityItemizedAdjustment(
                    proposition_text=p.proposition.source_text,
                    classification=cls.value,
                    severity_level="NONE",
                    severity_score=0.0,
                    contradiction_type="NONE",
                    evidence_strength=0.0,
                    adjustment_value=0.0,
                    rationale="UNCERTAIN: Unverified proposition receives zero factual bonus and zero penalty.",
                ))

            elif cls == AdditionalInfoClass.INCORRECT:
                n_incorrect += 1
                # AUTOMATIC SEVERITY ESTIMATION
                sev_res = self.severity_estimator.estimate(
                    contradiction_evidence=p.contradiction_evidence,
                    student_prop=p.proposition,
                    reference_props=ref_props,
                    question=question,
                    domain=domain,
                )
                sev_lvl = sev_res.severity.value
                sev_score = sev_res.severity_score
                ev_dict = sev_res.evidence.to_dict()

                if sev_res.severity == SeverityLevel.UNRESOLVED:
                    # Adjacent entity confusion or unresolved contradiction
                    items.append(SeverityItemizedAdjustment(
                        proposition_text=p.proposition.source_text,
                        classification=cls.value,
                        severity_level=sev_lvl,
                        severity_score=sev_score,
                        contradiction_type=sev_res.evidence.contradiction_type,
                        evidence_strength=sev_res.evidence.evidence_strength,
                        adjustment_value=0.0,
                        rationale=f"UNRESOLVED contradiction ({sev_res.explanation}); produces zero deduction on target entity.",
                        severity_evidence=ev_dict,
                    ))

                elif sev_res.severity == SeverityLevel.NONE or sev_score <= 0.0:
                    items.append(SeverityItemizedAdjustment(
                        proposition_text=p.proposition.source_text,
                        classification=cls.value,
                        severity_level="NONE",
                        severity_score=0.0,
                        contradiction_type="NONE",
                        evidence_strength=0.0,
                        adjustment_value=0.0,
                        rationale=f"Non-contradictory proposition ({sev_res.explanation}); neutral effect (0.0 adjustment).",
                        severity_evidence=ev_dict,
                    ))

                elif sev_score >= self.sigma_core_threshold:
                    # Core defining contradiction
                    core_contradiction_count += 1
                    items.append(SeverityItemizedAdjustment(
                        proposition_text=p.proposition.source_text,
                        classification=cls.value,
                        severity_level=sev_lvl,
                        severity_score=sev_score,
                        contradiction_type=sev_res.evidence.contradiction_type,
                        evidence_strength=sev_res.evidence.evidence_strength,
                        adjustment_value=-self.core_invalidation_discount,
                        rationale=f"CORE INVALIDATION: {sev_res.explanation}",
                        severity_evidence=ev_dict,
                    ))

                else:
                    # Minor or moderate contradiction
                    deduction = self.minor_penalty_weight * sev_score
                    minor_penalties.append(deduction)
                    items.append(SeverityItemizedAdjustment(
                        proposition_text=p.proposition.source_text,
                        classification=cls.value,
                        severity_level=sev_lvl,
                        severity_score=sev_score,
                        contradiction_type=sev_res.evidence.contradiction_type,
                        evidence_strength=sev_res.evidence.evidence_strength,
                        adjustment_value=-deduction,
                        rationale=f"{sev_lvl} DEDUCTION (-{deduction:.4f}): {sev_res.explanation}",
                        severity_evidence=ev_dict,
                    ))

        # 1. Core Invalidation
        has_core_invalidation = (core_contradiction_count > 0)
        if has_core_invalidation:
            core_effective = base_score * ((1.0 - self.core_invalidation_discount) ** core_contradiction_count)
        else:
            core_effective = base_score

        # 2. Gated Positive Bonus
        pos_adj = 0.0
        if n_correct > 0 and core_effective > 0.0:
            scaled_n = self.diminishing_rate * n_correct
            raw_bonus = self.max_positive_bonus * (scaled_n / (1.0 + scaled_n))
            pos_adj = min(raw_bonus, core_effective * 0.50)

        # 3. Itemize correct additional propositions
        for p in props:
            if p.classification == AdditionalInfoClass.CORRECT_ADDITIONAL:
                bonus_per_item = pos_adj / max(1, n_correct)
                items.append(SeverityItemizedAdjustment(
                    proposition_text=p.proposition.source_text,
                    classification=p.classification.value,
                    severity_level="NONE",
                    severity_score=0.0,
                    contradiction_type="NONE",
                    evidence_strength=p.verification_evidence.confidence if p.verification_evidence else 1.0,
                    adjustment_value=bonus_per_item,
                    rationale=f"CORRECT_ADDITIONAL: Gated positive bonus (+{bonus_per_item:.4f}).",
                ))

        # 4. Aggregations and Final Grade
        minor_pen_sum = sum(minor_penalties)
        raw_score = core_effective + pos_adj - minor_pen_sum
        clipped_score = max(0.0, min(1.0, raw_score))
        scaled_grade = clipped_score * self.max_points

        total_effective_penalty = (base_score - core_effective) + minor_pen_sum
        net_adjustment = pos_adj - total_effective_penalty

        counts = {
            "correct_additional": n_correct,
            "irrelevant": n_irrelevant,
            "incorrect": n_incorrect,
            "uncertain": n_uncertain,
            "matched": n_matched,
            "core_contradictions": core_contradiction_count,
            "minor_penalties_count": len(minor_penalties),
        }

        explanation = (
            f"SeverityAwareScorer (Model D): Base={base_score:.4f} -> Effective Core={core_effective:.4f} "
            f"(invalidation={has_core_invalidation}, n_core={core_contradiction_count}), "
            f"+Bonus={pos_adj:.4f}, -MinorPen={minor_pen_sum:.4f} -> Final={clipped_score:.4f} "
            f"(Grade={scaled_grade:.2f}/5.00)"
        )

        return SeverityAwareScoreResult(
            model_name="SeverityAwareScorer (Model D End-to-End)",
            base_score=base_score,
            core_effective_score=core_effective,
            has_core_invalidation=has_core_invalidation,
            core_contradiction_count=core_contradiction_count,
            positive_adjustment=pos_adj,
            negative_adjustment=total_effective_penalty,
            net_adjustment=net_adjustment,
            raw_score=raw_score,
            final_score=clipped_score,
            final_grade=scaled_grade,
            is_clipped_upper=raw_score > 1.0,
            is_clipped_lower=raw_score < 0.0,
            counts=counts,
            itemized_adjustments=items,
            explanation=explanation,
            metadata={
                "M_pos": self.max_positive_bonus,
                "core_invalidation_discount": self.core_invalidation_discount,
                "minor_penalty_weight": self.minor_penalty_weight,
                "diminishing_rate": self.diminishing_rate,
                "sigma_core_threshold": self.sigma_core_threshold,
                "max_points": self.max_points,
            },
        )


@dataclass(frozen=True)
class SeverityAwareEvaluationResult:
    """Complete end-to-end evaluation result with pipeline and severity-aware score traces."""
    question: str
    reference_answer: str
    student_answer: str
    pipeline_result: OverhauledASAGResult
    score_result: SeverityAwareScoreResult

    def to_dict(self) -> Dict[str, Any]:
        return {
            "question": self.question,
            "reference_answer": self.reference_answer,
            "student_answer": self.student_answer,
            "base_score_normalized": round(self.pipeline_result.base_score_normalized, 4),
            "base_score_scaled": round(self.pipeline_result.base_score_scaled, 4),
            "final_score_normalized": round(self.score_result.final_score, 4),
            "final_score_scaled": round(self.score_result.final_grade, 4),
            "has_core_invalidation": self.score_result.has_core_invalidation,
            "core_contradiction_count": self.score_result.core_contradiction_count,
            "positive_adjustment": round(self.score_result.positive_adjustment, 4),
            "negative_adjustment": round(self.score_result.negative_adjustment, 4),
            "net_adjustment": round(self.score_result.net_adjustment, 4),
            "counts": self.score_result.counts,
            "score_result": self.score_result.to_dict(),
            "pipeline_counts": self.pipeline_result.to_dict()["counts"],
            "explanation": self.score_result.explanation,
        }


class SeverityAwarePipeline:
    """
    End-to-End Severity-Aware ASAG Pipeline.
    Coordinates OverhauledASAGPipeline and SeverityAwareScorer with zero manual inputs.
    """

    def __init__(
        self,
        pipeline: Optional[Any] = None,
        scorer: Optional[SeverityAwareScorer] = None,
    ) -> None:
        if pipeline is None:
            from proposed_asag.overhauled_pipeline import OverhauledASAGPipeline
            self.pipeline = OverhauledASAGPipeline()
        else:
            self.pipeline = pipeline
        self.scorer = scorer or SeverityAwareScorer()

    def evaluate(
        self,
        question: str,
        reference_answer: str,
        student_answer: str,
        domain: Optional[str] = None,
    ) -> SeverityAwareEvaluationResult:
        """Execute full end-to-end grading with automatic severity estimation."""
        # 1. Run pipeline
        pipe_res = self.pipeline.evaluate(question, reference_answer, student_answer)

        # 2. Extract reference propositions
        ref_parsed = self.pipeline.parser.parse_document(reference_answer)
        if self.pipeline.use_hybrid_representation:
            ref_props = self.pipeline.hybrid_extractor.extract_document(ref_parsed, reference_answer)
        else:
            from proposed_asag.overhauled_pipeline import relation_to_robust_prop
            ref_triples = self.pipeline.clausal_extractor.extract_document(ref_parsed)
            ref_props = [relation_to_robust_prop(r) for r in ref_triples.canonical_relations]

        # 3. Derive severity and score end-to-end
        classified_props = (
            pipe_res.classification_result.classified_propositions
            if pipe_res.classification_result else []
        )
        score_res = self.scorer.score(
            base_score=pipe_res.base_score_normalized,
            classification_result=classified_props,
            reference_propositions=ref_props,
            question=question,
            domain=domain,
        )

        return SeverityAwareEvaluationResult(
            question=question,
            reference_answer=reference_answer,
            student_answer=student_answer,
            pipeline_result=pipe_res,
            score_result=score_res,
        )
