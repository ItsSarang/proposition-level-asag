"""
Base ASAG Semantic Analysis Package.

Provides lexical and WordNet-based semantic relationship analysis
across exact match, lemma match, morphological derivation, and WordNet tiers.
"""

from base_asag.semantic.relations import (
    LexicalSemanticComparator,
    SemanticRelation,
    is_pos_compatible,
    map_pos_to_wordnet,
)
from base_asag.semantic.semantic_matcher_v2 import (
    SemanticMatcherV1,
    SemanticMatcherV2,
)

__all__ = [
    "LexicalSemanticComparator",
    "SemanticRelation",
    "is_pos_compatible",
    "map_pos_to_wordnet",
    "SemanticMatcherV1",
    "SemanticMatcherV2",
]
