"""
Model D2 Soft-Gated Severity-Aware Scorer (Experiment 5 Part D).

Extends the interpretable severity-aware Model D formulation by replacing the hard
zero-gate with a smooth piecewise-linear soft-gate:

g(s_core) =
    gamma * s_core / tau_gate               if s_core < tau_gate
    gamma + (1 - gamma) * (s_core - tau_gate) / (1 - tau_gate)  if s_core >= tau_gate

Initial Candidate Design Parameters:
- tau_gate = 0.30
- gamma = 0.25
- max_positive_bonus (M_pos) = 0.25
- diminishing_rate (r) = 0.50
- core_invalidation_discount = 0.50
- minor_penalty_weight = 0.20
- max_points = 5.0
- sigma_core_threshold = 0.90

Preserves:
1. Exact severity hierarchy: NONE < MINOR < MODERATE < CORE_CONTRADICTION.
2. Invariant constraints R1 through R14.
3. Full itemized provenance tracking for every adjustment.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Union

from base_asag.representation.hybrid import RobustProposition
from evaluation.severity_development.phase4c_severity_estimator import (
    InterpretableSeverityEstimator,
    SeverityLevel,
)
from proposed_asag.classification.robust_classifier import (
    AdditionalInfoClass,
    ClassifiedProposition,
    RobustClassificationResult,
)
from proposed_asag.scoring.severity_aware_scorer import (
    SeverityAwareScoreResult,
    SeverityItemizedAdjustment,
    _extract_props,
)


class ModelD2Scorer:
    """
    Experiment 5 Candidate Scorer: Model D2 with Soft-Gated Compensation.
    """

    def __init__(
        self,
        tau_gate: float = 0.30,
        gamma: float = 0.25,
        max_positive_bonus: float = 0.25,
        core_invalidation_discount: float = 0.50,
        minor_penalty_weight: float = 0.20,
        diminishing_rate: float = 0.50,
        max_points: float = 5.0,
        sigma_core_threshold: float = 0.90,
        severity_estimator: Optional[InterpretableSeverityEstimator] = None,
    ) -> None:
        self.tau_gate = tau_gate
        self.gamma = gamma
        self.max_positive_bonus = max_positive_bonus
        self.core_invalidation_discount = core_invalidation_discount
        self.minor_penalty_weight = minor_penalty_weight
        self.diminishing_rate = diminishing_rate
        self.max_points = max_points
        self.sigma_core_threshold = sigma_core_threshold
        self.severity_estimator = severity_estimator or InterpretableSeverityEstimator()

    def gate_function(self, s_core: float) -> float:
        """
        Piecewise linear soft-gating function g(s_core) in [0.0, 1.0].
        """
        s = max(0.0, min(1.0, s_core))
        if s < self.tau_gate:
            if self.tau_gate <= 0.0:
                return self.gamma
            return self.gamma * (s / self.tau_gate)
        else:
            denom = 1.0 - self.tau_gate
            if denom <= 0.0:
                return 1.0
            return self.gamma + (1.0 - self.gamma) * ((s - self.tau_gate) / denom)

    def score(
        self,
        base_score: float,
        classification_result: Union[RobustClassificationResult, Sequence[ClassifiedProposition]],
        reference_propositions: Optional[Sequence[RobustProposition]] = None,
        question: str = "",
        domain: Optional[str] = None,
    ) -> SeverityAwareScoreResult:
        """
        Compute final grade by combining base score with soft-gated positive bonus
        and severity-aware contradiction deductions.
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

        seen_correct_rules: Set[str] = set()
        unique_correct_props: List[ClassifiedProposition] = []
        seen_contradiction_keys: Set[str] = set()

        for p in props:
            cls = p.classification
            if cls == AdditionalInfoClass.MATCHED_BY_BASE_ASAG:
                n_matched += 1
                items.append(
                    SeverityItemizedAdjustment(
                        proposition_text=p.proposition.source_text,
                        classification=cls.value,
                        severity_level="NONE",
                        severity_score=0.0,
                        contradiction_type="NONE",
                        evidence_strength=1.0,
                        adjustment_value=0.0,
                        rationale="MATCHED: Matched to reference proposition; included in base coverage.",
                    )
                )

            elif cls == AdditionalInfoClass.CORRECT_ADDITIONAL:
                rule_key = (
                    p.verification_evidence.rule_id
                    if p.verification_evidence and p.verification_evidence.rule_id
                    else f"{p.proposition.subject_lemma}_{p.proposition.predicate_lemma}_{p.proposition.object_lemma}_{p.proposition.polarity.value}"
                )
                if rule_key in seen_correct_rules:
                    # Repeated mention of an already credited fact/rule: do not multiply bonus
                    items.append(
                        SeverityItemizedAdjustment(
                            proposition_text=p.proposition.source_text,
                            classification=cls.value,
                            severity_level="NONE",
                            severity_score=0.0,
                            contradiction_type="NONE",
                            evidence_strength=p.verification_evidence.confidence if p.verification_evidence else 1.0,
                            adjustment_value=0.0,
                            rationale=f"CORRECT_ADDITIONAL (REPEATED): Repeated mention of already credited property rule '{rule_key}'; bonus awarded once.",
                        )
                    )
                else:
                    seen_correct_rules.add(rule_key)
                    unique_correct_props.append(p)
                    n_correct += 1

            elif cls == AdditionalInfoClass.IRRELEVANT:
                n_irrelevant += 1
                items.append(
                    SeverityItemizedAdjustment(
                        proposition_text=p.proposition.source_text,
                        classification=cls.value,
                        severity_level="NONE",
                        severity_score=0.0,
                        contradiction_type="NONE",
                        evidence_strength=0.0,
                        adjustment_value=0.0,
                        rationale="IRRELEVANT: Neutral off-topic proposition produces zero score effect.",
                    )
                )

            elif cls == AdditionalInfoClass.UNCERTAIN:
                n_uncertain += 1
                items.append(
                    SeverityItemizedAdjustment(
                        proposition_text=p.proposition.source_text,
                        classification=cls.value,
                        severity_level="NONE",
                        severity_score=0.0,
                        contradiction_type="NONE",
                        evidence_strength=0.0,
                        adjustment_value=0.0,
                        rationale="UNCERTAIN: Unverified proposition receives zero bonus and zero penalty.",
                    )
                )

            elif cls == AdditionalInfoClass.INCORRECT:
                contra_key = (
                    f"{p.contradiction_evidence.conflicting_property}_{p.contradiction_evidence.conflicting_value}"
                    if (p.contradiction_evidence and p.contradiction_evidence.conflicting_property)
                    else (
                        f"{p.contradiction_evidence.conflicting_entity}_{p.contradiction_evidence.conflicting_property}_{p.contradiction_evidence.conflicting_value}"
                        if p.contradiction_evidence
                        else f"{p.proposition.subject_lemma}_{p.proposition.predicate_lemma}_{p.proposition.object_lemma}"
                    )
                )
                if contra_key in seen_contradiction_keys:
                    # Repeated mention of an already penalized contradiction: penalty applied once
                    items.append(
                        SeverityItemizedAdjustment(
                            proposition_text=p.proposition.source_text,
                            classification=cls.value,
                            severity_level="NONE",
                            severity_score=0.0,
                            contradiction_type="NONE",
                            evidence_strength=0.0,
                            adjustment_value=0.0,
                            rationale=f"INCORRECT (REPEATED): Repeated mention of already penalized contradiction ('{contra_key}'); penalty applied once.",
                        )
                    )
                else:
                    seen_contradiction_keys.add(contra_key)
                    n_incorrect += 1
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
                        items.append(
                            SeverityItemizedAdjustment(
                                proposition_text=p.proposition.source_text,
                                classification=cls.value,
                                severity_level=sev_lvl,
                                severity_score=sev_score,
                                contradiction_type=sev_res.evidence.contradiction_type,
                                evidence_strength=sev_res.evidence.evidence_strength,
                                adjustment_value=0.0,
                                rationale=f"UNRESOLVED contradiction ({sev_res.explanation}); zero deduction.",
                                severity_evidence=ev_dict,
                            )
                        )

                    elif sev_res.severity == SeverityLevel.NONE or sev_score <= 0.0:
                        items.append(
                            SeverityItemizedAdjustment(
                                proposition_text=p.proposition.source_text,
                                classification=cls.value,
                                severity_level="NONE",
                                severity_score=0.0,
                                contradiction_type="NONE",
                                evidence_strength=0.0,
                                adjustment_value=0.0,
                                rationale=f"Non-contradictory proposition ({sev_res.explanation}); 0.0 adjustment.",
                                severity_evidence=ev_dict,
                            )
                        )

                    elif sev_score >= self.sigma_core_threshold:
                        core_contradiction_count += 1
                        items.append(
                            SeverityItemizedAdjustment(
                                proposition_text=p.proposition.source_text,
                                classification=cls.value,
                                severity_level=sev_lvl,
                                severity_score=sev_score,
                                contradiction_type=sev_res.evidence.contradiction_type,
                                evidence_strength=sev_res.evidence.evidence_strength,
                                adjustment_value=-self.core_invalidation_discount,
                                rationale=f"CORE INVALIDATION: {sev_res.explanation}",
                                severity_evidence=ev_dict,
                            )
                        )

                    else:
                        deduction = self.minor_penalty_weight * sev_score
                        minor_penalties.append(deduction)
                        items.append(
                            SeverityItemizedAdjustment(
                                proposition_text=p.proposition.source_text,
                                classification=cls.value,
                                severity_level=sev_lvl,
                                severity_score=sev_score,
                                contradiction_type=sev_res.evidence.contradiction_type,
                                evidence_strength=sev_res.evidence.evidence_strength,
                                adjustment_value=-deduction,
                                rationale=f"{sev_lvl} DEDUCTION (-{deduction:.4f}): {sev_res.explanation}",
                                severity_evidence=ev_dict,
                            )
                        )

        # 1. Core Invalidation Gate
        has_core_invalidation = (core_contradiction_count > 0)
        if has_core_invalidation:
            core_effective = base_score * ((1.0 - self.core_invalidation_discount) ** core_contradiction_count)
        else:
            core_effective = base_score

        # 2. Soft-Gated Positive Bonus (Model D2)
        pos_adj = 0.0
        gate_multiplier = self.gate_function(core_effective)
        if n_correct > 0 and gate_multiplier > 0.0:
            scaled_n = self.diminishing_rate * n_correct
            raw_bonus = self.max_positive_bonus * (scaled_n / (1.0 + scaled_n))
            pos_adj = gate_multiplier * raw_bonus

        # 3. Itemize unique correct additional propositions
        for p in unique_correct_props:
            bonus_per_item = pos_adj / max(1, n_correct)
            items.append(
                SeverityItemizedAdjustment(
                    proposition_text=p.proposition.source_text,
                    classification=p.classification.value,
                    severity_level="NONE",
                    severity_score=0.0,
                    contradiction_type="NONE",
                    evidence_strength=p.verification_evidence.confidence if p.verification_evidence else 1.0,
                    adjustment_value=bonus_per_item,
                    rationale=f"CORRECT_ADDITIONAL: Soft-gated bonus (+{bonus_per_item:.4f}; gate={gate_multiplier:.3f}).",
                )
            )

        # 4. Final Aggregation and Bounded Score
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
            f"ModelD2Scorer: Base={base_score:.4f} -> Effective Core={core_effective:.4f} "
            f"(invalidation={has_core_invalidation}, n_core={core_contradiction_count}), "
            f"+SoftBonus={pos_adj:.4f} (gate={gate_multiplier:.3f}), -MinorPen={minor_pen_sum:.4f} "
            f"-> Final={clipped_score:.4f} (Grade={scaled_grade:.2f}/5.00)"
        )

        return SeverityAwareScoreResult(
            model_name="ModelD2Scorer (Soft-Gated Severity-Aware)",
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
            is_clipped_upper=(raw_score > 1.0),
            is_clipped_lower=(raw_score < 0.0),
            counts=counts,
            itemized_adjustments=items,
            explanation=explanation,
            metadata={
                "tau_gate": self.tau_gate,
                "gamma": self.gamma,
                "gate_multiplier": round(gate_multiplier, 4),
            },
        )
