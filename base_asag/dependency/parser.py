"""
Dependency Parser for Base ASAG.

This module provides the Stage 4 dependency parsing component for the Base ASAG
system, producing structured dependency representations using spaCy's dependency
parser (`en_core_web_sm`).

For each token, it determines its grammatical dependency relation label, its
syntactic head token, and its syntactic dependents. Punctuation, stop words,
and negation markers are strictly preserved.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union
import spacy
from spacy.language import Language
from spacy.tokens import Doc, Span, Token

from base_asag.preprocessing.processor import (
    ProcessedDocument,
    ProcessedSentence,
    normalize_text,
)


@dataclass(frozen=True)
class ParsedToken:
    """
    Structured representation of a parsed token within a syntactic dependency tree.

    Attributes
    ----------
    text : str
        Surface form of the token.
    lemma : str
        Lemmatized base form of the token.
    pos : str
        Coarse-grained Universal POS tag (e.g., NOUN, VERB, DET).
    tag : str
        Fine-grained Penn Treebank POS tag (e.g., NN, VBZ, DT).
    dep : str
        Grammatical dependency relation label (e.g., nsubj, dobj, ROOT, punct).
    head_text : str
        Surface text of this token's syntactic head (governor).
    head_index : int
        Sentence-relative index of the syntactic head token (0-indexed).
    index : int
        Sentence-relative index of this token (0-indexed).
    char_offset : int
        Character offset index in the sentence string.
    is_root : bool
        Whether this token is the syntactic root of the sentence.
    is_stop : bool
        Whether this token is a stop word in spaCy.
    is_punct : bool
        Whether this token is punctuation.
    is_alpha : bool
        Whether this token is purely alphabetic.
    children_indices : Tuple[int, ...]
        Sentence-relative indices of tokens that directly depend on this token.
    doc_index : Optional[int]
        Document-level index of this token, if parsed in a multi-sentence document.
    doc_head_index : Optional[int]
        Document-level index of this token's syntactic head.
    """
    text: str
    lemma: str
    pos: str
    tag: str
    dep: str
    head_text: str
    head_index: int
    index: int
    char_offset: int
    is_root: bool
    is_stop: bool
    is_punct: bool
    is_alpha: bool
    children_indices: Tuple[int, ...] = ()
    doc_index: Optional[int] = None
    doc_head_index: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert token dependency attributes to a dictionary."""
        return {
            "text": self.text,
            "lemma": self.lemma,
            "pos": self.pos,
            "tag": self.tag,
            "dep": self.dep,
            "head_text": self.head_text,
            "head_index": self.head_index,
            "index": self.index,
            "char_offset": self.char_offset,
            "is_root": self.is_root,
            "is_stop": self.is_stop,
            "is_punct": self.is_punct,
            "is_alpha": self.is_alpha,
            "children_indices": list(self.children_indices),
            "doc_index": self.doc_index,
            "doc_head_index": self.doc_head_index,
        }


@dataclass
class ParsedSentence:
    """
    Representation of a parsed sentence containing structured dependency tokens.

    Attributes
    ----------
    original_text : str
        The raw surface text of the sentence.
    normalized_text : str
        The normalized text representation of the sentence.
    tokens : List[ParsedToken]
        List of parsed tokens in sequential sentence order.
    """
    original_text: str
    normalized_text: str
    tokens: List[ParsedToken]

    @property
    def token_count(self) -> int:
        """Total number of tokens in the sentence."""
        return len(self.tokens)

    @property
    def root(self) -> Optional[ParsedToken]:
        """The syntactic root token of the sentence (where dep == 'ROOT')."""
        for tok in self.tokens:
            if tok.is_root or tok.dep.upper() == "ROOT":
                return tok
        return None

    @property
    def lemmas(self) -> List[str]:
        """List of all token lemmas in the sentence."""
        return [tok.lemma for tok in self.tokens]

    @property
    def pos_tags(self) -> List[str]:
        """List of all coarse POS tags in the sentence."""
        return [tok.pos for tok in self.tokens]

    @property
    def dep_labels(self) -> List[str]:
        """List of all dependency relation labels in the sentence."""
        return [tok.dep for tok in self.tokens]

    def get_token(self, index: int) -> ParsedToken:
        """
        Retrieve a token by its sentence-relative index.

        Parameters
        ----------
        index : int
            Index of the token (0 <= index < token_count).

        Returns
        -------
        ParsedToken
            The requested parsed token.
        """
        return self.tokens[index]

    def get_head(self, token: ParsedToken) -> ParsedToken:
        """
        Retrieve the syntactic head (governor) of a token.

        Parameters
        ----------
        token : ParsedToken
            The dependent token.

        Returns
        -------
        ParsedToken
            The syntactic head token.
        """
        return self.tokens[token.head_index]

    def get_children(self, token: ParsedToken) -> List[ParsedToken]:
        """
        Retrieve all syntactic dependents (children) of a token.

        Parameters
        ----------
        token : ParsedToken
            The governor head token.

        Returns
        -------
        List[ParsedToken]
            List of parsed tokens that syntactically depend on the token.
        """
        return [self.tokens[idx] for idx in token.children_indices]

    def to_dict(self) -> Dict[str, Any]:
        """Convert sentence dependency representation to a dictionary."""
        return {
            "original_text": self.original_text,
            "normalized_text": self.normalized_text,
            "token_count": self.token_count,
            "root": self.root.to_dict() if self.root else None,
            "tokens": [t.to_dict() for t in self.tokens],
            "lemmas": self.lemmas,
            "pos_tags": self.pos_tags,
            "dep_labels": self.dep_labels,
        }


