"""
Additional-Information Classification Module (Stage 13).

This module provides the Stage 13 classification component for the Proposed ASAG
system (System 3). It analyzes student propositions that were left unmatched by the
Base ASAG (Stage 10/11) and structured into proposition representations (Stage 12),
classifying them into:
- CORRECT_ADDITIONAL: Semantically relevant to the question/topic, non-contradictory
  to the reference answer, and introducing valid/consistent supplementary information.
- IRRELEVANT: Unmatched proposition showing insufficient semantic overlap with the
  question or reference answer domain.
- INCORRECT: Unmatched proposition containing assertions that contradict the reference
  answer (via polarity clash, lexical antonymy, or conflicting qualifications).
- UNCERTAIN: Internal fallback category when semantic or factual evidence is ambiguous,
  weak, or borderline, avoiding unjustified binary classification.

Research Boundaries:
--------------------
- Stage 13 is strictly a CLASSIFICATION stage. It does NOT modify the score.
  All unmatched propositions maintain:
    score_effect = 0.0
- Base ASAG normalized score is preserved unchanged.
- Matched propositions remain classified as:
    classification = "MATCHED_BY_BASE_ASAG"
- Stage 13 does NOT use neural sentence embeddings, transformers, or large language models.
- Stage 13 does NOT hardcode demonstration answers or task-specific keywords.
- Unmatched != Incorrect: A proposition not matched to the reference is NOT automatically incorrect.
  Absence of reference support ("NOT_SUPPORTED") does NOT imply contradiction.
"""

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import nltk
from nltk.corpus import wordnet as wn

from base_asag.pipeline import BaseASAGPipelineResult
from base_asag.semantic.relations import LexicalSemanticComparator
from proposed_asag.proposition.representation import (
    DocumentPropositionRepresentation,
    PropositionContext,
    PropositionRepresentation,
    PropositionRepresentationBuilder,
)


# Standard functional and grammatical stopwords to exclude from content term analysis
STOPWORDS: Set[str] = {
    "a", "an", "the", "in", "on", "at", "to", "for", "with", "by", "of", "and", "or",
    "is", "are", "was", "were", "be", "been", "being", "do", "does", "did", "have",
    "has", "had", "can", "could", "shall", "should", "will", "would", "may", "might",
    "must", "it", "this", "that", "these", "those", "what", "which", "who", "whom",
    "how", "when", "where", "why", "there", "their", "its", "each", "every", "all",
    "some", "any", "no", "not", "so", "than", "then", "too", "very", "just", "also",
}

# Semantic opposition clusters for detecting qualification/modifier conflicts
# (e.g. uniqueness vs duplication/multiplicity)
OPPOSITION_CLUSTERS: List[Tuple[Set[str], Set[str]]] = [
    (
        {"unique", "uniquely", "singular", "single", "distinct", "distinctly"},
        {"duplicate", "duplicated", "multiple", "repeated", "copy", "copied", "redundant"},
    ),
    (
        {"allow", "allowed", "permit", "permitted", "enable", "accept", "admit"},
        {"forbid", "forbidden", "prohibit", "prohibited", "disallow", "prevent", "reject", "deny"},
    ),
    (
        {"valid", "validated", "correct", "true"},
        {"invalid", "unvalidated", "incorrect", "false", "wrong"},
    ),
    (
        {"include", "included", "contain", "contains", "held", "hold"},
        {"exclude", "excluded", "omit", "omitted", "reject"},
    ),
    (
        {"present", "exist", "exists", "existing"},
        {"absent", "missing", "nonexistent"},
    ),
    (
        {"mutable", "variable", "changeable", "modifying"},
        {"immutable", "constant", "fixed", "unchanging"},
    ),
]


def _find_wordnet_antonyms(word: str) -> Set[str]:
    """Retrieve explicit lexical antonyms for a lemma from WordNet."""
    antonyms: Set[str] = set()
    cleaned = word.strip().lower()
    for syn in wn.synsets(cleaned):
        for lem in syn.lemmas():
            for ant in lem.antonyms():
                antonyms.add(ant.name().lower())
    return antonyms


def _are_lexical_antonyms(word1: str, word2: str) -> bool:
    """Check if two words are explicit WordNet antonyms."""
    w1 = word1.strip().lower()
    w2 = word2.strip().lower()
    if not w1 or not w2:
        return False
    ants1 = _find_wordnet_antonyms(w1)
    if w2 in ants1:
        return True
    ants2 = _find_wordnet_antonyms(w2)
    return w1 in ants2


def _check_cluster_opposition(word1: str, word2: str) -> bool:
    """Check if two words belong to opposing sides of a defined opposition cluster."""
    w1 = word1.strip().lower()
    w2 = word2.strip().lower()
    if not w1 or not w2:
        return False
    for cluster_a, cluster_b in OPPOSITION_CLUSTERS:
        if (w1 in cluster_a and w2 in cluster_b) or (w1 in cluster_b and w2 in cluster_a):
            return True
    return False


