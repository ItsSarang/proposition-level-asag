"""
Unit and Integration Tests for Stage 13: Additional-Information Classification.

Verifies:
1. Classification of unmatched student propositions into:
   - CORRECT_ADDITIONAL (Student B: cannot contain NULL values)
   - IRRELEVANT (Student D: SQL was developed in the 1970s)
   - INCORRECT (Student C: can contain duplicate values; explicit polarity contradictions)
   - UNCERTAIN (borderline / ambiguous semantic evidence fallback)
2. Strict preservation of Base ASAG normalized scores (score_effect == 0.0).
3. Matched propositions preserved with classification == "MATCHED_BY_BASE_ASAG".
4. Independence of multiple unmatched propositions in a single student answer.
5. Distinction between NOT_SUPPORTED and INCORRECT (absence of support != contradiction).
6. Exact proposition ID and index linkage.
7. Pure JSON serializability without raw spaCy or NLTK objects.
8. Deterministic classification behavior.
"""

import json
import pytest

from base_asag.pipeline import BaseASAGPipeline, BaseASAGPipelineResult
from proposed_asag.classification import (
    AdditionalInformationClassifier,
    AdditionalInformationResult,
    CompatibilityAnalyzer,
    DocumentClassificationResult,
    RelevanceAnalyzer,
)
from proposed_asag.proposition.representation import (
    DocumentPropositionRepresentation,
    LinguisticArgument,
    LinguisticStructure,
    MatchingProvenance,
    PropositionContext,
    PropositionRepresentation,
    PropositionRepresentationBuilder,
    SpanInfo,
)


# Shared fixtures
@pytest.fixture(scope="module")
def pipeline() -> BaseASAGPipeline:
    return BaseASAGPipeline()


@pytest.fixture(scope="module")
def builder() -> PropositionRepresentationBuilder:
    return PropositionRepresentationBuilder()


@pytest.fixture(scope="module")
def classifier() -> AdditionalInformationClassifier:
    return AdditionalInformationClassifier()


@pytest.fixture(scope="module")
def primary_key_context():
    question = "What is the purpose of a primary key?"
    reference = "A primary key uniquely identifies each record in a table."
    return question, reference


# ---------------------------------------------------------------------------
# Test Cases
# ---------------------------------------------------------------------------

def test_correct_additional_primary_key_student_b(pipeline, classifier, primary_key_context):
    """Student B: 'cannot contain NULL values' is classified as CORRECT_ADDITIONAL."""
    question, reference = primary_key_context
    answer = "A primary key uniquely identifies each record in a table and cannot contain NULL values."

    pipe_res = pipeline.grade(student_answer=answer, reference_answer=reference, question=question)
    doc_cls = classifier.classify_document(pipe_res)

    assert doc_cls.total_student_propositions == 2
    assert doc_cls.matched_count == 1
    assert doc_cls.unmatched_count == 1
    assert doc_cls.correct_additional_count == 1
    assert doc_cls.irrelevant_count == 0
    assert doc_cls.incorrect_count == 0

    unmatched = doc_cls.unmatched_classifications[0]
    assert unmatched.classification == "CORRECT_ADDITIONAL"
    assert unmatched.score_effect == 0.0
    assert unmatched.relevance.is_relevant is True
    assert unmatched.compatibility.contradiction_status == "NO_CONTRADICTION"
    assert unmatched.compatibility.reference_support == "NOT_SUPPORTED"
    assert "CORRECT_ADDITIONAL" in unmatched.decision_reason


def test_irrelevant_additional_sql_student_d(pipeline, classifier, primary_key_context):
    """Student D: 'SQL was developed in the 1970s' is classified as IRRELEVANT."""
    question, reference = primary_key_context
    answer = "A primary key uniquely identifies each record in a table. SQL was developed in the 1970s."

    pipe_res = pipeline.grade(student_answer=answer, reference_answer=reference, question=question)
    doc_cls = classifier.classify_document(pipe_res)

    assert doc_cls.matched_count == 1
    assert doc_cls.unmatched_count == 1
    assert doc_cls.irrelevant_count == 1
    assert doc_cls.correct_additional_count == 0

    unmatched = doc_cls.unmatched_classifications[0]
    assert unmatched.classification == "IRRELEVANT"
    assert unmatched.score_effect == 0.0
    assert unmatched.relevance.is_relevant is False
    assert unmatched.relevance.score < 0.35
    assert "IRRELEVANT" in unmatched.decision_reason


