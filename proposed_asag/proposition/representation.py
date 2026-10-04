"""
Proposition-Level Representation Module (Stage 12).

This module provides the Stage 12 component for the Proposed ASAG system (System 3).
It organizes, enriches, and structures both matched and unmatched student propositions
into a unified, interpretable proposition-level representation.

Research Purpose:
-----------------
Stage 11 identifies *which* student propositions were matched vs unmatched.
Stage 12 answers: "What does each proposition structurally and linguistically contain?"
It builds a rich, standardized proposition representation that serves as the clean
input boundary for:
- Stage 13: Additional-Information Classification (CORRECT_ADDITIONAL / IRRELEVANT / INCORRECT)
- Stage 14: Proposed Scoring Mechanism

Research Boundaries:
--------------------
- Stage 12 is NOT the classification stage. It must NOT determine whether an unmatched
  proposition is correct, irrelevant, or incorrect. All unmatched propositions maintain:
    classification = "NOT_EVALUATED_BY_BASE_ASAG"
    score_effect = 0.0
- Stage 12 does NOT alter or recalculate the Base ASAG score.
- Stage 12 does NOT introduce neural transformers, large language models, or embeddings.
- Stage 12 does NOT duplicate dependency parsing, triple matching, or entailment logic;
  it consumes and unifies the evidence already produced by Stages 3–11.

Architecture:
-------------
Stage 10: BaseASAGPipelineResult
      ↓
Stage 11: PropositionAlignmentResult
      ↓
Stage 12: DocumentPropositionRepresentation / PropositionRepresentation
      ↓
Stage 13: (future) Additional-Information Classifier
      ↓
Stage 14: (future) Proposed Scoring

Key Data Structures:
--------------------
- LinguisticArgument: Structured representation of an individual argument/modifier.
- LinguisticStructure: Detailed token, lemma, POS, dependency, and argument information.
- PropositionContext: Question and reference answer contextual information.
- MatchingProvenance: Complete matching, semantic similarity, and entailment provenance.
- PropositionRepresentation: Unified common representation for both matched and unmatched propositions.
- DocumentPropositionRepresentation: Top-level container for all propositions in an evaluated answer.
- PropositionRepresentationBuilder: Factory class that constructs representations from pipeline outputs.
"""

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from base_asag.dependency.parser import ParsedDocument, ParsedSentence, ParsedToken
from base_asag.dependency.triples import DependencyRelation, DocumentTriples
from base_asag.entailment.polarity import PolarityDetector, PolarityInfo
from base_asag.pipeline import BaseASAGPipelineResult
from proposed_asag.proposition.alignment import (
    MatchedPropositionEvidence,
    PropositionAlignmentExtractor,
    PropositionAlignmentResult,
    SpanInfo,
    UnmatchedStudentPropositionEvidence,
)