# ---------------------------------------------------------------------------
# Data Structures
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RelevanceEvidence:
    """
    Evidence regarding the relevance of an unmatched proposition to the question/topic.

    Attributes
    ----------
    is_relevant : bool
        Whether the proposition satisfies the semantic relevance threshold.
    score : float
        Bounded continuous relevance score in [0.0, 1.0].
    relevance_threshold : float
        The decision threshold applied.
    matched_question_terms : List[str]
        Question content terms that matched proposition terms.
    matched_reference_terms : List[str]
        Reference content terms that matched proposition terms.
    method : str
        Decision method: "semantic_overlap", "insufficient_overlap", or "empty_terms".
    reasons : List[str]
        Human-readable explanations supporting the relevance assessment.
    details : Dict[str, Any]
        Diagnostic breakdown including max_overlap, mean_overlap, and term similarities.
    """
    is_relevant: bool
    score: float
    relevance_threshold: float
    matched_question_terms: List[str]
    matched_reference_terms: List[str]
    method: str
    reasons: List[str]
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert RelevanceEvidence to a JSON-serializable dictionary."""
        return {
            "is_relevant": self.is_relevant,
            "score": self.score,
            "relevance_threshold": self.relevance_threshold,
            "matched_question_terms": list(self.matched_question_terms),
            "matched_reference_terms": list(self.matched_reference_terms),
            "method": self.method,
            "reasons": list(self.reasons),
            "details": self.details,
        }


@dataclass(frozen=True)
class CompatibilityEvidence:
    """
    Evidence regarding compatibility or contradiction against reference propositions.

    Attributes
    ----------
    reference_support : str
        "NOT_SUPPORTED" (normal for unmatched propositions) or "CONTRADICTED".
    contradiction_status : str
        "NO_CONTRADICTION", "CONTRADICTION_DETECTED", or "UNCERTAIN".
    contradiction_type : Optional[str]
        "POLARITY_CONTRADICTION", "ANTONYM_CONTRADICTION", "MODIFIER_CONFLICT", or None.
    conflicting_reference_index : Optional[int]
        Index of the conflicting reference proposition, if identified.
    conflicting_reference_relation : Optional[Dict[str, Any]]
        Relation dictionary of the conflicting reference proposition, if identified.
    confidence : float
        Confidence score in [0.0, 1.0].
    reasons : List[str]
        Human-readable explanations supporting the compatibility decision.
    details : Dict[str, Any]
        Diagnostic breakdown of slot similarities and contradiction evidence.
    """
    reference_support: str
    contradiction_status: str
    contradiction_type: Optional[str]
    conflicting_reference_index: Optional[int]
    conflicting_reference_relation: Optional[Dict[str, Any]]
    confidence: float
    reasons: List[str]
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert CompatibilityEvidence to a JSON-serializable dictionary."""
        return {
            "reference_support": self.reference_support,
            "contradiction_status": self.contradiction_status,
            "contradiction_type": self.contradiction_type,
            "conflicting_reference_index": self.conflicting_reference_index,
            "conflicting_reference_relation": self.conflicting_reference_relation,
            "confidence": self.confidence,
            "reasons": list(self.reasons),
            "details": self.details,
        }


