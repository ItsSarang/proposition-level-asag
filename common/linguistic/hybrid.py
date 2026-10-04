"""
Shared hybrid proposition representation.

Defines robust linguistic proposition structures supporting non-clausal,
infinitive, participle, and copular structures beyond rigid S-P-O triples.
"""
from base_asag.representation.hybrid import (
    Modality,
    Polarity,
    PropositionType,
    RobustProposition,
    RobustPropositionExtractor,
)

__all__ = [
    "Modality",
    "Polarity",
    "PropositionType",
    "RobustProposition",
    "RobustPropositionExtractor",
]
