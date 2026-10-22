"""
Robust Hybrid Proposition Representation for Base and Proposed ASAG.

This module addresses the syntactic fragmentation problem where non-sentential
reference answers (infinitive phrases, nominal lists, prepositional phrases, and
property fragments) produce zero canonical S-P-O triples under standard clausal extraction.

Design Principles:
1. Primary Representation: Clausal dependency triples (S-P-O, S-P) extracted via
   DependencyTripleExtractor when grammatical subjects are present.
2. Fallback Representation: Linguistic propositions and semantic fragments extracted
   when standard clausal extraction yields zero relations.
3. Explicit Representation Types:
   - TRIPLE: Standard clausal subject-predicate-object or passive relation.
   - ARGUMENT_STRUCTURE: Non-finite / infinitive predicates with arguments.
   - PROPERTY: Entity-attribute or noun-adjective modifier structures.
   - RELATIONAL_FRAGMENT: Prepositional phrases and nominal coordinate lists.
4. Complete Provenance: Every proposition preserves character span, token indices,
   sentence index, dependency evidence, polarity, and modality.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from base_asag.dependency.parser import (
    ParsedDocument,
    ParsedSentence,
    ParsedToken,
)
from base_asag.dependency.triples import (
    DependencyRelation,
    DependencyTripleExtractor,
    _collect_modifiers,
    _collect_predicate_modifiers,
    _collect_prep_arguments,
)


class PropositionType(str, Enum):
    """Category of proposition representation."""
    TRIPLE = "TRIPLE"
    ARGUMENT_STRUCTURE = "ARGUMENT_STRUCTURE"
    PROPERTY = "PROPERTY"
    RELATIONAL_FRAGMENT = "RELATIONAL_FRAGMENT"


class Polarity(str, Enum):
    """Grammatical and semantic polarity of the proposition."""
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"


class Modality(str, Enum):
    """Epistemic modality of the proposition."""
    ASSERTED = "ASSERTED"
    POSSIBLE = "POSSIBLE"
    NECESSARY = "NECESSARY"
    UNCERTAIN = "UNCERTAIN"


@dataclass(frozen=True)
class RobustProposition:
    """
    Unified proposition structure preserving full linguistic provenance,
    representation category, polarity, and modality.
    """
    subject: Optional[str]
    predicate: str
    object: Optional[str]
    subject_lemma: Optional[str]
    predicate_lemma: str
    object_lemma: Optional[str]
    representation_type: PropositionType
    polarity: Polarity
    modality: Modality
    source_text: str
    char_start: int
    char_end: int
    sentence_index: int
    token_indices: Tuple[int, ...]
    dependency_evidence: Tuple[str, ...]
    properties: Dict[str, Any] = field(default_factory=dict)

    def to_tuple(self) -> Tuple[Optional[str], str, Optional[str]]:
        """Return (subject, predicate, object)."""
        return (self.subject, self.predicate, self.object)

    def to_lemma_tuple(self) -> Tuple[Optional[str], str, Optional[str]]:
        """Return (subject_lemma, predicate_lemma, object_lemma)."""
        return (self.subject_lemma, self.predicate_lemma, self.object_lemma)

    def to_dict(self) -> Dict[str, Any]:
        """Convert proposition to a JSON-serializable dictionary."""
        return {
            "subject": self.subject,
            "predicate": self.predicate,
            "object": self.object,
            "subject_lemma": self.subject_lemma,
            "predicate_lemma": self.predicate_lemma,
            "object_lemma": self.object_lemma,
            "representation_type": self.representation_type.value,
            "polarity": self.polarity.value,
            "modality": self.modality.value,
            "source_text": self.source_text,
            "char_start": self.char_start,
            "char_end": self.char_end,
            "sentence_index": self.sentence_index,
            "token_indices": list(self.token_indices),
            "dependency_evidence": list(self.dependency_evidence),
            "properties": self.properties,
        }


class RobustPropositionExtractor:
    """
    Hybrid proposition extractor combining primary clausal dependency triples
    with structured fallback extraction for fragments, infinitives, and properties.
    """

    def __init__(self) -> None:
        self._triple_extractor = DependencyTripleExtractor()

    def extract_document(
        self, parsed_doc: ParsedDocument, original_text: Optional[str] = None
    ) -> List[RobustProposition]:
        """
        Extract robust propositions across all sentences in a ParsedDocument.
        """
        propositions: List[RobustProposition] = []
        doc_text = original_text or parsed_doc.original_text

        for sent_idx, sent in enumerate(parsed_doc.sentences):
            sent_props = self.extract_sentence(
                sent, sentence_index=sent_idx, document_text=doc_text
            )
            propositions.extend(sent_props)

        # Deduplicate identical propositions while preserving provenance
        return self._deduplicate(propositions)

    def extract_sentence(
        self,
        parsed_sentence: ParsedSentence,
        sentence_index: int = 0,
        document_text: Optional[str] = None,
    ) -> List[RobustProposition]:
        """
        Extract robust propositions from a single ParsedSentence.
        Uses primary clausal relations if available; falls back to linguistic
        fragments if primary extraction yields zero propositions.
        """
        if parsed_sentence.token_count == 0:
            return []

        doc_text = document_text or parsed_sentence.original_text

        # 1. Primary: Try standard canonical clausal relations
        canonical_relations = self._triple_extractor._extract_canonical_relations(
            parsed_sentence
        )

        props: List[RobustProposition] = []
        if canonical_relations:
            props.extend([
                self._canonical_to_robust(rel, parsed_sentence, sentence_index, doc_text)
                for rel in canonical_relations
            ])

        # Check if sentence ROOT verb is represented
        root = next((t for t in parsed_sentence.tokens if t.is_root or t.dep.upper() == "ROOT"), None)
        root_represented = False
        if root is not None:
            root_represented = any(p.token_indices and root.index in p.token_indices for p in props)

        if not canonical_relations:
            fallback_props = self._extract_fallback_propositions(
                parsed_sentence, sentence_index, doc_text
            )
            props.extend(fallback_props)
        elif not root_represented and root is not None and root.pos in ("VERB", "AUX"):
            # Root verb is non-finite / infinitive but was shadowed by subordinate clause relations
            root_children = parsed_sentence.get_children(root)
            arg_props = self._extract_infinitive_arguments(root, root_children, parsed_sentence, sentence_index, doc_text)
            if arg_props:
                props.extend(arg_props)

        return self._deduplicate(props)

    def _canonical_to_robust(
        self,
        rel: DependencyRelation,
        parsed_sent: ParsedSentence,
        sent_idx: int,
        doc_text: str,
    ) -> RobustProposition:
        """Convert a standard DependencyRelation into a RobustProposition."""
        pred_token = parsed_sent.tokens[rel.predicate_index]
        children = parsed_sent.get_children(pred_token)

        # Polarity detection
        polarity = self._detect_polarity(pred_token, children, rel, parsed_sent)

        # Modality detection
        modality = self._detect_modality(pred_token, children)

        # Token indices & spans
        token_indices = [rel.predicate_index]
        if rel.subject_index is not None and rel.subject_index >= 0:
            token_indices.append(rel.subject_index)
        if rel.object_index is not None and rel.object_index >= 0:
            token_indices.append(rel.object_index)

        token_indices.sort()

        # Check if subject was inherited from an earlier clause in a conjoined VP
        # e.g., "A primary key [identifies records] and [can contain duplicate values]"
        # In coordinated VPs, the subject of the second conjunct is syntactically attached
        # to the primary verb. Including the inherited subject token causes the span
        # to span across the conjunction and duplicate the entire preceding clause.
        is_inherited_subj = (
            rel.subject_index is not None
            and rel.subject_index >= 0
            and rel.subject_index < rel.predicate_index
            and pred_token.dep == "conj"
            and parsed_sent.tokens[rel.subject_index].head_index != rel.predicate_index
        )

        if is_inherited_subj:
            # For coordinated clauses sharing an inherited subject, calculate a clause-local span
            visited: Set[int] = set()

            def _collect_local(tok: ParsedToken) -> List[ParsedToken]:
                if tok.index in visited:
                    return []
                visited.add(tok.index)
                res = [tok]
                for child in parsed_sent.get_children(tok):
                    if child.dep not in ("conj", "cc", "punct"):
                        res.extend(_collect_local(child))
                return res

            local_tokens = _collect_local(pred_token)
            if rel.object_index is not None and rel.object_index >= 0:
                obj_tok = parsed_sent.tokens[rel.object_index]
                if obj_tok.index not in visited:
                    local_tokens.extend(_collect_local(obj_tok))

            span_indices = sorted({t.index for t in local_tokens if 0 <= t.index < parsed_sent.token_count})
            if not span_indices:
                span_indices = token_indices
        else:
            span_indices = list(token_indices)
            # If the object is an adjectival complement (acomp) with a comparative preposition
            # e.g., "smaller than the parent", extend the span to include the comparative target
            if rel.object_index is not None and 0 <= rel.object_index < parsed_sent.token_count:
                obj_tok = parsed_sent.tokens[rel.object_index]
                if obj_tok.dep == "acomp":
                    than_prep = next(
                        (
                            c
                            for c in parsed_sent.get_children(obj_tok)
                            if c.dep == "prep" and c.lemma.lower() in ("than", "to", "as")
                        ),
                        None,
                    )
                    if than_prep is not None:
                        for pobj in parsed_sent.get_children(than_prep):
                            if pobj.dep in ("pobj", "obj") and 0 <= pobj.index < parsed_sent.token_count:
                                span_indices.append(pobj.index)
                        span_indices.sort()

            # Include predicate adverbial modifiers (e.g. "removed first", "yields sorted order")
            for c in parsed_sent.get_children(pred_token):
                if c.dep in ("advmod", "npadvmod") and 0 <= c.index < parsed_sent.token_count:
                    if c.index not in span_indices:
                        span_indices.append(c.index)
            span_indices.sort()

        char_start, char_end = self._compute_token_span(
            span_indices, parsed_sent, doc_text
        )

        prop_properties: Dict[str, Any] = {"relation_type": rel.relation_type}

        # Collect subtree tokens/lemmas for subject to preserve modifiers and compounds
        if rel.subject_index is not None and 0 <= rel.subject_index < parsed_sent.token_count:
            subj_tok = parsed_sent.tokens[rel.subject_index]
            def _collect_subj_lemmas(tok: ParsedToken) -> List[str]:
                res = [tok.lemma.lower()]
                for c in parsed_sent.get_children(tok):
                    if c.dep != "punct":
                        res.extend(_collect_subj_lemmas(c))
                return res
            prop_properties["subject_tree_lemmas"] = _collect_subj_lemmas(subj_tok)

        # Collect subtree tokens/lemmas for object
        if rel.object_index is not None and 0 <= rel.object_index < parsed_sent.token_count:
            obj_tok = parsed_sent.tokens[rel.object_index]
            def _collect_obj_lemmas(tok: ParsedToken) -> List[str]:
                res = [tok.lemma.lower()]
                for c in parsed_sent.get_children(tok):
                    if c.dep != "punct":
                        res.extend(_collect_obj_lemmas(c))
                return res
            prop_properties["object_tree_lemmas"] = _collect_obj_lemmas(obj_tok)

        # Collect prepositional complements attached to the predicate
        prep_lemmas: List[str] = []
        for c in parsed_sent.get_children(pred_token):
            if c.dep == "prep":
                def _collect_prep_lemmas(tok: ParsedToken) -> List[str]:
                    res = [tok.lemma.lower()]
                    for ch in parsed_sent.get_children(tok):
                        if ch.dep != "punct":
                            res.extend(_collect_prep_lemmas(ch))
                    return res
                prep_lemmas.extend(_collect_prep_lemmas(c))
        if prep_lemmas:
            prop_properties["prep_phrase_lemmas"] = prep_lemmas

        # Collect adverbial modifiers attached to the predicate
        advmod_lemmas: List[str] = [
            c.lemma.lower()
            for c in parsed_sent.get_children(pred_token)
            if c.dep in ("advmod", "npadvmod") and c.dep != "punct"
        ]
        if advmod_lemmas:
            prop_properties["predicate_modifier_lemmas"] = advmod_lemmas

        if rel.object_index is not None and 0 <= rel.object_index < parsed_sent.token_count:
            obj_tok = parsed_sent.tokens[rel.object_index]
            if obj_tok.dep == "acomp":
                prop_properties["is_copular_adjective"] = True
                than_prep = next(
                    (
                        c
                        for c in parsed_sent.get_children(obj_tok)
                        if c.dep == "prep" and c.lemma.lower() in ("than", "to", "as")
                    ),
                    None,
                )
                if than_prep is not None:
                    pobj = next(
                        (c for c in parsed_sent.get_children(than_prep) if c.dep in ("pobj", "obj")),
                        None,
                    )
                    if pobj is not None:
                        prop_properties["comparative_target"] = pobj.text
                        prop_properties["comparative_target_lemma"] = pobj.lemma
        if rel.indirect_object is not None:
            prop_properties["indirect_object"] = rel.indirect_object
            prop_properties["indirect_object_lemma"] = rel.indirect_object_lemma
        if rel.prepositional_arguments:
            prop_properties["prepositional_arguments"] = [list(x) for x in rel.prepositional_arguments]
        if rel.predicate_modifiers:
            prop_properties["predicate_modifiers"] = list(rel.predicate_modifiers)
        if rel.subject_modifiers:
            prop_properties["subject_modifiers"] = list(rel.subject_modifiers)
        if rel.object_modifiers:
            prop_properties["object_modifiers"] = list(rel.object_modifiers)

        return RobustProposition(
            subject=rel.subject,
            predicate=rel.predicate,
            object=rel.object,
            subject_lemma=rel.subject_lemma,
            predicate_lemma=rel.predicate_lemma,
            object_lemma=rel.object_lemma,
            representation_type=PropositionType.TRIPLE,
            polarity=polarity,
            modality=modality,
            source_text=doc_text[char_start:char_end] if char_start >= 0 and char_end > char_start else parsed_sent.original_text,
            char_start=char_start,
            char_end=char_end,
            sentence_index=sent_idx,
            token_indices=tuple(token_indices),
            dependency_evidence=rel.source_dependency_relations,
            properties=prop_properties,
        )

    def _extract_fallback_propositions(
        self,
        parsed_sent: ParsedSentence,
        sent_idx: int,
        doc_text: str,
    ) -> List[RobustProposition]:
        """
        Linguistic fallback extraction for non-sentential fragments:
        - Infinitive / participial predicates (ARGUMENT_STRUCTURE)
        - Prepositional phrases (RELATIONAL_FRAGMENT)
        - Nominal coordinations (RELATIONAL_FRAGMENT)
        - Noun-adjective / property structures (PROPERTY)
        """
        propositions: List[RobustProposition] = []

        # Find the root token
        root = next((t for t in parsed_sent.tokens if t.is_root or t.dep.upper() == "ROOT"), None)
        if root is None and parsed_sent.tokens:
            root = parsed_sent.tokens[0]

        if root is None:
            return []

        children = parsed_sent.get_children(root)

        # Fallback A: Non-finite verb root (e.g., "To simulate the behaviour...")
        if root.pos in ("VERB", "AUX"):
            arg_props = self._extract_infinitive_arguments(root, children, parsed_sent, sent_idx, doc_text)
            if arg_props:
                propositions.extend(arg_props)

        # Fallback B: Nominal coordination (e.g., "Abstraction and reusability.")
        if root.pos in ("NOUN", "PROPN"):
            coord_props = self._extract_nominal_coordination(root, children, parsed_sent, sent_idx, doc_text)
            if coord_props:
                propositions.extend(coord_props)

        # Fallback C: Prepositional phrase fragment (e.g., "At the main function", "by reference")
        if root.pos in ("ADP", "SCONJ") or any(c.dep == "prep" for c in children) or (root.pos in ("NOUN", "PROPN") and any(c.dep == "prep" for c in children)):
            prep_props = self._extract_prepositional_fragments(root, children, parsed_sent, sent_idx, doc_text)
            if prep_props:
                propositions.extend(prep_props)

        # Fallback D: Noun-property or modifier structure (e.g., "File scope")
        if root.pos in ("NOUN", "PROPN", "ADJ"):
            prop_props = self._extract_property_structures(root, children, parsed_sent, sent_idx, doc_text)
            if prop_props:
                propositions.extend(prop_props)

        # Fallback E: Minimal single-token or entity fragment if still empty
        if not propositions and parsed_sent.tokens:
            content_tokens = [t for t in parsed_sent.tokens if t.pos in ("NOUN", "PROPN", "VERB", "ADJ")]
            target = content_tokens[0] if content_tokens else root
            tok_indices = (target.index,)
            c_start, c_end = self._compute_token_span(list(tok_indices), parsed_sent, doc_text)
            propositions.append(
                RobustProposition(
                    subject=None,
                    predicate=target.text,
                    object=None,
                    subject_lemma=None,
                    predicate_lemma=target.lemma,
                    object_lemma=None,
                    representation_type=PropositionType.RELATIONAL_FRAGMENT,
                    polarity=Polarity.POSITIVE,
                    modality=Modality.ASSERTED,
                    source_text=doc_text[c_start:c_end] if c_start >= 0 else target.text,
                    char_start=c_start,
                    char_end=c_end,
                    sentence_index=sent_idx,
                    token_indices=tok_indices,
                    dependency_evidence=(target.dep,),
                    properties={"fragment_type": "content_word"},
                )
            )

        return propositions

    def _extract_infinitive_arguments(
        self,
        pred: ParsedToken,
        children: List[ParsedToken],
        parsed_sent: ParsedSentence,
        sent_idx: int,
        doc_text: str,
    ) -> List[RobustProposition]:
        """Extract argument structure from an infinitive or participle verb."""
        propositions: List[RobustProposition] = []

        # Find direct object
        obj = next((c for c in children if c.dep in ("dobj", "obj", "attr")), None)
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

        # Check for prepositional complement
        prep = next((c for c in children if c.dep == "prep"), None)
        pobj = None
        if prep:
            pobj = next((c for c in parsed_sent.get_children(prep) if c.dep in ("pobj", "obj")), None)

        target_obj = obj or pobj
        obj_text = target_obj.text if target_obj else None
        obj_lemma = target_obj.lemma if target_obj else None

        tok_indices = [pred.index]
        if target_obj:
            tok_indices.append(target_obj.index)
        if prep:
            tok_indices.append(prep.index)
        tok_indices.sort()

        c_start, c_end = self._compute_token_span(tok_indices, parsed_sent, doc_text)
        dep_evidence = [pred.dep]
        if target_obj:
            dep_evidence.append(target_obj.dep)

        polarity = (
            Polarity.NEGATIVE
            if any(
                (c.dep == "neg" or c.lemma.lower() in ("not", "never", "no", "neither", "nor", "none", "cannot") or "n't" in c.text.lower())
                for c in children
                if c.dep not in ("prep", "agent")
            )
            else Polarity.POSITIVE
        )
        modality = self._detect_modality(pred, children)

        # Collect prepositional arguments from pred and target_obj
        raw_prep_args = _collect_prep_arguments(parsed_sent, pred)
        if target_obj:
            raw_prep_args.extend(_collect_prep_arguments(parsed_sent, target_obj))
        prep_args = [list(item) for item in dict.fromkeys(raw_prep_args)]

        # Collect modifiers
        pred_mods = list(_collect_predicate_modifiers(parsed_sent, pred))
        obj_mods = list(_collect_modifiers(parsed_sent, target_obj)) if target_obj else []

        props_dict: Dict[str, Any] = {
            "predicate_type": "infinitive_or_nonfinite",
            "prepositional_arguments": prep_args,
            "predicate_modifiers": pred_mods,
            "object_modifiers": obj_mods,
        }
        if target_obj:
            def _collect_tree(tok: ParsedToken) -> List[str]:
                res = [tok.lemma.lower()]
                for ch in parsed_sent.get_children(tok):
                    if ch.dep != "punct":
                        res.extend(_collect_tree(ch))
                return res
            props_dict["object_tree_lemmas"] = _collect_tree(target_obj)

        propositions.append(
            RobustProposition(
                subject=None,
                predicate=pred.text,
                object=obj_text,
                subject_lemma=None,
                predicate_lemma=pred.lemma,
                object_lemma=obj_lemma,
                representation_type=PropositionType.ARGUMENT_STRUCTURE,
                polarity=polarity,
                modality=modality,
                source_text=doc_text[c_start:c_end] if c_start >= 0 else parsed_sent.original_text,
                char_start=c_start,
                char_end=c_end,
                sentence_index=sent_idx,
                token_indices=tuple(tok_indices),
                dependency_evidence=tuple(dep_evidence),
                properties=props_dict,
            )
        )
        return propositions

    def _extract_nominal_coordination(
        self,
        root: ParsedToken,
        children: List[ParsedToken],
        parsed_sent: ParsedSentence,
        sent_idx: int,
        doc_text: str,
    ) -> List[RobustProposition]:
        """Extract coordinate pairs from nominal lists (e.g. 'Abstraction and reusability')."""
        propositions: List[RobustProposition] = []
        conjoined = [c for c in children if c.dep == "conj" and c.pos in ("NOUN", "PROPN")]

        for conj in conjoined:
            tok_indices = sorted([root.index, conj.index])
            c_start, c_end = self._compute_token_span(tok_indices, parsed_sent, doc_text)
            propositions.append(
                RobustProposition(
                    subject=root.text,
                    predicate="and",
                    object=conj.text,
                    subject_lemma=root.lemma,
                    predicate_lemma="and",
                    object_lemma=conj.lemma,
                    representation_type=PropositionType.RELATIONAL_FRAGMENT,
                    polarity=Polarity.POSITIVE,
                    modality=Modality.ASSERTED,
                    source_text=doc_text[c_start:c_end] if c_start >= 0 else parsed_sent.original_text,
                    char_start=c_start,
                    char_end=c_end,
                    sentence_index=sent_idx,
                    token_indices=tuple(tok_indices),
                    dependency_evidence=(root.dep, conj.dep),
                    properties={"relation": "coordination"},
                )
            )
        return propositions

    def _extract_prepositional_fragments(
        self,
        root: ParsedToken,
        children: List[ParsedToken],
        parsed_sent: ParsedSentence,
        sent_idx: int,
        doc_text: str,
    ) -> List[RobustProposition]:
        """Extract prepositional relations (e.g. 'At the main function', 'by reference')."""
        propositions: List[RobustProposition] = []

        prep_tokens = []
        if root.pos in ("ADP", "SCONJ") or root.dep == "prep":
            prep_tokens.append(root)
        prep_tokens.extend([c for c in children if c.dep == "prep"])

        for prep in prep_tokens:
            pobjs = [c for c in parsed_sent.get_children(prep) if c.dep in ("pobj", "obj")]
            for pobj in pobjs:
                tok_indices = sorted([prep.index, pobj.index])
                c_start, c_end = self._compute_token_span(tok_indices, parsed_sent, doc_text)
                propositions.append(
                    RobustProposition(
                        subject=None,
                        predicate=prep.text,
                        object=pobj.text,
                        subject_lemma=None,
                        predicate_lemma=prep.lemma,
                        object_lemma=pobj.lemma,
                        representation_type=PropositionType.RELATIONAL_FRAGMENT,
                        polarity=Polarity.POSITIVE,
                        modality=Modality.ASSERTED,
                        source_text=doc_text[c_start:c_end] if c_start >= 0 else parsed_sent.original_text,
                        char_start=c_start,
                        char_end=c_end,
                        sentence_index=sent_idx,
                        token_indices=tuple(tok_indices),
                        dependency_evidence=(prep.dep, pobj.dep),
                        properties={"relation": "prepositional"},
                    )
                )
        return propositions

    def _extract_property_structures(
        self,
        root: ParsedToken,
        children: List[ParsedToken],
        parsed_sent: ParsedSentence,
        sent_idx: int,
        doc_text: str,
    ) -> List[RobustProposition]:
        """Extract entity-property structures (e.g. 'File scope', 'fixed size')."""
        propositions: List[RobustProposition] = []

        # Check for adjective or compound modifiers
        modifiers = [c for c in children if c.dep in ("amod", "compound", "nmod")]
        for mod in modifiers:
            tok_indices = sorted([mod.index, root.index])
            c_start, c_end = self._compute_token_span(tok_indices, parsed_sent, doc_text)
            propositions.append(
                RobustProposition(
                    subject=root.text,
                    predicate="has_property",
                    object=mod.text,
                    subject_lemma=root.lemma,
                    predicate_lemma="have",
                    object_lemma=mod.lemma,
                    representation_type=PropositionType.PROPERTY,
                    polarity=Polarity.POSITIVE,
                    modality=Modality.ASSERTED,
                    source_text=doc_text[c_start:c_end] if c_start >= 0 else parsed_sent.original_text,
                    char_start=c_start,
                    char_end=c_end,
                    sentence_index=sent_idx,
                    token_indices=tuple(tok_indices),
                    dependency_evidence=(root.dep, mod.dep),
                    properties={"entity": root.lemma, "property": mod.lemma},
                )
            )
        return propositions

    def _detect_modality(
        self, pred_token: ParsedToken, children: List[ParsedToken]
    ) -> Modality:
        """Detect epistemic modality from auxiliary tokens."""
        for c in children:
            if c.dep == "aux":
                lemma = c.lemma.lower()
                if lemma in ("can", "could", "may", "might"):
                    return Modality.POSSIBLE
                if lemma in ("must", "should", "shall", "need", "ought"):
                    return Modality.NECESSARY
                if lemma in ("would",):
                    return Modality.UNCERTAIN
        return Modality.ASSERTED

    def _detect_polarity(
        self,
        pred_token: ParsedToken,
        children: Sequence[ParsedToken],
        rel: DependencyRelation,
        parsed_sent: ParsedSentence,
    ) -> Polarity:
        """Detect grammatical or lexical negation on the proposition."""
        # 1. Predicate token itself
        pred_text_lower = pred_token.text.lower()
        pred_lemma_lower = pred_token.lemma.lower()
        if (
            pred_lemma_lower in ("not", "never", "no", "neither", "nor", "none", "cannot")
            or "n't" in pred_text_lower
            or pred_text_lower == "cannot"
        ):
            return Polarity.NEGATIVE

        # 2. Predicate direct children (excluding prepositions)
        for c in children:
            if c.dep in ("prep", "agent"):
                continue
            if (
                c.dep == "neg"
                or c.lemma.lower() in ("not", "never", "no", "neither", "nor", "none", "cannot")
                or "n't" in c.text.lower()
            ):
                return Polarity.NEGATIVE

            # Auxiliaries attached to predicate (e.g. does -> n't)
            if c.dep in ("aux", "auxpass"):
                for gc in parsed_sent.get_children(c):
                    if (
                        gc.dep == "neg"
                        or gc.lemma.lower() in ("not", "never", "no", "neither", "nor", "none", "cannot")
                        or "n't" in gc.text.lower()
                    ):
                        return Polarity.NEGATIVE

        # 3. Subject nominal determiners (e.g. "No key identifies...")
        if rel.subject_index is not None and 0 <= rel.subject_index < len(parsed_sent.tokens):
            subj_tok = parsed_sent.tokens[rel.subject_index]
            for c in parsed_sent.get_children(subj_tok):
                if (
                    c.dep in ("det", "neg")
                    and c.lemma.lower() in ("no", "neither", "none")
                ):
                    return Polarity.NEGATIVE

        # 4. Object nominal determiners (e.g. "...identifies no records")
        if rel.object_index is not None and 0 <= rel.object_index < len(parsed_sent.tokens):
            obj_tok = parsed_sent.tokens[rel.object_index]
            for c in parsed_sent.get_children(obj_tok):
                if (
                    c.dep in ("det", "neg")
                    and c.lemma.lower() in ("no", "neither", "none")
                ):
                    return Polarity.NEGATIVE

        # 5. Lexical fallback on surface tokens
        if any(w in ("not", "never", "neither", "nor", "cannot") or "n't" in w for w in rel.predicate.lower().split()):
            return Polarity.NEGATIVE
        if any(w in ("no", "neither", "none") for w in rel.subject.lower().split()):
            return Polarity.NEGATIVE
        if rel.object and any(w in ("no", "neither", "none") for w in rel.object.lower().split()):
            return Polarity.NEGATIVE

        return Polarity.POSITIVE

    def _compute_token_span(
        self, token_indices: List[int], parsed_sent: ParsedSentence, doc_text: str
    ) -> Tuple[int, int]:
        """Compute exact character offsets in doc_text for the given token indices."""
        if not token_indices or not parsed_sent.tokens:
            return (-1, -1)

        sent_text = parsed_sent.original_text
        sent_start = doc_text.find(sent_text)
        if sent_start == -1:
            sent_start = 0

        first_tok = parsed_sent.tokens[token_indices[0]]
        last_tok = parsed_sent.tokens[token_indices[-1]]

        char_start = sent_start + first_tok.char_offset
        char_end = sent_start + last_tok.char_offset + len(last_tok.text)

        return (char_start, char_end)

    def _deduplicate(
        self, propositions: List[RobustProposition]
    ) -> List[RobustProposition]:
        """Remove duplicate propositions while preserving order and polarity distinctions."""
        seen: Set[Tuple[Optional[str], str, Optional[str], str, str]] = set()
        unique: List[RobustProposition] = []
        for p in propositions:
            key = (
                p.subject_lemma,
                p.predicate_lemma,
                p.object_lemma,
                p.representation_type.value,
                p.polarity.value,
            )
            if key not in seen:
                seen.add(key)
                unique.append(p)
        return unique
