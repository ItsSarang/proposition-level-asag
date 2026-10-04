"""
Tests for Stage 8 Proposition-Level Textual Entailment.

Verifies:
1. Identical positive propositions evaluate to ENTAILS.
2. Identical proposition with inflected wording (lemmas) evaluates to ENTAILS.
3. Explicit student negation evaluates to CONTRADICTS.
4. Explicit reference negation with positive student evaluates to CONTRADICTS.
5. Both reference and student negated evaluates to ENTAILS.
6. Weak semantic similarity (record vs row in WordNet) evaluates to UNCERTAIN.
7. Distant/weak predicate alignment evaluates to UNCERTAIN.
8. Intransitive (SP) relations evaluate correctly.
9. Transitive (SPO) relations evaluate correctly.
10. Passive voice constructions evaluate correctly.
11. Conjoined clauses preserve extra relations unclassified.
12. Preservation of Stage 6/7 diagnostic slot evidence.
13. Absence of final grading or scoring logic.
14. Absence of additional-information classification.
15. Deterministic and reproducible evaluation.
16. Input validation and serialization.
"""

import pytest

from base_asag.dependency import DependencyParser, DependencyTripleExtractor
from base_asag.entailment import (
    EntailmentResult,
    PolarityDetector,
    PolarityInfo,
    PropositionalEntailmentAnalyzer,
)
from base_asag.matching import MatchedRelation, TripleMatcher


@pytest.fixture(scope="module")
def parser():
    """Provides a shared DependencyParser instance."""
    return DependencyParser(model_name="en_core_web_sm")


@pytest.fixture(scope="module")
def extractor():
    """Provides a shared DependencyTripleExtractor instance."""
    return DependencyTripleExtractor()


@pytest.fixture(scope="module")
def matcher():
    """Provides a shared TripleMatcher instance."""
    return TripleMatcher()


@pytest.fixture(scope="module")
def analyzer():
    """Provides a standard PropositionalEntailmentAnalyzer instance."""
    return PropositionalEntailmentAnalyzer()


# 1. Identical positive propositions
def test_identical_positive_propositions_entail(parser, extractor, matcher, analyzer):
    """Verify identical positive propositions produce ENTAILS with high confidence."""
    ref_text = "A primary key uniquely identifies each record in a table."
    stu_text = "A primary key uniquely identifies each record in a table."

    ref_doc = parser.parse(ref_text)
    stu_doc = parser.parse(stu_text)

    matching_res = matcher.match(
        extractor.extract_document(ref_doc),
        extractor.extract_document(stu_doc),
    )
    assert matching_res.matched_count == 1

    entailment_results = analyzer.evaluate_matching_result(
        matching_res, ref_doc, stu_doc
    )
    assert len(entailment_results) == 1

    res = entailment_results[0]
    assert res.relation == "ENTAILS"
    assert res.confidence == 1.0
    assert res.reference_polarity == "POSITIVE"
    assert res.student_polarity == "POSITIVE"
    assert any("Polarity is compatible" in r for r in res.reasons)


# 2. Inflected wording (lemma match)
def test_inflected_propositions_entail(parser, extractor, matcher, analyzer):
    """Verify inflected wording with identical lemmas produces ENTAILS."""
    ref_text = "Primary keys uniquely identify records in tables."
    stu_text = "A primary key uniquely identified each record in a table."

    ref_doc = parser.parse(ref_text)
    stu_doc = parser.parse(stu_text)

    matching_res = matcher.match(
        extractor.extract_document(ref_doc),
        extractor.extract_document(stu_doc),
    )
    assert matching_res.matched_count == 1

    res = analyzer.evaluate(matching_res.matched_relations[0], ref_doc.sentences[0], stu_doc.sentences[0])
    assert res.relation == "ENTAILS"
    assert res.reference_polarity == "POSITIVE"
    assert res.student_polarity == "POSITIVE"
    assert res.confidence == 1.0


