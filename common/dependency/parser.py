"""
Shared dependency parsing interface.

Provides linguistic tokenization, POS tagging, and syntactic dependency parsing
wrapping the spaCy NLP engine for all ASAG models.
"""
from base_asag.dependency.parser import (
    DependencyParser,
    ParsedDocument,
    ParsedSentence,
    ParsedToken,
)

__all__ = ["DependencyParser", "ParsedDocument", "ParsedSentence", "ParsedToken"]
