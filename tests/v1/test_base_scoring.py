"""
Tests for Stage 9 Base ASAG Scoring.

Verifies:
1. All reference propositions entailed yields normalized_score = 1.0.
2. One missing reference proposition reduces coverage appropriately (e.g. 0.5 for 1/2).
3. One uncertain proposition awards configurable partial credit (0.5 by default).
4. Contradicted proposition receives 0.0 credit and preserves CONTRADICTED status.
5. Mixed entailment + missing proposition scores correctly.
6. Mixed entailment + uncertain proposition scores correctly ((1.0 + 0.5) / 2 = 0.75).
7. Correct answer + correct extra student information: score = 1.0, extra relation untouched.
8. Correct answer + irrelevant extra student information: score = 1.0, extra relation untouched.
9. Correct answer + incorrect extra student information: score = 1.0, extra relation untouched.
10. Zero reference propositions handled gracefully without division by zero (score = 0.0).
11. Configurable uncertain_weight works as expected.
12. Configurable reference weights apply differential importance correctly.
13. Normalized score strictly bounded in [0.0, 1.0].
14. Deterministic and reproducible scoring.
15. Stage 7 triple_score and Stage 8 slot/polarity evidence preserved in PropositionScoreRecord.
16. Unmatched student information has ZERO effect on the Base ASAG score.
17. No proposed-extension classification (no correct/irrelevant/incorrect tags).
18. Full serialization to dictionary via to_dict().
19. Score scaling utility (e.g., 5.0 scale, 100.0 scale) functions accurately.
20. Optional letter grade mapping utility functions accurately.
"""

import pytest

from base_asag.dependency import DependencyParser, DependencyRelation, DependencyTripleExtractor
from base_asag.entailment import PropositionalEntailmentAnalyzer
from base_asag.matching import TripleMatcher
from base_asag.scoring import BaseASAGScorer, BaseScoreResult, PropositionScoreRecord


@pytest.fixture(scope="module")
def parser():
    return DependencyParser(model_name="en_core_web_sm")


@pytest.fixture(scope="module")
def extractor():
    return DependencyTripleExtractor()


@pytest.fixture(scope="module")
def matcher():
    return TripleMatcher()


@pytest.fixture(scope="module")
def analyzer():
    return PropositionalEntailmentAnalyzer()


@pytest.fixture(scope="module")
def scorer():
    return BaseASAGScorer()


# 1. All reference propositions entailed
def test_all_reference_propositions_entailed(parser, extractor, matcher, analyzer, scorer):
    """Verify fully entailed reference answer receives score 1.0."""
    ref_text = "A primary key uniquely identifies each record in a table."
    stu_text = "A primary key uniquely identifies each record in a table."

    ref_doc = parser.parse(ref_text)
    stu_doc = parser.parse(stu_text)

    match_res = matcher.match(
        extractor.extract_document(ref_doc),
        extractor.extract_document(stu_doc),
    )
    entail_list = analyzer.evaluate_matching_result(match_res, ref_doc, stu_doc)
    score_res = scorer.score_pipeline(match_res, entail_list)

    assert isinstance(score_res, BaseScoreResult)
    assert score_res.normalized_score == 1.0
    assert score_res.total_reference_propositions == 1
    assert score_res.entailed_count == 1
    assert score_res.missing_count == 0
    assert score_res.contradicted_count == 0
    assert score_res.uncertain_count == 0
    assert score_res.unmatched_student_count == 0
    assert score_res.proposition_results[0].status == "ENTAILED"
    assert score_res.proposition_results[0].contribution == 1.0


# 2. One missing reference proposition
def test_one_missing_reference_proposition(scorer):
    """Verify 1 of 2 reference propositions missing yields 0.5 coverage."""
    r1 = DependencyRelation("key", "identifies", "record", "key", "identify", "record", "SPO", ("nsubj", "dobj"), 0, 1, 2)
    r2 = DependencyRelation("key", "contain", "null", "key", "contain", "null", "SPO", ("nsubj", "dobj"), 3, 4, 5)

    # Student only provides R1
    s1 = DependencyRelation("key", "identifies", "record", "key", "identify", "record", "SPO", ("nsubj", "dobj"), 0, 1, 2)

    matcher = TripleMatcher()
    analyzer = PropositionalEntailmentAnalyzer()

    match_res = matcher.match([r1, r2], [s1])
    assert match_res.matched_count == 1
    assert match_res.unmatched_reference_count == 1

    entail_list = analyzer.evaluate_matching_result(match_res)
    score_res = scorer.score_pipeline(match_res, entail_list)

    assert score_res.normalized_score == 0.5
    assert score_res.total_reference_propositions == 2
    assert score_res.entailed_count == 1
    assert score_res.missing_count == 1
    assert score_res.proposition_results[1].status == "MISSING"
    assert score_res.proposition_results[1].contribution == 0.0


