"""
Tests for Stage 7 Dependency Triple Matching.

Verifies:
1. Exact triple match produces score 1.0 and match_method 'exact_triple'.
2. Lemma-based triple match produces score 1.0 and match_method 'lemma_triple'.
3. Semantic slot comparison consumes Stage 6 without recomputing.
4. Subject, predicate, and object roles are strictly preserved.
5. Triple score is calculated correctly from slot similarities.
6. Configurable weights work as expected.
7. SP relations are handled properly without penalizing missing objects as zero.
8. Alignment threshold is configurable and respected.
9. One-to-one matching is strictly enforced.
10. Highest-scoring candidate is selected greedily.
11. Deterministic tie-breaking across equal-scoring candidates.
12. Unmatched reference relations are explicitly preserved.
13. Unmatched student relations are explicitly preserved.
14. Unmatched student relations are NOT classified into correct/incorrect/irrelevant.
15. Empty reference relation list handled gracefully.
16. Empty student relation list handled gracefully.
17. Both reference and student relation lists empty handled gracefully.
18. Multiple reference and student relations matching.
19. Serialization via to_dict() produces valid data structures.
20. Direct consumption of Stage 5 SentenceTriples and DocumentTriples.
21. Absence of whole-sentence cosine similarity, TF-IDF, or grading.
22. Validation of input types and weights parameters.
"""

import pytest

from base_asag.dependency import (
    DependencyParser,
    DependencyRelation,
    DependencyTripleExtractor,
)
from base_asag.matching import (
    CandidateAlignment,
    MatchedRelation,
    MatchingResult,
    TripleMatcher,
)
from base_asag.semantic import LexicalSemanticComparator


@pytest.fixture(scope="module")
def parser():
    """Provides a shared DependencyParser instance."""
    return DependencyParser(model_name="en_core_web_sm")


@pytest.fixture(scope="module")
def extractor():
    """Provides a shared DependencyTripleExtractor instance."""
    return DependencyTripleExtractor()


@pytest.fixture(scope="module")
def comparator():
    """Provides a shared LexicalSemanticComparator instance."""
    return LexicalSemanticComparator()


@pytest.fixture
def matcher(comparator):
    """Provides a standard TripleMatcher instance with default settings."""
    return TripleMatcher(comparator=comparator)


# 1. Exact triple match
def test_exact_triple_match(matcher):
    """Verify identical triples produce score 1.0 and match_method 'exact_triple'."""
    r1 = DependencyRelation(
        subject="key",
        predicate="identifies",
        object="record",
        subject_lemma="key",
        predicate_lemma="identify",
        object_lemma="record",
        relation_type="SPO",
        source_dependency_relations=("nsubj", "dobj"),
        subject_index=1,
        predicate_index=2,
        object_index=3,
    )
    s1 = DependencyRelation(
        subject="key",
        predicate="identifies",
        object="record",
        subject_lemma="key",
        predicate_lemma="identify",
        object_lemma="record",
        relation_type="SPO",
        source_dependency_relations=("nsubj", "dobj"),
        subject_index=1,
        predicate_index=2,
        object_index=3,
    )

    result = matcher.match([r1], [s1])
    assert result.matched_count == 1
    assert result.unmatched_reference_count == 0
    assert result.unmatched_student_count == 0

    matched = result.matched_relations[0]
    assert matched.triple_score == 1.0
    assert matched.subject_similarity == 1.0
    assert matched.predicate_similarity == 1.0
    assert matched.object_similarity == 1.0
    assert matched.match_method == "exact_triple"


# 2. Lemma-based triple match
def test_lemma_triple_match(matcher):
    """Verify inflected triples with matching lemmas produce score 1.0 and 'lemma_triple'."""
    r1 = DependencyRelation(
        subject="keys",
        predicate="identifies",
        object="records",
        subject_lemma="key",
        predicate_lemma="identify",
        object_lemma="record",
        relation_type="SPO",
        source_dependency_relations=("nsubj", "dobj"),
        subject_index=1,
        predicate_index=2,
        object_index=3,
    )
    s1 = DependencyRelation(
        subject="key",
        predicate="identified",
        object="record",
        subject_lemma="key",
        predicate_lemma="identify",
        object_lemma="record",
        relation_type="SPO",
        source_dependency_relations=("nsubj", "dobj"),
        subject_index=1,
        predicate_index=2,
        object_index=3,
    )

    result = matcher.match([r1], [s1])
    assert result.matched_count == 1
    matched = result.matched_relations[0]
    assert matched.triple_score == 1.0
    assert matched.match_method == "lemma_triple"


