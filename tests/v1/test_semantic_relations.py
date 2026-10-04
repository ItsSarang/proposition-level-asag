"""
Unit tests for the Base ASAG Stage 6 Semantic and Lexical Relationship Component.

Covers:
1. Exact surface-form match.
2. Lemma match.
3. Exact match does not require WordNet.
4. Lemma match does not require WordNet.
5. POS-compatible semantic lookup.
6. POS-incompatible lookup is rejected or handled explicitly.
7. WordNet returns a reproducible relationship/similarity for a known test pair.
8. Unrelated terms do not receive a forced positive relationship.
9. Missing WordNet data is handled clearly.
10. Empty input handling.
11. Invalid input handling.
12. Serialization.
13. Stage 5 objects can be consumed directly.
14. The semantic module does not perform grading.
15. No sentence-level cosine similarity is introduced here.
"""

import pytest
from base_asag.dependency import DependencyParser, DependencyTripleExtractor
from base_asag.semantic import (
    LexicalSemanticComparator,
    SemanticRelation,
    is_pos_compatible,
    map_pos_to_wordnet,
)


@pytest.fixture(scope="module")
def comparator():
    """Provides a shared LexicalSemanticComparator instance."""
    return LexicalSemanticComparator()


@pytest.fixture(scope="module")
def parser():
    """Provides a shared DependencyParser instance."""
    return DependencyParser(model_name="en_core_web_sm")


@pytest.fixture(scope="module")
def extractor():
    """Provides a shared DependencyTripleExtractor instance."""
    return DependencyTripleExtractor()


# 1. Exact surface-form match
def test_exact_surface_match(comparator):
    """Verify identical surface strings produce exact_match=True with score 1.0."""
    res = comparator.compare("record", "record", source_pos="NOUN", target_pos="NOUN")

    assert isinstance(res, SemanticRelation)
    assert res.exact_match is True
    assert res.lemma_match is True
    assert res.similarity_score == 1.0
    assert res.method == "exact_match"
    assert res.semantic_relation == "EXACT_MATCH"

    # Case-insensitive check
    res_case = comparator.compare("Key", "key", source_pos="NOUN", target_pos="NOUN")
    assert res_case.exact_match is True
    assert res_case.similarity_score == 1.0
    assert res_case.method == "exact_match"


# 2. Lemma match
def test_lemma_match(comparator):
    """Verify different surface forms with identical lemmas produce lemma_match=True with score 1.0."""
    res = comparator.compare(
        source="identifies",
        target="identified",
        source_lemma="identify",
        target_lemma="identify",
        source_pos="VERB",
        target_pos="VERB",
    )

    assert res.exact_match is False
    assert res.lemma_match is True
    assert res.similarity_score == 1.0
    assert res.method == "lemma_match"
    assert res.semantic_relation == "LEMMA_MATCH"


# 3. Exact match does not require WordNet
def test_exact_match_does_not_require_wordnet(comparator):
    """Verify non-dictionary synthetic terms match at exact level without WordNet lookup."""
    synthetic_term = "unseen_synthetic_entity_123"
    res = comparator.compare(synthetic_term, synthetic_term, source_pos="NOUN", target_pos="NOUN")

    assert res.exact_match is True
    assert res.similarity_score == 1.0
    assert res.method == "exact_match"
    assert res.synset_source is None
    assert res.synset_target is None


# 4. Lemma match does not require WordNet
def test_lemma_match_does_not_require_wordnet(comparator):
    """Verify synthetic terms with matching lemmas succeed without WordNet lookup."""
    res = comparator.compare(
        source="synth_item_alpha",
        target="synth_item_beta",
        source_lemma="synth_item",
        target_lemma="synth_item",
        source_pos="NOUN",
        target_pos="NOUN",
    )

    assert res.exact_match is False
    assert res.lemma_match is True
    assert res.similarity_score == 1.0
    assert res.method == "lemma_match"
    assert res.synset_source is None
    assert res.synset_target is None


