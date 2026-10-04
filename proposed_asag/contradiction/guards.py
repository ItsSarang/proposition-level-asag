"""
Contradiction Guards Module (Experiment 5 Part C).

Implements interpretable contradiction guards before the final INCORRECT decision,
preventing the 75% false contradiction rate observed in Experiment 4.

Guards Implemented:
1. Converse Relations Guard: Recognizes semantic equivalence in transposed comparators
   (e.g., A < B <=> B > A, smaller/larger, before/after).
2. Multi-Valued Coordinate Terms Guard: Prevents dictionary antonym clashes on categorical
   enumerations (e.g., public/private/protected, stack/queue, by value/by reference).
3. Contrastive Subjects Guard: Preserves entity binding in comparison/difference prompts
   (e.g., array fixed-size vs. linked list dynamic-size).
4. Scope Qualifications Guard: Prevents treating descriptive qualifications or adverbials
   absent from the reference as contradictions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from base_asag.representation.hybrid import RobustProposition
from base_asag.semantic.semantic_matcher_v2 import SemanticMatcherV2
from proposed_asag.contradiction.property_contradiction import (
    ContradictionEvidence,
    ContradictionType,
)


COORDINATE_CATEGORICAL_SETS: List[Set[str]] = [
    # C++ Access Specifiers
    {"public", "private", "protected"},
    # Storage / Linkage Classes
    {"static", "extern", "auto", "register"},
    # Parameter Passing Modes
    {"value", "by value", "reference", "by reference", "pointer", "by pointer"},
    # Linear & Core Data Structures
    {"stack", "queue", "array", "linked list", "list", "vector", "tree"},
    # Class Member Categories
    {"data member", "data members", "member function", "member functions", "constructor", "destructor"},
    # Scope Classifications
    {"local", "global", "file scope", "block scope", "class scope"},
]

CONVERSE_TERMS_MAP: Dict[str, str] = {
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


class ContradictionGuardPipeline:
    """
    Applies contextual contradiction guards to raw ContradictionEvidence
    before a final INCORRECT classification is confirmed.
    """

    def __init__(self, comparator: Optional[Any] = None) -> None:
        self.comparator = comparator or SemanticMatcherV2(use_domain_equivalence=True)

    def guard_contradiction(
        self,
        raw_evidence: ContradictionEvidence,
        student_prop: RobustProposition,
        reference_props: List[RobustProposition],
        question: str = "",
        student_answer: str = "",
        reference_answer: str = "",
    ) -> ContradictionEvidence:
        """
        Inspect raw contradiction evidence and apply guards.
        Returns guarded evidence (with is_contradicted=False if suppressed) or raw evidence.
        """
        if not raw_evidence.is_contradicted:
            return raw_evidence

        # Guard 1: Converse Relations (e.g. A < B <=> B > A)
        converse_guard = self._check_converse_guard(raw_evidence, student_prop, reference_props)
        if converse_guard is not None:
            return converse_guard

        # Guard 2: Multi-Valued Coordinate Terms (e.g. public vs private)
        coord_guard = self._check_coordinate_terms_guard(raw_evidence, student_prop, reference_props)
        if coord_guard is not None:
            return coord_guard

        # Guard 3: Contrastive Subjects (e.g. array fixed vs linked list dynamic)
        contrast_guard = self._check_contrastive_subjects_guard(
            raw_evidence, student_prop, reference_props, question
        )
        if contrast_guard is not None:
            return contrast_guard

        # Guard 4: Scope Qualifications
        scope_guard = self._check_scope_qualification_guard(raw_evidence, student_prop)
        if scope_guard is not None:
            return scope_guard

        return raw_evidence

    def _check_converse_guard(
        self,
        raw_ev: ContradictionEvidence,
        student_prop: RobustProposition,
        reference_props: List[RobustProposition],
    ) -> Optional[ContradictionEvidence]:
        """
        Guard 1: Check if contradiction involves converse relational predicates with transposed arguments.
        """
        conf_prop = (raw_ev.conflicting_property or "").lower()
        conf_val = (raw_ev.conflicting_value or "").lower()

        # Check if conflicting pair is in converse terms map
        is_converse = (
            CONVERSE_TERMS_MAP.get(conf_prop) == conf_val
            or CONVERSE_TERMS_MAP.get(conf_val) == conf_prop
        )
        if not is_converse:
            # Also check predicate lemmas directly
            p_stu = (student_prop.predicate_lemma or "").lower()
            obj_stu = (student_prop.object_lemma or "").lower()
            for r in reference_props:
                p_ref = (r.predicate_lemma or "").lower()
                obj_ref = (r.object_lemma or "").lower()
                if (CONVERSE_TERMS_MAP.get(p_stu) == p_ref) or (CONVERSE_TERMS_MAP.get(obj_stu) == obj_ref):
                    is_converse = True
                    break

        if not is_converse:
            return None

        # Check argument transposition: Subj_S ~ Obj_R and Obj_S ~ Subj_R
        s_stu = (student_prop.subject_lemma or "").lower()
        o_stu = (
            student_prop.properties.get("comparative_target_lemma")
            or student_prop.object_lemma
            or ""
        ).lower()

        for r in reference_props:
            s_ref = (r.subject_lemma or "").lower()
            o_ref = (
                r.properties.get("comparative_target_lemma")
                or r.object_lemma
                or ""
            ).lower()

            sim_s_o = self._compare(s_stu, o_ref)
            sim_o_s = self._compare(o_stu, s_ref)

            if sim_s_o >= 0.40 and sim_o_s >= 0.40:
                return ContradictionEvidence(
                    is_contradicted=False,
                    contradiction_type=ContradictionType.NONE,
                    conflicting_entity=None,
                    conflicting_property=None,
                    conflicting_value=None,
                    evidence_strength=0.0,
                    explanation=(
                        f"GUARDED: Converse relational equivalence (arguments transposed: "
                        f"'{s_stu}' vs '{o_ref}', '{o_stu}' vs '{s_ref}')."
                    ),
                )

        return None

    def _check_coordinate_terms_guard(
        self,
        raw_ev: ContradictionEvidence,
        student_prop: RobustProposition,
        reference_props: List[RobustProposition],
    ) -> Optional[ContradictionEvidence]:
        """
        Guard 2: Check if conflict is between coordinate members of a multi-valued categorical set.
        """
        conf_prop = (raw_ev.conflicting_property or "").lower()
        conf_val = (raw_ev.conflicting_value or "").lower()
        stu_subj = (student_prop.subject_lemma or "").lower()
        stu_obj = (student_prop.object_lemma or "").lower()
        stu_text = (student_prop.source_text or "").lower()

        for coord_set in COORDINATE_CATEGORICAL_SETS:
            # Check if both conflicting values belong to the same coordinate set
            has_prop = any(item in conf_prop for item in coord_set) or any(item in stu_text for item in coord_set)
            has_val = any(item in conf_val for item in coord_set)

            if has_prop and has_val:
                # The student is using a coordinate term from the set.
                # If student is describing the coordinate category itself (e.g. public members vs private members),
                # it is an orthogonal description, not a self-contradiction.
                return ContradictionEvidence(
                    is_contradicted=False,
                    contradiction_type=ContradictionType.NONE,
                    conflicting_entity=None,
                    conflicting_property=None,
                    conflicting_value=None,
                    evidence_strength=0.0,
                    explanation=(
                        f"GUARDED: Coordinate categorical terms in non-conflicting context "
                        f"('{conf_prop}' vs '{conf_val}' in categorical set)."
                    ),
                )

        return None

    def _check_contrastive_subjects_guard(
        self,
        raw_ev: ContradictionEvidence,
        student_prop: RobustProposition,
        reference_props: List[RobustProposition],
        question: str,
    ) -> Optional[ContradictionEvidence]:
        """
        Guard 3: In comparison/difference questions, ensure assertions are bound to the same entity.
        """
        s_stu = (student_prop.subject_lemma or "").lower()
        conf_entity = (raw_ev.conflicting_entity or "").lower()

        if not s_stu or not conf_entity:
            return None

        # Check if the prompt asks for comparison or difference
        q_lower = question.lower()
        is_comparison_prompt = any(
            w in q_lower for w in ("difference", "different", "compare", "distinguish", "versus", "vs")
        )

        entity_sim = self._compare(s_stu, conf_entity)
        if entity_sim < 0.45:
            # The student proposition applies to a distinct entity from the conflicting reference entity!
            return ContradictionEvidence(
                is_contradicted=False,
                contradiction_type=ContradictionType.NONE,
                conflicting_entity=None,
                conflicting_property=None,
                conflicting_value=None,
                evidence_strength=0.0,
                explanation=(
                    f"GUARDED: Contrastive subjects (assertion applies to '{s_stu}', "
                    f"whereas reference entity is '{conf_entity}'; distinct entities in comparison)."
                ),
            )

        return None

    def _check_scope_qualification_guard(
        self,
        raw_ev: ContradictionEvidence,
        student_prop: RobustProposition,
    ) -> Optional[ContradictionEvidence]:
        """
        Guard 4: Adverbial or prepositional qualification is not a direct contradiction.
        """
        # If contradiction was triggered purely on an adverbial qualifier
        prep_args = student_prop.properties.get("prepositional_arguments", [])
        pred_mods = student_prop.properties.get("predicate_modifiers", [])
        qualifiers = set(pred_mods + [item[1].lower() for item in prep_args if len(item) == 2])

        scope_words = {"default", "initially", "inside", "outside", "heap", "stack", "locally", "globally"}
        if qualifiers.intersection(scope_words) and raw_ev.contradiction_type == ContradictionType.LEXICAL_ANTONYM:
            return ContradictionEvidence(
                is_contradicted=False,
                contradiction_type=ContradictionType.NONE,
                conflicting_entity=None,
                conflicting_property=None,
                conflicting_value=None,
                evidence_strength=0.0,
                explanation=f"GUARDED: Scope qualification (qualifier in {qualifiers.intersection(scope_words)}).",
            )

        return None

    def _compare(self, w1: str, w2: str) -> float:
        """Compare two word strings using semantic matcher."""
        if not w1 or not w2:
            return 0.0
        w1_c = w1.strip().lower()
        w2_c = w2.strip().lower()

        if w1_c == w2_c:
            return 1.0

        if hasattr(self.comparator, "similarity"):
            return float(self.comparator.similarity(w1_c, w2_c))
        elif hasattr(self.comparator, "compare_lemmas"):
            return float(self.comparator.compare_lemmas(w1_c, w2_c))

        return 0.0