# 3. Semantic slot comparison (record vs row)
def test_semantic_slot_comparison(matcher):
    """Verify slot-level comparison reflects Stage 6 WordNet scores without recomputing."""
    ref = DependencyRelation(
        subject="key",
        predicate="identifies",
        object="record",
        subject_lemma="key",
        predicate_lemma="identify",
        object_lemma="record",
        relation_type="SPO",
        source_dependency_relations=("nsubj", "dobj"),
        subject_index=2,
        predicate_index=4,
        object_index=6,
    )
    stu = DependencyRelation(
        subject="key",
        predicate="identifies",
        object="row",
        subject_lemma="key",
        predicate_lemma="identify",
        object_lemma="row",
        relation_type="SPO",
        source_dependency_relations=("nsubj", "dobj"),
        subject_index=2,
        predicate_index=4,
        object_index=6,
    )

    result = matcher.match([ref], [stu])
    assert result.matched_count == 1
    matched = result.matched_relations[0]
    assert matched.subject_similarity == 1.0
    assert matched.predicate_similarity == 1.0
    assert 0.12 <= matched.object_similarity <= 0.13  # WordNet path similarity ~0.125
    expected_score = round((1.0 + 1.0 + matched.object_similarity) / 3.0, 6)
    assert matched.triple_score == expected_score
    assert matched.match_method == "semantic_path_triple"


# 4. Subject/predicate/object roles are preserved
def test_roles_preserved_not_bag_of_words(matcher):
    """Verify swapped roles (key identifies record vs record identifies key) do not align."""
    r1 = DependencyRelation(
        subject="key",
        predicate="identifies",
        object="record",
        subject_lemma="key",
        predicate_lemma="identify",
        object_lemma="record",
        relation_type="SPO",
        source_dependency_relations=("nsubj", "dobj"),
        subject_index=0,
        predicate_index=1,
        object_index=2,
    )
    # Student swaps subject and object: "The record identifies the key"
    s_inverted = DependencyRelation(
        subject="record",
        predicate="identifies",
        object="key",
        subject_lemma="record",
        predicate_lemma="identify",
        object_lemma="key",
        relation_type="SPO",
        source_dependency_relations=("nsubj", "dobj"),
        subject_index=0,
        predicate_index=1,
        object_index=2,
    )

    # Subject comparison: key vs record -> WordNet similarity ~0.333
    # Predicate comparison: identifies vs identifies -> 1.0
    # Object comparison: record vs key -> WordNet similarity ~0.333
    # In a bag-of-words model, this would be a 1.0 exact match.
    # In role-preserved triple matching, score is strictly bounded: (0.333 + 1.0 + 0.333) / 3 = 0.555556.
    # With alignment_threshold=0.6, it is rejected; and subject is verified to align with subject, not object.
    strict_matcher = TripleMatcher(alignment_threshold=0.6)
    result = strict_matcher.match([r1], [s_inverted])

    assert result.matched_count == 0
    assert result.unmatched_reference_count == 1
    assert result.unmatched_student_count == 1

    # Verify that the candidate comparison strictly compared subject-to-subject and object-to-object
    cand = result.candidate_alignments[0]
    assert cand.triple_score < 0.6
    assert cand.slot_evidence["subject"].source_text == "key"
    assert cand.slot_evidence["subject"].target_text == "record"
    assert cand.slot_evidence["object"].source_text == "record"
    assert cand.slot_evidence["object"].target_text == "key"


# 5. Triple score is calculated from slot similarities
def test_triple_score_calculation(matcher):
    """Verify mathematical combination of slot scores."""
    score = matcher.compute_triple_score(
        subject_similarity=0.9,
        predicate_similarity=0.6,
        object_similarity=0.3,
        is_sp_pair=False,
    )
    # Default equal weights: (0.9 + 0.6 + 0.3) / 3 = 1.8 / 3 = 0.6
    assert score == 0.6


