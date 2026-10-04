"""
Unit tests for Robust Hybrid Proposition Representation (Phase 1 & Phase 6).
"""

import pytest
from base_asag.dependency.parser import DependencyParser
from base_asag.representation.hybrid import (
    Modality,
    Polarity,
    PropositionType,
    RobustProposition,
    RobustPropositionExtractor,
)


@pytest.fixture(scope="module")
def parser():
    return DependencyParser(model_name="en_core_web_sm")


@pytest.fixture(scope="module")
def extractor():
    return RobustPropositionExtractor()


def test_normal_spo(parser, extractor):
    """Test standard clausal S-P-O extraction."""
    parsed = parser.parse_document("A compiler converts source code into machine code.")
    props = extractor.extract_document(parsed)
    assert len(props) >= 1
    p = props[0]
    assert p.representation_type == PropositionType.TRIPLE
    assert p.subject.lower() == "compiler"
    assert p.predicate.lower() == "converts"
    assert "code" in p.object.lower()
    assert p.polarity == Polarity.POSITIVE
    assert p.modality == Modality.ASSERTED
    assert p.char_start >= 0
    assert p.char_end > p.char_start


def test_infinitive_argument_structure(parser, extractor):
    """Test infinitive fragment reference (e.g. Q 1.1: 'To simulate the behaviour...')."""
    parsed = parser.parse_document("To simulate the behaviour of software.")
    props = extractor.extract_document(parsed)
    assert len(props) >= 1
    p = props[0]
    assert p.representation_type == PropositionType.ARGUMENT_STRUCTURE
    assert p.predicate_lemma == "simulate"
    assert p.object_lemma == "behaviour"
    assert p.subject is None


def test_nominal_coordination_list(parser, extractor):
    """Test nominal coordination fragment (e.g. Q 1.3: 'Abstraction and reusability.')."""
    parsed = parser.parse_document("Abstraction and reusability.")
    props = extractor.extract_document(parsed)
    assert len(props) >= 1
    p = props[0]
    assert p.representation_type == PropositionType.RELATIONAL_FRAGMENT
    assert p.subject_lemma == "abstraction"
    assert p.object_lemma == "reusability"
    assert p.predicate_lemma == "and"


def test_prepositional_fragment(parser, extractor):
    """Test prepositional fragment (e.g. Q 1.4: 'At the main function.')."""
    parsed = parser.parse_document("At the main function.")
    props = extractor.extract_document(parsed)
    assert len(props) >= 1
    p = props[0]
    assert p.representation_type == PropositionType.RELATIONAL_FRAGMENT
    assert p.predicate_lemma == "at"
    assert p.object_lemma == "function"


def test_property_modifier_fragment(parser, extractor):
    """Test noun property structure (e.g. Q 3.2: 'File scope.')."""
    parsed = parser.parse_document("File scope.")
    props = extractor.extract_document(parsed)
    assert len(props) >= 1
    p = props[0]
    assert p.representation_type == PropositionType.PROPERTY
    assert p.subject_lemma == "scope"
    assert p.object_lemma == "file"


def test_passive_voice(parser, extractor):
    """Test passive voice extraction."""
    parsed = parser.parse_document("The function was executed by the operating system.")
    props = extractor.extract_document(parsed)
    assert len(props) >= 1
    p = props[0]
    assert p.representation_type == PropositionType.TRIPLE
    assert p.predicate_lemma == "execute"
    assert p.polarity == Polarity.POSITIVE


def test_negation_polarity(parser, extractor):
    """Test negative polarity detection."""
    parsed = parser.parse_document("A primary key cannot contain null values.")
    props = extractor.extract_document(parsed)
    assert len(props) >= 1
    p = props[0]
    assert p.polarity == Polarity.NEGATIVE


def test_modality_detection(parser, extractor):
    """Test modal auxiliary detection."""
    parsed_possible = parser.parse("The program may terminate early.")
    props_poss = extractor.extract_document(parsed_possible)
    assert props_poss[0].modality == Modality.POSSIBLE

    parsed_necessary = parser.parse("The programmer must declare variables.")
    props_nec = extractor.extract_document(parsed_necessary)
    assert props_nec[0].modality == Modality.NECESSARY


def test_deduplication(parser, extractor):
    """Test that identical propositions in a document are deduplicated."""
    parsed = parser.parse_document("The loop executes once. The loop executes once.")
    props = extractor.extract_document(parsed)
    assert len(props) == 1


def test_json_serialization(parser, extractor):
    """Test that RobustProposition serializes to dictionary cleanly."""
    parsed = parser.parse_document("A compiler converts code.")
    props = extractor.extract_document(parsed)
    assert len(props) >= 1
    d = props[0].to_dict()
    assert isinstance(d, dict)
    assert d["representation_type"] == "TRIPLE"
    assert d["polarity"] == "POSITIVE"
    assert d["modality"] == "ASSERTED"
    assert "char_start" in d
    assert "token_indices" in d


