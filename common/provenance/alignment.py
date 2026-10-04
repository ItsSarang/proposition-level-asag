"""
Shared proposition alignment and text span provenance structures.

Provides SpanInfo, MatchedPropositionEvidence, and UnmatchedStudentPropositionEvidence
for tracking character offsets and justification rationale.
"""
from proposed_asag.proposition.alignment import (
    MatchedPropositionEvidence,
    PropositionAlignmentExtractor,
    PropositionAlignmentResult,
    SpanInfo,
    UnmatchedStudentPropositionEvidence,
)

__all__ = [
    "MatchedPropositionEvidence",
    "PropositionAlignmentExtractor",
    "PropositionAlignmentResult",
    "SpanInfo",
    "UnmatchedStudentPropositionEvidence",
]
