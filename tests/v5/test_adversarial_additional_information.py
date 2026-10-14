"""
Adversarial and Contrastive Evaluation Suite for V5 Additional-Information Reasoning (Task 6).

Systematically audits V5 under adversarial, contrastive, and boundary conditions to verify:
1. Category A: Core-credit preservation across all four unmatched proposition categories
   (CORRECT_ADDITIONAL, IRRELEVANT, UNCERTAIN, INCORRECT) for full and partial core answers.
2. Category B: Question relevance analysis (paraphrases, background container facts,
   adjacent entities, anaphoric pronouns, uncurated topical claims).
3. Category C: Classification boundaries (contradicted vs unsupported, unverified vs irrelevant,
   additional vs redundant restatement, genuine contradiction vs compatible property,
   queried entity vs adjacent entity).
4. Category D: Scoring invariants (strict 0.0 neutral effect for irrelevant/uncertain,
   no collateral damage on unrelated requirements, no repetition compounding for bonuses
   or penalties, strict [0.0, 5.0] score bounds).
"""

import pytest

from proposed_asag.classification.robust_classifier import AdditionalInfoClass
from proposed_asag.pipeline_v5 import (
    Experiment5Pipeline,
    Experiment5Variant,
    ReferenceRequirementRecord,
    RequirementStatus,
)


@pytest.fixture(scope="module")
def pipeline():
    return Experiment5Pipeline(variant=Experiment5Variant.V5)


# ==============================================================================
# CATEGORY A: Core-Credit Preservation Under All Additional-Information Classes
# ==============================================================================