# 3. One uncertain proposition
def test_one_uncertain_proposition(parser, extractor, matcher, analyzer, scorer):
    """Verify uncertain proposition receives configured partial credit (0.5 by default)."""
    # Student uses 'row' instead of 'record', resulting in UNCERTAIN due to WordNet path 0.125
    ref_text = "A primary key uniquely identifies each record in a table."
    stu_text = "A primary key uniquely identifies every row in a table."

    ref_doc = parser.parse(ref_text)
    stu_doc = parser.parse(stu_text)

    match_res = matcher.match(
        extractor.extract_document(ref_doc),
        extractor.extract_document(stu_doc),
    )
    entail_list = analyzer.evaluate_matching_result(match_res, ref_doc, stu_doc)
    score_res = scorer.score_pipeline(match_res, entail_list)

    assert score_res.uncertain_count == 1
    assert score_res.normalized_score == 0.5
    assert score_res.proposition_results[0].status == "UNCERTAIN"
    assert score_res.proposition_results[0].contribution == 0.5


# 4. Contradiction
def test_contradicted_proposition_receives_zero(parser, extractor, matcher, analyzer, scorer):
    """Verify contradicted proposition receives 0.0 credit and records CONTRADICTED status."""
    ref_text = "A primary key uniquely identifies each record in a table."
    stu_text = "A primary key does not uniquely identify each record in a table."

    ref_doc = parser.parse(ref_text)
    stu_doc = parser.parse(stu_text)

    match_res = matcher.match(
        extractor.extract_document(ref_doc),
        extractor.extract_document(stu_doc),
    )
    entail_list = analyzer.evaluate_matching_result(match_res, ref_doc, stu_doc)
    score_res = scorer.score_pipeline(match_res, entail_list)

    assert score_res.contradicted_count == 1
    assert score_res.normalized_score == 0.0
    assert score_res.proposition_results[0].status == "CONTRADICTED"
    assert score_res.proposition_results[0].contribution == 0.0


# 5. Mixed entailment + missing
def test_mixed_entailment_and_missing(scorer):
    """Verify 1 entailed and 1 missing proposition yields (1.0 + 0.0)/2 = 0.5."""
    r1 = DependencyRelation("table", "stores", "data", "table", "store", "datum", "SPO", ("nsubj", "dobj"), 0, 1, 2)
    r2 = DependencyRelation("column", "defines", "type", "column", "define", "type", "SPO", ("nsubj", "dobj"), 3, 4, 5)

    s1 = DependencyRelation("table", "stores", "data", "table", "store", "datum", "SPO", ("nsubj", "dobj"), 0, 1, 2)

    matcher = TripleMatcher()
    analyzer = PropositionalEntailmentAnalyzer()

    match_res = matcher.match([r1, r2], [s1])
    entail_list = analyzer.evaluate_matching_result(match_res)
    score_res = scorer.score_pipeline(match_res, entail_list)

    assert score_res.normalized_score == 0.5
    assert score_res.entailed_count == 1
    assert score_res.missing_count == 1


# 6. Mixed entailment + uncertain
def test_mixed_entailment_and_uncertain(scorer):
    """Verify 1 entailed (1.0) and 1 uncertain (0.5) yields (1.0 + 0.5)/2 = 0.75."""
    r1 = DependencyRelation("key", "identifies", "record", "key", "identify", "record", "SPO", ("nsubj", "dobj"), 0, 1, 2)
    r2 = DependencyRelation("system", "logs", "error", "system", "log", "error", "SPO", ("nsubj", "dobj"), 3, 4, 5)

    # s1 matches r1 (exact), s2 matches r2 with partial/uncertain similarity
    s1 = DependencyRelation("key", "identifies", "record", "key", "identify", "record", "SPO", ("nsubj", "dobj"), 0, 1, 2)
    s2 = DependencyRelation("system", "logs", "bug", "system", "log", "bug", "SPO", ("nsubj", "dobj"), 3, 4, 5)

    matcher = TripleMatcher()
    analyzer = PropositionalEntailmentAnalyzer()

    match_res = matcher.match([r1, r2], [s1, s2])
    entail_list = analyzer.evaluate_matching_result(match_res)
    score_res = scorer.score_pipeline(match_res, entail_list)

    assert score_res.entailed_count == 1
    assert score_res.uncertain_count == 1
    assert score_res.normalized_score == 0.75


