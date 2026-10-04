"""
Base ASAG Entailment Package (Stage 8).

Provides proposition-level textual entailment, contradiction detection,
and uncertainty evaluation over aligned dependency relations.
"""

from base_asag.entailment.analyzer import (
    EntailmentResult,
    PropositionalEntailmentAnalyzer,
)
from base_asag.entailment.polarity import PolarityDetector, PolarityInfo

__all__ = [
    "PolarityDetector",
    "PolarityInfo",
    "EntailmentResult",
    "PropositionalEntailmentAnalyzer",
]