# 3. Explicit student negation
def test_explicit_student_negation_contradicts(parser, extractor, matcher, analyzer):
    """Verify positive reference + negated student produces CONTRADICTS."""
    ref_text = "A primary key uniquely identifies each record in a table."
    stu_text = "A primary key does not uniquely identify each record in a table."

    ref_doc = parser.parse(ref_text)
    stu_doc = parser.parse(stu_text)

    matching_res = matcher.match(
        extractor.extract_document(ref_doc),
        extractor.extract_document(stu_doc),
    )
    assert matching_res.matched_count == 1

    res = analyzer.evaluate(matching_res.matched_relations[0], ref_doc.sentences[0], stu_doc.sentences[0])
    assert res.relation == "CONTRADICTS"
    assert res.reference_polarity == "POSITIVE"
    assert res.student_polarity == "NEGATED"
    assert res.confidence == 1.0
    assert any("explicit negation" in r.lower() for r in res.reasons)


# 4. Explicit reference negation with positive student
def test_explicit_reference_negation_contradicts(parser, extractor, matcher, analyzer):
    """Verify negated reference + positive student produces CONTRADICTS."""
    ref_text = "A primary key does not uniquely identify each record in a table."
    stu_text = "A primary key uniquely identifies each record in a table."

    ref_doc = parser.parse(ref_text)
    stu_doc = parser.parse(stu_text)

    matching_res = matcher.match(
        extractor.extract_document(ref_doc),
        extractor.extract_document(stu_doc),
    )
    assert matching_res.matched_count == 1

    res = analyzer.evaluate(matching_res.matched_relations[0], ref_doc.sentences[0], stu_doc.sentences[0])
    assert res.relation == "CONTRADICTS"
    assert res.reference_polarity == "NEGATED"
    assert res.student_polarity == "POSITIVE"
    assert any("reference proposition contains explicit negation" in r.lower() for r in res.reasons)


# 5. Both reference and student negated
def test_both_negated_propositions_entail(parser, extractor, matcher, analyzer):
    """Verify both propositions negated produces compatible polarity and ENTAILS."""
    ref_text = "A primary key does not uniquely identify each record in a table."
    stu_text = "A primary key cannot uniquely identify each record in a table."

    ref_doc = parser.parse(ref_text)
    stu_doc = parser.parse(stu_text)

    matching_res = matcher.match(
        extractor.extract_document(ref_doc),
        extractor.extract_document(stu_doc),
    )
    assert matching_res.matched_count == 1

    res = analyzer.evaluate(matching_res.matched_relations[0], ref_doc.sentences[0], stu_doc.sentences[0])
    assert res.relation == "ENTAILS"
    assert res.reference_polarity == "NEGATED"
    assert res.student_polarity == "NEGATED"
    assert any("both propositions are NEGATED" in r for r in res.reasons)


# 6. Weak semantic similarity (record vs row) produces UNCERTAIN
def test_weak_semantic_similarity_produces_uncertain(parser, extractor, matcher, analyzer):
    """Verify general WordNet score of record vs row (~0.125) produces UNCERTAIN under standard thresholds."""
    ref_text = "A primary key uniquely identifies each record in a table."
    stu_text = "A primary key uniquely identifies every row in a table."

    ref_doc = parser.parse(ref_text)
    stu_doc = parser.parse(stu_text)

    matching_res = matcher.match(
        extractor.extract_document(ref_doc),
        extractor.extract_document(stu_doc),
    )
    assert matching_res.matched_count == 1

    res = analyzer.evaluate(matching_res.matched_relations[0], ref_doc.sentences[0], stu_doc.sentences[0])
    # Under min_slot_similarity=0.50, object similarity 0.125 fails slot threshold -> UNCERTAIN
    assert res.relation == "UNCERTAIN"
    assert res.reference_polarity == "POSITIVE"
    assert res.student_polarity == "POSITIVE"
    assert any("Object similarity" in r and "below slot threshold" in r for r in res.reasons)