# 7. Correct answer + correct extra student information (Student B)
def test_correct_answer_plus_correct_extra_info(parser, extractor, matcher, analyzer, scorer):
    """Verify Student B (identifies record + cannot contain null) scores 1.0 with 1 unmatched student relation."""
    ref_text = "A primary key uniquely identifies each record in a table."
    stu_text = "A primary key uniquely identifies each record in a table and cannot contain NULL values."

    ref_doc = parser.parse(ref_text)
    stu_doc = parser.parse(stu_text)

    match_res = matcher.match(
        extractor.extract_document(ref_doc),
        extractor.extract_document(stu_doc),
    )
    entail_list = analyzer.evaluate_matching_result(match_res, ref_doc, stu_doc)
    score_res = scorer.score_pipeline(match_res, entail_list)

    assert score_res.normalized_score == 1.0
    assert score_res.entailed_count == 1
    assert score_res.missing_count == 0
    assert score_res.unmatched_student_count == 1
    assert len(score_res.unmatched_student_relations) == 1
    # Crucial research boundary: Unmatched student proposition received neither bonus nor penalty
    assert score_res.normalized_score == 1.0


# 8. Correct answer + irrelevant extra student information (Student D)
def test_correct_answer_plus_irrelevant_extra_info(parser, extractor, matcher, analyzer, scorer):
    """Verify Student D (identifies record + SQL developed 1970s) scores 1.0 with 1 unmatched student relation."""
    ref_text = "A primary key uniquely identifies each record in a table."
    stu_text = "A primary key uniquely identifies each record in a table. SQL was developed in the 1970s."

    ref_doc = parser.parse(ref_text)
    stu_doc = parser.parse(stu_text)

    match_res = matcher.match(
        extractor.extract_document(ref_doc),
        extractor.extract_document(stu_doc),
    )
    entail_list = analyzer.evaluate_matching_result(match_res, ref_doc, stu_doc)
    score_res = scorer.score_pipeline(match_res, entail_list)

    assert score_res.normalized_score == 1.0
    assert score_res.unmatched_student_count == 1
    assert score_res.unmatched_student_relations[0].subject == "SQL"


# 9. Correct answer + incorrect extra student information (Student C)
def test_correct_answer_plus_incorrect_extra_info(parser, extractor, matcher, analyzer, scorer):
    """Verify Student C (identifies record + can contain duplicate values) scores 1.0 in Base ASAG."""
    ref_text = "A primary key uniquely identifies each record in a table."
    stu_text = "A primary key uniquely identifies each record in a table and can contain duplicate values."

    ref_doc = parser.parse(ref_text)
    stu_doc = parser.parse(stu_text)

    match_res = matcher.match(
        extractor.extract_document(ref_doc),
        extractor.extract_document(stu_doc),
    )
    entail_list = analyzer.evaluate_matching_result(match_res, ref_doc, stu_doc)
    score_res = scorer.score_pipeline(match_res, entail_list)

    # Base ASAG evaluates reference proposition coverage: R1 is entailed -> 1.0
    assert score_res.normalized_score == 1.0
    assert score_res.unmatched_student_count == 1
    # Unmatched incorrect info is preserved untouched for future Stage 11-14 evaluation
    assert not hasattr(score_res.unmatched_student_relations[0], "is_incorrect")


# 10. Zero reference propositions
def test_zero_reference_propositions(scorer):
    """Verify empty reference relation set produces 0.0 without divide-by-zero error."""
    score_res = scorer.score(
        reference_relations=[],
        entailment_results=[],
        unmatched_reference_relations=[],
        unmatched_student_relations=[],
    )
    assert score_res.normalized_score == 0.0
    assert score_res.total_reference_propositions == 0


# 11. Configurable uncertain weight
def test_configurable_uncertain_weight():
    """Verify custom uncertain_weight (e.g. 0.25 and 0.75)."""
    scorer_low = BaseASAGScorer(uncertain_weight=0.25)
    scorer_high = BaseASAGScorer(uncertain_weight=0.75)

    r1 = DependencyRelation("a", "b", "c", "a", "b", "c", "SPO", ("nsubj", "dobj"), 0, 1, 2)
    s1 = DependencyRelation("a", "b", "d", "a", "b", "d", "SPO", ("nsubj", "dobj"), 0, 1, 2)

    matcher = TripleMatcher()
    analyzer = PropositionalEntailmentAnalyzer()

    match_res = matcher.match([r1], [s1])
    entail_list = analyzer.evaluate_matching_result(match_res)

    res_low = scorer_low.score_pipeline(match_res, entail_list)
    res_high = scorer_high.score_pipeline(match_res, entail_list)

    assert res_low.normalized_score == 0.25
    assert res_high.normalized_score == 0.75


