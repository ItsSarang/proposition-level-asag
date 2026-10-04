"""
Shared domain lexicon and equivalence dictionaries.

Maintains curated computer science domain equivalences and antonym pairs
used across multi-tier semantic matching and contradiction detection.
"""
from base_asag.semantic.domain_lexicon import (
    ANTONYM_PAIRS,
    DOMAIN_EQUIVALENCES,
    get_domain_equivalence,
    is_domain_equivalent,
)

__all__ = [
    "ANTONYM_PAIRS",
    "DOMAIN_EQUIVALENCES",
    "get_domain_equivalence",
    "is_domain_equivalent",
]