@dataclass
class ParsedDocument:
    """
    Representation of a parsed document containing one or more parsed sentences.

    Attributes
    ----------
    original_text : str
        The raw surface text of the entire document.
    normalized_text : str
        The normalized document text.
    sentences : List[ParsedSentence]
        Individual segmented and parsed sentences.
    """
    original_text: str
    normalized_text: str
    sentences: List[ParsedSentence]

    @property
    def sentence_count(self) -> int:
        """Number of sentences in the document."""
        return len(self.sentences)

    @property
    def tokens(self) -> List[ParsedToken]:
        """Flattened list of all parsed tokens across sentences."""
        return [tok for sent in self.sentences for tok in sent.tokens]

    @property
    def lemmas(self) -> List[str]:
        """Flattened list of all lemmas across sentences."""
        return [lem for sent in self.sentences for lem in sent.lemmas]

    @property
    def pos_tags(self) -> List[str]:
        """Flattened list of all coarse POS tags across sentences."""
        return [pos for sent in self.sentences for pos in sent.pos_tags]

    @property
    def dep_labels(self) -> List[str]:
        """Flattened list of all dependency labels across sentences."""
        return [dep for sent in self.sentences for dep in sent.dep_labels]

    @property
    def roots(self) -> List[Optional[ParsedToken]]:
        """List of root tokens for each sentence in the document."""
        return [sent.root for sent in self.sentences]

    def to_dict(self) -> Dict[str, Any]:
        """Convert document dependency representation to a dictionary."""
        return {
            "original_text": self.original_text,
            "normalized_text": self.normalized_text,
            "sentence_count": self.sentence_count,
            "sentences": [s.to_dict() for s in self.sentences],
            "roots": [r.to_dict() if r else None for r in self.roots],
        }


