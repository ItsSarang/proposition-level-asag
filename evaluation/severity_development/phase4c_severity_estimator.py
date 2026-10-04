"""
Interpretable Contradiction Severity Estimator Module (Phase 4C).

Estimates the conceptual severity of an already-identified contradiction
using deterministic, interpretable signals from the ASAG pipeline:
- Core proposition alignment
- Defining property targeting (uniqueness, ordering, translation)
- Entity concept grounding (detecting entity mismatches)
- Syntactic/peripheral displacement (naming, extensions, formatting)
- Evidence source and strength

CRITICAL ARCHITECTURAL CONSTRAINTS:
1. Contradiction Detection strictly precedes Severity Estimation.
   Non-contradictory propositions NEVER receive severity.
2. No LLMs, dense embeddings, or external APIs are used.
3. Completely decoupled from scoring: severity is an input to grading,
   not reverse-engineered from desired scores.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import re
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from base_asag.representation.hybrid import RobustProposition
from proposed_asag.contradiction.property_contradiction import (
    ContradictionEvidence,
    ContradictionType,
)


class SeverityLevel(str, Enum):
    """Categorical classification of contradiction severity."""
    NONE = "NONE"
    MINOR = "MINOR"
    MODERATE = "MODERATE"
    CORE_CONTRADICTION = "CORE_CONTRADICTION"
    UNRESOLVED = "UNRESOLVED"


@dataclass(frozen=True)
class SeverityEvidence:
    """Interpretable feature provenance supporting a severity assessment."""
    is_contradicted: bool
    contradiction_type: str
    evidence_strength: float
    entity_grounded: bool
    entity_name: str
    core_link: bool
    defining_property_target: bool
    conflicting_property: Optional[str]
    is_peripheral: bool
    is_relational_confusion: bool
    question_centrality: float
    reference_coverage_weight: float
    rationale_reasons: Tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_contradicted": self.is_contradicted,
            "contradiction_type": self.contradiction_type,
            "evidence_strength": round(self.evidence_strength, 4),
            "entity_grounded": self.entity_grounded,
            "entity_name": self.entity_name,
            "core_link": self.core_link,
            "defining_property_target": self.defining_property_target,
            "conflicting_property": self.conflicting_property,
            "is_peripheral": self.is_peripheral,
            "is_relational_confusion": self.is_relational_confusion,
            "question_centrality": round(self.question_centrality, 4),
            "reference_coverage_weight": round(self.reference_coverage_weight, 4),
            "rationale_reasons": list(self.rationale_reasons),
        }


@dataclass(frozen=True)
class SeverityEstimationResult:
    """Complete structured result of contradiction severity estimation."""
    severity: SeverityLevel
    severity_score: float  # Nominal continuous signal: 0.0, 0.25, 0.60, 1.00
    evidence: SeverityEvidence
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "severity": self.severity.value,
            "severity_score": round(self.severity_score, 4),
            "evidence": self.evidence.to_dict(),
            "explanation": self.explanation,
        }


class InterpretableSeverityEstimator:
    """
    Rule- and feature-based severity estimator for verified contradictions.
    """

    # Core defining properties by concept domain
    DEFINING_PROPERTIES: Dict[str, Set[str]] = {
        "PRIMARY_KEY": {"uniqueness", "nullability"},
        "BST": {"relative_size", "sort_order", "ordering"},
        "COMPILER": {"translation", "execution_discipline", "translate"},
    }

    # Canonical entities and incompatible/confused entity pairs
    TARGET_ENTITIES: Dict[str, Set[str]] = {
        "PRIMARY_KEY": {"primary key", "key", "pk"},
        "BST": {"binary search tree", "bst"},
        "COMPILER": {"compiler"},
    }

    CONFUSED_ENTITIES: Dict[str, Set[str]] = {
        "PRIMARY_KEY": {"foreign key", "candidate key", "super key"},
        "BST": {"binary tree", "general binary tree", "b-tree", "trie"},
        "COMPILER": {"interpreter", "assembler", "linker", "loader"},
    }

    # Peripheral cues: naming, extensions, formatting, dates, syntax styles, colors, implementation details
    PERIPHERAL_CUES: Set[str] = {
        "named", "name", "id", "extension", "exe", "class", "uppercase",
        "lowercase", "invented", "year", "date", "ibm", "ritchie", "bytes",
        "diagram", "blue", "painted", "first column", "storage", "ram", "gigabytes",
        "root directory", "syntax style", "pointers", "recursive", "functions"
    }

    # Relational/behavioral confusion cues: arity, complexity, balancing, secondary operational properties
    RELATIONAL_CUES: Set[str] = {
        "random", "traversal", "o(1)", "constant time", "balanced", "perfectly",
        "three children", "integer data type", "composite", "auto-increment",
        "multiple primary keys", "destroyed", "line by line", "cpu", "faster",
        "detect syntax", "optimization", "only translates c"
    }

    def __init__(self, default_domain: str = "PRIMARY_KEY") -> None:
        self.default_domain = default_domain

    def estimate(
        self,
        contradiction_evidence: Optional[ContradictionEvidence],
        student_prop: RobustProposition,
        reference_props: List[RobustProposition],
        question: str = "",
        domain: Optional[str] = None,
    ) -> SeverityEstimationResult:
        """
        Estimate contradiction severity from structured pipeline evidence.
        """
        active_domain = domain or self._infer_domain(question, reference_props)

        # 1. MANDATORY GATE: Check if proposition is actually contradicted
        if contradiction_evidence is None or not contradiction_evidence.is_contradicted:
            evidence = SeverityEvidence(
                is_contradicted=False,
                contradiction_type="NONE",
                evidence_strength=0.0,
                entity_grounded=False,
                entity_name="",
                core_link=False,
                defining_property_target=False,
                conflicting_property=None,
                is_peripheral=False,
                is_relational_confusion=False,
                question_centrality=0.0,
                reference_coverage_weight=0.0,
                rationale_reasons=("Proposition is not contradictory: severity is NONE.",),
            )
            return SeverityEstimationResult(
                severity=SeverityLevel.NONE,
                severity_score=0.0,
                evidence=evidence,
                explanation="No factual contradiction detected; proposition does not incur contradiction severity.",
            )

        # 2. Extract text and token sets (including extracted modifiers for entity grounding)
        subj_mods = " ".join(str(m) for m in student_prop.properties.get("subject_modifiers", ()))
        obj_mods = " ".join(str(m) for m in student_prop.properties.get("object_modifiers", ()))
        pred_mods = " ".join(str(m) for m in student_prop.properties.get("predicate_modifiers", ()))
        full_text = f"{subj_mods} {student_prop.source_text or ''} {obj_mods} {pred_mods}".strip().lower()
        stu_text = full_text
        stu_words = set(re.findall(r"\b\w+\b", stu_text))
        reasons: List[str] = []

        # 3. Entity Concept Grounding Check
        entity_grounded, detected_entity, is_confused_entity = self._check_entity_grounding(
            stu_text, stu_words, active_domain
        )
        if is_confused_entity:
            reasons.append(
                f"Entity confusion detected: statement discusses '{detected_entity}' rather than target '{active_domain}'."
            )
        elif entity_grounded:
            reasons.append(f"Entity successfully grounded to target '{active_domain}'.")

        # 4. Core Proposition Link Check
        core_link, linked_ref_prop = self._check_core_link(student_prop, reference_props)
        if core_link:
            reasons.append(f"Contradiction directly links to reference proposition: '{linked_ref_prop.source_text}'.")

        # 5. Defining Property Target Check
        conf_prop = contradiction_evidence.conflicting_property
        defining_target = False
        if conf_prop:
            defining_target = conf_prop.lower() in self.DEFINING_PROPERTIES.get(active_domain, set())
            if defining_target:
                reasons.append(f"Contradiction targets defining domain property: '{conf_prop}'.")

        # Check explicit negation of core predicate:
        # Must specifically negate the defining predicate of the reference proposition, not an arbitrary auxiliary verb
        is_core_negation = False
        if contradiction_evidence.contradiction_type == ContradictionType.EXPLICIT_NEGATION:
            negates_ref_pred = any(
                ref.predicate_lemma and ref.predicate_lemma.lower() in stu_words
                for ref in reference_props
            )
            # Ensure it is not a secondary constraint (e.g. data type or composite column)
            is_secondary_constraint = any(
                sec in stu_words for sec in ("composite", "integer", "optimization", "syntax")
            )
            if negates_ref_pred and not is_secondary_constraint:
                is_core_negation = True
                defining_target = True
                reasons.append("Explicit negation of core defining predicate identified.")

        # 6. Peripheral & Relational Misconception Cues (checks words and multi-word phrases)
        is_peripheral = any(
            (cue in stu_text if " " in cue else cue in stu_words)
            for cue in self.PERIPHERAL_CUES
        )
        if is_peripheral:
            reasons.append("Proposition contains peripheral/syntactic naming or formatting markers.")

        is_relational = any(
            (cue in stu_text if " " in cue else cue in stu_words)
            for cue in self.RELATIONAL_CUES
        )
        if is_relational and not defining_target:
            reasons.append("Proposition targets behavioral/relational operational attribute.")

        # 7. Reference Coverage Weight & Question Centrality
        n_ref = len(reference_props)
        ref_weight = (1.0 / n_ref) if n_ref > 0 else 0.0

        q_terms = set(re.findall(r"\b\w+\b", question.lower()))
        q_overlap = len(stu_words.intersection(q_terms)) / max(1, len(q_terms))

        # 8. Decision Logic: Determine Severity Level
        if is_confused_entity:
            # When an adjacent entity is discussed, the statement does NOT directly contradict the target entity
            level = SeverityLevel.UNRESOLVED
            score = 0.0
            explanation = (
                f"UNRESOLVED: Proposition discusses confused adjacent entity '{detected_entity}' "
                f"rather than target entity '{active_domain}'. Does not constitute core contradiction of target."
            )
        elif defining_target and entity_grounded:
            level = SeverityLevel.CORE_CONTRADICTION
            score = 1.00
            explanation = (
                f"CORE_CONTRADICTION: Directly contradicts core defining property "
                f"'{conf_prop or 'core predicate'}' of target entity '{active_domain}'."
            )
        elif is_peripheral:
            level = SeverityLevel.MINOR
            score = 0.25
            explanation = (
                f"MINOR: Peripheral misconception regarding secondary naming, formatting, or convention. "
                f"Does not invalidate central entity concept."
            )
        elif is_relational or contradiction_evidence.contradiction_type == ContradictionType.ANTONYM_CONFLICT:
            level = SeverityLevel.MODERATE
            score = 0.60
            explanation = (
                f"MODERATE: Conflicts with operational behavior or secondary property, "
                f"without inverting the defining invariant."
            )
        elif core_link and contradiction_evidence.evidence_strength >= 0.85:
            level = SeverityLevel.CORE_CONTRADICTION
            score = 1.00
            explanation = (
                f"CORE_CONTRADICTION: High-confidence conflict ({contradiction_evidence.evidence_strength:.2f}) "
                f"directly linked to primary reference assertion."
            )
        else:
            level = SeverityLevel.MODERATE
            score = 0.60
            explanation = (
                f"MODERATE: Unclassified contradiction with moderate conceptual impact."
            )

        evidence = SeverityEvidence(
            is_contradicted=True,
            contradiction_type=contradiction_evidence.contradiction_type.value,
            evidence_strength=contradiction_evidence.evidence_strength,
            entity_grounded=entity_grounded,
            entity_name=detected_entity,
            core_link=core_link,
            defining_property_target=defining_target,
            conflicting_property=conf_prop,
            is_peripheral=is_peripheral,
            is_relational_confusion=is_relational,
            question_centrality=q_overlap,
            reference_coverage_weight=ref_weight,
            rationale_reasons=tuple(reasons),
        )

        return SeverityEstimationResult(
            severity=level,
            severity_score=score,
            evidence=evidence,
            explanation=explanation,
        )

    def _infer_domain(self, question: str, reference_props: List[RobustProposition]) -> str:
        """Infer concept domain from question and reference text."""
        combined = (question + " " + " ".join(p.source_text for p in reference_props)).lower()
        if "primary key" in combined or "database" in combined or "record" in combined:
            return "PRIMARY_KEY"
        if "binary search tree" in combined or "bst" in combined or "subtree" in combined:
            return "BST"
        if "compiler" in combined or "translation" in combined or "machine code" in combined:
            return "COMPILER"
        return self.default_domain

    def _check_entity_grounding(
        self,
        stu_text: str,
        stu_words: Set[str],
        domain: str,
    ) -> Tuple[bool, str, bool]:
        """
        Verify whether the student proposition grounds to the target entity,
        or confuses an adjacent entity.
        Returns: (entity_grounded, entity_name, is_confused_entity)
        """
        confused_set = self.CONFUSED_ENTITIES.get(domain, set())
        for conf_ent in confused_set:
            if conf_ent in stu_text:
                return (False, conf_ent, True)

        target_set = self.TARGET_ENTITIES.get(domain, set())
        for tgt in target_set:
            if tgt in stu_text:
                return (True, tgt, False)

        # Default fallback: check if general keywords match
        if domain == "PRIMARY_KEY" and "key" in stu_words:
            return (True, "key", False)
        if domain == "BST" and "tree" in stu_words:
            return (True, "tree", False)
        if domain == "COMPILER" and "compiler" in stu_words:
            return (True, "compiler", False)

        return (True, "implicit_entity", False)

    def _check_core_link(
        self,
        student_prop: RobustProposition,
        reference_props: List[RobustProposition],
    ) -> Tuple[bool, Optional[RobustProposition]]:
        """
        Determine if the student proposition links directly to a core reference proposition.
        """
        stu_text = (student_prop.source_text or "").lower()
        stu_words = set(re.findall(r"\b\w+\b", stu_text))

        for ref in reference_props:
            ref_text = (ref.source_text or "").lower()
            ref_words = set(re.findall(r"\b\w+\b", ref_text))

            # Predicate match or direct lemma overlap
            if student_prop.predicate_lemma and ref.predicate_lemma:
                if student_prop.predicate_lemma.lower() == ref.predicate_lemma.lower():
                    return (True, ref)

            # High lexical intersection on non-stop words
            overlap = stu_words.intersection(ref_words) - {"a", "an", "the", "in", "is", "of", "to"}
            if len(overlap) >= 2:
                return (True, ref)

        return (False, None)