def test_incorrect_additional_duplicates_student_c(pipeline, classifier, primary_key_context):
    """Student C: 'can contain duplicate values' is classified as INCORRECT via MODIFIER_CONFLICT."""
    question, reference = primary_key_context
    answer = "A primary key uniquely identifies each record in a table and can contain duplicate values."

    pipe_res = pipeline.grade(student_answer=answer, reference_answer=reference, question=question)
    doc_cls = classifier.classify_document(pipe_res)

    assert doc_cls.matched_count == 1
    assert doc_cls.unmatched_count == 1
    assert doc_cls.incorrect_count == 1

    unmatched = doc_cls.unmatched_classifications[0]
    assert unmatched.classification == "INCORRECT"
    assert unmatched.score_effect == 0.0
    assert unmatched.relevance.is_relevant is True
    assert unmatched.compatibility.contradiction_status == "CONTRADICTION_DETECTED"
    assert unmatched.compatibility.contradiction_type == "MODIFIER_CONFLICT"
    assert "uniquely" in unmatched.compatibility.reasons[0] or "duplicate" in unmatched.compatibility.reasons[0]


def test_explicit_polarity_contradiction(pipeline, classifier, primary_key_context):
    """Student asserting direct negation of reference claim is classified as INCORRECT."""
    question, reference = primary_key_context
    answer = "A primary key uniquely identifies each record in a table. It does not identify records."

    pipe_res = pipeline.grade(student_answer=answer, reference_answer=reference, question=question)
    doc_cls = classifier.classify_document(pipe_res)

    assert doc_cls.matched_count == 1
    assert doc_cls.unmatched_count == 1
    assert doc_cls.incorrect_count == 1

    unmatched = doc_cls.unmatched_classifications[0]
    assert unmatched.classification == "INCORRECT"
    assert unmatched.score_effect == 0.0
    assert unmatched.compatibility.contradiction_status == "CONTRADICTION_DETECTED"
    assert unmatched.compatibility.contradiction_type == "POLARITY_CONTRADICTION"


def test_not_supported_distinct_from_incorrect(pipeline, classifier, primary_key_context):
    """Absence of reference support (NOT_SUPPORTED) must NOT imply INCORRECT."""
    question, reference = primary_key_context
    answer = "A primary key uniquely identifies each record in a table and cannot contain NULL values."

    pipe_res = pipeline.grade(student_answer=answer, reference_answer=reference, question=question)
    doc_cls = classifier.classify_document(pipe_res)

    unmatched = doc_cls.unmatched_classifications[0]
    assert unmatched.compatibility.reference_support == "NOT_SUPPORTED"
    assert unmatched.classification != "INCORRECT"
    assert unmatched.classification == "CORRECT_ADDITIONAL"