# 6. Configurable weights work
def test_configurable_weights():
    """Verify custom slot weighting schemes."""
    # Predicate-heavy weighting
    pred_matcher = TripleMatcher(
        subject_weight=0.2,
        predicate_weight=0.6,
        object_weight=0.2,
    )
    score = pred_matcher.compute_triple_score(
        subject_similarity=1.0,
        predicate_similarity=0.5,
        object_similarity=1.0,
        is_sp_pair=False,
    )
    # 0.2*1.0 + 0.6*0.5 + 0.2*1.0 = 0.2 + 0.3 + 0.2 = 0.7
    assert score == 0.7


# 7. SP relations handled without treating missing object as zero
def test_sp_relations_weight_normalization(matcher):
    """Verify SP relations normalize weights over subject and predicate only."""
    sp_ref = DependencyRelation(
        subject="system",
        predicate="terminates",
        object=None,
        subject_lemma="system",
        predicate_lemma="terminate",
        object_lemma=None,
        relation_type="SP",
        source_dependency_relations=("nsubj",),
        subject_index=0,
        predicate_index=1,
        object_index=None,
    )
    sp_stu = DependencyRelation(
        subject="system",
        predicate="terminates",
        object=None,
        subject_lemma="system",
        predicate_lemma="terminate",
        object_lemma=None,
        relation_type="SP",
        source_dependency_relations=("nsubj",),
        subject_index=0,
        predicate_index=1,
        object_index=None,
    )

    result = matcher.match([sp_ref], [sp_stu])
    assert result.matched_count == 1
    matched = result.matched_relations[0]
    assert matched.triple_score == 1.0
    assert matched.object_similarity is None
    assert matched.match_method == "exact_triple"


# 8. Threshold is configurable
def test_configurable_threshold():
    """Verify threshold cleanly admits or rejects candidate pairs."""
    r1 = DependencyRelation(
        subject="key",
        predicate="identifies",
        object="record",
        subject_lemma="key",
        predicate_lemma="identify",
        object_lemma="record",
        relation_type="SPO",
        source_dependency_relations=("nsubj", "dobj"),
        subject_index=0,
        predicate_index=1,
        object_index=2,
    )
    s1 = DependencyRelation(
        subject="key",
        predicate="identifies",
        object="row",
        subject_lemma="key",
        predicate_lemma="identify",
        object_lemma="row",
        relation_type="SPO",
        source_dependency_relations=("nsubj", "dobj"),
        subject_index=0,
        predicate_index=1,
        object_index=2,
    )

    # With threshold 0.70: score ~0.7083 >= 0.70 -> Matches
    lenient_matcher = TripleMatcher(alignment_threshold=0.70)
    assert lenient_matcher.match([r1], [s1]).matched_count == 1

    # With threshold 0.80: score ~0.7083 < 0.80 -> Rejected
    strict_matcher = TripleMatcher(alignment_threshold=0.80)
    assert strict_matcher.match([r1], [s1]).matched_count == 0


# 9. One-to-one matching is enforced
def test_one_to_one_matching_enforced(matcher):
    """Verify one reference relation cannot match multiple student relations."""
    r1 = DependencyRelation(
        subject="key",
        predicate="identifies",
        object="record",
        subject_lemma="key",
        predicate_lemma="identify",
        object_lemma="record",
        relation_type="SPO",
        source_dependency_relations=("nsubj", "dobj"),
        subject_index=0,
        predicate_index=1,
        object_index=2,
    )
    s1 = DependencyRelation(
        subject="key",
        predicate="identifies",
        object="record",
        subject_lemma="key",
        predicate_lemma="identify",
        object_lemma="record",
        relation_type="SPO",
        source_dependency_relations=("nsubj", "dobj"),
        subject_index=0,
        predicate_index=1,
        object_index=2,
    )
    s2 = DependencyRelation(
        subject="key",
        predicate="identifies",
        object="record",
        subject_lemma="key",
        predicate_lemma="identify",
        object_lemma="record",
        relation_type="SPO",
        source_dependency_relations=("nsubj", "dobj"),
        subject_index=3,
        predicate_index=4,
        object_index=5,
    )

    result = matcher.match([r1], [s1, s2])
    assert result.matched_count == 1
    assert result.unmatched_reference_count == 0
    assert result.unmatched_student_count == 1


