"""
Controlled Regression Test Suite for V5 Task 5: Additional-Information Reasoning.

Verifies:
1. Epistemic 4-way classification: CORRECT_ADDITIONAL, IRRELEVANT, INCORRECT, UNCERTAIN.
2. Core answer credit preservation across different additional information categories.
3. Proper handling of related terminology that does not answer the question (IRRELEVANT).
4. Evidence-grounded verification via CuratedDomainKnowledge (CORRECT_ADDITIONAL).
5. Unverified topical assertions held as UNCERTAIN without score penalty or bonus.
6. Anaphoric pronoun resolution in supplementary clauses ("It cannot contain NULL values").
7. Forbidden entity modifier rejection ("Foreign keys cannot contain NULL values").
8. Multiple additional propositions in a single student answer.
"""

import pytest

from base_asag.representation.hybrid import Polarity
from proposed_asag.classification.robust_classifier import AdditionalInfoClass
from proposed_asag.pipeline_v5 import Experiment5Pipeline, Experiment5Variant
from proposed_asag.relevance.question_relevance import QuestionAnalyzer, QuestionAwareRelevanceAnalyzer


@pytest.fixture(scope="module")
def pipeline():
    return Experiment5Pipeline(variant=Experiment5Variant.V5)


@pytest.fixture(scope="module")
def relevance_analyzer():
    return QuestionAwareRelevanceAnalyzer()


@pytest.fixture(scope="module")
def question_analyzer():
    return QuestionAnalyzer()


# ==============================================================================
# SECTION 1: Question Relevance & Background Terminology Disambiguation
# ==============================================================================


class TestQuestionRelevanceAndContext:
    """Tests distinguishing primary queried entities from background domain context."""

    def test_question_analyzer_identifies_primary_and_domain_entities(self, question_analyzer):
        q = "What is the purpose of a primary key in a relational database?"
        analysis = question_analyzer.analyze(q)
        assert "key" in analysis.primary_entities or "primary" in analysis.primary_entities
        assert "database" in analysis.domain_context or "relational" in analysis.domain_context

    def test_related_terminology_without_queried_entity_is_irrelevant(self, pipeline):
        """
        Student appends: "Relational databases use tables."
        This uses domain words from the question prompt ("database") but does not address "primary key".
        Should be classified as IRRELEVANT, producing zero score effect.
        """
        question = "What is the purpose of a primary key in a relational database?"
        ref = "A primary key uniquely identifies each record in a table."
        stu = "A primary key uniquely identifies each record in a table. Relational databases use tables."

        res = pipeline.evaluate(question=question, reference_answer=ref, student_answer=stu)

        assert res.final_grade == pytest.approx(5.0, abs=0.1)
        classes = [item.classification for item in res.score_result.itemized_adjustments]
        assert AdditionalInfoClass.IRRELEVANT.value in classes
        assert AdditionalInfoClass.UNCERTAIN.value not in classes

    def test_completely_off_topic_appended_fact_is_irrelevant(self, pipeline):
        """
        Student appends: "SQL was developed in the 1970s."
        Completely unrelated historical fact -> IRRELEVANT, zero score effect.
        """
        question = "What is the purpose of a primary key?"
        ref = "A primary key uniquely identifies each record in a table."
        stu = "A primary key uniquely identifies each record in a table. SQL was developed in the 1970s."

        res = pipeline.evaluate(question=question, reference_answer=ref, student_answer=stu)

        assert res.final_grade == pytest.approx(5.0, abs=0.1)
        classes = [item.classification for item in res.score_result.itemized_adjustments]
        assert AdditionalInfoClass.IRRELEVANT.value in classes


# ==============================================================================
# SECTION 2: Epistemic 4-Way Classification
# ==============================================================================