class DependencyParser:
    """
    Syntactic Dependency Parser for Base ASAG.

    Coordinates syntactic parsing using spaCy's dependency parser component
    (`en_core_web_sm`). Consumes Stage 3 ProcessedSentence/ProcessedDocument
    representations or raw strings, generating structured ParsedSentence
    and ParsedDocument representations.
    """

    def __init__(
        self,
        model_name: str = "en_core_web_sm",
        nlp: Optional[Language] = None,
    ):
        """
        Initialize the DependencyParser with an active spaCy dependency parser.

        Parameters
        ----------
        model_name : str, default="en_core_web_sm"
            Name of the spaCy English model to load.
        nlp : Optional[Language], default=None
            Existing spaCy Language object to reuse. If provided, it must have
            an active 'parser' component in its pipeline.
        """
        self.model_name = model_name

        if nlp is not None:
            if "parser" not in nlp.pipe_names:
                raise ValueError(
                    f"Provided spaCy Language pipeline does not include an active 'parser' component. "
                    f"Active components: {nlp.pipe_names}"
                )
            self.nlp = nlp
        else:
            try:
                # Load full spaCy model with the dependency parser enabled
                self.nlp = spacy.load(model_name)
            except OSError as exc:
                raise OSError(
                    f"spaCy English model '{model_name}' is not installed.\n"
                    f"Please install it using:\n"
                    f"  python -m spacy download {model_name}"
                ) from exc

        # Verify parser component is active
        if "parser" not in self.nlp.pipe_names:
            raise RuntimeError(
                f"Loaded spaCy model '{model_name}' is missing the 'parser' component."
            )

    def _parse_spacy_span(
        self,
        span: Union[Doc, Span],
        original_text: str,
        normalized_text: str,
    ) -> ParsedSentence:
        """
        Convert a spaCy Span or Doc into a structured ParsedSentence.

        Calculates sentence-relative token and head indices so every head
        index is a valid lookup within ParsedSentence.tokens.
        """
        span_start = span.start if isinstance(span, Span) else 0
        span_end = span.end if isinstance(span, Span) else len(span)
        span_start_char = span.start_char if isinstance(span, Span) else 0

        parsed_tokens: List[ParsedToken] = []
        for tok in span:
            rel_i = tok.i - span_start

            # Calculate sentence-relative head index
            if tok.head == tok or tok.dep_.upper() == "ROOT":
                rel_head = rel_i
                is_root = True
            elif span_start <= tok.head.i < span_end:
                rel_head = tok.head.i - span_start
                is_root = False
            else:
                # Fallback in case of unexpected cross-span head
                rel_head = rel_i
                is_root = (tok.dep_.upper() == "ROOT")

            # Collect sentence-relative children indices
            children = tuple(
                c.i - span_start
                for c in tok.children
                if span_start <= c.i < span_end
            )

            parsed_tokens.append(
                ParsedToken(
                    text=tok.text,
                    lemma=tok.lemma_,
                    pos=tok.pos_,
                    tag=tok.tag_,
                    dep=tok.dep_,
                    head_text=tok.head.text,
                    head_index=rel_head,
                    index=rel_i,
                    char_offset=tok.idx - span_start_char,
                    is_root=is_root,
                    is_stop=tok.is_stop,
                    is_punct=tok.is_punct,
                    is_alpha=tok.is_alpha,
                    children_indices=children,
                    doc_index=tok.i,
                    doc_head_index=tok.head.i,
                )
            )

        parsed_tokens = self._repair_nominal_root_tokens(parsed_tokens)

        return ParsedSentence(
            original_text=original_text,
            normalized_text=normalized_text,
            tokens=parsed_tokens,
        )

    def _repair_nominal_root_tokens(
        self, tokens: List[ParsedToken]
    ) -> List[ParsedToken]:
        """
        Repair statistical parser errors where a transitive verb is misclassified as
        a compound noun or nominal modifier modifying a nominal root (e.g. 'A compiler converts programs...',
        'A compiler converts high-level source code...').

        In small statistical dependency parsers (e.g. spaCy en_core_web_sm), sequences of
        nouns, ambiguous 3rd-person singular present verbs, and intervening adjectival/nominal
        modifiers are frequently mis-parsed as compound or nmod chunks when preceded by a singular
        determiner ('A', 'An') without a subsequent determiner before the object noun. This linguistic repair:
        1. Checks if the syntactic root is a NOUN/PROPN with NO subject (nsubj/csubj) child.
        2. Ensures no other finite matrix verb exists in the sentence.
        3. Identifies a candidate verb token between the initial subject noun and nominal root
           that possesses verbal synsets in WordNet.
        4. Re-assigns the candidate token as the syntactic ROOT (VERB, VBZ), the preceding
           noun as nsubj, the nominal root as dobj, and updates dependency heads and children.
        """
        if not tokens:
            return tokens

        root = next((t for t in tokens if t.is_root or t.dep.upper() == "ROOT"), None)
        if not root or root.pos not in ("NOUN", "PROPN"):
            return tokens

        # If the root already has an active subject, the parse is structurally grounded
        has_subj = any(
            t.dep in ("nsubj", "csubj") and t.head_index == root.index
            for t in tokens
        )
        if has_subj:
            return tokens

        # If any token is already a root or matrix verb, do not alter
        has_matrix_verb = any(
            t.pos in ("VERB", "AUX") and t.dep in ("ROOT", "ccomp", "conj")
            for t in tokens
        )
        if has_matrix_verb:
            return tokens

        # Search for candidate verb before the nominal root
        cand = None
        subj_cand = None
        is_intransitive = False

        # 1. Search for candidate verb before nominal root (must have verbal morphology e.g. -s, -ed, -ing)
        for t in tokens:
            if t.index < root.index and (
                t.text.endswith("s") or t.text.endswith("ed") or t.text.endswith("ing")
            ):
                try:
                    from nltk.corpus import wordnet as wn
                    v_syns = wn.synsets(t.text.lower(), pos=wn.VERB)
                except Exception:
                    v_syns = []

                if v_syns and t.dep in ("compound", "amod", "nsubj", "nmod"):
                    # Look for subject candidate noun before t
                    for prev in reversed(tokens[: t.index]):
                        if prev.pos in ("NOUN", "PROPN", "PRON") or (
                            prev.dep in ("compound", "amod", "nmod")
                            and wn.synsets(prev.text.lower(), pos=wn.NOUN)
                        ):
                            cand = t
                            subj_cand = prev
                            break
            if cand:
                break

        # 2. If no candidate before root, check if root itself is a verb (intransitive clause)
        if not cand:
            try:
                from nltk.corpus import wordnet as wn
                root_v_syns = wn.synsets(root.text.lower(), pos=wn.VERB)
            except Exception:
                root_v_syns = []

            if root_v_syns and (
                root.text.endswith("s") or root.text.endswith("ed") or root.text.endswith("ing")
            ):
                for prev in reversed(tokens[: root.index]):
                    if prev.pos in ("NOUN", "PROPN", "PRON") or (
                        prev.dep in ("compound", "amod", "nmod")
                        and wn.synsets(prev.text.lower(), pos=wn.NOUN)
                    ):
                        cand = root
                        subj_cand = prev
                        is_intransitive = True
                        break

        if not cand or not subj_cand:
            return tokens

        try:
            from nltk.corpus import wordnet as wn
            v_lemma = wn.morphy(cand.text.lower(), wn.VERB) or cand.lemma
        except Exception:
            v_lemma = cand.lemma

        cand_idx = cand.index
        subj_idx = subj_cand.index
        old_root_idx = root.index

        new_tokens = []
        for t in tokens:
            idx = t.index
            text = t.text
            lemma = t.lemma
            pos = t.pos
            tag = t.tag
            dep = t.dep
            head_text = t.head_text
            head_index = t.head_index
            is_root = t.is_root

            if idx == cand_idx:
                pos = "VERB"
                tag = "VBZ" if text.endswith("s") else "VB"
                dep = "ROOT"
                lemma = v_lemma
                head_index = cand_idx
                head_text = text
                is_root = True
            elif idx == subj_idx:
                dep = "nsubj"
                head_index = cand_idx
                head_text = cand.text
            elif idx == old_root_idx and not is_intransitive:
                dep = "dobj"
                head_index = cand_idx
                head_text = cand.text
                is_root = False
            elif t.dep == "det" and t.head_index == old_root_idx and t.index < subj_idx:
                head_index = subj_idx
                head_text = subj_cand.text
            elif t.is_punct and t.head_index == old_root_idx:
                head_index = cand_idx
                head_text = cand.text

            new_tokens.append(
                ParsedToken(
                    text=text,
                    lemma=lemma,
                    pos=pos,
                    tag=tag,
                    dep=dep,
                    head_text=head_text,
                    head_index=head_index,
                    index=idx,
                    char_offset=t.char_offset,
                    is_root=is_root,
                    is_stop=t.is_stop,
                    is_punct=t.is_punct,
                    is_alpha=t.is_alpha,
                    doc_index=t.doc_index,
                    doc_head_index=t.doc_head_index,
                )
            )

        children_map = {t.index: [] for t in new_tokens}
        for t in new_tokens:
            if not t.is_root:
                children_map[t.head_index].append(t.index)

        return [
            ParsedToken(
                text=t.text,
                lemma=t.lemma,
                pos=t.pos,
                tag=t.tag,
                dep=t.dep,
                head_text=t.head_text,
                head_index=t.head_index,
                index=t.index,
                char_offset=t.char_offset,
                is_root=t.is_root,
                is_stop=t.is_stop,
                is_punct=t.is_punct,
                is_alpha=t.is_alpha,
                children_indices=tuple(sorted(children_map[t.index])),
                doc_index=t.doc_index,
                doc_head_index=t.doc_head_index,
            )
            for t in new_tokens
        ]

    def parse_sentence(
        self,
        sentence: Union[ProcessedSentence, str],
        allow_empty: bool = False,
    ) -> ParsedSentence:
        """
        Parse a single sentence into a structured ParsedSentence representation.

        Parameters
        ----------
        sentence : Union[ProcessedSentence, str]
            A Stage 3 ProcessedSentence instance or a single-sentence string.
        allow_empty : bool, default=False
            Whether empty sentence text is permitted.

        Returns
        -------
        ParsedSentence
            Structured sentence representation with dependency relations and heads.

        Raises
        ------
        TypeError
            If input is neither a string nor a ProcessedSentence.
        ValueError
            If input is empty (when allow_empty=False) or contains multiple sentences.
        """
        if isinstance(sentence, ProcessedSentence):
            raw_text = sentence.original_text
            norm_text = sentence.normalized_text
        elif isinstance(sentence, str):
            if not isinstance(sentence, str):
                raise TypeError(f"Expected str or ProcessedSentence, got {type(sentence).__name__}.")
            if not sentence.strip():
                if allow_empty:
                    return ParsedSentence(original_text=sentence, normalized_text="", tokens=[])
                raise ValueError("Input sentence cannot be empty or contain only whitespace.")
            raw_text = sentence
            norm_text = normalize_text(sentence)
        else:
            raise TypeError(f"Expected str or ProcessedSentence, got {type(sentence).__name__}.")

        spacy_doc = self.nlp(norm_text)
        sents = list(spacy_doc.sents)

        if len(sents) == 0:
            if allow_empty:
                return ParsedSentence(original_text=raw_text, normalized_text=norm_text, tokens=[])
            raise ValueError("Input sentence text did not yield any parseable sentence.")

        if len(sents) > 1:
            raise ValueError(
                f"Expected exactly 1 sentence, but input yielded {len(sents)} sentences. "
                f"Use parse_document() or parse() for multi-sentence inputs."
            )

        return self._parse_spacy_span(
            span=sents[0],
            original_text=raw_text,
            normalized_text=norm_text,
        )

    def parse_document(
        self,
        document: Union[ProcessedDocument, str],
        allow_empty: bool = False,
    ) -> ParsedDocument:
        """
        Parse a document or multi-sentence answer into a structured ParsedDocument.

        Parameters
        ----------
        document : Union[ProcessedDocument, str]
            A Stage 3 ProcessedDocument or a raw document text string.
        allow_empty : bool, default=False
            Whether empty input is accepted.

        Returns
        -------
        ParsedDocument
            Structured document containing segmented and parsed sentences.

        Raises
        ------
        TypeError
            If input is neither a string nor a ProcessedDocument.
        ValueError
            If input is empty or whitespace-only when allow_empty=False.
        """
        if isinstance(document, ProcessedDocument):
            if document.sentence_count == 0:
                if allow_empty:
                    return ParsedDocument(
                        original_text=document.original_text,
                        normalized_text=document.normalized_text,
                        sentences=[],
                    )
                raise ValueError("ProcessedDocument contains zero sentences.")

            parsed_sents: List[ParsedSentence] = []
            for proc_sent in document.sentences:
                spacy_doc = self.nlp(proc_sent.normalized_text)
                # Parse the single sentence span
                sents = list(spacy_doc.sents)
                span = sents[0] if sents else spacy_doc
                parsed_sents.append(
                    self._parse_spacy_span(
                        span=span,
                        original_text=proc_sent.original_text,
                        normalized_text=proc_sent.normalized_text,
                    )
                )

            return ParsedDocument(
                original_text=document.original_text,
                normalized_text=document.normalized_text,
                sentences=parsed_sents,
            )

        elif isinstance(document, str):
            if not document.strip():
                if allow_empty:
                    return ParsedDocument(original_text=document, normalized_text="", sentences=[])
                raise ValueError("Input document cannot be empty or contain only whitespace.")

            raw_text = document
            norm_text = normalize_text(document)
            spacy_doc = self.nlp(norm_text)

            parsed_sents = [
                self._parse_spacy_span(
                    span=sent_span,
                    original_text=sent_span.text,
                    normalized_text=normalize_text(sent_span.text),
                )
                for sent_span in spacy_doc.sents
            ]

            return ParsedDocument(
                original_text=raw_text,
                normalized_text=norm_text,
                sentences=parsed_sents,
            )

        else:
            raise TypeError(f"Expected str or ProcessedDocument, got {type(document).__name__}.")

    def parse(
        self,
        input_data: Union[ProcessedDocument, ProcessedSentence, str],
        allow_empty: bool = False,
    ) -> Union[ParsedDocument, ParsedSentence]:
        """
        Polymorphic parse entry point accepting ProcessedDocument, ProcessedSentence, or string.

        Parameters
        ----------
        input_data : Union[ProcessedDocument, ProcessedSentence, str]
            Input data to parse.
        allow_empty : bool, default=False
            Whether empty input is accepted.

        Returns
        -------
        Union[ParsedDocument, ParsedSentence]
            Parsed representation matching the input structure.
        """
        if isinstance(input_data, ProcessedSentence):
            return self.parse_sentence(input_data, allow_empty=allow_empty)
        if isinstance(input_data, ProcessedDocument):
            return self.parse_document(input_data, allow_empty=allow_empty)
        if isinstance(input_data, str):
            return self.parse_document(input_data, allow_empty=allow_empty)
        raise TypeError(
            f"Expected str, ProcessedSentence, or ProcessedDocument, got {type(input_data).__name__}."
        )
