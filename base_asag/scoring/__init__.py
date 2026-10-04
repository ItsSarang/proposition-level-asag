"""
Base ASAG Scoring Package (Stage 9).

Provides reference proposition coverage scoring, evidence aggregation,
and score scaling for the Base ASAG pipeline.
"""

from base_asag.scoring.base_scorer import (
    BaseASAGScorer,
    BaseScoreResult,
    PropositionScoreRecord,
)

__all__ = [
    "BaseASAGScorer",
    "BaseScoreResult",
    "PropositionScoreRecord",
]