# ---------------------------------------------------------------------------
# Linguistic Data Structures
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class LinguisticArgument:
    """
    Structured representation of an argument, modifier, or prepositional phrase.

    Attributes
    ----------
    role : str
        Linguistic role: "subject", "predicate", "object", "subject_modifier",
        "object_modifier", "adverbial_modifier", or "prepositional_argument".
    text : str
        Surface form of the argument or phrase.
    lemma : str
        Lemmatized form.
    pos : str
        Coarse Universal POS tag (e.g. NOUN, VERB, ADP).
    tag : str
        Fine-grained Penn Treebank POS tag (e.g. NN, VBZ, IN).
    dep : str
        Syntactic dependency label (e.g. nsubj, dobj, prep, compound).
    token_index : int
        Sentence-relative token index of the primary token.
    head_token_index : int
        Sentence-relative token index of the governor.
    modifiers : List[str]
        Surface texts of any immediate modifiers.
    """
    role: str
    text: str
    lemma: str
    pos: str
    tag: str
    dep: str
    token_index: int
    head_token_index: int
    modifiers: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert LinguisticArgument to a JSON-serializable dictionary."""
        return {
            "role": self.role,
            "text": self.text,
            "lemma": self.lemma,
            "pos": self.pos,
            "tag": self.tag,
            "dep": self.dep,
            "token_index": self.token_index,
            "head_token_index": self.head_token_index,
            "modifiers": list(self.modifiers),
        }


@dataclass(frozen=True)
class LinguisticStructure:
    """
    Detailed token-level and dependency-level linguistic attributes of a proposition.

    Attributes
    ----------
    tokens : List[str]
        Surface forms of the key tokens in the proposition span.
    token_indices : List[int]
        Sentence-relative indices of the key tokens in sorted order.
    lemmas : List[str]
        Lemmatized forms of the key tokens.
    pos_tags : List[str]
        Coarse Universal POS tags of the key tokens.
    detailed_tags : List[str]
        Fine-grained Penn Treebank POS tags of the key tokens.
    dependency_labels : List[str]
        Grammatical dependency relation labels of the key tokens.
    heads : List[str]
        Surface texts of the syntactic heads for each token.
    head_indices : List[int]
        Sentence-relative indices of the syntactic heads.
    arguments : List[LinguisticArgument]
        Itemized list of linguistic arguments and modifiers (subject, predicate,
        object, prepositional phrases, adjectival/adverbial modifiers).
    """
    tokens: List[str]
    token_indices: List[int]
    lemmas: List[str]
    pos_tags: List[str]
    detailed_tags: List[str]
    dependency_labels: List[str]
    heads: List[str]
    head_indices: List[int]
    arguments: List[LinguisticArgument]

    def to_dict(self) -> Dict[str, Any]:
        """Convert LinguisticStructure to a JSON-serializable dictionary."""
        return {
            "tokens": list(self.tokens),
            "token_indices": list(self.token_indices),
            "lemmas": list(self.lemmas),
            "pos_tags": list(self.pos_tags),
            "detailed_tags": list(self.detailed_tags),
            "dependency_labels": list(self.dependency_labels),
            "heads": list(self.heads),
            "head_indices": list(self.head_indices),
            "arguments": [arg.to_dict() for arg in self.arguments],
        }


# ---------------------------------------------------------------------------
# Context Data Structure
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PropositionContext:
    """
    Question and reference answer contextual information.

    Preserves the context necessary for future Stage 13 evaluation
    (e.g. determining whether unmatched information is question-relevant).

    Attributes
    ----------
    question : str
        The prompt question text.
    reference_answer : str
        The instructor's model reference answer.
    total_reference_propositions : int
        Total number of reference propositions extracted.
    reference_propositions : List[Dict[str, Any]]
        Itemized list of all extracted reference relations.
    """
    question: str
    reference_answer: str
    total_reference_propositions: int
    reference_propositions: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        """Convert PropositionContext to a JSON-serializable dictionary."""
        return {
            "question": self.question,
            "reference_answer": self.reference_answer,
            "total_reference_propositions": self.total_reference_propositions,
            "reference_propositions": self.reference_propositions,
        }


# ---------------------------------------------------------------------------
# Matching & Provenance Data Structure
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class MatchingProvenance:
    """
    Complete alignment, semantic similarity, and entailment evidence.

    Unifies matching evidence from Stages 6, 7, 8, 9, and 11.

    Attributes
    ----------
    match_status : str
        "MATCHED" if aligned to a reference proposition, "UNMATCHED" otherwise.
    classification : str
        "MATCHED_BY_BASE_ASAG" for matched propositions;
        "NOT_EVALUATED_BY_BASE_ASAG" for unmatched propositions (Stage 12 invariant).
    score_effect : float
        Contribution to Base ASAG grade (1.0, 0.5, or 0.0 for matched; 0.0 for unmatched).
    alignment_threshold : float
        Alignment threshold used in Stage 7 (e.g. 0.50).
    reference_proposition_index : Optional[int]
        Index of matched reference proposition, or None if unmatched.
    reference_relation : Optional[Dict[str, Any]]
        Dependency relation of the matched reference proposition, or None.
    triple_score : Optional[float]
        Stage 7 composite alignment score if matched, or None.
    match_method : Optional[str]
        Stage 7 match method (e.g. "exact_triple", "lemma_triple"), or None.
    subject_similarity : Optional[float]
        Stage 7 slot similarity score for subject.
    predicate_similarity : Optional[float]
        Stage 7 slot similarity score for predicate.
    object_similarity : Optional[float]
        Stage 7 slot similarity score for object.
    slot_evidence : Optional[Dict[str, Any]]
        Stage 6 diagnostic lexical/semantic evidence per slot.
    entailment_status : Optional[str]
        Stage 8 classification: "ENTAILS", "CONTRADICTS", "UNCERTAIN", or None.
    entailment_confidence : Optional[float]
        Stage 8 confidence score in [0.0, 1.0].
    score_contribution : float
        Stage 9 proposition score contribution.
    diagnostic_reasons : List[str]
        Stage 8 human-readable explanations.
    best_candidate_reference_index : Optional[int]
        For unmatched relations: index of closest reference proposition considered.
    best_candidate_score : Optional[float]
        For unmatched relations: highest triple score against any reference relation.
    best_candidate_relation : Optional[Dict[str, Any]]
        For unmatched relations: relation dictionary of best rejected candidate.
    rejection_reason : Optional[str]
        For unmatched relations: explanation of why the proposition was not matched.
    """
    match_status: str
    classification: str
    score_effect: float
    alignment_threshold: float
    reference_proposition_index: Optional[int] = None
    reference_relation: Optional[Dict[str, Any]] = None
    triple_score: Optional[float] = None
    match_method: Optional[str] = None
    subject_similarity: Optional[float] = None
    predicate_similarity: Optional[float] = None
    object_similarity: Optional[float] = None
    slot_evidence: Optional[Dict[str, Any]] = None
    entailment_status: Optional[str] = None
    entailment_confidence: Optional[float] = None
    score_contribution: float = 0.0
    diagnostic_reasons: List[str] = field(default_factory=list)
    best_candidate_reference_index: Optional[int] = None
    best_candidate_score: Optional[float] = None
    best_candidate_relation: Optional[Dict[str, Any]] = None
    rejection_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert MatchingProvenance to a JSON-serializable dictionary."""
        return {
            "match_status": self.match_status,
            "classification": self.classification,
            "score_effect": self.score_effect,
            "alignment_threshold": self.alignment_threshold,
            "reference_proposition_index": self.reference_proposition_index,
            "reference_relation": self.reference_relation,
            "triple_score": self.triple_score,
            "match_method": self.match_method,
            "subject_similarity": self.subject_similarity,
            "predicate_similarity": self.predicate_similarity,
            "object_similarity": self.object_similarity,
            "slot_evidence": self.slot_evidence,
            "entailment_status": self.entailment_status,
            "entailment_confidence": self.entailment_confidence,
            "score_contribution": self.score_contribution,
            "diagnostic_reasons": list(self.diagnostic_reasons),
            "best_candidate_reference_index": self.best_candidate_reference_index,
            "best_candidate_score": self.best_candidate_score,
            "best_candidate_relation": self.best_candidate_relation,
            "rejection_reason": self.rejection_reason,
        }


