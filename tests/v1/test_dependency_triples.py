"""
Unit tests for the Base ASAG Stage 5 Dependency Triples Component.

Covers:
1. Raw dependency arcs are generated.
2. Governor/dependent information is preserved in arcs.
3. Dependency relation labels are preserved.
4. Lemmas are retained in arcs and relations.
5. A simple active sentence produces a canonical relation (e.g. key, identifies, record).
6. Modifiers (e.g. advmod 'uniquely') do NOT become false objects.
7. Prepositional relations remain represented without unsafe semantic collapsing.
8. Multiple relations can be extracted from one sentence.
9. Multiple sentences are handled separately.
10. Empty input handling.
11. Serialization works.
12. Confirms that Stage 5 does NOT perform semantic synonym matching (e.g. record != row).
13. Passive voice handling (with agent and agentless).
"""

import pytest
from base_asag.dependency import (
    DependencyArc,
    DependencyParser,
    DependencyRelation,
    DependencyTripleExtractor,
    DocumentTriples,
    ParsedDocument,
    ParsedSentence,
    SentenceTriples,
)


@pytest.fixture(scope="module")
def parser():
    """Provides a shared DependencyParser instance."""
    return DependencyParser(model_name="en_core_web_sm")


@pytest.fixture(scope="module")
def extractor():
    """Provides a shared DependencyTripleExtractor instance."""
    return DependencyTripleExtractor()


# 1. Raw dependency arcs are generated
def test_raw_dependency_arcs_generated(parser, extractor):
    """Verify raw dependency arcs are generated for all non-root tokens."""
    text = "The key identifies the record."
    sent = parser.parse_sentence(text)
    triples = extractor.extract(sent)

    assert isinstance(triples, SentenceTriples)
    # 5 tokens ('The', 'key', 'identifies', 'the', 'record', '.') -> 6 tokens including '.'
    # Root is 'identifies'. There should be 5 non-root tokens -> 5 raw arcs.
    assert triples.arc_count == sent.token_count - 1
    assert all(isinstance(arc, DependencyArc) for arc in triples.raw_arcs)


# 2. Governor/dependent information is preserved
def test_governor_dependent_preserved(parser, extractor):
    """Verify governor and dependent texts and indices are accurately recorded."""
    text = "The key identifies the record."
    sent = parser.parse_sentence(text)
    triples = extractor.extract(sent)

    # Find the nsubj arc
    nsubj_arc = next(arc for arc in triples.raw_arcs if arc.relation == "nsubj")
    assert nsubj_arc.governor_text == "identifies"
    assert nsubj_arc.dependent_text == "key"
    assert nsubj_arc.governor_pos == "VERB"
    assert 0 <= nsubj_arc.governor_index < sent.token_count
    assert 0 <= nsubj_arc.dependent_index < sent.token_count


# 3. Dependency relation labels are preserved
def test_dependency_relation_labels_preserved(parser, extractor):
    """Verify all raw dependency relation labels from Stage 4 are preserved intact."""
    text = "A primary key uniquely identifies each record in a table."
    sent = parser.parse_sentence(text)
    triples = extractor.extract(sent)

    arc_relations = {arc.relation for arc in triples.raw_arcs}
    expected_relations = {"det", "amod", "nsubj", "advmod", "dobj", "prep", "pobj", "punct"}
    for rel in expected_relations:
        assert rel in arc_relations


# 4. Lemmas are retained
def test_lemmas_retained_in_arcs_and_relations(parser, extractor):
    """Verify base lemmas are retained alongside surface strings."""
    text = "The keys identified the records."
    sent = parser.parse_sentence(text)
    triples = extractor.extract(sent)

    # Verify arc lemmas
    nsubj_arc = next(arc for arc in triples.raw_arcs if arc.relation == "nsubj")
    assert nsubj_arc.governor_lemma == "identify"
    assert nsubj_arc.dependent_lemma == "key"

    # Verify canonical relation lemmas
    assert triples.relation_count >= 1
    rel = triples.canonical_relations[0]
    assert rel.predicate == "identified"
    assert rel.predicate_lemma == "identify"
    assert rel.subject_lemma == "key"
    assert rel.object_lemma == "record"


# 5. Simple active sentence produces a canonical relation (key, identifies, record)
def test_canonical_active_spo_relation(parser, extractor):
    """Verify active transitive clause extracts (subject, predicate, object)."""
    text = "The key identifies the record."
    sent = parser.parse_sentence(text)
    triples = extractor.extract(sent)

    assert triples.relation_count == 1
    rel = triples.canonical_relations[0]

    assert isinstance(rel, DependencyRelation)
    assert rel.relation_type == "SPO"
    assert rel.subject == "key"
    assert rel.predicate == "identifies"
    assert rel.object == "record"
    assert rel.to_tuple() == ("key", "identifies", "record")
    assert rel.to_lemma_tuple() == ("key", "identify", "record")


