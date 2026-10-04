"""
Question-Aware Relevance Analysis for Unmatched Student Propositions (Phase 2).

This module replaces surface topic checks with explicit question-aware relevance
evaluation. For every unmatched proposition, it determines:
1. What concepts/entities does the proposition discuss?
2. What semantic concepts and focus terms are requested by the question?
3. Does the proposition address the information requested by the question?

All features are fully interpretable (lexical overlap, lemma overlap, concept
affinity, predicate relevance, and question type awareness).
The score is explicitly termed `evidence_strength` or `relevance_score`,
NEVER a probability.
"""

from dataclasses import dataclass, field
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from nltk.corpus import wordnet as wn

from base_asag.dependency.parser import DependencyParser, ParsedDocument, ParsedToken
from base_asag.representation.hybrid import RobustProposition


@dataclass(frozen=True)
class QuestionAnalysis:
    """Structured linguistic analysis of an assessment question."""
    question_text: str
    question_type: str
    focus_terms: Tuple[str, ...]
    focus_lemmas: Tuple[str, ...]
    predicates: Tuple[str, ...]
    entities: Tuple[str, ...]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "question_text": self.question_text,
            "question_type": self.question_type,
            "focus_terms": list(self.focus_terms),
            "focus_lemmas": list(self.focus_lemmas),
            "predicates": list(self.predicates),
            "entities": list(self.entities),
        }


@dataclass(frozen=True)
class RelevanceEvidence:
    """
    Structured evidence of question-aware relevance for an unmatched proposition.
    The numeric evaluation is strictly `evidence_strength` / `relevance_score`,
    not a statistical probability.
    """
    question_similarity: float
    concept_overlap: float
    predicate_relevance: float
    lexical_evidence: Dict[str, Any]
    semantic_evidence: Dict[str, Any]
    evidence_strength: float
    is_relevant: bool
    evidence_explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "question_similarity": round(self.question_similarity, 4),
            "concept_overlap": round(self.concept_overlap, 4),
            "predicate_relevance": round(self.predicate_relevance, 4),
            "lexical_evidence": self.lexical_evidence,
            "semantic_evidence": self.semantic_evidence,
            "evidence_strength": round(self.evidence_strength, 4),
            "is_relevant": self.is_relevant,
            "evidence_explanation": self.evidence_explanation,
        }


class QuestionAnalyzer:
    """Extracts semantic focus terms, predicates, and question types from questions."""

    STOP_WORDS = {
        "what", "where", "when", "why", "how", "who", "which",
        "is", "are", "was", "were", "do", "does", "did", "can", "could",
        "the", "a", "an", "in", "on", "at", "by", "for", "with", "about",
        "between", "of", "and", "or", "to", "from", "program", "c++"
    }

    def __init__(self, parser: Optional[DependencyParser] = None) -> None:
        self._parser = parser or DependencyParser(model_name="en_core_web_sm")

    def analyze(self, question_text: str) -> QuestionAnalysis:
        """Analyze question text to extract focus concepts and question type."""
        q_lower = question_text.strip().lower()

        # Question Type Heuristics
        q_type = "GENERAL"
        if "difference" in q_lower or "distinguish" in q_lower or "versus" in q_lower or " vs" in q_lower:
            q_type = "DIFFERENCE"
        elif "similar" in q_lower or "similarity" in q_lower or "alike" in q_lower:
            q_type = "SIMILARITY"
        elif q_lower.startswith("where") or "where " in q_lower:
            q_type = "LOCATION_OR_SCOPE"
        elif q_lower.startswith("how") or "how " in q_lower:
            q_type = "MECHANISM_OR_PROCESS"
        elif q_lower.startswith("why") or "why " in q_lower:
            q_type = "REASON_OR_PURPOSE"
        elif "purpose" in q_lower or "advantage" in q_lower or "role" in q_lower:
            q_type = "PURPOSE_OR_ADVANTAGE"
        elif q_lower.startswith("what"):
            q_type = "DEFINITION_OR_PROPERTY"

        parsed = self._parser.parse_document(question_text)

        focus_terms: List[str] = []
        focus_lemmas: List[str] = []
        predicates: List[str] = []
        entities: List[str] = []

        for sent in parsed.sentences:
            for tok in sent.tokens:
                lemma = tok.lemma.lower()
                text = tok.text.lower()
                if lemma not in self.STOP_WORDS and len(lemma) > 1 and not tok.is_punct:
                    if tok.pos in ("NOUN", "PROPN"):
                        focus_terms.append(text)
                        focus_lemmas.append(lemma)
                        entities.append(lemma)
                    elif tok.pos == "ADJ":
                        focus_terms.append(text)
                        focus_lemmas.append(lemma)
                    elif tok.pos in ("VERB", "AUX") and lemma not in ("be", "have", "do"):
                        predicates.append(lemma)
                        focus_terms.append(text)
                        focus_lemmas.append(lemma)

        return QuestionAnalysis(
            question_text=question_text,
            question_type=q_type,
            focus_terms=tuple(focus_terms),
            focus_lemmas=tuple(focus_lemmas),
            predicates=tuple(predicates),
            entities=tuple(entities),
        )


