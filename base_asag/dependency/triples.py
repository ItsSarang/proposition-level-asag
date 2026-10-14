"""
Dependency Triples and Relational Structures for Base ASAG.

This module provides the Stage 5 component for the Base ASAG system. It converts
the Stage 4 syntactic dependency tree (ParsedSentence / ParsedDocument) into two
complementary representations:

1. RAW DEPENDENCY ARCS:
   Direct parser governor-dependent relationships: (governor, relation, dependent).
   Preserves complete syntactic context (modifiers, prepositions, determiners, punctuation).

2. ASAG-ORIENTED CANONICAL RELATIONS:
   Syntactically grounded clause-level relations: (subject, predicate, object).
   Extracted strictly from verified dependency paths without speculative collapsing.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from base_asag.dependency.parser import (
    ParsedDocument,
    ParsedSentence,
    ParsedToken,
)


@dataclass(frozen=True)
class DependencyArc:
    """
    Direct directed arc in the syntactic dependency tree:
    (governor, dependency_relation, dependent).

    Attributes
    ----------
    governor_text : str
        Surface form of the governing head token.
    governor_lemma : str
        Lemmatized base form of the governing head token.
    governor_pos : str
        Coarse Universal POS tag of the governor.
    governor_index : int
        Sentence-relative index of the governor token.
    relation : str
        Grammatical dependency relation label (e.g. nsubj, dobj, prep, pobj).
    dependent_text : str
        Surface form of the dependent token.
    dependent_lemma : str
        Lemmatized base form of the dependent token.
    dependent_pos : str
        Coarse Universal POS tag of the dependent.
    dependent_index : int
        Sentence-relative index of the dependent token.
    """
    governor_text: str
    governor_lemma: str
    governor_pos: str
    governor_index: int
    relation: str
    dependent_text: str
    dependent_lemma: str
    dependent_pos: str
    dependent_index: int

    def to_tuple(self) -> Tuple[str, str, str]:
        """Return (governor_text, relation, dependent_text)."""
        return (self.governor_text, self.relation, self.dependent_text)

    def to_lemma_tuple(self) -> Tuple[str, str, str]:
        """Return (governor_lemma, relation, dependent_lemma)."""
        return (self.governor_lemma, self.relation, self.dependent_lemma)

    def to_dict(self) -> Dict[str, Any]:
        """Return dictionary representation of the arc."""
        return {
            "governor_text": self.governor_text,
            "governor_lemma": self.governor_lemma,
            "governor_pos": self.governor_pos,
            "governor_index": self.governor_index,
            "relation": self.relation,
            "dependent_text": self.dependent_text,
            "dependent_lemma": self.dependent_lemma,
            "dependent_pos": self.dependent_pos,
            "dependent_index": self.dependent_index,
        }


@dataclass(frozen=True)
class DependencyRelation:
    """
    ASAG-oriented relational structure representing a clause relation
    such as (subject, predicate, object).

    Attributes
    ----------
    subject : str
        Surface form of the subject.
    predicate : str
        Surface form of the predicate (verb).
    object : Optional[str]
        Surface form of the object, or None if intransitive.
    subject_lemma : str
        Lemmatized form of the subject.
    predicate_lemma : str
        Lemmatized form of the predicate.
    object_lemma : Optional[str]
        Lemmatized form of the object, or None if intransitive.
    relation_type : str
        Category of relation: "SPO", "SP", "PASSIVE_SPO", or "PASSIVE_SP".
    source_dependency_relations : Tuple[str, ...]
        The underlying dependency relations supporting this structure.
    subject_index : int
        Sentence-relative index of the subject token.
    predicate_index : int
        Sentence-relative index of the predicate token.
    object_index : Optional[int]
        Sentence-relative index of the object token, or None.
    """
    subject: str
    predicate: str
    object: Optional[str]
    subject_lemma: str
    predicate_lemma: str
    object_lemma: Optional[str]
    relation_type: str
    source_dependency_relations: Tuple[str, ...]
    subject_index: int
    predicate_index: int
    object_index: Optional[int] = None
    indirect_object: Optional[str] = None
    indirect_object_lemma: Optional[str] = None
    prepositional_arguments: Tuple[Tuple[str, str], ...] = ()
    predicate_modifiers: Tuple[str, ...] = ()
    subject_modifiers: Tuple[str, ...] = ()
    object_modifiers: Tuple[str, ...] = ()

    def to_tuple(self) -> Tuple[str, str, Optional[str]]:
        """Return (subject, predicate, object)."""
        return (self.subject, self.predicate, self.object)

    def to_lemma_tuple(self) -> Tuple[str, str, Optional[str]]:
        """Return (subject_lemma, predicate_lemma, object_lemma)."""
        return (self.subject_lemma, self.predicate_lemma, self.object_lemma)

    def to_dict(self) -> Dict[str, Any]:
        """Return dictionary representation of the relation."""
        d: Dict[str, Any] = {
            "subject": self.subject,
            "predicate": self.predicate,
            "object": self.object,
            "subject_lemma": self.subject_lemma,
            "predicate_lemma": self.predicate_lemma,
            "object_lemma": self.object_lemma,
            "relation_type": self.relation_type,
            "source_dependency_relations": list(self.source_dependency_relations),
            "subject_index": self.subject_index,
            "predicate_index": self.predicate_index,
            "object_index": self.object_index,
        }
        if self.indirect_object is not None:
            d["indirect_object"] = self.indirect_object
            d["indirect_object_lemma"] = self.indirect_object_lemma
        if self.prepositional_arguments:
            d["prepositional_arguments"] = [list(item) for item in self.prepositional_arguments]
        if self.predicate_modifiers:
            d["predicate_modifiers"] = list(self.predicate_modifiers)
        if self.subject_modifiers:
            d["subject_modifiers"] = list(self.subject_modifiers)
        if self.object_modifiers:
            d["object_modifiers"] = list(self.object_modifiers)
        return d


@dataclass
class SentenceTriples:
    """
    Container for all dependency structures extracted from a single ParsedSentence.

    Attributes
    ----------
    sentence_text : str
        Raw original sentence text.
    normalized_text : str
        Normalized sentence text.
    raw_arcs : List[DependencyArc]
        Complete list of directed (governor, relation, dependent) dependency arcs.
    canonical_relations : List[DependencyRelation]
        List of clause-level ASAG relations (subject, predicate, object).
    """
    sentence_text: str
    normalized_text: str
    raw_arcs: List[DependencyArc]
    canonical_relations: List[DependencyRelation]

    @property
    def arc_count(self) -> int:
        """Total number of raw dependency arcs."""
        return len(self.raw_arcs)

    @property
    def relation_count(self) -> int:
        """Total number of canonical relations."""
        return len(self.canonical_relations)

    def to_dict(self) -> Dict[str, Any]:
        """Convert sentence triples to a dictionary."""
        return {
            "sentence_text": self.sentence_text,
            "normalized_text": self.normalized_text,
            "arc_count": self.arc_count,
            "relation_count": self.relation_count,
            "raw_arcs": [arc.to_dict() for arc in self.raw_arcs],
            "canonical_relations": [rel.to_dict() for rel in self.canonical_relations],
        }


@dataclass
class DocumentTriples:
    """
    Container for all dependency structures extracted across a ParsedDocument.

    Attributes
    ----------
    document_text : str
        Raw original document text.
    sentences : List[SentenceTriples]
        List of SentenceTriples for each sentence in the document.
    """
    document_text: str
    sentences: List[SentenceTriples]

    @property
    def raw_arcs(self) -> List[DependencyArc]:
        """Flattened list of all raw dependency arcs across all sentences."""
        return [arc for sent in self.sentences for arc in sent.raw_arcs]

    @property
    def canonical_relations(self) -> List[DependencyRelation]:
        """Flattened list of all canonical relations across all sentences."""
        return [rel for sent in self.sentences for rel in sent.canonical_relations]

    @property
    def sentence_count(self) -> int:
        """Number of sentences in the document."""
        return len(self.sentences)

    def to_dict(self) -> Dict[str, Any]:
        """Convert document triples to a dictionary."""
        return {
            "document_text": self.document_text,
            "sentence_count": self.sentence_count,
            "sentences": [s.to_dict() for s in self.sentences],
            "raw_arcs": [a.to_dict() for a in self.raw_arcs],
            "canonical_relations": [r.to_dict() for r in self.canonical_relations],
        }


def _collect_prep_arguments(
    parsed_sentence: ParsedSentence,
    head_tok: ParsedToken,
    visited: Optional[Set[int]] = None,
    depth: int = 0,
) -> List[Tuple[str, str]]:
    """
    Collect prepositional arguments (prep_lemma, pobj_lemma) attached to head_tok
    and nested prepositional chains up to depth 3.
    """
    if visited is None:
        visited = set()
    if head_tok.index in visited or depth > 3:
        return []
    visited.add(head_tok.index)

    prep_args: List[Tuple[str, str]] = []
    for c in parsed_sentence.get_children(head_tok):
        if c.dep in ("prep", "agent"):
            for pobj in parsed_sentence.get_children(c):
                if pobj.dep in ("pobj", "obj"):
                    prep_args.append((c.lemma.lower(), pobj.lemma.lower()))
                    prep_args.extend(
                        _collect_prep_arguments(parsed_sentence, pobj, visited, depth + 1)
                    )
    return prep_args


def _collect_modifiers(parsed_sentence: ParsedSentence, head_tok: ParsedToken) -> Tuple[str, ...]:
    """Collect compound, amod, and nmod lemmas attached to head_tok."""
    mods = [
        c.lemma.lower()
        for c in parsed_sentence.get_children(head_tok)
        if c.dep in ("compound", "amod", "nmod") and c.dep != "punct"
    ]
    return tuple(mods)


def _collect_predicate_modifiers(parsed_sentence: ParsedSentence, pred_tok: ParsedToken) -> Tuple[str, ...]:
    """Collect adverbial and negation modifier lemmas attached to pred_tok."""
    mods: List[str] = []
    stack = [
        c
        for c in parsed_sentence.get_children(pred_tok)
        if c.dep in ("advmod", "npadvmod", "neg") and c.dep != "punct"
    ]
    while stack:
        curr = stack.pop(0)
        mods.append(curr.lemma.lower())
        for child in parsed_sentence.get_children(curr):
            if child.dep in ("advmod", "npadvmod", "neg") and child.dep != "punct":
                stack.append(child)
    return tuple(mods)


class DependencyTripleExtractor:
    """
    Extracts raw dependency arcs and ASAG-oriented canonical relations
    from Stage 4 ParsedSentence and ParsedDocument instances.

    Extraction Principles:
    1. Complete Raw Arcs: Every non-root token generates a (governor, relation, dependent) arc.
    2. Conservative SPO Relations: Clause relations are formed only when backed by explicit
       syntactic dependency relations. Prepositions and modifiers are NOT converted into
       false direct objects.
    3. Passive Transformation: Explicitly documented rule maps (nsubjpass + agent:by:pobj)
       into canonical (agent, verb, patient) triples.
    """

    def extract(self, parsed_sentence: ParsedSentence) -> SentenceTriples:
        """
        Extract raw dependency arcs and canonical relations from a single ParsedSentence.

        Parameters
        ----------
        parsed_sentence : ParsedSentence
            Stage 4 parsed sentence structure.

        Returns
        -------
        SentenceTriples
            Structured representation containing raw_arcs and canonical_relations.

        Raises
        ------
        TypeError
            If parsed_sentence is not a ParsedSentence instance.
        """
        if not isinstance(parsed_sentence, ParsedSentence):
            raise TypeError(
                f"Expected ParsedSentence, got {type(parsed_sentence).__name__}."
            )

        if parsed_sentence.token_count == 0:
            return SentenceTriples(
                sentence_text=parsed_sentence.original_text,
                normalized_text=parsed_sentence.normalized_text,
                raw_arcs=[],
                canonical_relations=[],
            )

        # 1. Extract Raw Dependency Arcs (governor, relation, dependent)
        raw_arcs: List[DependencyArc] = []
        for tok in parsed_sentence.tokens:
            if not tok.is_root and tok.dep.upper() != "ROOT":
                gov = parsed_sentence.get_head(tok)
                raw_arcs.append(
                    DependencyArc(
                        governor_text=gov.text,
                        governor_lemma=gov.lemma,
                        governor_pos=gov.pos,
                        governor_index=gov.index,
                        relation=tok.dep,
                        dependent_text=tok.text,
                        dependent_lemma=tok.lemma,
                        dependent_pos=tok.pos,
                        dependent_index=tok.index,
                    )
                )

        # 2. Extract Canonical Clause Relations
        canonical_relations = self._extract_canonical_relations(parsed_sentence)

        return SentenceTriples(
            sentence_text=parsed_sentence.original_text,
            normalized_text=parsed_sentence.normalized_text,
            raw_arcs=raw_arcs,
            canonical_relations=canonical_relations,
        )

    def _extract_canonical_relations(
        self, parsed_sentence: ParsedSentence
    ) -> List[DependencyRelation]:
        """
        Identify clause predicates and extract canonical (subject, predicate, object) relations
        enriched with extended argument representations (indirect objects, prepositional
        arguments, and slot modifiers).

        Rules:
        - Active transitive (nsubj + dobj/attr): -> SPO relation.
        - Active intransitive (nsubj without dobj): -> SP relation.
        - Passive with agent (nsubjpass + agent:by:pobj): -> PASSIVE_SPO relation.
        - Passive agentless (nsubjpass without agent): -> PASSIVE_SP relation.
        - Modifiers and prepositional arguments are preserved in extended attributes
          without destroying canonical S-P-O slot roles.
        """
        relations: List[DependencyRelation] = []

        # Find candidate predicates: verbs, auxiliaries, or the sentence root
        predicate_candidates: List[ParsedToken] = [
            t for t in parsed_sentence.tokens
            if t.pos in ("VERB", "AUX") or t.is_root
        ]

        for pred in predicate_candidates:
            children = parsed_sentence.get_children(pred)

            # Check for indirect object
            iobj_tok = next((c for c in children if c.dep in ("iobj", "dative")), None)
            iobj = iobj_tok.text if iobj_tok else None
            iobj_lemma = iobj_tok.lemma.lower() if iobj_tok else None

            # Predicate adverbial modifiers
            pred_mods = _collect_predicate_modifiers(parsed_sentence, pred)

            # Check for active subject
            active_subj = next(
                (c for c in children if c.dep in ("nsubj", "csubj")),
                None
            )

            # Check for passive subject
            passive_subj = next(
                (c for c in children if c.dep in ("nsubjpass", "csubjpass")),
                None
            )

            # If pred has no explicit subject and is conjoined (dep == "conj"), inherit subject from governor
            if active_subj is None and passive_subj is None and pred.dep == "conj":
                gov = parsed_sentence.get_head(pred)
                gov_children = parsed_sentence.get_children(gov)
                active_subj = next(
                    (c for c in gov_children if c.dep in ("nsubj", "csubj")),
                    None
                )
                if active_subj is None:
                    passive_subj = next(
                        (c for c in gov_children if c.dep in ("nsubjpass", "csubjpass")),
                        None
                    )

            # Pre-verbal nominal dependent fallback: in statistical parses, a pre-verbal
            # subject noun modifying a verb may occasionally be mis-labeled as compound/dep
            if active_subj is None and passive_subj is None and pred.pos in ("VERB", "AUX"):
                pre_noun = next(
                    (
                        c
                        for c in children
                        if c.pos in ("NOUN", "PROPN", "PRON")
                        and c.dep in ("compound", "dep")
                        and c.index < pred.index
                    ),
                    None,
                )
                if pre_noun is not None:
                    active_subj = pre_noun

            # Adnominal clausal modifiers (dep in ("acl", "vmod"))
            # e.g., "programs written in a high-level language" -> governor "programs" is subject
            if active_subj is None and passive_subj is None and pred.dep in ("acl", "vmod"):
                gov = parsed_sentence.get_head(pred)
                if gov.pos in ("NOUN", "PROPN", "PRON"):
                    if pred.tag == "VBN":
                        passive_subj = gov
                    else:
                        active_subj = gov

            # Relative clauses (dep == "relcl") with relative pronoun subjects ("that", "which", "who")
            # e.g., "a program that converts source code" -> resolve "that" to antecedent noun "program"
            if (
                active_subj is not None
                and active_subj.pos == "PRON"
                and active_subj.text.lower() in ("that", "which", "who")
            ):
                gov = parsed_sentence.get_head(pred)
                if gov.pos in ("NOUN", "PROPN"):
                    active_subj = gov

            # Case A: Active construction with explicit subject
            if active_subj is not None:
                subj_mods = _collect_modifiers(parsed_sentence, active_subj)

                # Direct object, copular attribute, or adjectival complement (acomp)
                obj = next(
                    (c for c in children if c.dep in ("dobj", "obj", "attr", "acomp")),
                    None
                )
                if obj is None:
                    obj = next(
                        (
                            c
                            for c in children
                            if c.pos in ("NOUN", "PROPN", "PRON")
                            and c.dep in ("npadvmod", "dep")
                            and c.index > pred.index
                        ),
                        None,
                    )

                raw_prep_args = _collect_prep_arguments(parsed_sentence, pred)
                if obj is not None:
                    raw_prep_args.extend(_collect_prep_arguments(parsed_sentence, obj))
                    obj_mods = _collect_modifiers(parsed_sentence, obj)
                else:
                    obj_mods = ()
                prep_args = tuple(dict.fromkeys(raw_prep_args))

                if obj is not None:
                    relations.append(
                        DependencyRelation(
                            subject=active_subj.text,
                            predicate=pred.text,
                            object=obj.text,
                            subject_lemma=active_subj.lemma,
                            predicate_lemma=pred.lemma,
                            object_lemma=obj.lemma,
                            relation_type="SPO",
                            source_dependency_relations=(active_subj.dep, obj.dep),
                            subject_index=active_subj.index,
                            predicate_index=pred.index,
                            object_index=obj.index,
                            indirect_object=iobj,
                            indirect_object_lemma=iobj_lemma,
                            prepositional_arguments=prep_args,
                            predicate_modifiers=pred_mods,
                            subject_modifiers=subj_mods,
                            object_modifiers=obj_mods,
                        )
                    )
                else:
                    relations.append(
                        DependencyRelation(
                            subject=active_subj.text,
                            predicate=pred.text,
                            object=None,
                            subject_lemma=active_subj.lemma,
                            predicate_lemma=pred.lemma,
                            object_lemma=None,
                            relation_type="SP",
                            source_dependency_relations=(active_subj.dep,),
                            subject_index=active_subj.index,
                            predicate_index=pred.index,
                            object_index=None,
                            indirect_object=iobj,
                            indirect_object_lemma=iobj_lemma,
                            prepositional_arguments=prep_args,
                            predicate_modifiers=pred_mods,
                            subject_modifiers=subj_mods,
                            object_modifiers=(),
                        )
                    )

            # Case B: Passive construction with explicit patient
            elif passive_subj is not None:
                # Check for agent preposition ("by" with pobj)
                agent_prep = next(
                    (c for c in children if c.dep == "agent" or (c.dep == "prep" and c.lemma.lower() == "by")),
                    None
                )
                agent_obj = None
                if agent_prep is not None:
                    agent_children = parsed_sentence.get_children(agent_prep)
                    agent_obj = next(
                        (c for c in agent_children if c.dep == "pobj"),
                        None
                    )

                raw_prep_args = _collect_prep_arguments(parsed_sentence, pred)
                raw_prep_args.extend(_collect_prep_arguments(parsed_sentence, passive_subj))
                prep_args = tuple(dict.fromkeys(raw_prep_args))

                if agent_obj is not None:
                    subj_mods = _collect_modifiers(parsed_sentence, agent_obj)
                    obj_mods = _collect_modifiers(parsed_sentence, passive_subj)
                    # Passive with agent: logical subject is agent_obj, logical object is passive_subj
                    relations.append(
                        DependencyRelation(
                            subject=agent_obj.text,
                            predicate=pred.text,
                            object=passive_subj.text,
                            subject_lemma=agent_obj.lemma,
                            predicate_lemma=pred.lemma,
                            object_lemma=passive_subj.lemma,
                            relation_type="PASSIVE_SPO",
                            source_dependency_relations=(passive_subj.dep, f"{agent_prep.dep}:pobj"),
                            subject_index=agent_obj.index,
                            predicate_index=pred.index,
                            object_index=passive_subj.index,
                            indirect_object=iobj,
                            indirect_object_lemma=iobj_lemma,
                            prepositional_arguments=prep_args,
                            predicate_modifiers=pred_mods,
                            subject_modifiers=subj_mods,
                            object_modifiers=obj_mods,
                        )
                    )
                else:
                    subj_mods = _collect_modifiers(parsed_sentence, passive_subj)
                    # Agentless passive: patient is recorded as subject of passive predicate, object is None
                    relations.append(
                        DependencyRelation(
                            subject=passive_subj.text,
                            predicate=pred.text,
                            object=None,
                            subject_lemma=passive_subj.lemma,
                            predicate_lemma=pred.lemma,
                            object_lemma=None,
                            relation_type="PASSIVE_SP",
                            source_dependency_relations=(passive_subj.dep,),
                            subject_index=passive_subj.index,
                            predicate_index=pred.index,
                            object_index=None,
                            indirect_object=iobj,
                            indirect_object_lemma=iobj_lemma,
                            prepositional_arguments=prep_args,
                            predicate_modifiers=pred_mods,
                            subject_modifiers=subj_mods,
                            object_modifiers=(),
                        )
                    )

        return relations

    def extract_document(self, parsed_document: ParsedDocument) -> DocumentTriples:
        """
        Extract raw dependency arcs and canonical relations across a ParsedDocument.

        Parameters
        ----------
        parsed_document : ParsedDocument
            Stage 4 parsed document structure.

        Returns
        -------
        DocumentTriples
            Structured document representation containing sentence-level triples.

        Raises
        ------
        TypeError
            If parsed_document is not a ParsedDocument instance.
        """
        if not isinstance(parsed_document, ParsedDocument):
            raise TypeError(
                f"Expected ParsedDocument, got {type(parsed_document).__name__}."
            )

        sentence_triples_list: List[SentenceTriples] = [
            self.extract(sent) for sent in parsed_document.sentences
        ]

        return DocumentTriples(
            document_text=parsed_document.original_text,
            sentences=sentence_triples_list,
        )

    def extract_triples(
        self, parsed_data: Union[ParsedSentence, ParsedDocument]
    ) -> Union[SentenceTriples, DocumentTriples]:
        """
        Polymorphic extraction entry point for either ParsedSentence or ParsedDocument.

        Parameters
        ----------
        parsed_data : Union[ParsedSentence, ParsedDocument]
            Stage 4 parsed structure.

        Returns
        -------
        Union[SentenceTriples, DocumentTriples]
            Extracted dependency structures matching the input type.
        """
        if isinstance(parsed_data, ParsedSentence):
            return self.extract(parsed_data)
        if isinstance(parsed_data, ParsedDocument):
            return self.extract_document(parsed_data)
        raise TypeError(
            f"Expected ParsedSentence or ParsedDocument, got {type(parsed_data).__name__}."
        )