# 7. Uncertain proposition with weak predicate
def test_weak_predicate_produces_uncertain(parser, extractor, matcher, analyzer):
    """Verify weak predicate alignment produces UNCERTAIN."""
    ref_text = "A primary key uniquely identifies each record in a table."
    stu_text = "A primary key is associated with records in a table."

    ref_doc = parser.parse(ref_text)
    stu_doc = parser.parse(stu_text)

    matching_res = matcher.match(
        extractor.extract_document(ref_doc),
        extractor.extract_document(stu_doc),
    )
    if matching_res.matched_count > 0:
        res = analyzer.evaluate(matching_res.matched_relations[0], ref_doc.sentences[0], stu_doc.sentences[0])
        assert res.relation == "UNCERTAIN"
        assert any("Predicate similarity" in r or "triple score" in r for r in res.reasons)


# 8. Intransitive (SP) relations
def test_intransitive_sp_relation_entailment(parser, extractor, matcher, analyzer):
    """Verify SP relations lacking objects evaluate correctly without object errors."""
    ref_text = "The background process terminates."
    stu_text = "The background process terminates."

    ref_doc = parser.parse(ref_text)
    stu_doc = parser.parse(stu_text)

    matching_res = matcher.match(
        extractor.extract_document(ref_doc),
        extractor.extract_document(stu_doc),
    )
    assert matching_res.matched_count == 1

    res = analyzer.evaluate(matching_res.matched_relations[0], ref_doc.sentences[0], stu_doc.sentences[0])
    assert res.relation == "ENTAILS"
    assert res.object_evidence is None
    assert any("no object slot required" in r for r in res.reasons)


# 9. Transitive (SPO) relations
def test_transitive_spo_relation_entailment(parser, extractor, matcher, analyzer):
    """Verify SPO relations evaluate all three slots."""
    ref_text = "Users execute queries."
    stu_text = "Users execute queries."

    ref_doc = parser.parse(ref_text)
    stu_doc = parser.parse(stu_text)

    matching_res = matcher.match(
        extractor.extract_document(ref_doc),
        extractor.extract_document(stu_doc),
    )
    assert matching_res.matched_count == 1

    res = analyzer.evaluate(matching_res.matched_relations[0], ref_doc.sentences[0], stu_doc.sentences[0])
    assert res.relation == "ENTAILS"
    assert res.object_evidence is not None


# 10. Passive voice constructions
def test_passive_voice_entailment(parser, extractor, matcher, analyzer):
    """Verify passive and active forms of the same proposition evaluate to ENTAILS."""
    ref_text = "A primary key uniquely identifies each record in a table."
    stu_text = "Each record in a table is uniquely identified by a primary key."

    ref_doc = parser.parse(ref_text)
    stu_doc = parser.parse(stu_text)

    matching_res = matcher.match(
        extractor.extract_document(ref_doc),
        extractor.extract_document(stu_doc),
    )
    assert matching_res.matched_count == 1

    res = analyzer.evaluate(matching_res.matched_relations[0], ref_doc.sentences[0], stu_doc.sentences[0])
    assert res.relation == "ENTAILS"
    assert res.reference_polarity == "POSITIVE"
    assert res.student_polarity == "POSITIVE"


# 11. Conjunction handling (Student B)
def test_conjunction_preserves_unmatched_unclassified(parser, extractor, matcher, analyzer):
    """Verify matched relation entails while extra conjoined relation remains untouched."""
    ref_text = "A primary key uniquely identifies each record in a table."
    stu_text = "A primary key uniquely identifies each record in a table and cannot contain NULL values."

    ref_doc = parser.parse(ref_text)
    stu_doc = parser.parse(stu_text)

    matching_res = matcher.match(
        extractor.extract_document(ref_doc),
        extractor.extract_document(stu_doc),
    )
    assert matching_res.matched_count == 1
    assert matching_res.unmatched_student_count == 1

    # Evaluate the matched relation
    entailment_list = analyzer.evaluate_matching_result(matching_res, ref_doc, stu_doc)
    assert len(entailment_list) == 1
    assert entailment_list[0].relation == "ENTAILS"

    # Verify that the unmatched student relation was NOT processed or classified by Stage 8
    unmatched_stu = matching_res.unmatched_student_relations[0]
    assert not hasattr(unmatched_stu, "classification")
    assert not hasattr(unmatched_stu, "is_correct")
    assert not hasattr(unmatched_stu, "is_irrelevant")


