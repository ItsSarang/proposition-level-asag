"""Common provenance, alignment, and explanation trace types."""
from proposed_asag.proposition.alignment import (
    MatchedPropositionEvidence,
    PropositionAlignmentExtractor,
    PropositionAlignmentResult,
    SpanInfo,
    UnmatchedStudentPropositionEvidence,
)
from proposed_asag.explanation.trace_generator import ExplanationTraceGenerator, GradingExplanationTrace

__all__ = [
    "MatchedPropositionEvidence",
    "PropositionAlignmentExtractor",
    "PropositionAlignmentResult",
    "SpanInfo",
    "UnmatchedStudentPropositionEvidence",
    "ExplanationTraceGenerator",
    "GradingExplanationTrace",
]
