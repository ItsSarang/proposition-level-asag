"""
Robust Evidence-Based Additional-Information Classifier (Phase 7).

Implements formal 4-step evidence-based evaluation of unmatched student propositions:
STEP 1: Question-Aware Relevance (Phase 2)
STEP 2: Reference Compatibility
STEP 3: Property & Factual Contradiction Analysis (Phase 5)
STEP 4: Evidence Sufficiency

Classification Categories:
- CORRECT_ADDITIONAL: Relevant to the question, compatible with reference context,
  non-contradictory, with sufficient semantic evidence.
  *EPISTEMIC BOUNDARY: Does NOT mean 'proven factually true'. It means the proposition
  is relevant to the question, does not contradict available reference evidence,
  and has sufficient semantic/linguistic support under the implemented method.*
- IRRELEVANT: Shows low semantic affinity or concept overlap with the question domain.
- INCORRECT: Contradicts reference assertions via explicit polarity mismatch,
  lexical antonymy, or mutually exclusive property values.
- UNCERTAIN: Borderline or ambiguous evidence where neither relevance nor contradiction
  can be asserted with confidence.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from base_asag.representation.hybrid import RobustProposition
from proposed_asag.contradiction.property_contradiction import (
    ContradictionEvidence,
    PropertyContradictionDetector,
)
from proposed_asag.evidence import (
    EvidenceSource,
    EvidenceStatus,
    PropositionEvidenceVerifier,
    VerificationEvidence,
)
from proposed_asag.relevance.question_relevance import (
    QuestionAwareRelevanceAnalyzer,
    RelevanceEvidence,
)


class AdditionalInfoClass(str, Enum):
    """Categorical classification of unmatched student information."""
    MATCHED_BY_BASE_ASAG = "MATCHED_BY_BASE_ASAG"
    CORRECT_ADDITIONAL = "CORRECT_ADDITIONAL"
    IRRELEVANT = "IRRELEVANT"
    INCORRECT = "INCORRECT"
    UNCERTAIN = "UNCERTAIN"


@dataclass(frozen=True)
class ClassifiedProposition:
    """
    Proposition with formal classification, evidence traces, and provenance.
    """
    proposition: RobustProposition
    classification: AdditionalInfoClass
    relevance_evidence: Optional[RelevanceEvidence]
    contradiction_evidence: Optional[ContradictionEvidence]
    score_effect: float
    rationale: str
    verification_evidence: Optional[VerificationEvidence] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "proposition": self.proposition.to_dict(),
            "classification": self.classification.value,
            "relevance_evidence": self.relevance_evidence.to_dict() if self.relevance_evidence else None,
            "contradiction_evidence": self.contradiction_evidence.to_dict() if self.contradiction_evidence else None,
            "verification_evidence": self.verification_evidence.to_dict() if self.verification_evidence else None,
            "score_effect": self.score_effect,
            "rationale": self.rationale,
        }


@dataclass(frozen=True)
class RobustClassificationResult:
    """
    Complete document-level classification result for all student propositions.
    """
    question: str
    reference_answer: str
    student_answer: str
    total_propositions: int
    matched_count: int
    unmatched_count: int
    classified_propositions: List[ClassifiedProposition]
    category_counts: Dict[str, int]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "question": self.question,
            "reference_answer": self.reference_answer,
            "student_answer": self.student_answer,
            "total_propositions": self.total_propositions,
            "matched_count": self.matched_count,
            "unmatched_count": self.unmatched_count,
            "category_counts": self.category_counts,
            "classified_propositions": [cp.to_dict() for cp in self.classified_propositions],
        }


class RobustAdditionalInfoClassifier:
    """
    Evaluates unmatched propositions using the 4-step evidence pipeline.
    """

    def __init__(
        self,
        relevance_threshold: float = 0.35,
        sufficiency_threshold: float = 0.40,
        relevance_analyzer: Optional[QuestionAwareRelevanceAnalyzer] = None,
        contradiction_detector: Optional[PropertyContradictionDetector] = None,
        evidence_verifier: Optional[PropositionEvidenceVerifier] = None,
    ) -> None:
        self.relevance_threshold = relevance_threshold
        self.sufficiency_threshold = sufficiency_threshold
        self.relevance_analyzer = relevance_analyzer or QuestionAwareRelevanceAnalyzer(
            relevance_threshold=self.relevance_threshold
        )
        self.contradiction_detector = contradiction_detector or PropertyContradictionDetector()
        self.evidence_verifier = evidence_verifier or PropositionEvidenceVerifier()

    def classify_propositions(
        self,
        question: str,
        reference_answer: str,
        student_answer: str,
        unmatched_student_props: Sequence[RobustProposition],
        matched_student_props: Sequence[RobustProposition] = (),
        reference_props: Sequence[RobustProposition] = (),
    ) -> RobustClassificationResult:
        """
        Classify all student propositions across matched and unmatched categories.
        """
        classified: List[ClassifiedProposition] = []
        counts: Dict[str, int] = {
            AdditionalInfoClass.MATCHED_BY_BASE_ASAG.value: 0,
            AdditionalInfoClass.CORRECT_ADDITIONAL.value: 0,
            AdditionalInfoClass.IRRELEVANT.value: 0,
            AdditionalInfoClass.INCORRECT.value: 0,
            AdditionalInfoClass.UNCERTAIN.value: 0,
        }

        # 1. Matched propositions retain base ASAG matched status
        for mp in matched_student_props:
            cp = ClassifiedProposition(
                proposition=mp,
                classification=AdditionalInfoClass.MATCHED_BY_BASE_ASAG,
                relevance_evidence=None,
                contradiction_evidence=None,
                score_effect=0.0,
                rationale="Proposition was matched to a reference proposition by Base ASAG.",
                verification_evidence=VerificationEvidence(
                    status=EvidenceStatus.SUPPORTED,
                    source=EvidenceSource.REFERENCE_ASSERTION,
                    confidence=1.0,
                    rationale="Proposition matches reference answer content.",
                ),
            )
            classified.append(cp)
            counts[AdditionalInfoClass.MATCHED_BY_BASE_ASAG.value] += 1

        # 2. Evaluate each unmatched proposition via 3-step evidence pipeline
        ref_list = list(reference_props)
        for up in unmatched_student_props:
            cp = self._evaluate_unmatched_proposition(
                proposition=up,
                question=question,
                reference_answer=reference_answer,
                reference_props=ref_list,
            )
            classified.append(cp)
            counts[cp.classification.value] += 1

        return RobustClassificationResult(
            question=question,
            reference_answer=reference_answer,
            student_answer=student_answer,
            total_propositions=len(classified),
            matched_count=len(matched_student_props),
            unmatched_count=len(unmatched_student_props),
            classified_propositions=classified,
            category_counts=counts,
        )

    def _evaluate_unmatched_proposition(
        self,
        proposition: RobustProposition,
        question: str,
        reference_answer: str,
        reference_props: List[RobustProposition],
    ) -> ClassifiedProposition:
        """Execute the evidence pipeline on a single unmatched proposition."""
        # STEP 1: Contradiction and Reference Incompatibility Check
        contra_evidence = self.contradiction_detector.detect_contradiction(
            student_prop=proposition,
            reference_props=reference_props,
        )

        # A proposition that directly contradicts reference facts is INCORRECT (misconception)
        if contra_evidence.is_contradicted:
            return ClassifiedProposition(
                proposition=proposition,
                classification=AdditionalInfoClass.INCORRECT,
                relevance_evidence=None,
                contradiction_evidence=contra_evidence,
                score_effect=0.0,
                rationale=(
                    f"Proposition contradicts reference evidence via {contra_evidence.contradiction_type.value}: "
                    f"{contra_evidence.explanation}"
                ),
                verification_evidence=VerificationEvidence(
                    status=EvidenceStatus.CONTRADICTED,
                    source=EvidenceSource.PROPERTY_CONTRADICTION,
                    confidence=contra_evidence.evidence_strength,
                    rationale=contra_evidence.explanation,
                ),
            )

        # STEP 2: Question-Aware Relevance & Domain Applicability Analysis
        rel_evidence = self.relevance_analyzer.evaluate(
            proposition=proposition,
            question=question,
            reference_answer=reference_answer,
        )

        is_domain_app = self.evidence_verifier.is_applicable(
            proposition=proposition,
            question=question,
            reference_answer=reference_answer,
        )

        # STEP 3: Domain Evidence Verification Check
        # A proposition reaches the evidence verifier if it is lexically relevant OR domain-applicable
        if rel_evidence.is_relevant or is_domain_app:
            verification_ev = self.evidence_verifier.verify(
                proposition=proposition,
                question=question,
                reference_answer=reference_answer,
            )

            if verification_ev.status == EvidenceStatus.SUPPORTED:
                citation_str = f" [{verification_ev.academic_citation}]" if verification_ev.academic_citation else ""
                return ClassifiedProposition(
                    proposition=proposition,
                    classification=AdditionalInfoClass.CORRECT_ADDITIONAL,
                    relevance_evidence=rel_evidence,
                    contradiction_evidence=contra_evidence,
                    score_effect=0.0,
                    rationale=(
                        f"Proposition is verified by domain knowledge rule '{verification_ev.rule_id}'"
                        f"{citation_str}: {verification_ev.rationale}"
                    ),
                    verification_evidence=verification_ev,
                )
            else:
                return ClassifiedProposition(
                    proposition=proposition,
                    classification=AdditionalInfoClass.UNCERTAIN,
                    relevance_evidence=rel_evidence,
                    contradiction_evidence=contra_evidence,
                    score_effect=0.0,
                    rationale=(
                        f"Proposition is relevant to the question/domain, but lacks positive domain knowledge verification. "
                        "Classified as UNCERTAIN to maintain grading neutrality."
                    ),
                    verification_evidence=verification_ev,
                )

        # STEP 4: Off-Topic / Peripheral Proposition
        return ClassifiedProposition(
            proposition=proposition,
            classification=AdditionalInfoClass.IRRELEVANT,
            relevance_evidence=rel_evidence,
            contradiction_evidence=contra_evidence,
            score_effect=0.0,
            rationale=(
                f"Low question-domain relevance ({rel_evidence.evidence_strength:.2f} < "
                f"threshold {self.relevance_threshold}) and no applicable domain knowledge rule. "
                "Proposition is off-topic or peripheral."
            ),
            verification_evidence=VerificationEvidence(
                status=EvidenceStatus.OFF_TOPIC,
                source=EvidenceSource.QUESTION_RELEVANCE,
                confidence=1.0 - rel_evidence.evidence_strength,
                rationale="Proposition lacks topical relevance to the assessment question and domain knowledge.",
            ),
        )