# ---------------------------------------------------------------------------
# Core PropositionRepresentation
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PropositionRepresentation:
    """
    Unified proposition-level representation for both matched and unmatched propositions.

    Provides a complete, interpretable, structural record for an extracted proposition,
    integrating syntactic structure, text provenance, linguistic features, polarity,
    matching evidence, and evaluation context.

    Attributes
    ----------
    proposition_id : str
        Unique identifier (e.g. "stu_prop_0", "stu_prop_1").
    proposition_index : int
        Zero-based flat index within all extracted student propositions.
    sentence_index : int
        Zero-based sentence index within the student answer document.
    text : str
        The exact surface span text from the original student answer.
    span : SpanInfo
        Character-level provenance linking the proposition to student answer offsets.
    relation : Dict[str, Any]
        Canonical clause relation dictionary (subject, predicate, object, lemmas,
        modifiers, prepositional arguments).
    polarity : str
        "POSITIVE" or "NEGATED".
    is_negated : bool
        True if grammatical or lexical negation was detected.
    negation_tokens : List[str]
        Surface tokens triggering the negation assessment (e.g. ["not", "cannot"]).
    polarity_evidence : str
        Human-readable explanation of the polarity decision from Stage 8.
    linguistics : LinguisticStructure
        Detailed token-level lemmas, POS tags, dependency relations, and arguments.
    matching : MatchingProvenance
        Comprehensive matching, semantic similarity, and entailment provenance.
    context : PropositionContext
        Question and reference answer context.
    """
    proposition_id: str
    proposition_index: int
    sentence_index: int
    text: str
    span: SpanInfo
    relation: Dict[str, Any]
    polarity: str
    is_negated: bool
    negation_tokens: List[str]
    polarity_evidence: str
    linguistics: LinguisticStructure
    matching: MatchingProvenance
    context: PropositionContext

    @property
    def is_matched(self) -> bool:
        """Whether this proposition was aligned to a reference proposition."""
        return self.matching.match_status == "MATCHED"

    @property
    def is_unmatched(self) -> bool:
        """Whether this proposition remains unmatched by the Base ASAG."""
        return self.matching.match_status == "UNMATCHED"

    @property
    def classification(self) -> str:
        """The current evaluation classification of the proposition."""
        return self.matching.classification

    @property
    def score_effect(self) -> float:
        """The contribution of this proposition to the Base ASAG grade."""
        return self.matching.score_effect

    def to_dict(self) -> Dict[str, Any]:
        """Convert PropositionRepresentation to a JSON-serializable dictionary."""
        return {
            "proposition_id": self.proposition_id,
            "proposition_index": self.proposition_index,
            "sentence_index": self.sentence_index,
            "text": self.text,
            "span": self.span.to_dict(),
            "relation": self.relation,
            "polarity": self.polarity,
            "is_negated": self.is_negated,
            "negation_tokens": list(self.negation_tokens),
            "polarity_evidence": self.polarity_evidence,
            "linguistics": self.linguistics.to_dict(),
            "matching": self.matching.to_dict(),
            "context": self.context.to_dict(),
        }


