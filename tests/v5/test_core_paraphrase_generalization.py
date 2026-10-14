"""
Controlled Synthetic Paraphrase Generalization Test Suite (Task 2).

Systematic regression suite for generalized core paraphrase recovery across:
1. Synonyms and morphological variants
2. Active and passive voice diathesis alternations
3. Copula-adjective versus verbal predicate constructions
4. Preposition equivalence classes (inside <=> within, with <=> using, on <=> in)
5. Clause reordering
6. Nominalization and verbalization (light-verb constructions)
7. Conjunctions and coordinated clauses
8. Domain-specific terminology (pop <=> remove, table <=> relation, item <=> element)
9. Negative contrast (antonyms and conflicting prepositional arguments)
10. Negated paraphrases preserving polarity guards
"""

import pytest

from base_asag.dependency.parser import DependencyParser
from base_asag.representation.hybrid import RobustPropositionExtractor
from proposed_asag.pipeline_v5 import Experiment5Pipeline
from proposed_asag.proposition.canonical_reference import CanonicalReferenceExtractor
from proposed_asag.proposition.core_recovery.core_paraphrase_recovery import (
    CoreParaphraseRecoverer,
)


@pytest.fixture(scope="module")
def parser():
    return DependencyParser()


@pytest.fixture(scope="module")
def extractor():
    return CanonicalReferenceExtractor()


@pytest.fixture(scope="module")
def recoverer():
    return CoreParaphraseRecoverer()


@pytest.fixture(scope="module")
def pipeline():
    return Experiment5Pipeline()


# =========================================================================
# 1. Nominalization and Verbalization (Light-Verb Bridges)
# =========================================================================

def test_nominalization_storage_to_stores(parser, extractor, recoverer):
    """'provides storage of elements' <=> 'stores elements'."""
    p_ref = extractor.extract_document(parser.parse("An array stores elements."))[0]
    p_stu = extractor.extract_document(parser.parse("An array provides storage of elements."))[0]

    score, reason, evidence = recoverer._evaluate_paraphrase_evidence(p_stu, p_ref, "")
    assert score >= 0.55
    assert reason == "NOMINALIZATION_VERBALIZATION_BRIDGE"
    assert evidence["nominal_source"] == "storage"
    assert evidence["verbal_target"] == "store"
    assert evidence["derivational_similarity"] >= 0.85


def test_nominalization_allocation_to_allocates(parser, extractor, recoverer):
    """'performs allocation of memory' <=> 'allocates memory'."""
    p_ref = extractor.extract_document(parser.parse("The function allocates memory."))[0]
    p_stu = extractor.extract_document(parser.parse("The function performs allocation of memory."))[0]

    score, reason, evidence = recoverer._evaluate_paraphrase_evidence(p_stu, p_ref, "")
    assert score >= 0.55
    assert reason == "NOMINALIZATION_VERBALIZATION_BRIDGE"
    assert evidence["nominal_source"] == "allocation"
    assert evidence["verbal_target"] == "allocate"


def test_nominalization_pipeline_grading(pipeline):
    """End-to-end grading with nominalization paraphrase."""
    q = "What is the primary function of an array?"
    ref = "An array stores elements in contiguous memory."
    stu = "An array provides storage of elements in contiguous memory."

    res = pipeline.evaluate(q, ref, stu)
    assert res.final_grade >= 4.0
    assert res.recovered_core_count >= 1


# =========================================================================
# 2. Active-Passive Voice Diathesis Alternation
# =========================================================================

def test_active_student_passive_reference(parser, extractor, recoverer):
    """'The programmer allocates dynamic memory on the heap' <=> 'Dynamic memory is allocated on the heap'."""
    p_ref = extractor.extract_document(parser.parse("Dynamic memory is allocated on the heap."))[0]
    p_stu = extractor.extract_document(parser.parse("The programmer allocates dynamic memory on the heap."))[0]

    score, reason, evidence = recoverer._evaluate_paraphrase_evidence(p_stu, p_ref, "")
    assert score >= 0.55
    assert reason == "VOICE_ALTERNATION_BRIDGE"
    assert evidence["voice_direction"] == "active_student_passive_ref"
    assert evidence["is_generic_agent"] is True
    assert evidence["patient_similarity"] >= 0.80


