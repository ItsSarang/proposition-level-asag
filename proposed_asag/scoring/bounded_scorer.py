"""
Bounded Score Aggregation Module (Phase 8).

Implements three configurable evidence aggregation strategies to prevent verbosity
inflation while preserving mathematical bounds in [0.0, 1.0]:
1. SUM: Linear additive mode (Stage 14 historical baseline).
2. MEAN: Evidence-normalized average adjustment.
3. SATURATING: Non-linear diminishing marginal returns bounding maximum bonus.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Union

from proposed_asag.classification.robust_classifier import (
    AdditionalInfoClass,
    ClassifiedProposition,
    RobustClassificationResult,
)


class ScoringStrategy(str, Enum):
    """Aggregation strategy for incorporating proposition evaluations."""
    SUM = "SUM"
    MEAN = "MEAN"
    SATURATING = "SATURATING"


@dataclass(frozen=True)
class BoundedScoreResult:
    """
    Structured outcome of bounded score aggregation.
    """
    base_score: float
    net_adjustment: float
    final_score: float
    strategy: ScoringStrategy
    positive_adjustment: float
    negative_adjustment: float
    is_clipped_upper: bool
    is_clipped_lower: bool
    correct_additional_count: int
    irrelevant_count: int
    incorrect_count: int
    uncertain_count: int
    adjustment_records: List[Dict[str, Any]]
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "base_score": round(self.base_score, 4),
            "net_adjustment": round(self.net_adjustment, 4),
            "final_score": round(self.final_score, 4),
            "strategy": self.strategy.value,
            "positive_adjustment": round(self.positive_adjustment, 4),
            "negative_adjustment": round(self.negative_adjustment, 4),
            "is_clipped_upper": self.is_clipped_upper,
            "is_clipped_lower": self.is_clipped_lower,
            "category_counts": {
                "correct_additional": self.correct_additional_count,
                "irrelevant": self.irrelevant_count,
                "incorrect": self.incorrect_count,
                "uncertain": self.uncertain_count,
            },
            "explanation": self.explanation,
            "adjustment_records": self.adjustment_records,
        }


class BoundedScorer:
    """
    Aggregates proposition-level additional-information evidence into
    a bounded proposed grade.
    """

    def __init__(
        self,
        strategy: ScoringStrategy = ScoringStrategy.SATURATING,
        max_positive_bonus: float = 0.30,
        max_negative_penalty: float = 0.40,
        diminishing_rate: float = 0.50,
        linear_bonus_per_item: float = 0.10,
        linear_penalty_per_item: float = 0.20,
    ) -> None:
        self.strategy = strategy
        self.max_positive_bonus = max_positive_bonus
        self.max_negative_penalty = max_negative_penalty
        self.diminishing_rate = diminishing_rate
        self.linear_bonus_per_item = linear_bonus_per_item
        self.linear_penalty_per_item = linear_penalty_per_item

    def score(
        self,
        base_score: float,
        classification_result: Union[RobustClassificationResult, Sequence[ClassifiedProposition]],
    ) -> BoundedScoreResult:
        """
        Compute bounded score given a base ASAG score and proposition classifications.
        """
        if isinstance(classification_result, RobustClassificationResult):
            propositions = classification_result.classified_propositions
        else:
            propositions = list(classification_result)

        correct_props: List[ClassifiedProposition] = []
        incorrect_props: List[ClassifiedProposition] = []
        irrelevant_props: List[ClassifiedProposition] = []
        uncertain_props: List[ClassifiedProposition] = []

        for p in propositions:
            if p.classification == AdditionalInfoClass.CORRECT_ADDITIONAL:
                correct_props.append(p)
            elif p.classification == AdditionalInfoClass.INCORRECT:
                incorrect_props.append(p)
            elif p.classification == AdditionalInfoClass.IRRELEVANT:
                irrelevant_props.append(p)
            elif p.classification == AdditionalInfoClass.UNCERTAIN:
                uncertain_props.append(p)

        n_correct = len(correct_props)
        n_incorrect = len(incorrect_props)
        n_irrelevant = len(irrelevant_props)
        n_uncertain = len(uncertain_props)
        n_unmatched = n_correct + n_incorrect + n_irrelevant + n_uncertain

        pos_adj = 0.0
        neg_adj = 0.0

        if self.strategy == ScoringStrategy.SUM:
            # Linear additive accumulation (historical Stage 14 mode)
            pos_adj = n_correct * self.linear_bonus_per_item
            neg_adj = n_incorrect * self.linear_penalty_per_item

        elif self.strategy == ScoringStrategy.MEAN:
            # Normalized average evidence across unmatched statements
            denom = max(1, n_unmatched)
            pos_adj = (n_correct * self.linear_bonus_per_item) / denom
            neg_adj = (n_incorrect * self.linear_penalty_per_item) / denom

        elif self.strategy == ScoringStrategy.SATURATING:
            # Diminishing marginal returns formula with horizontal asymptote at max_positive_bonus
            if n_correct > 0:
                scaled_n = self.diminishing_rate * n_correct
                pos_adj = self.max_positive_bonus * (scaled_n / (1.0 + scaled_n))
            if n_incorrect > 0:
                scaled_neg = 0.50 * n_incorrect
                neg_adj = self.max_negative_penalty * (scaled_neg / (1.0 + scaled_neg))

        net_adj = pos_adj - neg_adj
        raw_final = base_score + net_adj
        clipped_final = max(0.0, min(1.0, raw_final))

        is_clipped_upper = raw_final > 1.0
        is_clipped_lower = raw_final < 0.0

        explanation = (
            f"Strategy '{self.strategy.value}': Base={base_score:.4f}, "
            f"+{pos_adj:.4f} (from {n_correct} correct additions), "
            f"-{neg_adj:.4f} (from {n_incorrect} incorrect additions) -> "
            f"Net={net_adj:.4f}, Final={clipped_final:.4f}"
        )

        records = [
            {
                "text": p.proposition.source_text,
                "classification": p.classification.value,
                "rationale": p.rationale,
            }
            for p in propositions
        ]

        return BoundedScoreResult(
            base_score=base_score,
            net_adjustment=net_adj,
            final_score=clipped_final,
            strategy=self.strategy,
            positive_adjustment=pos_adj,
            negative_adjustment=neg_adj,
            is_clipped_upper=is_clipped_upper,
            is_clipped_lower=is_clipped_lower,
            correct_additional_count=n_correct,
            irrelevant_count=n_irrelevant,
            incorrect_count=n_incorrect,
            uncertain_count=n_uncertain,
            adjustment_records=records,
            explanation=explanation,
        )
