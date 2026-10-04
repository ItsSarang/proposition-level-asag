"""
Lexical and Semantic Relationship Component for Base ASAG.

This module provides the Stage 6 semantic and lexical relationship component
for the Base ASAG system. It determines how two lexical items relate at
increasingly semantic levels:

1. Exact surface-form equality
2. Lemma equality
3. POS compatibility
4. WordNet-based semantic relationship / similarity

Crucially, exact and lemma matches are resolved without WordNet lookups,
preserving computational efficiency and transparency. General WordNet
relationships are queried only for unresolved, POS-compatible lexical pairs.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple, Union
import nltk
from nltk.corpus import wordnet as wn
from nltk.corpus.reader.wordnet import Synset


# Mapping from Universal POS and Penn Treebank tags to WordNet POS categories
_POS_TO_WORDNET: Dict[str, str] = {
    # Universal POS
    "NOUN": wn.NOUN,
    "PROPN": wn.NOUN,
    "VERB": wn.VERB,
    "ADJ": wn.ADJ,
    "ADV": wn.ADV,
    # WordNet native tags
    "n": wn.NOUN,
    "v": wn.VERB,
    "a": wn.ADJ,
    "r": wn.ADV,
    "s": wn.ADJ_SAT,
}


def map_pos_to_wordnet(pos_tag: Optional[str]) -> Optional[str]:
    """
    Map a Universal POS or Penn Treebank tag to a WordNet POS character ('n', 'v', 'a', 'r').

    Parameters
    ----------
    pos_tag : Optional[str]
        POS tag string (e.g., 'NOUN', 'VERB', 'NN', 'VBZ').

    Returns
    -------
    Optional[str]
        WordNet POS character if compatible, or None if function word / punctuation.
    """
    if not pos_tag or not isinstance(pos_tag, str):
        return None

    cleaned = pos_tag.strip().upper()

    # Direct Universal POS lookup
    if cleaned in _POS_TO_WORDNET:
        return _POS_TO_WORDNET[cleaned]

    # Penn Treebank prefixes
    if cleaned.startswith("NN"):
        return wn.NOUN
    if cleaned.startswith("VB"):
        return wn.VERB
    if cleaned.startswith("JJ"):
        return wn.ADJ
    if cleaned.startswith("RB"):
        return wn.ADV

    return None


def is_pos_compatible(pos1: Optional[str], pos2: Optional[str]) -> bool:
    """
    Check if two POS tags map to the same WordNet POS category.

    Parameters
    ----------
    pos1 : Optional[str]
        First POS tag.
    pos2 : Optional[str]
        Second POS tag.

    Returns
    -------
    bool
        True if both map to the same non-None WordNet category, False otherwise.
    """
    wn_pos1 = map_pos_to_wordnet(pos1)
    wn_pos2 = map_pos_to_wordnet(pos2)
    return wn_pos1 is not None and wn_pos1 == wn_pos2


@dataclass(frozen=True)
class SemanticRelation:
    """
    Represents the semantic/lexical relationship between two terms or tokens.

    Attributes
    ----------
    source_text : str
        Surface string of the source term.
    target_text : str
        Surface string of the target term.
    source_lemma : str
        Lemmatized form of the source term.
    target_lemma : str
        Lemmatized form of the target term.
    source_pos : Optional[str]
        POS tag of the source term.
    target_pos : Optional[str]
        POS tag of the target term.
    exact_match : bool
        Whether surface forms match identically (case-insensitive).
    lemma_match : bool
        Whether lemmas match identically (case-insensitive).
    pos_compatible : bool
        Whether both terms share compatible syntactic categories.
    semantic_relation : str
        Categorical description of relation:
        - "EXACT_MATCH": Identical surface tokens.
        - "LEMMA_MATCH": Identical lemmas.
        - "WORDNET_SYNONYM": Terms share an identical WordNet synset.
        - "WORDNET_PATH": Terms have a valid path similarity in WordNet.
        - "POS_INCOMPATIBLE": Categories differ, preventing WordNet comparison.
        - "NO_SYNSET": One or both lemmas do not exist in WordNet.
        - "NO_RELATION": No semantic path exists in WordNet.
    similarity_score : float
        Bounded continuous score in [0.0, 1.0].
    method : str
        The decision level: "exact_match", "lemma_match", "wordnet_synonym",
        "wordnet_path", "pos_incompatible", or "none".
    synset_source : Optional[str]
        Selected WordNet synset for source term, if applicable.
    synset_target : Optional[str]
        Selected WordNet synset for target term, if applicable.
    """
    source_text: str
    target_text: str
    source_lemma: str
    target_lemma: str
    source_pos: Optional[str]
    target_pos: Optional[str]
    exact_match: bool
    lemma_match: bool
    pos_compatible: bool
    semantic_relation: str
    similarity_score: float
    method: str
    synset_source: Optional[str] = None
    synset_target: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert relation to dictionary format."""
        return {
            "source_text": self.source_text,
            "target_text": self.target_text,
            "source_lemma": self.source_lemma,
            "target_lemma": self.target_lemma,
            "source_pos": self.source_pos,
            "target_pos": self.target_pos,
            "exact_match": self.exact_match,
            "lemma_match": self.lemma_match,
            "pos_compatible": self.pos_compatible,
            "semantic_relation": self.semantic_relation,
            "similarity_score": self.similarity_score,
            "method": self.method,
            "synset_source": self.synset_source,
            "synset_target": self.synset_target,
        }