class TestCoreCreditPreservationAdversarial:
    """Verifies that earned core credit is strictly protected across all four categories."""

    def test_full_core_clean_receives_full_credit(self, pipeline):
        q = "What is the purpose of a primary key?"
        ref = "A primary key uniquely identifies each record in a table."
        stu = "A primary key uniquely identifies each record in a table."

        res = pipeline.evaluate(q, ref, stu)

        assert res.base_score_effective == pytest.approx(1.0, abs=0.01)
        assert res.final_grade == pytest.approx(5.0, abs=0.01)
        assert len(res.score_result.itemized_adjustments) >= 1
        assert res.score_result.itemized_adjustments[0].classification == AdditionalInfoClass.MATCHED_BY_BASE_ASAG.value

    def test_full_core_plus_verified_bonus_preserves_core_and_awards_bonus(self, pipeline):
        q = "What is the purpose of a primary key?"
        ref = "A primary key uniquely identifies each record in a table."
        stu = "A primary key uniquely identifies each record in a table and cannot contain NULL values."

        res = pipeline.evaluate(q, ref, stu)

        assert res.base_score_effective == pytest.approx(1.0, abs=0.01)
        assert res.final_grade == pytest.approx(5.0, abs=0.01)  # Capped at max 5.0
        classes = [item.classification for item in res.score_result.itemized_adjustments]
        assert AdditionalInfoClass.MATCHED_BY_BASE_ASAG.value in classes
        assert AdditionalInfoClass.CORRECT_ADDITIONAL.value in classes
        # Positive bonus should be itemized with positive adjustment value
        correct_items = [i for i in res.score_result.itemized_adjustments if i.classification == AdditionalInfoClass.CORRECT_ADDITIONAL.value]
        assert len(correct_items) == 1
        assert correct_items[0].adjustment_value > 0.0

    def test_full_core_plus_irrelevant_preserves_full_grade(self, pipeline):
        q = "What is the purpose of a primary key?"
        ref = "A primary key uniquely identifies each record in a table."
        stu = "A primary key uniquely identifies each record in a table. SQL was created in the 1970s."

        res = pipeline.evaluate(q, ref, stu)

        assert res.base_score_effective == pytest.approx(1.0, abs=0.01)
        assert res.final_grade == pytest.approx(5.0, abs=0.01)
        classes = [item.classification for item in res.score_result.itemized_adjustments]
        assert AdditionalInfoClass.IRRELEVANT.value in classes
        irrel_items = [i for i in res.score_result.itemized_adjustments if i.classification == AdditionalInfoClass.IRRELEVANT.value]
        for it in irrel_items:
            assert it.adjustment_value == 0.0

    def test_full_core_plus_unverified_preserves_full_grade(self, pipeline):
        q = "What is the purpose of a primary key?"
        ref = "A primary key uniquely identifies each record in a table."
        stu = "A primary key uniquely identifies each record in a table. Primary keys create clustered indexes in MySQL."

        res = pipeline.evaluate(q, ref, stu)

        assert res.base_score_effective == pytest.approx(1.0, abs=0.01)
        assert res.final_grade == pytest.approx(5.0, abs=0.01)
        classes = [item.classification for item in res.score_result.itemized_adjustments]
        assert AdditionalInfoClass.UNCERTAIN.value in classes
        uncertain_items = [i for i in res.score_result.itemized_adjustments if i.classification == AdditionalInfoClass.UNCERTAIN.value]
        for it in uncertain_items:
            assert it.adjustment_value == 0.0

    def test_full_core_plus_contradiction_penalizes_proportionally_not_zeroed(self, pipeline):
        q = "What is the purpose of a primary key?"
        ref = "A primary key uniquely identifies each record in a table."
        stu = "A primary key uniquely identifies each record in a table and can contain duplicate values."

        res = pipeline.evaluate(q, ref, stu)

        # Core base credit was earned
        assert res.base_score_effective == pytest.approx(1.0, abs=0.01)
        # Contradiction triggers core invalidation discount (50%), yielding exactly 2.5 / 5.0
        assert res.final_grade == pytest.approx(2.5, abs=0.1)
        assert res.final_grade > 0.0
        classes = [item.classification for item in res.score_result.itemized_adjustments]
        assert AdditionalInfoClass.INCORRECT.value in classes

    def test_partial_core_alone(self, pipeline):
        q = "What are characteristics of arrays?"
        ref = "An array has fixed size and provides random access."
        stu = "An array has fixed size."

        res = pipeline.evaluate(q, ref, stu)

        assert len(res.reference_requirements) == 2
        assert res.reference_requirements[0].status == RequirementStatus.SUPPORTED
        assert res.reference_requirements[1].status == RequirementStatus.MISSING
        assert 2.0 <= res.final_grade <= 2.6

    def test_partial_core_plus_irrelevant_preserves_partial_grade(self, pipeline):
        q = "What are characteristics of arrays?"
        ref = "An array has fixed size and provides random access."
        stu_alone = "An array has fixed size."
        stu_irrel = "An array has fixed size. Python was invented in the 1990s."

        res_alone = pipeline.evaluate(q, ref, stu_alone)
        res_irrel = pipeline.evaluate(q, ref, stu_irrel)

        assert res_irrel.final_grade == pytest.approx(res_alone.final_grade, abs=0.05)
        classes = [item.classification for item in res_irrel.score_result.itemized_adjustments]
        assert AdditionalInfoClass.IRRELEVANT.value in classes

    def test_partial_core_plus_unverified_preserves_partial_grade(self, pipeline):
        q = "What are characteristics of arrays?"
        ref = "An array has fixed size and provides random access."
        stu_alone = "An array has fixed size."
        stu_unver = "An array has fixed size. Arrays have cache locality advantages on modern CPUs."

        res_alone = pipeline.evaluate(q, ref, stu_alone)
        res_unver = pipeline.evaluate(q, ref, stu_unver)

        assert res_unver.final_grade == pytest.approx(res_alone.final_grade, abs=0.05)
        classes = [item.classification for item in res_unver.score_result.itemized_adjustments]
        assert AdditionalInfoClass.UNCERTAIN.value in classes

    def test_partial_core_plus_contradiction_penalizes_without_discarding_supported(self, pipeline):
        q = "What are characteristics of arrays?"
        ref = "An array has fixed size and provides random access."
        stu_alone = "An array has fixed size."
        stu_contra = "An array has fixed size and provides sequential access only."

        res_alone = pipeline.evaluate(q, ref, stu_alone)
        res_contra = pipeline.evaluate(q, ref, stu_contra)

        assert res_contra.reference_requirements[0].status == RequirementStatus.SUPPORTED
        assert res_contra.reference_requirements[1].status == RequirementStatus.CONTRADICTED
        # Contradiction lowers score compared to partial alone, but does not zero out supported requirement
        assert 0.5 <= res_contra.final_grade < res_alone.final_grade
        assert res_contra.final_grade > 0.0


# ==============================================================================
# CATEGORY B: Question Relevance Analysis
# ==============================================================================