# ---------------------------------------------------------------------------
# Document-Level Container
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DocumentPropositionRepresentation:
    """
    Complete document-level proposition representation container for an answer evaluation.

    Attributes
    ----------
    student_answer : str
        The raw input student answer.
    question : str
        The prompt question text.
    reference_answer : str
        The instructor's model reference answer.
    base_asag_normalized_score : float
        The core Base ASAG grade normalized in [0.0, 1.0], preserved unchanged.
    total_student_propositions : int
        Total number of student propositions extracted and represented.
    matched_count : int
        Number of student propositions aligned to reference propositions.
    unmatched_count : int
        Number of student propositions not aligned to the reference answer.
    propositions : List[PropositionRepresentation]
        Complete ordered list of all student proposition representations.
    matched_propositions : List[PropositionRepresentation]
        Subset of propositions that were matched.
    unmatched_propositions : List[PropositionRepresentation]
        Subset of propositions that were unmatched.
    unmatched_reference_propositions : List[Dict[str, Any]]
        Reference propositions omitted by the student answer.
    context : PropositionContext
        Shared question and reference context.
    """
    student_answer: str
    question: str
    reference_answer: str
    base_asag_normalized_score: float
    total_student_propositions: int
    matched_count: int
    unmatched_count: int
    propositions: List[PropositionRepresentation]
    matched_propositions: List[PropositionRepresentation]
    unmatched_propositions: List[PropositionRepresentation]
    unmatched_reference_propositions: List[Dict[str, Any]]
    context: PropositionContext

    def get_proposition(self, identifier: Union[str, int]) -> Optional[PropositionRepresentation]:
        """
        Retrieve a proposition by its proposition_id or proposition_index.

        Parameters
        ----------
        identifier : Union[str, int]
            The proposition_id string (e.g. "stu_prop_0") or integer index.

        Returns
        -------
        Optional[PropositionRepresentation]
            The requested proposition representation if found, or None.
        """
        if isinstance(identifier, int):
            for prop in self.propositions:
                if prop.proposition_index == identifier:
                    return prop
            return None
        elif isinstance(identifier, str):
            for prop in self.propositions:
                if prop.proposition_id == identifier:
                    return prop
            return None
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert DocumentPropositionRepresentation to a JSON-serializable dictionary."""
        return {
            "student_answer": self.student_answer,
            "question": self.question,
            "reference_answer": self.reference_answer,
            "base_asag_normalized_score": self.base_asag_normalized_score,
            "total_student_propositions": self.total_student_propositions,
            "matched_count": self.matched_count,
            "unmatched_count": self.unmatched_count,
            "propositions": [p.to_dict() for p in self.propositions],
            "matched_propositions": [p.to_dict() for p in self.matched_propositions],
            "unmatched_propositions": [p.to_dict() for p in self.unmatched_propositions],
            "unmatched_reference_propositions": self.unmatched_reference_propositions,
            "context": self.context.to_dict(),
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize the complete document representation to formatted JSON."""
        return json.dumps(self.to_dict(), indent=indent)


