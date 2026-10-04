"""
Evidence Verification Module (Phase 9).
"""

from proposed_asag.evidence.models import (
    EvidenceSource,
    EvidenceStatus,
    VerificationEvidence,
)
from proposed_asag.evidence.domain_knowledge import (
    CuratedDomainKnowledge,
    DomainPropertyRule,
)
from proposed_asag.evidence.evidence_verifier import (
    PropositionEvidenceVerifier,
)

__all__ = [
    "EvidenceStatus",
    "EvidenceSource",
    "VerificationEvidence",
    "DomainPropertyRule",
    "CuratedDomainKnowledge",
    "PropositionEvidenceVerifier",
]
