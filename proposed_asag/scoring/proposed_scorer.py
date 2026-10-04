"""
Proposed ASAG Scoring Module (Stage 14).

This module provides the Stage 14 scoring component for the Proposed ASAG system (System 3).
It incorporates Stage 13 proposition-level additional-information classifications
(CORRECT_ADDITIONAL, IRRELEVANT, INCORRECT, UNCERTAIN) into a transparent, configurable
proposed grade, while preserving the existing Base ASAG score as an unperturbed control.

Methodological & Research Foundation:
-------------------------------------
- Base ASAG (System 2, inspired by Basak et al., 2019) evaluates student answers strictly
  by reference proposition coverage (entailment), discarding unmatched student propositions.
- Proposed ASAG (System 3) investigates the research hypothesis:
  "Can an interpretable proposition-level extension evaluate unmatched student information
  as correct additional, irrelevant, or incorrect information, and does incorporating this
  evaluation improve agreement with human grading?"

Research Boundaries:
--------------------
- The existing Base ASAG scoring logic (base_asag/scoring/base_scorer.py) is NOT modified.
- Base ASAG score serves as the strict baseline/control condition and is preserved exactly.
- All adjustment weights and penalties are implementation and experimental parameters.
  They have NOT been optimized, tuned, or empirically validated against human grades.
- We do NOT claim that this proposed scoring mechanism improves human agreement or grading
  accuracy. Empirical validation is reserved for Stage 15.
- No machine learning, deep learning, sentence transformers, embeddings, or LLMs are used.
- No hardcoded task-specific heuristics or demonstration facts are used.
"""

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Union

from base_asag.pipeline import BaseASAGPipelineResult
from proposed_asag.classification.additional_info import (
    AdditionalInformationClassifier,
    AdditionalInformationResult,
    DocumentClassificationResult,
)
from proposed_asag.proposition.representation import DocumentPropositionRepresentation


