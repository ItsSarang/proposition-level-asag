"""
Property-Level Contradiction Detection Module (Phase 5).

Provides conservative, interpretable contradiction analysis beyond simple surface
negation. Explicitly models entity-relation-value properties, resolves lexical
antonyms (preventing false contradictions on negated antonyms such as
'not fixed' == 'variable'), and enforces:
NOT_SUPPORTED != CONTRADICTED.
"""

from dataclasses import dataclass, field
from enum import Enum
import re
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from nltk.corpus import wordnet as wn
from base_asag.representation.hybrid import Polarity, RobustProposition


class ContradictionType(str, Enum):
    """Categorical classification of contradiction evidence."""
    NONE = "NONE"
    EXPLICIT_NEGATION = "EXPLICIT_NEGATION"
    ANTONYM_CONFLICT = "ANTONYM_CONFLICT"
    VALUE_CONFLICT = "VALUE_CONFLICT"


@dataclass(frozen=True)
class ContradictionEvidence:
    """
    Structured evidence of contradiction between a student proposition and reference context.
    """
    is_contradicted: bool
    contradiction_type: ContradictionType
    conflicting_entity: Optional[str]
    conflicting_property: Optional[str]
    conflicting_value: Optional[str]
    evidence_strength: float
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_contradicted": self.is_contradicted,
            "contradiction_type": self.contradiction_type.value,
            "conflicting_entity": self.conflicting_entity,
            "conflicting_property": self.conflicting_property,
            "conflicting_value": self.conflicting_value,
            "evidence_strength": round(self.evidence_strength, 4),
            "explanation": self.explanation,
        }


