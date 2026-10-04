"""
Base ASAG Dependency Package.

Provides dependency parsing (Stage 4) and dependency structures / triples (Stage 5)
for the Base ASAG pipeline.
"""

from base_asag.dependency.parser import (
    DependencyParser,
    ParsedDocument,
    ParsedSentence,
    ParsedToken,
)
from base_asag.dependency.triples import (
    DependencyArc,
    DependencyRelation,
    DependencyTripleExtractor,
    DocumentTriples,
    SentenceTriples,
)

__all__ = [
    "DependencyParser",
    "ParsedDocument",
    "ParsedSentence",
    "ParsedToken",
    "DependencyArc",
    "DependencyRelation",
    "SentenceTriples",
    "DocumentTriples",
    "DependencyTripleExtractor",
]