# ---------------------------------------------------------------------------
# Data Structures
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PropositionAdjustmentRecord:
    """
    Detailed provenance record for an individual proposition's score adjustment.

    Attributes
    ----------
    proposition_id : str
        Unique proposition identifier (e.g. 'stu_prop_1').
    proposition_index : int
        Zero-based index of the proposition in the student answer.
    text : str
        Surface span text of the proposition.
    classification : str
        Stage 13 category: 'CORRECT_ADDITIONAL', 'IRRELEVANT', 'INCORRECT', or 'UNCERTAIN'.
    confidence : float
        Stage 13 classification confidence score in [0.0, 1.0].
    raw_parameter_weight : float
        The configured weight or penalty for this classification category.
    evidence_weighted : bool
        Whether confidence weighting was applied.
    applied_adjustment : float
        Signed continuous adjustment: positive for bonus, negative for penalty, 0.0 for neutral.
    reason : str
        Human-readable explanation of why and how the adjustment was computed.
    details : Dict[str, Any]
        Additional diagnostic information from Stage 13 classification.
    """
    proposition_id: str
    proposition_index: int
    text: str
    classification: str
    confidence: float
    raw_parameter_weight: float
    evidence_weighted: bool
    applied_adjustment: float
    reason: str
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert adjustment record to a JSON-serializable dictionary."""
        return {
            "proposition_id": self.proposition_id,
            "proposition_index": self.proposition_index,
            "text": self.text,
            "classification": self.classification,
            "confidence": self.confidence,
            "raw_parameter_weight": self.raw_parameter_weight,
            "evidence_weighted": self.evidence_weighted,
            "applied_adjustment": self.applied_adjustment,
            "reason": self.reason,
            "details": self.details,
        }


@dataclass(frozen=True)
class ProposedScoreResult:
    """
    Comprehensive result of Stage 14 proposed scoring.

    Attributes
    ----------
    base_score : float
        Core Base ASAG score normalized in [0.0, 1.0], preserved unchanged as control.
    proposed_score : float
        Final proposed ASAG score in [0.0, 1.0], clipped to valid probability bounds.
    raw_proposed_score : float
        Unclipped continuous score (base_score + net_adjustment).
    correct_additional_count : int
        Count of CORRECT_ADDITIONAL propositions.
    irrelevant_count : int
        Count of IRRELEVANT propositions.
    incorrect_count : int
        Count of INCORRECT propositions.
    uncertain_count : int
        Count of UNCERTAIN propositions.
    positive_adjustment : float
        Total positive adjustment (bonus) from correct additional information.
    negative_adjustment : float
        Total negative adjustment magnitude (positive float) from incorrect information.
    net_adjustment : float
        Net signed adjustment (positive_adjustment - negative_adjustment).
    is_clipped_upper : bool
        True if raw_proposed_score exceeded 1.0 and was clipped to 1.0.
    is_clipped_lower : bool
        True if raw_proposed_score was below 0.0 and was clipped to 0.0.
    adjustment_details : List[PropositionAdjustmentRecord]
        Itemized provenance records for all evaluated propositions.
    config : Dict[str, Any]
        Scoring configuration parameters applied.
    summary : Dict[str, Any]
        Diagnostic summary metrics and count tallies.
    """
    base_score: float
    proposed_score: float
    raw_proposed_score: float
    correct_additional_count: int
    irrelevant_count: int
    incorrect_count: int
    uncertain_count: int
    positive_adjustment: float
    negative_adjustment: float
    net_adjustment: float
    is_clipped_upper: bool
    is_clipped_lower: bool
    adjustment_details: List[PropositionAdjustmentRecord]
    config: Dict[str, Any]
    summary: Dict[str, Any]

    def scale_base_score(self, max_points: float = 5.0) -> float:
        """
        Scale normalized base score in [0.0, 1.0] to an arbitrary numeric range [0, max_points].

        Parameters
        ----------
        max_points : float, default=5.0
            Maximum point value.

        Returns
        -------
        float
            Scaled base score rounded to 4 decimal places.
        """
        return float(round(self.base_score * max_points, 4))

    def scale_proposed_score(self, max_points: float = 5.0) -> float:
        """
        Scale normalized proposed score in [0.0, 1.0] to an arbitrary numeric range [0, max_points].

        Parameters
        ----------
        max_points : float, default=5.0
            Maximum point value.

        Returns
        -------
        float
            Scaled proposed score rounded to 4 decimal places.
        """
        return float(round(self.proposed_score * max_points, 4))

    def to_dict(self) -> Dict[str, Any]:
        """Convert ProposedScoreResult to a JSON-serializable dictionary."""
        return {
            "base_score": self.base_score,
            "proposed_score": self.proposed_score,
            "raw_proposed_score": self.raw_proposed_score,
            "correct_additional_count": self.correct_additional_count,
            "irrelevant_count": self.irrelevant_count,
            "incorrect_count": self.incorrect_count,
            "uncertain_count": self.uncertain_count,
            "positive_adjustment": self.positive_adjustment,
            "negative_adjustment": self.negative_adjustment,
            "net_adjustment": self.net_adjustment,
            "is_clipped_upper": self.is_clipped_upper,
            "is_clipped_lower": self.is_clipped_lower,
            "adjustment_details": [a.to_dict() for a in self.adjustment_details],
            "config": self.config,
            "summary": self.summary,
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize complete proposed scoring result to formatted JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


# ---------------------------------------------------------------------------
# Proposed Scorer Component
# ---------------------------------------------------------------------------

class ProposedScorer:
    """
    Stage 14 Scorer: Computes proposed ASAG grades by adjusting Base ASAG scores
    with proposition-level additional-information evaluations.

    Design Principles:
    ------------------
    1. Base Score Invariance: Base ASAG score is never modified in-place; it is
       treated as the exact unperturbed control condition.
    2. Transparent Adjustment:
       adjustment = sum(bonus for CORRECT_ADDITIONAL) - sum(penalty for INCORRECT)
       proposed_score = clip(base_score + adjustment, 0.0, 1.0)
    3. Fully Configurable: Adjustment weights, penalties, clipping caps, and
       evidence-weighting modes are configurable parameters.
    4. Complete Provenance: Every proposition contributing to the score adjustment
       is tracked with its exact classification, confidence, and signed delta.
    """

    # Default experimental parameters (NOT optimized or empirically validated)
    DEFAULT_CORRECT_ADDITIONAL_WEIGHT = 0.10
    DEFAULT_INCORRECT_ADDITIONAL_PENALTY = 0.20
    DEFAULT_IRRELEVANT_ADJUSTMENT = 0.0
    DEFAULT_UNCERTAIN_ADJUSTMENT = 0.0

    def __init__(
        self,
        correct_additional_weight: float = DEFAULT_CORRECT_ADDITIONAL_WEIGHT,
        incorrect_additional_penalty: float = DEFAULT_INCORRECT_ADDITIONAL_PENALTY,
        irrelevant_adjustment: float = DEFAULT_IRRELEVANT_ADJUSTMENT,
        uncertain_adjustment: float = DEFAULT_UNCERTAIN_ADJUSTMENT,
        evidence_weighted: bool = False,
        max_positive_adjustment: Optional[float] = None,
        max_negative_adjustment: Optional[float] = None,
        classifier: Optional[AdditionalInformationClassifier] = None,
    ):
        """
        Initialize ProposedScorer with configurable scoring parameters.

        Parameters
        ----------
        correct_additional_weight : float, default=0.10
            Score bonus per CORRECT_ADDITIONAL proposition.
        incorrect_additional_penalty : float, default=0.20
            Score deduction magnitude per INCORRECT proposition.
        irrelevant_adjustment : float, default=0.0
            Score adjustment for IRRELEVANT propositions. Default is neutral (0.0).
        uncertain_adjustment : float, default=0.0
            Score adjustment for UNCERTAIN propositions. Default is neutral (0.0).
        evidence_weighted : bool, default=False
            If True, scales each proposition adjustment by its Stage 13 confidence score.
            If False (default), applies a uniform step per proposition.
        max_positive_adjustment : Optional[float], default=None
            Optional maximum cap on total positive adjustment.
        max_negative_adjustment : Optional[float], default=None
            Optional maximum cap on total negative adjustment magnitude.
        classifier : Optional[AdditionalInformationClassifier], default=None
            Stage 13 classifier instance used when scoring raw pipeline results.
        """
        if correct_additional_weight < 0.0:
            raise ValueError(
                f"correct_additional_weight must be non-negative, got {correct_additional_weight}."
            )
        if incorrect_additional_penalty < 0.0:
            raise ValueError(
                f"incorrect_additional_penalty must be non-negative, got {incorrect_additional_penalty}."
            )

        self.correct_additional_weight = float(correct_additional_weight)
        self.incorrect_additional_penalty = float(incorrect_additional_penalty)
        self.irrelevant_adjustment = float(irrelevant_adjustment)
        self.uncertain_adjustment = float(uncertain_adjustment)
        self.evidence_weighted = bool(evidence_weighted)
        self.max_positive_adjustment = (
            float(max_positive_adjustment) if max_positive_adjustment is not None else None
        )
        self.max_negative_adjustment = (
            float(max_negative_adjustment) if max_negative_adjustment is not None else None
        )
        self.classifier = classifier or AdditionalInformationClassifier()

    def score_propositions(
        self,
        base_score: float,
        classifications: Sequence[Union[AdditionalInformationResult, Dict[str, Any]]],
    ) -> ProposedScoreResult:
        """
        Compute proposed score given a base score and a list of classified propositions.

        Parameters
        ----------
        base_score : float
            Core Base ASAG normalized score in [0.0, 1.0].
        classifications : Sequence[Union[AdditionalInformationResult, Dict[str, Any]]]
            List of Stage 13 proposition classification results or dictionaries.

        Returns
        -------
        ProposedScoreResult
            Structured scoring outcome with itemized provenance and clipped final score.
        """
        if not (0.0 <= base_score <= 1.0):
            raise ValueError(f"base_score must be normalized in [0.0, 1.0], got {base_score}.")

        adjustment_records: List[PropositionAdjustmentRecord] = []
        raw_pos_adjustment = 0.0
        raw_neg_adjustment = 0.0

        c_add_count = 0
        irrel_count = 0
        incorr_count = 0
        uncert_count = 0

        for item in classifications:
            # Extract attributes whether item is AdditionalInformationResult or dict
            if isinstance(item, AdditionalInformationResult):
                prop_id = item.proposition_id
                prop_idx = item.proposition_index
                text = item.text
                category = item.classification
                confidence = float(item.confidence)
                details = {
                    "relevance_score": item.relevance.score if hasattr(item, "relevance") else None,
                    "contradiction_type": (
                        item.compatibility.contradiction_type if hasattr(item, "compatibility") else None
                    ),
                }
            elif isinstance(item, dict):
                prop_id = item.get("proposition_id", "stu_prop_unknown")
                prop_idx = item.get("proposition_index", 0)
                text = item.get("text", "")
                category = item.get("classification", "UNCERTAIN")
                confidence = float(item.get("confidence", 1.0))
                details = item.get("details", {})
            else:
                continue

            # Calculate adjustment for this proposition
            applied_adj = 0.0
            param_weight = 0.0
            reason = ""

            if category == "CORRECT_ADDITIONAL":
                c_add_count += 1
                param_weight = self.correct_additional_weight
                factor = confidence if self.evidence_weighted else 1.0
                applied_adj = param_weight * factor
                raw_pos_adjustment += applied_adj
                weighting_desc = f" (evidence-weighted: {param_weight:.4f} × {confidence:.4f})" if self.evidence_weighted else ""
                reason = f"Bonus for correct additional proposition: +{applied_adj:.4f}{weighting_desc}."

            elif category == "INCORRECT":
                incorr_count += 1
                param_weight = self.incorrect_additional_penalty
                factor = confidence if self.evidence_weighted else 1.0
                applied_adj = -(param_weight * factor)
                raw_neg_adjustment += abs(applied_adj)
                weighting_desc = f" (evidence-weighted: {param_weight:.4f} × {confidence:.4f})" if self.evidence_weighted else ""
                reason = f"Deduction for incorrect/misconception proposition: {applied_adj:.4f}{weighting_desc}."

            elif category == "IRRELEVANT":
                irrel_count += 1
                param_weight = self.irrelevant_adjustment
                factor = confidence if self.evidence_weighted else 1.0
                applied_adj = param_weight * factor
                if applied_adj > 0.0:
                    raw_pos_adjustment += applied_adj
                elif applied_adj < 0.0:
                    raw_neg_adjustment += abs(applied_adj)
                reason = (
                    f"Irrelevant proposition: neutral adjustment ({applied_adj:+.4f})."
                    if applied_adj == 0.0
                    else f"Irrelevant proposition adjustment: {applied_adj:+.4f}."
                )

            elif category == "UNCERTAIN":
                uncert_count += 1
                param_weight = self.uncertain_adjustment
                factor = confidence if self.evidence_weighted else 1.0
                applied_adj = param_weight * factor
                if applied_adj > 0.0:
                    raw_pos_adjustment += applied_adj
                elif applied_adj < 0.0:
                    raw_neg_adjustment += abs(applied_adj)
                reason = (
                    f"Uncertain proposition: neutral fallback adjustment ({applied_adj:+.4f})."
                    if applied_adj == 0.0
                    else f"Uncertain proposition adjustment: {applied_adj:+.4f}."
                )
            else:
                # E.g. MATCHED_BY_BASE_ASAG passed in error; neutral effect
                applied_adj = 0.0
                param_weight = 0.0
                reason = f"Matched or non-additional proposition ({category}): 0.0 effect."

            adjustment_records.append(
                PropositionAdjustmentRecord(
                    proposition_id=prop_id,
                    proposition_index=prop_idx,
                    text=text,
                    classification=category,
                    confidence=float(round(confidence, 4)),
                    raw_parameter_weight=float(round(param_weight, 4)),
                    evidence_weighted=self.evidence_weighted,
                    applied_adjustment=float(round(applied_adj, 4)),
                    reason=reason,
                    details=details,
                )
            )

        # Apply optional adjustment caps if configured
        final_pos_adjustment = raw_pos_adjustment
        if self.max_positive_adjustment is not None:
            final_pos_adjustment = min(final_pos_adjustment, self.max_positive_adjustment)

        final_neg_adjustment = raw_neg_adjustment
        if self.max_negative_adjustment is not None:
            final_neg_adjustment = min(final_neg_adjustment, self.max_negative_adjustment)

        net_adjustment = float(round(final_pos_adjustment - final_neg_adjustment, 4))
        raw_proposed_score = float(round(base_score + net_adjustment, 4))

        # Clip to valid normalized range [0.0, 1.0]
        proposed_score = float(round(max(0.0, min(1.0, raw_proposed_score)), 4))
        is_clipped_upper = raw_proposed_score > 1.0
        is_clipped_lower = raw_proposed_score < 0.0

        config_dict = {
            "correct_additional_weight": self.correct_additional_weight,
            "incorrect_additional_penalty": self.incorrect_additional_penalty,
            "irrelevant_adjustment": self.irrelevant_adjustment,
            "uncertain_adjustment": self.uncertain_adjustment,
            "evidence_weighted": self.evidence_weighted,
            "max_positive_adjustment": self.max_positive_adjustment,
            "max_negative_adjustment": self.max_negative_adjustment,
        }

        summary_dict = {
            "base_score": base_score,
            "proposed_score": proposed_score,
            "net_adjustment": net_adjustment,
            "correct_additional_count": c_add_count,
            "irrelevant_count": irrel_count,
            "incorrect_count": incorr_count,
            "uncertain_count": uncert_count,
            "total_evaluated_propositions": len(classifications),
            "is_clipped_upper": is_clipped_upper,
            "is_clipped_lower": is_clipped_lower,
        }

        return ProposedScoreResult(
            base_score=base_score,
            proposed_score=proposed_score,
            raw_proposed_score=raw_proposed_score,
            correct_additional_count=c_add_count,
            irrelevant_count=irrel_count,
            incorrect_count=incorr_count,
            uncertain_count=uncert_count,
            positive_adjustment=float(round(final_pos_adjustment, 4)),
            negative_adjustment=float(round(final_neg_adjustment, 4)),
            net_adjustment=net_adjustment,
            is_clipped_upper=is_clipped_upper,
            is_clipped_lower=is_clipped_lower,
            adjustment_details=adjustment_records,
            config=config_dict,
            summary=summary_dict,
        )

    def score_document(
        self,
        document_or_pipeline_or_result: Union[
            DocumentClassificationResult,
            DocumentPropositionRepresentation,
            BaseASAGPipelineResult,
        ],
    ) -> ProposedScoreResult:
        """
        Compute proposed score from a Stage 13 classification result, Stage 12
        document representation, or Stage 10 pipeline result.

        Parameters
        ----------
        document_or_pipeline_or_result : Union[DocumentClassificationResult, DocumentPropositionRepresentation, BaseASAGPipelineResult]
            Input result object from Stage 10, 12, or 13.

        Returns
        -------
        ProposedScoreResult
            Comprehensive scoring result preserving base score and detailing adjustments.
        """
        if isinstance(document_or_pipeline_or_result, DocumentClassificationResult):
            doc_cls = document_or_pipeline_or_result
        elif isinstance(
            document_or_pipeline_or_result,
            (DocumentPropositionRepresentation, BaseASAGPipelineResult),
        ):
            doc_cls = self.classifier.classify_document(document_or_pipeline_or_result)
        else:
            raise TypeError(
                f"Expected DocumentClassificationResult, DocumentPropositionRepresentation, "
                f"or BaseASAGPipelineResult, got {type(document_or_pipeline_or_result).__name__}."
            )

        return self.score_propositions(
            base_score=doc_cls.base_asag_normalized_score,
            classifications=doc_cls.unmatched_classifications,
        )

    def score(
        self,
        document_or_pipeline_or_result: Union[
            DocumentClassificationResult,
            DocumentPropositionRepresentation,
            BaseASAGPipelineResult,
        ],
    ) -> ProposedScoreResult:
        """Convenience alias for score_document."""
        return self.score_document(document_or_pipeline_or_result)