def test_passive_student_active_reference(parser, extractor, recoverer):
    """'Source code is optimized during compilation' <=> 'The compiler optimizes source code during compilation'."""
    p_ref = extractor.extract_document(parser.parse("The compiler optimizes source code."))[0]
    p_stu = extractor.extract_document(parser.parse("Source code is optimized."))[0]

    score, reason, evidence = recoverer._evaluate_paraphrase_evidence(p_stu, p_ref, "")
    assert score >= 0.55
    assert reason == "VOICE_ALTERNATION_BRIDGE"
    assert evidence["voice_direction"] == "passive_student_active_ref"


def test_active_passive_pipeline_grading(pipeline):
    """End-to-end grading with active-passive diathesis alternation."""
    q = "Where is dynamic memory allocated?"
    ref = "Dynamic memory is allocated on the heap."
    stu = "The programmer allocates dynamic memory on the heap."

    res = pipeline.evaluate(q, ref, stu)
    assert res.final_grade >= 4.0
    assert res.recovered_core_count >= 1


# =========================================================================
# 3. Preposition Equivalence Classes
# =========================================================================

def test_preposition_equivalence_inside_within(recoverer):
    """'inside' and 'within' belong to the locative-containment equivalence class."""
    assert recoverer._are_preps_equivalent("inside", "within") is True
    assert recoverer._are_preps_equivalent("within", "in") is True
    assert recoverer._are_preps_equivalent("into", "in") is True


def test_preposition_equivalence_using_with(recoverer):
    """'using' and 'with' belong to the instrumental equivalence class."""
    assert recoverer._are_preps_equivalent("using", "with") is True
    assert recoverer._are_preps_equivalent("by", "via") is True
    assert recoverer._are_preps_equivalent("through", "with") is True


def test_preposition_non_equivalence(recoverer):
    """Distinct functional roles (e.g. locative vs directional outward) are not equivalent."""
    assert recoverer._are_preps_equivalent("inside", "outside") is False
    assert recoverer._are_preps_equivalent("to", "from") is False


# =========================================================================
# 4. Copula-Adjective to Verb Alternation
# =========================================================================

def test_copula_adjective_to_verb_bridge(parser, extractor, recoverer):
    """'A local variable is accessible inside the function' <=> 'can be accessed inside the function'."""
    p_ref = extractor.extract_document(parser.parse("A local variable is accessible within the function."))[0]
    p_stu = extractor.extract_document(parser.parse("A local variable can be accessed inside the function."))[0]

    score, reason, evidence = recoverer._evaluate_paraphrase_evidence(p_stu, p_ref, "")
    assert score >= 0.55
    assert reason == "COPULA_ADJECTIVE_VERB_BRIDGE"
    assert evidence["copula_adjective"] == "accessible"
    assert evidence["verbal_predicate"] == "access"


def test_copula_adjective_pipeline_example_b(pipeline):
    """Full Example B evaluation: copula adjective, scope noun, conjoined clauses."""
    q = "What is the scope of a local variable in a function?"
    ref = "A local variable is accessible only within the function or block in which it is declared."
    stu = "A local variable has local scope and can only be accessed inside the specific block or function where it is defined."

    res = pipeline.evaluate(q, ref, stu)
    assert res.final_grade >= 4.0
    assert res.recovered_core_count >= 1


# =========================================================================
# 5. Clause Reordering
# =========================================================================

def test_clause_reordering_evaluation(pipeline):
    """Reordered clauses retain core proposition alignment."""
    q = "Where can a local variable be accessed?"
    ref = "A local variable is accessible within the function where it is declared."
    stu = "Within the function where it is declared, a local variable is accessible."

    res = pipeline.evaluate(q, ref, stu)
    assert res.final_grade >= 4.0


# =========================================================================
# 6. Domain-Specific Terminology
# =========================================================================

def test_domain_lexicon_pop_removes(pipeline):
    """Pop <=> remove and item <=> element in stack context."""
    q = "What does the pop operation do on a stack?"
    ref = "A pop operation removes an element from the stack."
    stu = "A pop operation pops an item from the stack."

    res = pipeline.evaluate(q, ref, stu)
    assert res.final_grade >= 4.0


