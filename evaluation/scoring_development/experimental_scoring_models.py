"""
Experimental Scoring Formulations Module (Phase 4A Development).

Provides isolated implementations of candidate proposition-level scoring models
for controlled evaluation, without modifying the production scorer.

Candidate Models:
- Model A: Current Additive Saturating Scorer (Production Baseline)
- Model B: Proportional Penalty Scorer (Multiplicative Degradation)
- Model C: Evidence-Weighted Bounded Severity Penalty Scorer
- Model D: Core / Additional Decomposition with Gated Compensation
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Union

from proposed_asag.classification.robust_classifier import (
    AdditionalInfoClass,
    ClassifiedProposition,
    RobustClassificationResult,
)
from proposed_asag.contradiction.property_contradiction import ContradictionType


@dataclass(frozen=True)
class ItemizedAdjustment:
    """Detailed adjustment provenance for an individual proposition."""
    proposition_text: str
    classification: str
    evidence_type: str
    evidence_strength: float
    severity: float
    adjustment_value: float  # Signed (+ for bonus, - for penalty)
    rationale: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "proposition_text": self.proposition_text,
            "classification": self.classification,
            "evidence_type": self.evidence_type,
            "evidence_strength": round(self.evidence_strength, 4),
            "severity": round(self.severity, 4),
            "adjustment_value": round(self.adjustment_value, 4),
            "rationale": self.rationale,
        }


@dataclass(frozen=True)
class CandidateScoreResult:
    """Result of scoring evaluation under a candidate formulation."""
    model_name: str
    base_score: float
    positive_adjustment: float
    negative_adjustment: float
    net_adjustment: float
    raw_score: float
    clipped_score: float
    scaled_score: float  # Scaled to [0, max_points]
    is_clipped_upper: bool
    is_clipped_lower: bool
    itemized_adjustments: List[ItemizedAdjustment]
    explanation: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "base_score": round(self.base_score, 4),
            "positive_adjustment": round(self.positive_adjustment, 4),
            "negative_adjustment": round(self.negative_adjustment, 4),
            "net_adjustment": round(self.net_adjustment, 4),
            "raw_score": round(self.raw_score, 4),
            "clipped_score": round(self.clipped_score, 4),
            "scaled_score": round(self.scaled_score, 4),
            "is_clipped_upper": self.is_clipped_upper,
            "is_clipped_lower": self.is_clipped_lower,
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


def _compute_severity(p: ClassifiedProposition, explicit_severity: Optional[str] = None) -> float:
    """
    Extract or assign interpretable severity signal:
    - 1.00: Direct contradiction of core defining property (CORE_CONTRADICTION)
    - 0.60: Moderate conceptual/relational mistake (MODERATE)
    - 0.25: Minor/peripheral factual mistake (MINOR)
    - 0.00: Non-contradictory

    When explicit_severity is passed, uses the experimental dataset annotation.
    Otherwise, extracts conservatively from existing contradiction evidence structures.
    """
    if p.classification != AdditionalInfoClass.INCORRECT:
        return 0.0

    if explicit_severity:
        exp_up = explicit_severity.upper()
        if exp_up == "CORE_CONTRADICTION":
            return 1.00
        if exp_up == "MODERATE":
            return 0.60
        if exp_up == "MINOR":
            return 0.25

    ev = p.contradiction_evidence
    if ev is None or not ev.is_contradicted:
        return 0.30

    if ev.contradiction_type in (ContradictionType.VALUE_CONFLICT, ContradictionType.EXPLICIT_NEGATION):
        return 1.00
    if ev.contradiction_type == ContradictionType.ANTONYM_CONFLICT:
        return 0.60
    return 0.30


def _get_prop_severity(
    p: ClassifiedProposition,
    idx: int,
    severities: Optional[Dict[str, str]] = None,
) -> float:
    """Resolve severity from experimental annotations if available, otherwise from evidence."""
    if severities:
        if p.proposition.source_text in severities:
            return _compute_severity(p, severities[p.proposition.source_text])
        if str(idx) in severities:
            return _compute_severity(p, severities[str(idx)])
        # Check partial string matching in severities keys
        p_text_lower = p.proposition.source_text.lower()
        for k, v in severities.items():
            if k.lower() in p_text_lower:
                return _compute_severity(p, v)
    return _compute_severity(p)



# ============================================================================
# MODEL A — Current Additive Saturating Scorer (Production Baseline)
# ============================================================================

class ModelA_CurrentAdditiveScorer:
    """
    Model A: Current Production Scorer (BoundedScorer in SATURATING mode).
    S_final = clip(S_base + pos_adj - neg_adj, 0.0, 1.0)
    pos_adj = M_pos * (r * n_correct / (1 + r * n_correct))
    neg_adj = M_neg * (0.5 * n_incorrect / (1 + 0.5 * n_incorrect))
    """

    def __init__(
        self,
        max_positive_bonus: float = 0.30,
        max_negative_penalty: float = 0.40,
        diminishing_rate: float = 0.50,
        max_points: float = 5.0,
    ) -> None:
        self.max_positive_bonus = max_positive_bonus
        self.max_negative_penalty = max_negative_penalty
        self.diminishing_rate = diminishing_rate
        self.max_points = max_points

    def score(
        self,
        base_score: float,
        classification_result: Union[RobustClassificationResult, Sequence[ClassifiedProposition]],
        severities: Optional[Dict[str, str]] = None,
    ) -> CandidateScoreResult:
        props = _extract_props(classification_result)
        n_correct = sum(1 for p in props if p.classification == AdditionalInfoClass.CORRECT_ADDITIONAL)
        n_incorrect = sum(1 for p in props if p.classification == AdditionalInfoClass.INCORRECT)

        pos_adj = 0.0
        if n_correct > 0:
            scaled_n = self.diminishing_rate * n_correct
            pos_adj = self.max_positive_bonus * (scaled_n / (1.0 + scaled_n))

        neg_adj = 0.0
        if n_incorrect > 0:
            scaled_neg = 0.50 * n_incorrect
            neg_adj = self.max_negative_penalty * (scaled_neg / (1.0 + scaled_neg))

        net_adj = pos_adj - neg_adj
        raw = base_score + net_adj
        clipped = max(0.0, min(1.0, raw))

        items: List[ItemizedAdjustment] = []
        for idx, p in enumerate(props):
            if p.classification == AdditionalInfoClass.CORRECT_ADDITIONAL:
                items.append(ItemizedAdjustment(
                    proposition_text=p.proposition.source_text,
                    classification=p.classification.value,
                    evidence_type="SUPPORTED" if p.verification_evidence else "RELEVANT",
                    evidence_strength=1.0,
                    severity=0.0,
                    adjustment_value=pos_adj / max(1, n_correct),
                    rationale=f"Correct additional information (shared saturating bonus).",
                ))
            elif p.classification == AdditionalInfoClass.INCORRECT:
                severity = _get_prop_severity(p, idx, severities)
                items.append(ItemizedAdjustment(
                    proposition_text=p.proposition.source_text,
                    classification=p.classification.value,
                    evidence_type=p.contradiction_evidence.contradiction_type.value if p.contradiction_evidence else "NONE",
                    evidence_strength=p.contradiction_evidence.evidence_strength if p.contradiction_evidence else 0.0,
                    severity=severity,
                    adjustment_value=-(neg_adj / max(1, n_incorrect)),
                    rationale=f"Incorrect additional statement (shared saturating deduction).",
                ))
            else:
                items.append(ItemizedAdjustment(
                    proposition_text=p.proposition.source_text,
                    classification=p.classification.value,
                    evidence_type="NONE",
                    evidence_strength=0.0,
                    severity=0.0,
                    adjustment_value=0.0,
                    rationale=f"{p.classification.value}: neutral effect (0.0 adjustment).",
                ))

        return CandidateScoreResult(
            model_name="Model A (Current Additive Saturating)",
            base_score=base_score,
            positive_adjustment=pos_adj,
            negative_adjustment=neg_adj,
            net_adjustment=net_adj,
            raw_score=raw,
            clipped_score=clipped,
            scaled_score=clipped * self.max_points,
            is_clipped_upper=raw > 1.0,
            is_clipped_lower=raw < 0.0,
            itemized_adjustments=items,
            explanation=f"Model A: Base={base_score:.4f}, +{pos_adj:.4f}, -{neg_adj:.4f} -> Final={clipped:.4f}",
            metadata={"M_pos": self.max_positive_bonus, "M_neg": self.max_negative_penalty, "r": self.diminishing_rate},
        )


# ============================================================================
# MODEL B — Proportional Penalty Scorer (Multiplicative Degradation)
# ============================================================================

class ModelB_ProportionalPenaltyScorer:
    """
    Model B: Proportional Penalty Scorer.
    Incorrect additions degrade earned credit multiplicatively rather than acting
    as a flat additive deduction.
    S_final = clip((S_base + pos_adj) * prod(1.0 - penalty_rate_i), 0.0, 1.0)
    """

    def __init__(
        self,
        max_positive_bonus: float = 0.30,
        penalty_per_incorrect: float = 0.35,
        diminishing_rate: float = 0.50,
        max_points: float = 5.0,
    ) -> None:
        self.max_positive_bonus = max_positive_bonus
        self.penalty_per_incorrect = penalty_per_incorrect
        self.diminishing_rate = diminishing_rate
        self.max_points = max_points

    def score(
        self,
        base_score: float,
        classification_result: Union[RobustClassificationResult, Sequence[ClassifiedProposition]],
        severities: Optional[Dict[str, str]] = None,
    ) -> CandidateScoreResult:
        props = _extract_props(classification_result)
        n_correct = sum(1 for p in props if p.classification == AdditionalInfoClass.CORRECT_ADDITIONAL)
        incorrect_props = [p for p in props if p.classification == AdditionalInfoClass.INCORRECT]

        pos_adj = 0.0
        if n_correct > 0:
            scaled_n = self.diminishing_rate * n_correct
            pos_adj = self.max_positive_bonus * (scaled_n / (1.0 + scaled_n))

        credit_before_penalty = base_score + pos_adj
        multiplication_factor = 1.0
        items: List[ItemizedAdjustment] = []

        for idx, p in enumerate(props):
            if p.classification == AdditionalInfoClass.CORRECT_ADDITIONAL:
                items.append(ItemizedAdjustment(
                    proposition_text=p.proposition.source_text,
                    classification=p.classification.value,
                    evidence_type="SUPPORTED" if p.verification_evidence else "RELEVANT",
                    evidence_strength=1.0,
                    severity=0.0,
                    adjustment_value=pos_adj / max(1, n_correct),
                    rationale="Correct additional bonus.",
                ))
            elif p.classification == AdditionalInfoClass.INCORRECT:
                severity = _get_prop_severity(p, idx, severities)
                p_rate = self.penalty_per_incorrect * severity
                multiplication_factor *= (1.0 - p_rate)
                items.append(ItemizedAdjustment(
                    proposition_text=p.proposition.source_text,
                    classification=p.classification.value,
                    evidence_type=p.contradiction_evidence.contradiction_type.value if p.contradiction_evidence else "NONE",
                    evidence_strength=p.contradiction_evidence.evidence_strength if p.contradiction_evidence else 0.0,
                    severity=severity,
                    adjustment_value=-p_rate,
                    rationale=f"Proportional penalty factor (1.0 - {p_rate:.2f}).",
                ))
            else:
                items.append(ItemizedAdjustment(
                    proposition_text=p.proposition.source_text,
                    classification=p.classification.value,
                    evidence_type="NONE",
                    evidence_strength=0.0,
                    severity=0.0,
                    adjustment_value=0.0,
                    rationale=f"{p.classification.value}: neutral effect.",
                ))

        raw = credit_before_penalty * multiplication_factor
        clipped = max(0.0, min(1.0, raw))
        effective_neg_adj = credit_before_penalty - raw

        return CandidateScoreResult(
            model_name="Model B (Proportional Penalty)",
            base_score=base_score,
            positive_adjustment=pos_adj,
            negative_adjustment=effective_neg_adj,
            net_adjustment=pos_adj - effective_neg_adj,
            raw_score=raw,
            clipped_score=clipped,
            scaled_score=clipped * self.max_points,
            is_clipped_upper=raw > 1.0,
            is_clipped_lower=raw < 0.0,
            itemized_adjustments=items,
            explanation=f"Model B: (Base {base_score:.4f} + Pos {pos_adj:.4f}) * Factor {multiplication_factor:.4f} -> Final={clipped:.4f}",
            metadata={"penalty_per_incorrect": self.penalty_per_incorrect, "mult_factor": multiplication_factor},
        )


# ============================================================================
# MODEL C — Evidence-Weighted Bounded Severity Penalty Scorer
# ============================================================================

class ModelC_EvidenceWeightedSeverityScorer:
    """
    Model C: Evidence-Weighted Bounded Severity Penalty Scorer.
    Penalties scale directly with contradiction evidence strength and semantic severity:
    deduction_i = severity_i * evidence_strength_i * base_penalty_weight
    neg_adj = saturating_bounded(sum(deduction_i))
    S_final = clip(S_base + pos_adj - neg_adj, 0.0, 1.0)
    """

    def __init__(
        self,
        max_positive_bonus: float = 0.30,
        base_penalty_weight: float = 0.40,
        max_negative_penalty: float = 0.70,
        diminishing_rate: float = 0.50,
        max_points: float = 5.0,
    ) -> None:
        self.max_positive_bonus = max_positive_bonus
        self.base_penalty_weight = base_penalty_weight
        self.max_negative_penalty = max_negative_penalty
        self.diminishing_rate = diminishing_rate
        self.max_points = max_points

    def score(
        self,
        base_score: float,
        classification_result: Union[RobustClassificationResult, Sequence[ClassifiedProposition]],
        severities: Optional[Dict[str, str]] = None,
    ) -> CandidateScoreResult:
        props = _extract_props(classification_result)
        n_correct = sum(1 for p in props if p.classification == AdditionalInfoClass.CORRECT_ADDITIONAL)

        pos_adj = 0.0
        if n_correct > 0:
            scaled_n = self.diminishing_rate * n_correct
            pos_adj = self.max_positive_bonus * (scaled_n / (1.0 + scaled_n))

        raw_penalties: List[float] = []
        items: List[ItemizedAdjustment] = []

        for idx, p in enumerate(props):
            if p.classification == AdditionalInfoClass.CORRECT_ADDITIONAL:
                items.append(ItemizedAdjustment(
                    proposition_text=p.proposition.source_text,
                    classification=p.classification.value,
                    evidence_type="SUPPORTED" if p.verification_evidence else "RELEVANT",
                    evidence_strength=1.0,
                    severity=0.0,
                    adjustment_value=pos_adj / max(1, n_correct),
                    rationale="Correct additional bonus.",
                ))
            elif p.classification == AdditionalInfoClass.INCORRECT:
                severity = _get_prop_severity(p, idx, severities)
                ev_strength = p.contradiction_evidence.evidence_strength if p.contradiction_evidence else 0.80
                deduction = severity * ev_strength * self.base_penalty_weight
                raw_penalties.append(deduction)
                items.append(ItemizedAdjustment(
                    proposition_text=p.proposition.source_text,
                    classification=p.classification.value,
                    evidence_type=p.contradiction_evidence.contradiction_type.value if p.contradiction_evidence else "NONE",
                    evidence_strength=ev_strength,
                    severity=severity,
                    adjustment_value=-deduction,
                    rationale=f"Evidence-weighted deduction (severity={severity:.2f}, ev_str={ev_strength:.2f}).",
                ))
            else:
                items.append(ItemizedAdjustment(
                    proposition_text=p.proposition.source_text,
                    classification=p.classification.value,
                    evidence_type="NONE",
                    evidence_strength=0.0,
                    severity=0.0,
                    adjustment_value=0.0,
                    rationale=f"{p.classification.value}: neutral effect.",
                ))

        sum_raw_penalties = sum(raw_penalties)
        # Saturating aggregation to max_negative_penalty
        if sum_raw_penalties > 0:
            neg_adj = self.max_negative_penalty * (sum_raw_penalties / (1.0 + sum_raw_penalties))
        else:
            neg_adj = 0.0

        net_adj = pos_adj - neg_adj
        raw = base_score + net_adj
        clipped = max(0.0, min(1.0, raw))

        return CandidateScoreResult(
            model_name="Model C (Evidence-Weighted Severity)",
            base_score=base_score,
            positive_adjustment=pos_adj,
            negative_adjustment=neg_adj,
            net_adjustment=net_adj,
            raw_score=raw,
            clipped_score=clipped,
            scaled_score=clipped * self.max_points,
            is_clipped_upper=raw > 1.0,
            is_clipped_lower=raw < 0.0,
            itemized_adjustments=items,
            explanation=f"Model C: Base={base_score:.4f}, +{pos_adj:.4f}, -{neg_adj:.4f} (raw pen={sum_raw_penalties:.4f}) -> Final={clipped:.4f}",
            metadata={"base_penalty_weight": self.base_penalty_weight, "max_penalty": self.max_negative_penalty},
        )


# ============================================================================
# MODEL D — Core / Additional Decomposition with Gated Compensation
# ============================================================================

class ModelD_CoreAdditionalDecompositionScorer:
    """
    Model D: Core / Additional Decomposition with Gated Compensation.
    Explicitly separates core reference coverage from additional proposition evaluation:
    1. If an incorrect additional proposition directly contradicts a defining property
       of the core entity (severity >= 0.90), it invalidates core understanding:
       S_core_effective = S_base * (1.0 - core_invalidation_discount)
    2. Peripheral incorrect propositions apply bounded additive deductions.
    3. Correct additional information is bounded and CANNOT compensate for missing core content:
       Bonus capped at min(S_core_effective, max_positive_bonus).
    """

    def __init__(
        self,
        max_positive_bonus: float = 0.25,
        core_invalidation_discount: float = 0.50,
        minor_penalty_weight: float = 0.20,
        diminishing_rate: float = 0.50,
        max_points: float = 5.0,
    ) -> None:
        self.max_positive_bonus = max_positive_bonus
        self.core_invalidation_discount = core_invalidation_discount
        self.minor_penalty_weight = minor_penalty_weight
        self.diminishing_rate = diminishing_rate
        self.max_points = max_points

    def score(
        self,
        base_score: float,
        classification_result: Union[RobustClassificationResult, Sequence[ClassifiedProposition]],
        severities: Optional[Dict[str, str]] = None,
    ) -> CandidateScoreResult:
        props = _extract_props(classification_result)
        n_correct = sum(1 for p in props if p.classification == AdditionalInfoClass.CORRECT_ADDITIONAL)

        has_core_invalidation = False
        minor_penalties: List[float] = []
        items: List[ItemizedAdjustment] = []

        for idx, p in enumerate(props):
            if p.classification == AdditionalInfoClass.CORRECT_ADDITIONAL:
                # Track correct
                pass
            elif p.classification == AdditionalInfoClass.INCORRECT:
                severity = _get_prop_severity(p, idx, severities)
                if severity >= 0.90:
                    has_core_invalidation = True
                    items.append(ItemizedAdjustment(
                        proposition_text=p.proposition.source_text,
                        classification=p.classification.value,
                        evidence_type=p.contradiction_evidence.contradiction_type.value if p.contradiction_evidence else "NONE",
                        evidence_strength=p.contradiction_evidence.evidence_strength if p.contradiction_evidence else 0.90,
                        severity=severity,
                        adjustment_value=-self.core_invalidation_discount,
                        rationale="CORE INVALIDATION: Direct contradiction of core defining property discounts effective core understanding.",
                    ))
                else:
                    ded = self.minor_penalty_weight * severity
                    minor_penalties.append(ded)
                    items.append(ItemizedAdjustment(
                        proposition_text=p.proposition.source_text,
                        classification=p.classification.value,
                        evidence_type=p.contradiction_evidence.contradiction_type.value if p.contradiction_evidence else "NONE",
                        evidence_strength=p.contradiction_evidence.evidence_strength if p.contradiction_evidence else 0.50,
                        severity=severity,
                        adjustment_value=-ded,
                        rationale=f"Minor peripheral deduction ({ded:.2f}).",
                    ))
            else:
                items.append(ItemizedAdjustment(
                    proposition_text=p.proposition.source_text,
                    classification=p.classification.value,
                    evidence_type="NONE",
                    evidence_strength=0.0,
                    severity=0.0,
                    adjustment_value=0.0,
                    rationale=f"{p.classification.value}: neutral effect.",
                ))

        # Core discount
        if has_core_invalidation:
            core_effective = base_score * (1.0 - self.core_invalidation_discount)
        else:
            core_effective = base_score

        # Gated bonus: cannot compensate if core_effective is zero, capped by core_effective
        pos_adj = 0.0
        if n_correct > 0 and core_effective > 0.0:
            scaled_n = self.diminishing_rate * n_correct
            raw_bonus = self.max_positive_bonus * (scaled_n / (1.0 + scaled_n))
            pos_adj = min(raw_bonus, core_effective * 0.50)

        # Record correct items with computed pos_adj
        for p in props:
            if p.classification == AdditionalInfoClass.CORRECT_ADDITIONAL:
                items.append(ItemizedAdjustment(
                    proposition_text=p.proposition.source_text,
                    classification=p.classification.value,
                    evidence_type="SUPPORTED" if p.verification_evidence else "RELEVANT",
                    evidence_strength=1.0,
                    severity=0.0,
                    adjustment_value=pos_adj / max(1, n_correct),
                    rationale="Gated correct additional bonus.",
                ))

        minor_pen = sum(minor_penalties)
        raw = core_effective + pos_adj - minor_pen
        clipped = max(0.0, min(1.0, raw))

        total_effective_penalty = base_score - core_effective + minor_pen

        return CandidateScoreResult(
            model_name="Model D (Core/Additional Decomposition)",
            base_score=base_score,
            positive_adjustment=pos_adj,
            negative_adjustment=total_effective_penalty,
            net_adjustment=pos_adj - total_effective_penalty,
            raw_score=raw,
            clipped_score=clipped,
            scaled_score=clipped * self.max_points,
            is_clipped_upper=raw > 1.0,
            is_clipped_lower=raw < 0.0,
            itemized_adjustments=items,
            explanation=(
                f"Model D: Base={base_score:.4f} -> Effective Core={core_effective:.4f} "
                f"(invalidation={has_core_invalidation}), +{pos_adj:.4f}, -{minor_pen:.4f} -> Final={clipped:.4f}"
            ),
            metadata={"has_core_invalidation": has_core_invalidation, "core_effective": core_effective},
        )
