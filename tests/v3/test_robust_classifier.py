"""
Unit tests for Robust Additional-Information Classifier (Phase 7).
"""

import pytest
from base_asag.representation.hybrid import (
    Modality,
    Polarity,
    PropositionType,
    RobustProposition,
)
from proposed_asag.classification.robust_classifier import (
    AdditionalInfoClass,
    RobustAdditionalInfoClassifier,
)


@pytest.fixture(scope="module")
def classifier():
    return RobustAdditionalInfoClassifier()


def make_prop(subj, pred, obj, polarity=Polarity.POSITIVE, text=""):
    return RobustProposition(
        subject=subj,
        predicate=pred,
        object=obj,
        subject_lemma=subj.lower() if subj else None,
        predicate_lemma=pred.lower() if pred else "",
        object_lemma=obj.lower() if obj else None,
        representation_type=PropositionType.TRIPLE,
        polarity=polarity,
        modality=Modality.ASSERTED,
        source_text=text or f"{subj} {pred} {obj}",
        char_start=0,
        char_end=len(text) if text else 10,
        sentence_index=0,
        token_indices=(0, 1, 2),
        dependency_evidence=("nsubj", "dobj"),
    )


def test_correct_additional_classification(classifier):
    """A relevant, non-contradictory elaboration is classified as CORRECT_ADDITIONAL."""
    question = "What is the purpose of a primary key?"
    reference = "A primary key uniquely identifies each record in a table."
    ref_props = [make_prop("key", "identify", "record", text="primary key uniquely identifies records")]

    # Student additional proposition: "cannot contain null values"
    extra_prop = make_prop("key", "contain", "value", polarity=Polarity.NEGATIVE, text="primary key cannot contain null values")

    res = classifier.classify_propositions(
        question=question,
        reference_answer=reference,
        student_answer="A primary key uniquely identifies records and cannot contain null values.",
        unmatched_student_props=[extra_prop],
        reference_props=ref_props,
    )

    assert len(res.classified_propositions) == 1
    cp = res.classified_propositions[0]
    assert cp.classification == AdditionalInfoClass.CORRECT_ADDITIONAL
    assert cp.score_effect == 0.0


def test_irrelevant_classification(classifier):
    """An off-topic statement is classified as IRRELEVANT."""
    question = "What is the purpose of a primary key?"
    reference = "A primary key uniquely identifies each record in a table."
    ref_props = [make_prop("key", "identify", "record")]

    extra_prop = make_prop("sql", "develop", "system", text="SQL was developed in 1970 by IBM")

    res = classifier.classify_propositions(
        question=question,
        reference_answer=reference,
        student_answer="SQL was developed in 1970",
        unmatched_student_props=[extra_prop],
        reference_props=ref_props,
    )

    cp = res.classified_propositions[0]
    assert cp.classification == AdditionalInfoClass.IRRELEVANT
    assert cp.score_effect == 0.0


def test_incorrect_classification(classifier):
    """A proposition introducing a contradictory property is classified as INCORRECT."""
    question = "What is the purpose of a primary key?"
    reference = "A primary key uniquely identifies each record in a table."
    ref_props = [make_prop("key", "identify", "record", text="primary key uniquely identifies records")]

    # Student additional proposition: "can contain duplicate values"
    extra_prop = make_prop("key", "contain", "duplicate", text="primary keys can contain duplicate values")

    res = classifier.classify_propositions(
        question=question,
        reference_answer=reference,
        student_answer="primary keys can contain duplicate values",
        unmatched_student_props=[extra_prop],
        reference_props=ref_props,
    )

    cp = res.classified_propositions[0]
    assert cp.classification == AdditionalInfoClass.INCORRECT
    assert cp.score_effect == 0.0


def test_matched_propositions_preserved(classifier):
    """Matched propositions retain MATCHED_BY_BASE_ASAG status."""
    matched_prop = make_prop("key", "identify", "record", text="primary key uniquely identifies records")

    res = classifier.classify_propositions(
        question="What is a primary key?",
        reference_answer="A primary key uniquely identifies records.",
        student_answer="A primary key uniquely identifies records.",
        unmatched_student_props=[],
        matched_student_props=[matched_prop],
    )

    assert len(res.classified_propositions) == 1
    assert res.classified_propositions[0].classification == AdditionalInfoClass.MATCHED_BY_BASE_ASAG
    assert res.matched_count == 1
    assert res.unmatched_count == 0