# ---------------------------------------------------------------------------
# Builder Class
# ---------------------------------------------------------------------------

class PropositionRepresentationBuilder:
    """
    Stage 12 Builder: Constructs structured proposition-level representations.

    Consumes BaseASAGPipelineResult (Stage 10) and PropositionAlignmentResult (Stage 11)
    to assemble rich, unified PropositionRepresentation instances.

    Design Principles:
    ------------------
    - Zero logic duplication: Reuses Stage 11 spans, Stage 7 matching, Stage 8 entailment/polarity,
      and Stage 4 parse trees.
    - Zero scoring side-effects: Preserves Base ASAG normalized score exactly.
    - Pure serialization: All generated objects convert to plain JSON-compatible dictionaries.
    """

    def __init__(
        self,
        polarity_detector: Optional[PolarityDetector] = None,
        alignment_extractor: Optional[PropositionAlignmentExtractor] = None,
    ):
        """
        Initialize the representation builder.

        Parameters
        ----------
        polarity_detector : Optional[PolarityDetector], default=None
            Polarity detector instance from Stage 8. If None, initialized default.
        alignment_extractor : Optional[PropositionAlignmentExtractor], default=None
            Proposition alignment extractor from Stage 11. If None, initialized default.
        """
        self.polarity_detector = polarity_detector or PolarityDetector()
        self.alignment_extractor = alignment_extractor or PropositionAlignmentExtractor()

    def build(
        self,
        pipeline_result: BaseASAGPipelineResult,
        alignment_result: Optional[PropositionAlignmentResult] = None,
    ) -> DocumentPropositionRepresentation:
        """
        Construct a DocumentPropositionRepresentation from pipeline and alignment results.

        Parameters
        ----------
        pipeline_result : BaseASAGPipelineResult
            The completed Base ASAG pipeline result from Stage 10.
        alignment_result : Optional[PropositionAlignmentResult], default=None
            Pre-computed Stage 11 alignment result. If None, extracted automatically.

        Returns
        -------
        DocumentPropositionRepresentation
            Complete structured representation of all student propositions.
        """
        if not isinstance(pipeline_result, BaseASAGPipelineResult):
            raise TypeError(
                f"Expected BaseASAGPipelineResult, got {type(pipeline_result).__name__}."
            )

        if alignment_result is None:
            alignment_result = self.alignment_extractor.extract(pipeline_result)
        elif not isinstance(alignment_result, PropositionAlignmentResult):
            raise TypeError(
                f"Expected PropositionAlignmentResult, got {type(alignment_result).__name__}."
            )

        # Build context
        context = self._build_context(pipeline_result)

        # Index matched evidence by student_proposition_index
        matched_map: Dict[int, MatchedPropositionEvidence] = {
            m.student_proposition_index: m for m in alignment_result.matched_propositions
        }

        # Index unmatched evidence by student_proposition_index
        unmatched_map: Dict[int, UnmatchedStudentPropositionEvidence] = {
            u.student_proposition_index: u for u in alignment_result.unmatched_student_propositions
        }

        # Flat ordered list of all student relations
        all_student_relations: List[DependencyRelation] = []
        for sent_triples in pipeline_result.student_triples.sentences:
            all_student_relations.extend(sent_triples.canonical_relations)

        # Map flat index -> sentence index
        student_rel_to_sent_index: Dict[int, int] = {}
        flat_idx = 0
        for sent_idx, sent_triples in enumerate(pipeline_result.student_triples.sentences):
            for _ in sent_triples.canonical_relations:
                student_rel_to_sent_index[flat_idx] = sent_idx
                flat_idx += 1

        propositions: List[PropositionRepresentation] = []

        for s_idx, stu_rel in enumerate(all_student_relations):
            sent_idx = student_rel_to_sent_index.get(s_idx, 0)
            sent_parsed = pipeline_result.student_parsed.sentences[sent_idx]

            # Detect polarity using Stage 8 PolarityDetector
            pol_info = self.polarity_detector.detect(stu_rel, sent_parsed)

            # Determine whether matched or unmatched
            if s_idx in matched_map:
                m_ev = matched_map[s_idx]
                span = m_ev.span
                matching = MatchingProvenance(
                    match_status="MATCHED",
                    classification="MATCHED_BY_BASE_ASAG",
                    score_effect=m_ev.score_contribution,
                    alignment_threshold=m_ev.alignment_threshold,
                    reference_proposition_index=m_ev.reference_proposition_index,
                    reference_relation=m_ev.reference_relation,
                    triple_score=m_ev.triple_score,
                    match_method=m_ev.match_method,
                    subject_similarity=m_ev.subject_similarity,
                    predicate_similarity=m_ev.predicate_similarity,
                    object_similarity=m_ev.object_similarity,
                    slot_evidence=m_ev.slot_evidence,
                    entailment_status=m_ev.entailment_status,
                    entailment_confidence=m_ev.entailment_confidence,
                    score_contribution=m_ev.score_contribution,
                    diagnostic_reasons=list(m_ev.diagnostic_reasons),
                )
            elif s_idx in unmatched_map:
                u_ev = unmatched_map[s_idx]
                span = u_ev.span
                matching = MatchingProvenance(
                    match_status="UNMATCHED",
                    classification="NOT_EVALUATED_BY_BASE_ASAG",
                    score_effect=0.0,
                    alignment_threshold=pipeline_result.matching_result.config.get("alignment_threshold", 0.50),
                    reference_proposition_index=None,
                    reference_relation=None,
                    triple_score=None,
                    match_method=None,
                    subject_similarity=None,
                    predicate_similarity=None,
                    object_similarity=None,
                    slot_evidence=None,
                    entailment_status=None,
                    entailment_confidence=None,
                    score_contribution=0.0,
                    diagnostic_reasons=[],
                    best_candidate_reference_index=u_ev.best_candidate_reference_index,
                    best_candidate_score=u_ev.best_candidate_score,
                    best_candidate_relation=u_ev.best_candidate_relation,
                    rejection_reason=u_ev.rejection_reason,
                )
            else:
                # Fallback if somehow not present in alignment maps
                span = SpanInfo(char_start=-1, char_end=-1, sentence_index=sent_idx, token_indices=(), span_text="")
                matching = MatchingProvenance(
                    match_status="UNMATCHED",
                    classification="NOT_EVALUATED_BY_BASE_ASAG",
                    score_effect=0.0,
                    alignment_threshold=0.50,
                )

            # Linguistic analysis: tokens, lemmas, POS, detailed tags, dependencies, and arguments
            linguistics = self._extract_linguistics(sent_parsed, stu_rel, span)

            # Structured relation dictionary enriched with modifiers and prepositional arguments
            relation_dict = self._enrich_relation_dict(stu_rel, sent_parsed, linguistics.arguments)

            prop = PropositionRepresentation(
                proposition_id=f"stu_prop_{s_idx}",
                proposition_index=s_idx,
                sentence_index=sent_idx,
                text=span.span_text,
                span=span,
                relation=relation_dict,
                polarity=pol_info.polarity,
                is_negated=pol_info.is_negated,
                negation_tokens=list(pol_info.negation_tokens),
                polarity_evidence=pol_info.evidence,
                linguistics=linguistics,
                matching=matching,
                context=context,
            )
            propositions.append(prop)

        matched_props = [p for p in propositions if p.is_matched]
        unmatched_props = [p for p in propositions if p.is_unmatched]

        return DocumentPropositionRepresentation(
            student_answer=pipeline_result.student_answer,
            question=pipeline_result.question,
            reference_answer=pipeline_result.reference_answer,
            base_asag_normalized_score=pipeline_result.normalized_score,
            total_student_propositions=len(propositions),
            matched_count=len(matched_props),
            unmatched_count=len(unmatched_props),
            propositions=propositions,
            matched_propositions=matched_props,
            unmatched_propositions=unmatched_props,
            unmatched_reference_propositions=alignment_result.unmatched_reference_propositions,
            context=context,
        )

    # -----------------------------------------------------------------------
    # Internal Helpers
    # -----------------------------------------------------------------------

    def _build_context(self, pipeline_result: BaseASAGPipelineResult) -> PropositionContext:
        """Construct the PropositionContext object from the pipeline result."""
        all_ref_rels: List[DependencyRelation] = []
        for sent_triples in pipeline_result.reference_triples.sentences:
            all_ref_rels.extend(sent_triples.canonical_relations)

        return PropositionContext(
            question=pipeline_result.question,
            reference_answer=pipeline_result.reference_answer,
            total_reference_propositions=len(all_ref_rels),
            reference_propositions=[r.to_dict() for r in all_ref_rels],
        )

    def _extract_linguistics(
        self,
        sent_parsed: ParsedSentence,
        relation: DependencyRelation,
        span: SpanInfo,
    ) -> LinguisticStructure:
        """Extract structured linguistic token and argument details for a proposition."""
        tokens_list = sent_parsed.tokens

        # Use span.token_indices if available and valid; otherwise fall back to relation indices
        indices: List[int] = []
        if span.token_indices:
            indices = [i for i in span.token_indices if 0 <= i < len(tokens_list)]
        if not indices:
            raw_indices = [relation.subject_index, relation.predicate_index, relation.object_index]
            indices = [i for i in raw_indices if i is not None and 0 <= i < len(tokens_list)]
        indices = sorted(set(indices))

        tokens: List[str] = []
        lemmas: List[str] = []
        pos_tags: List[str] = []
        detailed_tags: List[str] = []
        dependency_labels: List[str] = []
        heads: List[str] = []
        head_indices: List[int] = []

        for idx in indices:
            tok = tokens_list[idx]
            tokens.append(tok.text)
            lemmas.append(tok.lemma)
            pos_tags.append(tok.pos)
            detailed_tags.append(tok.tag)
            dependency_labels.append(tok.dep)
            heads.append(tok.head_text)
            head_indices.append(tok.head_index)

        # Extract itemized arguments (subject, predicate, object, prepositional phrases)
        arguments = self._extract_arguments(sent_parsed, relation)

        return LinguisticStructure(
            tokens=tokens,
            token_indices=indices,
            lemmas=lemmas,
            pos_tags=pos_tags,
            detailed_tags=detailed_tags,
            dependency_labels=dependency_labels,
            heads=heads,
            head_indices=head_indices,
            arguments=arguments,
        )

    def _extract_arguments(
        self,
        sent_parsed: ParsedSentence,
        relation: DependencyRelation,
    ) -> List[LinguisticArgument]:
        """Extract itemized linguistic arguments and attached prepositional phrases."""
        tokens_list = sent_parsed.tokens
        arguments: List[LinguisticArgument] = []

        # 1. Subject Argument
        if relation.subject_index is not None and 0 <= relation.subject_index < len(tokens_list):
            s_tok = tokens_list[relation.subject_index]
            s_mods = [
                tokens_list[c].text
                for c in s_tok.children_indices
                if 0 <= c < len(tokens_list) and tokens_list[c].dep in ("compound", "amod", "det")
            ]
            arguments.append(
                LinguisticArgument(
                    role="subject",
                    text=s_tok.text,
                    lemma=s_tok.lemma,
                    pos=s_tok.pos,
                    tag=s_tok.tag,
                    dep=s_tok.dep,
                    token_index=s_tok.index,
                    head_token_index=s_tok.head_index,
                    modifiers=s_mods,
                )
            )

        # 2. Predicate Argument
        if relation.predicate_index is not None and 0 <= relation.predicate_index < len(tokens_list):
            p_tok = tokens_list[relation.predicate_index]
            p_mods = [
                tokens_list[c].text
                for c in p_tok.children_indices
                if 0 <= c < len(tokens_list) and tokens_list[c].dep in ("advmod", "aux", "auxpass", "neg", "prt")
            ]
            arguments.append(
                LinguisticArgument(
                    role="predicate",
                    text=p_tok.text,
                    lemma=p_tok.lemma,
                    pos=p_tok.pos,
                    tag=p_tok.tag,
                    dep=p_tok.dep,
                    token_index=p_tok.index,
                    head_token_index=p_tok.head_index,
                    modifiers=p_mods,
                )
            )

        # 3. Object Argument (if present)
        if relation.object_index is not None and 0 <= relation.object_index < len(tokens_list):
            o_tok = tokens_list[relation.object_index]
            o_mods = [
                tokens_list[c].text
                for c in o_tok.children_indices
                if 0 <= c < len(tokens_list) and tokens_list[c].dep in ("compound", "amod", "det")
            ]
            arguments.append(
                LinguisticArgument(
                    role="object",
                    text=o_tok.text,
                    lemma=o_tok.lemma,
                    pos=o_tok.pos,
                    tag=o_tok.tag,
                    dep=o_tok.dep,
                    token_index=o_tok.index,
                    head_token_index=o_tok.head_index,
                    modifiers=o_mods,
                )
            )

        # 4. Prepositional Arguments attached to Predicate
        if relation.predicate_index is not None and 0 <= relation.predicate_index < len(tokens_list):
            pred_tok = tokens_list[relation.predicate_index]
            for c_idx in pred_tok.children_indices:
                if 0 <= c_idx < len(tokens_list):
                    c = tokens_list[c_idx]
                    if c.dep in ("prep", "agent", "dative"):
                        pobj = next(
                            (
                                tokens_list[gc]
                                for gc in c.children_indices
                                if 0 <= gc < len(tokens_list) and tokens_list[gc].dep in ("pobj", "pcomp")
                            ),
                            None,
                        )
                        if pobj:
                            pobj_mods = [
                                tokens_list[gc].text
                                for gc in pobj.children_indices
                                if 0 <= gc < len(tokens_list) and tokens_list[gc].dep in ("compound", "amod")
                            ]
                            mod_str = " ".join(pobj_mods) + " " if pobj_mods else ""
                            phrase_text = f"{c.text} {mod_str}{pobj.text}".strip()
                            arguments.append(
                                LinguisticArgument(
                                    role="prepositional_argument",
                                    text=phrase_text,
                                    lemma=pobj.lemma,
                                    pos=pobj.pos,
                                    tag=pobj.tag,
                                    dep=c.dep,
                                    token_index=pobj.index,
                                    head_token_index=pred_tok.index,
                                    modifiers=pobj_mods,
                                )
                            )

        # 5. Prepositional Arguments attached to Object
        if relation.object_index is not None and 0 <= relation.object_index < len(tokens_list):
            obj_tok = tokens_list[relation.object_index]
            for c_idx in obj_tok.children_indices:
                if 0 <= c_idx < len(tokens_list):
                    c = tokens_list[c_idx]
                    if c.dep in ("prep",):
                        pobj = next(
                            (
                                tokens_list[gc]
                                for gc in c.children_indices
                                if 0 <= gc < len(tokens_list) and tokens_list[gc].dep in ("pobj", "pcomp")
                            ),
                            None,
                        )
                        if pobj:
                            pobj_mods = [
                                tokens_list[gc].text
                                for gc in pobj.children_indices
                                if 0 <= gc < len(tokens_list) and tokens_list[gc].dep in ("compound", "amod")
                            ]
                            mod_str = " ".join(pobj_mods) + " " if pobj_mods else ""
                            phrase_text = f"{c.text} {mod_str}{pobj.text}".strip()
                            arguments.append(
                                LinguisticArgument(
                                    role="prepositional_argument",
                                    text=phrase_text,
                                    lemma=pobj.lemma,
                                    pos=pobj.pos,
                                    tag=pobj.tag,
                                    dep=c.dep,
                                    token_index=pobj.index,
                                    head_token_index=obj_tok.index,
                                    modifiers=pobj_mods,
                                )
                            )

        return arguments

    def _enrich_relation_dict(
        self,
        relation: DependencyRelation,
        sent_parsed: ParsedSentence,
        arguments: List[LinguisticArgument],
    ) -> Dict[str, Any]:
        """Construct the enriched relation dictionary."""
        rel_dict = relation.to_dict()

        # Subject modifiers
        s_arg = next((a for a in arguments if a.role == "subject"), None)
        rel_dict["subject_modifiers"] = list(s_arg.modifiers) if s_arg else []

        # Object modifiers
        o_arg = next((a for a in arguments if a.role == "object"), None)
        rel_dict["object_modifiers"] = list(o_arg.modifiers) if o_arg else []

        # Adverbial modifiers
        p_arg = next((a for a in arguments if a.role == "predicate"), None)
        rel_dict["adverbial_modifiers"] = list(p_arg.modifiers) if p_arg else []

        # Prepositional arguments
        prep_args = [a.to_dict() for a in arguments if a.role == "prepositional_argument"]
        rel_dict["prepositional_arguments"] = prep_args

        return rel_dict
