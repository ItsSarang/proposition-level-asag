"""
Unit tests for the Base ASAG Stage 3 Preprocessing Component.

Covers:
1. Normal sentence processing
2. Lower/upper-case normalization
3. Lemmatization of a word such as: identifies -> identify
4. POS tags are produced
5. Multiple sentences are separated correctly
6. Empty input handling
7. Whitespace-only input handling
8. Non-string input handling
9. Preservation of stop words, negation, and punctuation
"""

import pytest
from base_asag.preprocessing import (
    ProcessedDocument,
    ProcessedSentence,
    TextPreprocessor,
    normalize_text,
)


@pytest.fixture(scope="module")
def preprocessor():
    """Provides a shared TextPreprocessor instance for tests."""
    return TextPreprocessor(model_name="en_core_web_sm")


# 1. Normal sentence processing
def test_normal_sentence_processing(preprocessor):
    """Test standard sentence processing on the primary key reference sentence."""
    text = "A primary key uniquely identifies each record in a table."
    doc = preprocessor.process(text)

    assert isinstance(doc, ProcessedDocument)
    assert doc.sentence_count == 1

    sent = doc.sentences[0]
    assert isinstance(sent, ProcessedSentence)
    assert sent.original_text == text
    assert sent.token_count == 11
    assert sent.tokens[0] == "A"
    assert sent.tokens[-1] == "."
    assert len(sent.lemmas) == sent.token_count
    assert len(sent.pos_tags) == sent.token_count


# 2. Lower/upper-case normalization
def test_case_normalization(preprocessor):
    """Test lower/upper-case normalization with both default and lowercase=True preprocessors."""
    text = "  A PRIMARY KEY  uniquely IDENTIFIES each record.  "

    # Default preserves case in tokens but normalizes whitespace
    doc_default = preprocessor.process(text)
    assert doc_default.normalized_text == "A PRIMARY KEY uniquely IDENTIFIES each record."
    assert "PRIMARY" in doc_default.tokens

    # Lowercase preprocessor normalizes casing
    prep_lower = TextPreprocessor(lowercase=True)
    doc_lower = prep_lower.process(text)
    assert doc_lower.normalized_text == "a primary key uniquely identifies each record."
    assert "primary" in doc_lower.tokens
    assert "primary" in doc_lower.lemmas

    # Direct normalize_text check
    assert normalize_text("  HELLO   WORLD  ", lowercase=True) == "hello world"
    assert normalize_text("  HELLO   WORLD  ", lowercase=False) == "HELLO WORLD"


# 3. Lemmatization of a word such as: identifies -> identify
def test_lemmatization(preprocessor):
    """Test that verbs, plurals, and inflections are properly lemmatized (e.g. identifies -> identify)."""
    text = "A primary key uniquely identifies each record in a table."
    doc = preprocessor.process(text)
    sent = doc.sentences[0]

    # Find the lemma for 'identifies'
    idx_identifies = sent.tokens.index("identifies")
    assert sent.lemmas[idx_identifies].lower() == "identify"

    # Additional inflection check: records -> record, tables -> table
    text_plural = "Keys identify records in tables."
    doc_plural = preprocessor.process(text_plural)
    sent_plural = doc_plural.sentences[0]
    assert "record" in sent_plural.lemmas
    assert "table" in sent_plural.lemmas


# 4. POS tags are produced
def test_pos_tags_produced(preprocessor):
    """Test that valid Universal POS tags and detailed tags are generated for all tokens."""
    text = "A primary key uniquely identifies each record in a table."
    doc = preprocessor.process(text)
    sent = doc.sentences[0]

    assert len(sent.pos_tags) == sent.token_count
    assert len(sent.detailed_pos_tags) == sent.token_count

    # Check that tags are non-empty strings
    for pos, tag in zip(sent.pos_tags, sent.detailed_pos_tags):
        assert isinstance(pos, str) and len(pos) > 0
        assert isinstance(tag, str) and len(tag) > 0

    # Check key expected POS categories exist without overly strict exact matching
    assert "VERB" in sent.pos_tags
    assert "NOUN" in sent.pos_tags
    assert "DET" in sent.pos_tags