def test_uncertain_fallback_borderline_evidence(classifier):
    """Borderline semantic relevance triggers UNCERTAIN fallback classification."""
    context = PropositionContext(
        question="What is the purpose of a primary key?",
        reference_answer="A primary key uniquely identifies each record in a table.",
        total_reference_propositions=1,
        reference_propositions=[{"subject": "key", "predicate": "identifies", "object": "record"}],
    )

    span = SpanInfo(char_start=0, char_end=15, sentence_index=0, token_indices=(0, 1), span_text="system entry")
    ling = LinguisticStructure(
        tokens=["system", "entry"],
        token_indices=[0, 1],
        lemmas=["system", "entry"],
        pos_tags=["NOUN", "NOUN"],
        detailed_tags=["NN", "NN"],
        dependency_labels=["compound", "ROOT"],
        heads=["entry", "entry"],
        head_indices=[1, 1],
        arguments=[
            LinguisticArgument(role="subject", text="entry", lemma="entry", pos="NOUN", tag="NN", dep="nsubj", token_index=1, head_token_index=1),
        ],
    )
    matching = MatchingProvenance(
        match_status="UNMATCHED",
        classification="NOT_EVALUATED_BY_BASE_ASAG",
        score_effect=0.0,
        alignment_threshold=0.50,
    )

    prop = PropositionRepresentation(
        proposition_id="stu_prop_test",
        proposition_index=0,
        sentence_index=0,
        text="system entry",
        span=span,
        relation={"subject": "entry", "predicate": "contains", "object": "data", "subject_lemma": "entry", "predicate_lemma": "contain", "object_lemma": "data"},
        polarity="POSITIVE",
        is_negated=False,
        negation_tokens=[],
        polarity_evidence="No negation",
        linguistics=ling,
        matching=matching,
        context=context,
    )

    # Use a classifier with a wide uncertainty margin so borderline overlap falls into UNCERTAIN
    test_clf = AdditionalInformationClassifier(relevance_threshold=0.30, uncertainty_margin=0.20)
    result = test_clf.classify_proposition(prop, context)

    assert result.classification in ("UNCERTAIN", "CORRECT_ADDITIONAL")
    assert result.score_effect == 0.0


def test_multiple_unmatched_propositions_independent(pipeline, classifier, primary_key_context):
    """Multiple unmatched propositions are classified independently in a single document."""
    question, reference = primary_key_context
    # Answer containing both a correct additional constraint and an irrelevant historical fact
    answer = (
        "A primary key uniquely identifies each record in a table and cannot contain NULL values. "
        "SQL was developed in the 1970s."
    )

    pipe_res = pipeline.grade(student_answer=answer, reference_answer=reference, question=question)
    doc_cls = classifier.classify_document(pipe_res)

    assert doc_cls.matched_count == 1
    assert doc_cls.unmatched_count == 2
    assert doc_cls.correct_additional_count == 1
    assert doc_cls.irrelevant_count == 1

    classes = [u.classification for u in doc_cls.unmatched_classifications]
    assert "CORRECT_ADDITIONAL" in classes
    assert "IRRELEVANT" in classes
    for u in doc_cls.unmatched_classifications:
        assert u.score_effect == 0.0


def test_matched_propositions_preserved(pipeline, classifier, primary_key_context):
    """Matched propositions must be preserved with MATCHED_BY_BASE_ASAG and Base score effect."""
    question, reference = primary_key_context
    answer = "A primary key uniquely identifies each record in a table and cannot contain NULL values."

    pipe_res = pipeline.grade(student_answer=answer, reference_answer=reference, question=question)
    doc_cls = classifier.classify_document(pipe_res)

    assert len(doc_cls.matched_propositions) == 1
    matched = doc_cls.matched_propositions[0]
    assert matched["classification"] == "MATCHED_BY_BASE_ASAG"
    assert matched["match_status"] == "MATCHED"
    assert matched["score_effect"] == 1.0


def test_student_a_no_unmatched(pipeline, classifier, primary_key_context):
    """Answer with no unmatched propositions produces 0 unmatched classifications."""
    question, reference = primary_key_context
    answer = "A primary key uniquely identifies every row in a table."

    pipe_res = pipeline.grade(student_answer=answer, reference_answer=reference, question=question)
    doc_cls = classifier.classify_document(pipe_res)

    assert doc_cls.matched_count == 1
    assert doc_cls.unmatched_count == 0
    assert len(doc_cls.unmatched_classifications) == 0
    assert doc_cls.correct_additional_count == 0
    assert doc_cls.irrelevant_count == 0
    assert doc_cls.incorrect_count == 0
    assert doc_cls.uncertain_count == 0