class TestQuestionRelevanceAnalysis:
    """Verifies that relevance distinguishes primary targets, domain context, and unrelated facts."""

    def test_paraphrase_of_core_concept_is_relevant_and_matched(self, pipeline):
        q = "What is the purpose of a primary key?"
        ref = "A primary key uniquely identifies each record in a table."
        stu = "A primary key uniquely identifies every single row in a table."

        res = pipeline.evaluate(q, ref, stu)

        assert res.final_grade >= 4.5
        matched = [i for i in res.score_result.itemized_adjustments if i.classification == AdditionalInfoClass.MATCHED_BY_BASE_ASAG.value]
        assert len(matched) >= 1

    def test_domain_container_fact_without_target_entity_is_irrelevant(self, pipeline):
        q = "What is the purpose of a primary key in a relational database?"
        ref = "A primary key uniquely identifies each record in a table."
        stu = "A primary key uniquely identifies each record in a table. Relational databases use tables."

        res = pipeline.evaluate(q, ref, stu)

        # "Relational databases use tables" has domain context words but no primary key assertion -> IRRELEVANT
        classes = [item.classification for item in res.score_result.itemized_adjustments]
        assert AdditionalInfoClass.IRRELEVANT.value in classes
        assert AdditionalInfoClass.UNCERTAIN.value not in classes

    def test_different_entity_assertion_is_not_credited_as_target_bonus(self, pipeline):
        q = "What is the purpose of a primary key?"
        ref = "A primary key uniquely identifies each record in a table."
        stu = "A primary key uniquely identifies each record in a table. Foreign keys cannot contain NULL values."

        res = pipeline.evaluate(q, ref, stu)

        # "Foreign keys cannot contain NULL values" must NOT receive PK_NOT_NULL bonus
        correct_items = [i for i in res.score_result.itemized_adjustments if i.classification == AdditionalInfoClass.CORRECT_ADDITIONAL.value]
        assert len(correct_items) == 0

    def test_anaphoric_pronoun_resolves_to_queried_target(self, pipeline):
        q = "What is the purpose of a primary key?"
        ref = "A primary key uniquely identifies each record in a table."
        stu = "A primary key uniquely identifies each record in a table. It cannot contain NULL values."

        res = pipeline.evaluate(q, ref, stu)

        # "It cannot contain NULL values" refers back to primary key -> matches PK_NOT_NULL
        classes = [item.classification for item in res.score_result.itemized_adjustments]
        assert AdditionalInfoClass.CORRECT_ADDITIONAL.value in classes
        assert res.final_grade == pytest.approx(5.0, abs=0.01)

    def test_uncurated_topical_assertion_is_uncertain(self, pipeline):
        q = "What is the purpose of a primary key?"
        ref = "A primary key uniquely identifies each record in a table."
        stu = "A primary key uniquely identifies each record in a table. Primary keys create B-tree indices."

        res = pipeline.evaluate(q, ref, stu)

        # Mentions primary key (relevant), but not in curated domain rules -> UNCERTAIN, NOT IRRELEVANT
        classes = [item.classification for item in res.score_result.itemized_adjustments]
        assert AdditionalInfoClass.UNCERTAIN.value in classes
        assert AdditionalInfoClass.CORRECT_ADDITIONAL.value not in classes


# ==============================================================================
# CATEGORY C: Classification Boundaries
# ==============================================================================


