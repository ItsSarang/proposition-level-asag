"""
Base ASAG Matching Package (Stage 7 & Overhaul Phase 4).

Provides dependency triple matching between reference and student answers,
evaluating slot-level semantic alignment, establishing one-to-one matches,
and preserving unmatched reference and student relations.
Supports both greedy and global (Hungarian algorithm) matching strategies.
"""

from base_asag.matching.triple_matcher import (
    CandidateAlignment,
    MatchedRelation,
    MatchingResult,
    TripleMatcher,
)
from base_asag.matching.global_matcher import (
    ConfigurableTripleMatcher,
)

__all__ = [
    "TripleMatcher",
    "ConfigurableTripleMatcher",
    "MatchedRelation",
    "CandidateAlignment",
    "MatchingResult",
]