class TestFourWayClassification:
    """Verifies that each category is assigned based strictly on evidence."""

    def test_correct_additional_verified_by_domain_knowledge(self, pipeline):
        """
        Student provides: "cannot contain NULL values."
        Supported by domain knowledge rule PK_NOT_NULL -> CORRECT_ADDITIONAL.
        """
        question = "What is the purpose of a primary key?"
        ref = "A primary key uniquely identifies each record in a table."
        stu = "A primary key uniquely identifies each record in a table and cannot contain NULL values."

        res = pipeline.evaluate(question=question, reference_answer=ref, student_answer=stu)

        classes = [item.classification for item in res.score_result.itemized_adjustments]
        assert AdditionalInfoClass.CORRECT_ADDITIONAL.value in classes
        assert res.counts.get("correct_additional", 0) >= 1
        assert res.final_grade == pytest.approx(5.0, abs=0.1)

    def test_incorrect_additional_contradicted_by_domain_invariants(self, pipeline):
        """
        Student provides: "can contain duplicate values."
        Contradicts uniqueness requirement -> INCORRECT (misconception/contradiction).
        """
        question = "What is the purpose of a primary key?"
        ref = "A primary key uniquely identifies each record in a table."
        stu = "A primary key uniquely identifies each record in a table and can contain duplicate values."

        res = pipeline.evaluate(question=question, reference_answer=ref, student_answer=stu)

        classes = [item.classification for item in res.score_result.itemized_adjustments]
        assert AdditionalInfoClass.INCORRECT.value in classes
        assert res.counts.get("incorrect", 0) >= 1

    def test_uncertain_additional_relevant_but_unverified(self, pipeline):
        """
        Student provides: "Primary keys create clustered indexes in MySQL."
        Mentions primary key (relevant), but not covered by curated domain knowledge -> UNCERTAIN.
        Must receive zero score penalty and zero bonus.
        """
        question = "What is the purpose of a primary key?"
        ref = "A primary key uniquely identifies each record in a table."
        stu = "A primary key uniquely identifies each record in a table. Primary keys create clustered indexes in MySQL."

        res = pipeline.evaluate(question=question, reference_answer=ref, student_answer=stu)

        classes = [item.classification for item in res.score_result.itemized_adjustments]
        assert AdditionalInfoClass.UNCERTAIN.value in classes
        # Core answer was 100% correct, so grade remains 5.0 (neutrality preserved)
        assert res.final_grade == pytest.approx(5.0, abs=0.1)


# ==============================================================================
# SECTION 3: Core Credit Preservation
# ==============================================================================


class TestCoreCreditPreservation:
    """Verifies that additional propositions do not improperly overwrite core credit."""

    def test_core_correct_plus_irrelevant_preserves_full_grade(self, pipeline):
        question = "What is a stack?"
        ref = "A stack is a last in first out data structure."
        stu = "A stack is a last in first out data structure. Python was created by Guido van Rossum."

        res = pipeline.evaluate(question=question, reference_answer=ref, student_answer=stu)

        assert res.final_grade == pytest.approx(5.0, abs=0.1)
        classes = [item.classification for item in res.score_result.itemized_adjustments]
        assert AdditionalInfoClass.IRRELEVANT.value in classes

    def test_core_correct_plus_unverified_preserves_full_grade(self, pipeline):
        question = "What is an array?"
        ref = "An array is a collection of elements stored at contiguous memory locations."
        stu = (
            "An array is a collection of elements stored at contiguous memory locations. "
            "Arrays have cache locality advantages on modern CPUs."
        )

        res = pipeline.evaluate(question=question, reference_answer=ref, student_answer=stu)

        # Full base credit preserved, UNCERTAIN produces 0 penalty
        assert res.base_score_effective == pytest.approx(1.0, abs=0.1)
        assert res.final_grade == pytest.approx(5.0, abs=0.2)

    def test_core_partial_plus_correct_additional(self, pipeline):
        """
        Partial core coverage receives soft-gated positive bonus from valid additional information.
        """
        question = "What is the purpose of a primary key?"
        ref = "A primary key uniquely identifies each record in a table."
        # Student omits unique identification, but correctly states:
        stu = "A primary key cannot contain NULL values."

        res = pipeline.evaluate(question=question, reference_answer=ref, student_answer=stu)

        classes = [item.classification for item in res.score_result.itemized_adjustments]
        assert AdditionalInfoClass.CORRECT_ADDITIONAL.value in classes
        # Base coverage is 0.0 because core identification is missing, but positive adjustment is recognized
        assert res.counts.get("correct_additional", 0) >= 1

    def test_core_correct_plus_incorrect_additional_preserves_partial_credit(self, pipeline):
        """
        When student gets the core right but adds a contradictory statement,
        the grade is penalized proportionally but NOT zeroed out (unlike total failure).
        Core credit (base = 1.0) is preserved and discounted.
        """
        question = "What is the purpose of a primary key?"
        ref = "A primary key uniquely identifies each record in a table."
        stu = "A primary key uniquely identifies each record in a table and can contain duplicate values."

        res = pipeline.evaluate(question=question, reference_answer=ref, student_answer=stu)

        # Core was satisfied
        assert res.base_score_effective == pytest.approx(1.0, abs=0.1)
        # Grade should be penalized but strictly above 0.0 (e.g. 2.5 / 5.0)
        assert 0.0 < res.final_grade < 5.0
        assert res.final_grade == pytest.approx(2.5, abs=0.1)
        classes = [item.classification for item in res.score_result.itemized_adjustments]
        assert AdditionalInfoClass.INCORRECT.value in classes


