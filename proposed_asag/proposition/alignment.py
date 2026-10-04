"""
Proposition Alignment Extractor (Stage 11).

This module provides the Stage 11 component for the Proposed ASAG system.
It extracts full matched and unmatched proposition provenance from an existing
BaseASAGPipelineResult without re-running any matching, entailment, or scoring.

Research Purpose:
-----------------
Stage 11 is the first step in the proposed extension pipeline. It identifies:
1. Which student propositions were matched to reference propositions (and how).
2. Which student propositions were NOT matched (unmatched student information).

Stage 11 does NOT:
- Classify unmatched student information as correct, irrelevant, or incorrect.
  (That is the responsibility of Stage 13.)
- Modify or re-compute the Base ASAG score.
- Add bonus or penalty for additional student information.
- Re-run any Stage 3–9 components.

The unmatched_student_propositions in the output are labeled with:
  classification = "NOT_EVALUATED_BY_BASE_ASAG"

This preserves research integrity: Stage 11 documents that unmatched information
exists but makes no judgment about its quality.

Key Data Structures:
--------------------
- SpanInfo: Character-level provenance linking a proposition to the original answer text.
- MatchedPropositionEvidence: Full diagnostic record for a student proposition that was
  aligned to a reference proposition.
- UnmatchedStudentPropositionEvidence: Record for a student proposition that was not
  aligned to any reference proposition.
- PropositionAlignmentResult: Top-level container exposing the complete alignment.

Span Computation Note:
----------------------
ParsedToken.char_offset is the character offset within the normalized sentence text
(not within the full multi-sentence student answer). For single-sentence answers,
this offset is also valid relative to the sentence's original text if normalization
is minimal (e.g. only lowercasing or whitespace normalization). For multi-sentence
answers, each sentence's offset must be located within the full answer by string search.

OUR IMPLEMENTATION DECISION: We locate each sentence in the original student answer
using `str.find(sentence_original_text)`. If the sentence cannot be found (e.g. because
preprocessing substantially altered it), we fall back to char_start=-1, char_end=-1.

Assumptions:
- student_triples.sentences[i] corresponds to student_parsed.sentences[i].
- MatchedRelation.student_index is the flat index into the complete list of all
  student canonical relations across all sentences.
- CandidateAlignment.student_index uses the same flat indexing.
"""

import json
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from base_asag.dependency.parser import ParsedDocument
from base_asag.dependency.triples import DependencyRelation, DocumentTriples