# 12. Configurable reference weights
def test_configurable_reference_weights(scorer):
    """Verify non-uniform reference weights (e.g. [2.0, 1.0])."""
    r1 = DependencyRelation("key", "identifies", "record", "key", "identify", "record", "SPO", ("nsubj", "dobj"), 0, 1, 2)
    r2 = DependencyRelation("key", "contain", "null", "key", "contain", "null", "SPO", ("nsubj", "dobj"), 3, 4, 5)

    # Student only gets R1 (weight 2.0)
    s1 = DependencyRelation("key", "identifies", "record", "key", "identify", "record", "SPO", ("nsubj", "dobj"), 0, 1, 2)

    matcher = TripleMatcher()
    analyzer = PropositionalEntailmentAnalyzer()

    match_res = matcher.match([r1, r2], [s1])
    entail_list = analyzer.evaluate_matching_result(match_res)

    # R1 weight=2.0 (entailed -> 2.0*1.0), R2 weight=1.0 (missing -> 1.0*0.0)
    # Total = 2.0 / 3.0 = 0.6667
    score_res = scorer.score_pipeline(match_res, entail_list, reference_weights=[2.0, 1.0])
    assert score_res.normalized_score == 0.6667


# 13. Score strictly bounded in [0.0, 1.0]
def test_score_bounded_in_zero_to_one(scorer):
    """Verify that score cannot exceed 1.0 or drop below 0.0."""
    r1 = DependencyRelation("a", "b", "c", "a", "b", "c", "SPO", ("nsubj", "dobj"), 0, 1, 2)
    s1 = DependencyRelation("a", "b", "c", "a", "b", "c", "SPO", ("nsubj", "dobj"), 0, 1, 2)

    match_res = TripleMatcher().match([r1], [s1])
    entail_list = PropositionalEntailmentAnalyzer().evaluate_matching_result(match_res)
    score_res = scorer.score_pipeline(match_res, entail_list)

    assert 0.0 <= score_res.normalized_score <= 1.0


# 14. Deterministic output
def test_deterministic_scoring(scorer):
    """Verify multiple executions on identical input yield identical results."""
    r1 = DependencyRelation("a", "b", "c", "a", "b", "c", "SPO", ("nsubj", "dobj"), 0, 1, 2)
    s1 = DependencyRelation("a", "b", "c", "a", "b", "c", "SPO", ("nsubj", "dobj"), 0, 1, 2)

    match_res = TripleMatcher().match([r1], [s1])
    entail_list = PropositionalEntailmentAnalyzer().evaluate_matching_result(match_res)

    res1 = scorer.score_pipeline(match_res, entail_list)
    res2 = scorer.score_pipeline(match_res, entail_list)

    assert res1.normalized_score == res2.normalized_score
    assert res1.to_dict() == res2.to_dict()


# 15. Stage 7/8 evidence preserved in PropositionScoreRecord
def test_stage7_8_evidence_preserved(parser, extractor, matcher, analyzer, scorer):
    """Verify continuous triple_score, slot evidence, and entailment result are retained."""
    ref_text = "A primary key uniquely identifies each record in a table."
    stu_text = "A primary key uniquely identifies each record in a table."

    ref_doc = parser.parse(ref_text)
    stu_doc = parser.parse(stu_text)

    match_res = matcher.match(extractor.extract_document(ref_doc), extractor.extract_document(stu_doc))
    entail_list = analyzer.evaluate_matching_result(match_res, ref_doc, stu_doc)
    score_res = scorer.score_pipeline(match_res, entail_list)

    rec = score_res.proposition_results[0]
    assert rec.triple_score == 1.0
    assert rec.entailment_result is not None
    assert rec.entailment_result.relation == "ENTAILS"
    assert rec.slot_evidence is not None
    assert "subject" in rec.slot_evidence
    assert len(rec.diagnostic_reasons) > 0