class QuestionAwareRelevanceAnalyzer:
    """
    Evaluates whether an unmatched proposition is question-relevant
    using interpretable concept overlap and semantic affinity.
    """

    def __init__(
        self,
        relevance_threshold: float = 0.35,
        analyzer: Optional[QuestionAnalyzer] = None,
    ) -> None:
        self.relevance_threshold = relevance_threshold
        self.question_analyzer = analyzer or QuestionAnalyzer()

    def evaluate(
        self,
        proposition: RobustProposition,
        question: str,
        reference_answer: Optional[str] = None,
    ) -> RelevanceEvidence:
        """
        Evaluate question-aware relevance for a given proposition.
        """
        q_analysis = self.question_analyzer.analyze(question)

        # 1. Collect proposition concepts
        prop_concepts: Set[str] = set()
        prop_lemmas: Set[str] = set()

        if proposition.subject_lemma:
            prop_concepts.add(proposition.subject_lemma.lower())
            prop_lemmas.add(proposition.subject_lemma.lower())
        if proposition.predicate_lemma and proposition.predicate_lemma.lower() not in ("be", "have", "do", "and"):
            prop_concepts.add(proposition.predicate_lemma.lower())
            prop_lemmas.add(proposition.predicate_lemma.lower())
        if proposition.object_lemma:
            prop_concepts.add(proposition.object_lemma.lower())
            prop_lemmas.add(proposition.object_lemma.lower())

        for k, v in proposition.properties.items():
            if isinstance(v, str) and len(v) > 1:
                prop_concepts.add(v.lower())

        # 2. Extract reference concepts if available
        ref_lemmas: Set[str] = set()
        if reference_answer:
            ref_parsed = self.question_analyzer._parser.parse_document(reference_answer)
            for s in ref_parsed.sentences:
                for t in s.tokens:
                    if t.pos in ("NOUN", "PROPN", "VERB", "ADJ") and not t.is_stop and len(t.lemma) > 1:
                        ref_lemmas.add(t.lemma.lower())

        # Target concepts = question focus lemmas + reference lemmas
        target_focus = set(q_analysis.focus_lemmas)
        all_target_concepts = target_focus | ref_lemmas

        # 3. Compute Concept Overlap
        exact_concept_matches = prop_concepts & target_focus
        context_concept_matches = prop_concepts & all_target_concepts

        if not target_focus and not all_target_concepts:
            concept_overlap = 0.5  # Neutral default
        else:
            denom = max(1, len(prop_concepts))
            overlap_count = len(context_concept_matches)
            concept_overlap = min(1.0, overlap_count / denom)

        # 4. Compute Predicate Relevance
        predicate_relevance = 0.0
        prop_pred = proposition.predicate_lemma.lower()
        if prop_pred in ("be", "have", "do", "and"):
            # Copular or fragment predicates inherit relevance from arguments
            predicate_relevance = 0.5 if context_concept_matches else 0.2
        elif q_analysis.predicates:
            sims = [
                self._compute_wordnet_similarity(prop_pred, q_p)
                for q_p in q_analysis.predicates
            ]
            predicate_relevance = max(sims) if sims else 0.0
        elif context_concept_matches:
            predicate_relevance = 0.5
        else:
            predicate_relevance = 0.2

        # 5. Question Similarity (Overall Jaccard on content words)
        q_tokens = set(q_analysis.focus_lemmas)
        union = prop_concepts | q_tokens
        question_similarity = len(prop_concepts & q_tokens) / max(1, len(union))

        # 6. Combined Evidence Strength (Weighted Linear Combination, NOT Probability)
        evidence_strength = (
            0.45 * concept_overlap +
            0.35 * question_similarity +
            0.20 * predicate_relevance
        )

        # Boost if direct focus entity match
        if exact_concept_matches:
            evidence_strength = min(1.0, evidence_strength + 0.15)

        is_relevant = evidence_strength >= self.relevance_threshold

        explanation = (
            f"Concept overlap={concept_overlap:.2f} ({len(context_concept_matches)} matched), "
            f"Question similarity={question_similarity:.2f}, "
            f"Predicate relevance={predicate_relevance:.2f}, "
            f"Question type='{q_analysis.question_type}', "
            f"Evidence strength={evidence_strength:.2f} "
            f"({'RELEVANT' if is_relevant else 'IRRELEVANT'} against threshold {self.relevance_threshold})"
        )

        return RelevanceEvidence(
            question_similarity=question_similarity,
            concept_overlap=concept_overlap,
            predicate_relevance=predicate_relevance,
            lexical_evidence={
                "exact_concept_matches": sorted(list(exact_concept_matches)),
                "context_concept_matches": sorted(list(context_concept_matches)),
                "prop_concepts": sorted(list(prop_concepts)),
            },
            semantic_evidence={
                "question_type": q_analysis.question_type,
                "target_predicates": list(q_analysis.predicates),
            },
            evidence_strength=evidence_strength,
            is_relevant=is_relevant,
            evidence_explanation=explanation,
        )

    def _compute_wordnet_similarity(self, word1: str, word2: str) -> float:
        """Compute maximum path similarity between word synsets."""
        if word1 == word2:
            return 1.0

        syns1 = wn.synsets(word1, pos=wn.VERB)
        syns2 = wn.synsets(word2, pos=wn.VERB)
        if not syns1 or not syns2:
            syns1 = wn.synsets(word1)
            syns2 = wn.synsets(word2)

        if not syns1 or not syns2:
            return 0.0

        max_sim = 0.0
        for s1 in syns1[:3]:
            for s2 in syns2[:3]:
                sim = s1.path_similarity(s2)
                if sim and sim > max_sim:
                    max_sim = sim
        return max_sim