# 5. Multiple sentences are separated correctly
def test_multiple_sentences_separated(preprocessor):
    """Test segmentation when an answer contains multiple sentences."""
    text = "A primary key uniquely identifies each record in a table. SQL was developed in the 1970s."
    doc = preprocessor.process(text)

    assert doc.sentence_count == 2
    assert "primary key" in doc.sentences[0].original_text
    assert "SQL was developed" in doc.sentences[1].original_text
    assert doc.sentences[0].tokens[-1] == "."
    assert doc.sentences[1].tokens[-1] == "."


# 6. Empty input handling
def test_empty_input_handling(preprocessor):
    """Test that empty string raises ValueError by default, or returns empty doc if allow_empty=True."""
    with pytest.raises(ValueError, match="Input text cannot be empty"):
        preprocessor.process("")

    # With allow_empty=True, returns empty structure
    empty_doc = preprocessor.process("", allow_empty=True)
    assert empty_doc.sentence_count == 0
    assert empty_doc.tokens == []
    assert empty_doc.lemmas == []


# 7. Whitespace-only input handling
def test_whitespace_only_handling(preprocessor):
    """Test that whitespace-only string raises ValueError by default."""
    with pytest.raises(ValueError, match="Input text cannot be empty"):
        preprocessor.process("   \t\n  \r  ")

    # With allow_empty=True
    empty_doc = preprocessor.process("   \t\n  ", allow_empty=True)
    assert empty_doc.sentence_count == 0
    assert empty_doc.tokens == []


# 8. Non-string input handling
def test_non_string_input_handling(preprocessor):
    """Test that non-string inputs explicitly raise TypeError."""
    invalid_inputs = [None, 123, 45.67, ["some", "tokens"], {"key": "val"}]
    for invalid in invalid_inputs:
        with pytest.raises(TypeError, match="must be a string"):
            preprocessor.process(invalid)

        with pytest.raises(TypeError, match="must be a string"):
            normalize_text(invalid)


# 9. Preservation of stop words, negation, and punctuation
def test_preserves_syntactic_integrity(preprocessor):
    """
    Ensure stop words, negation, and punctuation are strictly preserved
    so downstream dependency parsing in Stage 4 has complete grammatical context.
    """
    text = "A primary key cannot contain NULL values and must not be empty."
    doc = preprocessor.process(text)
    sent = doc.sentences[0]

    # Stop words / determiners preserved
    assert "A" in sent.tokens or "a" in sent.tokens
    assert "and" in sent.tokens

    # Negation preserved
    assert "not" in sent.tokens or "not" in sent.lemmas
    assert any("not" in t.lower() or "n't" in t.lower() for t in sent.tokens)

    # Punctuation preserved
    assert "." in sent.tokens


# 10. process_sentence API check
def test_process_sentence_api(preprocessor):
    """Test process_sentence single-sentence helper and its validation."""
    single_sent = "This is a single valid sentence."
    sent = preprocessor.process_sentence(single_sent)
    assert isinstance(sent, ProcessedSentence)
    assert sent.token_count > 0

    # Multi-sentence input to process_sentence must raise ValueError
    multi_sent = "First sentence. Second sentence."
    with pytest.raises(ValueError, match="Expected exactly 1 sentence"):
        preprocessor.process_sentence(multi_sent)


# 11. Serialization check
def test_to_dict_serialization(preprocessor):
    """Test that ProcessedDocument and ProcessedSentence serialize to dict cleanly."""
    text = "A primary key uniquely identifies each record in a table."
    doc = preprocessor.process(text)
    data = doc.to_dict()

    assert data["sentence_count"] == 1
    assert data["original_text"] == text
    assert len(data["sentences"]) == 1
    assert "tokens_info" in data["sentences"][0]
    assert len(data["sentences"][0]["tokens_info"]) == doc.sentences[0].token_count
