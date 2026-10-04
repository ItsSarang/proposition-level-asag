"""
Evidence Verification Data Models (Phase 9).

Defines epistemic evidence statuses, sources, and verification records
to decouple factual evidence verification from grading classification policy.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class EvidenceStatus(str, Enum):
    """
    Epistemic verification state of an unmatched proposition.
    Independently evaluated before policy classification.
    """
    SUPPORTED = "SUPPORTED"        # Auditable positive evidence verifies the proposition is true
    CONTRADICTED = "CONTRADICTED"  # Contradiction detector identifies incompatible/opposing facts
    UNVERIFIED = "UNVERIFIED"      # Relevant to question domain, but lacks positive verification
    OFF_TOPIC = "OFF_TOPIC"        # Fails question-aware topical relevance check


class EvidenceSource(str, Enum):
    """Origin of the corroborating or refuting evidence."""
    DOMAIN_KNOWLEDGE_BASE = "DOMAIN_KNOWLEDGE_BASE"
    REFERENCE_ASSERTION = "REFERENCE_ASSERTION"
    PROPERTY_CONTRADICTION = "PROPERTY_CONTRADICTION"
    QUESTION_RELEVANCE = "QUESTION_RELEVANCE"


@dataclass(frozen=True)
class VerificationEvidence:
    """
    Full provenance record for an evidence verification decision.
    """
    status: EvidenceStatus
    source: EvidenceSource
    rule_id: Optional[str] = None
    target_entity: Optional[str] = None
    target_property: Optional[str] = None
    confidence: float = 0.0
    rationale: str = ""
    academic_citation: Optional[str] = None
    slot_matches: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "source": self.source.value,
            "rule_id": self.rule_id,
            "target_entity": self.target_entity,
            "target_property": self.target_property,
            "confidence": round(self.confidence, 4),
            "rationale": self.rationale,
            "academic_citation": self.academic_citation,
            "slot_matches": self.slot_matches,
        }
