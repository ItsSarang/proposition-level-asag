"""
Proposition Evidence Verifier (Phase 9).

Executes independent factual evidence verification on unmatched student propositions
against curated domain knowledge, strictly isolated from grading policy classifiers.
"""

from typing import Optional

from base_asag.representation.hybrid import RobustProposition
from proposed_asag.evidence.domain_knowledge import CuratedDomainKnowledge
from proposed_asag.evidence.models import EvidenceSource, EvidenceStatus, VerificationEvidence


class PropositionEvidenceVerifier:
    """
    Verifies whether an unmatched student proposition has positive domain evidence.
    Does NOT assign grades or policy classifications.
    """

    def __init__(self, domain_knowledge: Optional[CuratedDomainKnowledge] = None) -> None:
        self.domain_knowledge = domain_knowledge or CuratedDomainKnowledge()

    def verify(
        self,
        proposition: RobustProposition,
        question: str = "",
        reference_answer: str = "",
    ) -> VerificationEvidence:
        """
        Verify proposition against domain knowledge resources.
        Returns explicit VerificationEvidence with provenance and academic citation.
        """
        match_result = self.domain_knowledge.find_matching_rule(
            proposition, question=question, context=reference_answer
        )

        if match_result is not None:
            rule, slot_evidence = match_result
            return VerificationEvidence(
                status=EvidenceStatus.SUPPORTED,
                source=EvidenceSource.DOMAIN_KNOWLEDGE_BASE,
                rule_id=rule.rule_id,
                target_entity=rule.target_entity_lemmas[0],
                target_property=rule.property_category,
                confidence=0.90,
                rationale=rule.rationale,
                academic_citation=rule.academic_citation,
                slot_matches=slot_evidence,
            )

        return VerificationEvidence(
            status=EvidenceStatus.UNVERIFIED,
            source=EvidenceSource.DOMAIN_KNOWLEDGE_BASE,
            rule_id=None,
            target_entity=proposition.subject_lemma,
            target_property=None,
            confidence=0.50,
            rationale=(
                "Proposition is topical, but lacks positive verification in the curated domain knowledge "
                "resource. Held as UNVERIFIED to avoid unearned bonus credit."
            ),
            academic_citation=None,
            slot_matches={},
        )

    def is_applicable(
        self,
        proposition: RobustProposition,
        question: str = "",
        reference_answer: str = "",
    ) -> bool:
        """Check if proposition is domain-applicable to curated rules in context."""
        return self.domain_knowledge.is_domain_applicable(
            proposition=proposition,
            question=question,
            reference_answer=reference_answer,
        )
