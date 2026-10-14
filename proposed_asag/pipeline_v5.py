"""
Experiment 5 Modular ASAG Pipeline (System 5).

Coordinates the three focused interventions developed from the Experiment 4 diagnostic:
1. Core Paraphrase Recovery (Part A)
2. Canonical Reference Fragment Representation (Part B)
3. Contradiction Guards (Part C)
4. Soft-Gated Severity-Aware Scorer Model D2 (Part D)

Supports clean execution of all 5 experimental variants:
- V4: Frozen Experiment 4 baseline.
- V5-A: Core Paraphrase Recovery + Canonical Fragments + Exp 4 Scorer (Model D).
- V5-B: V5-A + Contradiction Guards + Exp 4 Scorer (Model D).
- V5-C: Frozen Exp 4 upstream/classification + Model D2 Scorer.
- V5: Full Experiment 5 Pipeline (V5-A + V5-B + Model D2).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple, Union

from base_asag.dependency.parser import DependencyParser, ParsedDocument
from base_asag.dependency.triples import DependencyRelation
from base_asag.matching.triple_matcher import MatchedRelation
from base_asag.representation.hybrid import RobustProposition, RobustPropositionExtractor
from proposed_asag.classification.robust_classifier import (
    AdditionalInfoClass,
    ClassifiedProposition,
    RobustAdditionalInfoClassifier,
)
from proposed_asag.contradiction.guards import ContradictionGuardPipeline
from proposed_asag.contradiction.property_contradiction import (
    ContradictionEvidence,
    ContradictionType,
    PropertyContradictionDetector,
)
from proposed_asag.evidence.models import EvidenceSource, EvidenceStatus, VerificationEvidence
from proposed_asag.overhauled_pipeline import (
    OverhauledASAGPipeline,
    OverhauledASAGResult,
    relation_to_robust_prop,
    robust_prop_to_relation,
)
from proposed_asag.proposition.canonical_reference import CanonicalReferenceExtractor
from proposed_asag.proposition.core_recovery.core_paraphrase_recovery import (
    CoreParaphraseRecoverer,
    CoreParaphraseRecoveryResult,
    CoreRecoveryBatchResult,
)
from proposed_asag.scoring.model_d2_scorer import ModelD2Scorer
from proposed_asag.scoring.severity_aware_scorer import (
    SeverityAwareEvaluationResult,
    SeverityAwareScoreResult,
    SeverityAwareScorer,
    SeverityItemizedAdjustment,
)


class Experiment5Variant(str, Enum):
    """Experimental variants for Experiment 5 evaluation and ablation."""
    V4 = "V4"        # Frozen Experiment 4
    V5_A = "V5-A"    # Core Paraphrase + Non-sentential Fragments + Model D
    V5_B = "V5-B"    # V5-A + Contradiction Guards + Model D
    V5_C = "V5-C"    # Frozen Exp 4 Upstream + Model D2
    V5 = "V5"        # Full System: V5-A + V5-B + Model D2


class RequirementStatus(str, Enum):
    """Evaluation status of an individual reference requirement."""
    SUPPORTED = "SUPPORTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    MISSING = "MISSING"
    CONTRADICTED = "CONTRADICTED"
    UNCERTAIN = "UNCERTAIN"


@dataclass(frozen=True)
class ReferenceRequirementRecord:
    """Interpretable evaluation record for an essential reference proposition/requirement."""
    requirement_index: int
    reference_text: str
    requirement_proposition: RobustProposition
    status: RequirementStatus
    assigned_student_proposition: Optional[RobustProposition] = None
    fulfillment_method: str = "NONE"
    confidence: float = 0.0
    score_contribution: float = 0.0
    explanation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "requirement_index": self.requirement_index,
            "reference_text": self.reference_text,
            "requirement_proposition": self.requirement_proposition.to_dict(),
            "status": self.status.value,
            "assigned_student_proposition": (
                self.assigned_student_proposition.to_dict()
                if self.assigned_student_proposition
                else None
            ),
            "fulfillment_method": self.fulfillment_method,
            "confidence": round(self.confidence, 4),
            "score_contribution": round(self.score_contribution, 4),
            "explanation": self.explanation,
        }


@dataclass(frozen=True)
class Experiment5Result:
    """Complete evaluation result for an Experiment 5 pipeline execution."""
    variant: str
    question: str
    reference_answer: str
    student_answer: str
    base_score_raw: float
    base_score_effective: float
    final_score: float
    final_grade: float
    score_result: SeverityAwareScoreResult
    core_recovery_result: Optional[CoreRecoveryBatchResult] = None
    recovered_core_count: int = 0
    guarded_contradiction_count: int = 0
    reference_requirements: List[ReferenceRequirementRecord] = field(default_factory=list)
    counts: Dict[str, int] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "variant": self.variant,
            "question": self.question,
            "reference_answer": self.reference_answer,
            "student_answer": self.student_answer,
            "base_score_raw": round(self.base_score_raw, 4),
            "base_score_effective": round(self.base_score_effective, 4),
            "final_score": round(self.final_score, 4),
            "final_grade": round(self.final_grade, 4),
            "score_result": self.score_result.to_dict(),
            "recovered_core_count": self.recovered_core_count,
            "guarded_contradiction_count": self.guarded_contradiction_count,
            "reference_requirements": [r.to_dict() for r in self.reference_requirements],
            "counts": self.counts,
            "metadata": self.metadata,
        }


class Experiment5Pipeline:
    """
    End-to-End Experiment 5 ASAG Pipeline supporting all 5 experimental variants.
    """

    def __init__(
        self,
        variant: Union[Experiment5Variant, str] = Experiment5Variant.V5,
        enable_core_recovery: Optional[bool] = None,
        enable_canonical_fragments: Optional[bool] = None,
        enable_contradiction_guards: Optional[bool] = None,
        scoring_model: Optional[str] = None,
        enable_additional_info: bool = True,
    ) -> None:
        if isinstance(variant, str):
            variant = Experiment5Variant(variant)
        self.variant = variant
        self.enable_additional_info = enable_additional_info

        # Configure switches according to variant unless explicitly overridden
        if variant == Experiment5Variant.V4:
            self.enable_core_recovery = False if enable_core_recovery is None else enable_core_recovery
            self.enable_canonical_fragments = False if enable_canonical_fragments is None else enable_canonical_fragments
            self.enable_contradiction_guards = False if enable_contradiction_guards is None else enable_contradiction_guards
            self.scoring_model_type = "model_d" if scoring_model is None else scoring_model

        elif variant == Experiment5Variant.V5_A:
            self.enable_core_recovery = True if enable_core_recovery is None else enable_core_recovery
            self.enable_canonical_fragments = True if enable_canonical_fragments is None else enable_canonical_fragments
            self.enable_contradiction_guards = False if enable_contradiction_guards is None else enable_contradiction_guards
            self.scoring_model_type = "model_d" if scoring_model is None else scoring_model

        elif variant == Experiment5Variant.V5_B:
            self.enable_core_recovery = True if enable_core_recovery is None else enable_core_recovery
            self.enable_canonical_fragments = True if enable_canonical_fragments is None else enable_canonical_fragments
            self.enable_contradiction_guards = True if enable_contradiction_guards is None else enable_contradiction_guards
            self.scoring_model_type = "model_d" if scoring_model is None else scoring_model

        elif variant == Experiment5Variant.V5_C:
            self.enable_core_recovery = False if enable_core_recovery is None else enable_core_recovery
            self.enable_canonical_fragments = False if enable_canonical_fragments is None else enable_canonical_fragments
            self.enable_contradiction_guards = False if enable_contradiction_guards is None else enable_contradiction_guards
            self.scoring_model_type = "model_d2" if scoring_model is None else scoring_model

        else:  # V5 (Full System)
            self.enable_core_recovery = True if enable_core_recovery is None else enable_core_recovery
            self.enable_canonical_fragments = True if enable_canonical_fragments is None else enable_canonical_fragments
            self.enable_contradiction_guards = True if enable_contradiction_guards is None else enable_contradiction_guards
            self.scoring_model_type = "model_d2" if scoring_model is None else scoring_model

        # Subcomponents
        self.parser = DependencyParser()
        self.hybrid_extractor = RobustPropositionExtractor()
        self.canonical_ref_extractor = CanonicalReferenceExtractor(self.parser)
        self.base_pipeline = OverhauledASAGPipeline()
        self.core_recoverer = CoreParaphraseRecoverer()
        self.contradiction_detector = PropertyContradictionDetector()
        self.contradiction_guards = ContradictionGuardPipeline()
        self.model_d_scorer = SeverityAwareScorer()
        self.model_d2_scorer = ModelD2Scorer()

    def evaluate(
        self,
        question: str,
        reference_answer: str,
        student_answer: str,
        domain: Optional[str] = None,
    ) -> Experiment5Result:
        """
        Execute full end-to-end evaluation under the configured Experiment 5 variant.
        """
        # 1. Parse texts
        ref_parsed = self.parser.parse_document(reference_answer)
        stu_parsed = self.parser.parse_document(student_answer)

        # 2. Extract reference propositions
        if self.enable_canonical_fragments:
            ref_props = self.canonical_ref_extractor.extract_document(
                ref_parsed, reference_answer, question=question
            )
        else:
            ref_props = self.hybrid_extractor.extract_document(ref_parsed, reference_answer)

        # 3. Extract student propositions
        if self.enable_canonical_fragments:
            stu_props = self.canonical_ref_extractor.extract_document(
                stu_parsed, student_answer, question=question
            )
        else:
            stu_props = self.hybrid_extractor.extract_document(stu_parsed, student_answer)

        # 4. Standard base matching
        ref_relations = [robust_prop_to_relation(p) for p in ref_props]
        stu_relations = [robust_prop_to_relation(p) for p in stu_props]
        matching_res = self.base_pipeline.matcher.match(ref_relations, stu_relations)

        # Compute initial base coverage
        n_ref = len(ref_relations)
        base_coverage = 0.0
        matched_ref_indices: Set[int] = set()
        matched_stu_indices: Set[int] = set()
        contradicted_stu_props: List[Tuple[RobustProposition, Any]] = []
        req_eval_map: Dict[int, Dict[str, Any]] = {}
        guarded_contradiction_count = 0

        if n_ref > 0:
            entail_res_list = self.base_pipeline.entailment_analyzer.evaluate_matching_result(
                matching_res, ref_parsed, stu_parsed
            )
            for matched, entail_res in zip(matching_res.matched_relations, entail_res_list):
                status = entail_res.relation
                ref_p = ref_props[matched.reference_index]
                stu_p = stu_props[matched.student_index]

                # Entity Qualifier Incompatibility Guard (e.g., 'primary key' vs 'foreign key')
                ref_smods = ref_p.properties.get("subject_modifiers", [])
                stu_smods = stu_p.properties.get("subject_modifiers", [])
                if self.core_recoverer.are_entity_qualifiers_incompatible(ref_smods, stu_smods):
                    # Incompatible entities: this student relation cannot satisfy the reference proposition
                    continue

                # 1. Check for Converse Relational Equivalence (e.g., A < B <=> B > A, Above/Below)
                conv_score, conv_ev = self.core_recoverer._check_converse_equivalence(stu_p, ref_p)
                cont_score, _ = self.core_recoverer._check_containment_converse_bridge(stu_p, ref_p)
                is_converse = (conv_score >= 0.55 or cont_score >= 0.55)

                if is_converse:
                    status = "ENTAILS"
                    matched_triple_score = max(conv_score, cont_score)
                elif conv_ev.get("reason") == "NON_CONVERSE_ARGUMENT_REVERSAL":
                    status = "CONTRADICTS"
                    matched_triple_score = matched.triple_score
                else:
                    matched_triple_score = matched.triple_score

                    # Inverted Containment Conflict Guard (e.g. 'array is in elements')
                    if self.core_recoverer._check_containment_inverted(stu_p, ref_p):
                        status = "CONTRADICTS"

                    # Property Value Incompatibility Guard (e.g., 'unique' vs 'duplicate')
                    ref_omods = list(ref_p.properties.get("object_modifiers", []))
                    if ref_p.object_lemma:
                        ref_omods.append(ref_p.object_lemma)
                    stu_omods = list(stu_p.properties.get("object_modifiers", []))
                    if stu_p.object_lemma:
                        stu_omods.append(stu_p.object_lemma)
                    if self.core_recoverer.are_property_values_incompatible(ref_omods, stu_omods):
                        status = "CONTRADICTS"

                    # Predicate & Predicate Modifier Incompatibility Guard (e.g., 'randomly' vs 'sequentially', 'increase' vs 'decrease')
                    ref_pmods = list(ref_p.properties.get("predicate_modifiers", []))
                    if ref_p.predicate_lemma:
                        ref_pmods.append(ref_p.predicate_lemma)
                    stu_pmods = list(stu_p.properties.get("predicate_modifiers", []))
                    if stu_p.predicate_lemma:
                        stu_pmods.append(stu_p.predicate_lemma)
                    if self.core_recoverer.are_property_values_incompatible(ref_pmods, stu_pmods):
                        status = "CONTRADICTS"

                    # Prepositional Argument Mutually Exclusive Conflict Guard
                    # Enforces: Low similarity alone or different prepositions NEVER establish contradiction.
                    # Contradiction requires positive evidence of mutually exclusive values or spatial opposites.
                    if self.core_recoverer._check_prepositional_contradiction(stu_p, ref_p):
                        status = "CONTRADICTS"

                if status == "CONTRADICTS":
                    # If contradiction was triggered by explicit negation, verify that the negation
                    # does not target a different prepositional argument
                    # (e.g. 'not allocated on the heap' vs 'allocated on the stack' does NOT contradict because targets differ).
                    if entail_res.student_polarity == "NEGATED" or "explicit negation" in " ".join(entail_res.reasons).lower():
                        ref_prep_args = [
                            (str(it[0]).strip().lower(), str(it[1]).strip().lower().strip(" .?!,:;"))
                            for it in ref_p.properties.get("prepositional_arguments", [])
                            if isinstance(it, (list, tuple)) and len(it) >= 2
                        ]
                        stu_prep_args = [
                            (str(it[0]).strip().lower(), str(it[1]).strip().lower().strip(" .?!,:;"))
                            for it in stu_p.properties.get("prepositional_arguments", [])
                            if isinstance(it, (list, tuple)) and len(it) >= 2
                        ]
                        if ref_prep_args and stu_prep_args:
                            has_divergent_target = False
                            for p_ref_item, n_ref_item in ref_prep_args:
                                for p_stu_item, n_stu_item in stu_prep_args:
                                    if p_ref_item == p_stu_item or self.core_recoverer._are_preps_equivalent(p_ref_item, p_stu_item):
                                        if (
                                            self.core_recoverer.are_property_values_incompatible([n_ref_item], [n_stu_item])
                                            or self.core_recoverer.are_entity_qualifiers_incompatible([n_ref_item], [n_stu_item])
                                        ):
                                            has_divergent_target = True
                                            break
                            if has_divergent_target:
                                status = "MISSING"

                # Check contradiction guards if contradiction was detected
                if status == "CONTRADICTS" and self.enable_contradiction_guards:
                    reason_str = '; '.join(entail_res.reasons) or 'Mutually exclusive property/argument conflict'
                    if conv_ev.get("reason") == "NON_CONVERSE_ARGUMENT_REVERSAL":
                        reason_str = "NON_CONVERSE_ARGUMENT_REVERSAL"
                    cev = ContradictionEvidence(
                        is_contradicted=True,
                        contradiction_type=ContradictionType.EXPLICIT_NEGATION
                        if entail_res.student_polarity == "NEGATED"
                        or "explicit negation" in " ".join(entail_res.reasons).lower()
                        else ContradictionType.VALUE_CONFLICT,
                        conflicting_entity=stu_p.subject,
                        conflicting_property=stu_p.predicate,
                        conflicting_value=stu_p.object,
                        evidence_strength=entail_res.confidence,
                        explanation=f"Core reference proposition contradicted: {reason_str}",
                    )
                    guarded_cev = self.contradiction_guards.guard_contradiction(
                        raw_evidence=cev,
                        student_prop=stu_p,
                        reference_props=ref_props,
                        question=question,
                        student_answer=student_answer,
                        reference_answer=reference_answer,
                    )
                    if not guarded_cev.is_contradicted:
                        guarded_contradiction_count += 1
                        status = "UNCERTAIN"

                weight = 1.0 if status == "ENTAILS" else (0.5 if status == "UNCERTAIN" else 0.0)
                base_coverage += (weight * matched_triple_score) / n_ref
                matched_ref_indices.add(matched.reference_index)
                matched_stu_indices.add(matched.student_index)
                if status == "CONTRADICTS":
                    contradicted_stu_props.append((stu_props[matched.student_index], entail_res))
                    req_eval_map[matched.reference_index] = {
                        "status": RequirementStatus.CONTRADICTED,
                        "student_proposition": stu_p,
                        "method": "BASE_TRIPLE_CONTRADICTED",
                        "confidence": entail_res.confidence,
                        "score_contribution": 0.0,
                        "explanation": f"Core reference requirement contradicted: {'; '.join(entail_res.reasons) or 'Mutually exclusive property/argument conflict'}",
                    }
                elif status == "ENTAILS":
                    req_eval_map[matched.reference_index] = {
                        "status": RequirementStatus.SUPPORTED,
                        "student_proposition": stu_p,
                        "method": "BASE_TRIPLE_MATCH",
                        "confidence": matched_triple_score,
                        "score_contribution": (1.0 * matched_triple_score) / n_ref,
                        "explanation": f"Entailed by student statement: '{stu_p.source_text}'",
                    }
                elif status == "UNCERTAIN":
                    req_eval_map[matched.reference_index] = {
                        "status": RequirementStatus.PARTIALLY_SUPPORTED,
                        "student_proposition": stu_p,
                        "method": "BASE_TRIPLE_MATCH_UNCERTAIN",
                        "confidence": 0.5 * matched_triple_score,
                        "score_contribution": (0.5 * matched_triple_score) / n_ref,
                        "explanation": f"Partially entailed with uncertainty: '{stu_p.source_text}'",
                    }
                elif status == "MISSING":
                    req_eval_map[matched.reference_index] = {
                        "status": RequirementStatus.MISSING,
                        "student_proposition": stu_p,
                        "method": "NEGATION_DIFFERENT_TARGET",
                        "confidence": 0.0,
                        "score_contribution": 0.0,
                        "explanation": "Student asserts negative property of a different target; reference requirement is unfulfilled.",
                    }

        # Identify initially unmatched student propositions
        unmatched_stu_props = [
            stu_props[i] for i in range(len(stu_props)) if i not in matched_stu_indices
        ]
        matched_stu_props = [
            stu_props[i]
            for i in range(len(stu_props))
            if i in matched_stu_indices
            and not any(cp[0] is stu_props[i] for cp in contradicted_stu_props)
        ]

        # 5. Core Paraphrase Recovery (Part A)
        recovery_batch_res: Optional[CoreRecoveryBatchResult] = None
        recovered_core_count = 0
        effective_base_coverage = base_coverage

        if self.enable_core_recovery and (len(unmatched_stu_props) > 0 or len(matched_ref_indices) < n_ref) and n_ref > 0:
            recovery_batch_res = self.core_recoverer.recover(
                unmatched_student_props=unmatched_stu_props,
                reference_props=ref_props,
                matched_reference_indices=matched_ref_indices,
                matched_student_props=matched_stu_props,
                question=question,
                reference_answer=reference_answer,
                student_answer=student_answer,
            )
            recovered_core_count = recovery_batch_res.recovered_count
            for rec in recovery_batch_res.recovered_propositions:
                # Add recovered core proposition to base coverage
                effective_base_coverage += (rec.confidence * 1.0) / n_ref
                if rec.student_proposition not in matched_stu_props:
                    matched_stu_props.append(rec.student_proposition)
                if rec.reference_index is not None:
                    matched_ref_indices.add(rec.reference_index)
                    if rec.reference_index not in req_eval_map:
                        r_status = (
                            RequirementStatus.SUPPORTED
                            if rec.confidence >= 0.70
                            else RequirementStatus.PARTIALLY_SUPPORTED
                        )
                        req_eval_map[rec.reference_index] = {
                            "status": r_status,
                            "student_proposition": rec.student_proposition,
                            "method": rec.reason,
                            "confidence": rec.confidence,
                            "score_contribution": (rec.confidence * 1.0) / n_ref,
                            "explanation": f"Recovered as core paraphrase ({rec.reason}): '{rec.student_proposition.source_text}'",
                        }

            # Only genuine non-core propositions proceed to additional info layer
            props_for_additional = recovery_batch_res.unmatched_propositions
        else:
            props_for_additional = unmatched_stu_props

        effective_base_coverage = min(1.0, max(0.0, effective_base_coverage))

        # 6. Additional Information Classification
        classified_props: List[ClassifiedProposition] = []
        if len(props_for_additional) > 0:
            raw_class_res = self.base_pipeline.classifier.classify_propositions(
                question=question,
                reference_answer=reference_answer,
                student_answer=student_answer,
                unmatched_student_props=props_for_additional,
                matched_student_props=(),
                reference_props=ref_props,
            )
            classified_props = list(raw_class_res.classified_propositions)

        # 7. Contradiction Guards (Part C)
        if self.enable_contradiction_guards and classified_props:
            guarded_classified: List[ClassifiedProposition] = []
            for cp in classified_props:
                if cp.classification == AdditionalInfoClass.INCORRECT and cp.contradiction_evidence:
                    guarded_ev = self.contradiction_guards.guard_contradiction(
                        raw_evidence=cp.contradiction_evidence,
                        student_prop=cp.proposition,
                        reference_props=ref_props,
                        question=question,
                        student_answer=student_answer,
                        reference_answer=reference_answer,
                    )
                    if not guarded_ev.is_contradicted:
                        guarded_contradiction_count += 1
                        # Reclassify from INCORRECT to UNCERTAIN (zero penalty, neutral)
                        guarded_cp = ClassifiedProposition(
                            proposition=cp.proposition,
                            classification=AdditionalInfoClass.UNCERTAIN,
                            score_effect=0.0,
                            rationale=f"CONTRADICTION_GUARDED: {guarded_ev.explanation}",
                            relevance_evidence=cp.relevance_evidence,
                            contradiction_evidence=guarded_ev,
                            verification_evidence=None,
                        )
                        guarded_classified.append(guarded_cp)
                    else:
                        guarded_classified.append(cp)
                else:
                    guarded_classified.append(cp)
            classified_props = guarded_classified

        # Add non-contradicted matched propositions as MATCHED_BY_BASE_ASAG
        all_propositions_for_scoring: List[ClassifiedProposition] = []
        for mp in matched_stu_props:
            all_propositions_for_scoring.append(
                ClassifiedProposition(
                    proposition=mp,
                    classification=AdditionalInfoClass.MATCHED_BY_BASE_ASAG,
                    score_effect=0.0,
                    rationale="Matched core proposition.",
                    relevance_evidence=None,
                    contradiction_evidence=None,
                    verification_evidence=VerificationEvidence(
                        status=EvidenceStatus.SUPPORTED,
                        source=EvidenceSource.REFERENCE_ASSERTION,
                        confidence=1.0,
                        rationale="Proposition matches reference answer content.",
                    ),
                )
            )

        # Propagate base-level core contradictions to the scoring layer
        for c_prop, entail_res in contradicted_stu_props:
            cev = ContradictionEvidence(
                is_contradicted=True,
                contradiction_type=ContradictionType.EXPLICIT_NEGATION
                if entail_res.student_polarity == "NEGATED"
                or "explicit negation" in " ".join(entail_res.reasons).lower()
                else ContradictionType.VALUE_CONFLICT,
                conflicting_entity=c_prop.subject,
                conflicting_property=c_prop.predicate,
                conflicting_value=c_prop.object,
                evidence_strength=entail_res.confidence,
                explanation=f"Core reference proposition contradicted: {'; '.join(entail_res.reasons)}",
            )
            all_propositions_for_scoring.append(
                ClassifiedProposition(
                    proposition=c_prop,
                    classification=AdditionalInfoClass.INCORRECT,
                    score_effect=0.0,
                    rationale=f"CORE_CONTRADICTION: {'; '.join(entail_res.reasons)}",
                    relevance_evidence=None,
                    contradiction_evidence=cev,
                    verification_evidence=None,
                )
            )

        if not self.enable_additional_info:
            # Ablation Mode: Score purely on core reference requirement coverage
            score_res = SeverityAwareScoreResult(
                model_name="core_only",
                base_score=effective_base_coverage,
                core_effective_score=effective_base_coverage,
                has_core_invalidation=(len(contradicted_stu_props) > 0),
                core_contradiction_count=len(contradicted_stu_props),
                positive_adjustment=0.0,
                negative_adjustment=0.0,
                net_adjustment=0.0,
                raw_score=effective_base_coverage,
                final_score=effective_base_coverage,
                final_grade=effective_base_coverage * 5.0,
                is_clipped_upper=False,
                is_clipped_lower=False,
                counts={
                    "matched": len(matched_stu_props),
                    "core_contradictions": len(contradicted_stu_props),
                    "correct_additional": 0,
                    "incorrect": 0,
                    "irrelevant": 0,
                    "uncertain": 0,
                },
                itemized_adjustments=[],
                explanation="V5 Core Only: Scored solely on core reference requirement coverage.",
                metadata={"ablation": "core_only"},
            )
        else:
            all_propositions_for_scoring.extend(classified_props)

            # 8. Scoring: Model D2 vs Model D (Part D)
            if self.scoring_model_type == "model_d2":
                score_res = self.model_d2_scorer.score(
                    base_score=effective_base_coverage,
                    classification_result=all_propositions_for_scoring,
                    reference_propositions=ref_props,
                    question=question,
                    domain=domain,
                )
            else:
                score_res = self.model_d_scorer.score(
                    base_score=effective_base_coverage,
                    classification_result=all_propositions_for_scoring,
                    reference_propositions=ref_props,
                    question=question,
                    domain=domain,
                )

        final_norm = score_res.final_score
        final_grade = score_res.final_grade

        counts = {
            "total_ref_props": n_ref,
            "total_stu_props": len(stu_props),
            "matched_by_base": len(matched_ref_indices),
            "recovered_core": recovered_core_count,
            "guarded_contradictions": guarded_contradiction_count,
            "correct_additional": score_res.counts.get("correct_additional", 0),
            "incorrect": score_res.counts.get("incorrect", 0),
            "irrelevant": score_res.counts.get("irrelevant", 0),
            "uncertain": score_res.counts.get("uncertain", 0),
        }

        # Build ReferenceRequirementRecord for each reference proposition
        reference_requirements: List[ReferenceRequirementRecord] = []
        for r_idx, ref_p in enumerate(ref_props):
            info = req_eval_map.get(
                r_idx,
                {
                    "status": RequirementStatus.MISSING,
                    "student_proposition": None,
                    "method": "NONE",
                    "confidence": 0.0,
                    "score_contribution": 0.0,
                    "explanation": "Requirement not mentioned or supported in student answer.",
                },
            )
            reference_requirements.append(
                ReferenceRequirementRecord(
                    requirement_index=r_idx,
                    reference_text=ref_p.source_text or reference_answer,
                    requirement_proposition=ref_p,
                    status=info["status"],
                    assigned_student_proposition=info["student_proposition"],
                    fulfillment_method=info["method"],
                    confidence=info["confidence"],
                    score_contribution=info["score_contribution"],
                    explanation=info["explanation"],
                )
            )

        return Experiment5Result(
            variant=self.variant.value,
            question=question,
            reference_answer=reference_answer,
            student_answer=student_answer,
            base_score_raw=base_coverage,
            base_score_effective=effective_base_coverage,
            final_score=final_norm,
            final_grade=final_grade,
            score_result=score_res,
            core_recovery_result=recovery_batch_res,
            recovered_core_count=recovered_core_count,
            guarded_contradiction_count=guarded_contradiction_count,
            reference_requirements=reference_requirements,
            counts=counts,
            metadata={
                "enable_core_recovery": self.enable_core_recovery,
                "enable_canonical_fragments": self.enable_canonical_fragments,
                "enable_contradiction_guards": self.enable_contradiction_guards,
                "scoring_model": self.scoring_model_type,
            },
        )