# ---------------------------------------------------------------------------
# SpanInfo
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SpanInfo:
    """
    Character-level span linking a dependency relation to the original student answer.

    Attributes
    ----------
    char_start : int
        Character start index (inclusive) in the original student answer string.
        -1 if the span could not be computed.
    char_end : int
        Character end index (exclusive) in the original student answer string.
        -1 if the span could not be computed.
    sentence_index : int
        Zero-based index of the sentence within the student answer.
    token_indices : Tuple[int, ...]
        Sentence-relative token indices of the key proposition tokens
        (subject, predicate, object) in sorted order.
    span_text : str
        The substring student_answer[char_start:char_end] if char_start >= 0
        and char_end > char_start. Otherwise the sentence original text is used.

    Notes
    -----
    - char_start and char_end are relative to the ORIGINAL student answer string
      (pipeline_result.student_answer), not the normalized text.
    - char_offset on ParsedToken is relative to the NORMALIZED sentence text.
      This module maps those offsets back to the original via string search.
    """
    char_start: int
    char_end: int
    sentence_index: int
    token_indices: Tuple[int, ...]
    span_text: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert SpanInfo to a JSON-serializable dictionary."""
        return {
            "char_start": self.char_start,
            "char_end": self.char_end,
            "sentence_index": self.sentence_index,
            "token_indices": list(self.token_indices),
            "span_text": self.span_text,
        }


# ---------------------------------------------------------------------------
# MatchedPropositionEvidence
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class MatchedPropositionEvidence:
    """
    Full diagnostic evidence for a student proposition matched to a reference proposition.

    Each instance corresponds to one MatchedRelation from Stage 7 and its associated
    entailment result from Stage 8 and score contribution from Stage 9.

    Attributes
    ----------
    student_proposition_index : int
        Flat index of the student relation in the ordered list of all student
        canonical relations across all sentences.
    reference_proposition_index : int
        Flat index of the reference relation (reference_index from Stage 7 MatchedRelation).
    student_relation : dict
        DependencyRelation.to_dict() for the student's matched relation.
    reference_relation : dict
        DependencyRelation.to_dict() for the reference relation.
    span : SpanInfo
        Character-level provenance linking this proposition to the student answer.
    subject_similarity : float
        Semantic similarity score for the subject slot from Stage 7.
    predicate_similarity : float
        Semantic similarity score for the predicate slot from Stage 7.
    object_similarity : Optional[float]
        Semantic similarity score for the object slot from Stage 7, or None if intransitive.
    triple_score : float
        Weighted composite alignment score from Stage 7.
    match_method : str
        Descriptive match type from Stage 7 (e.g. "exact_triple", "lemma_triple").
    alignment_threshold : float
        Alignment threshold used in Stage 7.
    entailment_status : str
        Stage 8 entailment classification: "ENTAILS", "CONTRADICTS", "UNCERTAIN",
        or "NO_ENTAILMENT_RESULT" if Stage 8 did not produce a result for this pair.
    entailment_confidence : float
        Stage 8 confidence score in [0.0, 1.0].
    score_contribution : float
        Stage 9 contribution value (1.0 = ENTAILED, 0.5 = UNCERTAIN, 0.0 otherwise).
    slot_evidence : dict
        Stage 6 semantic evidence for each slot (subject, predicate, object).
    diagnostic_reasons : List[str]
        Human-readable explanations from Stage 8.
    polarity_reference : str
        "POSITIVE" or "NEGATED" for the reference proposition.
    polarity_student : str
        "POSITIVE" or "NEGATED" for the student proposition.
    """
    student_proposition_index: int
    reference_proposition_index: int
    student_relation: dict
    reference_relation: dict
    span: SpanInfo
    subject_similarity: float
    predicate_similarity: float
    object_similarity: Optional[float]
    triple_score: float
    match_method: str
    alignment_threshold: float
    entailment_status: str
    entailment_confidence: float
    score_contribution: float
    slot_evidence: dict
    diagnostic_reasons: List[str]
    polarity_reference: str
    polarity_student: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert MatchedPropositionEvidence to a JSON-serializable dictionary."""
        return {
            "student_proposition_index": self.student_proposition_index,
            "reference_proposition_index": self.reference_proposition_index,
            "student_relation": self.student_relation,
            "reference_relation": self.reference_relation,
            "span": self.span.to_dict(),
            "subject_similarity": self.subject_similarity,
            "predicate_similarity": self.predicate_similarity,
            "object_similarity": self.object_similarity,
            "triple_score": self.triple_score,
            "match_method": self.match_method,
            "alignment_threshold": self.alignment_threshold,
            "entailment_status": self.entailment_status,
            "entailment_confidence": self.entailment_confidence,
            "score_contribution": self.score_contribution,
            "slot_evidence": self.slot_evidence,
            "diagnostic_reasons": list(self.diagnostic_reasons),
            "polarity_reference": self.polarity_reference,
            "polarity_student": self.polarity_student,
        }