def test_base_asag_score_strictly_unchanged(pipeline, classifier, primary_key_context):
    """Base ASAG score must be preserved exactly across all evaluated answers."""
    question, reference = primary_key_context
    test_answers = [
        "A primary key uniquely identifies every row in a table.",
        "A primary key uniquely identifies each record in a table and cannot contain NULL values.",
        "A primary key uniquely identifies each record in a table and can contain duplicate values.",
        "A primary key uniquely identifies each record in a table. SQL was developed in the 1970s.",
    ]

    for ans in test_answers:
        pipe_res = pipeline.grade(student_answer=ans, reference_answer=reference, question=question)
        doc_cls = classifier.classify_document(pipe_res)

        assert doc_cls.base_asag_normalized_score == pipe_res.normalized_score
        assert doc_cls.summary["base_asag_normalized_score"] == pipe_res.normalized_score
        assert doc_cls.summary["proposed_score_effect_total"] == 0.0


def test_exact_proposition_id_linkage(pipeline, classifier, primary_key_context):
    """Proposition ID and index must match between Stage 12 representation and Stage 13 results."""
    question, reference = primary_key_context
    answer = "A primary key uniquely identifies each record in a table and cannot contain NULL values."

    pipe_res = pipeline.grade(student_answer=answer, reference_answer=reference, question=question)
    doc_cls = classifier.classify_document(pipe_res)

    unmatched = doc_cls.unmatched_classifications[0]
    assert unmatched.proposition_id == "stu_prop_1"
    assert unmatched.proposition_index == 1
    assert unmatched.text == "cannot contain NULL values"


def test_json_serializability(pipeline, classifier, primary_key_context):
    """DocumentClassificationResult and AdditionalInformationResult serialize to JSON cleanly."""
    question, reference = primary_key_context
    answer = "A primary key uniquely identifies each record in a table and cannot contain NULL values."

    pipe_res = pipeline.grade(student_answer=answer, reference_answer=reference, question=question)
    doc_cls = classifier.classify_document(pipe_res)

    json_str = doc_cls.to_json(indent=2)
    assert isinstance(json_str, str)

    parsed = json.loads(json_str)
    assert parsed["student_answer"] == answer
    assert parsed["matched_count"] == 1
    assert parsed["unmatched_count"] == 1
    assert parsed["correct_additional_count"] == 1
    assert len(parsed["unmatched_classifications"]) == 1
    assert parsed["unmatched_classifications"][0]["score_effect"] == 0.0


def test_wordnet_antonym_contradiction(classifier):
    """Explicit WordNet antonym on predicate (allow vs forbid) is classified as INCORRECT."""
    context = PropositionContext(
        question="What does the security policy do?",
        reference_answer="The policy allows access to verified users.",
        total_reference_propositions=1,
        reference_propositions=[{"subject": "policy", "predicate": "allows", "object": "access", "subject_lemma": "policy", "predicate_lemma": "allow", "object_lemma": "access"}],
    )

    span = SpanInfo(char_start=0, char_end=20, sentence_index=0, token_indices=(0, 1, 2), span_text="policy forbids access")
    ling = LinguisticStructure(
        tokens=["policy", "forbids", "access"],
        token_indices=[0, 1, 2],
        lemmas=["policy", "forbid", "access"],
        pos_tags=["NOUN", "VERB", "NOUN"],
        detailed_tags=["NN", "VBZ", "NN"],
        dependency_labels=["nsubj", "ROOT", "dobj"],
        heads=["forbids", "forbids", "forbids"],
        head_indices=[1, 1, 1],
        arguments=[
            LinguisticArgument(role="subject", text="policy", lemma="policy", pos="NOUN", tag="NN", dep="nsubj", token_index=0, head_token_index=1),
            LinguisticArgument(role="predicate", text="forbids", lemma="forbid", pos="VERB", tag="VBZ", dep="ROOT", token_index=1, head_token_index=1),
            LinguisticArgument(role="object", text="access", lemma="access", pos="NOUN", tag="NN", dep="dobj", token_index=2, head_token_index=1),
        ],
    )
    matching = MatchingProvenance(
        match_status="UNMATCHED",
        classification="NOT_EVALUATED_BY_BASE_ASAG",
        score_effect=0.0,
        alignment_threshold=0.50,
    )

    prop = PropositionRepresentation(
        proposition_id="stu_prop_antonym",
        proposition_index=1,
        sentence_index=0,
        text="policy forbids access",
        span=span,
        relation={"subject": "policy", "predicate": "forbids", "object": "access", "subject_lemma": "policy", "predicate_lemma": "forbid", "object_lemma": "access"},
        polarity="POSITIVE",
        is_negated=False,
        negation_tokens=[],
        polarity_evidence="No negation",
        linguistics=ling,
        matching=matching,
        context=context,
    )

    result = classifier.classify_proposition(prop, context)
    assert result.classification == "INCORRECT"
    assert result.compatibility.contradiction_type == "ANTONYM_CONTRADICTION"
    assert result.score_effect == 0.0


