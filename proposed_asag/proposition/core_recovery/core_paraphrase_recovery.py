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

from nltk.corpus import wordnet as wn
from base_asag.representation.hybrid import PropositionType, RobustProposition
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
    "above": "below",
    "child": "parent",
    "parent": "child",
    "inside": "outside",
    "outside": "inside",
}

# Verbs asserting containment relations
CONTAINMENT_VERBS: Set[str] = {
    "contain", "hold", "store", "include", "enclose", "house", "have",
}

# Locative containment prepositions
LOCATIVE_PREPS: Set[str] = {"in", "inside", "within", "into"}

# Mutually exclusive entity qualifiers in Computer Science
INCOMPATIBLE_ENTITY_QUALIFIERS: List[Tuple[Set[str], Set[str]]] = [
    ({"primary"}, {"foreign", "secondary", "candidate"}),
    ({"foreign"}, {"primary", "secondary", "candidate"}),
    ({"local"}, {"global", "static"}),
    ({"global"}, {"local", "static"}),
    ({"static"}, {"dynamic"}),
    ({"dynamic"}, {"static"}),
    ({"singly", "single"}, {"doubly", "double"}),
    ({"doubly", "double"}, {"singly", "single"}),
    ({"stack"}, {"queue", "deque"}),
    ({"queue"}, {"stack", "deque"}),
    ({"row", "record"}, {"column", "attribute", "field"}),
    ({"column", "attribute", "field"}, {"row", "record"}),
    ({"compile", "compilation", "compile-time"}, {"run", "runtime", "execution"}),
    ({"runtime", "execution"}, {"compile", "compilation", "compile-time"}),
]

# Mutually exclusive property value sets in Computer Science
INCOMPATIBLE_PROPERTY_VALUE_SETS: Dict[str, Tuple[Set[str], Set[str]]] = {
    "uniqueness": (
        {"unique", "distinct", "uniquely"},
        {"duplicate", "identical", "repeated", "redundant", "same"},
    ),
    "size_mutability": (
        {"variable", "dynamic", "resizable", "growable"},
        {"fixed", "static", "constant", "inflexible"},
    ),
    "nullability": (
        {"null", "nil", "empty"},
        {"non-null", "not null", "cannot be null"},
    ),
    "pass_mechanism": (
        {"reference", "by reference"},
        {"value", "by value"},
    ),
    "ordering": (
        {"before", "prior"},
        {"after", "following", "later"},
    ),
    "spatial_position": (
        {"above", "over", "top"},
        {"below", "under", "bottom"},
    ),
    "relative_size": (
        {"smaller", "less", "lower", "fewer", "minor", "small", "shortest"},
        {"larger", "greater", "higher", "more", "major", "large", "bigger", "longest"},
    ),
    "access_discipline": (
        {"lifo", "last in first out", "last-in-first-out", "last-in, first-out", "last in, first out"},
        {"fifo", "first in first out", "first-in-first-out", "first-in, first-out", "first in, first out"},
    ),
    "sort_order": (
        {"ascending", "increasing", "nondecreasing"},
        {"descending", "decreasing", "nonincreasing"},
    ),
    "access_pattern": (
        {"random", "randomly", "direct", "directly", "arbitrary", "arbitrarily"},
        {"sequential", "sequentially", "linear", "linearly", "serial", "serially"},
    ),
    "memory_storage": (
        {"heap", "free store", "dynamic memory"},
        {"stack", "call stack", "automatic storage"},
    ),
    "size_trend": (
        {"increase", "increasing", "grow", "growing", "expand", "expanding", "grows", "increases", "increment"},
        {"decrease", "decreasing", "shrink", "shrinking", "reduce", "reducing", "shrinks", "decreases", "decrement"},
    ),
    "allocation_action": (
        {"allocate", "allocating", "allocation", "create", "new"},
        {"deallocate", "deallocating", "deallocation", "destroy", "free", "delete"},
    ),
    "containment_scope": (
        {"inside", "in", "within"},
        {"outside", "without"},
    ),
}

# Recognized English light / support verbs in nominalized event constructions
LIGHT_VERBS: Set[str] = {
    "provide", "perform", "do", "make", "handle", "execute", "conduct",
    "carry", "support", "achieve", "allow", "enable", "offer", "involve",
    "cause", "give", "have", "serve", "act", "facilitate",
}

# Generic agents frequently used in active voice paraphrases of agentless passives
GENERIC_AGENTS: Set[str] = {
    "programmer", "developer", "user", "system", "compiler",
    "function", "program", "code", "we", "one", "person", "process",
    "operator", "computer", "application", "method", "operation",
}

# Prepositions and verbs indicating instrumental means
INSTRUMENTAL_PREPS: Set[str] = {"with", "by", "via", "through", "using"}
INSTRUMENTAL_VERBS: Set[str] = {"use", "utilize", "apply"}

