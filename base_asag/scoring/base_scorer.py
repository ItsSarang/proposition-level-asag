"""
Base ASAG Scoring Module (Stage 9).

Converts Stage 7 triple matching and Stage 8 proposition-level entailment
evidence into a transparent, normalized Base ASAG score.

Methodological Foundation:
--------------------------
Inspired by the classical ASAG methodology of Basak et al. (2019)
("Short-answer grading using textual entailment"), where student answers are
evaluated on how much of the reference answer's dependency/propositional
content is entailed.

Key Research Boundaries:
-----------------------
- Reference propositions are the primary scoring criteria.
- Scoring is strictly based on reference proposition coverage:
    - ENTAILED:   Full credit (default 1.0)
    - UNCERTAIN:  Configurable partial credit (default 0.5)
    - CONTRADICTED: Zero credit (0.0)
    - MISSING:    Zero credit (0.0)
- Unmatched student relations are explicitly preserved and reported in diagnostics.
- Unmatched student relations contribute ZERO to the Base ASAG score (neither
  rewarded nor penalized).
- Does NOT classify unmatched student information as correct, irrelevant, or incorrect
  (reserved for the proposed extension in Stage 13).
- Does NOT employ opaque deep learning, whole-sentence embeddings, or LLM grading.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

from base_asag.dependency.triples import DependencyRelation
from base_asag.entailment.analyzer import EntailmentResult
from base_asag.matching.triple_matcher import MatchingResult


@dataclass(frozen=True)
class PropositionScoreRecord:
    """
    Detailed evaluation and scoring record for a single reference proposition.

    Attributes
    ----------
    reference_relation : DependencyRelation
        The reference relation evaluated.
    status : str
        Evaluation state: "ENTAILED", "UNCERTAIN", "CONTRADICTED", or "MISSING".
    weight : float
        Relative importance weight of this reference proposition.
    contribution : float
        Score contribution of this proposition to the numerator in [0.0, 1.0].
    weighted_contribution : float
        Weight * contribution.
    student_relation : Optional[DependencyRelation]
        The aligned student relation, or None if MISSING.
    entailment_result : Optional[EntailmentResult]
        Stage 8 diagnostic result, or None if MISSING.
    triple_score : Optional[float]
        Stage 7 continuous triple alignment score, or None if MISSING.
    slot_evidence : Optional[Dict[str, Any]]
        Stage 6 diagnostic evidence for constituent slots, or None if MISSING.
    diagnostic_reasons : List[str]
        Human-readable explanation of the scoring decision.
    """
    reference_relation: DependencyRelation
    status: str
    weight: float
    contribution: float
    weighted_contribution: float
    student_relation: Optional[DependencyRelation] = None
    entailment_result: Optional[EntailmentResult] = None
    triple_score: Optional[float] = None
    slot_evidence: Optional[Dict[str, Any]] = None
    diagnostic_reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert proposition record to dictionary format."""
        return {
            "reference_relation": self.reference_relation.to_dict(),
            "status": self.status,
            "weight": self.weight,
            "contribution": self.contribution,
            "weighted_contribution": self.weighted_contribution,
            "student_relation": (
                self.student_relation.to_dict() if self.student_relation else None
            ),
            "entailment_result": (
                self.entailment_result.to_dict() if self.entailment_result else None
            ),
            "triple_score": self.triple_score,
            "slot_evidence": self.slot_evidence,
            "diagnostic_reasons": list(self.diagnostic_reasons),
        }


