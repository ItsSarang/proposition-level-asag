"""
Unit tests for the curated Computer Science domain lexicon.
"""

import pytest
from base_asag.semantic.domain_lexicon import (
    DOMAIN_EQUIVALENCE_RATIONALE,
    DOMAIN_LEXICAL_EQUIVALENCES,
    are_domain_equivalent,
    get_domain_equivalence_rationale,
)
from base_asag.semantic.semantic_matcher_v2 import SemanticMatcherV2


def test_domain_lexicon_contains_thirteen_keys():
    expected_terms = {
        "record", "row", "convert", "translate", "instantiate",
        "create", "prototype", "definition", "terminate",
        "deallocate", "free", "subroutine", "function"
    }
    assert set(DOMAIN_LEXICAL_EQUIVALENCES.keys()) == expected_terms
    assert len(DOMAIN_LEXICAL_EQUIVALENCES) == 13


def test_domain_lexicon_symmetry():
    # If A contains B, B must contain A in DOMAIN_LEXICAL_EQUIVALENCES
    for term_a, targets in DOMAIN_LEXICAL_EQUIVALENCES.items():
        for term_b in targets:
            if term_b in DOMAIN_LEXICAL_EQUIVALENCES:
                assert term_a in DOMAIN_LEXICAL_EQUIVALENCES[term_b], (
                    f"Asymmetry detected: '{term_a}' -> '{term_b}' but '{term_b}' does not map to '{term_a}'"
                )


def test_are_domain_equivalent_functionality():
    assert are_domain_equivalent("record", "row") is True
    assert are_domain_equivalent("row", "record") is True
    assert are_domain_equivalent("instantiate", "create") is True
    assert are_domain_equivalent("prototype", "signature") is True
    assert are_domain_equivalent("deallocate", "free") is True
    assert are_domain_equivalent("record", "deallocate") is False
    assert are_domain_equivalent("pointer", "array") is False
    # Identity
    assert are_domain_equivalent("record", "record") is True


def test_domain_equivalence_rationales_documented():
    for term in DOMAIN_LEXICAL_EQUIVALENCES:
        rationale = get_domain_equivalence_rationale(term)
        assert rationale is not None, f"Missing documented rationale for domain term '{term}'"
        assert len(rationale.strip()) > 20


def test_semantic_matcher_v2_lexicon_toggle():
    matcher_with = SemanticMatcherV2(use_domain_equivalence=True)
    matcher_without = SemanticMatcherV2(use_domain_equivalence=False)

    rel_with = matcher_with.compare("record", "row", source_pos="NN", target_pos="NN")
    rel_without = matcher_without.compare("record", "row", source_pos="NN", target_pos="NN")

    assert rel_with.semantic_relation == "DOMAIN_LEXICAL_EQUIVALENCE"
    assert rel_with.similarity_score == 0.80
    assert rel_with.method == "domain_lexical_equivalence"

    # When disabled, it falls back to WordNet path similarity or low score
    assert rel_without.semantic_relation != "DOMAIN_LEXICAL_EQUIVALENCE"