# 6. Modifiers do not become false objects
def test_modifiers_do_not_become_false_objects(parser, extractor):
    """Verify adverbial and adjectival modifiers are not mistakenly extracted as objects."""
    text = "The key uniquely identifies the record."
    sent = parser.parse_sentence(text)
    triples = extractor.extract(sent)

    assert triples.relation_count == 1
    rel = triples.canonical_relations[0]

    # Object must be 'record', NEVER 'uniquely'
    assert rel.object == "record"
    assert rel.object != "uniquely"

    # 'uniquely' remains represented in raw arcs
    advmod_arc = next((arc for arc in triples.raw_arcs if arc.relation == "advmod"), None)
    assert advmod_arc is not None
    assert advmod_arc.dependent_text == "uniquely"
    assert advmod_arc.governor_text == "identifies"


# 7. Prepositional relations remain represented without unsafe semantic collapsing
def test_prepositional_relations_not_collapsed(parser, extractor):
    """
    Verify prepositional phrases (in a table) are preserved as raw arcs
    and NOT improperly collapsed into an invented triple (key, identifies, table).
    """
    text = "A primary key uniquely identifies each record in a table."
    sent = parser.parse_sentence(text)
    triples = extractor.extract(sent)

    # Canonical relation must be (key, identifies, record)
    assert triples.relation_count == 1
    rel = triples.canonical_relations[0]
    assert rel.subject == "key"
    assert rel.predicate == "identifies"
    assert rel.object == "record"

    # Ensure NO canonical relation states (key, identifies, table)
    for r in triples.canonical_relations:
        assert r.object != "table"

    # Prepositional relations must be present in raw arcs
    prep_arc = next(arc for arc in triples.raw_arcs if arc.relation == "prep")
    assert prep_arc.governor_text == "identifies"
    assert prep_arc.dependent_text == "in"

    pobj_arc = next(arc for arc in triples.raw_arcs if arc.relation == "pobj")
    assert pobj_arc.governor_text == "in"
    assert pobj_arc.dependent_text == "table"


# 8. Multiple relations can be extracted from one sentence
def test_multiple_relations_extracted(parser, extractor):
    """Verify a sentence with coordinate clauses extracts multiple canonical relations."""
    text = "The teacher explained the lesson and the student solved the problem."
    sent = parser.parse_sentence(text)
    triples = extractor.extract(sent)

    assert triples.relation_count == 2
    tuples = [r.to_tuple() for r in triples.canonical_relations]

    assert ("teacher", "explained", "lesson") in tuples
    assert ("student", "solved", "problem") in tuples


# 9. Multiple sentences are handled separately
def test_multiple_sentences_handled_separately(parser, extractor):
    """Verify multi-sentence documents maintain sentence separation with distinct triples."""
    text = "A primary key uniquely identifies each record in a table. SQL was developed in the 1970s."
    doc = parser.parse_document(text)
    doc_triples = extractor.extract_document(doc)

    assert isinstance(doc_triples, DocumentTriples)
    assert doc_triples.sentence_count == 2

    s1_triples = doc_triples.sentences[0]
    s2_triples = doc_triples.sentences[1]

    assert s1_triples.relation_count == 1
    assert s1_triples.canonical_relations[0].to_tuple() == ("key", "identifies", "record")

    assert s2_triples.relation_count == 1
    assert s2_triples.canonical_relations[0].subject == "SQL"
    assert s2_triples.canonical_relations[0].predicate == "developed"


# 10. Empty input handling
def test_empty_input_handling(extractor):
    """Verify empty ParsedSentence and ParsedDocument yield empty triple containers."""
    empty_sent = ParsedSentence(original_text="", normalized_text="", tokens=[])
    triples = extractor.extract(empty_sent)
    assert triples.arc_count == 0
    assert triples.relation_count == 0

    empty_doc = ParsedDocument(original_text="", normalized_text="", sentences=[])
    doc_triples = extractor.extract_document(empty_doc)
    assert doc_triples.sentence_count == 0
    assert len(doc_triples.raw_arcs) == 0

    # Invalid type
    with pytest.raises(TypeError):
        extractor.extract("raw string not allowed")


# 11. Serialization works
def test_serialization(parser, extractor):
    """Verify SentenceTriples and DocumentTriples serialize cleanly to dictionaries."""
    text = "A primary key uniquely identifies each record in a table."
    sent = parser.parse_sentence(text)
    triples = extractor.extract(sent)
    data = triples.to_dict()

    assert data["sentence_text"] == text
    assert data["arc_count"] == triples.arc_count
    assert data["relation_count"] == triples.relation_count
    assert "raw_arcs" in data
    assert "canonical_relations" in data
    assert data["canonical_relations"][0]["subject"] == "key"