class TestClassificationBoundaries:
    """Verifies clear demarcations between adjacent classification states."""

    def test_boundary_contradicted_vs_unsupported(self, pipeline):
        q = "What is the purpose of a primary key?"
        ref = "A primary key uniquely identifies each record in a table."

        # Contradicted claim
        stu_contra = "A primary key uniquely identifies each record in a table and can contain duplicate values."
        res_contra = pipeline.evaluate(q, ref, stu_contra)
        classes_contra = [i.classification for i in res_contra.score_result.itemized_adjustments]
        assert AdditionalInfoClass.INCORRECT.value in classes_contra

        # Unsupported consistent claim
        stu_unsupported = "A primary key uniquely identifies each record in a table. Primary keys create indexes."
        res_unsupported = pipeline.evaluate(q, ref, stu_unsupported)
        classes_unsupported = [i.classification for i in res_unsupported.score_result.itemized_adjustments]
        assert AdditionalInfoClass.UNCERTAIN.value in classes_unsupported
        assert AdditionalInfoClass.INCORRECT.value not in classes_unsupported

    def test_boundary_unverified_vs_irrelevant(self, pipeline):
        q = "What is the purpose of a primary key?"
        ref = "A primary key uniquely identifies each record in a table."

        # Unverified topical: mentions primary key
        stu_unver = "A primary key uniquely identifies each record in a table. Primary keys speed up table queries."
        res_unver = pipeline.evaluate(q, ref, stu_unver)
        classes_unver = [i.classification for i in res_unver.score_result.itemized_adjustments]
        assert AdditionalInfoClass.UNCERTAIN.value in classes_unver

        # Irrelevant off-topic: does not mention target concept
        stu_irrel = "A primary key uniquely identifies each record in a table. C++ was created by Bjarne Stroustrup."
        res_irrel = pipeline.evaluate(q, ref, stu_irrel)
        classes_irrel = [i.classification for i in res_irrel.score_result.itemized_adjustments]
        assert AdditionalInfoClass.IRRELEVANT.value in classes_irrel

    def test_boundary_additional_vs_redundant_restatement(self, pipeline):
        q = "What is the purpose of a primary key?"
        ref = "A primary key uniquely identifies each record in a table."
        stu_redundant = "A primary key uniquely identifies each record in a table. It uniquely identifies each record in a table."

        res = pipeline.evaluate(q, ref, stu_redundant)

        # Redundant repetition of the core claim must NOT receive CORRECT_ADDITIONAL bonus
        classes = [i.classification for i in res.score_result.itemized_adjustments]
        assert AdditionalInfoClass.CORRECT_ADDITIONAL.value not in classes
        assert res.final_grade == pytest.approx(5.0, abs=0.01)

    def test_boundary_genuine_contradiction_vs_compatible_property(self, pipeline):
        q = "What is the purpose of a primary key?"
        ref = "A primary key uniquely identifies each record in a table."

        # Genuine contradiction of uniqueness
        stu_contra = "A primary key uniquely identifies each record in a table and can contain duplicate values."
        res_contra = pipeline.evaluate(q, ref, stu_contra)
        classes_contra = [i.classification for i in res_contra.score_result.itemized_adjustments]
        assert AdditionalInfoClass.INCORRECT.value in classes_contra

        # Compatible supplementary property (nullability invariant)
        stu_compatible = "A primary key uniquely identifies each record in a table and cannot contain NULL values."
        res_compatible = pipeline.evaluate(q, ref, stu_compatible)
        classes_comp = [i.classification for i in res_compatible.score_result.itemized_adjustments]
        assert AdditionalInfoClass.CORRECT_ADDITIONAL.value in classes_comp
        assert AdditionalInfoClass.INCORRECT.value not in classes_comp

    def test_boundary_queried_entity_vs_forbidden_modifier(self, pipeline):
        q = "What is the purpose of a primary key?"
        ref = "A primary key uniquely identifies each record in a table."

        # Queried entity: matches PK_NOT_NULL
        stu_pk = "A primary key uniquely identifies each record in a table. Primary keys cannot contain NULL values."
        res_pk = pipeline.evaluate(q, ref, stu_pk)
        classes_pk = [i.classification for i in res_pk.score_result.itemized_adjustments]
        assert AdditionalInfoClass.CORRECT_ADDITIONAL.value in classes_pk

        # Conflicting entity: foreign key has forbidden modifier
        stu_fk = "A primary key uniquely identifies each record in a table. Foreign keys cannot contain NULL values."
        res_fk = pipeline.evaluate(q, ref, stu_fk)
        classes_fk = [i.classification for i in res_fk.score_result.itemized_adjustments]
        assert AdditionalInfoClass.CORRECT_ADDITIONAL.value not in classes_fk


# ==============================================================================
# CATEGORY D: Scoring Invariants & Reliability
# ==============================================================================


