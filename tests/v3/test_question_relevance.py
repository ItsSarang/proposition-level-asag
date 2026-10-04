"""
Unit tests for Question-Aware Relevance Analysis (Phase 2).
"""

import pytest
from base_asag.representation.hybrid import (
    Modality,
    Polarity,
    PropositionType,
    RobustProposition,
)
from proposed_asag.relevance.question_relevance import (
    QuestionAnalyzer,
    QuestionAwareRelevanceAnalyzer,
    RelevanceEvidence,
)


@pytest.fixture(scope="module")
def analyzer():
    return QuestionAwareRelevanceAnalyzer(relevance_threshold=0.35)


@pytest.fixture(scope="module")
def q_analyzer():
    return QuestionAnalyzer()


def test_question_type_detection(q_analyzer):
    """Test heuristic question type extraction across typical assessment queries."""
    assert q_analyzer.analyze("What is the difference between while and do-while?").question_type == "DIFFERENCE"
    assert q_analyzer.analyze("What are the similarities between iteration and recursion?").question_type == "SIMILARITY"
    assert q_analyzer.analyze("Where are variables declared in a C++ program?").question_type == "LOCATION_OR_SCOPE"
    assert q_analyzer.analyze("How do you delete a node from a binary search tree?").question_type == "MECHANISM_OR_PROCESS"
    assert q_analyzer.analyze("What is the purpose of a primary key?").question_type == "PURPOSE_OR_ADVANTAGE"


def test_question_focus_terms(q_analyzer):
    """Test extraction of core semantic concepts excluding stopwords."""
    analysis = q_analyzer.analyze("What is the purpose of a primary key?")
    assert "primary" in analysis.focus_lemmas or "primary" in analysis.focus_terms
    assert "key" in analysis.focus_lemmas or "key" in analysis.focus_terms
    assert "what" not in analysis.focus_lemmas
    assert "is" not in analysis.focus_lemmas


def test_relevant_proposition(analyzer):
    """A proposition discussing primary keys and null values is relevant to a primary key question."""
    prop = RobustProposition(
        subject="key",
        predicate="contain",
        object="value",
        subject_lemma="key",
        predicate_lemma="contain",
        object_lemma="value",
        representation_type=PropositionType.TRIPLE,
        polarity=Polarity.NEGATIVE,
        modality=Modality.ASSERTED,
        source_text="cannot contain null values",
        char_start=0,
        char_end=25,
        sentence_index=0,
        token_indices=(0, 1, 2),
        dependency_evidence=("nsubj", "dobj"),
        properties={"property": "null"},
    )
    question = "What is the purpose of a primary key?"
    reference = "A primary key uniquely identifies each record in a table."

    evidence = analyzer.evaluate(prop, question, reference)
    assert evidence.is_relevant is True
    assert evidence.evidence_strength >= 0.35
    assert len(evidence.lexical_evidence["context_concept_matches"]) >= 1


def test_irrelevant_proposition(analyzer):
    """A proposition discussing SQL history is irrelevant to a primary key question."""
    prop = RobustProposition(
        subject="SQL",
        predicate="develop",
        object="system",
        subject_lemma="sql",
        predicate_lemma="develop",
        object_lemma="system",
        representation_type=PropositionType.TRIPLE,
        polarity=Polarity.POSITIVE,
        modality=Modality.ASSERTED,
        source_text="SQL was developed in the 1970s",
        char_start=0,
        char_end=30,
        sentence_index=1,
        token_indices=(0, 1, 2),
        dependency_evidence=("nsubjpass", "pobj"),
    )
    question = "What is the purpose of a primary key?"
    reference = "A primary key uniquely identifies each record in a table."

    evidence = analyzer.evaluate(prop, question, reference)
    assert evidence.is_relevant is False
    assert evidence.evidence_strength < 0.35


def test_evidence_strength_bounds(analyzer):
    """Test that evidence strength is strictly bounded in [0.0, 1.0]."""
    prop = RobustProposition(
        subject="compiler",
        predicate="convert",
        object="code",
        subject_lemma="compiler",
        predicate_lemma="convert",
        object_lemma="code",
        representation_type=PropositionType.TRIPLE,
        polarity=Polarity.POSITIVE,
        modality=Modality.ASSERTED,
        source_text="compiler converts code",
        char_start=0,
        char_end=20,
        sentence_index=0,
        token_indices=(0, 1, 2),
        dependency_evidence=("nsubj", "dobj"),
    )
    evidence = analyzer.evaluate(prop, "What is a compiler?", "A compiler converts source code.")
    assert 0.0 <= evidence.evidence_strength <= 1.0
    assert 0.0 <= evidence.concept_overlap <= 1.0
    assert 0.0 <= evidence.predicate_relevance <= 1.0


def test_relevance_serialization(analyzer):
    """Test that RelevanceEvidence serializes to dict properly."""
    prop = RobustProposition(
        subject="loop",
        predicate="execute",
        object=None,
        subject_lemma="loop",
        predicate_lemma="execute",
        object_lemma=None,
        representation_type=PropositionType.TRIPLE,
        polarity=Polarity.POSITIVE,
        modality=Modality.ASSERTED,
        source_text="loop executes",
        char_start=0,
        char_end=13,
        sentence_index=0,
        token_indices=(0, 1),
        dependency_evidence=("nsubj",),
    )
    evidence = analyzer.evaluate(prop, "How does a while loop work?")
    d = evidence.to_dict()
    assert isinstance(d, dict)
    assert "evidence_strength" in d
    assert "is_relevant" in d
    assert "evidence_explanation" in d