# 12. Confirms that Stage 5 does NOT perform semantic synonym matching
def test_no_synonym_matching_in_stage_5(parser, extractor):
    """
    Stage 5 must NOT equate synonyms like 'record' and 'row'.
    Semantic mapping is strictly deferred to Stage 6 (WordNet / Semantic Relations).
    """
    ref_sent = parser.parse_sentence("A primary key uniquely identifies each record in a table.")
    stu_sent = parser.parse_sentence("A primary key uniquely identifies every row in a table.")

    ref_triples = extractor.extract(ref_sent)
    stu_triples = extractor.extract(stu_sent)

    ref_rel = ref_triples.canonical_relations[0]
    stu_rel = stu_triples.canonical_relations[0]

    assert ref_rel.predicate_lemma == stu_rel.predicate_lemma == "identify"
    assert ref_rel.subject_lemma == stu_rel.subject_lemma == "key"

    # Strictly verify that 'record' and 'row' remain UNMATCHED and DISTINCT in Stage 5
    assert ref_rel.object != stu_rel.object
    assert ref_rel.object_lemma != stu_rel.object_lemma
    assert ref_rel.object_lemma == "record"
    assert stu_rel.object_lemma == "row"


# 13. Passive voice handling
def test_passive_voice_handling(parser, extractor):
    """Verify passive constructions with agent and agentless are handled safely."""
    # Passive with explicit agent: 'The record is identified by the key.'
    sent_with_agent = parser.parse_sentence("The record is identified by the key.")
    triples_agent = extractor.extract(sent_with_agent)

    assert triples_agent.relation_count == 1
    rel_agent = triples_agent.canonical_relations[0]
    assert rel_agent.relation_type == "PASSIVE_SPO"
    assert rel_agent.subject == "key"
    assert rel_agent.predicate == "identified"
    assert rel_agent.object == "record"
    assert rel_agent.to_lemma_tuple() == ("key", "identify", "record")

    # Agentless passive: 'SQL was developed in the 1970s.'
    sent_agentless = parser.parse_sentence("SQL was developed in the 1970s.")
    triples_agentless = extractor.extract(sent_agentless)

    assert triples_agentless.relation_count == 1
    rel_agentless = triples_agentless.canonical_relations[0]
    assert rel_agentless.relation_type == "PASSIVE_SP"
    assert rel_agentless.subject == "SQL"
    assert rel_agentless.predicate == "developed"
    assert rel_agentless.object is None


# 14. Compiler sentence proposition extraction regression tests (Stage 10A)
def test_compiler_sentences_canonical_propositions(parser, extractor):
    """
    Verify canonical proposition extraction across the compiler validation sentences:
    a. 'A compiler converts high-level source code into machine code.' -> ('compiler', 'converts', 'code')
    b. 'A compiler converts programs written in a high-level language into machine code.'
       -> ('compiler', 'converts', 'programs'), ('programs', 'written', None)
    c. 'A compiler translates high-level source code into machine code.' -> ('compiler', 'translates', 'code')
    """
    # Case c: Reference sentence
    ref_sent = parser.parse_sentence("A compiler translates high-level source code into machine code.")
    ref_triples = extractor.extract(ref_sent)
    assert len(ref_triples.canonical_relations) == 1
    ref_rel = ref_triples.canonical_relations[0]
    assert ref_rel.to_tuple() == ("compiler", "translates", "code")
    assert ref_rel.to_lemma_tuple() == ("compiler", "translate", "code")

    # Case a: Simple student paraphrase with intervening modifiers
    stu_simple_sent = parser.parse_sentence("A compiler converts high-level source code into machine code.")
    stu_simple_triples = extractor.extract(stu_simple_sent)
    assert len(stu_simple_triples.canonical_relations) == 1
    stu_simple_rel = stu_simple_triples.canonical_relations[0]
    assert stu_simple_rel.to_tuple() == ("compiler", "converts", "code")
    assert stu_simple_rel.to_lemma_tuple() == ("compiler", "convert", "code")

    # Case b: Complex student paraphrase with participial modifier
    stu_complex_sent = parser.parse_sentence(
        "A compiler converts programs written in a high-level language into machine code."
    )
    stu_complex_triples = extractor.extract(stu_complex_sent)
    assert len(stu_complex_triples.canonical_relations) == 2
    tuples = [r.to_tuple() for r in stu_complex_triples.canonical_relations]
    assert ("compiler", "converts", "programs") in tuples
    assert ("programs", "written", None) in tuples

