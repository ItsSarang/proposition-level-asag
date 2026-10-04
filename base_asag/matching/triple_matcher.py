"""
Base ASAG Dependency Triple Matching Module (Stage 7).

Aligns clause-level dependency relations (subject, predicate, object) between
a reference answer and a student answer using the 4-level semantic hierarchy
from Stage 6.

Key Research Boundaries:
-----------------------
- Operates strictly on structured dependency relations (DependencyRelation from Stage 5).
- Evaluates individual slot similarities using Stage 6 (LexicalSemanticComparator).
- Preserves subject, predicate, and object grammatical roles.
- Employs deterministic one-to-one greedy matching.
- Explicitly partitions relations into:
    1. matched_relations
    2. unmatched_reference_relations
    3. unmatched_student_relations
- Does NOT perform sentence embeddings, cosine similarity, or textual entailment.
- Does NOT classify unmatched student information as correct, irrelevant, or incorrect.
- Does NOT compute a final ASAG grade.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from base_asag.dependency.triples import DependencyRelation, DocumentTriples, SentenceTriples
from base_asag.semantic.relations import LexicalSemanticComparator, SemanticRelation


@dataclass(frozen=True)
class CandidateAlignment:
    """
    Evaluated candidate alignment between a reference relation and a student relation.

    Attributes
    ----------
    reference_relation : DependencyRelation
        The candidate reference relation.
    student_relation : DependencyRelation
        The candidate student relation.
    reference_index : int
        Index of the reference relation in the input sequence.
    student_index : int
        Index of the student relation in the input sequence.
    subject_similarity : float
        Semantic similarity score between subject slots in [0.0, 1.0].
    predicate_similarity : float
        Semantic similarity score between predicate slots in [0.0, 1.0].
    object_similarity : Optional[float]
        Semantic similarity score between object slots in [0.0, 1.0],
        or None if both relations are intransitive (SP).
    triple_score : float
        Weighted continuous alignment score in [0.0, 1.0].
    slot_evidence : Dict[str, SemanticRelation]
        Detailed Stage 6 semantic relations for each slot ('subject', 'predicate', 'object').
    is_eligible : bool
        Whether triple_score meets or exceeds the alignment threshold.
    """
    reference_relation: DependencyRelation
    student_relation: DependencyRelation
    reference_index: int
    student_index: int
    subject_similarity: float
    predicate_similarity: float
    object_similarity: Optional[float]
    triple_score: float
    slot_evidence: Dict[str, SemanticRelation]
    is_eligible: bool

    def to_dict(self) -> Dict[str, Any]:
        """Convert candidate alignment to dictionary format."""
        return {
            "reference_relation": self.reference_relation.to_dict(),
            "student_relation": self.student_relation.to_dict(),
            "reference_index": self.reference_index,
            "student_index": self.student_index,
            "subject_similarity": self.subject_similarity,
            "predicate_similarity": self.predicate_similarity,
            "object_similarity": self.object_similarity,
            "triple_score": self.triple_score,
            "slot_evidence": {k: v.to_dict() for k, v in self.slot_evidence.items()},
            "is_eligible": self.is_eligible,
        }


@dataclass(frozen=True)
class MatchedRelation:
    """
    Established one-to-one alignment between a reference and student relation.

    Attributes
    ----------
    reference_relation : DependencyRelation
        The matched reference relation.
    student_relation : DependencyRelation
        The matched student relation.
    reference_index : int
        Index of the reference relation in the input sequence.
    student_index : int
        Index of the student relation in the input sequence.
    subject_similarity : float
        Semantic similarity score between subject slots in [0.0, 1.0].
    predicate_similarity : float
        Semantic similarity score between predicate slots in [0.0, 1.0].
    object_similarity : Optional[float]
        Semantic similarity score between object slots in [0.0, 1.0], or None.
    triple_score : float
        Continuous weighted alignment score in [0.0, 1.0].
    threshold : float
        Alignment threshold applied during matching.
    match_method : str
        Descriptive classification of the match type:
        - "exact_triple": All active slots matched identically at surface level.
        - "lemma_triple": All active slots matched at exact or lemma level.
        - "semantic_synonym_triple": An active slot matched via WordNet shared synset.
        - "semantic_path_triple": An active slot matched via WordNet path similarity.
        - "weighted_slots": General composite weighted match.
    slot_evidence : Dict[str, SemanticRelation]
        Detailed Stage 6 semantic relations for each constituent slot.
    """
    reference_relation: DependencyRelation
    student_relation: DependencyRelation
    reference_index: int
    student_index: int
    subject_similarity: float
    predicate_similarity: float
    object_similarity: Optional[float]
    triple_score: float
    threshold: float
    match_method: str
    slot_evidence: Dict[str, SemanticRelation]

    def to_dict(self) -> Dict[str, Any]:
        """Convert matched relation to dictionary format."""
        return {
            "reference_relation": self.reference_relation.to_dict(),
            "student_relation": self.student_relation.to_dict(),
            "reference_index": self.reference_index,
            "student_index": self.student_index,
            "subject_similarity": self.subject_similarity,
            "predicate_similarity": self.predicate_similarity,
            "object_similarity": self.object_similarity,
            "triple_score": self.triple_score,
            "threshold": self.threshold,
            "match_method": self.match_method,
            "slot_evidence": {k: v.to_dict() for k, v in self.slot_evidence.items()},
        }


@dataclass(frozen=True)
class MatchingResult:
    """
    Complete result of dependency triple matching between a reference answer
    and a student answer.

    Attributes
    ----------
    matched_relations : List[MatchedRelation]
        Aligned one-to-one relation pairs meeting the threshold.
    unmatched_reference_relations : List[DependencyRelation]
        Reference relations not aligned to any student relation.
    unmatched_student_relations : List[DependencyRelation]
        Student relations not aligned to any reference relation.
    candidate_alignments : List[CandidateAlignment]
        All evaluated candidate alignments prior to greedy selection.
    config : Dict[str, Any]
        Configuration parameters used during matching.
    """
    matched_relations: List[MatchedRelation]
    unmatched_reference_relations: List[DependencyRelation]
    unmatched_student_relations: List[DependencyRelation]
    candidate_alignments: List[CandidateAlignment]
    config: Dict[str, Any]

    @property
    def matched_count(self) -> int:
        """Return number of matched relation pairs."""
        return len(self.matched_relations)

    @property
    def unmatched_reference_count(self) -> int:
        """Return number of unmatched reference relations."""
        return len(self.unmatched_reference_relations)

    @property
    def unmatched_student_count(self) -> int:
        """Return number of unmatched student relations."""
        return len(self.unmatched_student_relations)

    def to_dict(self) -> Dict[str, Any]:
        """Convert matching result to dictionary format."""
        return {
            "matched_relations": [m.to_dict() for m in self.matched_relations],
            "unmatched_reference_relations": [
                r.to_dict() for r in self.unmatched_reference_relations
            ],
            "unmatched_student_relations": [
                s.to_dict() for s in self.unmatched_student_relations
            ],
            "candidate_alignments": [c.to_dict() for c in self.candidate_alignments],
            "config": self.config,
            "matched_count": self.matched_count,
            "unmatched_reference_count": self.unmatched_reference_count,
            "unmatched_student_count": self.unmatched_student_count,
        }


class TripleMatcher:
    """
    Matches reference dependency relations against student dependency relations.

    Attributes
    ----------
    comparator : LexicalSemanticComparator
        Stage 6 comparator used for slot-level semantic evaluation.
    subject_weight : float
        Relative importance weight for the subject slot.
    predicate_weight : float
        Relative importance weight for the predicate slot.
    object_weight : float
        Relative importance weight for the object slot.
    alignment_threshold : float
        Minimum continuous triple alignment score required to form a match.
    """

    DEFAULT_SUBJECT_WEIGHT = 1.0 / 3.0
    DEFAULT_PREDICATE_WEIGHT = 1.0 / 3.0
    DEFAULT_OBJECT_WEIGHT = 1.0 / 3.0
    DEFAULT_ALIGNMENT_THRESHOLD = 0.5

    def __init__(
        self,
        comparator: Optional[LexicalSemanticComparator] = None,
        subject_weight: float = DEFAULT_SUBJECT_WEIGHT,
        predicate_weight: float = DEFAULT_PREDICATE_WEIGHT,
        object_weight: float = DEFAULT_OBJECT_WEIGHT,
        alignment_threshold: float = DEFAULT_ALIGNMENT_THRESHOLD,
        enable_cross_slot: bool = False,
        min_predicate_threshold: Optional[float] = None,
        min_cross_slot_arg_threshold: float = 0.70,
    ):
        """
        Initialize TripleMatcher with configurable weights and threshold.

        Parameters
        ----------
        comparator : Optional[LexicalSemanticComparator], default=None
            Lexical comparator from Stage 6. If None, instantiates a default comparator.
        subject_weight : float, default=1/3
            Relative weight for subject slot similarity.
        predicate_weight : float, default=1/3
            Relative weight for predicate slot similarity.
        object_weight : float, default=1/3
            Relative weight for object slot similarity.
        alignment_threshold : float, default=0.5
            Threshold in [0.0, 1.0] for admitting a candidate pair into matching.
        enable_cross_slot : bool, default=False
            Whether to enable cross-slot argument matching and modifier refinement.
        min_predicate_threshold : Optional[float], default=None
            Minimum predicate similarity required for eligibility.
            Defaults to 0.50 when enable_cross_slot is True, and 0.0 otherwise.
        min_cross_slot_arg_threshold : float, default=0.70
            Minimum similarity required for an argument to cross syntactic slots.
        """
        if subject_weight < 0 or predicate_weight < 0 or object_weight < 0:
            raise ValueError("Slot weights must be non-negative.")
        if (subject_weight + predicate_weight + object_weight) <= 0:
            raise ValueError("Sum of slot weights must be greater than zero.")
        if not (0.0 <= alignment_threshold <= 1.0):
            raise ValueError(
                f"alignment_threshold must be between 0.0 and 1.0, got {alignment_threshold}."
            )

        self.comparator = comparator or LexicalSemanticComparator()
        self.subject_weight = float(subject_weight)
        self.predicate_weight = float(predicate_weight)
        self.object_weight = float(object_weight)
        self.alignment_threshold = float(alignment_threshold)
        self.enable_cross_slot = bool(enable_cross_slot)
        self.min_predicate_threshold = (
            float(min_predicate_threshold)
            if min_predicate_threshold is not None
            else (0.50 if self.enable_cross_slot else 0.0)
        )
        self.min_cross_slot_arg_threshold = float(min_cross_slot_arg_threshold)

    def _coerce_relations(self, relations_input: Any) -> List[DependencyRelation]:
        """
        Coerce various input representations into a list of DependencyRelation objects.

        Supports:
        - List / Sequence of DependencyRelation
        - Single DependencyRelation
        - SentenceTriples (extracts canonical_relations)
        - DocumentTriples (extracts canonical_relations from all sentences)
        """
        if relations_input is None:
            raise TypeError("Relations input cannot be None.")

        if isinstance(relations_input, DependencyRelation):
            return [relations_input]

        if isinstance(relations_input, SentenceTriples):
            return list(relations_input.canonical_relations)

        if isinstance(relations_input, DocumentTriples):
            all_rels: List[DependencyRelation] = []
            for sent_tr in relations_input.sentences:
                all_rels.extend(sent_tr.canonical_relations)
            return all_rels

        if isinstance(relations_input, (list, tuple)):
            for i, item in enumerate(relations_input):
                if not isinstance(item, DependencyRelation):
                    raise TypeError(
                        f"Element {i} in relations list is {type(item).__name__}, "
                        "expected DependencyRelation."
                    )
            return list(relations_input)

        raise TypeError(
            f"Unsupported relations input type: {type(relations_input).__name__}. "
            "Expected List[DependencyRelation], SentenceTriples, or DocumentTriples."
        )

    def compare_slots(
        self,
        ref_rel: DependencyRelation,
        stu_rel: DependencyRelation,
    ) -> Tuple[float, Optional[float], float, Dict[str, SemanticRelation]]:
        """
        Compare the subject, predicate, and object slots between two relations,
        incorporating cross-slot argument flexibility and modifier refinement.

        Returns
        -------
        Tuple[float, Optional[float], float, Dict[str, SemanticRelation]]
            (subject_score, object_score, predicate_score, slot_evidence)
        """
        # 1. Predicate slot comparison (both are clausal verbal predicates)
        pred_rel = self.comparator.compare(
            source=ref_rel.predicate,
            target=stu_rel.predicate,
            source_lemma=ref_rel.predicate_lemma,
            target_lemma=stu_rel.predicate_lemma,
            source_pos="VERB",
            target_pos="VERB",
        )
        pred_score = pred_rel.similarity_score

        # 2. Subject slot comparison (both are nominal arguments)
        is_ref_nonfinite_subj = (
            ref_rel.subject.lower() in ("it", "to", "there", "what", "which")
            or ref_rel.subject_lemma.lower() in ("it", "to", "there", "what", "which")
        )

        subj_rel = self.comparator.compare(
            source=ref_rel.subject,
            target=stu_rel.subject,
            source_lemma=ref_rel.subject_lemma,
            target_lemma=stu_rel.subject_lemma,
            source_pos="NOUN",
            target_pos="NOUN",
        )
        subj_score = subj_rel.similarity_score

        # 3. Object slot comparison
        obj_rel: Optional[SemanticRelation] = None
        obj_score: Optional[float] = None

        if ref_rel.object is not None and stu_rel.object is not None:
            # Both relations possess direct objects
            obj_rel = self.comparator.compare(
                source=ref_rel.object,
                target=stu_rel.object,
                source_lemma=ref_rel.object_lemma,
                target_lemma=stu_rel.object_lemma,
                source_pos="NOUN",
                target_pos="NOUN",
            )
            obj_score = obj_rel.similarity_score
        elif ref_rel.object is None and stu_rel.object is None:
            # Both relations are intransitive (SP relations) - no direct object
            obj_score = None
        else:
            # Asymmetry: one relation has a direct object, the other does not
            obj_score = 0.0

        # Extended cross-slot argument matching and modifier refinement
        # (Enabled only when enable_cross_slot is True and predicate aligns: pred_score >= 0.50)
        if self.enable_cross_slot and pred_score >= 0.50:
            # Subject refinement
            is_ref_nonfinite_subj = (
                ref_rel.subject.lower() in ("it", "to", "there", "what", "which")
                or ref_rel.subject_lemma.lower() in ("it", "to", "there", "what", "which")
            )
            if is_ref_nonfinite_subj:
                is_grounded = (pred_score >= 0.70) or (obj_score is not None and obj_score >= 0.70)
                if is_grounded:
                    subj_score = max(subj_score, 1.0)
            elif subj_score < 0.70:
                best_mod_subj_score = subj_score
                best_subj_mod_rel = subj_rel
                stu_smods = getattr(stu_rel, "subject_modifiers", ())
                for s_mod in stu_smods:
                    mod_comp = self.comparator.compare(
                        source=ref_rel.subject_lemma,
                        target=s_mod,
                        source_pos="NOUN",
                        target_pos="NOUN",
                    )
                    if mod_comp.similarity_score * 0.90 > best_mod_subj_score:
                        best_mod_subj_score = mod_comp.similarity_score * 0.90
                        best_subj_mod_rel = mod_comp

                ref_smods = getattr(ref_rel, "subject_modifiers", ())
                for r_mod in ref_smods:
                    mod_comp = self.comparator.compare(
                        source=r_mod,
                        target=stu_rel.subject_lemma,
                        source_pos="NOUN",
                        target_pos="NOUN",
                    )
                    if mod_comp.similarity_score * 0.90 > best_mod_subj_score:
                        best_mod_subj_score = mod_comp.similarity_score * 0.90
                        best_subj_mod_rel = mod_comp

                if best_mod_subj_score > subj_score:
                    subj_score = best_mod_subj_score
                    subj_rel = best_subj_mod_rel

            # Object cross-slot matching
            best_obj_score = obj_score if obj_score is not None else 0.0
            best_cross_rel: Optional[SemanticRelation] = None

            ref_preps = getattr(ref_rel, "prepositional_arguments", ())
            stu_preps = getattr(stu_rel, "prepositional_arguments", ())
            ref_omods = getattr(ref_rel, "object_modifiers", ())
            stu_omods = getattr(stu_rel, "object_modifiers", ())

            # Check 1: Student object matching Reference prepositional arguments
            # e.g., stu.object="portions" vs ref.prepositional_arguments=[("of", "portion"), ("of", "product")]
            if stu_rel.object is not None:
                for prep, pobj in ref_preps:
                    cross_comp = self.comparator.compare(
                        source=pobj,
                        target=stu_rel.object,
                        source_lemma=pobj,
                        target_lemma=stu_rel.object_lemma,
                        source_pos="NOUN",
                        target_pos="NOUN",
                    )
                    if cross_comp.similarity_score >= self.min_cross_slot_arg_threshold:
                        candidate_score = cross_comp.similarity_score * 0.90
                        if candidate_score > best_obj_score:
                            best_obj_score = candidate_score
                            best_cross_rel = cross_comp

            # Check 2: Reference object matching Student prepositional arguments
            # e.g., ref.object="code" vs stu.prepositional_arguments=[("into", "code")]
            if ref_rel.object is not None:
                for prep, pobj in stu_preps:
                    cross_comp = self.comparator.compare(
                        source=ref_rel.object,
                        target=pobj,
                        source_lemma=ref_rel.object_lemma,
                        target_lemma=pobj,
                        source_pos="NOUN",
                        target_pos="NOUN",
                    )
                    if cross_comp.similarity_score >= self.min_cross_slot_arg_threshold:
                        candidate_score = cross_comp.similarity_score * 0.90
                        if candidate_score > best_obj_score:
                            best_obj_score = candidate_score
                            best_cross_rel = cross_comp

            # Check 3: Object modifier matching (compound / amod)
            # e.g., ref.object="value", modifier="boolean" vs stu.object="boolean"
            if ref_rel.object is not None and stu_rel.object is not None:
                for r_mod in ref_omods:
                    mod_comp = self.comparator.compare(
                        source=r_mod,
                        target=stu_rel.object,
                        source_pos="NOUN",
                        target_pos="NOUN",
                    )
                    if mod_comp.similarity_score >= self.min_cross_slot_arg_threshold:
                        candidate_score = mod_comp.similarity_score * 0.90
                        if candidate_score > best_obj_score:
                            best_obj_score = candidate_score
                            best_cross_rel = mod_comp

                for s_mod in stu_omods:
                    mod_comp = self.comparator.compare(
                        source=ref_rel.object,
                        target=s_mod,
                        source_pos="NOUN",
                        target_pos="NOUN",
                    )
                    if mod_comp.similarity_score >= self.min_cross_slot_arg_threshold:
                        candidate_score = mod_comp.similarity_score * 0.90
                        if candidate_score > best_obj_score:
                            best_obj_score = candidate_score
                            best_cross_rel = mod_comp

            # If cross-slot yielded a strictly higher score, update obj_score and obj_rel
            current_obj = obj_score if obj_score is not None else 0.0
            if best_cross_rel is not None and best_obj_score > current_obj:
                obj_score = best_obj_score
                obj_rel = best_cross_rel

            # Re-check grounded non-finite subject relaxation if obj_score was updated by cross-slot matching
            if is_ref_nonfinite_subj and subj_score < 1.0:
                is_grounded = (pred_score >= 0.70) or (obj_score is not None and obj_score >= 0.70)
                if is_grounded:
                    subj_score = max(subj_score, 1.0)

            # Zero-argument relation hollow match gate:
            # If reference relation has a dummy placeholder subject ("it", "to", "there", "what", "which"),
            # no direct object, and no prepositional arguments (zero semantic arguments),
            # it cannot match an argument-free student relation on a weak path similarity.
            # It requires exact/lemma/domain match (pred_score >= 0.80).
            is_ref_nonfinite_placeholder = (
                ref_rel.subject.lower() in ("it", "to", "there", "what", "which")
                or ref_rel.subject_lemma.lower() in ("it", "to", "there", "what", "which")
            )
            is_ref_arg_free = (
                ref_rel.object is None and len(ref_preps) == 0
            )
            is_stu_arg_free = (
                stu_rel.object is None and len(stu_preps) == 0
            )
            if is_ref_nonfinite_placeholder and is_ref_arg_free and is_stu_arg_free:
                if pred_score < 0.80:
                    pred_score = 0.0
                    subj_score = 0.0

        slot_evidence: Dict[str, SemanticRelation] = {
            "subject": subj_rel,
            "predicate": pred_rel,
        }
        if obj_rel is not None:
            slot_evidence["object"] = obj_rel

        return subj_score, obj_score, pred_score, slot_evidence

    def compute_triple_score(
        self,
        subject_similarity: float,
        predicate_similarity: float,
        object_similarity: Optional[float],
        is_sp_pair: bool,
    ) -> float:
        """
        Compute weighted alignment score across active slots.

        When is_sp_pair is True and object_similarity is None, active weights are
        normalized over subject and predicate slots only. When object_similarity is
        provided (e.g. through prepositional argument alignment), three-slot
        weighting is applied.
        """
        # Predicate eligibility gate: propositions asserting incompatible actions cannot align
        if predicate_similarity < self.min_predicate_threshold:
            return 0.0

        if is_sp_pair and object_similarity is None:
            # Normalization over active slots (subject + predicate)
            active_weight_sum = self.subject_weight + self.predicate_weight
            if active_weight_sum <= 0:
                return 0.0
            norm_subj_w = self.subject_weight / active_weight_sum
            norm_pred_w = self.predicate_weight / active_weight_sum
            score = (norm_subj_w * subject_similarity) + (norm_pred_w * predicate_similarity)
        else:
            # Three-slot weighting (subject + predicate + object)
            total_weight_sum = self.subject_weight + self.predicate_weight + self.object_weight
            if total_weight_sum <= 0:
                return 0.0
            norm_subj_w = self.subject_weight / total_weight_sum
            norm_pred_w = self.predicate_weight / total_weight_sum
            norm_obj_w = self.object_weight / total_weight_sum
            actual_obj_sim = object_similarity if object_similarity is not None else 0.0
            score = (
                (norm_subj_w * subject_similarity)
                + (norm_pred_w * predicate_similarity)
                + (norm_obj_w * actual_obj_sim)
            )

        return float(round(score, 6))

    def _determine_match_method(
        self,
        slot_evidence: Dict[str, SemanticRelation],
        is_sp_pair: bool,
        has_object_asymmetry: bool,
    ) -> str:
        """Determine a human-interpretable label for the composite match type."""
        if has_object_asymmetry:
            return "partial_structural_match"

        methods = [rel.method for rel in slot_evidence.values()]

        if all(m == "exact_match" for m in methods):
            return "exact_triple"
        if all(m in ("exact_match", "lemma_match") for m in methods):
            return "lemma_triple"
        if any(m == "wordnet_synonym" for m in methods):
            return "semantic_synonym_triple"
        if any(m == "wordnet_path" for m in methods):
            return "semantic_path_triple"

        return "weighted_slots"

    def match(
        self,
        reference_relations: Any,
        student_relations: Any,
    ) -> MatchingResult:
        """
        Perform one-to-one dependency triple matching between reference and student answers.

        Parameters
        ----------
        reference_relations : Any
            Reference relations (List[DependencyRelation], SentenceTriples, or DocumentTriples).
        student_relations : Any
            Student relations (List[DependencyRelation], SentenceTriples, or DocumentTriples).

        Returns
        -------
        MatchingResult
            Structured result containing matched pairs, unmatched reference relations,
            unmatched student relations, candidate alignments, and configuration.
        """
        ref_list = self._coerce_relations(reference_relations)
        stu_list = self._coerce_relations(student_relations)

        config = {
            "subject_weight": self.subject_weight,
            "predicate_weight": self.predicate_weight,
            "object_weight": self.object_weight,
            "alignment_threshold": self.alignment_threshold,
            "reference_relations_count": len(ref_list),
            "student_relations_count": len(stu_list),
        }

        # Handle trivial empty cases immediately
        if not ref_list and not stu_list:
            return MatchingResult([], [], [], [], config)
        if not ref_list:
            return MatchingResult([], [], list(stu_list), [], config)
        if not stu_list:
            return MatchingResult([], list(ref_list), [], [], config)

        # 1. Generate all candidate alignments and compute continuous scores
        candidate_alignments: List[CandidateAlignment] = []

        for r_idx, ref_rel in enumerate(ref_list):
            for s_idx, stu_rel in enumerate(stu_list):
                subj_sim, obj_sim, pred_sim, evidence = self.compare_slots(ref_rel, stu_rel)

                is_sp_pair = (ref_rel.object is None and stu_rel.object is None)
                triple_score = self.compute_triple_score(
                    subject_similarity=subj_sim,
                    predicate_similarity=pred_sim,
                    object_similarity=obj_sim,
                    is_sp_pair=is_sp_pair,
                )

                is_eligible = triple_score >= self.alignment_threshold

                candidate = CandidateAlignment(
                    reference_relation=ref_rel,
                    student_relation=stu_rel,
                    reference_index=r_idx,
                    student_index=s_idx,
                    subject_similarity=subj_sim,
                    predicate_similarity=pred_sim,
                    object_similarity=obj_sim,
                    triple_score=triple_score,
                    slot_evidence=evidence,
                    is_eligible=is_eligible,
                )
                candidate_alignments.append(candidate)

        # 2. Filter eligible candidates
        eligible_candidates = [c for c in candidate_alignments if c.is_eligible]

        # 3. Sort candidates deterministically
        # Tie-breaking rule:
        #   1. triple_score descending (-c.triple_score)
        #   2. reference_index ascending (c.reference_index)
        #   3. student_index ascending (c.student_index)
        sorted_candidates = sorted(
            eligible_candidates,
            key=lambda c: (-c.triple_score, c.reference_index, c.student_index),
        )

        # 4. Greedy one-to-one selection
        matched_relations: List[MatchedRelation] = []
        used_ref_indices: Set[int] = set()
        used_stu_indices: Set[int] = set()

        for cand in sorted_candidates:
            if cand.reference_index in used_ref_indices:
                continue
            if cand.student_index in used_stu_indices:
                continue

            # Establish alignment
            used_ref_indices.add(cand.reference_index)
            used_stu_indices.add(cand.student_index)

            ref_rel = cand.reference_relation
            stu_rel = cand.student_relation
            is_sp_pair = (ref_rel.object is None and stu_rel.object is None)
            has_obj_asymmetry = (ref_rel.object is None) != (stu_rel.object is None)

            match_method = self._determine_match_method(
                cand.slot_evidence, is_sp_pair, has_obj_asymmetry
            )

            matched_relations.append(
                MatchedRelation(
                    reference_relation=cand.reference_relation,
                    student_relation=cand.student_relation,
                    reference_index=cand.reference_index,
                    student_index=cand.student_index,
                    subject_similarity=cand.subject_similarity,
                    predicate_similarity=cand.predicate_similarity,
                    object_similarity=cand.object_similarity,
                    triple_score=cand.triple_score,
                    threshold=self.alignment_threshold,
                    match_method=match_method,
                    slot_evidence=cand.slot_evidence,
                )
            )

        # 5. Collect unmatched reference relations
        unmatched_ref: List[DependencyRelation] = [
            ref_list[i] for i in range(len(ref_list)) if i not in used_ref_indices
        ]

        # 6. Collect unmatched student relations
        unmatched_stu: List[DependencyRelation] = [
            stu_list[j] for j in range(len(stu_list)) if j not in used_stu_indices
        ]

        return MatchingResult(
            matched_relations=matched_relations,
            unmatched_reference_relations=unmatched_ref,
            unmatched_student_relations=unmatched_stu,
            candidate_alignments=candidate_alignments,
            config=config,
        )
