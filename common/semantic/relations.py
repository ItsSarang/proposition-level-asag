"""
Shared lexical-semantic relation analysis.

Implements the multi-tiered lexical similarity hierarchy:
1. Exact surface match (1.0)
2. Lemma match (0.9)
3. POS-compatible match (0.7)
4. WordNet synset path similarity (fallback)
"""
from base_asag.semantic.relations import (
    LexicalSemanticComparator,
    SemanticMatchTier,
    SlotSimilarity,
)

__all__ = [
    "LexicalSemanticComparator",
    "SemanticMatchTier",
    "SlotSimilarity",
]