def test_conjoined_clause_local_span(parser, extractor):
    """
    Regression test for Issue 2:
    Ensure coordinated/conjoined clauses sharing an inherited subject receive
    a linguistically appropriate clause-local character span instead of
    spanning the entire sentence.
    """
    text1 = "A primary key uniquely identifies each record in a table and can contain duplicate values."
    parsed1 = parser.parse_document(text1)
    props1 = extractor.extract_document(parsed1)

    assert len(props1) == 2
    # First proposition: core assertion
    p0 = props1[0]
    assert p0.subject_lemma == "key"
    assert p0.predicate_lemma == "identify"
    assert p0.object_lemma == "record"
    assert p0.source_text == "key uniquely identifies each record"

    # Second proposition: conjoined clause
    p1 = props1[1]
    # Relation itself MUST remain (key, contain, values)
    assert p1.subject == "key"
    assert p1.predicate == "contain"
    assert p1.object == "values"
    assert p1.subject_lemma == "key"
    assert p1.predicate_lemma == "contain"
    assert p1.object_lemma == "value"
    # Span must be clause-local
    assert p1.source_text == "can contain duplicate values"
    assert text1[p1.char_start:p1.char_end] == "can contain duplicate values"

    # Also verify conjoined negative clause
    text2 = "A primary key uniquely identifies each record in a table and cannot contain NULL values."
    parsed2 = parser.parse_document(text2)
    props2 = extractor.extract_document(parsed2)
    assert len(props2) == 2
    p2 = props2[1]
    assert p2.subject == "key"
    assert p2.predicate == "contain"
    assert p2.object == "values"
    assert p2.polarity == Polarity.NEGATIVE
    assert p2.source_text == "cannot contain NULL values"
    assert text2[p2.char_start:p2.char_end] == "cannot contain NULL values"


def test_polarity_preserving_deduplication(parser, extractor):
    """
    Regression test for Issue 1:
    Ensure positive and negative propositions with identical lemmas never
    silently collapse into one proposition during deduplication, regardless of order.
    """
    # 1. Positive followed by negative
    text_pos_neg = "A compiler translates source code into machine code, and a compiler does not translate source code into machine code."
    doc_pn = parser.parse_document(text_pos_neg)
    props_pn = extractor.extract_document(doc_pn)
    assert len(props_pn) == 2
    polarities_pn = [p.polarity for p in props_pn]
    assert Polarity.POSITIVE in polarities_pn
    assert Polarity.NEGATIVE in polarities_pn
    for p in props_pn:
        assert p.subject_lemma == "compiler"
        assert p.predicate_lemma == "translate"
        assert p.object_lemma == "code"

    # 2. Negative followed by positive
    text_neg_pos = "A compiler does not translate source code into machine code, and a compiler translates source code into machine code."
    doc_np = parser.parse_document(text_neg_pos)
    props_np = extractor.extract_document(doc_np)
    assert len(props_np) == 2
    polarities_np = [p.polarity for p in props_np]
    assert Polarity.POSITIVE in polarities_np
    assert Polarity.NEGATIVE in polarities_np


def test_copular_adjectival_and_comparative_preservation(parser, extractor):
    """
    Regression test for Issue 2:
    Ensure adjectival complements (acomp) and comparative prepositional complements
    are preserved rather than collapsing into (subject, is, None).
    """
    # 1. Comparative copular: "smaller than parent"
    text1 = "The left child is smaller than the parent."
    doc1 = parser.parse_document(text1)
    props1 = extractor.extract_document(doc1)
    assert len(props1) == 1
    p1 = props1[0]
    assert p1.subject_lemma == "child"
    assert p1.predicate_lemma == "be"
    assert p1.object == "smaller"
    assert p1.object_lemma == "small"
    assert p1.properties.get("comparative_target") == "parent"
    assert "smaller than the parent" in p1.source_text

    # 2. Comparative copular: "larger than parent"
    text2 = "The left child is larger than the parent."
    doc2 = parser.parse_document(text2)
    props2 = extractor.extract_document(doc2)
    assert len(props2) == 1
    p2 = props2[0]
    assert p2.subject_lemma == "child"
    assert p2.predicate_lemma == "be"
    assert p2.object == "larger"
    assert p2.object_lemma == "large"
    assert p2.properties.get("comparative_target") == "parent"

    # 3. Simple copular adjectives across multiple domains
    copular_examples = [
        ("The stack is empty.", "stack", "empty", "empty"),
        ("The queue is full.", "queue", "full", "full"),
        ("The variable is global.", "variable", "global", "global"),
    ]
    for text, exp_subj, exp_obj, exp_obj_lemma in copular_examples:
        doc = parser.parse_document(text)
        props = extractor.extract_document(doc)
        assert len(props) == 1, f"Failed extraction for: {text}"
        p = props[0]
        assert p.subject_lemma == exp_subj
        assert p.predicate_lemma == "be"
        assert p.object == exp_obj
        assert p.object_lemma == exp_obj_lemma


