"""
Unit tests for the Base ASAG Stage 4 Dependency Parsing Component.

Covers:
1. Basic dependency parsing of a normal sentence.
2. A dependency root is identified.
3. Dependency labels are produced.
4. Every parsed token has a head/index representation.
5. Lemmas/POS information from preprocessing is retained consistently.
6. Multiple sentences can be parsed separately.
7. Punctuation remains represented.
8. Empty input handling.
9. Whitespace-only input handling.
10. Non-string/invalid input handling.
11. Confirmation that dependency triples are NOT generated in Stage 4.
12. Clean integration with Stage 3 ProcessedSentence and ProcessedDocument.
"""

import pytest
from base_asag.dependency import (
    DependencyParser,
    ParsedDocument,
    ParsedSentence,
    ParsedToken,
)
from base_asag.preprocessing import TextPreprocessor


@pytest.fixture(scope="module")
def parser():
    """Provides a shared DependencyParser instance."""
    return DependencyParser(model_name="en_core_web_sm")


@pytest.fixture(scope="module")
def preprocessor():
    """Provides a shared TextPreprocessor instance."""
    return TextPreprocessor(model_name="en_core_web_sm")


# 1. Basic dependency parsing of a normal sentence
def test_basic_dependency_parsing(parser):
    """Test basic parsing on the primary key reference sentence."""
    text = "A primary key uniquely identifies each record in a table."
    sent = parser.parse_sentence(text)

    assert isinstance(sent, ParsedSentence)
    assert sent.token_count == 11
    assert sent.original_text == text
    assert len(sent.tokens) == 11
    assert all(isinstance(t, ParsedToken) for t in sent.tokens)


# 2. A dependency root is identified
def test_dependency_root_identified(parser):
    """Verify that every parsed sentence has an identifiable root token."""
    text = "A primary key uniquely identifies each record in a table."
    sent = parser.parse_sentence(text)

    root = sent.root
    assert root is not None
    assert isinstance(root, ParsedToken)
    assert root.is_root is True
    assert root.dep.upper() == "ROOT"
    assert root.lemma == "identify"
    assert root.pos == "VERB"
    # Root points to itself in standard dependency trees
    assert root.head_index == root.index


# 3. Dependency labels are produced
def test_dependency_labels_produced(parser):
    """Verify all tokens receive valid, non-empty grammatical dependency labels."""
    text = "A primary key uniquely identifies each record in a table."
    sent = parser.parse_sentence(text)

    assert len(sent.dep_labels) == sent.token_count
    for label in sent.dep_labels:
        assert isinstance(label, str)
        assert len(label.strip()) > 0

    # Verify standard universal dependency labels exist in the sentence
    assert "ROOT" in sent.dep_labels
    assert any("subj" in dep for dep in sent.dep_labels)  # nsubj exists


# 4. Every parsed token has a head/index representation
def test_head_and_index_representation(parser):
    """Verify that every token has valid sentence-relative index and head_index."""
    text = "A primary key uniquely identifies each record in a table."
    sent = parser.parse_sentence(text)

    for i, tok in enumerate(sent.tokens):
        assert tok.index == i
        assert 0 <= tok.head_index < sent.token_count

        # Head lookup consistency
        head_tok = sent.get_head(tok)
        assert head_tok.text == tok.head_text
        assert head_tok.index == tok.head_index

        # Children indices consistency
        children = sent.get_children(tok)
        for child in children:
            assert child.head_index == tok.index


# 5. Lemmas/POS information from preprocessing is retained consistently
def test_consistency_with_stage3_preprocessing(parser, preprocessor):
    """Verify that Stage 4 parsing retains exact tokens, lemmas, and POS tags from Stage 3."""
    text = "A primary key uniquely identifies each record in a table."
    proc_doc = preprocessor.process(text)
    proc_sent = proc_doc.sentences[0]

    # Parse using ProcessedSentence input
    parsed_sent = parser.parse_sentence(proc_sent)

    assert parsed_sent.token_count == proc_sent.token_count
    assert [t.text for t in parsed_sent.tokens] == proc_sent.tokens
    assert parsed_sent.lemmas == proc_sent.lemmas
    assert parsed_sent.pos_tags == proc_sent.pos_tags


# 6. Multiple sentences can be parsed separately
def test_multiple_sentences_parsing(parser, preprocessor):
    """Verify multi-sentence answer parsing produces distinct sentences with valid relative heads."""
    text = "A primary key uniquely identifies each record in a table. SQL was developed in the 1970s."
    proc_doc = preprocessor.process(text)

    # Parse multi-sentence ProcessedDocument
    parsed_doc = parser.parse_document(proc_doc)
    assert isinstance(parsed_doc, ParsedDocument)
    assert parsed_doc.sentence_count == 2

    # Each sentence has its own root and valid sentence-relative indexing
    s1 = parsed_doc.sentences[0]
    s2 = parsed_doc.sentences[1]

    assert s1.root is not None
    assert s2.root is not None
    assert s1.root.lemma == "identify"
    assert s2.root.lemma == "develop"

    # Verify head indices are strictly within sentence bounds
    for tok in s1.tokens:
        assert 0 <= tok.head_index < s1.token_count
    for tok in s2.tokens:
        assert 0 <= tok.head_index < s2.token_count