# 10. Highest-scoring candidate is selected deterministically
def test_highest_scoring_candidate_selected_first(matcher):
    """Verify greedy selection selects the best matching candidate."""
    r1 = DependencyRelation(
        subject="key",
        predicate="identifies",
        object="record",
        subject_lemma="key",
        predicate_lemma="identify",
        object_lemma="record",
        relation_type="SPO",
        source_dependency_relations=("nsubj", "dobj"),
        subject_index=0,
        predicate_index=1,
        object_index=2,
    )
    # Student relation 1: Partial match (row ~ 0.125)
    s_partial = DependencyRelation(
        subject="key",
        predicate="identifies",
        object="row",
        subject_lemma="key",
        predicate_lemma="identify",
        object_lemma="row",
        relation_type="SPO",
        source_dependency_relations=("nsubj", "dobj"),
        subject_index=0,
        predicate_index=1,
        object_index=2,
    )
    # Student relation 2: Exact match (record == 1.0)
    s_exact = DependencyRelation(
        subject="key",
        predicate="identifies",
        object="record",
        subject_lemma="key",
        predicate_lemma="identify",
        object_lemma="record",
        relation_type="SPO",
        source_dependency_relations=("nsubj", "dobj"),
        subject_index=3,
        predicate_index=4,
        object_index=5,
    )

    # Even if partial candidate is passed first, exact match must be chosen
    result = matcher.match([r1], [s_partial, s_exact])
    assert result.matched_count == 1
    matched = result.matched_relations[0]
    assert matched.student_index == 1
    assert matched.triple_score == 1.0
    assert result.unmatched_student_relations[0].object == "row"


# 11. Tie-breaking is deterministic
def test_deterministic_tie_breaking(matcher):
    """Verify tie-breaking by reference_index and student_index when scores are identical."""
    r0 = DependencyRelation(
        subject="key",
        predicate="identifies",
        object="record",
        subject_lemma="key",
        predicate_lemma="identify",
        object_lemma="record",
        relation_type="SPO",
        source_dependency_relations=("nsubj", "dobj"),
        subject_index=0,
        predicate_index=1,
        object_index=2,
    )
    s0 = DependencyRelation(
        subject="key",
        predicate="identifies",
        object="record",
        subject_lemma="key",
        predicate_lemma="identify",
        object_lemma="record",
        relation_type="SPO",
        source_dependency_relations=("nsubj", "dobj"),
        subject_index=0,
        predicate_index=1,
        object_index=2,
    )
    s1 = DependencyRelation(
        subject="key",
        predicate="identifies",
        object="record",
        subject_lemma="key",
        predicate_lemma="identify",
        object_lemma="record",
        relation_type="SPO",
        source_dependency_relations=("nsubj", "dobj"),
        subject_index=3,
        predicate_index=4,
        object_index=5,
    )

    result = matcher.match([r0], [s0, s1])
    # Tie-breaking prioritizes lower student index (s0 at index 0 over s1 at index 1)
    assert result.matched_relations[0].student_index == 0
    assert result.unmatched_student_relations[0] == s1


# 12. Unmatched reference relations are returned
def test_unmatched_reference_relations_preserved(matcher):
    """Verify unmentioned reference points are recorded in unmatched_reference_relations."""
    r1 = DependencyRelation(
        subject="key",
        predicate="identifies",
        object="record",
        subject_lemma="key",
        predicate_lemma="identify",
        object_lemma="record",
        relation_type="SPO",
        source_dependency_relations=("nsubj", "dobj"),
        subject_index=0,
        predicate_index=1,
        object_index=2,
    )
    r2 = DependencyRelation(
        subject="database",
        predicate="enforces",
        object="uniqueness",
        subject_lemma="database",
        predicate_lemma="enforce",
        object_lemma="uniqueness",
        relation_type="SPO",
        source_dependency_relations=("nsubj", "dobj"),
        subject_index=3,
        predicate_index=4,
        object_index=5,
    )
    s1 = DependencyRelation(
        subject="key",
        predicate="identifies",
        object="record",
        subject_lemma="key",
        predicate_lemma="identify",
        object_lemma="record",
        relation_type="SPO",
        source_dependency_relations=("nsubj", "dobj"),
        subject_index=0,
        predicate_index=1,
        object_index=2,
    )

    result = matcher.match([r1, r2], [s1])
    assert result.matched_count == 1
    assert result.unmatched_reference_count == 1
    assert result.unmatched_reference_relations[0].subject == "database"


