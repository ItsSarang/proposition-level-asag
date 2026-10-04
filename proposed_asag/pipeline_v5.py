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
)


class Experiment5Variant(str, Enum):
    """Experimental variants for Experiment 5 evaluation and ablation."""
    V4 = "V4"        # Frozen Experiment 4
    V5_A = "V5-A"    # Core Paraphrase + Non-sentential Fragments + Model D
    V5_B = "V5-B"    # V5-A + Contradiction Guards + Model D
    V5_C = "V5-C"    # Frozen Exp 4 Upstream + Model D2
    V5 = "V5"        # Full System: V5-A + V5-B + Model D2


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
    ) -> None:
        if isinstance(variant, str):
            variant = Experiment5Variant(variant)
        self.variant = variant

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

        if n_ref > 0:
            entail_res_list = self.base_pipeline.entailment_analyzer.evaluate_matching_result(
                matching_res, ref_parsed, stu_parsed
            )
            for matched, entail_res in zip(matching_res.matched_relations, entail_res_list):
                status = entail_res.relation
                weight = 1.0 if status == "ENTAILS" else (0.5 if status == "UNCERTAIN" else 0.0)
                base_coverage += (weight * matched.triple_score) / n_ref
                matched_ref_indices.add(matched.reference_index)
                matched_stu_indices.add(matched.student_index)

        # Identify initially unmatched student propositions
        unmatched_stu_props = [
            stu_props[i] for i in range(len(stu_props)) if i not in matched_stu_indices
        ]
        matched_stu_props = [
            stu_props[i] for i in range(len(stu_props)) if i in matched_stu_indices
        ]

        # 5. Core Paraphrase Recovery (Part A)
        recovery_batch_res: Optional[CoreRecoveryBatchResult] = None
        recovered_core_count = 0
        effective_base_coverage = base_coverage

        if self.enable_core_recovery and len(unmatched_stu_props) > 0 and n_ref > 0:
            recovery_batch_res = self.core_recoverer.recover(
                unmatched_student_props=unmatched_stu_props,
                reference_props=ref_props,
                matched_reference_indices=matched_ref_indices,
                question=question,
                reference_answer=reference_answer,
                student_answer=student_answer,
            )
            recovered_core_count = recovery_batch_res.recovered_count
            for rec in recovery_batch_res.recovered_propositions:
                # Add recovered core proposition to base coverage
                effective_base_coverage += (rec.confidence * 1.0) / n_ref
                matched_stu_props.append(rec.student_proposition)

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
                matched_student_props=matched_stu_props,
                reference_props=ref_props,
            )
            classified_props = list(raw_class_res.classified_propositions)

        # 7. Contradiction Guards (Part C)
        guarded_contradiction_count = 0
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

        # Add matched propositions as MATCHED_BY_BASE_ASAG
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
                    verification_evidence=None,
                )
            )
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
            counts=counts,
            metadata={
                "enable_core_recovery": self.enable_core_recovery,
                "enable_canonical_fragments": self.enable_canonical_fragments,
                "enable_contradiction_guards": self.enable_contradiction_guards,
                "scoring_model": self.scoring_model_type,
            },
        )