# 12. Preservation of Stage 7 slot evidence
def test_preservation_of_stage7_evidence(parser, extractor, matcher, analyzer):
    """Verify diagnostic Stage 6/7 evidence is carried in EntailmentResult."""
    ref_text = "A primary key uniquely identifies each record in a table."
    stu_text = "A primary key uniquely identifies each record in a table."

    ref_doc = parser.parse(ref_text)
    stu_doc = parser.parse(stu_text)

    matching_res = matcher.match(
        extractor.extract_document(ref_doc),
        extractor.extract_document(stu_doc),
    )
    res = analyzer.evaluate(matching_res.matched_relations[0], ref_doc.sentences[0], stu_doc.sentences[0])

    assert "exact_match" in res.subject_evidence
    assert res.subject_evidence["exact_match"] is True
    assert "exact_match" in res.predicate_evidence
    assert res.predicate_evidence["exact_match"] is True


# 13. Absence of final grading or scoring
def test_no_final_grading_in_stage_8(analyzer):
    """Verify Stage 8 has no grading, scoring, or grade prediction methods."""
    assert not hasattr(analyzer, "grade")
    assert not hasattr(analyzer, "compute_final_score")
    assert not hasattr(analyzer, "predict_score")
    assert not hasattr(analyzer, "assign_grade")


# 14. Absence of additional-information classification
def test_no_additional_information_classification_in_stage_8(analyzer):
    """Verify Stage 8 does not classify unmatched propositions."""
    assert not hasattr(analyzer, "classify_additional_information")
    assert not hasattr(analyzer, "classify_unmatched")


# 15. Deterministic and reproducible evaluation
def test_deterministic_results(parser, extractor, matcher, analyzer):
    """Verify identical inputs yield identical outputs across multiple evaluations."""
    ref_text = "A primary key uniquely identifies each record in a table."
    stu_text = "A primary key does not uniquely identify each record in a table."

    ref_doc = parser.parse(ref_text)
    stu_doc = parser.parse(stu_text)

    matching_res = matcher.match(
        extractor.extract_document(ref_doc),
        extractor.extract_document(stu_doc),
    )
    matched = matching_res.matched_relations[0]

    res1 = analyzer.evaluate(matched, ref_doc.sentences[0], stu_doc.sentences[0])
    res2 = analyzer.evaluate(matched, ref_doc.sentences[0], stu_doc.sentences[0])

    assert res1.relation == res2.relation
    assert res1.confidence == res2.confidence
    assert res1.reasons == res2.reasons


# 16. Serialization and input validation
def test_serialization_and_validation(parser, extractor, matcher, analyzer):
    """Verify to_dict() produces complete dictionaries and invalid inputs raise exceptions."""
    ref_text = "A primary key uniquely identifies each record in a table."
    stu_text = "A primary key uniquely identifies each record in a table."

    ref_doc = parser.parse(ref_text)
    stu_doc = parser.parse(stu_text)

    matching_res = matcher.match(
        extractor.extract_document(ref_doc),
        extractor.extract_document(stu_doc),
    )
    res = analyzer.evaluate(matching_res.matched_relations[0], ref_doc.sentences[0], stu_doc.sentences[0])
    data = res.to_dict()

    expected_keys = {
        "reference_relation",
        "student_relation",
        "relation",
        "confidence",
        "reference_polarity",
        "student_polarity",
        "subject_evidence",
        "predicate_evidence",
        "object_evidence",
        "triple_score",
        "reasons",
        "reference_polarity_info",
        "student_polarity_info",
    }
    assert expected_keys.issubset(data.keys())

    # Invalid thresholds
    with pytest.raises(ValueError):
        PropositionalEntailmentAnalyzer(entailment_threshold=1.5)

    with pytest.raises(ValueError):
        PropositionalEntailmentAnalyzer(min_slot_similarity=-0.2)

    with pytest.raises(TypeError):
        analyzer.evaluate("not_a_matched_relation")