# 13. Unmatched student relations are returned
def test_unmatched_student_relations_preserved(matcher):
    """Verify additional student statements are recorded in unmatched_student_relations."""
    r1 = DependencyRelation(
        subject="key",
        predicate="identifies",
        object="record",
        subject_lemma="key",
        predicate_lemma="identify",
        object_lemma="record",
        relation_type="SPO",
        source_dependency_relations=("nsubj", "dobj"),
        subject_index=0,
        predicate_index=1,
        object_index=2,
    )
    s1 = DependencyRelation(
        subject="key",
        predicate="identifies",
        object="record",
        subject_lemma="key",
        predicate_lemma="identify",
        object_lemma="record",
        relation_type="SPO",
        source_dependency_relations=("nsubj", "dobj"),
        subject_index=0,
        predicate_index=1,
        object_index=2,
    )
    s_extra = DependencyRelation(
        subject="SQL",
        predicate="developed",
        object=None,
        subject_lemma="SQL",
        predicate_lemma="develop",
        object_lemma=None,
        relation_type="PASSIVE_SP",
        source_dependency_relations=("nsubjpass",),
        subject_index=3,
        predicate_index=4,
        object_index=None,
    )

    result = matcher.match([r1], [s1, s_extra])
    assert result.matched_count == 1
    assert result.unmatched_student_count == 1
    assert result.unmatched_student_relations[0].subject == "SQL"


# 14. No unmatched student relation is classified as correct/incorrect/irrelevant
def test_no_classification_of_unmatched_information(matcher):
    """Verify Stage 7 does NOT attach correctness or relevance classifications."""
    r1 = DependencyRelation(
        subject="key",
        predicate="identifies",
        object="record",
        subject_lemma="key",
        predicate_lemma="identify",
        object_lemma="record",
        relation_type="SPO",
        source_dependency_relations=("nsubj", "dobj"),
        subject_index=0,
        predicate_index=1,
        object_index=2,
    )
    s_extra = DependencyRelation(
        subject="key",
        predicate="contain",
        object="NULL",
        subject_lemma="key",
        predicate_lemma="contain",
        object_lemma="null",
        relation_type="SPO",
        source_dependency_relations=("nsubj", "dobj"),
        subject_index=3,
        predicate_index=4,
        object_index=5,
    )

    result = matcher.match([r1], [s_extra])
    assert result.unmatched_student_count == 1
    unmatched = result.unmatched_student_relations[0]

    # Verify absence of classification attributes
    assert not hasattr(unmatched, "classification")
    assert not hasattr(unmatched, "is_correct")
    assert not hasattr(unmatched, "is_irrelevant")
    assert not hasattr(unmatched, "misconception")


# 15. Empty reference relation set
def test_empty_reference_relation_set(matcher):
    """Verify matching with empty reference relation set produces all unmatched student."""
    s1 = DependencyRelation(
        subject="key",
        predicate="identifies",
        object="record",
        subject_lemma="key",
        predicate_lemma="identify",
        object_lemma="record",
        relation_type="SPO",
        source_dependency_relations=("nsubj", "dobj"),
        subject_index=0,
        predicate_index=1,
        object_index=2,
    )
    result = matcher.match([], [s1])
    assert result.matched_count == 0
    assert result.unmatched_reference_count == 0
    assert result.unmatched_student_count == 1


# 16. Empty student relation set
def test_empty_student_relation_set(matcher):
    """Verify matching with empty student relation set produces all unmatched reference."""
    r1 = DependencyRelation(
        subject="key",
        predicate="identifies",
        object="record",
        subject_lemma="key",
        predicate_lemma="identify",
        object_lemma="record",
        relation_type="SPO",
        source_dependency_relations=("nsubj", "dobj"),
        subject_index=0,
        predicate_index=1,
        object_index=2,
    )
    result = matcher.match([r1], [])
    assert result.matched_count == 0
    assert result.unmatched_reference_count == 1
    assert result.unmatched_student_count == 0


# 17. Both sets empty
def test_both_sets_empty(matcher):
    """Verify matching when both reference and student relation sets are empty."""
    result = matcher.match([], [])
    assert result.matched_count == 0
    assert result.unmatched_reference_count == 0
    assert result.unmatched_student_count == 0


