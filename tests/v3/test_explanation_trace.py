"""
Tests for Phase 9: Deterministic Explanation Trace Generator.
"""

import json
import pytest

from base_asag.representation.hybrid import Modality, Polarity, PropositionType, RobustProposition
from proposed_asag.classification.robust_classifier import (
    AdditionalInfoClass,
    ClassifiedProposition,
    RobustClassificationResult,
)
from proposed_asag.contradiction.property_contradiction import (
    ContradictionEvidence,
    ContradictionType,
)
from proposed_asag.explanation.trace_generator import (
    ExplanationTraceGenerator,
    GradingExplanationTrace,
)
from proposed_asag.relevance.question_relevance import RelevanceEvidence
from proposed_asag.scoring.bounded_scorer import (
    BoundedScoreResult,
    ScoringStrategy,
)


def test_explanation_trace_matched_and_correct_addition():
    generator = ExplanationTraceGenerator(default_scale=5.0)

    prop1 = RobustProposition(
        subject="primary key",
        predicate="contain",
        object="null values",
        subject_lemma="primary key",
        predicate_lemma="contain",
        object_lemma="null value",
        representation_type=PropositionType.TRIPLE,
        polarity=Polarity.NEGATIVE,
        modality=Modality.ASSERTED,
        source_text="cannot contain NULL values",
        char_start=0,
        char_end=26,
        sentence_index=0,
        token_indices=(0, 1, 2),
        dependency_evidence=("aux", "neg"),
    )

    rel_ev = RelevanceEvidence(
        question_similarity=0.85,
        concept_overlap=0.80,
        predicate_relevance=0.90,
        lexical_evidence={"matched_tokens": ["primary", "key"]},
        semantic_evidence={"score": 0.85},
        evidence_strength=0.85,
        is_relevant=True,
        evidence_explanation="High question focus term overlap",
    )

    cp = ClassifiedProposition(
        proposition=prop1,
        classification=AdditionalInfoClass.CORRECT_ADDITIONAL,
        relevance_evidence=rel_ev,
        contradiction_evidence=None,
        score_effect=0.0,
        rationale="Relevant and non-contradictory domain property.",
    )

    score_result = BoundedScoreResult(
        base_score=0.70,
        net_adjustment=0.15,
        final_score=0.85,
        strategy=ScoringStrategy.SATURATING,
        positive_adjustment=0.15,
        negative_adjustment=0.0,
        is_clipped_upper=False,
        is_clipped_lower=False,
        correct_additional_count=1,
        irrelevant_count=0,
        incorrect_count=0,
        uncertain_count=0,
        adjustment_records=[],
        explanation="Saturating bonus applied",
    )

    matched_evidence = [
        {
            "reference_statement": "A primary key uniquely identifies each record.",
            "student_statement": "A primary key uniquely identifies each record.",
            "match_score": 1.0,
            "entailment_status": "ENTAILS",
            "evidence_summary": "Exact dependency match",
        }
    ]

    trace = generator.generate_trace(
        question="What is the purpose of a primary key?",
        reference_answer="A primary key uniquely identifies each record.",
        student_answer="A primary key uniquely identifies each record and cannot contain NULL values.",
        score_result=score_result,
        classification_result=[cp],
        matched_evidence=matched_evidence,
    )

    assert isinstance(trace, GradingExplanationTrace)
    assert trace.base_score_scaled == 3.5
    assert trace.final_score_scaled == pytest.approx(4.25, abs=1e-3)
    assert len(trace.matched_items) == 1
    assert len(trace.correct_additional_items) == 1
    assert len(trace.irrelevant_items) == 0
    assert len(trace.contradictory_items) == 0

    text = trace.formatted_text
    assert "ASAG GRADING EXPLANATION TRACE" in text
    assert "FINAL GRADE: 4.25 / 5.00" in text
    assert "Base ASAG Score:      3.50 / 5.00" in text
    assert "cannot contain NULL values" in text
    assert "CORRECT_ADDITIONAL" in text