@dataclass(frozen=True)
class BaseScoreResult:
    """
    Complete result of Base ASAG scoring.

    Attributes
    ----------
    normalized_score : float
        Core Base ASAG score normalized in [0.0, 1.0].
    total_reference_propositions : int
        Total number of reference propositions evaluated.
    entailed_count : int
        Number of reference propositions successfully entailed.
    uncertain_count : int
        Number of reference propositions evaluated as uncertain.
    contradicted_count : int
        Number of reference propositions contradicted by the student answer.
    missing_count : int
        Number of reference propositions omitted by the student answer.
    unmatched_student_count : int
        Number of student relations not aligned to any reference proposition.
    proposition_results : List[PropositionScoreRecord]
        Itemized evaluation and scoring records for every reference proposition.
    unmatched_student_relations : List[DependencyRelation]
        Student propositions left unaligned (preserved for Stage 11-14).
    config : Dict[str, Any]
        Scoring configuration parameters applied.
    """
    normalized_score: float
    total_reference_propositions: int
    entailed_count: int
    uncertain_count: int
    contradicted_count: int
    missing_count: int
    unmatched_student_count: int
    proposition_results: List[PropositionScoreRecord]
    unmatched_student_relations: List[DependencyRelation]
    config: Dict[str, Any]

    def scale_score(self, max_points: float = 5.0) -> float:
        """
        Scale the normalized score [0, 1] to an arbitrary numeric range [0, max_points].

        Parameters
        ----------
        max_points : float, default=5.0
            Maximum point scale (e.g., 5.0, 10.0, 100.0).

        Returns
        -------
        float
            Scaled score rounded to 4 decimal places.
        """
        if max_points < 0:
            raise ValueError(f"max_points must be non-negative, got {max_points}.")
        return float(round(self.normalized_score * max_points, 4))

    def map_to_letter_grade(
        self, scale: Optional[Dict[str, float]] = None
    ) -> str:
        """
        Map the normalized score to an optional letter grade.

        This is an optional demonstration utility and is kept strictly
        separate from the core research score.
        """
        if scale is None:
            # Standard academic percentage boundaries
            scale = {"A": 0.90, "B": 0.80, "C": 0.70, "D": 0.60}

        sorted_scale = sorted(scale.items(), key=lambda x: x[1], reverse=True)
        for letter, cutoff in sorted_scale:
            if self.normalized_score >= cutoff:
                return letter
        return "F"

    def to_dict(self) -> Dict[str, Any]:
        """Convert Base ASAG score result to dictionary format."""
        return {
            "normalized_score": self.normalized_score,
            "total_reference_propositions": self.total_reference_propositions,
            "entailed_count": self.entailed_count,
            "uncertain_count": self.uncertain_count,
            "contradicted_count": self.contradicted_count,
            "missing_count": self.missing_count,
            "unmatched_student_count": self.unmatched_student_count,
            "proposition_results": [p.to_dict() for p in self.proposition_results],
            "unmatched_student_relations": [
                s.to_dict() for s in self.unmatched_student_relations
            ],
            "config": self.config,
        }