def test_domain_lexicon_table_relation(parser, extractor, recoverer):
    """table <=> relation and column <=> attribute in relational context."""
    p_ref = extractor.extract_document(parser.parse("A table stores records."))[0]
    p_stu = extractor.extract_document(parser.parse("A relation stores records."))[0]

    score, reason, _ = recoverer._evaluate_paraphrase_evidence(p_stu, p_ref, "")
    assert score >= 0.70
    assert reason == "SLOT_ALIGNMENT_RECOVERY"


# =========================================================================
# 7. Negative Contrast (False Friends, Antonyms, Prep Conflicts)
# =========================================================================

def test_negative_contrast_antonym_predicates(parser, extractor, recoverer):
    """'allocates' vs 'deallocates' must NOT be accepted as a core paraphrase."""
    p_ref = extractor.extract_document(parser.parse("The program deallocates memory."))[0]
    p_stu = extractor.extract_document(parser.parse("The program allocates memory."))[0]

    score, reason, evidence = recoverer._evaluate_paraphrase_evidence(p_stu, p_ref, "")
    assert score < 0.55
    assert evidence.get("reason") == "PREDICATE_INCOMPATIBLE"


def test_negative_contrast_antonym_pipeline(pipeline):
    """Antonymous predicate statement receives zero credit."""
    q = "What does free do in C?"
    ref = "The program deallocates memory on the heap."
    stu = "The program allocates memory on the heap."

    res = pipeline.evaluate(q, ref, stu)
    assert res.final_grade == 0.0


def test_negative_contrast_prep_argument_conflict(parser, extractor, recoverer):
    """'adds an element to the queue' vs 'to the stack' must be rejected due to prep arg conflict."""
    p_ref = extractor.extract_document(parser.parse("Push adds an element to the stack."))[0]
    p_stu = extractor.extract_document(parser.parse("Push adds an element to the queue."))[0]

    score, reason, evidence = recoverer._evaluate_paraphrase_evidence(p_stu, p_ref, "")
    assert score < 0.55
    assert evidence.get("reason") == "PREPOSITIONAL_ARGUMENT_CONFLICT"


def test_negative_contrast_prep_conflict_pipeline(pipeline):
    """Conflicting preposition argument causes contradiction / zero score."""
    q = "What does push do in a stack?"
    ref = "Push adds an element to the stack."
    stu = "Push adds an element to the queue."

    res = pipeline.evaluate(q, ref, stu)
    assert res.final_grade == 0.0


# =========================================================================
# 8. Negation and Contradiction Guards
# =========================================================================

def test_polarity_conflict_gate(parser, extractor, recoverer):
    """Opposite polarities are immediately blocked by the polarity gate."""
    p_ref = extractor.extract_document(parser.parse("A primary key uniquely identifies each record in a table."))[0]
    p_stu = extractor.extract_document(parser.parse("A primary key never identifies each record in a table."))[0]

    score, reason, evidence = recoverer._evaluate_paraphrase_evidence(p_stu, p_ref, "")
    assert score == 0.0
    assert reason == "POLARITY_MISMATCH"
    assert "conflict" in evidence["reason"].lower()


def test_example_a_contradiction_pipeline(pipeline):
    """Example A receives 0.0/5.0 due to explicit negation contradiction."""
    q = "What is the purpose of a primary key in a relational database?"
    ref = "A primary key uniquely identifies each record in a table."
    stu = "A primary key never identifies each record in a table."

    res = pipeline.evaluate(q, ref, stu)
    assert res.final_grade == 0.0


def test_matching_negated_paraphrases(parser, extractor, recoverer):
    """Both negative polarities expressing the same meaning are valid paraphrases."""
    p_ref = extractor.extract_document(parser.parse("A local variable cannot be accessed outside the block."))[0]
    p_stu = extractor.extract_document(parser.parse("A local variable is not accessible outside the block."))[0]

    score, reason, _ = recoverer._evaluate_paraphrase_evidence(p_stu, p_ref, "")
    assert score >= 0.55
    assert reason == "COPULA_ADJECTIVE_VERB_BRIDGE"
