"""
Propositional Entailment Analyzer for Base ASAG (Stage 8).

Evaluates whether an aligned student proposition (from Stage 7 MatchedRelation)
semantically supports (ENTAILS), opposes (CONTRADICTS), or insufficiently
evidences (UNCERTAIN) the corresponding reference proposition.

Key Research Boundaries:
-----------------------
- Operates on dependency relations and Stage 7 MatchedRelation alignments.
- Reuses Stage 6 LexicalSemanticComparator slot evidence.
- Detects explicit grammatical and lexical polarity.
- Does NOT classify unmatched student information (reserved for Stage 13).
- Does NOT calculate answer grades or predict human scores (reserved for Stage 9).
- Does NOT perform whole-sentence embeddings, cosine similarity, or LLM prompting.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

from base_asag.dependency.parser import ParsedDocument, ParsedSentence
from base_asag.dependency.triples import DependencyRelation
from base_asag.entailment.polarity import PolarityDetector, PolarityInfo
from base_asag.matching.triple_matcher import MatchedRelation, MatchingResult


@dataclass(frozen=True)
class EntailmentResult:
    """
    Interpretable outcome of proposition-level entailment evaluation.

    Attributes
    ----------
    reference_relation : DependencyRelation
        The reference relation evaluated.
    student_relation : DependencyRelation
        The aligned student relation evaluated.
    relation : str
        Entailment classification: "ENTAILS", "CONTRADICTS", or "UNCERTAIN".
    confidence : float
        Confidence score in [0.0, 1.0].
    reference_polarity : str
        "POSITIVE" or "NEGATED".
    student_polarity : str
        "POSITIVE" or "NEGATED".
    subject_evidence : Dict[str, Any]
        Diagnostic semantic evidence for the subject slot from Stage 6.
    predicate_evidence : Dict[str, Any]
        Diagnostic semantic evidence for the predicate slot from Stage 6.
    object_evidence : Optional[Dict[str, Any]]
        Diagnostic semantic evidence for the object slot from Stage 6, or None.
    triple_score : float
        Continuous weighted alignment score from Stage 7.
    reasons : List[str]
        Human-readable explanations supporting the decision.
    reference_polarity_info : PolarityInfo
        Detailed polarity detection result for reference proposition.
    student_polarity_info : PolarityInfo
        Detailed polarity detection result for student proposition.
    """
    reference_relation: DependencyRelation
    student_relation: DependencyRelation
    relation: str
    confidence: float
    reference_polarity: str
    student_polarity: str
    subject_evidence: Dict[str, Any]
    predicate_evidence: Dict[str, Any]
    object_evidence: Optional[Dict[str, Any]]
    triple_score: float
    reasons: List[str]
    reference_polarity_info: PolarityInfo
    student_polarity_info: PolarityInfo

    def to_dict(self) -> Dict[str, Any]:
        """Convert entailment result to dictionary format."""
        return {
            "reference_relation": self.reference_relation.to_dict(),
            "student_relation": self.student_relation.to_dict(),
            "relation": self.relation,
            "confidence": self.confidence,
            "reference_polarity": self.reference_polarity,
            "student_polarity": self.student_polarity,
            "subject_evidence": self.subject_evidence,
            "predicate_evidence": self.predicate_evidence,
            "object_evidence": self.object_evidence,
            "triple_score": self.triple_score,
            "reasons": list(self.reasons),
            "reference_polarity_info": self.reference_polarity_info.to_dict(),
            "student_polarity_info": self.student_polarity_info.to_dict(),
        }


class PropositionalEntailmentAnalyzer:
    """
    Evaluates proposition-level entailment, contradiction, and uncertainty.

    Applies conservative, interpretable heuristics:
    1. Polarity check: Detects whether either proposition is negated.
    2. Contradiction rule: If polarities clash (e.g. POSITIVE vs NEGATED) and
       underlying semantic alignment is sufficient, classifies as CONTRADICTS.
    3. Entailment rule: If polarities match, all active slots meet minimum
       thresholds, and triple_score meets entailment_threshold, classifies as ENTAILS.
    4. Uncertainty fallback: If evidence is partial, weak, or conflicting,
       classifies as UNCERTAIN without forcing a binary choice.
    """

    DEFAULT_ENTAILMENT_THRESHOLD = 0.70
    DEFAULT_MIN_SLOT_SIMILARITY = 0.50
    DEFAULT_CONTRADICTION_THRESHOLD = 0.50

    def __init__(
        self,
        polarity_detector: Optional[PolarityDetector] = None,
        entailment_threshold: float = DEFAULT_ENTAILMENT_THRESHOLD,
        min_slot_similarity: float = DEFAULT_MIN_SLOT_SIMILARITY,
        contradiction_threshold: float = DEFAULT_CONTRADICTION_THRESHOLD,
    ):
        """
        Initialize the analyzer with configurable decision thresholds.

        Parameters
        ----------
        polarity_detector : Optional[PolarityDetector], default=None
            Detector instance for grammatical negation. If None, instantiates default.
        entailment_threshold : float, default=0.70
            Minimum composite triple alignment score required to confirm ENTAILS.
        min_slot_similarity : float, default=0.50
            Minimum similarity score required on each active slot for ENTAILS.
        contradiction_threshold : float, default=0.50
            Minimum alignment on underlying slots to confirm CONTRADICTS when polarities oppose.
        """
        if not (0.0 <= entailment_threshold <= 1.0):
            raise ValueError(
                f"entailment_threshold must be in [0.0, 1.0], got {entailment_threshold}."
            )
        if not (0.0 <= min_slot_similarity <= 1.0):
            raise ValueError(
                f"min_slot_similarity must be in [0.0, 1.0], got {min_slot_similarity}."
            )
        if not (0.0 <= contradiction_threshold <= 1.0):
            raise ValueError(
                f"contradiction_threshold must be in [0.0, 1.0], got {contradiction_threshold}."
            )

        self.polarity_detector = polarity_detector or PolarityDetector()
        self.entailment_threshold = float(entailment_threshold)
        self.min_slot_similarity = float(min_slot_similarity)
        self.contradiction_threshold = float(contradiction_threshold)

    def evaluate(
        self,
        matched_relation: MatchedRelation,
        reference_sentence: Optional[ParsedSentence] = None,
        student_sentence: Optional[ParsedSentence] = None,
    ) -> EntailmentResult:
        """
        Evaluate entailment for a single MatchedRelation.

        Parameters
        ----------
        matched_relation : MatchedRelation
            The aligned reference-student relation pair from Stage 7.
        reference_sentence : Optional[ParsedSentence], default=None
            Parsed sentence tree for the reference proposition.
        student_sentence : Optional[ParsedSentence], default=None
            Parsed sentence tree for the student proposition.

        Returns
        -------
        EntailmentResult
            Structured entailment assessment.
        """
        if not isinstance(matched_relation, MatchedRelation):
            raise TypeError(
                f"Expected MatchedRelation, got {type(matched_relation).__name__}."
            )

        ref_rel = matched_relation.reference_relation
        stu_rel = matched_relation.student_relation

        # 1. Detect Polarity
        ref_pol = self.polarity_detector.detect(ref_rel, reference_sentence)
        stu_pol = self.polarity_detector.detect(stu_rel, student_sentence)

        # 2. Extract Slot Evidence
        subj_ev = matched_relation.slot_evidence.get("subject")
        pred_ev = matched_relation.slot_evidence.get("predicate")
        obj_ev = matched_relation.slot_evidence.get("object")

        subj_dict = subj_ev.to_dict() if subj_ev else {}
        pred_dict = pred_ev.to_dict() if pred_ev else {}
        obj_dict = obj_ev.to_dict() if obj_ev else None

        reasons: List[str] = []
        score = matched_relation.triple_score

        # 3. Decision Logic: Contradiction Check
        if ref_pol.is_negated != stu_pol.is_negated:
            # Polarity opposition detected
            if score >= self.contradiction_threshold:
                decision = "CONTRADICTS"
                confidence = score

                if ref_pol.is_negated:
                    reasons.append("Reference proposition contains explicit negation.")
                    reasons.append("Student proposition expresses a positive claim.")
                else:
                    reasons.append("Reference proposition expresses a positive claim.")
                    reasons.append(
                        f"Student proposition contains explicit negation ({', '.join(stu_pol.negation_tokens)})."
                    )

                reasons.append(
                    f"Underlying proposition terms are sufficiently aligned (triple score: {score:.4f} >= {self.contradiction_threshold:.2f})."
                )
                reasons.append(
                    "Explicit polarity contradiction on structurally corresponding dependency relations."
                )

                return EntailmentResult(
                    reference_relation=ref_rel,
                    student_relation=stu_rel,
                    relation=decision,
                    confidence=confidence,
                    reference_polarity=ref_pol.polarity,
                    student_polarity=stu_pol.polarity,
                    subject_evidence=subj_dict,
                    predicate_evidence=pred_dict,
                    object_evidence=obj_dict,
                    triple_score=score,
                    reasons=reasons,
                    reference_polarity_info=ref_pol,
                    student_polarity_info=stu_pol,
                )
            else:
                # Weak semantic overlap despite polarity opposition -> UNCERTAIN
                decision = "UNCERTAIN"
                confidence = round(score, 4)
                reasons.append(
                    f"Polarity opposition detected ({ref_pol.polarity} vs {stu_pol.polarity}), but alignment score ({score:.4f}) is below contradiction threshold ({self.contradiction_threshold:.2f})."
                )
                reasons.append(
                    "Insufficient semantic evidence to confirm whether opposing claims address the same underlying proposition."
                )

                return EntailmentResult(
                    reference_relation=ref_rel,
                    student_relation=stu_rel,
                    relation=decision,
                    confidence=confidence,
                    reference_polarity=ref_pol.polarity,
                    student_polarity=stu_pol.polarity,
                    subject_evidence=subj_dict,
                    predicate_evidence=pred_dict,
                    object_evidence=obj_dict,
                    triple_score=score,
                    reasons=reasons,
                    reference_polarity_info=ref_pol,
                    student_polarity_info=stu_pol,
                )

        # 4. Decision Logic: Compatible Polarities (Both POSITIVE or Both NEGATED)
        pol_desc = "both propositions are POSITIVE" if not ref_pol.is_negated else "both propositions are NEGATED"

        # Check individual slot criteria
        subj_score = matched_relation.subject_similarity
        pred_score = matched_relation.predicate_similarity
        obj_score = matched_relation.object_similarity

        subj_ok = subj_score >= self.min_slot_similarity
        pred_ok = pred_score >= self.min_slot_similarity
        obj_ok = (obj_score is None) or (obj_score >= self.min_slot_similarity)
        score_ok = score >= self.entailment_threshold

        if subj_ok and pred_ok and obj_ok and score_ok:
            decision = "ENTAILS"
            confidence = score
            reasons.append(f"Polarity is compatible ({pol_desc}).")
            reasons.append(
                f"Subject slot satisfies minimum similarity ({subj_score:.4f} >= {self.min_slot_similarity:.2f}) via {subj_dict.get('method', 'unknown')}."
            )
            reasons.append(
                f"Predicate slot satisfies minimum similarity ({pred_score:.4f} >= {self.min_slot_similarity:.2f}) via {pred_dict.get('method', 'unknown')}."
            )
            if obj_score is not None:
                reasons.append(
                    f"Object slot satisfies minimum similarity ({obj_score:.4f} >= {self.min_slot_similarity:.2f}) via {obj_dict.get('method', 'unknown') if obj_dict else 'unknown'}."
                )
            else:
                reasons.append("Intransitive SP relation: no object slot required.")
            reasons.append(
                f"Composite triple alignment score ({score:.4f}) meets entailment threshold ({self.entailment_threshold:.2f})."
            )
        else:
            decision = "UNCERTAIN"
            confidence = round(score, 4)
            reasons.append(f"Polarity is compatible ({pol_desc}), but semantic support is inconclusive.")

            if not score_ok:
                reasons.append(
                    f"Composite triple score ({score:.4f}) is below entailment threshold ({self.entailment_threshold:.2f})."
                )
            if not subj_ok:
                reasons.append(
                    f"Subject similarity ({subj_score:.4f}) for '{ref_rel.subject}' <-> '{stu_rel.subject}' is below slot threshold ({self.min_slot_similarity:.2f})."
                )
            if not pred_ok:
                reasons.append(
                    f"Predicate similarity ({pred_score:.4f}) for '{ref_rel.predicate}' <-> '{stu_rel.predicate}' is below slot threshold ({self.min_slot_similarity:.2f})."
                )
            if not obj_ok and obj_score is not None:
                reasons.append(
                    f"Object similarity ({obj_score:.4f}) for '{ref_rel.object}' <-> '{stu_rel.object}' is below slot threshold ({self.min_slot_similarity:.2f})."
                )

        return EntailmentResult(
            reference_relation=ref_rel,
            student_relation=stu_rel,
            relation=decision,
            confidence=confidence,
            reference_polarity=ref_pol.polarity,
            student_polarity=stu_pol.polarity,
            subject_evidence=subj_dict,
            predicate_evidence=pred_dict,
            object_evidence=obj_dict,
            triple_score=score,
            reasons=reasons,
            reference_polarity_info=ref_pol,
            student_polarity_info=stu_pol,
        )

    def evaluate_matching_result(
        self,
        matching_result: MatchingResult,
        reference_doc: Optional[Union[ParsedDocument, ParsedSentence]] = None,
        student_doc: Optional[Union[ParsedDocument, ParsedSentence]] = None,
    ) -> List[EntailmentResult]:
        """
        Evaluate entailment for all matched relations in a MatchingResult.

        Unmatched reference and student relations are preserved without
        classification, strictly adhering to Stage 8 research boundaries.

        Parameters
        ----------
        matching_result : MatchingResult
            The complete alignment result from Stage 7.
        reference_doc : Optional[Union[ParsedDocument, ParsedSentence]], default=None
            Parsed sentence or document for the reference answer.
        student_doc : Optional[Union[ParsedDocument, ParsedSentence]], default=None
            Parsed sentence or document for the student answer.

        Returns
        -------
        List[EntailmentResult]
            List of evaluated entailment decisions for each aligned relation.
        """
        if not isinstance(matching_result, MatchingResult):
            raise TypeError(
                f"Expected MatchingResult, got {type(matching_result).__name__}."
            )

        # Helper to extract sentence
        ref_sent = None
        if reference_doc is not None:
            if isinstance(reference_doc, ParsedSentence):
                ref_sent = reference_doc
            elif isinstance(reference_doc, ParsedDocument) and reference_doc.sentences:
                ref_sent = reference_doc.sentences[0]

        stu_sent = None
        if student_doc is not None:
            if isinstance(student_doc, ParsedSentence):
                stu_sent = student_doc
            elif isinstance(student_doc, ParsedDocument) and student_doc.sentences:
                stu_sent = student_doc.sentences[0]

        results: List[EntailmentResult] = []
        for matched in matching_result.matched_relations:
            # If documents have multiple sentences, find matching sentence by token index
            r_s = ref_sent
            if isinstance(reference_doc, ParsedDocument) and len(reference_doc.sentences) > 1:
                # Fallback to first sentence or sentence containing predicate
                r_s = reference_doc.sentences[0]

            s_s = stu_sent
            if isinstance(student_doc, ParsedDocument) and len(student_doc.sentences) > 1:
                s_s = student_doc.sentences[0]

            res = self.evaluate(
                matched_relation=matched,
                reference_sentence=r_s,
                student_sentence=s_s,
            )
            results.append(res)

        return results
