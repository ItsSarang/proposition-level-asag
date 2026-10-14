"""
Canonical Reference Fragment Representation Module (Experiment 5 Part B).

Provides robust, supported semantic representations for non-sentential reference
answers (infinitives, noun-modifier pairs, prepositional phrases, and coordinate lists)
without replacing the underlying dependency parser or fabricating relations.

Key Fragment Types Supported:
1. Non-finite verb phrases: e.g. "deallocates memory", "To simulate the behaviour..."
2. Entity-property fragments: e.g. "dynamic size", "random access"
3. Noun with prepositional complement: e.g. "root of tree"
4. Prepositional phrases: e.g. "At the main function", "by reference"
5. Coordinate nominal lists: e.g. "Abstraction and reusability", "Data members and member functions"

Invariant:
Every proposition preserves exact token indices, character offsets, dependency evidence,
and original text provenance. Noise or empty inputs generate zero propositions (R20).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from base_asag.dependency.parser import (
    DependencyParser,
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
from base_asag.representation.hybrid import (
    Modality,
    Polarity,
    PropositionType,
    RobustProposition,
    RobustPropositionExtractor,
)


class CanonicalReferenceExtractor:
    """
    Extracts canonical, supported semantic propositions from reference answers,
    especially non-sentential fragments that fail standard clausal parsing.
    """

    def __init__(self, parser: Optional[DependencyParser] = None) -> None:
        self.parser = parser or DependencyParser()
        self.hybrid_extractor = RobustPropositionExtractor()
        self.triple_extractor = DependencyTripleExtractor()

    def extract_document(
        self,
        parsed_doc: Optional[ParsedDocument] = None,
        original_text: Optional[str] = None,
        question: str = "",
    ) -> List[RobustProposition]:
        """
        Extract canonical propositions across all sentences in a reference document.
        Returns an empty list for empty, whitespace, or unsupported texts (R20).
        """
        text = (original_text or (parsed_doc.original_text if parsed_doc else "") or "").strip()
        if not text:
            return []

        # If doc was not provided, parse it safely
        if parsed_doc is None:
            try:
                parsed_doc = self.parser.parse_document(text)
            except ValueError:
                return []

        propositions: List[RobustProposition] = []
        for sent_idx, sent in enumerate(parsed_doc.sentences):
            sent_props = self.extract_sentence(
                sent,
                sentence_index=sent_idx,
                document_text=text,
                question=question,
            )
            propositions.extend(sent_props)

        return self._deduplicate(propositions)

    def extract_sentence(
        self,
        parsed_sent: ParsedSentence,
        sentence_index: int = 0,
        document_text: Optional[str] = None,
        question: str = "",
    ) -> List[RobustProposition]:
        """
        Extract canonical propositions from a single reference sentence.
        """
        if parsed_sent.token_count == 0:
            return []

        doc_text = document_text or parsed_sent.original_text or ""
        tokens = parsed_sent.tokens

        # Filter out pure punctuation or whitespace
        content_tokens = [
            t for t in tokens
            if t.pos not in ("PUNCT", "SPACE", "SYM") and len(t.text.strip()) > 0
        ]
        if not content_tokens:
            return []

        # 1. First, check if standard clausal extraction yields relations
        canonical_relations = self.triple_extractor._extract_canonical_relations(parsed_sent)
        props: List[RobustProposition] = []

        if canonical_relations:
            for rel in canonical_relations:
                robust_p = self.hybrid_extractor._canonical_to_robust(
                    rel, parsed_sent, sentence_index, doc_text
                )
                props.append(robust_p)

        # 2. Check for specialized fragment structures (especially if clausal extraction is empty or incomplete)
        root = next((t for t in tokens if t.is_root or t.dep.upper() == "ROOT"), None)
        if root is None and tokens:
            root = tokens[0]

        if root is not None:
            children = parsed_sent.get_children(root)

            # Fragment Type 1: Non-finite / infinitive verb root (e.g. "deallocates memory")
            has_clausal_subject = any(
                c.dep in ("nsubj", "nsubjpass", "csubj", "csubjpass") for c in children
            )
            if root.pos in ("VERB", "AUX") and not has_clausal_subject:
                infinitive_props = self._extract_verb_fragment(
                    root, children, parsed_sent, sentence_index, doc_text
                )
                props.extend(infinitive_props)

            # Fragment Types 2-5: Standalone non-sentential fragments (only when clausal extraction yields no relations)
            if not canonical_relations:
                # Fragment Type 2: Noun with Prepositional Complement (e.g. "root of tree")
                if root.pos in ("NOUN", "PROPN"):
                    noun_prep_props = self._extract_noun_prep_complement(
                        root, children, parsed_sent, sentence_index, doc_text
                    )
                    props.extend(noun_prep_props)

                # Fragment Type 3: Entity-property / Noun-adjective (e.g. "dynamic size", "random access")
                if root.pos in ("NOUN", "PROPN"):
                    prop_props = self._extract_entity_property_fragment(
                        root, children, parsed_sent, sentence_index, doc_text
                    )
                    props.extend(prop_props)

                # Fragment Type 4: Coordinate nominal list (e.g. "Abstraction and reusability")
                if root.pos in ("NOUN", "PROPN") or any(c.dep == "conj" for c in children):
                    coord_props = self._extract_coordinate_concepts(
                        root, children, parsed_sent, sentence_index, doc_text
                    )
                    props.extend(coord_props)

                # Fragment Type 5: Prepositional phrase root (e.g. "At the main function", "by reference")
                if root.pos in ("ADP", "SCONJ") or root.dep == "prep":
                    prep_props = self._extract_prepositional_root(
                        root, children, parsed_sent, sentence_index, doc_text
                    )
                    props.extend(prep_props)

        # 3. Check for xcomp purpose / complement clauses (e.g. 'A destructor is used to deallocate memory')
        xcomp_props = self._extract_xcomp_clauses(parsed_sent, sentence_index, doc_text)
        props.extend(xcomp_props)

        # 4. Fallback: if still zero propositions, try standard hybrid extractor
        if not props:
            fallback = self.hybrid_extractor.extract_sentence(
                parsed_sent, sentence_index=sentence_index, document_text=doc_text
            )
            props.extend(fallback)

        return self._deduplicate(props)

    def _extract_verb_fragment(
        self,
        pred: ParsedToken,
        children: List[ParsedToken],
        parsed_sent: ParsedSentence,
        sent_idx: int,
        doc_text: str,
    ) -> List[RobustProposition]:
        """Extract canonical proposition from non-finite verb fragment (e.g. 'deallocates memory')."""
        obj = next((c for c in children if c.dep in ("dobj", "obj", "attr")), None)
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

        polarity = Polarity.NEGATIVE if any(c.dep == "neg" for c in children) else Polarity.POSITIVE

        prep_args = _collect_prep_arguments(parsed_sent, pred)
        if target_obj:
            prep_args.extend(_collect_prep_arguments(parsed_sent, target_obj))

        pred_mods = list(_collect_predicate_modifiers(parsed_sent, pred))
        obj_mods = list(_collect_modifiers(parsed_sent, target_obj)) if target_obj else []

        props_dict: Dict[str, Any] = {
            "fragment_type": "verb_fragment",
            "is_unanchored": True,
            "prepositional_arguments": [list(x) for x in dict.fromkeys(prep_args)],
            "predicate_modifiers": pred_mods,
            "object_modifiers": obj_mods,
        }

        # Check for conjoined verbs (e.g. "Deallocates memory and clean up after class object")
        propositions = [
            RobustProposition(
                subject=None,
                predicate=pred.text,
                object=obj_text,
                subject_lemma=None,
                predicate_lemma=pred.lemma,
                object_lemma=obj_lemma,
                representation_type=PropositionType.ARGUMENT_STRUCTURE,
                polarity=polarity,
                modality=Modality.ASSERTED,
                source_text=doc_text[c_start:c_end] if c_start >= 0 else pred.text,
                char_start=c_start,
                char_end=c_end,
                sentence_index=sent_idx,
                token_indices=tuple(tok_indices),
                dependency_evidence=tuple(dep_evidence),
                properties=props_dict,
            )
        ]

        # Extract conjoined verbs
        conjoined_verbs = [c for c in children if c.dep == "conj" and c.pos in ("VERB", "AUX")]
        for cv in conjoined_verbs:
            cv_children = parsed_sent.get_children(cv)
            cv_props = self._extract_verb_fragment(cv, cv_children, parsed_sent, sent_idx, doc_text)
            propositions.extend(cv_props)

        return propositions

    def _extract_noun_prep_complement(
        self,
        root: ParsedToken,
        children: List[ParsedToken],
        parsed_sent: ParsedSentence,
        sent_idx: int,
        doc_text: str,
    ) -> List[RobustProposition]:
        """
        Extract canonical relation from noun with prepositional complement (e.g. 'root of tree').
        Head noun = subject ('root'), prep = predicate ('of'), prep object = object ('tree').
        """
        propositions: List[RobustProposition] = []
        preps = [c for c in children if c.dep == "prep"]

        for prep in preps:
            pobjs = [c for c in parsed_sent.get_children(prep) if c.dep in ("pobj", "obj")]
            for pobj in pobjs:
                tok_indices = sorted([root.index, prep.index, pobj.index])
                c_start, c_end = self._compute_token_span(tok_indices, parsed_sent, doc_text)

                propositions.append(
                    RobustProposition(
                        subject=root.text,
                        predicate=prep.text,
                        object=pobj.text,
                        subject_lemma=root.lemma,
                        predicate_lemma=prep.lemma,
                        object_lemma=pobj.lemma,
                        representation_type=PropositionType.RELATIONAL_FRAGMENT,
                        polarity=Polarity.POSITIVE,
                        modality=Modality.ASSERTED,
                        source_text=doc_text[c_start:c_end] if c_start >= 0 else f"{root.text} {prep.text} {pobj.text}",
                        char_start=c_start,
                        char_end=c_end,
                        sentence_index=sent_idx,
                        token_indices=tuple(tok_indices),
                        dependency_evidence=(root.dep, prep.dep, pobj.dep),
                        properties={"fragment_type": "noun_prep_complement"},
                    )
                )
        return propositions

    def _extract_entity_property_fragment(
        self,
        root: ParsedToken,
        children: List[ParsedToken],
        parsed_sent: ParsedSentence,
        sent_idx: int,
        doc_text: str,
    ) -> List[RobustProposition]:
        """
        Extract entity-property structures (e.g. 'dynamic size', 'random access', 'data members', 'member functions').
        Entity = subject ('size'), property = object ('dynamic'), predicate = 'has_property'.
        Scans all nouns in the sentence to capture properties across coordinate structures.
        """
        propositions: List[RobustProposition] = []
        candidate_nouns = [t for t in parsed_sent.tokens if t.pos in ("NOUN", "PROPN")]

        for noun in candidate_nouns:
            n_children = parsed_sent.get_children(noun)
            modifiers = [c for c in n_children if c.dep in ("amod", "compound", "nmod")]

            for mod in modifiers:
                tok_indices = sorted([mod.index, noun.index])
                c_start, c_end = self._compute_token_span(tok_indices, parsed_sent, doc_text)

                propositions.append(
                    RobustProposition(
                        subject=noun.text,
                        predicate="has_property",
                        object=mod.text,
                        subject_lemma=noun.lemma,
                        predicate_lemma="has_property",
                        object_lemma=mod.lemma,
                        representation_type=PropositionType.PROPERTY,
                        polarity=Polarity.POSITIVE,
                        modality=Modality.ASSERTED,
                        source_text=doc_text[c_start:c_end] if c_start >= 0 else f"{mod.text} {noun.text}",
                        char_start=c_start,
                        char_end=c_end,
                        sentence_index=sent_idx,
                        token_indices=tuple(tok_indices),
                        dependency_evidence=(mod.dep, noun.dep),
                        properties={
                            "fragment_type": "entity_property",
                            "entity": noun.lemma,
                            "property": mod.lemma,
                        },
                    )
                )
        return propositions

    def _extract_coordinate_concepts(
        self,
        root: ParsedToken,
        children: List[ParsedToken],
        parsed_sent: ParsedSentence,
        sent_idx: int,
        doc_text: str,
    ) -> List[RobustProposition]:
        """
        Extract canonical concept propositions for coordinate items (e.g. 'Abstraction and reusability').
        Produces distinct propositions for each coordinate item so partial coverage is rewarded.
        """
        propositions: List[RobustProposition] = []
        
        # Collect all coordinate heads and conjuncts
        conj_tokens = [t for t in parsed_sent.tokens if t.dep == "conj" and t.pos in ("NOUN", "PROPN")]
        if not conj_tokens:
            return []

        seen_indices: Set[int] = set()
        for conj in conj_tokens:
            head = parsed_sent.tokens[conj.head_index]
            for target in (head, conj):
                if target.index in seen_indices or target.pos not in ("NOUN", "PROPN"):
                    continue
                seen_indices.add(target.index)

                target_children = parsed_sent.get_children(target)
                compound_mods = [c for c in target_children if c.dep in ("compound", "amod")]
                tok_indices = sorted([target.index] + [c.index for c in compound_mods])
                c_start, c_end = self._compute_token_span(tok_indices, parsed_sent, doc_text)

                full_concept_text = " ".join(parsed_sent.tokens[i].text for i in tok_indices)
                full_concept_lemma = " ".join(parsed_sent.tokens[i].lemma for i in tok_indices)

                propositions.append(
                    RobustProposition(
                        subject="concept",
                        predicate="includes",
                        object=full_concept_text,
                        subject_lemma="concept",
                        predicate_lemma="include",
                        object_lemma=full_concept_lemma,
                        representation_type=PropositionType.RELATIONAL_FRAGMENT,
                        polarity=Polarity.POSITIVE,
                        modality=Modality.ASSERTED,
                        source_text=doc_text[c_start:c_end] if c_start >= 0 else full_concept_text,
                        char_start=c_start,
                        char_end=c_end,
                        sentence_index=sent_idx,
                        token_indices=tuple(tok_indices),
                        dependency_evidence=tuple(parsed_sent.tokens[i].dep for i in tok_indices),
                        properties={
                            "fragment_type": "coordinate_concept",
                            "concept_lemma": target.lemma,
                            "compound_modifiers": [c.lemma for c in compound_mods],
                        },
                    )
                )

        return propositions

    def _extract_prepositional_root(
        self,
        root: ParsedToken,
        children: List[ParsedToken],
        parsed_sent: ParsedSentence,
        sent_idx: int,
        doc_text: str,
    ) -> List[RobustProposition]:
        """
        Extract prepositional root phrase (e.g. 'At the main function', 'by reference').
        """
        propositions: List[RobustProposition] = []
        pobjs = [c for c in children if c.dep in ("pobj", "obj")]

        for pobj in pobjs:
            pobj_children = parsed_sent.get_children(pobj)
            amods = [c for c in pobj_children if c.dep in ("amod", "compound")]
            tok_indices = sorted([root.index, pobj.index] + [c.index for c in amods])
            c_start, c_end = self._compute_token_span(tok_indices, parsed_sent, doc_text)

            propositions.append(
                RobustProposition(
                    subject=None,
                    predicate=root.text,
                    object=pobj.text,
                    subject_lemma=None,
                    predicate_lemma=root.lemma,
                    object_lemma=pobj.lemma,
                    representation_type=PropositionType.RELATIONAL_FRAGMENT,
                    polarity=Polarity.POSITIVE,
                    modality=Modality.ASSERTED,
                    source_text=doc_text[c_start:c_end] if c_start >= 0 else f"{root.text} {pobj.text}",
                    char_start=c_start,
                    char_end=c_end,
                    sentence_index=sent_idx,
                    token_indices=tuple(tok_indices),
                    dependency_evidence=(root.dep, pobj.dep),
                    properties={
                        "fragment_type": "prepositional_root",
                        "object_modifiers": [c.lemma for c in amods],
                    },
                )
            )

        return propositions

    def _extract_xcomp_clauses(
        self,
        parsed_sent: ParsedSentence,
        sent_idx: int,
        doc_text: str,
    ) -> List[RobustProposition]:
        """
        Extract purpose / complement clauses (e.g. 'A destructor is used to deallocate memory and clean up after class objects').
        Inherits subject from matrix clause if unexpressed, and extracts conjoined complement verbs.
        """
        propositions: List[RobustProposition] = []
        for tok in parsed_sent.tokens:
            if tok.dep == "xcomp" and tok.pos in ("VERB", "AUX"):
                head = parsed_sent.tokens[tok.head_index]
                subj_tok = next((c for c in parsed_sent.get_children(head) if "subj" in c.dep), None)

                # Collect root xcomp verb plus any conjoined complement verbs
                action_verbs = [tok] + [
                    c for c in parsed_sent.get_children(tok)
                    if c.dep == "conj" and c.pos in ("VERB", "AUX")
                ]

                for v in action_verbs:
                    v_children = parsed_sent.get_children(v)
                    obj_tok = next((c for c in v_children if c.dep in ("dobj", "obj", "attr")), None)
                    prep = next((c for c in v_children if c.dep == "prep"), None)
                    pobj = None
                    if prep:
                        pobj = next((c for c in parsed_sent.get_children(prep) if c.dep in ("pobj", "obj")), None)

                    target_obj = obj_tok or pobj
                    tok_indices = [v.index]
                    if subj_tok:
                        tok_indices.append(subj_tok.index)
                    if target_obj:
                        tok_indices.append(target_obj.index)
                    tok_indices.sort()

                    c_start, c_end = self._compute_token_span(tok_indices, parsed_sent, doc_text)
                    prep_args = _collect_prep_arguments(parsed_sent, v)
                    pred_mods = list(_collect_predicate_modifiers(parsed_sent, v))

                    propositions.append(
                        RobustProposition(
                            subject=subj_tok.text if subj_tok else None,
                            predicate=v.text,
                            object=target_obj.text if target_obj else None,
                            subject_lemma=subj_tok.lemma if subj_tok else None,
                            predicate_lemma=v.lemma,
                            object_lemma=target_obj.lemma if target_obj else None,
                            representation_type=PropositionType.TRIPLE if subj_tok else PropositionType.ARGUMENT_STRUCTURE,
                            polarity=Polarity.POSITIVE,
                            modality=Modality.ASSERTED,
                            source_text=doc_text[c_start:c_end] if c_start >= 0 else v.text,
                            char_start=c_start,
                            char_end=c_end,
                            sentence_index=sent_idx,
                            token_indices=tuple(tok_indices),
                            dependency_evidence=(v.dep,),
                            properties={
                                "clause_type": "xcomp_purpose",
                                "prepositional_arguments": [list(x) for x in dict.fromkeys(prep_args)],
                                "predicate_modifiers": pred_mods,
                            },
                        )
                    )
        return propositions

    def _compute_token_span(
        self, token_indices: List[int], parsed_sent: ParsedSentence, doc_text: str
    ) -> Tuple[int, int]:
        """Compute character offsets for a sequence of token indices."""
        if not token_indices or not parsed_sent.tokens:
            return (-1, -1)

        valid_indices = [i for i in token_indices if 0 <= i < parsed_sent.token_count]
        if not valid_indices:
            return (-1, -1)

        first_tok = parsed_sent.tokens[min(valid_indices)]
        last_tok = parsed_sent.tokens[max(valid_indices)]

        sent_text = parsed_sent.original_text
        sent_start = doc_text.find(sent_text) if (doc_text and sent_text) else -1

        if sent_start >= 0:
            char_start = sent_start + first_tok.char_offset
            char_end = sent_start + last_tok.char_offset + len(last_tok.text)
            return (char_start, char_end)

        return (first_tok.char_offset, last_tok.char_offset + len(last_tok.text))

    def _deduplicate(self, props: List[RobustProposition]) -> List[RobustProposition]:
        """Deduplicate propositions while preserving linguistic provenance."""
        seen: Set[Tuple[Optional[str], str, Optional[str], str]] = set()
        deduped: List[RobustProposition] = []

        for p in props:
            key = (p.subject_lemma, p.predicate_lemma, p.object_lemma, p.representation_type.value)
            if key not in seen:
                seen.add(key)
                deduped.append(p)

        return deduped