# Preposition semantic equivalence classes (functional synonyms)
PREPOSITION_EQUIVALENCE_CLASSES: List[Set[str]] = [
    {"in", "within", "inside", "into"},
    {"using", "by", "via", "with", "through"},
    {"on", "upon", "in"},
    {"from", "out of", "off"},
    {"during", "at", "in"},
    {"to", "into", "toward", "towards"},
]


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
        matched_student_props: Optional[Sequence[RobustProposition]] = None,
        question: str = "",
        reference_answer: str = "",
        student_answer: str = "",
    ) -> CoreRecoveryBatchResult:
        """
        Process unmatched student propositions and recover valid core paraphrases.
        Also recovers unfulfilled reference concepts fulfilled by arguments of matched student propositions.
        """
        matched_ref_set: Set[int] = set(matched_reference_indices or set())
        recovered_results: List[CoreParaphraseRecoveryResult] = []
        remaining_unmatched: List[RobustProposition] = []
        provenance_list: List[Dict[str, Any]] = []

        unfulfilled_ref_indices = [
            i for i in range(len(reference_props)) if i not in matched_ref_set
        ]

        # 1. Global deterministic candidate evaluation across all unmatched student props
        # Candidate format: (score, r_idx, s_idx, reason, evidence)
        CandidateMatch = Tuple[float, int, int, str, Dict[str, Any]]
        candidates: List[CandidateMatch] = []
        best_candidate_for_student: Dict[int, Tuple[float, str, Dict[str, Any]]] = {}

        for s_idx, stu_prop in enumerate(unmatched_student_props):
            best_s_score = 0.0
            best_s_reason = "INSUFFICIENT_EVIDENCE"
            best_s_ev: Dict[str, Any] = {}

            for r_idx in unfulfilled_ref_indices:
                ref_prop = reference_props[r_idx]
                score, reason, evidence = self._evaluate_paraphrase_evidence(
                    stu_prop=stu_prop,
                    ref_prop=ref_prop,
                    question=question,
                )
                if score > best_s_score:
                    best_s_score = score
                    best_s_reason = reason
                    best_s_ev = evidence

                if score >= self.recovery_threshold:
                    candidates.append((score, r_idx, s_idx, reason, evidence))

            best_candidate_for_student[s_idx] = (best_s_score, best_s_reason, best_s_ev)

        # Sort candidates globally by score descending, breaking ties deterministically
        # Tie-breaker: (-score, r_idx, s_idx)
        candidates.sort(key=lambda c: (-c[0], c[1], c[2]))

        assigned_stu_indices: Set[int] = set()
        consumed_ref_indices: Set[int] = set()
        matched_pair_records: Dict[int, CoreParaphraseRecoveryResult] = {}

        for score, r_idx, s_idx, reason, evidence in candidates:
            if s_idx in assigned_stu_indices or r_idx in consumed_ref_indices:
                continue

            stu_prop = unmatched_student_props[s_idx]
            target_ref = reference_props[r_idx]

            rec_res = CoreParaphraseRecoveryResult(
                is_recovered=True,
                student_proposition=stu_prop,
                reference_proposition=target_ref,
                reference_index=r_idx,
                student_index=s_idx,
                reason=reason,
                confidence=score,
                evidence=evidence,
                status="CORE_PARAPHRASE_RECOVERED",
            )
            matched_pair_records[s_idx] = rec_res
            assigned_stu_indices.add(s_idx)
            consumed_ref_indices.add(r_idx)
            matched_ref_set.add(r_idx)
            if r_idx in unfulfilled_ref_indices:
                unfulfilled_ref_indices.remove(r_idx)

        # Build recovered_results and remaining_unmatched maintaining student index order
        for s_idx, stu_prop in enumerate(unmatched_student_props):
            if s_idx in matched_pair_records:
                rec_res = matched_pair_records[s_idx]
                recovered_results.append(rec_res)
                provenance_list.append(rec_res.to_dict())
            else:
                best_score, best_reason, best_ev = best_candidate_for_student.get(
                    s_idx, (0.0, "INSUFFICIENT_EVIDENCE", {})
                )
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

        # 2. Check if remaining unfulfilled references are fulfilled by arguments of matched student propositions
        all_matched_stu: List[RobustProposition] = list(matched_student_props or []) + [
            r.student_proposition for r in recovered_results
        ]
        if unfulfilled_ref_indices and all_matched_stu:
            arg_fulfilled = self.recover_argument_fulfilled_references(
                matched_student_props=all_matched_stu,
                reference_props=reference_props,
                matched_reference_indices=matched_ref_set,
            )
            for rec in arg_fulfilled:
                recovered_results.append(rec)
                provenance_list.append(rec.to_dict())
                if rec.reference_index in unfulfilled_ref_indices:
                    unfulfilled_ref_indices.remove(rec.reference_index)

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

        # 0. Polarity Guard: Conflicting polarities can NEVER be recovered as paraphrases
        if stu_prop.polarity != ref_prop.polarity:
            return (
                0.0,
                "POLARITY_MISMATCH",
                {
                    "stu_polarity": getattr(stu_prop.polarity, "value", str(stu_prop.polarity)),
                    "ref_polarity": getattr(ref_prop.polarity, "value", str(ref_prop.polarity)),
                    "reason": "Student and reference polarities conflict; cannot recover as a paraphrase.",
                },
            )

        # 1. Check for Converse Relational Equivalence (A < B <=> B > A, Above/Below)
        converse_score, converse_ev = self._check_converse_equivalence(stu_prop, ref_prop)
        if converse_score >= self.recovery_threshold:
            evidence.update(converse_ev)
            return (converse_score, "CONVERSE_EQUIVALENCE", evidence)

        # 1b. Check for Containment Converse Equivalence (Container contains Element <=> Element is in Container)
        contain_score, contain_ev = self._check_containment_converse_bridge(stu_prop, ref_prop)
        if contain_score >= self.recovery_threshold:
            evidence.update(contain_ev)
            return (contain_score, "CONTAINMENT_CONVERSE_BRIDGE", evidence)

        # 2. Check for Nominalization-Verbalization Alternation (e.g. 'provides storage of' <=> 'stores')
        nom_verb_score, nom_verb_ev = self._check_nominalization_verbalization_bridge(stu_prop, ref_prop)
        if nom_verb_score >= self.recovery_threshold:
            evidence.update(nom_verb_ev)
            return (nom_verb_score, "NOMINALIZATION_VERBALIZATION_BRIDGE", evidence)

        # 3. Check for Active-Passive Voice Alternation (e.g. 'programmer allocates memory' <=> 'memory is allocated')
        voice_score, voice_ev = self._check_active_passive_voice_alternation(stu_prop, ref_prop)
        if voice_score >= self.recovery_threshold:
            evidence.update(voice_ev)
            return (voice_score, "VOICE_ALTERNATION_BRIDGE", evidence)

        # 4. Check for Relational Fragment Fulfillment (prepositional roots, content words, noun-prep complements)
        if ref_prop.representation_type == PropositionType.RELATIONAL_FRAGMENT:
            frag_score, frag_ev = self._check_relational_fragment_fulfillment(stu_prop, ref_prop)
            if frag_score >= self.recovery_threshold:
                evidence.update(frag_ev)
                return (frag_score, "RELATIONAL_FRAGMENT_FULFILLMENT", evidence)

        # 4b. Check for Clausal-Nominal Bridge on Unanchored Predicates (e.g. 'deallocates memory')
        if ref_prop.subject is None or ref_prop.properties.get("is_unanchored"):
            bridge_score, bridge_ev = self._check_unanchored_predicate_bridge(stu_prop, ref_prop, question)
            if bridge_score >= self.recovery_threshold:
                evidence.update(bridge_ev)
                return (bridge_score, "UNANCHORED_PREDICATE_FULFILLMENT", evidence)

        # 5. Check for Coordinate Concept Fulfillment (e.g. reference 'concept includes X')
        if ref_prop.predicate_lemma == "include" and ref_prop.subject_lemma == "concept":
            coord_score, coord_ev = self._check_coordinate_concept_fulfillment(stu_prop, ref_prop)
            if coord_score >= self.recovery_threshold:
                evidence.update(coord_ev)
                return (coord_score, "COORDINATE_CONCEPT_FULFILLMENT", evidence)

        # 6. Check for Entity-Property Match (e.g. 'dynamic size', 'random access')
        if ref_prop.predicate == "has_property":
            prop_score, prop_ev = self._check_property_bridge(stu_prop, ref_prop)
            if prop_score >= self.recovery_threshold:
                evidence.update(prop_ev)
                return (prop_score, "ENTITY_PROPERTY_BRIDGE", evidence)

        # 7. Check for Copula-Adjective to Verb Alternation (e.g. 'is accessible' <=> 'can be accessed')
        copula_verb_score, copula_verb_ev = self._check_copula_adjective_verb_bridge(stu_prop, ref_prop)
        if copula_verb_score >= self.recovery_threshold:
            evidence.update(copula_verb_ev)
            return (copula_verb_score, "COPULA_ADJECTIVE_VERB_BRIDGE", evidence)

        # 8. General Clausal Slot Matching with Prepositional Support
        general_score, general_ev = self._check_slot_alignment(stu_prop, ref_prop)
        evidence.update(general_ev)
        if general_score >= self.recovery_threshold:
            return (general_score, "SLOT_ALIGNMENT_RECOVERY", evidence)

        return (general_score, "INSUFFICIENT_EVIDENCE", evidence)

    def _check_converse_equivalence(
        self, stu_prop: RobustProposition, ref_prop: RobustProposition
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Detect if student is converse of reference (e.g. parent > child vs child < parent,
        or Block A is above Block B vs Block B is below Block A).
        Strictly rejects non-converse argument reversals (e.g. A above B vs B above A).
        """
        p_stu = (stu_prop.predicate_lemma or "").lower()
        p_ref = (ref_prop.predicate_lemma or "").lower()

        s_stu = (stu_prop.subject_lemma or stu_prop.subject or "").lower().strip(" .?!,:;")
        s_ref = (ref_prop.subject_lemma or ref_prop.subject or "").lower().strip(" .?!,:;")

        # Extract prepositional arguments
        stu_prep_args = [
            (str(it[0]).strip().lower(), str(it[1]).strip().lower().strip(" .?!,:;"))
            for it in stu_prop.properties.get("prepositional_arguments", [])
            if isinstance(it, (list, tuple)) and len(it) >= 2
        ]
        ref_prep_args = [
            (str(it[0]).strip().lower(), str(it[1]).strip().lower().strip(" .?!,:;"))
            for it in ref_prop.properties.get("prepositional_arguments", [])
            if isinstance(it, (list, tuple)) and len(it) >= 2
        ]

        # 1. Prepositional converses (e.g., 'A is above B' <=> 'B is below A')
        # Only applies when the prepositions themselves express directional/locative relations in CONVERSE_PREDICATE_PAIRS.
        # Grammatical comparative markers like 'than' are handled by comparative object analysis below.
        if stu_prep_args and ref_prep_args:
            p_stu_prep, n_stu_prep = stu_prep_args[0]
            p_ref_prep, n_ref_prep = ref_prep_args[0]

            is_prep_converse_eligible = (
                p_stu_prep in CONVERSE_PREDICATE_PAIRS
                or p_ref_prep in CONVERSE_PREDICATE_PAIRS
            )
            if is_prep_converse_eligible:
                # Negative Contrast Check: Same directional preposition with swapped arguments
                # e.g., 'A is above B' vs 'B is above A'
                if p_stu_prep == p_ref_prep:
                    sim_fwd = self._compare_lemmas(s_stu, n_ref_prep)
                    sim_bwd = self._compare_lemmas(n_stu_prep, s_ref)
                    if sim_fwd >= 0.50 and sim_bwd >= 0.50:
                        return (0.0, {"reason": "NON_CONVERSE_ARGUMENT_REVERSAL"})

                is_converse_prep = (
                    CONVERSE_PREDICATE_PAIRS.get(p_stu_prep) == p_ref_prep
                    or CONVERSE_PREDICATE_PAIRS.get(p_ref_prep) == p_stu_prep
                )
                if is_converse_prep:
                    sim_fwd = self._compare_lemmas(s_stu, n_ref_prep)
                    sim_bwd = self._compare_lemmas(n_stu_prep, s_ref)
                    avg_sim = (sim_fwd + sim_bwd) / 2.0
                    if avg_sim >= 0.50:
                        conf = 0.85 * avg_sim + 0.15
                        return (
                            conf,
                            {
                                "converse_prepositions": (p_stu_prep, p_ref_prep),
                                "swapped_arg_similarity": round(avg_sim, 4),
                                "confidence": round(conf, 4),
                            },
                        )

        # 2. Check if predicates or comparative objects form a converse pair
        is_converse_pred = (
            CONVERSE_PREDICATE_PAIRS.get(p_stu) == p_ref
            or CONVERSE_PREDICATE_PAIRS.get(p_ref) == p_stu
        )

        obj_stu = (stu_prop.object_lemma or "").lower().strip(" .?!,:;")
        obj_ref = (ref_prop.object_lemma or "").lower().strip(" .?!,:;")
        is_converse_obj = (
            CONVERSE_PREDICATE_PAIRS.get(obj_stu) == obj_ref
            or CONVERSE_PREDICATE_PAIRS.get(obj_ref) == obj_stu
        )

        if not (is_converse_pred or is_converse_obj):
            # Check for non-converse comparative reversal: same comparative predicate with swapped arguments!
            # e.g., 'The stack is smaller than the queue' vs 'The queue is smaller than the stack'
            is_same_asym = (
                (obj_stu == obj_ref and obj_stu in CONVERSE_PREDICATE_PAIRS)
                or (p_stu == p_ref and p_stu in CONVERSE_PREDICATE_PAIRS)
            )
            if is_same_asym:
                target_stu = (stu_prop.properties.get("comparative_target_lemma") or obj_stu).lower().strip(" .?!,:;")
                target_ref = (ref_prop.properties.get("comparative_target_lemma") or obj_ref).lower().strip(" .?!,:;")
                sim_forward = self._compare_lemmas(s_stu, target_ref)
                sim_backward = self._compare_lemmas(target_stu, s_ref)
                avg_arg_sim = (sim_forward + sim_backward) / 2.0
                if avg_arg_sim >= 0.50:
                    return (0.0, {"reason": "NON_CONVERSE_ARGUMENT_REVERSAL"})
            return (0.0, {})

        # Extract comparative targets if copular
        target_stu = (stu_prop.properties.get("comparative_target_lemma") or obj_stu).lower().strip(" .?!,:;")
        target_ref = (ref_prop.properties.get("comparative_target_lemma") or obj_ref).lower().strip(" .?!,:;")

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

    def _check_containment_converse_bridge(
        self, stu_prop: RobustProposition, ref_prop: RobustProposition
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Bridge containment active verb to copula/locative preposition
        (e.g. 'The array contains elements' <=> 'Elements are in the array').
        Strictly rejects inverted roles (e.g. 'The array is in elements').
        """
        p_stu = (stu_prop.predicate_lemma or stu_prop.predicate or "").lower()
        p_ref = (ref_prop.predicate_lemma or ref_prop.predicate or "").lower()

        s_stu = (stu_prop.subject_lemma or stu_prop.subject or "").lower().strip(" .?!,:;")
        o_stu = (stu_prop.object_lemma or stu_prop.object or "").lower().strip(" .?!,:;")
        s_ref = (ref_prop.subject_lemma or ref_prop.subject or "").lower().strip(" .?!,:;")
        o_ref = (ref_prop.object_lemma or ref_prop.object or "").lower().strip(" .?!,:;")

        stu_prep_args = [
            (str(it[0]).strip().lower(), str(it[1]).strip().lower().strip(" .?!,:;"))
            for it in stu_prop.properties.get("prepositional_arguments", [])
            if isinstance(it, (list, tuple)) and len(it) >= 2
        ]
        ref_prep_args = [
            (str(it[0]).strip().lower(), str(it[1]).strip().lower().strip(" .?!,:;"))
            for it in ref_prop.properties.get("prepositional_arguments", [])
            if isinstance(it, (list, tuple)) and len(it) >= 2
        ]

        # Case 1: Ref has containment verb (Container contains Element), Stu has copula (Element is in Container)
        if p_ref in CONTAINMENT_VERBS and o_ref:
            ref_container = s_ref
            ref_element = o_ref
            for p, n in stu_prep_args:
                if p in LOCATIVE_PREPS:
                    stu_container = n
                    stu_element = s_stu
                    sim_c = self._compare_lemmas(stu_container, ref_container)
                    sim_e = self._compare_lemmas(stu_element, ref_element)
                    avg_sim = (sim_c + sim_e) / 2.0
                    if avg_sim >= 0.55:
                        conf = 0.85 * avg_sim + 0.15
                        return (
                            conf,
                            {
                                "bridge": "containment_converse",
                                "container_sim": round(sim_c, 4),
                                "element_sim": round(sim_e, 4),
                                "confidence": round(conf, 4),
                            },
                        )

        # Case 2: Stu has containment verb (Container contains Element), Ref has copula (Element is in Container)
        if p_stu in CONTAINMENT_VERBS and o_stu:
            stu_container = s_stu
            stu_element = o_stu
            for p, n in ref_prep_args:
                if p in LOCATIVE_PREPS:
                    ref_container = n
                    ref_element = s_ref
                    sim_c = self._compare_lemmas(stu_container, ref_container)
                    sim_e = self._compare_lemmas(stu_element, ref_element)
                    avg_sim = (sim_c + sim_e) / 2.0
                    if avg_sim >= 0.55:
                        conf = 0.85 * avg_sim + 0.15
                        return (
                            conf,
                            {
                                "bridge": "containment_converse",
                                "container_sim": round(sim_c, 4),
                                "element_sim": round(sim_e, 4),
                                "confidence": round(conf, 4),
                            },
                        )

        return (0.0, {})

    def _check_containment_inverted(
        self, stu_prop: RobustProposition, ref_prop: RobustProposition
    ) -> bool:
        """
        Detect if student and reference express an inverted containment relation
        (e.g., 'The array contains elements' vs 'The array is in elements',
        or 'Elements are in the array' vs 'Elements contain the array').
        """
        p_stu = (stu_prop.predicate_lemma or stu_prop.predicate or "").lower()
        p_ref = (ref_prop.predicate_lemma or ref_prop.predicate or "").lower()

        s_stu = (stu_prop.subject_lemma or stu_prop.subject or "").lower().strip(" .?!,:;")
        o_stu = (stu_prop.object_lemma or stu_prop.object or "").lower().strip(" .?!,:;")
        s_ref = (ref_prop.subject_lemma or ref_prop.subject or "").lower().strip(" .?!,:;")
        o_ref = (ref_prop.object_lemma or ref_prop.object or "").lower().strip(" .?!,:;")

        stu_prep_args = [
            (str(it[0]).strip().lower(), str(it[1]).strip().lower().strip(" .?!,:;"))
            for it in stu_prop.properties.get("prepositional_arguments", [])
            if isinstance(it, (list, tuple)) and len(it) >= 2
        ]
        ref_prep_args = [
            (str(it[0]).strip().lower(), str(it[1]).strip().lower().strip(" .?!,:;"))
            for it in ref_prop.properties.get("prepositional_arguments", [])
            if isinstance(it, (list, tuple)) and len(it) >= 2
        ]

        # Case 1: Ref has containment verb, Stu has copula with locative prep
        if p_ref in CONTAINMENT_VERBS and o_ref:
            ref_container = s_ref
            ref_element = o_ref
            for p, n in stu_prep_args:
                if p in LOCATIVE_PREPS:
                    stu_container = n
                    stu_element = s_stu
                    sim_inv1 = self._compare_lemmas(stu_element, ref_container)
                    sim_inv2 = self._compare_lemmas(stu_container, ref_element)
                    if sim_inv1 >= 0.60 and sim_inv2 >= 0.60:
                        return True

        # Case 2: Stu has containment verb, Ref has copula with locative prep
        if p_stu in CONTAINMENT_VERBS and o_stu:
            stu_container = s_stu
            stu_element = o_stu
            for p, n in ref_prep_args:
                if p in LOCATIVE_PREPS:
                    ref_container = n
                    ref_element = s_ref
                    sim_inv1 = self._compare_lemmas(stu_container, ref_element)
                    sim_inv2 = self._compare_lemmas(stu_element, ref_container)
                    if sim_inv1 >= 0.60 and sim_inv2 >= 0.60:
                        return True

        return False

    def _check_unanchored_predicate_bridge(
        self,
        stu_prop: RobustProposition,
        ref_prop: RobustProposition,
        question: str,
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Match clausal student proposition to unanchored reference predicate (e.g. 'deallocates memory', 'using delete').
        """
        p_sim = self._compare_lemmas(stu_prop.predicate_lemma, ref_prop.predicate_lemma)
        o_sim = self._compare_lemmas(stu_prop.object_lemma, ref_prop.object_lemma)

        # 1. If predicate and object match with high similarity
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

        # 2. Instrumental check: ref is (None, using, X), stu has prep (with/using, X)
        is_ref_instrumental = (
            (ref_prop.predicate_lemma in INSTRUMENTAL_VERBS or ref_prop.predicate_lemma in INSTRUMENTAL_PREPS)
            and bool(ref_prop.object_lemma)
        )
        if is_ref_instrumental:
            stu_prep_args = stu_prop.properties.get("prepositional_arguments", [])
            for item in stu_prep_args:
                if isinstance(item, (list, tuple)) and len(item) >= 2:
                    p, noun = str(item[0]).lower(), str(item[1]).lower()
                    if p in INSTRUMENTAL_PREPS:
                        n_sim = self._compare_lemmas(noun, ref_prop.object_lemma)
                        if n_sim >= 0.70:
                            score = 0.85 * n_sim + 0.15
                            return (
                                score,
                                {
                                    "instrumental_fulfillment": True,
                                    "ref_target": ref_prop.object_lemma,
                                    "stu_prep": p,
                                    "stu_noun": noun,
                                    "noun_similarity": round(n_sim, 4),
                                },
                            )

        # 3. Check prepositional arguments
        ref_prep_args = ref_prop.properties.get("prepositional_arguments", [])
        stu_prep_args = stu_prop.properties.get("prepositional_arguments", [])
        prep_sim = 0.0
        if ref_prep_args and stu_prep_args:
            prep_sim = self._evaluate_prep_args_similarity(stu_prep_args, ref_prep_args)

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

    def _check_relational_fragment_fulfillment(
        self, stu_prop: RobustProposition, ref_prop: RobustProposition
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Match student assertion to non-sentential reference relational fragments
        (prepositional roots, content words, noun with prepositional complement).
        """
        frag_type = ref_prop.properties.get("fragment_type")

        # Fragment Type A: Prepositional root (e.g. ref: (None, 'On', 'stack'))
        if frag_type == "prepositional_root":
            ref_prep = (ref_prop.predicate_lemma or ref_prop.predicate or "").lower()
            ref_target = (ref_prop.object_lemma or ref_prop.object or "").lower().strip(" .?!,:;")
            if not ref_target:
                return (0.0, {})

            # 1. Match against student prepositional arguments (e.g. 'Local variables are stored on the stack')
            stu_prep_args = stu_prop.properties.get("prepositional_arguments", [])
            for item in stu_prep_args:
                if isinstance(item, (list, tuple)) and len(item) >= 2:
                    p, noun = str(item[0]).lower(), str(item[1]).lower().strip(" .?!,:;")
                    n_sim = self._compare_lemmas(noun, ref_target)
                    p_comp = self._are_preps_equivalent(p, ref_prep)
                    if n_sim >= 0.70 and p_comp:
                        score = 0.85 * n_sim + 0.15
                        return (
                            score,
                            {
                                "fragment_type": "prepositional_root",
                                "matched_via": "prepositional_argument",
                                "ref_prep": ref_prep,
                                "ref_target": ref_target,
                                "stu_prep": p,
                                "stu_noun": noun,
                                "target_similarity": round(n_sim, 4),
                            },
                        )

            # 2. Match against student's own prepositional root predicate & object
            p_stu = (stu_prop.predicate_lemma or stu_prop.predicate or "").lower()
            o_stu = (stu_prop.object_lemma or stu_prop.object or "").lower().strip(" .?!,:;")
            p_comp = self._are_preps_equivalent(p_stu, ref_prep)
            n_sim = self._compare_lemmas(o_stu, ref_target)
            if p_comp and n_sim >= 0.70:
                score = 0.85 * n_sim + 0.15
                return (
                    score,
                    {
                        "fragment_type": "prepositional_root",
                        "matched_via": "prepositional_root_direct",
                        "ref_prep": ref_prep,
                        "ref_target": ref_target,
                        "target_similarity": round(n_sim, 4),
                    },
                )

            # 3. Match against student prepositional phrase tokens or source text
            prep_tokens = set(ref_prop.properties.get("prep_phrase_lemmas", [ref_prep, ref_target]))
            stu_tokens = set(stu_prop.properties.get("prep_phrase_lemmas", []))
            if ref_target in (stu_prop.source_text or "").lower():
                if prep_tokens and prep_tokens.intersection(stu_tokens):
                    return (
                        0.85,
                        {
                            "fragment_type": "prepositional_root",
                            "matched_via": "prep_phrase_overlap",
                            "ref_target": ref_target,
                        },
                    )

        # Fragment Type B: Content word (e.g. ref: (None, 'stack', None))
        elif frag_type == "content_word":
            ref_target = (ref_prop.predicate_lemma or ref_prop.predicate or ref_prop.object_lemma or "").lower().strip(" .?!,:;")
            if not ref_target:
                return (0.0, {})

            candidates = [
                (stu_prop.object_lemma or "").lower(),
                (stu_prop.subject_lemma or "").lower(),
                (stu_prop.predicate_lemma or "").lower(),
                str(stu_prop.properties.get("property", "")).lower(),
                str(stu_prop.properties.get("entity", "")).lower(),
            ]
            candidates.extend([m.lower() for m in stu_prop.properties.get("subject_modifiers", [])])
            candidates.extend([m.lower() for m in stu_prop.properties.get("object_modifiers", [])])
            candidates = [c for c in candidates if c]

            best_sim = 0.0
            best_cand = ""
            for cand in candidates:
                sim = self._compare_lemmas(cand, ref_target)
                if sim > best_sim:
                    best_sim = sim
                    best_cand = cand

            if best_sim >= 0.70:
                score = 0.85 * best_sim + 0.15
                return (
                    score,
                    {
                        "fragment_type": "content_word",
                        "matched_candidate": best_cand,
                        "ref_target": ref_target,
                        "similarity": round(best_sim, 4),
                    },
                )

        # Fragment Type C: Noun with Prepositional Complement (e.g. 'root of tree')
        elif frag_type == "noun_prep_complement":
            ref_head = (ref_prop.subject_lemma or ref_prop.subject or "").lower().strip(" .?!,:;")
            ref_prep = (ref_prop.predicate_lemma or ref_prop.predicate or "").lower()
            ref_obj = (ref_prop.object_lemma or ref_prop.object or "").lower().strip(" .?!,:;")

            s_sim = max(
                self._compare_lemmas((stu_prop.subject_lemma or "").lower(), ref_head),
                self._compare_lemmas((stu_prop.object_lemma or "").lower(), ref_head),
            )
            stu_prep_args = stu_prop.properties.get("prepositional_arguments", [])
            prep_sim = 0.0
            for item in stu_prep_args:
                if isinstance(item, (list, tuple)) and len(item) >= 2:
                    p, noun = str(item[0]).lower(), str(item[1]).lower().strip(" .?!,:;")
                    if self._are_preps_equivalent(p, ref_prep):
                        n_sim = self._compare_lemmas(noun, ref_obj)
                        if n_sim > prep_sim:
                            prep_sim = n_sim

            if prep_sim < 0.60:
                s_tree = [w.lower() for w in stu_prop.properties.get("subject_tree_lemmas", [])]
                o_tree = [w.lower() for w in stu_prop.properties.get("object_tree_lemmas", [])]
                combined_tree = s_tree + o_tree
                if ref_prep in combined_tree:
                    best_obj = max([self._compare_lemmas(w, ref_obj) for w in combined_tree] or [0.0])
                    if best_obj >= 0.70:
                        prep_sim = best_obj

            if s_sim >= 0.60 and prep_sim >= 0.60:
                score = 0.50 * s_sim + 0.50 * prep_sim
                return (
                    score,
                    {
                        "fragment_type": "noun_prep_complement",
                        "head_similarity": round(s_sim, 4),
                        "prep_similarity": round(prep_sim, 4),
                    },
                )

        return (0.0, {})

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

    def _check_copula_adjective_verb_bridge(
        self, stu_prop: RobustProposition, ref_prop: RobustProposition
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Match copula-adjective assertion to verbal assertion (e.g. 'is accessible' <=> 'can be accessed').
        """
        is_ref_copular = (
            ref_prop.properties.get("is_copular_adjective")
            or ref_prop.predicate_lemma in ("be", "is", "have")
        ) and bool(ref_prop.object_lemma)

        is_stu_copular = (
            stu_prop.properties.get("is_copular_adjective")
            or stu_prop.predicate_lemma in ("be", "is", "have")
        ) and bool(stu_prop.object_lemma)

        if is_ref_copular and not is_stu_copular:
            subj_sim = self._compare_lemmas(stu_prop.subject_lemma, ref_prop.subject_lemma, pos="NOUN")
            pred_adj_sim = self._compare_lemmas(stu_prop.predicate_lemma, ref_prop.object_lemma)
            copula_target = ref_prop.object_lemma
            verbal_target = stu_prop.predicate_lemma
        elif is_stu_copular and not is_ref_copular:
            subj_sim = self._compare_lemmas(stu_prop.subject_lemma, ref_prop.subject_lemma, pos="NOUN")
            pred_adj_sim = self._compare_lemmas(ref_prop.predicate_lemma, stu_prop.object_lemma)
            copula_target = stu_prop.object_lemma
            verbal_target = ref_prop.predicate_lemma
        else:
            return (0.0, {})

        if pred_adj_sim < 0.60:
            return (0.0, {})

        ref_prep_lemmas = set(
            ref_prop.properties.get("object_tree_lemmas", [])
            + [item[1].lower() for item in ref_prop.properties.get("prepositional_arguments", []) if len(item) == 2]
        )
        stu_prep_lemmas = set(
            stu_prop.properties.get("prep_phrase_lemmas", [])
            + [item[1].lower() for item in stu_prop.properties.get("prepositional_arguments", []) if len(item) == 2]
        )

        stop_words = {"a", "an", "the", "be", "or", "and", "it", "that", "which"}
        content_ref = {w for w in ref_prep_lemmas if w not in stop_words}
        content_stu = {w for w in stu_prep_lemmas if w not in stop_words}

        prep_sim = 0.0
        if content_ref and content_stu:
            overlap = 0.0
            for w1 in content_ref:
                best_w_sim = max([self._compare_lemmas(w1, w2) for w2 in content_stu] or [0.0])
                if best_w_sim >= 0.70:
                    overlap += 1.0
            prep_sim = overlap / max(1, len(content_ref))

        if prep_sim > 0.0:
            combined = 0.35 * subj_sim + 0.45 * pred_adj_sim + 0.20 * prep_sim
        else:
            combined = 0.45 * subj_sim + 0.55 * pred_adj_sim

        if combined >= self.recovery_threshold:
            return (
                combined,
                {
                    "subject_similarity": round(subj_sim, 4),
                    "pred_adjective_similarity": round(pred_adj_sim, 4),
                    "copula_adjective": copula_target,
                    "verbal_predicate": verbal_target,
                    "prep_similarity": round(prep_sim, 4),
                },
            )

        return (combined, {})

    def _check_nominalization_verbalization_bridge(
        self, stu_prop: RobustProposition, ref_prop: RobustProposition
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Bridge light-verb + nominalization to verbal expression
        (e.g., 'provides storage of elements' <=> 'stores elements').
        """
        p_stu_pred = (stu_prop.predicate_lemma or "").lower()
        p_ref_pred = (ref_prop.predicate_lemma or "").lower()
        stu_obj = (stu_prop.object_lemma or "").lower()
        ref_obj = (ref_prop.object_lemma or "").lower()

        is_stu_light = p_stu_pred in LIGHT_VERBS and bool(stu_obj)
        is_ref_light = p_ref_pred in LIGHT_VERBS and bool(ref_obj)

        if is_stu_light and not is_ref_light:
            deriv_sim = self._check_derivational_relation(stu_obj, p_ref_pred)
            if deriv_sim < 0.70:
                return (0.0, {})

            subj_sim = self._compare_lemmas(stu_prop.subject_lemma, ref_prop.subject_lemma, pos="NOUN")

            # Find semantic patient in student prep args or tree lemmas
            patient_candidates = []
            for item in stu_prop.properties.get("prepositional_arguments", []):
                if isinstance(item, (list, tuple)) and len(item) >= 2:
                    patient_candidates.append(str(item[1]).lower())
            patient_candidates.extend(stu_prop.properties.get("object_tree_lemmas", []))
            patient_candidates.extend(stu_prop.properties.get("prep_phrase_lemmas", []))
            patient_candidates.extend(stu_prop.properties.get("object_modifiers", []))

            if ref_obj:
                patient_sim = max([self._compare_lemmas(cand, ref_obj) for cand in patient_candidates] or [0.0])
            else:
                patient_sim = 0.85

            if patient_sim < 0.50 and ref_obj:
                return (0.0, {})

            combined = 0.35 * subj_sim + 0.40 * deriv_sim + 0.25 * patient_sim
            if combined >= self.recovery_threshold:
                return (
                    combined,
                    {
                        "nominal_source": stu_obj,
                        "verbal_target": p_ref_pred,
                        "derivational_similarity": round(deriv_sim, 4),
                        "subject_similarity": round(subj_sim, 4),
                        "patient_similarity": round(patient_sim, 4),
                    },
                )

        elif is_ref_light and not is_stu_light:
            deriv_sim = self._check_derivational_relation(ref_obj, p_stu_pred)
            if deriv_sim < 0.70:
                return (0.0, {})

            subj_sim = self._compare_lemmas(stu_prop.subject_lemma, ref_prop.subject_lemma, pos="NOUN")

            patient_candidates = []
            for item in ref_prop.properties.get("prepositional_arguments", []):
                if isinstance(item, (list, tuple)) and len(item) >= 2:
                    patient_candidates.append(str(item[1]).lower())
            patient_candidates.extend(ref_prop.properties.get("object_tree_lemmas", []))
            patient_candidates.extend(ref_prop.properties.get("prep_phrase_lemmas", []))
            patient_candidates.extend(ref_prop.properties.get("object_modifiers", []))

            if stu_obj:
                patient_sim = max([self._compare_lemmas(cand, stu_obj) for cand in patient_candidates] or [0.0])
            else:
                patient_sim = 0.85

            if patient_sim < 0.50 and stu_obj:
                return (0.0, {})

            combined = 0.35 * subj_sim + 0.40 * deriv_sim + 0.25 * patient_sim
            if combined >= self.recovery_threshold:
                return (
                    combined,
                    {
                        "nominal_source": ref_obj,
                        "verbal_target": p_stu_pred,
                        "derivational_similarity": round(deriv_sim, 4),
                        "subject_similarity": round(subj_sim, 4),
                        "patient_similarity": round(patient_sim, 4),
                    },
                )

        return (0.0, {})

    def _check_active_passive_voice_alternation(
        self, stu_prop: RobustProposition, ref_prop: RobustProposition
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Bridge active and passive voice diathesis alternations
        (e.g., 'programmer allocates dynamic memory on heap' <=> 'dynamic memory is allocated on heap').
        """
        # Direction 1: Reference is Passive (or agentless), Student is Active
        ref_is_agentless = ref_prop.object_lemma is None
        stu_is_transitive = stu_prop.object_lemma is not None

        if ref_is_agentless and stu_is_transitive:
            patient_sim = self._compare_lemmas(stu_prop.object_lemma, ref_prop.subject_lemma, pos="NOUN")
            if patient_sim < 0.60:
                return (0.0, {})

            pred_sim = self._compare_lemmas(stu_prop.predicate_lemma, ref_prop.predicate_lemma, pos="VERB")
            if pred_sim < 0.60:
                return (0.0, {})

            stu_subj = (stu_prop.subject_lemma or "").lower()
            if stu_subj in GENERIC_AGENTS:
                agent_sim = 0.85
            else:
                by_target = self._find_prep_arg(ref_prop, "by")
                if by_target:
                    agent_sim = self._compare_lemmas(stu_subj, by_target)
                else:
                    agent_sim = 0.70

            stu_prep = stu_prop.properties.get("prepositional_arguments", [])
            ref_prep = ref_prop.properties.get("prepositional_arguments", [])
            if stu_prep and ref_prep:
                prep_sim = self._evaluate_prep_args_similarity(stu_prep, ref_prep)
                combined = 0.35 * pred_sim + 0.35 * patient_sim + 0.15 * agent_sim + 0.15 * prep_sim
            else:
                combined = 0.45 * pred_sim + 0.40 * patient_sim + 0.15 * agent_sim

            if combined >= self.recovery_threshold:
                return (
                    combined,
                    {
                        "predicate_similarity": round(pred_sim, 4),
                        "patient_similarity": round(patient_sim, 4),
                        "agent": stu_subj,
                        "is_generic_agent": stu_subj in GENERIC_AGENTS,
                        "voice_direction": "active_student_passive_ref",
                    },
                )

        # Direction 2: Reference is Active, Student is Passive (or agentless)
        stu_is_agentless = stu_prop.object_lemma is None
        ref_is_transitive = ref_prop.object_lemma is not None

        if stu_is_agentless and ref_is_transitive:
            patient_sim = self._compare_lemmas(stu_prop.subject_lemma, ref_prop.object_lemma, pos="NOUN")
            if patient_sim < 0.60:
                return (0.0, {})

            pred_sim = self._compare_lemmas(stu_prop.predicate_lemma, ref_prop.predicate_lemma, pos="VERB")
            if pred_sim < 0.60:
                return (0.0, {})

            ref_subj = (ref_prop.subject_lemma or "").lower()
            if ref_subj in GENERIC_AGENTS:
                agent_sim = 0.85
            else:
                by_target = self._find_prep_arg(stu_prop, "by")
                if by_target:
                    agent_sim = self._compare_lemmas(ref_subj, by_target)
                else:
                    agent_sim = 0.70

            stu_prep = stu_prop.properties.get("prepositional_arguments", [])
            ref_prep = ref_prop.properties.get("prepositional_arguments", [])
            if stu_prep and ref_prep:
                prep_sim = self._evaluate_prep_args_similarity(stu_prep, ref_prep)
                combined = 0.35 * pred_sim + 0.35 * patient_sim + 0.15 * agent_sim + 0.15 * prep_sim
            else:
                combined = 0.45 * pred_sim + 0.40 * patient_sim + 0.15 * agent_sim

            if combined >= self.recovery_threshold:
                return (
                    combined,
                    {
                        "predicate_similarity": round(pred_sim, 4),
                        "patient_similarity": round(patient_sim, 4),
                        "agent": ref_subj,
                        "is_generic_agent": ref_subj in GENERIC_AGENTS,
                        "voice_direction": "passive_student_active_ref",
                    },
                )

        return (0.0, {})

    def _check_derivational_relation(self, w1: Optional[str], w2: Optional[str]) -> float:
        """
        Check if w1 and w2 are derivationally related via WordNet
        (e.g., allocate <=> allocation, store <=> storage, remove <=> removal).
        """
        if not w1 or not w2:
            return 0.0
        w1_clean = w1.strip().lower()
        w2_clean = w2.strip().lower()
        if w1_clean == w2_clean:
            return 1.0

        synsets_1 = wn.synsets(w1_clean)
        synsets_2 = wn.synsets(w2_clean)

        for s1 in synsets_1:
            for lemma1 in s1.lemmas():
                for drf in lemma1.derivationally_related_forms():
                    if drf.name().lower() == w2_clean:
                        return 0.90
                    if any(drf.synset() == s2 for s2 in synsets_2):
                        return 0.85

        for s2 in synsets_2:
            for lemma2 in s2.lemmas():
                for drf in lemma2.derivationally_related_forms():
                    if drf.name().lower() == w1_clean:
                        return 0.90
                    if any(drf.synset() == s1 for s1 in synsets_1):
                        return 0.85

        # Morphological suffix heuristic fallback
        root1 = self._stem_nominalization(w1_clean)
        root2 = self._stem_nominalization(w2_clean)
        if root1 and (root1 == w2_clean or root1 == root2):
            return 0.80
        if root2 and (root2 == w1_clean or root2 == root1):
            return 0.80

        return 0.0

    @staticmethod
    def _stem_nominalization(word: str) -> Optional[str]:
        """Simple morphological suffix reduction for English nominalizations."""
        w = word.strip().lower()
        suffixes = [
            ("ation", "e"),
            ("ition", "e"),
            ("tion", "t"),
            ("sion", "d"),
            ("ment", ""),
            ("ance", "e"),
            ("ence", "e"),
            ("age", ""),
            ("al", "e"),
            ("al", ""),
        ]
        for suf, repl in suffixes:
            if w.endswith(suf) and len(w) > len(suf) + 2:
                return w[:-len(suf)] + repl
        return None

    def _are_preps_equivalent(self, p1: str, p2: str) -> bool:
        """Check if two prepositions are identical or belong to the same equivalence class."""
        if not p1 or not p2:
            return False
        p1_clean = p1.strip().lower()
        p2_clean = p2.strip().lower()
        if p1_clean == p2_clean:
            return True
        for eq_class in PREPOSITION_EQUIVALENCE_CLASSES:
            if p1_clean in eq_class and p2_clean in eq_class:
                return True
        return False

    def _evaluate_prep_args_similarity(
        self,
        prep_args_1: Sequence[Any],
        prep_args_2: Sequence[Any],
    ) -> float:
        """
        Compare two lists of prepositional arguments [(prep, lemma), ...]
        incorporating functional preposition equivalence and lemma matching.
        """
        if not prep_args_1 or not prep_args_2:
            return 0.0

        norm_1: List[Tuple[str, str]] = []
        for item in prep_args_1:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                norm_1.append((str(item[0]).lower(), str(item[1]).lower()))

        norm_2: List[Tuple[str, str]] = []
        for item in prep_args_2:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                norm_2.append((str(item[0]).lower(), str(item[1]).lower()))

        if not norm_1 or not norm_2:
            return 0.0

        total_sim = 0.0
        bisection_set = {"half", "halves", "two"}
        for p1, arg1 in norm_1:
            best_match = 0.0
            for p2, arg2 in norm_2:
                if self._are_preps_equivalent(p1, p2):
                    if (
                        p1 in {"in", "into"}
                        and p2 in {"in", "into"}
                        and arg1 in bisection_set
                        and arg2 in bisection_set
                    ):
                        sim = 1.0
                    else:
                        sim = self._compare_lemmas(arg1, arg2)
                    if sim > best_match:
                        best_match = sim
            total_sim += best_match

        return total_sim / max(len(norm_1), 1)

    def _find_prep_arg(self, prop: RobustProposition, target_prep: str) -> Optional[str]:
        """Find the argument noun corresponding to a target preposition."""
        prep_args = prop.properties.get("prepositional_arguments", [])
        for item in prep_args:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                prep, noun = str(item[0]).lower(), str(item[1]).lower()
                if prep == target_prep or self._are_preps_equivalent(prep, target_prep):
                    return noun
        return None

    def recover_argument_fulfilled_references(
        self,
        matched_student_props: Sequence[RobustProposition],
        reference_props: Sequence[RobustProposition],
        matched_reference_indices: Set[int],
    ) -> List[CoreParaphraseRecoveryResult]:
        """
        Check if any remaining unfulfilled reference propositions (such as instrumental
        phrases or prepositional fragments) are fulfilled by arguments or modifiers
        of already-matched student propositions.
        Tracks used prepositional arguments to prevent argument double-dipping.
        """
        recovered: List[CoreParaphraseRecoveryResult] = []
        unfulfilled = [i for i in range(len(reference_props)) if i not in matched_reference_indices]
        used_stu_prep_args: Set[Tuple[int, int]] = set()

        for r_idx in unfulfilled:
            ref_p = reference_props[r_idx]
            ref_pred = (ref_p.predicate_lemma or ref_p.predicate or "").lower()
            ref_obj = (ref_p.object_lemma or ref_p.object or "").lower()

            for s_idx, stu_p in enumerate(matched_student_props):
                # 1. Instrumental check: ref is "using X", student has "with X" or "using X" in prep_args
                is_ref_instrumental = (
                    ref_pred in INSTRUMENTAL_VERBS or ref_pred in INSTRUMENTAL_PREPS
                )
                stu_prep_args = stu_p.properties.get("prepositional_arguments", [])

                if is_ref_instrumental and ref_obj and stu_prep_args:
                    for arg_idx, item in enumerate(stu_prep_args):
                        if (s_idx, arg_idx) in used_stu_prep_args:
                            continue
                        if isinstance(item, (list, tuple)) and len(item) >= 2:
                            prep, noun = str(item[0]).lower(), str(item[1]).lower()
                            if prep in INSTRUMENTAL_PREPS:
                                n_sim = self._compare_lemmas(noun, ref_obj)
                                if n_sim >= 0.70:
                                    conf = 0.85 * n_sim + 0.15
                                    res = CoreParaphraseRecoveryResult(
                                        is_recovered=True,
                                        student_proposition=stu_p,
                                        reference_proposition=ref_p,
                                        reference_index=r_idx,
                                        student_index=s_idx,
                                        reason="INSTRUMENTAL_ARGUMENT_FULFILLMENT",
                                        confidence=conf,
                                        evidence={
                                            "instrumental_prep": prep,
                                            "instrumental_noun": noun,
                                            "ref_target": ref_obj,
                                            "noun_similarity": round(n_sim, 4),
                                        },
                                        status="CORE_PARAPHRASE_RECOVERED",
                                    )
                                    recovered.append(res)
                                    matched_reference_indices.add(r_idx)
                                    used_stu_prep_args.add((s_idx, arg_idx))
                                    break
                    if r_idx in matched_reference_indices:
                        break

                # 2. Prepositional fragment / argument fulfillment
                if (
                    ref_p.representation_type != PropositionType.TRIPLE
                    or ref_p.subject is None
                    or ref_p.properties.get("is_unanchored")
                ):
                    if stu_prep_args and ref_obj:
                        for arg_idx, item in enumerate(stu_prep_args):
                            if (s_idx, arg_idx) in used_stu_prep_args:
                                continue
                            if isinstance(item, (list, tuple)) and len(item) >= 2:
                                prep, noun = str(item[0]).lower(), str(item[1]).lower()
                                if self._are_preps_equivalent(prep, ref_pred):
                                    n_sim = self._compare_lemmas(noun, ref_obj)
                                    if n_sim >= 0.70:
                                        conf = 0.80 * n_sim + 0.20
                                        res = CoreParaphraseRecoveryResult(
                                            is_recovered=True,
                                            student_proposition=stu_p,
                                            reference_proposition=ref_p,
                                            reference_index=r_idx,
                                            student_index=s_idx,
                                            reason="PREPOSITIONAL_ARGUMENT_FULFILLMENT",
                                            confidence=conf,
                                            evidence={
                                                "student_prep": prep,
                                                "student_noun": noun,
                                                "ref_prep": ref_pred,
                                                "ref_target": ref_obj,
                                                "noun_similarity": round(n_sim, 4),
                                            },
                                            status="CORE_PARAPHRASE_RECOVERED",
                                        )
                                        recovered.append(res)
                                        matched_reference_indices.add(r_idx)
                                        used_stu_prep_args.add((s_idx, arg_idx))
                                        break
                        if r_idx in matched_reference_indices:
                            break

        return recovered

    @staticmethod
    def are_entity_qualifiers_incompatible(
        mods1: Optional[Sequence[str]], mods2: Optional[Sequence[str]]
    ) -> bool:
        """
        Check if two modifier collections contain mutually exclusive entity qualifiers
        (e.g., 'primary' vs 'foreign', 'local' vs 'global', 'static' vs 'dynamic', 'stack' vs 'queue').
        """
        if not mods1 or not mods2:
            return False
        s1 = set()
        for m in mods1:
            if m:
                s1.update(str(m).lower().strip().split())
        s2 = set()
        for m in mods2:
            if m:
                s2.update(str(m).lower().strip().split())
        for set_a, set_b in INCOMPATIBLE_ENTITY_QUALIFIERS:
            if (s1.intersection(set_a) and s2.intersection(set_b)) or (
                s1.intersection(set_b) and s2.intersection(set_a)
            ):
                return True
        return False

    @staticmethod
    def are_property_values_incompatible(
        mods1: Optional[Sequence[str]], mods2: Optional[Sequence[str]]
    ) -> bool:
        """
        Check if two modifier/lemma collections contain mutually exclusive property values
        (e.g., 'unique' vs 'duplicate', 'fixed' vs 'variable').
        """
        if not mods1 or not mods2:
            return False
        s1 = set()
        for m in mods1:
            if m:
                s1.update(str(m).lower().strip().split())
        s2 = set()
        for m in mods2:
            if m:
                s2.update(str(m).lower().strip().split())
        for prop_name, (set_a, set_b) in INCOMPATIBLE_PROPERTY_VALUE_SETS.items():
            if (s1.intersection(set_a) and s2.intersection(set_b)) or (
                s1.intersection(set_b) and s2.intersection(set_a)
            ):
                return True
        return False

    def _check_prepositional_contradiction(
        self,
        stu_prop: RobustProposition,
        ref_prop: RobustProposition,
    ) -> bool:
        """
        Detect whether student and reference prepositional arguments express
        a genuine, mutually exclusive contradiction.

        Enforces the epistemic principle:
        Low similarity, missing arguments, or different prepositions alone
        must never establish a contradiction. A contradiction requires positive
        evidence of mutually exclusive values or antonymous spatial/directional clash.
        """
        ref_prep_args = [
            (str(it[0]).strip().lower(), str(it[1]).strip().lower().strip(" .?!,:;"))
            for it in ref_prop.properties.get("prepositional_arguments", [])
            if isinstance(it, (list, tuple)) and len(it) >= 2
        ]
        stu_prep_args = [
            (str(it[0]).strip().lower(), str(it[1]).strip().lower().strip(" .?!,:;"))
            for it in stu_prop.properties.get("prepositional_arguments", [])
            if isinstance(it, (list, tuple)) and len(it) >= 2
        ]

        if not ref_prep_args or not stu_prep_args:
            return False

        for p_ref, noun_ref in ref_prep_args:
            for p_stu, noun_stu in stu_prep_args:
                # Case 1: Equivalent or compatible prepositions with mutually exclusive argument nouns
                # e.g., "stored on the stack" vs "stored on the heap" (p='on', 'stack' vs 'heap')
                # or "passed by value" vs "passed by reference" (p='by', 'value' vs 'reference')
                # or "accessed in random order" vs "accessed in sequential order" (p='in', 'random' vs 'sequential')
                # or "adds an element to the stack" vs "adds an element to the queue" (p='to', 'stack' vs 'queue')
                if self._are_preps_equivalent(p_ref, p_stu) or p_ref == p_stu:
                    if (
                        self.are_property_values_incompatible([noun_ref], [noun_stu])
                        or self.are_entity_qualifiers_incompatible([noun_ref], [noun_stu])
                    ):
                        return True

                # Case 2: Mutually exclusive prepositions targeting the same entity
                # e.g., "stored above the threshold" vs "stored below the threshold"
                # ('above' vs 'below' with same noun 'threshold')
                # or "executed before main" vs "executed after main" ('before' vs 'after' with noun 'main')
                if self.are_property_values_incompatible([p_ref], [p_stu]) or (CONVERSE_PREDICATE_PAIRS.get(p_ref) == p_stu):
                    noun_sim = self._compare_lemmas(noun_ref, noun_stu)
                    if noun_sim >= 0.55:
                        return True

        return False

    def _check_slot_alignment(
        self, stu_prop: RobustProposition, ref_prop: RobustProposition
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Evaluate standard subject-predicate-object slot similarity with prepositional support.
        """
        s_sim = self._compare_lemmas(stu_prop.subject_lemma, ref_prop.subject_lemma, pos="NOUN")
        p_sim = self._compare_lemmas(stu_prop.predicate_lemma, ref_prop.predicate_lemma, pos="VERB")

        # Entity Qualifier Incompatibility Guard:
        ref_smods = ref_prop.properties.get("subject_modifiers", [])
        stu_smods = stu_prop.properties.get("subject_modifiers", [])
        if self.are_entity_qualifiers_incompatible(ref_smods, stu_smods):
            return (
                0.0,
                {
                    "subject_similarity": round(s_sim, 4),
                    "predicate_similarity": round(p_sim, 4),
                    "reason": "ENTITY_QUALIFIER_INCOMPATIBLE",
                },
            )

        # Property Value Incompatibility Guard on Objects/Modifiers:
        ref_omods = list(ref_prop.properties.get("object_modifiers", []))
        if ref_prop.object_lemma:
            ref_omods.append(ref_prop.object_lemma)
        stu_omods = list(stu_prop.properties.get("object_modifiers", []))
        if stu_prop.object_lemma:
            stu_omods.append(stu_prop.object_lemma)
        if self.are_property_values_incompatible(ref_omods, stu_omods):
            return (
                0.0,
                {
                    "subject_similarity": round(s_sim, 4),
                    "predicate_similarity": round(p_sim, 4),
                    "reason": "PROPERTY_VALUE_INCOMPATIBLE",
                },
            )

        # Property Value / Antonym Incompatibility Guard on Predicates & Predicate Modifiers:
        ref_pmods = list(ref_prop.properties.get("predicate_modifiers", []))
        if ref_prop.predicate_lemma:
            ref_pmods.append(ref_prop.predicate_lemma)
        stu_pmods = list(stu_prop.properties.get("predicate_modifiers", []))
        if stu_prop.predicate_lemma:
            stu_pmods.append(stu_prop.predicate_lemma)
        if self.are_property_values_incompatible(ref_pmods, stu_pmods):
            return (
                0.0,
                {
                    "subject_similarity": round(s_sim, 4),
                    "predicate_similarity": round(p_sim, 4),
                    "reason": "PREDICATE_INCOMPATIBLE",
                },
            )

        # Prepositional Argument Mutually Exclusive Conflict Guard:
        if self._check_prepositional_contradiction(stu_prop, ref_prop):
            return (
                0.0,
                {
                    "subject_similarity": round(s_sim, 4),
                    "predicate_similarity": round(p_sim, 4),
                    "reason": "PREPOSITIONAL_ARGUMENT_CONFLICT",
                },
            )

        # Predicate Compatibility Guard & Modifier Bridge:
        # Check if either predicate's meaning is carried by a subject or object modifier
        # (e.g. 'array has fixed size' vs 'array fixed size', or where a light/auxiliary verb + modifier
        # bridges to a participle predicate).
        s_mods = [m.lower() for m in ref_prop.properties.get("subject_modifiers", [])] + [
            m.lower() for m in stu_prop.properties.get("subject_modifiers", [])
        ]
        o_mods = [m.lower() for m in ref_prop.properties.get("object_modifiers", [])] + [
            m.lower() for m in stu_prop.properties.get("object_modifiers", [])
        ]
        all_mods = s_mods + o_mods

        best_mod_sim = 0.0
        for m in all_mods:
            sim_stu = self._compare_lemmas(m, stu_prop.predicate_lemma)
            sim_ref = self._compare_lemmas(m, ref_prop.predicate_lemma)
            best_m = max(sim_stu, sim_ref)
            if best_m > best_mod_sim:
                best_mod_sim = best_m

        if best_mod_sim >= 0.70 and p_sim < 0.70:
            p_sim = 0.85 * best_mod_sim
        elif p_sim <= 0.20:
            return (
                0.0,
                {
                    "subject_similarity": round(s_sim, 4),
                    "predicate_similarity": round(p_sim, 4),
                    "reason": "PREDICATE_INCOMPATIBLE",
                },
            )

        stu_prep_args = stu_prop.properties.get("prepositional_arguments", [])
        ref_prep_args = ref_prop.properties.get("prepositional_arguments", [])
        has_both_preps = bool(stu_prep_args and ref_prep_args)
        prep_sim = 0.0
        if has_both_preps:
            prep_sim = self._evaluate_prep_args_similarity(stu_prep_args, ref_prep_args)
            # If both explicitly specify prepositional arguments and they conflict (< 0.30)
            if prep_sim < 0.30:
                return (
                    0.0,
                    {
                        "subject_similarity": round(s_sim, 4),
                        "predicate_similarity": round(p_sim, 4),
                        "prep_similarity": round(prep_sim, 4),
                        "reason": "PREPOSITIONAL_ARGUMENT_CONFLICT",
                    },
                )

        if stu_prop.object_lemma is None and ref_prop.object_lemma is None:
            # Both lack an object (e.g. intransitive or passive clauses)
            if has_both_preps:
                score = 0.35 * s_sim + 0.35 * p_sim + 0.30 * prep_sim
            else:
                score = 0.45 * s_sim + 0.55 * p_sim
            o_sim = 1.0
        else:
            o_sim = self._compare_lemmas(stu_prop.object_lemma, ref_prop.object_lemma, pos="NOUN")
            if has_both_preps:
                score = 0.30 * s_sim + 0.35 * p_sim + 0.20 * o_sim + 0.15 * prep_sim
            else:
                score = 0.35 * s_sim + 0.40 * p_sim + 0.25 * o_sim

        return (
            score,
            {
                "subject_similarity": round(s_sim, 4),
                "predicate_similarity": round(p_sim, 4),
                "object_similarity": round(o_sim, 4),
                "prep_similarity": round(prep_sim, 4) if has_both_preps else None,
            },
        )

    def _compare_lemmas(
        self,
        l1: Optional[str],
        l2: Optional[str],
        pos: Optional[str] = None,
    ) -> float:
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
        elif hasattr(self.comparator, "compare"):
            rel = self.comparator.compare(l1_clean, l2_clean, source_pos=pos, target_pos=pos)
            if hasattr(rel, "similarity_score"):
                return float(rel.similarity_score)
            return float(rel)

        return 0.0