class TestScoringInvariants:
    """Verifies mathematical guarantees: neutrality, deduplication, and bounds."""

    def test_irrelevant_proposition_strictly_zero_score_effect(self, pipeline):
        q = "What is the purpose of a primary key?"
        ref = "A primary key uniquely identifies each record in a table."
        stu_clean = "A primary key uniquely identifies each record in a table."
        stu_irrel = "A primary key uniquely identifies each record in a table. Databases are widely used in banking."

        res_clean = pipeline.evaluate(q, ref, stu_clean)
        res_irrel = pipeline.evaluate(q, ref, stu_irrel)

        assert res_clean.final_grade == pytest.approx(res_irrel.final_grade, abs=1e-5)
        for item in res_irrel.score_result.itemized_adjustments:
            if item.classification == AdditionalInfoClass.IRRELEVANT.value:
                assert item.adjustment_value == 0.0

    def test_uncertain_proposition_strictly_zero_score_effect(self, pipeline):
        q = "What is the purpose of a primary key?"
        ref = "A primary key uniquely identifies each record in a table."
        stu_clean = "A primary key uniquely identifies each record in a table."
        stu_unver = "A primary key uniquely identifies each record in a table. Primary keys are indexed automatically."

        res_clean = pipeline.evaluate(q, ref, stu_clean)
        res_unver = pipeline.evaluate(q, ref, stu_unver)

        assert res_clean.final_grade == pytest.approx(res_unver.final_grade, abs=1e-5)
        for item in res_unver.score_result.itemized_adjustments:
            if item.classification == AdditionalInfoClass.UNCERTAIN.value:
                assert item.adjustment_value == 0.0

    def test_repetition_does_not_multiply_positive_bonus(self, pipeline):
        q = "What is the purpose of a primary key?"
        ref = "A primary key uniquely identifies each record in a table."
        stu_single = (
            "A primary key uniquely identifies each record in a table and cannot contain NULL values."
        )
        stu_repeated = (
            "A primary key uniquely identifies each record in a table and cannot contain NULL values. "
            "It cannot contain NULL values."
        )

        res_single = pipeline.evaluate(q, ref, stu_single)
        res_repeated = pipeline.evaluate(q, ref, stu_repeated)

        assert res_single.final_grade == pytest.approx(res_repeated.final_grade, abs=1e-5)
        # Deduplication must mark repeated item and give 0.0 adjustment
        repeated_items = [
            i for i in res_repeated.score_result.itemized_adjustments
            if "REPEATED" in i.rationale
        ]
        assert len(repeated_items) >= 1
        assert repeated_items[0].adjustment_value == 0.0

    def test_repetition_does_not_multiply_contradiction_penalty(self, pipeline):
        q = "What is the purpose of a primary key?"
        ref = "A primary key uniquely identifies each record in a table."
        stu_single = (
            "A primary key uniquely identifies each record in a table and can contain duplicate values."
        )
        stu_repeated = (
            "A primary key uniquely identifies each record in a table and can contain duplicate values. "
            "It can contain duplicate values."
        )

        res_single = pipeline.evaluate(q, ref, stu_single)
        res_repeated = pipeline.evaluate(q, ref, stu_repeated)

        # Penalty must apply ONCE (50% discount = 2.5), NOT compound (25% discount = 1.25)
        assert res_single.final_grade == pytest.approx(2.5, abs=0.1)
        assert res_repeated.final_grade == pytest.approx(res_single.final_grade, abs=1e-5)
        repeated_contra_items = [
            i for i in res_repeated.score_result.itemized_adjustments
            if "REPEATED" in i.rationale
        ]
        assert len(repeated_contra_items) >= 1
        assert repeated_contra_items[0].adjustment_value == 0.0

    @pytest.mark.parametrize(
        "stu",
        [
            "A primary key uniquely identifies each record in a table.",
            "A primary key uniquely identifies each record in a table and cannot contain NULL values.",
            "A primary key uniquely identifies each record in a table and can contain duplicate values.",
            "A primary key uniquely identifies each record in a table. SQL was created in the 1970s.",
            "A primary key uniquely identifies each record in a table. Primary keys create indexes.",
            "Completely wrong answer about cooking pasta.",
            "No answer provided here.",
            "A primary key can contain duplicate values and can contain NULL values and is not unique.",
        ],
    )
    def test_score_bounds_strictly_within_zero_to_five(self, pipeline, stu):
        q = "What is the purpose of a primary key?"
        ref = "A primary key uniquely identifies each record in a table."

        res = pipeline.evaluate(q, ref, stu)

        assert 0.0 <= res.final_grade <= 5.0
        assert 0.0 <= res.score_result.final_score <= 1.0
