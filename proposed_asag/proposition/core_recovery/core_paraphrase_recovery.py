"""
Core Paraphrase Recovery Module (Experiment 5 Part A).

When the standard dependency/hybrid matcher leaves a student proposition unmatched,
this module evaluates whether it actually expresses an unfulfilled reference concept.

Principles:
1. Strict Interpretable Evidence: Requires predicate compatibility, entity alignment,
   coordination resolution, or clausal-nominal bridging.
2. No Over-Recovery: Only unfulfilled reference propositions are eligible targets (R18).
3. Explicit Provenance: Emits CORE_PARAPHRASE_RECOVERED with similarity values, rationale,
   and structural evidence. If evidence is insufficient, leaves as genuinely unmatched.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from base_asag.representation.hybrid import RobustProposition
from base_asag.semantic.semantic_matcher_v2 import SemanticMatcherV2


# Directional converse pairs (A < B <=> B > A)
CONVERSE_PREDICATE_PAIRS: Dict[str, str] = {
    "smaller": "larger",
    "larger": "smaller",
    "small": "large",
    "large": "small",
    "smaller": "greater",
    "greater": "smaller",
    "small": "great",
    "great": "small",
    "less": "more",
    "more": "less",
    "lower": "higher",
    "higher": "lower",
    "low": "high",
    "high": "low",
    "before": "after",
    "after": "before",
    "precedes": "follows",
    "follows": "precedes",
    "under": "above",
    "above": "under",
    "below": "above",
    "child": "parent",
    "parent": "child",
}


@dataclass(frozen=True)
class CoreParaphraseRecoveryResult:
    """Provenance record for an individual core paraphrase recovery decision."""
    is_recovered: bool
    student_proposition: RobustProposition
    reference_proposition: Optional[RobustProposition]
    reference_index: Optional[int]
    student_index: int
    reason: str
    confidence: float
    evidence: Dict[str, Any]
    status: str  # "CORE_PARAPHRASE_RECOVERED" or "UNMATCHED_RETAINED"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_recovered": self.is_recovered,
            "student_proposition": self.student_proposition.to_dict(),
            "reference_proposition": self.reference_proposition.to_dict() if self.reference_proposition else None,
            "reference_index": self.reference_index,
            "student_index": self.student_index,
            "reason": self.reason,
            "confidence": round(self.confidence, 4),
            "evidence": self.evidence,
            "status": self.status,
        }


@dataclass(frozen=True)
class CoreRecoveryBatchResult:
    """Batch result of core paraphrase recovery across all unmatched propositions."""
    recovered_propositions: List[CoreParaphraseRecoveryResult]
    unmatched_propositions: List[RobustProposition]
    recovered_count: int
    unmatched_count: int
    provenance_records: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "recovered_count": self.recovered_count,
            "unmatched_count": self.unmatched_count,
            "recovered_propositions": [r.to_dict() for r in self.recovered_propositions],
            "unmatched_propositions": [u.to_dict() for u in self.unmatched_propositions],
            "provenance_records": self.provenance_records,
        }


class CoreParaphraseRecoverer:
    """
    Evaluates unmatched student propositions against unfulfilled reference concepts
    to recover dropped core paraphrases based on transparent linguistic evidence.
    """

    def __init__(
        self,
        comparator: Optional[Any] = None,
        recovery_threshold: float = 0.55,
    ) -> None:
        self.comparator = comparator or SemanticMatcherV2(use_domain_equivalence=True)
        self.recovery_threshold = recovery_threshold

    def recover(
        self,
        unmatched_student_props: Sequence[RobustProposition],
        reference_props: Sequence[RobustProposition],
        matched_reference_indices: Optional[Set[int]] = None,
        question: str = "",
        reference_answer: str = "",
        student_answer: str = "",
    ) -> CoreRecoveryBatchResult:
        """
        Process unmatched student propositions and recover valid core paraphrases.
        """
        matched_ref_set: Set[int] = set(matched_reference_indices or set())
        recovered_results: List[CoreParaphraseRecoveryResult] = []
        remaining_unmatched: List[RobustProposition] = []
        provenance_list: List[Dict[str, Any]] = []

        unfulfilled_ref_indices = [
            i for i in range(len(reference_props)) if i not in matched_ref_set
        ]

        # Greedily match each unmatched student prop to the best unfulfilled reference prop
        for s_idx, stu_prop in enumerate(unmatched_student_props):
            best_ref_idx: Optional[int] = None
            best_score: float = 0.0
            best_reason: str = ""
            best_evidence: Dict[str, Any] = {}

            for r_idx in unfulfilled_ref_indices:
                ref_prop = reference_props[r_idx]
                score, reason, evidence = self._evaluate_paraphrase_evidence(
                    stu_prop=stu_prop,
                    ref_prop=ref_prop,
                    question=question,
                )
                if score > best_score:
                    best_score = score
                    best_ref_idx = r_idx
                    best_reason = reason
                    best_evidence = evidence

            # Gate: require sufficient evidence (R18)
            if best_ref_idx is not None and best_score >= self.recovery_threshold:
                target_ref = reference_props[best_ref_idx]
                # Consume this reference index so it is not double-assigned
                unfulfilled_ref_indices.remove(best_ref_idx)
                matched_ref_set.add(best_ref_idx)

                rec_res = CoreParaphraseRecoveryResult(
                    is_recovered=True,
                    student_proposition=stu_prop,
                    reference_proposition=target_ref,
                    reference_index=best_ref_idx,
                    student_index=s_idx,
                    reason=best_reason,
                    confidence=best_score,
                    evidence=best_evidence,
                    status="CORE_PARAPHRASE_RECOVERED",
                )
                recovered_results.append(rec_res)
                provenance_list.append(rec_res.to_dict())
            else:
                # Retained as genuinely unmatched
                rec_res = CoreParaphraseRecoveryResult(
                    is_recovered=False,
                    student_proposition=stu_prop,
                    reference_proposition=None,
                    reference_index=None,
                    student_index=s_idx,
                    reason="INSUFFICIENT_EVIDENCE",
                    confidence=best_score,
                    evidence={"best_candidate_score": best_score, "best_candidate_reason": best_reason},
                    status="UNMATCHED_RETAINED",
                )
                remaining_unmatched.append(stu_prop)
                provenance_list.append(rec_res.to_dict())

        return CoreRecoveryBatchResult(
            recovered_propositions=recovered_results,
            unmatched_propositions=remaining_unmatched,
            recovered_count=len(recovered_results),
            unmatched_count=len(remaining_unmatched),
            provenance_records=provenance_list,
        )

    def _evaluate_paraphrase_evidence(
        self,
        stu_prop: RobustProposition,
        ref_prop: RobustProposition,
        question: str,
    ) -> Tuple[float, str, Dict[str, Any]]:
        """
        Evaluate interpretable semantic evidence between a student and reference proposition.
        Returns: (score, reason, evidence_dict)
        """
        evidence: Dict[str, Any] = {}

        # 1. Check for Converse Relational Equivalence (A < B <=> B > A)
        converse_score, converse_ev = self._check_converse_equivalence(stu_prop, ref_prop)
        if converse_score >= self.recovery_threshold:
            evidence.update(converse_ev)
            return (converse_score, "CONVERSE_EQUIVALENCE", evidence)

        # 2. Check for Clausal-Nominal Bridge on Unanchored Predicates (e.g. "deallocates memory")
        if ref_prop.subject is None or ref_prop.properties.get("is_unanchored"):
            bridge_score, bridge_ev = self._check_unanchored_predicate_bridge(stu_prop, ref_prop, question)
            if bridge_score >= self.recovery_threshold:
                evidence.update(bridge_ev)
                return (bridge_score, "UNANCHORED_PREDICATE_FULFILLMENT", evidence)

        # 3. Check for Coordinate Concept Fulfillment (e.g. reference 'concept includes X')
        if ref_prop.predicate_lemma == "include" and ref_prop.subject_lemma == "concept":
            coord_score, coord_ev = self._check_coordinate_concept_fulfillment(stu_prop, ref_prop)
            if coord_score >= self.recovery_threshold:
                evidence.update(coord_ev)
                return (coord_score, "COORDINATE_CONCEPT_FULFILLMENT", evidence)

        # 4. Check for Entity-Property Match (e.g. 'dynamic size', 'random access')
        if ref_prop.predicate == "has_property":
            prop_score, prop_ev = self._check_property_bridge(stu_prop, ref_prop)
            if prop_score >= self.recovery_threshold:
                evidence.update(prop_ev)
                return (prop_score, "ENTITY_PROPERTY_BRIDGE", evidence)

        # 5. General Clausal Slot Matching (Coordination / Conjunction Split)
        general_score, general_ev = self._check_slot_alignment(stu_prop, ref_prop)
        evidence.update(general_ev)
        if general_score >= self.recovery_threshold:
            return (general_score, "SLOT_ALIGNMENT_RECOVERY", evidence)

        return (general_score, "INSUFFICIENT_EVIDENCE", evidence)

    def _check_converse_equivalence(
        self, stu_prop: RobustProposition, ref_prop: RobustProposition
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Detect if student is converse of reference (e.g. parent > child vs child < parent).
        """
        p_stu = stu_prop.predicate_lemma.lower()
        p_ref = ref_prop.predicate_lemma.lower()

        # Check if predicates form a converse pair
        is_converse_pred = (
            CONVERSE_PREDICATE_PAIRS.get(p_stu) == p_ref
            or CONVERSE_PREDICATE_PAIRS.get(p_ref) == p_stu
        )

        # Also check comparative objects/adjectives (e.g. 'is greater than' vs 'is smaller than')
        obj_stu = (stu_prop.object_lemma or "").lower()
        obj_ref = (ref_prop.object_lemma or "").lower()
        is_converse_obj = (
            CONVERSE_PREDICATE_PAIRS.get(obj_stu) == obj_ref
            or CONVERSE_PREDICATE_PAIRS.get(obj_ref) == obj_stu
        )

        if not (is_converse_pred or is_converse_obj):
            return (0.0, {})

        # Compare swapped arguments: Subj_S ~ Obj_R and Obj_S ~ Subj_R
        s_stu = (stu_prop.subject_lemma or "").lower()
        s_ref = (ref_prop.subject_lemma or "").lower()

        # Extract comparative targets if copular
        target_stu = (stu_prop.properties.get("comparative_target_lemma") or obj_stu).lower()
        target_ref = (ref_prop.properties.get("comparative_target_lemma") or obj_ref).lower()

        sim_forward = self._compare_lemmas(s_stu, target_ref)
        sim_backward = self._compare_lemmas(target_stu, s_ref)

        avg_arg_sim = (sim_forward + sim_backward) / 2.0
        if avg_arg_sim >= 0.50:
            confidence = 0.85 * avg_arg_sim + 0.15
            return (
                confidence,
                {
                    "converse_predicates": (p_stu, p_ref),
                    "swapped_arg_similarity": round(avg_arg_sim, 4),
                    "confidence": round(confidence, 4),
                },
            )

        return (0.0, {})

    def _check_unanchored_predicate_bridge(
        self,
        stu_prop: RobustProposition,
        ref_prop: RobustProposition,
        question: str,
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Match clausal student proposition to unanchored reference predicate (e.g. 'deallocates memory').
        """
        p_sim = self._compare_lemmas(stu_prop.predicate_lemma, ref_prop.predicate_lemma)
        o_sim = self._compare_lemmas(stu_prop.object_lemma, ref_prop.object_lemma)

        # If predicate and object match with high similarity
        if p_sim >= 0.60 and o_sim >= 0.60:
            score = 0.50 * p_sim + 0.50 * o_sim
            return (
                score,
                {
                    "predicate_similarity": round(p_sim, 4),
                    "object_similarity": round(o_sim, 4),
                    "unanchored_fulfillment": True,
                },
            )

        # Check prepositional arguments
        ref_prep_args = ref_prop.properties.get("prepositional_arguments", [])
        stu_prep_args = stu_prop.properties.get("prepositional_arguments", [])
        prep_sim = 0.0
        if ref_prep_args and stu_prep_args:
            ref_lemmas = [item[1].lower() for item in ref_prep_args if len(item) == 2]
            stu_lemmas = [item[1].lower() for item in stu_prep_args if len(item) == 2]
            overlap = set(ref_lemmas).intersection(set(stu_lemmas))
            prep_sim = len(overlap) / max(1, len(ref_lemmas))

        combined = 0.40 * p_sim + 0.40 * o_sim + 0.20 * prep_sim
        if combined >= self.recovery_threshold:
            return (
                combined,
                {
                    "predicate_similarity": round(p_sim, 4),
                    "object_similarity": round(o_sim, 4),
                    "prep_similarity": round(prep_sim, 4),
                },
            )

        return (combined, {})

    def _check_coordinate_concept_fulfillment(
        self, stu_prop: RobustProposition, ref_prop: RobustProposition
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Match student assertion to coordinate concept (e.g. ref: 'concept includes Abstraction').
        """
        target_concept = (ref_prop.object_lemma or ref_prop.object or "").lower()
        if not target_concept:
            return (0.0, {})

        # Check if student mentions the target concept in object or subject
        stu_obj = (stu_prop.object_lemma or "").lower()
        stu_subj = (stu_prop.subject_lemma or "").lower()

        obj_sim = self._compare_lemmas(stu_obj, target_concept)
        subj_sim = self._compare_lemmas(stu_subj, target_concept)
        best_sim = max(obj_sim, subj_sim)

        if best_sim >= 0.70:
            return (
                best_sim,
                {
                    "target_concept": target_concept,
                    "matched_concept_similarity": round(best_sim, 4),
                },
            )

        # Check word-level containment for multi-word concepts (e.g. 'member functions')
        target_words = set(target_concept.split())
        stu_words = set(f"{stu_subj} {stu_obj}".split())
        if target_words and target_words.issubset(stu_words):
            return (
                0.85,
                {
                    "target_concept": target_concept,
                    "concept_containment": True,
                },
            )

        return (best_sim, {})

    def _check_property_bridge(
        self, stu_prop: RobustProposition, ref_prop: RobustProposition
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Match clausal statement to property fragment (e.g. ref: 'size has_property dynamic').
        """
        ref_entity = (ref_prop.subject_lemma or "").lower()
        ref_prop_val = (ref_prop.object_lemma or "").lower()

        stu_subj = (stu_prop.subject_lemma or "").lower()
        stu_pred = (stu_prop.predicate_lemma or "").lower()
        stu_obj = (stu_prop.object_lemma or "").lower()
        stu_mods = [m.lower() for m in stu_prop.properties.get("object_modifiers", [])]

        # Student: 'arrays have dynamic size' -> obj='size', mod='dynamic'
        e_sim = self._compare_lemmas(stu_obj, ref_entity) or self._compare_lemmas(stu_subj, ref_entity)
        p_sim = max(
            [self._compare_lemmas(stu_pred, ref_prop_val)]
            + [self._compare_lemmas(m, ref_prop_val) for m in stu_mods]
            + [self._compare_lemmas(stu_obj, ref_prop_val)]
        )

        score = 0.50 * e_sim + 0.50 * p_sim
        if score >= self.recovery_threshold:
            return (
                score,
                {
                    "entity_similarity": round(e_sim, 4),
                    "property_similarity": round(p_sim, 4),
                },
            )

        return (score, {})

    def _check_slot_alignment(
        self, stu_prop: RobustProposition, ref_prop: RobustProposition
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Evaluate standard subject-predicate-object slot similarity.
        """
        s_sim = self._compare_lemmas(stu_prop.subject_lemma, ref_prop.subject_lemma)
        p_sim = self._compare_lemmas(stu_prop.predicate_lemma, ref_prop.predicate_lemma)
        o_sim = self._compare_lemmas(stu_prop.object_lemma, ref_prop.object_lemma)

        # Weighting: 0.35 Subj, 0.40 Pred, 0.25 Obj
        score = 0.35 * s_sim + 0.40 * p_sim + 0.25 * o_sim
        return (
            score,
            {
                "subject_similarity": round(s_sim, 4),
                "predicate_similarity": round(p_sim, 4),
                "object_similarity": round(o_sim, 4),
            },
        )

    def _compare_lemmas(self, l1: Optional[str], l2: Optional[str]) -> float:
        """Compare two word lemmas using the semantic matcher."""
        if not l1 or not l2:
            return 0.0
        l1_clean = l1.strip().lower()
        l2_clean = l2.strip().lower()

        if l1_clean == l2_clean:
            return 1.0

        if hasattr(self.comparator, "similarity"):
            return float(self.comparator.similarity(l1_clean, l2_clean))
        elif hasattr(self.comparator, "compare_lemmas"):
            return float(self.comparator.compare_lemmas(l1_clean, l2_clean))
        elif hasattr(self.comparator, "match_words"):
            res = self.comparator.match_words(l1_clean, l2_clean)
            return float(res[0] if isinstance(res, tuple) else res)

        return 0.0