# ==============================================================================
# SECTION 4: Linguistic Mechanisms (Anaphora & Modifier Guards)
# ==============================================================================


class TestLinguisticMechanisms:
    """Verifies anaphoric resolution and modifier constraints."""

    def test_anaphoric_pronoun_subject_inherits_target_entity(self, pipeline):
        """
        Student writes two sentences:
        "A primary key uniquely identifies each record. It cannot contain NULL values."
        'It' refers back to 'primary key' -> matches PK_NOT_NULL -> CORRECT_ADDITIONAL.
        """
        question = "What is the purpose of a primary key?"
        ref = "A primary key uniquely identifies each record in a table."
        stu = "A primary key uniquely identifies each record in a table. It cannot contain NULL values."

        res = pipeline.evaluate(question=question, reference_answer=ref, student_answer=stu)

        classes = [item.classification for item in res.score_result.itemized_adjustments]
        assert AdditionalInfoClass.CORRECT_ADDITIONAL.value in classes

    def test_forbidden_modifier_prevents_false_positive_credit(self, pipeline):
        """
        Student writes: "Foreign keys cannot contain NULL values."
        'foreign' is a forbidden modifier for PK_NOT_NULL -> rejected!
        """
        question = "What is the purpose of a primary key?"
        ref = "A primary key uniquely identifies each record in a table."
        stu = "A primary key uniquely identifies each record in a table. Foreign keys cannot contain NULL values."

        res = pipeline.evaluate(question=question, reference_answer=ref, student_answer=stu)

        # Must NOT be credited as CORRECT_ADDITIONAL under PK_NOT_NULL
        for item in res.score_result.itemized_adjustments:
            if "foreign" in item.proposition_text.lower():
                assert item.classification != AdditionalInfoClass.CORRECT_ADDITIONAL.value

    def test_multiple_additional_propositions_evaluated_independently(self, pipeline):
        """
        Student provides core answer + 1 correct additional + 1 irrelevant remark:
        "A primary key uniquely identifies records and cannot contain NULL values. SQL was made in the 1970s."
        Both propositions must be tracked and classified individually.
        """
        question = "What is the purpose of a primary key?"
        ref = "A primary key uniquely identifies each record in a table."
        stu = (
            "A primary key uniquely identifies each record in a table and cannot contain NULL values. "
            "SQL was created in the 1970s."
        )

        res = pipeline.evaluate(question=question, reference_answer=ref, student_answer=stu)

        classes = [item.classification for item in res.score_result.itemized_adjustments]
        assert AdditionalInfoClass.CORRECT_ADDITIONAL.value in classes
        assert AdditionalInfoClass.IRRELEVANT.value in classes
        assert res.final_grade == pytest.approx(5.0, abs=0.1)


# ==============================================================================
# SECTION 5: Scoring Trace & Deduplication Verification
# ==============================================================================


class TestScoringTraceIntegrity:
    """Verifies that propositions are not duplicated in the itemized adjustments."""

    def test_matched_propositions_not_duplicated_in_itemized_adjustments(self, pipeline):
        question = "What is the purpose of a primary key?"
        ref = "A primary key uniquely identifies each record in a table."
        stu = "A primary key uniquely identifies each record in a table and cannot contain NULL values."

        res = pipeline.evaluate(question=question, reference_answer=ref, student_answer=stu)

        matched_items = [
            item for item in res.score_result.itemized_adjustments
            if item.classification == AdditionalInfoClass.MATCHED_BY_BASE_ASAG.value
        ]
        # Should be exactly 1 matched item, NOT duplicated!
        assert len(matched_items) == 1