@dataclass(frozen=True)
class AdditionalInformationResult:
    """
    Classification outcome for an individual unmatched student proposition.

    Attributes
    ----------
    proposition_id : str
        Unique proposition identifier (e.g. "stu_prop_1").
    proposition_index : int
        Zero-based index of the proposition in the student answer.
    text : str
        Surface text span of the proposition.
    classification : str
        "CORRECT_ADDITIONAL", "IRRELEVANT", "INCORRECT", or "UNCERTAIN".
    confidence : float
        Confidence score in [0.0, 1.0].
    relevance : RelevanceEvidence
        Detailed relevance evidence to prompt question and core domain.
    compatibility : CompatibilityEvidence
        Detailed compatibility and contradiction analysis against reference propositions.
    decision_reason : str
        Human-readable summary explanation for the classification.
    score_effect : float
        Score adjustment for this proposition. STRICT INVARIANT: Always 0.0 in Stage 13.
    span : Optional[Dict[str, Any]]
        Character offset and token index provenance from Stage 11/12.
    relation : Optional[Dict[str, Any]]
        Clause relation dictionary from Stage 12.
    polarity : Optional[str]
        Polarity ("POSITIVE" or "NEGATED") from Stage 8/12.
    """
    proposition_id: str
    proposition_index: int
    text: str
    classification: str
    confidence: float
    relevance: RelevanceEvidence
    compatibility: CompatibilityEvidence
    decision_reason: str
    score_effect: float = 0.0
    span: Optional[Dict[str, Any]] = None
    relation: Optional[Dict[str, Any]] = None
    polarity: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert AdditionalInformationResult to a JSON-serializable dictionary."""
        return {
            "proposition_id": self.proposition_id,
            "proposition_index": self.proposition_index,
            "text": self.text,
            "classification": self.classification,
            "confidence": self.confidence,
            "relevance": self.relevance.to_dict(),
            "compatibility": self.compatibility.to_dict(),
            "decision_reason": self.decision_reason,
            "score_effect": self.score_effect,
            "span": self.span,
            "relation": self.relation,
            "polarity": self.polarity,
        }


@dataclass(frozen=True)
class DocumentClassificationResult:
    """
    Top-level classification container for all propositions in an evaluated answer.

    Attributes
    ----------
    student_answer : str
        Input student answer text.
    question : str
        Prompt question text.
    reference_answer : str
        Instructor model reference answer.
    base_asag_normalized_score : float
        Core Base ASAG grade in [0.0, 1.0], preserved unchanged.
    total_student_propositions : int
        Total number of propositions extracted from the student answer.
    matched_count : int
        Number of propositions aligned by the Base ASAG.
    unmatched_count : int
        Number of propositions left unmatched by the Base ASAG.
    correct_additional_count : int
        Count of unmatched propositions classified as CORRECT_ADDITIONAL.
    irrelevant_count : int
        Count of unmatched propositions classified as IRRELEVANT.
    incorrect_count : int
        Count of unmatched propositions classified as INCORRECT.
    uncertain_count : int
        Count of unmatched propositions classified as UNCERTAIN.
    unmatched_classifications : List[AdditionalInformationResult]
        Detailed classification results for all unmatched propositions.
    matched_propositions : List[Dict[str, Any]]
        Matched propositions preserved with classification="MATCHED_BY_BASE_ASAG".
    all_propositions : List[Dict[str, Any]]
        Unified ordered list of all evaluated student propositions.
    summary : Dict[str, Any]
        High-level distribution summary and diagnostic statistics.
    """
    student_answer: str
    question: str
    reference_answer: str
    base_asag_normalized_score: float
    total_student_propositions: int
    matched_count: int
    unmatched_count: int
    correct_additional_count: int
    irrelevant_count: int
    incorrect_count: int
    uncertain_count: int
    unmatched_classifications: List[AdditionalInformationResult]
    matched_propositions: List[Dict[str, Any]]
    all_propositions: List[Dict[str, Any]]
    summary: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert DocumentClassificationResult to a JSON-serializable dictionary."""
        return {
            "student_answer": self.student_answer,
            "question": self.question,
            "reference_answer": self.reference_answer,
            "base_asag_normalized_score": self.base_asag_normalized_score,
            "total_student_propositions": self.total_student_propositions,
            "matched_count": self.matched_count,
            "unmatched_count": self.unmatched_count,
            "correct_additional_count": self.correct_additional_count,
            "irrelevant_count": self.irrelevant_count,
            "incorrect_count": self.incorrect_count,
            "uncertain_count": self.uncertain_count,
            "unmatched_classifications": [c.to_dict() for c in self.unmatched_classifications],
            "matched_propositions": self.matched_propositions,
            "all_propositions": self.all_propositions,
            "summary": self.summary,
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize complete document classification to formatted JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


# ---------------------------------------------------------------------------
# Relevance Analyzer
# ---------------------------------------------------------------------------

class RelevanceAnalyzer:
    """
    Evaluates whether an unmatched proposition is semantically relevant to the question/topic.

    Uses Stage 6 LexicalSemanticComparator to measure semantic overlap between
    proposition content terms (subject, predicate, object, arguments, modifiers)
    and context terms (question and reference answer).
    """

    DEFAULT_RELEVANCE_THRESHOLD = 0.35

    def __init__(
        self,
        comparator: Optional[LexicalSemanticComparator] = None,
        relevance_threshold: float = DEFAULT_RELEVANCE_THRESHOLD,
    ):
        """
        Initialize the RelevanceAnalyzer.

        Parameters
        ----------
        comparator : Optional[LexicalSemanticComparator], default=None
            Lexical/semantic comparator instance from Stage 6.
        relevance_threshold : float, default=0.35
            Continuous threshold above which a proposition is deemed relevant.
        """
        if not (0.0 <= relevance_threshold <= 1.0):
            raise ValueError(
                f"relevance_threshold must be in [0.0, 1.0], got {relevance_threshold}."
            )
        self.comparator = comparator or LexicalSemanticComparator()
        self.relevance_threshold = float(relevance_threshold)

    def extract_proposition_terms(self, prop: PropositionRepresentation) -> Set[str]:
        """
        Extract meaningful content terms and lemmas from a proposition.

        Collects tokens from subject, predicate, object, modifiers, and arguments,
        excluding functional stopwords and punctuation.
        """
        terms: Set[str] = set()

        # Relation slots and lemmas
        rel = prop.relation or {}
        for key in ["subject", "predicate", "object", "subject_lemma", "predicate_lemma", "object_lemma"]:
            val = rel.get(key)
            if val and isinstance(val, str):
                cleaned = val.strip().lower()
                if len(cleaned) > 1 and cleaned not in STOPWORDS:
                    terms.add(cleaned)

        # Modifiers from relation
        for m_list_key in ["subject_modifiers", "object_modifiers", "adverbial_modifiers"]:
            for mod in rel.get(m_list_key, []):
                if isinstance(mod, str):
                    cleaned = mod.strip().lower()
                    if len(cleaned) > 1 and cleaned not in STOPWORDS:
                        terms.add(cleaned)

        # Arguments from linguistics structure
        if hasattr(prop, "linguistics") and prop.linguistics:
            for arg in prop.linguistics.arguments:
                if arg.lemma:
                    cleaned_lem = arg.lemma.strip().lower()
                    if len(cleaned_lem) > 1 and cleaned_lem not in STOPWORDS:
                        terms.add(cleaned_lem)
                for mod in arg.modifiers:
                    cleaned_mod = mod.strip().lower()
                    if len(cleaned_mod) > 1 and cleaned_mod not in STOPWORDS:
                        terms.add(cleaned_mod)

        # Span text tokens as fallback
        if not terms and hasattr(prop, "linguistics") and prop.linguistics:
            for tok in prop.linguistics.lemmas:
                cleaned_tok = tok.strip().lower()
                if len(cleaned_tok) > 1 and cleaned_tok not in STOPWORDS:
                    terms.add(cleaned_tok)

        return terms

    def extract_context_terms(self, context: PropositionContext) -> Tuple[Set[str], Set[str]]:
        """
        Extract content terms from the question and reference answer context.

        Returns
        -------
        Tuple[Set[str], Set[str]]
            (question_terms, reference_terms)
        """
        import re

        def _clean_text_to_terms(text: str) -> Set[str]:
            words = re.findall(r"\b[a-zA-Z0-9_\-]+\b", text.lower())
            return {w for w in words if len(w) > 1 and w not in STOPWORDS}

        q_terms = _clean_text_to_terms(context.question)
        ref_terms = _clean_text_to_terms(context.reference_answer)

        # Add explicit relation lemmas from reference propositions
        for r_rel in context.reference_propositions:
            for key in ["subject", "predicate", "object", "subject_lemma", "predicate_lemma", "object_lemma"]:
                v = r_rel.get(key)
                if v and isinstance(v, str):
                    cleaned = v.strip().lower()
                    if len(cleaned) > 1 and cleaned not in STOPWORDS:
                        ref_terms.add(cleaned)

        return q_terms, ref_terms

    def _compare_terms(
        self,
        w1: str,
        w2: str,
        pos1: Optional[str] = None,
        pos2: Optional[str] = None,
    ) -> float:
        """
        Compare two terms across the 4-level hierarchy with POS fallback for WordNet.

        If explicit POS tags are provided, uses them. Otherwise, checks exact/lemma,
        and if unresolved, tries content POS categories (NOUN, VERB, ADJ).
        """
        if not w1 or not w2:
            return 0.0
        if w1.lower() == w2.lower():
            return 1.0

        # Try with provided POS
        sim = self.comparator.compare(w1, w2, source_pos=pos1, target_pos=pos2).similarity_score
        if sim > 0.0:
            return sim

        # If unresolved and no POS given, try candidate content categories in WordNet
        if not pos1 and not pos2:
            for candidate_pos in ["NOUN", "VERB", "ADJ"]:
                cand_sim = self.comparator.compare(
                    w1, w2, source_pos=candidate_pos, target_pos=candidate_pos
                ).similarity_score
                if cand_sim > sim:
                    sim = cand_sim

        return float(round(sim, 4))

    def analyze(
        self,
        prop: PropositionRepresentation,
        context: PropositionContext,
    ) -> RelevanceEvidence:
        """
        Evaluate relevance of an unmatched proposition against question and reference context.

        Parameters
        ----------
        prop : PropositionRepresentation
            The unmatched student proposition representation.
        context : PropositionContext
            Context containing question and reference answer details.

        Returns
        -------
        RelevanceEvidence
            Structured assessment of topical and question relevance.
        """
        prop_terms = self.extract_proposition_terms(prop)
        q_terms, ref_terms = self.extract_context_terms(context)

        if not prop_terms:
            return RelevanceEvidence(
                is_relevant=False,
                score=0.0,
                relevance_threshold=self.relevance_threshold,
                matched_question_terms=[],
                matched_reference_terms=[],
                method="empty_terms",
                reasons=["Proposition does not contain analyzable content terms."],
                details={"max_overlap": 0.0, "mean_overlap": 0.0, "term_similarities": {}},
            )

        term_sims: Dict[str, Dict[str, float]] = {}
        matched_q: Set[str] = set()
        matched_ref: Set[str] = set()
        all_max_sims: List[float] = []

        for pt in prop_terms:
            best_q_sim = 0.0
            best_q_term = ""
            for qt in q_terms:
                sim = self._compare_terms(pt, qt)
                if sim > best_q_sim:
                    best_q_sim = sim
                    best_q_term = qt

            best_ref_sim = 0.0
            best_ref_term = ""
            for rt in ref_terms:
                sim = self._compare_terms(pt, rt)
                if sim > best_ref_sim:
                    best_ref_sim = sim
                    best_ref_term = rt

            overall_term_sim = max(best_q_sim, best_ref_sim)
            all_max_sims.append(overall_term_sim)

            if best_q_sim >= 0.50 and best_q_term:
                matched_q.add(best_q_term)
            if best_ref_sim >= 0.50 and best_ref_term:
                matched_ref.add(best_ref_term)

            term_sims[pt] = {
                "question_sim": float(round(best_q_sim, 4)),
                "best_q_term": best_q_term,
                "reference_sim": float(round(best_ref_sim, 4)),
                "best_ref_term": best_ref_term,
                "max_sim": float(round(overall_term_sim, 4)),
            }

        max_overlap = max(all_max_sims) if all_max_sims else 0.0
        mean_overlap = (sum(all_max_sims) / len(all_max_sims)) if all_max_sims else 0.0

        # Topic grounding: Check if proposition subject matches question or reference topic
        subj_score = 0.0
        subj = (prop.relation.get("subject_lemma") or prop.relation.get("subject") or "").strip().lower()
        if subj and subj not in STOPWORDS:
            for target_term in q_terms | ref_terms:
                s_sim = self._compare_terms(subj, target_term)
                if s_sim > subj_score:
                    subj_score = s_sim

        # Composite relevance score: 50% topic grounding, 30% max overlap, 20% mean overlap
        composite_score = float(round(
            0.50 * max(subj_score, max_overlap) + 0.30 * max_overlap + 0.20 * mean_overlap,
            4,
        ))

        is_relevant = composite_score >= self.relevance_threshold
        reasons: List[str] = []

        if is_relevant:
            reasons.append(
                f"Proposition demonstrates topic relevance (relevance score: {composite_score:.4f} >= threshold: {self.relevance_threshold:.2f})."
            )
            if matched_q:
                reasons.append(f"Matched question entities: {', '.join(sorted(matched_q))}.")
            if matched_ref:
                reasons.append(f"Matched reference concepts: {', '.join(sorted(matched_ref))}.")
            method = "semantic_overlap"
        else:
            reasons.append(
                f"Proposition shows insufficient semantic relevance (relevance score: {composite_score:.4f} < threshold: {self.relevance_threshold:.2f})."
            )
            reasons.append("Proposition terms lack semantic connection to the prompt question or reference concepts.")
            method = "insufficient_overlap"

        return RelevanceEvidence(
            is_relevant=is_relevant,
            score=composite_score,
            relevance_threshold=self.relevance_threshold,
            matched_question_terms=sorted(list(matched_q)),
            matched_reference_terms=sorted(list(matched_ref)),
            method=method,
            reasons=reasons,
            details={
                "max_overlap": float(round(max_overlap, 4)),
                "mean_overlap": float(round(mean_overlap, 4)),
                "subject_topic_score": float(round(subj_score, 4)),
                "term_similarities": term_sims,
            },
        )


# ---------------------------------------------------------------------------
# Compatibility Analyzer
# ---------------------------------------------------------------------------

class CompatibilityAnalyzer:
    """
    Evaluates whether an unmatched proposition contradicts any reference proposition.

    Inspects:
    1. Polarity opposition on structurally aligned candidate propositions (from Stage 7/11).
    2. Explicit lexical antonymy on corresponding subject/predicate/object slots.
    3. Conflicting property qualifications (e.g. uniqueness vs duplication/multiplicity).
    """

    DEFAULT_CONTRADICTION_THRESHOLD = 0.50

    def __init__(
        self,
        comparator: Optional[LexicalSemanticComparator] = None,
        contradiction_threshold: float = DEFAULT_CONTRADICTION_THRESHOLD,
    ):
        """
        Initialize the CompatibilityAnalyzer.

        Parameters
        ----------
        comparator : Optional[LexicalSemanticComparator], default=None
            Lexical/semantic comparator instance from Stage 6.
        contradiction_threshold : float, default=0.50
            Continuous alignment threshold required to confirm a contradiction.
        """
        if not (0.0 <= contradiction_threshold <= 1.0):
            raise ValueError(
                f"contradiction_threshold must be in [0.0, 1.0], got {contradiction_threshold}."
            )
        self.comparator = comparator or LexicalSemanticComparator()
        self.contradiction_threshold = float(contradiction_threshold)

    def _compare_terms(
        self,
        w1: str,
        w2: str,
        pos1: Optional[str] = None,
        pos2: Optional[str] = None,
    ) -> float:
        """Compare two terms across hierarchy with POS fallback."""
        if not w1 or not w2:
            return 0.0
        if w1.lower() == w2.lower():
            return 1.0
        sim = self.comparator.compare(w1, w2, source_pos=pos1, target_pos=pos2).similarity_score
        if sim > 0.0:
            return sim
        if not pos1 and not pos2:
            for candidate_pos in ["NOUN", "VERB", "ADJ"]:
                cand_sim = self.comparator.compare(
                    w1, w2, source_pos=candidate_pos, target_pos=candidate_pos
                ).similarity_score
                if cand_sim > sim:
                    sim = cand_sim
        return float(round(sim, 4))

    def analyze(
        self,
        prop: PropositionRepresentation,
        context: PropositionContext,
    ) -> CompatibilityEvidence:
        """
        Evaluate compatibility and contradiction for an unmatched proposition.

        Parameters
        ----------
        prop : PropositionRepresentation
            The unmatched student proposition representation.
        context : PropositionContext
            Context containing question and reference answer details.

        Returns
        -------
        CompatibilityEvidence
            Structured assessment of compatibility and potential contradictions.
        """
        # ------------------------------------------------------------------
        # Check 1: Polarity opposition on candidate alignment (from Stage 11)
        # ------------------------------------------------------------------
        best_cand_score = prop.matching.best_candidate_score
        best_cand_rel = prop.matching.best_candidate_relation
        best_cand_idx = prop.matching.best_candidate_reference_index

        if best_cand_score is not None and best_cand_score >= self.contradiction_threshold and best_cand_rel:
            # Candidate alignment was strong, but proposition was unmatched (e.g. competitor or negated)
            # Check polarity of student proposition vs positive reference assumption
            if prop.is_negated:
                reasons = [
                    f"Contradiction detected: Student proposition asserts a negated claim ({', '.join(prop.negation_tokens) or 'negation'}), opposing an aligned reference proposition.",
                    f"Candidate alignment score ({best_cand_score:.4f}) meets contradiction threshold ({self.contradiction_threshold:.2f}).",
                    f"Aligned reference proposition: '{best_cand_rel.get('subject')} {best_cand_rel.get('predicate')} {best_cand_rel.get('object', '')}'.",
                ]
                return CompatibilityEvidence(
                    reference_support="CONTRADICTED",
                    contradiction_status="CONTRADICTION_DETECTED",
                    contradiction_type="POLARITY_CONTRADICTION",
                    conflicting_reference_index=best_cand_idx,
                    conflicting_reference_relation=best_cand_rel,
                    confidence=float(round(best_cand_score, 4)),
                    reasons=reasons,
                    details={"best_candidate_score": best_cand_score, "polarity": prop.polarity},
                )

        # ------------------------------------------------------------------
        # Check 2: Direct comparison against all reference propositions
        # ------------------------------------------------------------------
        stu_subj = (prop.relation.get("subject_lemma") or prop.relation.get("subject") or "").strip().lower()
        stu_pred = (prop.relation.get("predicate_lemma") or prop.relation.get("predicate") or "").strip().lower()
        stu_obj = (prop.relation.get("object_lemma") or prop.relation.get("object") or "").strip().lower()

        # Collect student modifiers and argument lemmas
        stu_mods: Set[str] = set()
        for mod_list in [prop.relation.get("subject_modifiers", []), prop.relation.get("object_modifiers", []), prop.relation.get("adverbial_modifiers", [])]:
            for m in mod_list:
                if isinstance(m, str):
                    stu_mods.add(m.strip().lower())
        for arg in getattr(prop.linguistics, "arguments", []):
            if arg.lemma:
                stu_mods.add(arg.lemma.strip().lower())
            for m in arg.modifiers:
                stu_mods.add(m.strip().lower())

        for ref_idx, ref_rel in enumerate(context.reference_propositions):
            ref_subj = (ref_rel.get("subject_lemma") or ref_rel.get("subject") or "").strip().lower()
            ref_pred = (ref_rel.get("predicate_lemma") or ref_rel.get("predicate") or "").strip().lower()
            ref_obj = (ref_rel.get("object_lemma") or ref_rel.get("object") or "").strip().lower()

            subj_sim = self._compare_terms(stu_subj, ref_subj, "NOUN", "NOUN") if (stu_subj and ref_subj) else 0.0
            pred_sim = self._compare_terms(stu_pred, ref_pred, "VERB", "VERB") if (stu_pred and ref_pred) else 0.0
            obj_sim = self._compare_terms(stu_obj, ref_obj, "NOUN", "NOUN") if (stu_obj and ref_obj) else 0.0

            # Collect reference modifiers from relation and full reference answer text
            ref_mods: Set[str] = set()
            for mod_list in [ref_rel.get("subject_modifiers", []), ref_rel.get("object_modifiers", []), ref_rel.get("adverbial_modifiers", [])]:
                for m in mod_list:
                    if isinstance(m, str):
                        ref_mods.add(m.strip().lower())
            for p_arg in ref_rel.get("prepositional_arguments", []):
                if isinstance(p_arg, dict):
                    if p_arg.get("lemma"):
                        ref_mods.add(str(p_arg["lemma"]).strip().lower())
                elif isinstance(p_arg, str):
                    ref_mods.add(p_arg.strip().lower())

            # Also extract content qualifiers from reference answer text
            import re
            ref_words = re.findall(r"\b[a-zA-Z0-9_\-]+\b", context.reference_answer.lower())
            for rw in ref_words:
                if rw not in STOPWORDS and len(rw) > 1:
                    ref_mods.add(rw)

            # 2a. Slot Polarity Opposition Check
            if subj_sim >= 0.50 and pred_sim >= 0.50:
                if prop.is_negated:
                    reasons = [
                        "Polarity contradiction: student negates a predicate aligned with the reference proposition.",
                        f"Subject similarity: {subj_sim:.4f} ('{stu_subj}' <-> '{ref_subj}').",
                        f"Predicate similarity: {pred_sim:.4f} ('{stu_pred}' <-> '{ref_pred}').",
                    ]
                    return CompatibilityEvidence(
                        reference_support="CONTRADICTED",
                        contradiction_status="CONTRADICTION_DETECTED",
                        contradiction_type="POLARITY_CONTRADICTION",
                        conflicting_reference_index=ref_idx,
                        conflicting_reference_relation=ref_rel,
                        confidence=float(round(0.5 * (subj_sim + pred_sim), 4)),
                        reasons=reasons,
                        details={"subj_sim": subj_sim, "pred_sim": pred_sim},
                    )

            # 2b. Lexical Antonymy Check on Shared Subject
            if subj_sim >= 0.50:
                # Check predicate antonymy
                if _are_lexical_antonyms(stu_pred, ref_pred):
                    reasons = [
                        f"Antonym contradiction on predicate: '{stu_pred}' opposes reference predicate '{ref_pred}'.",
                        f"Subject '{stu_subj}' matches reference subject '{ref_subj}' (similarity: {subj_sim:.4f}).",
                    ]
                    return CompatibilityEvidence(
                        reference_support="CONTRADICTED",
                        contradiction_status="CONTRADICTION_DETECTED",
                        contradiction_type="ANTONYM_CONTRADICTION",
                        conflicting_reference_index=ref_idx,
                        conflicting_reference_relation=ref_rel,
                        confidence=0.85,
                        reasons=reasons,
                        details={"slot": "predicate", "student_term": stu_pred, "ref_term": ref_pred},
                    )
                # Check object antonymy on compatible predicate
                if pred_sim >= 0.50 and _are_lexical_antonyms(stu_obj, ref_obj):
                    reasons = [
                        f"Antonym contradiction on object: '{stu_obj}' opposes reference object '{ref_obj}'.",
                        f"Predicate '{stu_pred}' is aligned (similarity: {pred_sim:.4f}).",
                    ]
                    return CompatibilityEvidence(
                        reference_support="CONTRADICTED",
                        contradiction_status="CONTRADICTION_DETECTED",
                        contradiction_type="ANTONYM_CONTRADICTION",
                        conflicting_reference_index=ref_idx,
                        conflicting_reference_relation=ref_rel,
                        confidence=0.85,
                        reasons=reasons,
                        details={"slot": "object", "student_term": stu_obj, "ref_term": ref_obj},
                    )

            # 2c. Modifier / Qualification Opposition Check on Shared Subject
            if subj_sim >= 0.50:
                for s_term in (stu_mods | {stu_obj, stu_pred}):
                    for r_term in (ref_mods | {ref_obj, ref_pred}):
                        if _check_cluster_opposition(s_term, r_term):
                            # Cluster opposition detected (e.g. uniqueness vs duplication)
                            # If student asserts it in POSITIVE polarity -> Contradiction!
                            # If student asserts it in NEGATED polarity -> Compatible!
                            if not prop.is_negated:
                                reasons = [
                                    f"Property qualification conflict: student asserts '{s_term}' (positive polarity), which opposes reference qualification '{r_term}'.",
                                    f"Subject '{stu_subj}' addresses the same entity as reference subject '{ref_subj}'.",
                                ]
                                return CompatibilityEvidence(
                                    reference_support="CONTRADICTED",
                                    contradiction_status="CONTRADICTION_DETECTED",
                                    contradiction_type="MODIFIER_CONFLICT",
                                    conflicting_reference_index=ref_idx,
                                    conflicting_reference_relation=ref_rel,
                                    confidence=0.80,
                                    reasons=reasons,
                                    details={"student_modifier": s_term, "reference_modifier": r_term},
                                )

        # ------------------------------------------------------------------
        # Default: No contradiction detected
        # ------------------------------------------------------------------
        reasons = [
            "No contradiction detected with reference propositions.",
            "Proposition asserts supplementary information not directly covered by reference answer (NOT_SUPPORTED).",
        ]
        return CompatibilityEvidence(
            reference_support="NOT_SUPPORTED",
            contradiction_status="NO_CONTRADICTION",
            contradiction_type=None,
            conflicting_reference_index=None,
            conflicting_reference_relation=None,
            confidence=0.75,
            reasons=reasons,
            details={},
        )


# ---------------------------------------------------------------------------
# Additional Information Classifier (Stage 13 Coordinator)
# ---------------------------------------------------------------------------

class AdditionalInformationClassifier:
    """
    Stage 13 Classifier: Categorizes unmatched propositions into:
    - CORRECT_ADDITIONAL
    - IRRELEVANT
    - INCORRECT
    - UNCERTAIN

    Coordinates RelevanceAnalyzer and CompatibilityAnalyzer, enforces strict research
    invariants (score_effect = 0.0, Base score preserved), and produces complete,
    explainable DocumentClassificationResult objects.
    """

    def __init__(
        self,
        relevance_analyzer: Optional[RelevanceAnalyzer] = None,
        compatibility_analyzer: Optional[CompatibilityAnalyzer] = None,
        relevance_threshold: float = RelevanceAnalyzer.DEFAULT_RELEVANCE_THRESHOLD,
        contradiction_threshold: float = CompatibilityAnalyzer.DEFAULT_CONTRADICTION_THRESHOLD,
        uncertainty_margin: float = 0.05,
        builder: Optional[PropositionRepresentationBuilder] = None,
    ):
        """
        Initialize the AdditionalInformationClassifier.

        Parameters
        ----------
        relevance_analyzer : Optional[RelevanceAnalyzer], default=None
            Relevance analyzer instance. If None, initialized default.
        compatibility_analyzer : Optional[CompatibilityAnalyzer], default=None
            Compatibility analyzer instance. If None, initialized default.
        relevance_threshold : float, default=0.35
            Continuous threshold for question relevance.
        contradiction_threshold : float, default=0.50
            Continuous threshold for confirming contradictions.
        uncertainty_margin : float, default=0.05
            Margin above relevance threshold where classification defaults to UNCERTAIN.
        builder : Optional[PropositionRepresentationBuilder], default=None
            Stage 12 builder used when evaluating raw pipeline results.
        """
        self.relevance_analyzer = relevance_analyzer or RelevanceAnalyzer(
            relevance_threshold=relevance_threshold
        )
        self.compatibility_analyzer = compatibility_analyzer or CompatibilityAnalyzer(
            contradiction_threshold=contradiction_threshold
        )
        self.relevance_threshold = float(relevance_threshold)
        self.contradiction_threshold = float(contradiction_threshold)
        self.uncertainty_margin = float(uncertainty_margin)
        self.builder = builder or PropositionRepresentationBuilder()

    def classify_proposition(
        self,
        prop: PropositionRepresentation,
        context: PropositionContext,
    ) -> AdditionalInformationResult:
        """
        Classify a single unmatched student proposition.

        Parameters
        ----------
        prop : PropositionRepresentation
            The unmatched student proposition representation.
        context : PropositionContext
            Evaluation context (question and reference answers).

        Returns
        -------
        AdditionalInformationResult
            Interpretable classification outcome with full evidence.
        """
        relevance_ev = self.relevance_analyzer.analyze(prop, context)
        compat_ev = self.compatibility_analyzer.analyze(prop, context)

        # ------------------------------------------------------------------
        # Decision Step 1: Relevance Check
        # ------------------------------------------------------------------
        if not relevance_ev.is_relevant:
            classification = "IRRELEVANT"
            confidence = float(round(1.0 - relevance_ev.score, 4))
            reason = (
                f"Proposition is classified as IRRELEVANT: semantic relevance score ({relevance_ev.score:.4f}) "
                f"is below relevance threshold ({self.relevance_threshold:.2f})."
            )

        # ------------------------------------------------------------------
        # Decision Step 2: Contradiction Check
        # ------------------------------------------------------------------
        elif compat_ev.contradiction_status == "CONTRADICTION_DETECTED":
            classification = "INCORRECT"
            confidence = compat_ev.confidence
            reason = (
                f"Proposition is classified as INCORRECT: contradicts reference answer "
                f"({compat_ev.contradiction_type}): {compat_ev.reasons[0]}"
            )

        # ------------------------------------------------------------------
        # Decision Step 3: Consistency / Addition Check vs Uncertainty Fallback
        # ------------------------------------------------------------------
        else:
            # Check for borderline relevance / weak evidence
            if relevance_ev.score < (self.relevance_threshold + self.uncertainty_margin):
                classification = "UNCERTAIN"
                confidence = float(round(relevance_ev.score, 4))
                reason = (
                    f"Proposition is classified as UNCERTAIN: relevance score ({relevance_ev.score:.4f}) is borderline, "
                    "providing insufficient semantic evidence to confirm correctness or irrelevance."
                )
            else:
                classification = "CORRECT_ADDITIONAL"
                confidence = float(round(min(relevance_ev.score, compat_ev.confidence), 4))
                reason = (
                    "Proposition is classified as CORRECT_ADDITIONAL: semantically relevant to the topic, "
                    "consistent with reference answer propositions, and introduces valid supplementary information."
                )

        span_dict = prop.span.to_dict() if hasattr(prop.span, "to_dict") else None

        return AdditionalInformationResult(
            proposition_id=prop.proposition_id,
            proposition_index=prop.proposition_index,
            text=prop.text,
            classification=classification,
            confidence=confidence,
            relevance=relevance_ev,
            compatibility=compat_ev,
            decision_reason=reason,
            score_effect=0.0,  # STRICT INVARIANT: Always 0.0 in Stage 13
            span=span_dict,
            relation=dict(prop.relation) if prop.relation else None,
            polarity=prop.polarity,
        )

    def classify_document(
        self,
        document_or_pipeline_result: Union[DocumentPropositionRepresentation, BaseASAGPipelineResult],
    ) -> DocumentClassificationResult:
        """
        Classify all propositions for a document.

        Preserves matched propositions as MATCHED_BY_BASE_ASAG, evaluates all
        unmatched propositions, and maintains exact Base ASAG scores.

        Parameters
        ----------
        document_or_pipeline_result : Union[DocumentPropositionRepresentation, BaseASAGPipelineResult]
            Stage 12 DocumentPropositionRepresentation, or Stage 10 BaseASAGPipelineResult.

        Returns
        -------
        DocumentClassificationResult
            Complete classification container with summary metrics and JSON serialization.
        """
        if isinstance(document_or_pipeline_result, BaseASAGPipelineResult):
            doc_rep = self.builder.build(document_or_pipeline_result)
        elif isinstance(document_or_pipeline_result, DocumentPropositionRepresentation):
            doc_rep = document_or_pipeline_result
        else:
            raise TypeError(
                f"Expected DocumentPropositionRepresentation or BaseASAGPipelineResult, got {type(document_or_pipeline_result).__name__}."
            )

        unmatched_results: List[AdditionalInformationResult] = []
        matched_records: List[Dict[str, Any]] = []
        all_records: List[Dict[str, Any]] = []

        c_add_count = 0
        irrel_count = 0
        incorr_count = 0
        uncert_count = 0

        for prop in doc_rep.propositions:
            if prop.is_matched:
                matched_dict = {
                    "proposition_id": prop.proposition_id,
                    "proposition_index": prop.proposition_index,
                    "text": prop.text,
                    "classification": "MATCHED_BY_BASE_ASAG",
                    "match_status": "MATCHED",
                    "score_effect": prop.matching.score_effect,
                    "reference_proposition_index": prop.matching.reference_proposition_index,
                    "entailment_status": prop.matching.entailment_status,
                    "triple_score": prop.matching.triple_score,
                    "relation": dict(prop.relation) if prop.relation else None,
                    "span": prop.span.to_dict() if hasattr(prop.span, "to_dict") else None,
                }
                matched_records.append(matched_dict)
                all_records.append(matched_dict)
            else:
                unmatched_res = self.classify_proposition(prop, doc_rep.context)
                unmatched_results.append(unmatched_res)
                all_records.append(unmatched_res.to_dict())

                if unmatched_res.classification == "CORRECT_ADDITIONAL":
                    c_add_count += 1
                elif unmatched_res.classification == "IRRELEVANT":
                    irrel_count += 1
                elif unmatched_res.classification == "INCORRECT":
                    incorr_count += 1
                elif unmatched_res.classification == "UNCERTAIN":
                    uncert_count += 1

        summary = {
            "total_propositions": doc_rep.total_student_propositions,
            "matched_count": doc_rep.matched_count,
            "unmatched_count": doc_rep.unmatched_count,
            "correct_additional_count": c_add_count,
            "irrelevant_count": irrel_count,
            "incorrect_count": incorr_count,
            "uncertain_count": uncert_count,
            "base_asag_normalized_score": doc_rep.base_asag_normalized_score,
            "proposed_score_effect_total": 0.0,  # Enforced 0.0 in Stage 13
        }

        return DocumentClassificationResult(
            student_answer=doc_rep.student_answer,
            question=doc_rep.question,
            reference_answer=doc_rep.reference_answer,
            base_asag_normalized_score=doc_rep.base_asag_normalized_score,
            total_student_propositions=doc_rep.total_student_propositions,
            matched_count=doc_rep.matched_count,
            unmatched_count=doc_rep.unmatched_count,
            correct_additional_count=c_add_count,
            irrelevant_count=irrel_count,
            incorrect_count=incorr_count,
            uncertain_count=uncert_count,
            unmatched_classifications=unmatched_results,
            matched_propositions=matched_records,
            all_propositions=all_records,
            summary=summary,
        )