# 7. Punctuation remains represented
def test_punctuation_represented(parser):
    """Verify punctuation is retained in the dependency tree and receives a punct relation."""
    text = "A primary key uniquely identifies each record in a table."
    sent = parser.parse_sentence(text)

    punct_tokens = [t for t in sent.tokens if t.is_punct]
    assert len(punct_tokens) >= 1
    assert punct_tokens[-1].text == "."
    assert punct_tokens[-1].dep.lower() == "punct"
    # Punctuation attaches to a head inside the sentence
    assert 0 <= punct_tokens[-1].head_index < sent.token_count


# 8. Empty input handling
def test_empty_input_handling(parser):
    """Verify empty inputs raise ValueError by default or yield empty structures when allow_empty=True."""
    with pytest.raises(ValueError, match="cannot be empty"):
        parser.parse_sentence("")

    with pytest.raises(ValueError, match="cannot be empty"):
        parser.parse_document("")

    # allow_empty=True behavior
    empty_sent = parser.parse_sentence("", allow_empty=True)
    assert empty_sent.token_count == 0
    assert empty_sent.root is None

    empty_doc = parser.parse_document("", allow_empty=True)
    assert empty_doc.sentence_count == 0
    assert empty_doc.tokens == []


# 9. Whitespace-only input handling
def test_whitespace_only_handling(parser):
    """Verify whitespace-only inputs raise ValueError when allow_empty=False."""
    with pytest.raises(ValueError, match="cannot be empty"):
        parser.parse_sentence("   \t\n  \r  ")

    with pytest.raises(ValueError, match="cannot be empty"):
        parser.parse_document("   \t\n  \r  ")


# 10. Non-string/invalid input handling
def test_invalid_input_handling(parser):
    """Verify invalid input types raise TypeError."""
    invalid_types = [None, 123, 45.67, ["invalid", "list"], {"key": "val"}]
    for invalid in invalid_types:
        with pytest.raises(TypeError):
            parser.parse_sentence(invalid)

        with pytest.raises(TypeError):
            parser.parse_document(invalid)

        with pytest.raises(TypeError):
            parser.parse(invalid)


# 11. Confirmation that dependency triples are NOT generated in Stage 4
def test_no_dependency_triples_in_stage_4(parser):
    """
    Stage 4 is strictly responsible for syntactic dependency parsing.
    Dependency triple generation is explicitly reserved for Stage 5.
    Verify that Stage 4 structures do NOT contain triples.
    """
    text = "A primary key uniquely identifies each record in a table."
    sent = parser.parse_sentence(text)
    doc = parser.parse_document(text)

    # Neither ParsedSentence nor ParsedDocument should have a triples attribute
    assert not hasattr(sent, "triples")
    assert not hasattr(doc, "triples")
    assert not hasattr(parser, "extract_triples")
    assert not hasattr(parser, "generate_triples")

    # Tokens should not contain triple fields
    assert not hasattr(sent.tokens[0], "triple")


# 12. Polymorphic parse() API check
def test_polymorphic_parse_api(parser, preprocessor):
    """Verify that parser.parse() correctly dispatches based on input type."""
    text = "A primary key uniquely identifies each record in a table."
    proc_doc = preprocessor.process(text)
    proc_sent = proc_doc.sentences[0]

    # Passing ProcessedSentence yields ParsedSentence
    res_sent = parser.parse(proc_sent)
    assert isinstance(res_sent, ParsedSentence)

    # Passing ProcessedDocument yields ParsedDocument
    res_doc = parser.parse(proc_doc)
    assert isinstance(res_doc, ParsedDocument)

    # Passing raw string yields ParsedDocument
    res_str = parser.parse(text)
    assert isinstance(res_str, ParsedDocument)


# 13. Dictionary serialization
def test_to_dict_serialization(parser):
    """Verify ParsedSentence and ParsedDocument serialize cleanly to dictionaries."""
    text = "A primary key uniquely identifies each record in a table."
    sent = parser.parse_sentence(text)
    data = sent.to_dict()

    assert data["token_count"] == 11
    assert data["root"]["lemma"] == "identify"
    assert "tokens" in data
    assert "dep_labels" in data
    assert len(data["tokens"]) == 11


# 14. Nominal root repair with nmod label (Stage 10A regression test)
def test_nominal_root_repair_with_nmod(parser):
    """
    Verify that statistical mis-parsing of transitive verbs as nominal modifiers
    (nmod) before an object noun with intervening modifiers is repaired.

    Sentence: 'A compiler converts high-level source code into machine code.'
    - 'converts' is repaired to ROOT (VERB)
    - 'compiler' is repaired to nsubj
    - 'code' is repaired to dobj
    """
    text = "A compiler converts high-level source code into machine code."
    sent = parser.parse_sentence(text)

    root = sent.root
    assert root is not None
    assert root.text == "converts"
    assert root.pos == "VERB"
    assert root.dep.upper() == "ROOT"

    # Subject check
    nsubj = next((t for t in sent.tokens if t.dep == "nsubj"), None)
    assert nsubj is not None
    assert nsubj.text == "compiler"
    assert nsubj.head_index == root.index

    # Object check
    dobj = next((t for t in sent.tokens if t.dep == "dobj"), None)
    assert dobj is not None
    assert dobj.text == "code"
    assert dobj.head_index == root.index