# 16. Unmatched student information has ZERO effect on Base score
def test_unmatched_student_has_no_score_effect(scorer):
    """Verify adding extra unmatched student relations does not change the Base ASAG score."""
    r1 = DependencyRelation("key", "identifies", "record", "key", "identify", "record", "SPO", ("nsubj", "dobj"), 0, 1, 2)
    s1 = DependencyRelation("key", "identifies", "record", "key", "identify", "record", "SPO", ("nsubj", "dobj"), 0, 1, 2)

    s_extra1 = DependencyRelation("SQL", "developed", None, "SQL", "develop", None, "PASSIVE_SP", ("nsubjpass",), 3, 4, None)
    s_extra2 = DependencyRelation("database", "runs", "server", "database", "run", "server", "SPO", ("nsubj", "dobj"), 5, 6, 7)

    matcher = TripleMatcher()
    analyzer = PropositionalEntailmentAnalyzer()

    # Score with 0 extra student relations
    match_res1 = matcher.match([r1], [s1])
    score_res1 = scorer.score_pipeline(match_res1, analyzer.evaluate_matching_result(match_res1))

    # Score with 2 extra student relations
    match_res2 = matcher.match([r1], [s1, s_extra1, s_extra2])
    score_res2 = scorer.score_pipeline(match_res2, analyzer.evaluate_matching_result(match_res2))

    assert score_res1.normalized_score == score_res2.normalized_score == 1.0
    assert score_res1.unmatched_student_count == 0
    assert score_res2.unmatched_student_count == 2


# 17. No proposed-extension classification
def test_no_proposed_extension_classification_in_stage_9(scorer):
    """Verify BaseASAGScorer does not implement additional-information classification."""
    assert not hasattr(scorer, "classify_unmatched")
    assert not hasattr(scorer, "classify_additional_information")
    assert not hasattr(scorer, "detect_misconceptions")


# 18. Serialization works
def test_serialization(scorer):
    """Verify BaseScoreResult and PropositionScoreRecord serialize to valid dicts."""
    r1 = DependencyRelation("a", "b", "c", "a", "b", "c", "SPO", ("nsubj", "dobj"), 0, 1, 2)
    s1 = DependencyRelation("a", "b", "c", "a", "b", "c", "SPO", ("nsubj", "dobj"), 0, 1, 2)

    match_res = TripleMatcher().match([r1], [s1])
    entail_list = PropositionalEntailmentAnalyzer().evaluate_matching_result(match_res)
    score_res = scorer.score_pipeline(match_res, entail_list)
    data = score_res.to_dict()

    expected_keys = {
        "normalized_score",
        "total_reference_propositions",
        "entailed_count",
        "uncertain_count",
        "contradicted_count",
        "missing_count",
        "unmatched_student_count",
        "proposition_results",
        "unmatched_student_relations",
        "config",
    }
    assert expected_keys.issubset(data.keys())


# 19. Score scaling utility
def test_score_scaling(scorer):
    """Verify scale_score() maps normalized score to arbitrary target ranges."""
    r1 = DependencyRelation("a", "b", "c", "a", "b", "c", "SPO", ("nsubj", "dobj"), 0, 1, 2)
    r2 = DependencyRelation("d", "e", "f", "d", "e", "f", "SPO", ("nsubj", "dobj"), 3, 4, 5)
    s1 = DependencyRelation("a", "b", "c", "a", "b", "c", "SPO", ("nsubj", "dobj"), 0, 1, 2)

    match_res = TripleMatcher().match([r1, r2], [s1])
    entail_list = PropositionalEntailmentAnalyzer().evaluate_matching_result(match_res)
    score_res = scorer.score_pipeline(match_res, entail_list)

    assert score_res.normalized_score == 0.5
    assert score_res.scale_score(5.0) == 2.5
    assert score_res.scale_score(10.0) == 5.0
    assert score_res.scale_score(100.0) == 50.0

    with pytest.raises(ValueError):
        score_res.scale_score(-1.0)


# 20. Optional letter grade mapping utility
def test_letter_grade_mapping(scorer):
    """Verify map_to_letter_grade() provides demonstration letter grades."""
    r1 = DependencyRelation("a", "b", "c", "a", "b", "c", "SPO", ("nsubj", "dobj"), 0, 1, 2)
    s1 = DependencyRelation("a", "b", "c", "a", "b", "c", "SPO", ("nsubj", "dobj"), 0, 1, 2)

    match_res = TripleMatcher().match([r1], [s1])
    entail_list = PropositionalEntailmentAnalyzer().evaluate_matching_result(match_res)
    score_res = scorer.score_pipeline(match_res, entail_list)

    assert score_res.normalized_score == 1.0
    assert score_res.map_to_letter_grade() == "A"