class LexicalSemanticComparator:
    """
    Compares two lexical items across a multi-tier hierarchy:
    1. Exact surface match
    2. Lemma match
    3. POS compatibility
    4. WordNet path similarity

    WordNet is queried only when exact and lemma matches do not apply.
    """

    def __init__(self, wn_corpus: Optional[Any] = None):
        """
        Initialize the comparator with WordNet corpus access.

        Parameters
        ----------
        wn_corpus : Optional[Any], default=None
            WordNet corpus reader instance. If None, uses nltk.corpus.wordnet.
        """
        if wn_corpus is not None:
            self.wn = wn_corpus
        else:
            try:
                # Test WordNet availability
                wn.synsets("test", pos=wn.NOUN)
                self.wn = wn
            except LookupError as exc:
                raise LookupError(
                    "WordNet corpus data is not installed.\n"
                    "Please download WordNet using:\n"
                    "  python -m nltk.downloader wordnet omw-1.4"
                ) from exc

    def _extract_token_attributes(
        self,
        item: Any,
        explicit_lemma: Optional[str],
        explicit_pos: Optional[str],
    ) -> Tuple[str, str, Optional[str]]:
        """Extract text, lemma, and pos attributes from item or fallback arguments."""
        if item is None:
            raise TypeError("Input term or token cannot be None. Expected str or token object.")

        # Check if item is a token dataclass / object from Stage 3, 4, or 5
        if hasattr(item, "text") and hasattr(item, "lemma"):
            text = str(item.text).strip()
            if not text:
                raise ValueError("Input token text cannot be empty.")
            lemma = str(item.lemma).strip() if item.lemma else text.lower()
            pos = getattr(item, "pos", explicit_pos)
            return text, lemma, pos

        # Raw string handling
        if isinstance(item, str):
            text = item.strip()
            if not text:
                raise ValueError("Input term string cannot be empty or whitespace-only.")
            lemma = explicit_lemma.strip() if explicit_lemma else text.lower()
            pos = explicit_pos.strip() if explicit_pos else None
            return text, lemma, pos

        raise TypeError(
            f"Expected string or token object (ParsedToken/TokenInfo), got {type(item).__name__}."
        )

    def compare(
        self,
        source: Any,
        target: Any,
        source_lemma: Optional[str] = None,
        target_lemma: Optional[str] = None,
        source_pos: Optional[str] = None,
        target_pos: Optional[str] = None,
    ) -> SemanticRelation:
        """
        Compare two lexical items across the 4-level semantic hierarchy.

        Parameters
        ----------
        source : Any
            Source token object (ParsedToken, TokenInfo) or string.
        target : Any
            Target token object (ParsedToken, TokenInfo) or string.
        source_lemma : Optional[str]
            Explicit source lemma if source is a string.
        target_lemma : Optional[str]
            Explicit target lemma if target is a string.
        source_pos : Optional[str]
            Explicit source POS if source is a string.
        target_pos : Optional[str]
            Explicit target POS if target is a string.

        Returns
        -------
        SemanticRelation
            Structured comparison result.
        """
        src_text, src_lem, src_pos = self._extract_token_attributes(
            source, source_lemma, source_pos
        )
        tgt_text, tgt_lem, tgt_pos = self._extract_token_attributes(
            target, target_lemma, target_pos
        )

        pos_compat = is_pos_compatible(src_pos, tgt_pos)

        # ------------------------------------------------------------------
        # Level 1 — Exact Surface Match (Case-Insensitive)
        # ------------------------------------------------------------------
        if src_text.lower() == tgt_text.lower():
            return SemanticRelation(
                source_text=src_text,
                target_text=tgt_text,
                source_lemma=src_lem,
                target_lemma=tgt_lem,
                source_pos=src_pos,
                target_pos=tgt_pos,
                exact_match=True,
                lemma_match=True,
                pos_compatible=pos_compat,
                semantic_relation="EXACT_MATCH",
                similarity_score=1.0,
                method="exact_match",
            )

        # ------------------------------------------------------------------
        # Level 2 — Lemma Match (Case-Insensitive)
        # ------------------------------------------------------------------
        if src_lem.lower() == tgt_lem.lower():
            return SemanticRelation(
                source_text=src_text,
                target_text=tgt_text,
                source_lemma=src_lem,
                target_lemma=tgt_lem,
                source_pos=src_pos,
                target_pos=tgt_pos,
                exact_match=False,
                lemma_match=True,
                pos_compatible=pos_compat,
                semantic_relation="LEMMA_MATCH",
                similarity_score=1.0,
                method="lemma_match",
            )

        # ------------------------------------------------------------------
        # Level 3 — POS Compatibility Check
        # ------------------------------------------------------------------
        wn_pos = map_pos_to_wordnet(src_pos)
        if not pos_compat or wn_pos is None:
            return SemanticRelation(
                source_text=src_text,
                target_text=tgt_text,
                source_lemma=src_lem,
                target_lemma=tgt_lem,
                source_pos=src_pos,
                target_pos=tgt_pos,
                exact_match=False,
                lemma_match=False,
                pos_compatible=pos_compat,
                semantic_relation="POS_INCOMPATIBLE",
                similarity_score=0.0,
                method="pos_incompatible",
            )

        # ------------------------------------------------------------------
        # Level 4 — WordNet Semantic Relationship & Path Similarity
        # ------------------------------------------------------------------
        src_synsets = self.wn.synsets(src_lem.lower(), pos=wn_pos)
        tgt_synsets = self.wn.synsets(tgt_lem.lower(), pos=wn_pos)

        if not src_synsets or not tgt_synsets:
            return SemanticRelation(
                source_text=src_text,
                target_text=tgt_text,
                source_lemma=src_lem,
                target_lemma=tgt_lem,
                source_pos=src_pos,
                target_pos=tgt_pos,
                exact_match=False,
                lemma_match=False,
                pos_compatible=True,
                semantic_relation="NO_SYNSET",
                similarity_score=0.0,
                method="wordnet_path",
            )

        # Check for direct synonymy (shared synset in WordNet)
        common_synsets: Set[Synset] = set(src_synsets).intersection(set(tgt_synsets))
        if common_synsets:
            shared_syn = next(iter(common_synsets))
            return SemanticRelation(
                source_text=src_text,
                target_text=tgt_text,
                source_lemma=src_lem,
                target_lemma=tgt_lem,
                source_pos=src_pos,
                target_pos=tgt_pos,
                exact_match=False,
                lemma_match=False,
                pos_compatible=True,
                semantic_relation="WORDNET_SYNONYM",
                similarity_score=1.0,
                method="wordnet_synonym",
                synset_source=shared_syn.name(),
                synset_target=shared_syn.name(),
            )

        # Calculate maximum path similarity across all candidate synset pairs
        best_score = 0.0
        best_pair: Tuple[Optional[Synset], Optional[Synset]] = (None, None)

        for s1 in src_synsets:
            for s2 in tgt_synsets:
                sim = s1.path_similarity(s2)
                if sim is not None and sim > best_score:
                    best_score = sim
                    best_pair = (s1, s2)

        if best_score > 0.0 and best_pair[0] is not None and best_pair[1] is not None:
            return SemanticRelation(
                source_text=src_text,
                target_text=tgt_text,
                source_lemma=src_lem,
                target_lemma=tgt_lem,
                source_pos=src_pos,
                target_pos=tgt_pos,
                exact_match=False,
                lemma_match=False,
                pos_compatible=True,
                semantic_relation="WORDNET_PATH",
                similarity_score=float(round(best_score, 6)),
                method="wordnet_path",
                synset_source=best_pair[0].name(),
                synset_target=best_pair[1].name(),
            )

        return SemanticRelation(
            source_text=src_text,
            target_text=tgt_text,
            source_lemma=src_lem,
            target_lemma=tgt_lem,
            source_pos=src_pos,
            target_pos=tgt_pos,
            exact_match=False,
            lemma_match=False,
            pos_compatible=True,
            semantic_relation="NO_RELATION",
            similarity_score=0.0,
            method="wordnet_path",
        )

    def compare_tokens(self, source_token: Any, target_token: Any) -> SemanticRelation:
        """
        Convenience wrapper to compare two parsed token objects directly.

        Parameters
        ----------
        source_token : Any
            Stage 3 TokenInfo or Stage 4 ParsedToken.
        target_token : Any
            Stage 3 TokenInfo or Stage 4 ParsedToken.

        Returns
        -------
        SemanticRelation
            Structured comparison result.
        """
        return self.compare(source_token, target_token)
