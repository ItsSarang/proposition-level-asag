"""
Shared dependency triple representations.

Extracts Subject-Predicate-Object canonical relational structures from
dependency parse trees, supporting core clausal proposition analysis.
"""
from base_asag.dependency.triples import (
    DependencyRelation,
    DependencyTripleExtractor,
    DocumentTriples,
    SentenceTriples,
)

__all__ = [
    "DependencyRelation",
    "DependencyTripleExtractor",
    "DocumentTriples",
    "SentenceTriples",
]