class PropertyContradictionDetector:
    """
    Detects factual, lexical, and property-level contradictions with
    conservative thresholds and antonymy-aware polarity resolution.
    """

    # Domain-specific mutually exclusive property value sets in Computer Science
    INCOMPATIBLE_VALUE_SETS: Dict[str, Tuple[Set[str], Set[str]]] = {
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
        "execution_location": (
            {"main", "main()", "main function"},
            {"header", "before main", "library"},
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
            {"random", "direct", "arbitrary", "indexed"},
            {"sequential", "linear", "serial"},
        ),
    }

    def __init__(self, wn_corpus: Optional[Any] = None) -> None:
        self.wn = wn_corpus or wn

    def detect_contradiction(
        self,
        student_prop: RobustProposition,
        reference_props: List[RobustProposition],
    ) -> ContradictionEvidence:
        """
        Check if student_prop directly contradicts any reference proposition.
        """
        if not reference_props:
            return ContradictionEvidence(
                is_contradicted=False,
                contradiction_type=ContradictionType.NONE,
                conflicting_entity=None,
                conflicting_property=None,
                conflicting_value=None,
                evidence_strength=0.0,
                explanation="No reference propositions available for contradiction comparison.",
            )

        # 1. Check for Incompatible Property Values (e.g. unique vs duplicate, fixed vs variable)
        val_evidence = self._check_property_value_conflict(student_prop, reference_props)
        if val_evidence.is_contradicted:
            return val_evidence

        # 1b. Check for Inverted Containment Contradiction (e.g. array is in elements)
        inv_contain_ev = self._check_containment_inverted(student_prop, reference_props)
        if inv_contain_ev.is_contradicted:
            return inv_contain_ev

        # 2. Check for Direct Polarity Clash on Semantically Aligned Predicates
        neg_evidence = self._check_explicit_negation_conflict(student_prop, reference_props)
        if neg_evidence.is_contradicted:
            return neg_evidence

        # 3. Check for WordNet Lexical Antonyms
        ant_evidence = self._check_lexical_antonyms(student_prop, reference_props)
        if ant_evidence.is_contradicted:
            return ant_evidence

        # Conservative default: NOT_SUPPORTED is NOT CONTRADICTED
        return ContradictionEvidence(
            is_contradicted=False,
            contradiction_type=ContradictionType.NONE,
            conflicting_entity=None,
            conflicting_property=None,
            conflicting_value=None,
            evidence_strength=0.0,
            explanation="No factual contradiction or incompatible property value detected.",
        )

    @staticmethod
    def _match_value_set(text: str, words: Set[str], val_set: Set[str]) -> Optional[str]:
        """
        Check if any value in val_set is present in text or words.
        Supports multi-word technical phrases and single words.
        """
        for val in val_set:
            if " " in val or "-" in val or "," in val:
                pattern = r"\b" + re.escape(val).replace(r"\ ", r"[\s\-_,]+") + r"\b"
                if re.search(pattern, text):
                    return val
            else:
                if val in words:
                    return val
        return None

    @staticmethod
    def _get_prop_text_and_words(prop: RobustProposition) -> Tuple[str, Set[str]]:
        """Extract full lexical text and word set from proposition and its linguistic trees."""
        parts = [prop.source_text or ""]
        if "subject_tree_lemmas" in prop.properties:
            parts.append(" ".join(prop.properties["subject_tree_lemmas"]))
        if "object_tree_lemmas" in prop.properties:
            parts.append(" ".join(prop.properties["object_tree_lemmas"]))
        if "prep_phrase_lemmas" in prop.properties:
            parts.append(" ".join(prop.properties["prep_phrase_lemmas"]))
        if "predicate_modifier_lemmas" in prop.properties:
            parts.append(" ".join(prop.properties["predicate_modifier_lemmas"]))
        combined = " ".join(parts).lower()
        words = set(re.findall(r"\b\w+\b", combined))
        return combined, words

    @staticmethod
    def _are_entity_qualifiers_incompatible(
        mods1: Optional[Sequence[str]], mods2: Optional[Sequence[str]]
    ) -> bool:
        from proposed_asag.proposition.core_recovery.core_paraphrase_recovery import (
            CoreParaphraseRecoverer,
        )
        return CoreParaphraseRecoverer.are_entity_qualifiers_incompatible(mods1, mods2)

    def _is_converse_relation(
        self, stu_prop: RobustProposition, ref_prop: RobustProposition
    ) -> bool:
        """
        Check if student and reference express an equivalent converse relation
        (e.g., A < B <=> B > A, or A is above B <=> B is below A, or Container contains Element).
        """
        from proposed_asag.proposition.core_recovery.core_paraphrase_recovery import (
            CoreParaphraseRecoverer,
        )
        recoverer = CoreParaphraseRecoverer()
        score, _ = recoverer._check_converse_equivalence(stu_prop, ref_prop)
        if score >= 0.55:
            return True
        c_score, _ = recoverer._check_containment_converse_bridge(stu_prop, ref_prop)
        return c_score >= 0.55

    def _check_containment_inverted(
        self, stu_prop: RobustProposition, ref_props: List[RobustProposition]
    ) -> ContradictionEvidence:
        from proposed_asag.proposition.core_recovery.core_paraphrase_recovery import (
            CoreParaphraseRecoverer,
        )
        recoverer = CoreParaphraseRecoverer()
        for ref in ref_props:
            if recoverer._check_containment_inverted(stu_prop, ref):
                return ContradictionEvidence(
                    is_contradicted=True,
                    contradiction_type=ContradictionType.VALUE_CONFLICT,
                    conflicting_entity=stu_prop.subject or "entity",
                    conflicting_property="containment_direction",
                    conflicting_value="inverted container and contained roles",
                    evidence_strength=0.90,
                    explanation=(
                        f"Inverted containment conflict: student asserts that container "
                        f"'{stu_prop.subject}' is contained within its elements."
                    ),
                )
        return ContradictionEvidence(
            is_contradicted=False,
            contradiction_type=ContradictionType.NONE,
            conflicting_entity=None,
            conflicting_property=None,
            conflicting_value=None,
            evidence_strength=0.0,
            explanation="",
        )

    def _check_property_value_conflict(
        self,
        stu_prop: RobustProposition,
        ref_props: List[RobustProposition],
    ) -> ContradictionEvidence:
        """
        Detect mutual exclusion in domain properties (e.g., unique vs duplicate).
        Also accounts for negation + antonym equivalence (e.g. 'not fixed' == 'variable'),
        entity compatibility, and converse relational equivalence.
        """
        from base_asag.semantic.domain_lexicon import are_domain_equivalent

        stu_text, stu_words = self._get_prop_text_and_words(stu_prop)
        is_stu_negated = (stu_prop.polarity == Polarity.NEGATIVE)

        for ref in ref_props:
            ref_text, ref_words = self._get_prop_text_and_words(ref)
            is_ref_negated = (ref.polarity == Polarity.NEGATIVE)

            # 1. Entity Qualifier Gate:
            ref_smods = ref.properties.get("subject_modifiers", [])
            stu_smods = stu_prop.properties.get("subject_modifiers", [])
            if self._are_entity_qualifiers_incompatible(ref_smods, stu_smods):
                continue

            # 2. Converse Equivalence Gate:
            # If student and reference form an equivalent converse relation (e.g. A < B <=> B > A),
            # opposite comparative values on swapped entities do NOT contradict!
            if self._is_converse_relation(stu_prop, ref):
                continue

            for prop_name, (set_a, set_b) in self.INCOMPATIBLE_VALUE_SETS.items():
                ref_val_a = self._match_value_set(ref_text, ref_words, set_a)
                ref_val_b = self._match_value_set(ref_text, ref_words, set_b)
                stu_val_a = self._match_value_set(stu_text, stu_words, set_a)
                stu_val_b = self._match_value_set(stu_text, stu_words, set_b)

                ref_in_a = ref_val_a is not None
                ref_in_b = ref_val_b is not None
                stu_in_a = stu_val_a is not None
                stu_in_b = stu_val_b is not None

                if (ref_in_a or ref_in_b) and (stu_in_a or stu_in_b):
                    # Check Antonymy Equivalence (e.g. ref has 'variable' (set_a), stu has 'not fixed' (negated set_b))
                    # Negated set_b is semantically equivalent to set_a!
                    if ref_in_a and stu_in_b and is_stu_negated and not is_ref_negated:
                        # Negated opposite is an equivalent paraphrase! NOT a contradiction!
                        continue
                    if ref_in_b and stu_in_a and is_stu_negated and not is_ref_negated:
                        continue

                    # Direct Value Conflict: Affirmative in set_a vs Affirmative in set_b
                    if (ref_in_a and stu_in_b and not is_stu_negated and not is_ref_negated) or \
                       (ref_in_b and stu_in_a and not is_stu_negated and not is_ref_negated):
                        ref_val = ref_val_a or ref_val_b
                        stu_val = stu_val_a or stu_val_b
                        return ContradictionEvidence(
                            is_contradicted=True,
                            contradiction_type=ContradictionType.VALUE_CONFLICT,
                            conflicting_entity=stu_prop.subject or "entity",
                            conflicting_property=prop_name,
                            conflicting_value=f"student '{stu_val}' vs reference '{ref_val}'",
                            evidence_strength=0.90,
                            explanation=(
                                f"Incompatible property value conflict on '{prop_name}': "
                                f"student claims '{stu_val}' while reference specifies '{ref_val}'."
                            ),
                        )

        return ContradictionEvidence(
            is_contradicted=False,
            contradiction_type=ContradictionType.NONE,
            conflicting_entity=None,
            conflicting_property=None,
            conflicting_value=None,
            evidence_strength=0.0,
            explanation="",
        )

    def _check_explicit_negation_conflict(
        self,
        stu_prop: RobustProposition,
        ref_props: List[RobustProposition],
    ) -> ContradictionEvidence:
        """
        Check for explicit negation polarity clash on matching subject-predicate pairs.
        """
        from base_asag.semantic.domain_lexicon import are_domain_equivalent

        for ref in ref_props:
            # Entity Qualifier Gate:
            ref_smods = ref.properties.get("subject_modifiers", [])
            stu_smods = stu_prop.properties.get("subject_modifiers", [])
            if self._are_entity_qualifiers_incompatible(ref_smods, stu_smods):
                continue

            # Check subject alignment
            subj_match = False
            s_stu = (stu_prop.subject_lemma or "").lower()
            s_ref = (ref.subject_lemma or "").lower()
            if s_stu and s_ref:
                subj_match = (s_stu == s_ref) or are_domain_equivalent(s_stu, s_ref)
            elif not s_stu and not s_ref:
                subj_match = True

            # Check predicate alignment
            p_stu = (stu_prop.predicate_lemma or "").lower()
            p_ref = (ref.predicate_lemma or "").lower()
            pred_match = (p_stu == p_ref) or are_domain_equivalent(p_stu, p_ref)
            if not pred_match and self.wn and p_stu and p_ref:
                try:
                    syns_stu = set(self.wn.synsets(p_stu, pos=self.wn.VERB))
                    syns_ref = set(self.wn.synsets(p_ref, pos=self.wn.VERB))
                    if syns_stu.intersection(syns_ref):
                        pred_match = True
                except Exception:
                    pass

            # Check object alignment if both specify an object
            obj_match = True
            o_stu = (stu_prop.object_lemma or "").lower()
            o_ref = (ref.object_lemma or "").lower()
            if o_stu and o_ref:
                obj_match = (o_stu == o_ref) or are_domain_equivalent(o_stu, o_ref)
                if not obj_match and self.wn:
                    try:
                        syns_stu = set(self.wn.synsets(o_stu, pos=self.wn.NOUN))
                        syns_ref = set(self.wn.synsets(o_ref, pos=self.wn.NOUN))
                        if syns_stu.intersection(syns_ref):
                            obj_match = True
                    except Exception:
                        pass
            elif o_ref and not o_stu and ref.representation_type.value in ("SPO", "PASSIVE_SPO"):
                obj_match = False

            # Prepositional Target Check:
            # If both specify prepositional arguments, they must be directed at matching targets
            # for negation to constitute a direct contradiction.
            # E.g., 'not allocated on heap' vs 'allocated on stack' does NOT contradict because targets differ.
            stu_prep_args = stu_prop.properties.get("prepositional_arguments", [])
            ref_prep_args = ref.properties.get("prepositional_arguments", [])
            if stu_prep_args and ref_prep_args:
                has_matching_target = False
                for p_stu_arg in stu_prep_args:
                    for p_ref_arg in ref_prep_args:
                        if isinstance(p_stu_arg, (list, tuple)) and isinstance(p_ref_arg, (list, tuple)):
                            noun_stu = str(p_stu_arg[1]).lower().strip(" .?!,:;")
                            noun_ref = str(p_ref_arg[1]).lower().strip(" .?!,:;")
                            if noun_stu == noun_ref or are_domain_equivalent(noun_stu, noun_ref):
                                has_matching_target = True
                                break
                    if has_matching_target:
                        break
                if not has_matching_target:
                    continue

            if subj_match and pred_match and obj_match:
                if stu_prop.polarity != ref.polarity:
                    return ContradictionEvidence(
                        is_contradicted=True,
                        contradiction_type=ContradictionType.EXPLICIT_NEGATION,
                        conflicting_entity=stu_prop.subject or "subject",
                        conflicting_property=stu_prop.predicate,
                        conflicting_value=f"polarity mismatch ({stu_prop.polarity.value} vs {ref.polarity.value})",
                        evidence_strength=0.85,
                        explanation=(
                            f"Explicit negation polarity conflict: student asserts {stu_prop.polarity.value} "
                            f"while reference asserts {ref.polarity.value} on predicate '{stu_prop.predicate}'."
                        ),
                    )

        return ContradictionEvidence(
            is_contradicted=False,
            contradiction_type=ContradictionType.NONE,
            conflicting_entity=None,
            conflicting_property=None,
            conflicting_value=None,
            evidence_strength=0.0,
            explanation="",
        )

    LIFO_TERMS: Set[str] = {
        "lifo", "last in first out", "last-in-first-out", "last-in, first-out", "last in, first out"
    }

    def _check_lexical_antonyms(
        self,
        stu_prop: RobustProposition,
        ref_props: List[RobustProposition],
    ) -> ContradictionEvidence:
        """
        Check for genuine lexical antonym contradictions with context-awareness:
        1. Contextual alignment: Antonyms only contradict when applied to the same
           predication (matching predicates with antonymous objects/complements,
           or matching subjects with antonymous predicates).
        2. Technical phrase / polar co-occurrence suppression: Terms like 'first' and 'last'
           occurring within technical idioms (e.g. LIFO) or co-occurring in
           the proposition/context do not contradict.
        """
        stu_text = (stu_prop.source_text or "").lower()
        stu_is_lifo = any(t in stu_text for t in self.LIFO_TERMS)

        for ref in ref_props:
            ref_text = (ref.source_text or "").lower()
            ref_is_lifo = any(t in ref_text for t in self.LIFO_TERMS)

            # Contextual Suppression 1: Both describe LIFO -> 'first' and 'last' do not contradict
            if stu_is_lifo and ref_is_lifo:
                continue

            # Contextual Suppression 2: If both student and reference describe LIFO via 'last ... first' structure
            # e.g., ref: "last item added will be the first removed" and stu: "last in first out"
            if (stu_is_lifo or ("last" in stu_text and "first" in stu_text)) and \
               ("last" in ref_text and "first" in ref_text):
                continue

            # Alignment Check:
            # Determine if the two propositions are semantically aligned enough to contradict.
            pred_match = False
            if stu_prop.predicate_lemma and ref.predicate_lemma:
                pred_match = (stu_prop.predicate_lemma.lower() == ref.predicate_lemma.lower())

            subj_match = False
            if stu_prop.subject_lemma and ref.subject_lemma:
                subj_match = (stu_prop.subject_lemma.lower() == ref.subject_lemma.lower())
            elif not stu_prop.subject_lemma and not ref.subject_lemma:
                subj_match = True

            # If neither predicate nor subject matches, propositions are unaligned:
            # opposing words do not imply factual contradiction across unrelated predications.
            if not pred_match and not subj_match:
                continue

            # Case A: Predicate Antonymy (Matching subjects, opposing predicates)
            # e.g. "cache increases latency" vs "cache decreases latency"
            if subj_match and stu_prop.predicate_lemma and ref.predicate_lemma:
                sp = stu_prop.predicate_lemma.lower()
                rp = ref.predicate_lemma.lower()
                antonyms = self._get_wordnet_antonyms(sp)
                if rp in antonyms and stu_prop.polarity == ref.polarity:
                    return ContradictionEvidence(
                        is_contradicted=True,
                        contradiction_type=ContradictionType.ANTONYM_CONFLICT,
                        conflicting_entity=stu_prop.subject or "subject",
                        conflicting_property="predicate_antonym",
                        conflicting_value=f"'{sp}' is antonym of '{rp}'",
                        evidence_strength=0.85,
                        explanation=f"Predicate antonymy conflict: '{sp}' directly opposes reference predicate '{rp}' on '{stu_prop.subject}'.",
                    )

            # Case B: Object / Complement Antonymy under Aligned Predicates
            # e.g. "the first item is removed last" vs "the first item is removed first"
            # e.g. "an inorder traversal outputs in descending order" vs "an inorder traversal outputs in ascending order"
            if pred_match:
                stu_objs = [w.lower() for w in (stu_prop.object_lemma, stu_prop.object) if w]
                if "predicate_modifier_lemmas" in stu_prop.properties:
                    stu_objs.extend(stu_prop.properties["predicate_modifier_lemmas"])
                if stu_prop.predicate and stu_prop.predicate.lower() in stu_text:
                    post_pred_stu = stu_text[stu_text.find(stu_prop.predicate.lower()) + len(stu_prop.predicate):]
                    stu_objs.extend(re.findall(r"\b\w+\b", post_pred_stu))

                ref_objs = [w.lower() for w in (ref.object_lemma, ref.object) if w]
                if "predicate_modifier_lemmas" in ref.properties:
                    ref_objs.extend(ref.properties["predicate_modifier_lemmas"])
                if ref.predicate and ref.predicate.lower() in ref_text:
                    post_pred_ref = ref_text[ref_text.find(ref.predicate.lower()) + len(ref.predicate):]
                    ref_objs.extend(re.findall(r"\b\w+\b", post_pred_ref))

                for so in set(stu_objs):
                    antonyms = self._get_wordnet_antonyms(so)
                    for ro in set(ref_objs):
                        if ro in antonyms and stu_prop.polarity == ref.polarity:
                            # Avoid false conflict if so and ro co-occur in the same complement
                            if so in ref_objs or ro in stu_objs:
                                continue
                            return ContradictionEvidence(
                                is_contradicted=True,
                                contradiction_type=ContradictionType.ANTONYM_CONFLICT,
                                conflicting_entity=stu_prop.predicate or "predicate",
                                conflicting_property="complement_antonym",
                                conflicting_value=f"'{so}' is antonym of '{ro}'",
                                evidence_strength=0.80,
                                explanation=(
                                    f"Complement antonymy conflict: student specifies '{so}' "
                                    f"while reference specifies '{ro}' for action '{stu_prop.predicate}'."
                                ),
                            )

            # Case C: Direct Object Antonymy with Aligned Subjects
            if subj_match and stu_prop.object_lemma and ref.object_lemma:
                so = stu_prop.object_lemma.lower()
                ro = ref.object_lemma.lower()
                antonyms = self._get_wordnet_antonyms(so)
                if ro in antonyms and stu_prop.polarity == ref.polarity:
                    return ContradictionEvidence(
                        is_contradicted=True,
                        contradiction_type=ContradictionType.ANTONYM_CONFLICT,
                        conflicting_entity=stu_prop.subject or "subject",
                        conflicting_property="object_antonym",
                        conflicting_value=f"'{so}' is antonym of '{ro}'",
                        evidence_strength=0.80,
                        explanation=f"Lexical antonymy conflict: '{so}' directly opposes reference concept '{ro}'.",
                    )

        return ContradictionEvidence(
            is_contradicted=False,
            contradiction_type=ContradictionType.NONE,
            conflicting_entity=None,
            conflicting_property=None,
            conflicting_value=None,
            evidence_strength=0.0,
            explanation="",
        )

    def _get_wordnet_antonyms(self, word: str) -> Set[str]:
        """Collect all lexical antonyms for a word across its synsets."""
        ants: Set[str] = set()
        for s in self.wn.synsets(word):
            for l in s.lemmas():
                for a in l.antonyms():
                    ants.add(a.name().lower())
        return ants
