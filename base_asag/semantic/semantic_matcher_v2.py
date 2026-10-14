"""
Extended Semantic Matcher (Phase 3: SemanticMatcherV1 and SemanticMatcherV2).

Improves lexical and semantic similarity between terms while strictly preserving
interpretability and avoiding opaque neural black-boxes.

Matcher Versions:
- SemanticMatcherV1: Existing interpretable Stage 6 comparator
  (exact -> lemma -> POS compatibility -> WordNet path).
- SemanticMatcherV2: Extended multi-tier hierarchy:
  1. Exact surface equality
  2. Lemma equality
  3. Controlled morphological derivation (WordNet derivational forms)
  4. Curated domain lexical equivalence (common computer science terms)
  5. WordNet synset synonymy and path similarity
  6. Optional distributional vector similarity (bounded and gated)
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple

import nltk
from nltk.corpus import wordnet as wn

from base_asag.semantic.domain_lexicon import DOMAIN_LEXICAL_EQUIVALENCES
from base_asag.semantic.relations import (
    LexicalSemanticComparator,
    SemanticRelation,
    is_pos_compatible,
    map_pos_to_wordnet,
)

# Aliasing existing Stage 6 matcher as SemanticMatcherV1
SemanticMatcherV1 = LexicalSemanticComparator


class SemanticMatcherV2:
    """
    Tiered semantic matcher incorporating morphological derivation,
    controlled domain equivalence, and optional vector similarity.
    """

    # Transparent, domain-specific lexical equivalences commonly found in computer science
    # (Delegated to curated domain_lexicon registry)
    DOMAIN_LEXICAL_EQUIVALENCES: Dict[str, Set[str]] = DOMAIN_LEXICAL_EQUIVALENCES

    def __init__(
        self,
        wn_corpus: Optional[Any] = None,
        use_domain_equivalence: bool = True,
        use_morphology: bool = True,
        distributional_model: Optional[Any] = None,
        path_similarity_threshold: float = 0.50,
    ) -> None:
        self.wn = wn_corpus or wn
        self.use_domain_equivalence = use_domain_equivalence
        self.use_morphology = use_morphology
        self.distributional_model = distributional_model
        self.path_similarity_threshold = path_similarity_threshold
        self._v1 = SemanticMatcherV1(wn_corpus=self.wn)

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
        Compare two lexical items using the V2 extended hierarchy.
        """
        src_text, src_lemma, src_pos = self._v1._extract_token_attributes(
            source, source_lemma, source_pos
        )
        tgt_text, tgt_lemma, tgt_pos = self._v1._extract_token_attributes(
            target, target_lemma, target_pos
        )

        s_clean = src_text.strip().lower()
        t_clean = tgt_text.strip().lower()
        s_lem = src_lemma.strip().lower()
        t_lem = tgt_lemma.strip().lower()

        if source_lemma is None:
            morph = self.wn.morphy(s_clean)
            if morph:
                s_lem = morph.lower()
        if target_lemma is None:
            morph = self.wn.morphy(t_clean)
            if morph:
                t_lem = morph.lower()

        # Tier 1: Exact Surface Match
        if s_clean == t_clean:
            return SemanticRelation(
                source_text=src_text,
                target_text=tgt_text,
                source_lemma=src_lemma,
                target_lemma=tgt_lemma,
                source_pos=src_pos,
                target_pos=tgt_pos,
                exact_match=True,
                lemma_match=True,
                pos_compatible=True,
                semantic_relation="EXACT_MATCH",
                similarity_score=1.0,
                method="exact_match",
            )

        # Tier 2: Lemma Match
        if s_lem == t_lem:
            return SemanticRelation(
                source_text=src_text,
                target_text=tgt_text,
                source_lemma=src_lemma,
                target_lemma=tgt_lemma,
                source_pos=src_pos,
                target_pos=tgt_pos,
                exact_match=False,
                lemma_match=True,
                pos_compatible=True,
                semantic_relation="LEMMA_MATCH",
                similarity_score=0.95,
                method="lemma_match",
            )

        # Tier 3: Controlled Morphological Derivation (WordNet)
        if self.use_morphology:
            morph_match = self._check_morphological_derivation(s_lem, t_lem)
            if morph_match:
                return SemanticRelation(
                    source_text=src_text,
                    target_text=tgt_text,
                    source_lemma=src_lemma,
                    target_lemma=tgt_lemma,
                    source_pos=src_pos,
                    target_pos=tgt_pos,
                    exact_match=False,
                    lemma_match=False,
                    pos_compatible=True,
                    semantic_relation="MORPHOLOGICAL_DERIVATION",
                    similarity_score=0.85,
                    method="morphological_derivation",
                )

        # Tier 4: Domain Lexical Equivalence
        if self.use_domain_equivalence:
            if s_lem in self.DOMAIN_LEXICAL_EQUIVALENCES and t_lem in self.DOMAIN_LEXICAL_EQUIVALENCES[s_lem]:
                return SemanticRelation(
                    source_text=src_text,
                    target_text=tgt_text,
                    source_lemma=src_lemma,
                    target_lemma=tgt_lemma,
                    source_pos=src_pos,
                    target_pos=tgt_pos,
                    exact_match=False,
                    lemma_match=False,
                    pos_compatible=True,
                    semantic_relation="DOMAIN_LEXICAL_EQUIVALENCE",
                    similarity_score=0.80,
                    method="domain_lexical_equivalence",
                )

        # Tier 5: WordNet Synonymy & Path Similarity (via V1 with sense dominance gating)
        v1_rel = self._v1.compare(
            src_text, tgt_text,
            source_lemma=src_lemma, target_lemma=tgt_lemma,
            source_pos=src_pos, target_pos=tgt_pos,
        )
        if v1_rel.similarity_score >= self.path_similarity_threshold:
            # Sense dominance gate on WORDNET_SYNONYM for verbs
            if v1_rel.semantic_relation == "WORDNET_SYNONYM" and (v1_rel.source_pos == "VERB" or v1_rel.target_pos == "VERB"):
                s1_list = self.wn.synsets(v1_rel.source_lemma.lower(), pos=wn.VERB)
                s2_list = self.wn.synsets(v1_rel.target_lemma.lower(), pos=wn.VERB)
                if s1_list and s2_list:
                    common = set(s1_list).intersection(set(s2_list))
                    if common:
                        best_syn = min(common, key=lambda s: s1_list.index(s) + s2_list.index(s))
                        r1 = s1_list.index(best_syn)
                        r2 = s2_list.index(best_syn)
                        # If neither word has this sense as primary (0) or secondary (1)
                        if min(r1, r2) > 1:
                            factor = 1.0 / (1.0 + 0.35 * (r1 + r2))
                            new_score = round(1.0 * factor, 4)
                            discounted_rel = SemanticRelation(
                                source_text=v1_rel.source_text,
                                target_text=v1_rel.target_text,
                                source_lemma=v1_rel.source_lemma,
                                target_lemma=v1_rel.target_lemma,
                                source_pos=v1_rel.source_pos,
                                target_pos=v1_rel.target_pos,
                                exact_match=v1_rel.exact_match,
                                lemma_match=v1_rel.lemma_match,
                                pos_compatible=v1_rel.pos_compatible,
                                semantic_relation="PERIPHERAL_SYNSET_OVERLAP",
                                similarity_score=new_score,
                                method="wordnet_synonym_discounted",
                                synset_source=best_syn.name(),
                                synset_target=best_syn.name(),
                            )
                            if new_score >= self.path_similarity_threshold:
                                return discounted_rel
                            v1_rel = discounted_rel
                        else:
                            return v1_rel
                    else:
                        return v1_rel
                else:
                    return v1_rel
            else:
                return v1_rel

        # Tier 5b: Fallback when POS is unspecified: search across WordNet synsets
        if v1_rel.semantic_relation == "POS_INCOMPATIBLE" and src_pos is None and tgt_pos is None:
            s1_all = self.wn.synsets(s_lem)
            t1_all = self.wn.synsets(t_lem)
            common = set(s1_all).intersection(set(t1_all))
            if common:
                shared = next(iter(common))
                return SemanticRelation(
                    source_text=src_text,
                    target_text=tgt_text,
                    source_lemma=src_lemma,
                    target_lemma=tgt_lemma,
                    source_pos=None,
                    target_pos=None,
                    exact_match=False,
                    lemma_match=False,
                    pos_compatible=True,
                    semantic_relation="WORDNET_SYNONYM",
                    similarity_score=1.0,
                    method="wordnet_synonym",
                    synset_source=shared.name(),
                    synset_target=shared.name(),
                )
            best_sim = 0.0
            best_s1 = None
            best_s2 = None
            for s1 in s1_all:
                for s2 in t1_all:
                    if s1.pos() == s2.pos():
                        sim = s1.path_similarity(s2) or 0.0
                        if sim > best_sim:
                            best_sim = sim
                            best_s1 = s1
                            best_s2 = s2
            if best_sim >= self.path_similarity_threshold:
                return SemanticRelation(
                    source_text=src_text,
                    target_text=tgt_text,
                    source_lemma=src_lemma,
                    target_lemma=tgt_lemma,
                    source_pos=None,
                    target_pos=None,
                    exact_match=False,
                    lemma_match=False,
                    pos_compatible=True,
                    semantic_relation="WORDNET_PATH",
                    similarity_score=round(best_sim, 6),
                    method="wordnet_path",
                    synset_source=best_s1.name() if best_s1 else None,
                    synset_target=best_s2.name() if best_s2 else None,
                )

        # Tier 6: Optional Distributional Vector Similarity
        if self.distributional_model is not None:
            dist_sim = self._compute_distributional_similarity(s_lem, t_lem)
            if dist_sim >= 0.60:
                score = round(0.50 + 0.30 * ((dist_sim - 0.60) / 0.40), 4)
                return SemanticRelation(
                    source_text=src_text,
                    target_text=tgt_text,
                    source_lemma=src_lemma,
                    target_lemma=tgt_lemma,
                    source_pos=src_pos,
                    target_pos=tgt_pos,
                    exact_match=False,
                    lemma_match=False,
                    pos_compatible=True,
                    semantic_relation="DISTRIBUTIONAL_SIMILARITY",
                    similarity_score=score,
                    method="distributional_similarity",
                )

        # Fallback: No relation
        return v1_rel

    def _check_morphological_derivation(self, lemma1: str, lemma2: str) -> bool:
        """Check if lemma1 and lemma2 share a derivational relationship in WordNet."""
        syns1 = self.wn.synsets(lemma1)
        for s in syns1:
            for l in s.lemmas():
                for d in l.derivationally_related_forms():
                    if d.name().lower() == lemma2:
                        return True

        syns2 = self.wn.synsets(lemma2)
        for s in syns2:
            for l in s.lemmas():
                for d in l.derivationally_related_forms():
                    if d.name().lower() == lemma1:
                        return True
        return False

    def _compute_distributional_similarity(self, word1: str, word2: str) -> float:
        """Compute cosine similarity using an optional distributional model."""
        try:
            if hasattr(self.distributional_model, "similarity"):
                doc1 = self.distributional_model(word1)
                doc2 = self.distributional_model(word2)
                if doc1.has_vector and doc2.has_vector:
                    return float(doc1.similarity(doc2))
        except Exception:
            pass
        return 0.0