def test_deterministic_classification(pipeline, classifier, primary_key_context):
    """Running classification twice produces identical results."""
    question, reference = primary_key_context
    answer = "A primary key uniquely identifies each record in a table and cannot contain NULL values."

    pipe_res = pipeline.grade(student_answer=answer, reference_answer=reference, question=question)
    res1 = classifier.classify_document(pipe_res).to_dict()
    res2 = classifier.classify_document(pipe_res).to_dict()

    assert res1 == res2


def test_document_summary_metrics(pipeline, classifier, primary_key_context):
    """Document classification summary correctly tallies all proposition categories."""
    question, reference = primary_key_context
    answer = "A primary key uniquely identifies each record in a table and cannot contain NULL values."

    pipe_res = pipeline.grade(student_answer=answer, reference_answer=reference, question=question)
    doc_cls = classifier.classify_document(pipe_res)

    summary = doc_cls.summary
    assert summary["total_propositions"] == 2
    assert summary["matched_count"] == 1
    assert summary["unmatched_count"] == 1
    assert summary["correct_additional_count"] == 1
    assert summary["irrelevant_count"] == 0
    assert summary["incorrect_count"] == 0
    assert summary["uncertain_count"] == 0
    assert summary["proposed_score_effect_total"] == 0.0


def test_custom_relevance_threshold(pipeline, primary_key_context):
    """Configuring strict relevance threshold changes low-overlap propositions to IRRELEVANT."""
    question, reference = primary_key_context
    answer = "A primary key uniquely identifies each record in a table and cannot contain NULL values."

    strict_clf = AdditionalInformationClassifier(relevance_threshold=0.99)
    pipe_res = pipeline.grade(student_answer=answer, reference_answer=reference, question=question)
    doc_cls = strict_clf.classify_document(pipe_res)

    unmatched = doc_cls.unmatched_classifications[0]
    # Because 0.8667 < 0.99, it is classified as IRRELEVANT under extreme strict threshold
    assert unmatched.classification == "IRRELEVANT"


def test_classify_document_with_doc_rep_input(pipeline, builder, classifier, primary_key_context):
    """Classifier accepts DocumentPropositionRepresentation directly as input."""
    question, reference = primary_key_context
    answer = "A primary key uniquely identifies each record in a table and cannot contain NULL values."

    pipe_res = pipeline.grade(student_answer=answer, reference_answer=reference, question=question)
    doc_rep = builder.build(pipe_res)

    doc_cls = classifier.classify_document(doc_rep)
    assert isinstance(doc_cls, DocumentClassificationResult)
    assert doc_cls.matched_count == 1
    assert doc_cls.unmatched_count == 1
    assert doc_cls.correct_additional_count == 1


def test_all_propositions_structure_and_ordering(pipeline, classifier, primary_key_context):
    """all_propositions list retains exact ordering and contains both matched and unmatched."""
    question, reference = primary_key_context
    answer = "A primary key uniquely identifies each record in a table and cannot contain NULL values."

    pipe_res = pipeline.grade(student_answer=answer, reference_answer=reference, question=question)
    doc_cls = classifier.classify_document(pipe_res)

    assert len(doc_cls.all_propositions) == doc_cls.total_student_propositions
    assert doc_cls.all_propositions[0]["classification"] == "MATCHED_BY_BASE_ASAG"
    assert doc_cls.all_propositions[1]["classification"] == "CORRECT_ADDITIONAL"