# 5. POS-compatible semantic lookup
def test_pos_compatible_lookup(comparator):
    """Verify POS-compatible words proceed to WordNet and identify synonymy or similarity."""
    # Direct synonyms: car vs automobile (NOUN)
    res_syn = comparator.compare(
        source="car",
        target="automobile",
        source_lemma="car",
        target_lemma="automobile",
        source_pos="NOUN",
        target_pos="NOUN",
    )

    assert res_syn.pos_compatible is True
    assert res_syn.exact_match is False
    assert res_syn.lemma_match is False
    assert res_syn.similarity_score == 1.0
    assert res_syn.method == "wordnet_synonym"
    assert res_syn.semantic_relation == "WORDNET_SYNONYM"
    assert res_syn.synset_source == res_syn.synset_target


# 6. POS-incompatible lookup is rejected or handled explicitly
def test_pos_incompatible_handling(comparator):
    """Verify comparing different parts of speech returns POS_INCOMPATIBLE with score 0.0."""
    res = comparator.compare(
        source="identifies",
        target="table",
        source_lemma="identify",
        target_lemma="table",
        source_pos="VERB",
        target_pos="NOUN",
    )

    assert res.pos_compatible is False
    assert res.exact_match is False
    assert res.lemma_match is False
    assert res.similarity_score == 0.0
    assert res.method == "pos_incompatible"
    assert res.semantic_relation == "POS_INCOMPATIBLE"


# 7. WordNet returns reproducible relationship/similarity for known test pair
def test_reproducible_wordnet_similarity(comparator):
    """Verify dog vs cat yields deterministic, non-zero path similarity in WordNet."""
    res = comparator.compare(
        source="dog",
        target="cat",
        source_lemma="dog",
        target_lemma="cat",
        source_pos="NOUN",
        target_pos="NOUN",
    )

    assert res.pos_compatible is True
    assert res.method == "wordnet_path"
    assert res.similarity_score > 0.0
    assert 0.0 < res.similarity_score <= 1.0
    assert res.synset_source is not None
    assert res.synset_target is not None


# 8. Unrelated terms do not receive a forced positive relationship
def test_unrelated_terms_not_forced_positive(comparator):
    """Verify completely distant concepts receive low similarity."""
    res = comparator.compare(
        source="record",
        target="photosynthesis",
        source_lemma="record",
        target_lemma="photosynthesis",
        source_pos="NOUN",
        target_pos="NOUN",
    )

    assert res.pos_compatible is True
    # Path similarity between distant taxonomy nodes is typically <= 0.1
    assert res.similarity_score <= 0.1


# 9. Missing WordNet data is handled clearly
def test_missing_wordnet_data_handling(comparator):
    """Verify terms absent from WordNet yield NO_SYNSET with 0.0 score."""
    res = comparator.compare(
        source="record",
        target="xyznonexistenttoken123",
        source_lemma="record",
        target_lemma="xyznonexistenttoken123",
        source_pos="NOUN",
        target_pos="NOUN",
    )

    assert res.pos_compatible is True
    assert res.similarity_score == 0.0
    assert res.semantic_relation == "NO_SYNSET"
    assert res.method == "wordnet_path"


# 10. Empty input handling
def test_empty_input_handling(comparator):
    """Verify empty or whitespace strings explicitly raise ValueError."""
    with pytest.raises(ValueError):
        comparator.compare("", "record")

    with pytest.raises(ValueError):
        comparator.compare("record", "   ")


# 11. Invalid input handling
def test_invalid_input_handling(comparator):
    """Verify non-string / non-token inputs explicitly raise TypeError."""
    invalid_inputs = [None, 123, 45.67, ["invalid"], {"dict": 1}]
    for invalid in invalid_inputs:
        with pytest.raises(TypeError):
            comparator.compare(invalid, "record")
        with pytest.raises(TypeError):
            comparator.compare("record", invalid)


