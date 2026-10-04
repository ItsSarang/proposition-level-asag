"""
Deterministic Grading Explanation Trace Generator (Phase 9).

Produces structured, human-interpretable and machine-readable explanation traces
for ASAG decisions without opaque models or LLMs.
Deconstructs grading into:
1. Matched Core Information (reference proposition coverage and entailment)
2. Correct Additional Information (relevant, non-contradictory extensions)
3. Irrelevant Information (off-topic or domain-peripheral additions)
4. Contradictory Information (direct property, polarity, or antonym conflicts)
5. Full Mathematical Score Breakdown (Base score, adjustments, strategy, bounds)
"""

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Union

from proposed_asag.classification.robust_classifier import (
    AdditionalInfoClass,
    ClassifiedProposition,
    RobustClassificationResult,
)
from proposed_asag.scoring.bounded_scorer import BoundedScoreResult


@dataclass(frozen=True)
class MatchedTraceItem:
    """Trace details for a matched core proposition."""
    reference_statement: str
    student_statement: str
    match_score: float
    entailment_status: str
    evidence_summary: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "reference_statement": self.reference_statement,
            "student_statement": self.student_statement,
            "match_score": round(self.match_score, 4),
            "entailment_status": self.entailment_status,
            "evidence_summary": self.evidence_summary,
        }


@dataclass(frozen=True)
class AdditionalTraceItem:
    """Trace details for an additional proposition evaluated by the classifier."""
    text: str
    classification: str
    relevance_strength: Optional[float]
    contradiction_type: Optional[str]
    rationale: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "classification": self.classification,
            "relevance_strength": round(self.relevance_strength, 4) if self.relevance_strength is not None else None,
            "contradiction_type": self.contradiction_type,
            "rationale": self.rationale,
        }


@dataclass(frozen=True)
class GradingExplanationTrace:
    """
    Comprehensive, auditable explanation trace for an evaluated student answer.
    """
    question: str
    reference_answer: str
    student_answer: str
    scale: float
    base_score_normalized: float
    base_score_scaled: float
    final_score_normalized: float
    final_score_scaled: float
    positive_adjustment_normalized: float
    positive_adjustment_scaled: float
    negative_adjustment_normalized: float
    negative_adjustment_scaled: float
    net_adjustment_normalized: float
    net_adjustment_scaled: float
    strategy: str
    is_clipped_upper: bool
    is_clipped_lower: bool
    matched_items: List[MatchedTraceItem]
    correct_additional_items: List[AdditionalTraceItem]
    irrelevant_items: List[AdditionalTraceItem]
    contradictory_items: List[AdditionalTraceItem]
    uncertain_items: List[AdditionalTraceItem]
    formatted_text: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "question": self.question,
            "reference_answer": self.reference_answer,
            "student_answer": self.student_answer,
            "scale": self.scale,
            "scores": {
                "base_score_normalized": round(self.base_score_normalized, 4),
                "base_score_scaled": round(self.base_score_scaled, 4),
                "final_score_normalized": round(self.final_score_normalized, 4),
                "final_score_scaled": round(self.final_score_scaled, 4),
                "positive_adjustment_normalized": round(self.positive_adjustment_normalized, 4),
                "positive_adjustment_scaled": round(self.positive_adjustment_scaled, 4),
                "negative_adjustment_normalized": round(self.negative_adjustment_normalized, 4),
                "negative_adjustment_scaled": round(self.negative_adjustment_scaled, 4),
                "net_adjustment_normalized": round(self.net_adjustment_normalized, 4),
                "net_adjustment_scaled": round(self.net_adjustment_scaled, 4),
                "strategy": self.strategy,
                "is_clipped_upper": self.is_clipped_upper,
                "is_clipped_lower": self.is_clipped_lower,
            },
            "matched_information": [item.to_dict() for item in self.matched_items],
            "correct_additional_information": [item.to_dict() for item in self.correct_additional_items],
            "irrelevant_information": [item.to_dict() for item in self.irrelevant_items],
            "contradictory_information": [item.to_dict() for item in self.contradictory_items],
            "uncertain_information": [item.to_dict() for item in self.uncertain_items],
            "formatted_text": self.formatted_text,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)


