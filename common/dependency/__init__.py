"""Common dependency parsing and triple extraction."""
from base_asag.dependency.parser import DependencyParser, ParsedDocument, ParsedSentence, ParsedToken
from base_asag.dependency.triples import DependencyRelation, DependencyTripleExtractor, DocumentTriples, SentenceTriples

__all__ = [
    "DependencyParser",
    "ParsedDocument",
    "ParsedSentence",
    "ParsedToken",
    "DependencyRelation",
    "DependencyTripleExtractor",
    "DocumentTriples",
    "SentenceTriples",
]