def test_bst_core_contradiction_not_irrelevant(classifier):
    """
    Regression test for Issue 2:
    Case 2E - BST with inverted relative_size must be detected as INCORRECT
    via VALUE_CONFLICT (relative_size) and never misclassified as IRRELEVANT.
    """
    from base_asag.dependency.parser import DependencyParser
    from base_asag.representation.hybrid import RobustPropositionExtractor
    parser = DependencyParser()
    extractor = RobustPropositionExtractor()
    question = "What is a binary search tree?"
    ref = "A binary search tree is a tree where the left child is smaller than the parent."
    stu = "A binary search tree is a tree where the left child is larger than the parent."
    ref_props = extractor.extract_document(parser.parse_document(ref))
    stu_props = extractor.extract_document(parser.parse_document(stu))

    larger_props = [p for p in stu_props if "larger" in p.source_text.lower() or p.object_lemma == "large"]
    assert len(larger_props) >= 1

    res = classifier.classify_propositions(
        question=question,
        reference_answer=ref,
        student_answer=stu,
        unmatched_student_props=larger_props,
        reference_props=ref_props,
    )
    assert len(res.classified_propositions) == 1
    cp = res.classified_propositions[0]
    assert cp.classification == AdditionalInfoClass.INCORRECT
    assert cp.score_effect == 0.0
    assert cp.contradiction_evidence is not None
    assert cp.contradiction_evidence.contradiction_type.value == "VALUE_CONFLICT"
    assert cp.contradiction_evidence.conflicting_property == "relative_size"


def test_unsupported_relevant_information_analysis(classifier):
    """
    Diagnostic test for Issue 3:
    Case 1D - Domain-relevant proposition without reference match or property contradiction.
    Documents that domain relevance alone leads to CORRECT_ADDITIONAL under current heuristics,
    demonstrating the need for UNCERTAIN representation when factual support is absent.
    """
    from base_asag.dependency.parser import DependencyParser
    from base_asag.representation.hybrid import RobustPropositionExtractor
    parser = DependencyParser()
    extractor = RobustPropositionExtractor()
    question = "What is the purpose of a primary key?"
    ref = "A primary key uniquely identifies each record in a table."
    stu = "A primary key requires an integer data type."
    ref_props = extractor.extract_document(parser.parse_document(ref))
    stu_props = extractor.extract_document(parser.parse_document(stu))
    assert len(stu_props) >= 1

    res = classifier.classify_propositions(
        question=question,
        reference_answer=ref,
        student_answer=stu,
        unmatched_student_props=stu_props,
        reference_props=ref_props,
    )
    assert len(res.classified_propositions) >= 1
    cp = res.classified_propositions[0]
    # Under evidence-grounded verification, unsupported relevant info is held as UNCERTAIN
    assert cp.classification == AdditionalInfoClass.UNCERTAIN
    assert cp.score_effect == 0.0
    assert cp.relevance_evidence is not None
    assert cp.verification_evidence is not None
    assert cp.verification_evidence.status.value == "UNVERIFIED"


def test_primary_key_contradiction_invariance():
    """
    Regression test for Issue 4:
    Confirms that Case 1E retains the exact production V3 score of 4.33/5.0
    (verifying that no ad-hoc scoring multipliers or gates were introduced).
    """
    from proposed_asag.overhauled_pipeline import OverhauledASAGPipeline
    from proposed_asag.scoring.bounded_scorer import ScoringStrategy
    pipeline = OverhauledASAGPipeline(
        use_hybrid_representation=True,
        semantic_matcher_version="v2",
        matching_strategy="global",
        use_question_relevance=True,
        use_property_contradiction=True,
        scoring_strategy=ScoringStrategy.SATURATING,
        enable_proposed_scoring=True,
        scale=5.0,
    )
    q = "What is the purpose of a primary key?"
    r = "A primary key uniquely identifies each record in a table."
    s = "A primary key uniquely identifies each record in a table and can contain duplicate values."
    res = pipeline.evaluate(q, r, s)
    assert res.matched_propositions_count >= 1
    assert res.incorrect_count >= 1
    assert round(res.base_score_scaled, 2) == 5.00
    assert round(res.final_score_scaled, 2) == 4.33
    assert round(res.base_score_scaled - res.final_score_scaled, 2) == 0.67