class ExplanationTraceGenerator:
    """
    Deterministic, rule-based explanation trace generator.
    """

    def __init__(self, default_scale: float = 5.0) -> None:
        self.default_scale = default_scale

    def generate_trace(
        self,
        question: str,
        reference_answer: str,
        student_answer: str,
        score_result: BoundedScoreResult,
        classification_result: Optional[Union[RobustClassificationResult, Sequence[ClassifiedProposition]]] = None,
        matched_evidence: Optional[Sequence[Union[Dict[str, Any], Any]]] = None,
        scale: Optional[float] = None,
    ) -> GradingExplanationTrace:
        """
        Synthesize complete explanation trace from score result and intermediate evidence.
        """
        target_scale = scale if scale is not None else self.default_scale

        # 1. Parse matched items
        matched_items: List[MatchedTraceItem] = []
        if matched_evidence:
            for item in matched_evidence:
                if isinstance(item, dict):
                    matched_items.append(
                        MatchedTraceItem(
                            reference_statement=item.get("reference_statement", item.get("reference_text", "")),
                            student_statement=item.get("student_statement", item.get("student_text", "")),
                            match_score=float(item.get("match_score", item.get("triple_score", 0.0))),
                            entailment_status=str(item.get("entailment_status", "ENTAILS")),
                            evidence_summary=str(item.get("evidence_summary", item.get("evidence", "Semantic match"))),
                        )
                    )
                else:
                    # Duck typing for dataclasses / MatchedPropositionEvidence
                    matched_items.append(
                        MatchedTraceItem(
                            reference_statement=getattr(item, "reference_statement", str(getattr(item, "reference_relation", ""))),
                            student_statement=getattr(item, "student_statement", str(getattr(item, "student_relation", ""))),
                            match_score=float(getattr(item, "triple_score", 1.0)),
                            entailment_status=str(getattr(item, "entailment_status", "ENTAILS")),
                            evidence_summary=str(getattr(item, "match_method", "Matched by Base ASAG")),
                        )
                    )

        # 2. Parse classified items
        correct_items: List[AdditionalTraceItem] = []
        irrelevant_items: List[AdditionalTraceItem] = []
        contra_items: List[AdditionalTraceItem] = []
        uncertain_items: List[AdditionalTraceItem] = []

        propositions: List[ClassifiedProposition] = []
        if classification_result is not None:
            if isinstance(classification_result, RobustClassificationResult):
                propositions = classification_result.classified_propositions
            else:
                propositions = list(classification_result)

        for p in propositions:
            rel_strength = p.relevance_evidence.evidence_strength if p.relevance_evidence else None
            contra_type = (
                p.contradiction_evidence.contradiction_type.value
                if p.contradiction_evidence and p.contradiction_evidence.is_contradicted
                else None
            )

            item = AdditionalTraceItem(
                text=p.proposition.source_text,
                classification=p.classification.value,
                relevance_strength=rel_strength,
                contradiction_type=contra_type,
                rationale=p.rationale,
            )

            if p.classification == AdditionalInfoClass.CORRECT_ADDITIONAL:
                correct_items.append(item)
            elif p.classification == AdditionalInfoClass.IRRELEVANT:
                irrelevant_items.append(item)
            elif p.classification == AdditionalInfoClass.INCORRECT:
                contra_items.append(item)
            elif p.classification == AdditionalInfoClass.UNCERTAIN:
                uncertain_items.append(item)

        # 3. Compute score metrics
        base_norm = score_result.base_score
        base_scaled = base_norm * target_scale
        final_norm = score_result.final_score
        final_scaled = final_norm * target_scale
        pos_norm = score_result.positive_adjustment
        pos_scaled = pos_norm * target_scale
        neg_norm = score_result.negative_adjustment
        neg_scaled = neg_norm * target_scale
        net_norm = score_result.net_adjustment
        net_scaled = net_norm * target_scale

        # 4. Generate formatted text
        lines: List[str] = [
            "=" * 60,
            "ASAG GRADING EXPLANATION TRACE",
            "=" * 60,
            f"Question:         {question.strip()}",
            f"Reference Answer: {reference_answer.strip()}",
            f"Student Answer:   {student_answer.strip()}",
            "",
            f"FINAL GRADE: {final_scaled:.2f} / {target_scale:.2f} (Normalized: {final_norm:.4f})",
            "-" * 60,
            "SCORE BREAKDOWN:",
            f"  Base ASAG Score:      {base_scaled:.2f} / {target_scale:.2f} ({base_norm:.4f})",
            f"  Positive Adjustment: +{pos_scaled:.2f} / {target_scale:.2f} (+{pos_norm:.4f}) [{len(correct_items)} correct addition(s)]",
            f"  Negative Adjustment: -{neg_scaled:.2f} / {target_scale:.2f} (-{neg_norm:.4f}) [{len(contra_items)} incorrect addition(s)]",
            f"  Net Adjustment:       {'+' if net_norm >= 0 else ''}{net_scaled:.2f} / {target_scale:.2f} ({net_norm:+.4f})",
            f"  Aggregation Strategy: {score_result.strategy.value}",
            f"  Score Bounds:         Clipped Upper={score_result.is_clipped_upper}, Clipped Lower={score_result.is_clipped_lower}",
            "",
            f"MATCHED INFORMATION ({len(matched_items)} items):",
        ]

        if matched_items:
            for m in matched_items:
                lines.append(f"  ✓ Ref: \"{m.reference_statement}\"")
                lines.append(f"    Stu: \"{m.student_statement}\"")
                lines.append(f"    Score: {m.match_score:.2f} | Status: {m.entailment_status} | Evidence: {m.evidence_summary}")
        else:
            lines.append("  (No direct reference propositions matched)")

        lines.append("")
        lines.append(f"ADDITIONAL INFORMATION (CORRECT) ({len(correct_items)} items):")
        if correct_items:
            for c in correct_items:
                rel_str = f"{c.relevance_strength:.2f}" if c.relevance_strength is not None else "N/A"
                lines.append(f"  ✓ \"{c.text}\"")
                lines.append(f"    Relevance: {rel_str} | Classification: {c.classification}")
                lines.append(f"    Rationale: {c.rationale}")
        else:
            lines.append("  (None detected)")

        lines.append("")
        lines.append(f"IRRELEVANT INFORMATION ({len(irrelevant_items)} items):")
        if irrelevant_items:
            for irr in irrelevant_items:
                rel_str = f"{irr.relevance_strength:.2f}" if irr.relevance_strength is not None else "N/A"
                lines.append(f"  ✗ \"{irr.text}\"")
                lines.append(f"    Relevance: {rel_str} (Off-topic)")
                lines.append(f"    Rationale: {irr.rationale}")
        else:
            lines.append("  (None detected)")

        lines.append("")
        lines.append(f"CONTRADICTORY / INCORRECT INFORMATION ({len(contra_items)} items):")
        if contra_items:
            for ci in contra_items:
                lines.append(f"  ✗ \"{ci.text}\"")
                lines.append(f"    Conflict Type: {ci.contradiction_type}")
                lines.append(f"    Rationale: {ci.rationale}")
        else:
            lines.append("  (None detected)")

        if uncertain_items:
            lines.append("")
            lines.append(f"UNCERTAIN INFORMATION ({len(uncertain_items)} items):")
            for ui in uncertain_items:
                lines.append(f"  ? \"{ui.text}\"")
                lines.append(f"    Rationale: {ui.rationale}")

        lines.append("=" * 60)
        formatted_text = "\n".join(lines)

        return GradingExplanationTrace(
            question=question,
            reference_answer=reference_answer,
            student_answer=student_answer,
            scale=target_scale,
            base_score_normalized=base_norm,
            base_score_scaled=base_scaled,
            final_score_normalized=final_norm,
            final_score_scaled=final_scaled,
            positive_adjustment_normalized=pos_norm,
            positive_adjustment_scaled=pos_scaled,
            negative_adjustment_normalized=neg_norm,
            negative_adjustment_scaled=neg_scaled,
            net_adjustment_normalized=net_norm,
            net_adjustment_scaled=net_scaled,
            strategy=score_result.strategy.value,
            is_clipped_upper=score_result.is_clipped_upper,
            is_clipped_lower=score_result.is_clipped_lower,
            matched_items=matched_items,
            correct_additional_items=correct_items,
            irrelevant_items=irrelevant_items,
            contradictory_items=contra_items,
            uncertain_items=uncertain_items,
            formatted_text=formatted_text,
        )