class BaseASAGScorer:
    """
    Computes Base ASAG scores from Stage 7 alignments and Stage 8 entailment decisions.

    Methodology:
    ------------
    1. Evaluates coverage of reference propositions.
    2. Maps entailment statuses to configurable contributions:
       - ENTAILED:   entails_weight (default 1.0)
       - UNCERTAIN:  uncertain_weight (default 0.5)
       - CONTRADICTED: contradicts_weight (default 0.0)
       - MISSING:    missing_weight (default 0.0)
    3. Normalizes by total reference proposition weight:
       score = sum(weight_i * contribution_i) / sum(weight_i)
    4. Preserves unmatched student relations without altering the score.
    """

    DEFAULT_ENTAILS_WEIGHT = 1.0
    DEFAULT_UNCERTAIN_WEIGHT = 0.5
    DEFAULT_CONTRADICTS_WEIGHT = 0.0
    DEFAULT_MISSING_WEIGHT = 0.0

    def __init__(
        self,
        entails_weight: float = DEFAULT_ENTAILS_WEIGHT,
        uncertain_weight: float = DEFAULT_UNCERTAIN_WEIGHT,
        contradicts_weight: float = DEFAULT_CONTRADICTS_WEIGHT,
        missing_weight: float = DEFAULT_MISSING_WEIGHT,
    ):
        """
        Initialize the Base ASAG scorer with configurable proposition weights.

        Parameters
        ----------
        entails_weight : float, default=1.0
            Credit awarded when a reference proposition is ENTAILED.
        uncertain_weight : float, default=0.5
            Partial credit awarded when a reference proposition is UNCERTAIN.
        contradicts_weight : float, default=0.0
            Credit awarded when a reference proposition is CONTRADICTED.
        missing_weight : float, default=0.0
            Credit awarded when a reference proposition is MISSING.
        """
        if not (0.0 <= entails_weight <= 1.0):
            raise ValueError(f"entails_weight must be in [0.0, 1.0], got {entails_weight}.")
        if not (0.0 <= uncertain_weight <= 1.0):
            raise ValueError(
                f"uncertain_weight must be in [0.0, 1.0], got {uncertain_weight}."
            )
        if not (0.0 <= contradicts_weight <= 1.0):
            raise ValueError(
                f"contradicts_weight must be in [0.0, 1.0], got {contradicts_weight}."
            )
        if not (0.0 <= missing_weight <= 1.0):
            raise ValueError(f"missing_weight must be in [0.0, 1.0], got {missing_weight}.")

        self.entails_weight = float(entails_weight)
        self.uncertain_weight = float(uncertain_weight)
        self.contradicts_weight = float(contradicts_weight)
        self.missing_weight = float(missing_weight)

    def score(
        self,
        reference_relations: Sequence[DependencyRelation],
        entailment_results: Sequence[EntailmentResult],
        unmatched_reference_relations: Sequence[DependencyRelation],
        unmatched_student_relations: Sequence[DependencyRelation],
        reference_weights: Optional[Sequence[float]] = None,
    ) -> BaseScoreResult:
        """
        Calculate Base ASAG score from evaluated propositions.

        Parameters
        ----------
        reference_relations : Sequence[DependencyRelation]
            Complete list of reference propositions in original order.
        entailment_results : Sequence[EntailmentResult]
            Stage 8 entailment evaluations for aligned relation pairs.
        unmatched_reference_relations : Sequence[DependencyRelation]
            Reference relations left unaligned in Stage 7.
        unmatched_student_relations : Sequence[DependencyRelation]
            Student relations left unaligned in Stage 7.
        reference_weights : Optional[Sequence[float]], default=None
            Importance weights for each reference relation. If None, defaults to uniform 1.0.

        Returns
        -------
        BaseScoreResult
            Structured scoring outcome.
        """
        ref_list = list(reference_relations)
        num_refs = len(ref_list)

        # Handle reference weights
        if reference_weights is not None:
            weights = list(reference_weights)
            if len(weights) != num_refs:
                raise ValueError(
                    f"Length of reference_weights ({len(weights)}) must match "
                    f"reference_relations ({num_refs})."
                )
            for w in weights:
                if w < 0:
                    raise ValueError(f"Reference weights must be non-negative, got {w}.")
        else:
            weights = [1.0] * num_refs

        config = {
            "entails_weight": self.entails_weight,
            "uncertain_weight": self.uncertain_weight,
            "contradicts_weight": self.contradicts_weight,
            "missing_weight": self.missing_weight,
            "total_reference_count": num_refs,
            "unmatched_student_count": len(unmatched_student_relations),
            "scoring_model": "Base ASAG Reference Proposition Coverage",
        }

        # Trivial edge case: Zero reference propositions
        if num_refs == 0:
            return BaseScoreResult(
                normalized_score=0.0,
                total_reference_propositions=0,
                entailed_count=0,
                uncertain_count=0,
                contradicted_count=0,
                missing_count=0,
                unmatched_student_count=len(unmatched_student_relations),
                proposition_results=[],
                unmatched_student_relations=list(unmatched_student_relations),
                config=config,
            )

        # Build lookup for entailment results by reference relation tuple
        entail_by_ref: Dict[Tuple[str, str, Optional[str]], EntailmentResult] = {
            res.reference_relation.to_tuple(): res for res in entailment_results
        }
        unmatched_ref_tuples = {
            r.to_tuple() for r in unmatched_reference_relations
        }

        proposition_results: List[PropositionScoreRecord] = []
        entailed_cnt = 0
        uncertain_cnt = 0
        contradicted_cnt = 0
        missing_cnt = 0

        total_weighted_points = 0.0
        total_possible_weight = sum(weights)

        for i, ref_rel in enumerate(ref_list):
            ref_tup = ref_rel.to_tuple()
            w_i = weights[i]

            if ref_tup in entail_by_ref:
                entail_res = entail_by_ref[ref_tup]
                decision = entail_res.relation  # "ENTAILS", "CONTRADICTS", or "UNCERTAIN"

                if decision == "ENTAILS":
                    status = "ENTAILED"
                    contrib = self.entails_weight
                    entailed_cnt += 1
                    reasons = [
                        "Proposition is successfully entailed by student answer.",
                        f"Awarded full credit ({contrib:.2f}).",
                    ] + entail_res.reasons
                elif decision == "CONTRADICTS":
                    status = "CONTRADICTED"
                    contrib = self.contradicts_weight
                    contradicted_cnt += 1
                    reasons = [
                        "Proposition is explicitly contradicted by student answer.",
                        f"Awarded zero credit ({contrib:.2f}).",
                    ] + entail_res.reasons
                else:  # UNCERTAIN
                    status = "UNCERTAIN"
                    contrib = self.uncertain_weight
                    uncertain_cnt += 1
                    reasons = [
                        "Proposition evidence is uncertain or inconclusive.",
                        f"Awarded partial credit ({contrib:.2f}).",
                    ] + entail_res.reasons

                weighted_contrib = round(w_i * contrib, 6)
                total_weighted_points += weighted_contrib

                # Construct slot evidence summary
                slot_ev = {
                    "subject": entail_res.subject_evidence,
                    "predicate": entail_res.predicate_evidence,
                }
                if entail_res.object_evidence:
                    slot_ev["object"] = entail_res.object_evidence

                rec = PropositionScoreRecord(
                    reference_relation=ref_rel,
                    status=status,
                    weight=w_i,
                    contribution=contrib,
                    weighted_contribution=weighted_contrib,
                    student_relation=entail_res.student_relation,
                    entailment_result=entail_res,
                    triple_score=entail_res.triple_score,
                    slot_evidence=slot_ev,
                    diagnostic_reasons=reasons,
                )
                proposition_results.append(rec)

            else:
                # Reference relation is missing / unmatched
                status = "MISSING"
                contrib = self.missing_weight
                missing_cnt += 1
                weighted_contrib = round(w_i * contrib, 6)
                total_weighted_points += weighted_contrib

                reasons = [
                    "Proposition was not addressed or covered in the student answer.",
                    f"Awarded zero credit ({contrib:.2f}).",
                ]

                rec = PropositionScoreRecord(
                    reference_relation=ref_rel,
                    status=status,
                    weight=w_i,
                    contribution=contrib,
                    weighted_contribution=weighted_contrib,
                    student_relation=None,
                    entailment_result=None,
                    triple_score=None,
                    slot_evidence=None,
                    diagnostic_reasons=reasons,
                )
                proposition_results.append(rec)

        # Normalize score
        if total_possible_weight > 0:
            raw_score = total_weighted_points / total_possible_weight
            normalized_score = float(round(max(0.0, min(1.0, raw_score)), 4))
        else:
            normalized_score = 0.0

        return BaseScoreResult(
            normalized_score=normalized_score,
            total_reference_propositions=num_refs,
            entailed_count=entailed_cnt,
            uncertain_count=uncertain_cnt,
            contradicted_count=contradicted_cnt,
            missing_count=missing_cnt,
            unmatched_student_count=len(unmatched_student_relations),
            proposition_results=proposition_results,
            unmatched_student_relations=list(unmatched_student_relations),
            config=config,
        )

    def score_pipeline(
        self,
        matching_result: MatchingResult,
        entailment_results: Sequence[EntailmentResult],
        reference_weights: Optional[Sequence[float]] = None,
    ) -> BaseScoreResult:
        """
        Convenience method to compute Base ASAG score directly from Stage 7 and 8 outputs.

        Parameters
        ----------
        matching_result : MatchingResult
            Stage 7 matching result containing matched and unmatched relations.
        entailment_results : Sequence[EntailmentResult]
            Stage 8 entailment evaluations.
        reference_weights : Optional[Sequence[float]], default=None
            Optional proposition weights.

        Returns
        -------
        BaseScoreResult
            Structured scoring outcome.
        """
        if not isinstance(matching_result, MatchingResult):
            raise TypeError(
                f"Expected MatchingResult, got {type(matching_result).__name__}."
            )

        # Reconstruct all reference relations in order
        all_refs: List[DependencyRelation] = [
            m.reference_relation for m in matching_result.matched_relations
        ] + list(matching_result.unmatched_reference_relations)

        # Sort by original reference index if available
        # Matched relations carry reference_index
        # To maintain exact input order, order by index where available
        matched_dict = {
            m.reference_index: m.reference_relation
            for m in matching_result.matched_relations
        }

        # Build full ordered list if reference_relations_count is known
        total_ref_count = matching_result.config.get(
            "reference_relations_count", len(all_refs)
        )
        ordered_refs: List[DependencyRelation] = []

        unmatched_ref_iter = iter(matching_result.unmatched_reference_relations)
        for idx in range(total_ref_count):
            if idx in matched_dict:
                ordered_refs.append(matched_dict[idx])
            else:
                try:
                    ordered_refs.append(next(unmatched_ref_iter))
                except StopIteration:
                    pass

        if not ordered_refs:
            ordered_refs = all_refs

        return self.score(
            reference_relations=ordered_refs,
            entailment_results=entailment_results,
            unmatched_reference_relations=matching_result.unmatched_reference_relations,
            unmatched_student_relations=matching_result.unmatched_student_relations,
            reference_weights=reference_weights,
        )
