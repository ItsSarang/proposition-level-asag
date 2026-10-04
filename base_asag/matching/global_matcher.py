"""
Global and Configurable Proposition Matching Module (Phase 4).

Extends Stage 7 dependency triple matching with global bipartite matching
using the Hungarian algorithm (scipy.optimize.linear_sum_assignment) while
preserving backward-compatible greedy matching.

Matching Strategies:
- "greedy": Deterministic highest-score-first assignment.
- "global": Maximum-weight bipartite matching solving linear sum assignment
  over the similarity matrix with threshold constraints.
"""

from typing import Any, Dict, List, Optional, Sequence, Set, Tuple
import numpy as np
from scipy.optimize import linear_sum_assignment

from base_asag.dependency.triples import DependencyRelation, DocumentTriples, SentenceTriples
from base_asag.matching.triple_matcher import (
    CandidateAlignment,
    MatchedRelation,
    MatchingResult,
    TripleMatcher,
)
from base_asag.semantic.relations import LexicalSemanticComparator


class ConfigurableTripleMatcher:
    """
    Dependency triple and proposition matcher supporting both 'greedy'
    and 'global' (Hungarian algorithm) assignment strategies.
    """

    def __init__(
        self,
        comparator: Optional[Any] = None,
        threshold: float = 0.50,
        weights: Optional[Dict[str, float]] = None,
        matching_strategy: str = "greedy",
        enable_cross_slot: bool = False,
    ) -> None:
        """
        Parameters
        ----------
        comparator : Optional[Any]
            Semantic comparator instance (V1 or V2).
        threshold : float
            Minimum alignment score threshold for matching (default 0.50).
        weights : Optional[Dict[str, float]]
            Weights for subject, predicate, and object slots.
        matching_strategy : str
            Either "greedy" or "global" (default "greedy").
        enable_cross_slot : bool, default=False
            Whether to enable cross-slot argument matching and modifier refinement.
        """
        if matching_strategy not in ("greedy", "global"):
            raise ValueError(
                f"Invalid matching_strategy: '{matching_strategy}'. Must be 'greedy' or 'global'."
            )

        self.threshold = threshold
        self.weights = weights or {"subject": 1.0 / 3.0, "predicate": 1.0 / 3.0, "object": 1.0 / 3.0}
        self.matching_strategy = matching_strategy
        self.enable_cross_slot = bool(enable_cross_slot)
        self.comparator = comparator or LexicalSemanticComparator()
        self._greedy_matcher = TripleMatcher(
            comparator=self.comparator,
            alignment_threshold=self.threshold,
            subject_weight=self.weights.get("subject", 1.0 / 3.0),
            predicate_weight=self.weights.get("predicate", 1.0 / 3.0),
            object_weight=self.weights.get("object", 1.0 / 3.0),
            enable_cross_slot=self.enable_cross_slot,
        )

    def match(
        self,
        reference_relations: Sequence[DependencyRelation],
        student_relations: Sequence[DependencyRelation],
    ) -> MatchingResult:
        """
        Align reference and student relations using the configured matching strategy.
        """
        if self.matching_strategy == "greedy":
            return self._greedy_matcher.match(reference_relations, student_relations)

        return self._global_match(reference_relations, student_relations)

    def _global_match(
        self,
        reference_relations: Sequence[DependencyRelation],
        student_relations: Sequence[DependencyRelation],
    ) -> MatchingResult:
        """
        Optimal global bipartite matching via the Hungarian algorithm.
        """
        num_ref = len(reference_relations)
        num_stu = len(student_relations)

        config = {
            "subject_weight": self.weights.get("subject", 1.0 / 3.0),
            "predicate_weight": self.weights.get("predicate", 1.0 / 3.0),
            "object_weight": self.weights.get("object", 1.0 / 3.0),
            "alignment_threshold": self.threshold,
            "matching_strategy": self.matching_strategy,
        }

        if num_ref == 0 or num_stu == 0:
            return MatchingResult(
                matched_relations=[],
                unmatched_reference_relations=list(reference_relations),
                unmatched_student_relations=list(student_relations),
                candidate_alignments=[],
                config=config,
            )

        # 1. Compute all candidate alignments
        all_candidates: List[CandidateAlignment] = []
        score_matrix = np.zeros((num_ref, num_stu), dtype=np.float64)

        for r_idx, ref_rel in enumerate(reference_relations):
            for s_idx, stu_rel in enumerate(student_relations):
                subj_sim, obj_sim, pred_sim, evidence = self._greedy_matcher.compare_slots(ref_rel, stu_rel)
                is_sp_pair = (ref_rel.object is None and stu_rel.object is None)
                triple_score = self._greedy_matcher.compute_triple_score(
                    subject_similarity=subj_sim,
                    predicate_similarity=pred_sim,
                    object_similarity=obj_sim,
                    is_sp_pair=is_sp_pair,
                )
                is_eligible = triple_score >= self.threshold
                cand = CandidateAlignment(
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
                all_candidates.append(cand)
                score_matrix[r_idx, s_idx] = cand.triple_score

        # 2. Formulate cost matrix for linear sum assignment (minimization of negative scores)
        cost_matrix = -score_matrix
        row_ind, col_ind = linear_sum_assignment(cost_matrix)

        # 3. Filter matched pairs by threshold
        matched_relations: List[MatchedRelation] = []
        matched_ref_indices: Set[int] = set()
        matched_stu_indices: Set[int] = set()

        for r_idx, s_idx in zip(row_ind, col_ind):
            score = float(score_matrix[r_idx, s_idx])
            if score >= self.threshold:
                cand = next(
                    c for c in all_candidates
                    if c.reference_index == r_idx and c.student_index == s_idx
                )
                is_sp_pair = (cand.reference_relation.object is None and cand.student_relation.object is None)
                has_obj_asym = ((cand.reference_relation.object is None) != (cand.student_relation.object is None))
                match_method = self._greedy_matcher._determine_match_method(
                    cand.slot_evidence, is_sp_pair, has_obj_asym
                )

                matched_relations.append(
                    MatchedRelation(
                        reference_relation=cand.reference_relation,
                        student_relation=cand.student_relation,
                        reference_index=r_idx,
                        student_index=s_idx,
                        subject_similarity=cand.subject_similarity,
                        predicate_similarity=cand.predicate_similarity,
                        object_similarity=cand.object_similarity,
                        triple_score=cand.triple_score,
                        threshold=self.threshold,
                        match_method=match_method,
                        slot_evidence=cand.slot_evidence,
                    )
                )
                matched_ref_indices.add(r_idx)
                matched_stu_indices.add(s_idx)

        # Sort matches deterministically by reference index
        matched_relations.sort(key=lambda m: m.reference_index)

        # 4. Partition unmatched relations
        unmatched_ref = [
            rel for idx, rel in enumerate(reference_relations)
            if idx not in matched_ref_indices
        ]
        unmatched_stu = [
            rel for idx, rel in enumerate(student_relations)
            if idx not in matched_stu_indices
        ]

        return MatchingResult(
            matched_relations=matched_relations,
            unmatched_reference_relations=unmatched_ref,
            unmatched_student_relations=unmatched_stu,
            candidate_alignments=all_candidates,
            config=config,
        )