# 12. Serialization
def test_serialization(comparator):
    """Verify SemanticRelation serializes cleanly to a dictionary."""
    res = comparator.compare("key", "column", source_pos="NOUN", target_pos="NOUN")
    data = res.to_dict()

    expected_keys = {
        "source_text",
        "target_text",
        "source_lemma",
        "target_lemma",
        "source_pos",
        "target_pos",
        "exact_match",
        "lemma_match",
        "pos_compatible",
        "semantic_relation",
        "similarity_score",
        "method",
        "synset_source",
        "synset_target",
    }
    assert expected_keys.issubset(data.keys())
    assert isinstance(data["similarity_score"], float)


# 13. Stage 5 objects can be consumed directly
def test_consume_stage5_objects(parser, extractor, comparator):
    """Verify ParsedToken objects from Stage 4/5 can be passed directly to comparator."""
    ref_sent = parser.parse_sentence("A primary key uniquely identifies each record in a table.")
    stu_sent = parser.parse_sentence("A primary key uniquely identifies every row in a table.")

    ref_triples = extractor.extract(ref_sent)
    stu_triples = extractor.extract(stu_sent)

    ref_rel = ref_triples.canonical_relations[0]
    stu_rel = stu_triples.canonical_relations[0]

    # Retrieve ParsedToken objects for the object arguments ('record' and 'row')
    ref_tok = ref_sent.get_token(ref_rel.object_index)
    stu_tok = stu_sent.get_token(stu_rel.object_index)

    # Pass tokens directly
    res = comparator.compare(ref_tok, stu_tok)

    assert isinstance(res, SemanticRelation)
    assert res.source_text == "record"
    assert res.target_text == "row"
    assert res.source_lemma == "record"
    assert res.target_lemma == "row"
    assert res.pos_compatible is True
    assert res.exact_match is False
    assert res.lemma_match is False
    # Verified path similarity in WordNet for record.n.04 and quarrel.n.01 is 0.125
    assert res.method == "wordnet_path"
    assert res.similarity_score == pytest.approx(0.125, rel=1e-3)


# 14. The semantic module does not perform grading
def test_no_grading_in_stage_6(comparator):
    """Verify that Stage 6 components contain no grading logic or grade fields."""
    res = comparator.compare("record", "row", source_pos="NOUN", target_pos="NOUN")

    assert not hasattr(res, "grade")
    assert not hasattr(res, "marks")
    assert not hasattr(res, "score_percentage")
    assert not hasattr(res, "is_correct")
    assert not hasattr(comparator, "grade")
    assert not hasattr(comparator, "score_answer")


# 15. No sentence-level cosine similarity is introduced here
def test_no_cosine_similarity_introduced():
    """Verify that Stage 6 module does not import or implement sentence cosine similarity."""
    import base_asag.semantic.relations as rel_mod
    assert not hasattr(rel_mod, "cosine_similarity")
    assert not hasattr(rel_mod, "TfidfVectorizer")


# 16. POS mapping utilities
def test_pos_mapping_utilities():
    """Verify Universal and Penn Treebank POS tag mapping to WordNet categories."""
    assert map_pos_to_wordnet("NOUN") == "n"
    assert map_pos_to_wordnet("VERB") == "v"
    assert map_pos_to_wordnet("ADJ") == "a"
    assert map_pos_to_wordnet("ADV") == "r"
    assert map_pos_to_wordnet("NN") == "n"
    assert map_pos_to_wordnet("VBZ") == "v"
    assert map_pos_to_wordnet("DET") is None
    assert map_pos_to_wordnet("PUNCT") is None

    assert is_pos_compatible("NOUN", "PROPN") is True
    assert is_pos_compatible("NOUN", "VERB") is False
    assert is_pos_compatible("DET", "DET") is False  # Non-content categories
