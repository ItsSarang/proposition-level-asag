"""
Unit tests for SemanticMatcherV1 and SemanticMatcherV2 (Phase 3).
"""

import pytest
from base_asag.semantic.relations import LexicalSemanticComparator
from base_asag.semantic.semantic_matcher_v2 import (
    SemanticMatcherV1,
    SemanticMatcherV2,
)


@pytest.fixture(scope="module")
def matcher_v1():
    return SemanticMatcherV1()


@pytest.fixture(scope="module")
def matcher_v2():
    return SemanticMatcherV2()


def test_v1_identical_to_comparator(matcher_v1):
    """Verify that SemanticMatcherV1 is a direct alias of LexicalSemanticComparator."""
    assert issubclass(SemanticMatcherV1, LexicalSemanticComparator)
    res = matcher_v1.compare("compiler", "compiler")
    assert res.exact_match is True
    assert res.similarity_score == 1.0


def test_v2_exact_and_lemma(matcher_v2):
    """Test exact surface and lemma matches in V2."""
    res_exact = matcher_v2.compare("converts", "converts")
    assert res_exact.exact_match is True
    assert res_exact.similarity_score == 1.0
    assert res_exact.method == "exact_match"

    res_lemma = matcher_v2.compare("converts", "convert")
    assert res_lemma.lemma_match is True
    assert res_lemma.similarity_score == 0.95
    assert res_lemma.method == "lemma_match"


def test_v2_morphological_derivation(matcher_v2):
    """Test controlled morphological derivation (e.g. execute <-> execution, define <-> definition)."""
    res1 = matcher_v2.compare("execute", "execution")
    assert res1.method == "morphological_derivation"
    assert res1.similarity_score == 0.85

    res2 = matcher_v2.compare("define", "definition")
    assert res2.method == "morphological_derivation"
    assert res2.similarity_score == 0.85


def test_v2_domain_lexical_equivalence(matcher_v2):
    """Test domain-specific computer science equivalences (e.g. row <-> record, translate <-> convert)."""
    res_row = matcher_v2.compare("row", "record")
    assert res_row.method == "domain_lexical_equivalence"
    assert res_row.similarity_score == 0.80

    res_convert = matcher_v2.compare("translate", "convert")
    assert res_convert.method == "domain_lexical_equivalence"
    assert res_convert.similarity_score == 0.80

    res_instantiate = matcher_v2.compare("instantiate", "create")
    assert res_instantiate.method == "domain_lexical_equivalence"
    assert res_instantiate.similarity_score == 0.80


def test_v2_unrelated_terms(matcher_v2):
    """Test completely unrelated terms return zero score."""
    res = matcher_v2.compare("compiler", "banana")
    assert res.similarity_score == 0.0
    assert res.method in ("none", "pos_incompatible")