# ---------------------------------------------------------------------------
# UnmatchedStudentPropositionEvidence
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class UnmatchedStudentPropositionEvidence:
    """
    Evidence record for a student proposition that was NOT matched to any reference proposition.

    Stage 11 exposes these unmatched propositions explicitly and labels them with
    classification = "NOT_EVALUATED_BY_BASE_ASAG".

    Stage 11 does NOT determine whether this unmatched information is:
    - Correct additional information
    - Irrelevant information
    - Incorrect or misconception-related information

    That evaluation is reserved for Stage 13 (Additional-Information Classification).

    Attributes
    ----------
    student_proposition_index : int
        Flat index of the student relation in the ordered list of all student
        canonical relations across all sentences.
    student_relation : dict
        DependencyRelation.to_dict() for the unmatched student relation.
    span : SpanInfo
        Character-level provenance linking this proposition to the student answer.
    match_status : str
        Always "UNMATCHED".
    classification : str
        Always "NOT_EVALUATED_BY_BASE_ASAG" in Stage 11.
        This will be updated by Stage 13 to CORRECT_ADDITIONAL, IRRELEVANT, or
        INCORRECT_ADDITIONAL.
    score_effect : float
        Always 0.0. Unmatched student information contributes zero to the Base ASAG score.
    best_candidate_reference_index : Optional[int]
        Index of the closest reference relation that was considered but not selected,
        or None if no candidates existed.
    best_candidate_score : Optional[float]
        Triple score of the best rejected candidate, or None.
    best_candidate_relation : Optional[dict]
        DependencyRelation.to_dict() of the best rejected reference candidate, or None.
    rejection_reason : str
        Human-readable explanation of why this student relation was not matched.
    """
    student_proposition_index: int
    student_relation: dict
    span: SpanInfo
    match_status: str
    classification: str
    score_effect: float
    best_candidate_reference_index: Optional[int]
    best_candidate_score: Optional[float]
    best_candidate_relation: Optional[dict]
    rejection_reason: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert UnmatchedStudentPropositionEvidence to a JSON-serializable dictionary."""
        return {
            "student_proposition_index": self.student_proposition_index,
            "student_relation": self.student_relation,
            "span": self.span.to_dict(),
            "match_status": self.match_status,
            "classification": self.classification,
            "score_effect": self.score_effect,
            "best_candidate_reference_index": self.best_candidate_reference_index,
            "best_candidate_score": self.best_candidate_score,
            "best_candidate_relation": self.best_candidate_relation,
            "rejection_reason": self.rejection_reason,
        }


# ---------------------------------------------------------------------------
# PropositionAlignmentResult
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PropositionAlignmentResult:
    """
    Complete proposition alignment result for a single student answer evaluation.

    This is the primary output of Stage 11. It organizes all matched and unmatched
    student propositions with full provenance and diagnostic evidence.

    Research Relevance:
    -------------------
    - matched_propositions: Student information that was evaluated by the Base ASAG.
    - unmatched_student_propositions: Student information that was NOT evaluated by
      the Base ASAG. These are candidates for Stage 13 classification.
    - unmatched_reference_propositions: Reference propositions not covered by the
      student answer (counted as MISSING in Stage 9).
    - base_asag_normalized_score: The Base ASAG score is preserved unchanged.

    Attributes
    ----------
    original_student_answer : str
        The original (pre-normalization) student answer text.
    total_student_propositions : int
        Total number of dependency relations extracted from the student answer.
    total_reference_propositions : int
        Total number of dependency relations extracted from the reference answer.
    matched_count : int
        Number of student propositions successfully aligned to reference propositions.
    unmatched_student_count : int
        Number of student propositions not aligned to any reference proposition.
    unmatched_reference_count : int
        Number of reference propositions not covered by the student answer.
    matched_propositions : List[MatchedPropositionEvidence]
        Full evidence records for matched propositions.
    unmatched_student_propositions : List[UnmatchedStudentPropositionEvidence]
        Evidence records for unmatched student propositions.
    unmatched_reference_propositions : List[dict]
        DependencyRelation.to_dict() for each unmatched reference proposition.
    alignment_summary : dict
        High-level summary statistics for quick inspection.
    base_asag_normalized_score : float
        The Base ASAG normalized score, preserved unchanged from Stage 9.
    """
    original_student_answer: str
    total_student_propositions: int
    total_reference_propositions: int
    matched_count: int
    unmatched_student_count: int
    unmatched_reference_count: int
    matched_propositions: List[MatchedPropositionEvidence]
    unmatched_student_propositions: List[UnmatchedStudentPropositionEvidence]
    unmatched_reference_propositions: List[dict]
    alignment_summary: dict
    base_asag_normalized_score: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert PropositionAlignmentResult to a JSON-serializable dictionary."""
        return {
            "original_student_answer": self.original_student_answer,
            "total_student_propositions": self.total_student_propositions,
            "total_reference_propositions": self.total_reference_propositions,
            "matched_count": self.matched_count,
            "unmatched_student_count": self.unmatched_student_count,
            "unmatched_reference_count": self.unmatched_reference_count,
            "matched_propositions": [m.to_dict() for m in self.matched_propositions],
            "unmatched_student_propositions": [u.to_dict() for u in self.unmatched_student_propositions],
            "unmatched_reference_propositions": self.unmatched_reference_propositions,
            "alignment_summary": self.alignment_summary,
            "base_asag_normalized_score": self.base_asag_normalized_score,
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize the complete alignment result to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


# ---------------------------------------------------------------------------
# PropositionAlignmentExtractor
# ---------------------------------------------------------------------------

class PropositionAlignmentExtractor:
    """
    Stage 11: Extracts full matched/unmatched proposition provenance from BaseASAGPipelineResult.

    This class reads the already-computed pipeline result and reorganizes the
    Stage 7–9 evidence into a structured PropositionAlignmentResult.

    It does NOT:
    - Re-run any NLP pipeline stage.
    - Modify or recalculate the Base ASAG score.
    - Classify unmatched student information.
    - Add any bonus or penalty for additional student information.

    Usage
    -----
    >>> pipeline = BaseASAGPipeline()
    >>> result = pipeline.grade(question, reference_answer, student_answer)
    >>> extractor = PropositionAlignmentExtractor()
    >>> alignment = extractor.extract(result)
    >>> print(alignment.to_json())
    """

    def extract(self, pipeline_result: Any) -> PropositionAlignmentResult:
        """
        Build a PropositionAlignmentResult from an existing BaseASAGPipelineResult.

        This method does NOT re-run matching, entailment, or scoring. It reads
        the pipeline_result fields and reorganizes the evidence.

        Parameters
        ----------
        pipeline_result : BaseASAGPipelineResult
            The completed Base ASAG pipeline result from Stage 10.

        Returns
        -------
        PropositionAlignmentResult
            Complete alignment record with full matched/unmatched provenance.
        """
        student_answer_original = pipeline_result.student_answer
        student_parsed: ParsedDocument = pipeline_result.student_parsed
        student_triples: DocumentTriples = pipeline_result.student_triples

        # Build flat list of all student relations in sentence order
        # This is the global indexing used throughout Stage 7 (candidate_alignments
        # and matched_relations use student_index into this flat list).
        all_student_relations: List[DependencyRelation] = []
        for sent_triples in student_triples.sentences:
            all_student_relations.extend(sent_triples.canonical_relations)

        # Build flat list of all reference relations
        all_reference_relations: List[DependencyRelation] = []
        for sent_triples in pipeline_result.reference_triples.sentences:
            all_reference_relations.extend(sent_triples.canonical_relations)

        # Build sentence-index map for student relations
        # Maps flat student relation index -> sentence index
        student_rel_to_sent_index: Dict[int, int] = {}
        flat_idx = 0
        for sent_idx, sent_triples in enumerate(student_triples.sentences):
            for _ in sent_triples.canonical_relations:
                student_rel_to_sent_index[flat_idx] = sent_idx
                flat_idx += 1

        # Build score contributions from Stage 9 proposition_results
        # Key: reference relation tuple (subject, predicate, object) -> contribution
        score_contributions: Dict[Tuple[str, str, Optional[str]], float] = {}
        for prop_record in pipeline_result.scoring_result.proposition_results:
            key = prop_record.reference_relation.to_tuple()
            score_contributions[key] = prop_record.contribution

        # Build entailment results lookup by reference relation tuple
        entailment_by_ref: Dict[Tuple[str, str, Optional[str]], Any] = {}
        for entail_res in pipeline_result.entailment_results:
            key = entail_res.reference_relation.to_tuple()
            entailment_by_ref[key] = entail_res

        # Build candidate alignments lookup: student_index -> best candidate alignment
        # Used to report diagnostic rejection reasons for unmatched student relations
        best_candidate_by_student: Dict[int, Any] = {}
        for cand in pipeline_result.matching_result.candidate_alignments:
            s_idx = cand.student_index
            if (
                s_idx not in best_candidate_by_student
                or cand.triple_score > best_candidate_by_student[s_idx].triple_score
            ):
                best_candidate_by_student[s_idx] = cand

        # Identify which student_indices were matched
        matched_student_indices: set = {
            mr.student_index for mr in pipeline_result.matched_relations
        }

        # ----------------------------------------------------------------
        # Build MatchedPropositionEvidence records
        # ----------------------------------------------------------------
        matched_propositions: List[MatchedPropositionEvidence] = []

        for matched_rel in pipeline_result.matched_relations:
            student_prop_idx = matched_rel.student_index
            reference_prop_idx = matched_rel.reference_index

            # Sentence index for this student relation
            sent_idx = student_rel_to_sent_index.get(student_prop_idx, 0)

            # Compute character span
            span = self._compute_span(
                student_answer_original=student_answer_original,
                student_parsed=student_parsed,
                relation=matched_rel.student_relation,
                sentence_index=sent_idx,
            )

            # Get entailment result for this pair
            ref_key = matched_rel.reference_relation.to_tuple()
            entail_res = entailment_by_ref.get(ref_key)

            if entail_res is not None:
                entailment_status = entail_res.relation  # ENTAILS / CONTRADICTS / UNCERTAIN
                entailment_confidence = entail_res.confidence
                diagnostic_reasons = list(entail_res.reasons)
                polarity_ref = entail_res.reference_polarity
                polarity_stu = entail_res.student_polarity
            else:
                entailment_status = "NO_ENTAILMENT_RESULT"
                entailment_confidence = 0.0
                diagnostic_reasons = []
                polarity_ref = "UNKNOWN"
                polarity_stu = "UNKNOWN"

            # Score contribution from Stage 9
            score_contrib = score_contributions.get(ref_key, 0.0)

            # Slot evidence serialization
            slot_ev_dict: Dict[str, Any] = {}
            for slot_name, sem_rel in matched_rel.slot_evidence.items():
                slot_ev_dict[slot_name] = sem_rel.to_dict() if hasattr(sem_rel, "to_dict") else str(sem_rel)

            evidence = MatchedPropositionEvidence(
                student_proposition_index=student_prop_idx,
                reference_proposition_index=reference_prop_idx,
                student_relation=matched_rel.student_relation.to_dict(),
                reference_relation=matched_rel.reference_relation.to_dict(),
                span=span,
                subject_similarity=matched_rel.subject_similarity,
                predicate_similarity=matched_rel.predicate_similarity,
                object_similarity=matched_rel.object_similarity,
                triple_score=matched_rel.triple_score,
                match_method=matched_rel.match_method,
                alignment_threshold=matched_rel.threshold,
                entailment_status=entailment_status,
                entailment_confidence=entailment_confidence,
                score_contribution=score_contrib,
                slot_evidence=slot_ev_dict,
                diagnostic_reasons=diagnostic_reasons,
                polarity_reference=polarity_ref,
                polarity_student=polarity_stu,
            )
            matched_propositions.append(evidence)

        # ----------------------------------------------------------------
        # Build UnmatchedStudentPropositionEvidence records
        # ----------------------------------------------------------------
        unmatched_student_propositions: List[UnmatchedStudentPropositionEvidence] = []

        for s_idx, stu_rel in enumerate(all_student_relations):
            if s_idx in matched_student_indices:
                continue  # This student relation was matched; skip

            # Sentence index for this unmatched student relation
            sent_idx = student_rel_to_sent_index.get(s_idx, 0)

            # Compute character span
            span = self._compute_span(
                student_answer_original=student_answer_original,
                student_parsed=student_parsed,
                relation=stu_rel,
                sentence_index=sent_idx,
            )

            # Best candidate alignment for this student relation
            best_cand = best_candidate_by_student.get(s_idx)
            threshold = pipeline_result.matching_result.config.get("alignment_threshold", 0.5)
            if best_cand is not None:
                best_ref_idx = best_cand.reference_index
                best_ref_score = best_cand.triple_score
                best_ref_rel = best_cand.reference_relation.to_dict()
                if best_cand.is_eligible:
                    rejection_reason = (
                        f"Candidate alignment with reference proposition {best_ref_idx} met the alignment "
                        f"threshold ({best_ref_score:.4f} >= {threshold:.2f}), but the reference proposition "
                        f"was assigned to a higher-scoring student proposition under one-to-one matching constraints."
                    )
                else:
                    rejection_reason = (
                        f"Best candidate alignment score ({best_ref_score:.4f}) is below the "
                        f"alignment threshold ({threshold:.2f}). Student relation was not matched."
                    )
            else:
                best_ref_idx = None
                best_ref_score = None
                best_ref_rel = None
                if not all_reference_relations:
                    rejection_reason = "No reference relations were extracted. Nothing to match against."
                else:
                    rejection_reason = (
                        "No candidate alignment was generated for this student relation. "
                        "This may indicate a structural mismatch with all reference relations."
                    )

            evidence = UnmatchedStudentPropositionEvidence(
                student_proposition_index=s_idx,
                student_relation=stu_rel.to_dict(),
                span=span,
                match_status="UNMATCHED",
                classification="NOT_EVALUATED_BY_BASE_ASAG",
                score_effect=0.0,
                best_candidate_reference_index=best_ref_idx,
                best_candidate_score=best_ref_score,
                best_candidate_relation=best_ref_rel,
                rejection_reason=rejection_reason,
            )
            unmatched_student_propositions.append(evidence)

        # ----------------------------------------------------------------
        # Unmatched reference propositions (for completeness)
        # ----------------------------------------------------------------
        unmatched_ref_dicts = [r.to_dict() for r in pipeline_result.unmatched_reference_relations]

        # ----------------------------------------------------------------
        # Build alignment summary
        # ----------------------------------------------------------------
        total_stu = len(all_student_relations)
        total_ref = len(all_reference_relations)
        matched_cnt = len(matched_propositions)
        unmatched_stu_cnt = len(unmatched_student_propositions)
        unmatched_ref_cnt = len(unmatched_ref_dicts)

        # Count entailment outcomes
        entailed_cnt = sum(1 for m in matched_propositions if m.entailment_status == "ENTAILS")
        contradicted_cnt = sum(1 for m in matched_propositions if m.entailment_status == "CONTRADICTS")
        uncertain_cnt = sum(1 for m in matched_propositions if m.entailment_status == "UNCERTAIN")

        alignment_summary = {
            "total_student_propositions": total_stu,
            "total_reference_propositions": total_ref,
            "matched_count": matched_cnt,
            "unmatched_student_count": unmatched_stu_cnt,
            "unmatched_reference_count": unmatched_ref_cnt,
            "entailed_count": entailed_cnt,
            "contradicted_count": contradicted_cnt,
            "uncertain_count": uncertain_cnt,
            "base_asag_normalized_score": pipeline_result.normalized_score,
            "student_coverage_ratio": round(matched_cnt / total_stu, 4) if total_stu > 0 else 0.0,
            "reference_coverage_ratio": round(
                (total_ref - unmatched_ref_cnt) / total_ref, 4
            ) if total_ref > 0 else 0.0,
            "stage": "STAGE_11_ALIGNMENT",
            "note": (
                "Unmatched student propositions are labeled NOT_EVALUATED_BY_BASE_ASAG. "
                "Stage 13 will classify them as CORRECT_ADDITIONAL, IRRELEVANT, or INCORRECT_ADDITIONAL."
            ),
        }

        return PropositionAlignmentResult(
            original_student_answer=student_answer_original,
            total_student_propositions=total_stu,
            total_reference_propositions=total_ref,
            matched_count=matched_cnt,
            unmatched_student_count=unmatched_stu_cnt,
            unmatched_reference_count=unmatched_ref_cnt,
            matched_propositions=matched_propositions,
            unmatched_student_propositions=unmatched_student_propositions,
            unmatched_reference_propositions=unmatched_ref_dicts,
            alignment_summary=alignment_summary,
            base_asag_normalized_score=pipeline_result.normalized_score,
        )

    # -----------------------------------------------------------------------
    # Private helpers
    # -----------------------------------------------------------------------

    def _compute_span(
        self,
        student_answer_original: str,
        student_parsed: ParsedDocument,
        relation: DependencyRelation,
        sentence_index: int,
    ) -> SpanInfo:
        """
        Compute character-level span for a dependency relation within the original student answer.

        Parameters
        ----------
        student_answer_original : str
            The original (pre-normalization) student answer string.
        student_parsed : ParsedDocument
            The Stage 4 parsed document for the student answer.
        relation : DependencyRelation
            The dependency relation whose span we are computing.
        sentence_index : int
            Zero-based sentence index within student_parsed.sentences.

        Returns
        -------
        SpanInfo
            Character-level provenance. char_start=-1, char_end=-1 if computation fails.

        Implementation Notes
        --------------------
        ParsedToken.char_offset is relative to the NORMALIZED sentence text.
        We use string search to locate the sentence's original text within the
        full student answer, then apply the token offsets.

        If the normalized text differs significantly from the original sentence text,
        the character span may be approximate. In practice, normalization in this
        system is minimal (lowercasing and whitespace normalization), so the offsets
        are usually valid or very close.
        """
        try:
            # Validate sentence index
            if sentence_index < 0 or sentence_index >= len(student_parsed.sentences):
                sent_original = ""
                return SpanInfo(
                    char_start=-1,
                    char_end=-1,
                    sentence_index=sentence_index,
                    token_indices=(),
                    span_text=sent_original,
                )

            sent_parsed = student_parsed.sentences[sentence_index]
            sent_original = sent_parsed.original_text

            # Locate the sentence in the full student answer
            sent_start_in_answer = student_answer_original.find(sent_original)
            if sent_start_in_answer == -1:
                # Fallback: whitespace-resilient search if normalization collapsed spaces
                pattern = r"\s+".join(re.escape(w) for w in sent_original.split())
                match = re.search(pattern, student_answer_original)
                if match:
                    sent_start_in_answer = match.start()

            tokens = sent_parsed.tokens
            subj_idx = relation.subject_index
            pred_idx = relation.predicate_index
            obj_idx = relation.object_index

            # Check if subject was inherited from an earlier clause in a conjoined VP
            # e.g., "A primary key [identifies records] and [cannot contain NULL values]"
            # In coordinated VPs, the subject of the second conjunct is syntactically attached
            # to the first conjunct (head_index points to the first verb).
            # Including the inherited subject token causes the second proposition span to
            # span across the conjunction and duplicate the entire first clause.
            is_inherited_subj = (
                subj_idx is not None
                and pred_idx is not None
                and 0 <= subj_idx < len(tokens)
                and 0 <= pred_idx < len(tokens)
                and tokens[subj_idx].head_index != pred_idx
                and subj_idx < pred_idx
                and tokens[pred_idx].dep == "conj"
            )

            key_token_indices = []

            # Predicate and its clause-internal dependents (aux, neg, prt, etc.)
            if pred_idx is not None and 0 <= pred_idx < len(tokens):
                key_token_indices.append(pred_idx)
                pred_tok = tokens[pred_idx]
                for c_idx in pred_tok.children_indices:
                    if 0 <= c_idx < len(tokens):
                        c = tokens[c_idx]
                        if c.dep in ("aux", "auxpass", "neg", "prt") or (is_inherited_subj and c.dep == "advmod"):
                            key_token_indices.append(c_idx)

            # Object and its compound / adjectival modifiers
            if obj_idx is not None and 0 <= obj_idx < len(tokens):
                key_token_indices.append(obj_idx)
                obj_tok = tokens[obj_idx]
                for c_idx in obj_tok.children_indices:
                    if 0 <= c_idx < len(tokens):
                        c = tokens[c_idx]
                        if c.dep in ("compound", "amod"):
                            key_token_indices.append(c_idx)

            # Subject: only include if it belongs to this clause (not inherited from a prior conjunct)
            if not is_inherited_subj and subj_idx is not None and 0 <= subj_idx < len(tokens):
                key_token_indices.append(subj_idx)
                subj_tok = tokens[subj_idx]
                for c_idx in subj_tok.children_indices:
                    if 0 <= c_idx < len(tokens):
                        c = tokens[c_idx]
                        if c.dep in ("compound", "amod"):
                            key_token_indices.append(c_idx)

            if not key_token_indices:
                return SpanInfo(
                    char_start=-1,
                    char_end=-1,
                    sentence_index=sentence_index,
                    token_indices=(),
                    span_text=sent_original,
                )

            # Compute min/max character offsets within the normalized sentence
            min_start_norm = None
            max_end_norm = None

            for tok_idx in key_token_indices:
                if tok_idx < 0 or tok_idx >= len(tokens):
                    continue
                tok = tokens[tok_idx]
                tok_start = tok.char_offset
                tok_end = tok.char_offset + len(tok.text)
                if min_start_norm is None or tok_start < min_start_norm:
                    min_start_norm = tok_start
                if max_end_norm is None or tok_end > max_end_norm:
                    max_end_norm = tok_end

            if min_start_norm is None or max_end_norm is None:
                return SpanInfo(
                    char_start=-1,
                    char_end=-1,
                    sentence_index=sentence_index,
                    token_indices=tuple(sorted(set(key_token_indices))),
                    span_text=sent_original,
                )

            if sent_start_in_answer == -1:
                # Sentence not found in original answer — cannot compute valid char span
                return SpanInfo(
                    char_start=-1,
                    char_end=-1,
                    sentence_index=sentence_index,
                    token_indices=tuple(sorted(set(key_token_indices))),
                    span_text=sent_original,
                )

            # Map normalized offsets to original answer
            # IMPLEMENTATION DECISION: Since normalization in this system is minimal
            # (lowercasing, basic whitespace normalization), we use normalized offsets
            # directly as an approximation for the original sentence offsets.
            char_start = sent_start_in_answer + min_start_norm
            char_end = sent_start_in_answer + max_end_norm

            # Extract span text from original answer
            if char_start >= 0 and char_end > char_start and char_end <= len(student_answer_original):
                span_text = student_answer_original[char_start:char_end]
            else:
                span_text = sent_original

            return SpanInfo(
                char_start=char_start,
                char_end=char_end,
                sentence_index=sentence_index,
                token_indices=tuple(sorted(set(key_token_indices))),
                span_text=span_text,
            )

        except Exception:
            # Fallback: return invalid span to avoid crashing the extractor
            try:
                fallback_text = student_parsed.sentences[sentence_index].original_text
            except Exception:
                fallback_text = ""
            return SpanInfo(
                char_start=-1,
                char_end=-1,
                sentence_index=sentence_index,
                token_indices=(),
                span_text=fallback_text,
            )

    def _find_sentence_index_for_relation(
        self,
        student_triples: DocumentTriples,
        target_rel: DependencyRelation,
    ) -> int:
        """
        Find the sentence index for a given DependencyRelation within student_triples.

        Searches sentence-by-sentence using to_tuple() + subject_index for disambiguation.

        Parameters
        ----------
        student_triples : DocumentTriples
            The student's complete extracted triples.
        target_rel : DependencyRelation
            The relation whose sentence index we need.

        Returns
        -------
        int
            Zero-based sentence index, or 0 as fallback if not found.
        """
        target_tuple = target_rel.to_tuple()
        for sent_idx, sent_triples in enumerate(student_triples.sentences):
            for rel in sent_triples.canonical_relations:
                if (
                    rel.to_tuple() == target_tuple
                    and rel.subject_index == target_rel.subject_index
                ):
                    return sent_idx
        return 0