def test_explanation_trace_irrelevant_and_contradiction():
    generator = ExplanationTraceGenerator(default_scale=5.0)

    prop_irr = RobustProposition(
        subject="SQL",
        predicate="developed",
        object="in 1970s",
        subject_lemma="sql",
        predicate_lemma="develop",
        object_lemma="in 1970s",
        representation_type=PropositionType.TRIPLE,
        polarity=Polarity.POSITIVE,
        modality=Modality.ASSERTED,
        source_text="SQL was developed in the 1970s.",
        char_start=0,
        char_end=32,
        sentence_index=1,
        token_indices=(0, 1, 2),
        dependency_evidence=(),
    )

    prop_contra = RobustProposition(
        subject="primary key",
        predicate="contain",
        object="duplicate values",
        subject_lemma="primary key",
        predicate_lemma="contain",
        object_lemma="duplicate value",
        representation_type=PropositionType.PROPERTY,
        polarity=Polarity.POSITIVE,
        modality=Modality.ASSERTED,
        source_text="can contain duplicate values",
        char_start=0,
        char_end=28,
        sentence_index=1,
        token_indices=(3, 4, 5),
        dependency_evidence=(),
    )

    cp_irr = ClassifiedProposition(
        proposition=prop_irr,
        classification=AdditionalInfoClass.IRRELEVANT,
        relevance_evidence=RelevanceEvidence(
            question_similarity=0.10,
            concept_overlap=0.05,
            predicate_relevance=0.10,
            lexical_evidence={"matched_tokens": []},
            semantic_evidence={"score": 0.10},
            evidence_strength=0.10,
            is_relevant=False,
            evidence_explanation="Off-topic historical trivia",
        ),
        contradiction_evidence=None,
        score_effect=0.0,
        rationale="Off-topic historical trivia",
    )

    cp_contra = ClassifiedProposition(
        proposition=prop_contra,
        classification=AdditionalInfoClass.INCORRECT,
        relevance_evidence=RelevanceEvidence(
            question_similarity=0.80,
            concept_overlap=0.75,
            predicate_relevance=0.80,
            lexical_evidence={"matched_tokens": ["primary", "key"]},
            semantic_evidence={"score": 0.80},
            evidence_strength=0.80,
            is_relevant=True,
            evidence_explanation="Mentions primary key",
        ),
        contradiction_evidence=ContradictionEvidence(
            is_contradicted=True,
            contradiction_type=ContradictionType.VALUE_CONFLICT,
            conflicting_entity="primary key",
            conflicting_property="uniqueness",
            conflicting_value="contain duplicate values",
            evidence_strength=0.90,
            explanation="Uniqueness property directly violated by duplicate values",
        ),
        score_effect=0.0,
        rationale="Direct property contradiction regarding uniqueness",
    )

    score_result = BoundedScoreResult(
        base_score=0.70,
        net_adjustment=-0.20,
        final_score=0.50,
        strategy=ScoringStrategy.SUM,
        positive_adjustment=0.0,
        negative_adjustment=0.20,
        is_clipped_upper=False,
        is_clipped_lower=False,
        correct_additional_count=0,
        irrelevant_count=1,
        incorrect_count=1,
        uncertain_count=0,
        adjustment_records=[],
        explanation="Penalty applied",
    )

    trace = generator.generate_trace(
        question="What is the purpose of a primary key?",
        reference_answer="A primary key uniquely identifies each record.",
        student_answer="A primary key uniquely identifies each record. SQL was developed in 1970s and can contain duplicate values.",
        score_result=score_result,
        classification_result=[cp_irr, cp_contra],
        matched_evidence=[],
    )

    assert len(trace.irrelevant_items) == 1
    assert len(trace.contradictory_items) == 1
    assert "VALUE_CONFLICT" in trace.contradictory_items[0].contradiction_type
    assert trace.final_score_scaled == pytest.approx(2.50, abs=1e-3)

    # Test serialization
    data = trace.to_dict()
    assert data["scores"]["final_score_scaled"] == 2.5
    json_str = trace.to_json()
    assert json.loads(json_str)["scores"]["base_score_scaled"] == 3.5
