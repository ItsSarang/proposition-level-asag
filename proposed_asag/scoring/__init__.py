"""
Proposed ASAG Scoring Package (Stage 14 & Overhaul Phase 8).

Provides components for computing proposed ASAG grades by incorporating
Stage 13 proposition-level additional-information evaluations while
preserving Base ASAG scores as an unperturbed control condition.
Supports linear (SUM), normalized (MEAN), and diminishing returns (SATURATING) strategies.
"""

from proposed_asag.scoring.proposed_scorer import (
    ProposedScorer,
    ProposedScoreResult,
    PropositionAdjustmentRecord,
)
from proposed_asag.scoring.bounded_scorer import (
    BoundedScorer,
    BoundedScoreResult,
    ScoringStrategy,
)
from proposed_asag.scoring.severity_aware_scorer import (
    SeverityAwareScorer,
    SeverityAwareScoreResult,
    SeverityItemizedAdjustment,
    SeverityAwarePipeline,
    SeverityAwareEvaluationResult,
)

from proposed_asag.scoring.model_d2_scorer import (
    ModelD2Scorer,
)

__all__ = [
    "ProposedScorer",
    "ProposedScoreResult",
    "PropositionAdjustmentRecord",
    "BoundedScorer",
    "BoundedScoreResult",
    "ScoringStrategy",
    "SeverityAwareScorer",
    "SeverityAwareScoreResult",
    "SeverityItemizedAdjustment",
    "SeverityAwarePipeline",
    "SeverityAwareEvaluationResult",
    "ModelD2Scorer",
]