# 18. Serialization works
def test_serialization(matcher):
    """Verify MatchingResult, MatchedRelation, and CandidateAlignment serialize to dict."""
    r1 = DependencyRelation(
        subject="key",
        predicate="identifies",
        object="record",
        subject_lemma="key",
        predicate_lemma="identify",
        object_lemma="record",
        relation_type="SPO",
        source_dependency_relations=("nsubj", "dobj"),
        subject_index=0,
        predicate_index=1,
        object_index=2,
    )
    s1 = DependencyRelation(
        subject="key",
        predicate="identifies",
        object="record",
        subject_lemma="key",
        predicate_lemma="identify",
        object_lemma="record",
        relation_type="SPO",
        source_dependency_relations=("nsubj", "dobj"),
        subject_index=0,
        predicate_index=1,
        object_index=2,
    )

    result = matcher.match([r1], [s1])
    data = result.to_dict()

    expected_keys = {
        "matched_relations",
        "unmatched_reference_relations",
        "unmatched_student_relations",
        "candidate_alignments",
        "config",
        "matched_count",
        "unmatched_reference_count",
        "unmatched_student_count",
    }
    assert expected_keys.issubset(data.keys())
    assert len(data["matched_relations"]) == 1
    assert data["matched_relations"][0]["match_method"] == "exact_triple"


# 19. Stage 5 representations are consumed directly
def test_consume_stage5_pipeline_objects(parser, extractor, matcher):
    """Verify SentenceTriples and DocumentTriples from Stage 5 can be passed directly."""
    ref_doc = parser.parse("A primary key uniquely identifies each record in a table.")
    stu_doc = parser.parse("A primary key uniquely identifies every row in a table.")

    ref_triples = extractor.extract_document(ref_doc)
    stu_triples = extractor.extract_document(stu_doc)

    # Pass DocumentTriples directly to TripleMatcher.match()
    result = matcher.match(ref_triples, stu_triples)
    assert result.matched_count == 1
    matched = result.matched_relations[0]
    assert matched.reference_relation.object == "record"
    assert matched.student_relation.object == "row"


# 20. Stage 6 semantic evidence is consumed rather than recomputed
def test_stage6_evidence_preserved_in_matched_relation(matcher):
    """Verify slot_evidence contains rich Stage 6 SemanticRelation objects."""
    r1 = DependencyRelation(
        subject="key",
        predicate="identifies",
        object="record",
        subject_lemma="key",
        predicate_lemma="identify",
        object_lemma="record",
        relation_type="SPO",
        source_dependency_relations=("nsubj", "dobj"),
        subject_index=0,
        predicate_index=1,
        object_index=2,
    )
    s1 = DependencyRelation(
        subject="key",
        predicate="identifies",
        object="row",
        subject_lemma="key",
        predicate_lemma="identify",
        object_lemma="row",
        relation_type="SPO",
        source_dependency_relations=("nsubj", "dobj"),
        subject_index=0,
        predicate_index=1,
        object_index=2,
    )

    result = matcher.match([r1], [s1])
    evidence = result.matched_relations[0].slot_evidence

    assert "subject" in evidence
    assert "predicate" in evidence
    assert "object" in evidence

    assert evidence["subject"].method == "exact_match"
    assert evidence["predicate"].method == "exact_match"
    assert evidence["object"].method == "wordnet_path"
    assert evidence["object"].synset_source == "record.n.04"
    assert evidence["object"].synset_target == "quarrel.n.01"


# 21. No whole-sentence cosine similarity or grading in Stage 7
def test_no_cosine_similarity_or_grading_in_stage_7(matcher):
    """Verify TripleMatcher has no sentence-level cosine similarity or grading methods."""
    assert not hasattr(matcher, "compute_cosine_similarity")
    assert not hasattr(matcher, "grade")
    assert not hasattr(matcher, "calculate_score")
    assert not hasattr(matcher, "evaluate_entailment")


# 22. Input validation for matcher and match method
def test_input_validation(matcher):
    """Verify invalid weights and types raise ValueError / TypeError."""
    with pytest.raises(ValueError):
        TripleMatcher(subject_weight=-0.1)

    with pytest.raises(ValueError):
        TripleMatcher(subject_weight=0, predicate_weight=0, object_weight=0)

    with pytest.raises(ValueError):
        TripleMatcher(alignment_threshold=1.5)

    with pytest.raises(TypeError):
        matcher.match(None, [])

    with pytest.raises(TypeError):
        matcher.match([], None)

    with pytest.raises(TypeError):
        matcher.match(["invalid_string_element"], [])
