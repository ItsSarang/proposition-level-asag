"""
Overhauled ASAG Grading Pipeline (System 4).

Coordinates the modular research improvements developed across Phases 1–9:
- Hybrid Proposition Representation (clausal S-P-O + fragments + infinitives + properties)
- Multi-tier Semantic Matching V2 (exact, lemma, WordNet derivation, domain equivalences)
- Global Proposition Matching (Hungarian algorithm bipartite assignment)
- Question-Aware Relevance Analysis (focus terms, question type, concept overlap)
- Property & Antonym Contradiction Detection (polarity mismatch, value conflicts, antonyms)
- Robust 4-step Additional-Information Classification (CORRECT_ADDITIONAL, IRRELEVANT, INCORRECT, UNCERTAIN)
- Bounded Horizontal-Asymptote Scoring (diminishing marginal returns, clipping in [0, 1])
- Deterministic Explanation Trace Generation (structured audit trail)

Maintains full backward-compatible configuration switches for controlled ablation studies (Phase 12).
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Union

from base_asag.dependency.parser import DependencyParser, ParsedDocument
from base_asag.dependency.triples import (
    DependencyRelation,
    DependencyTripleExtractor,
    DocumentTriples,
)
from base_asag.entailment.analyzer import (
    EntailmentResult,
    PropositionalEntailmentAnalyzer,
)
from base_asag.matching.global_matcher import ConfigurableTripleMatcher
from base_asag.matching.triple_matcher import MatchedRelation, MatchingResult, TripleMatcher
from base_asag.representation.hybrid import (
    Modality,
    Polarity,
    PropositionType,
    RobustProposition,
    RobustPropositionExtractor,
)
from base_asag.semantic.relations import LexicalSemanticComparator
from base_asag.semantic.semantic_matcher_v2 import SemanticMatcherV2
from proposed_asag.classification.robust_classifier import (
    AdditionalInfoClass,
    ClassifiedProposition,
    RobustAdditionalInfoClassifier,
    RobustClassificationResult,
)
from proposed_asag.contradiction.property_contradiction import PropertyContradictionDetector
from proposed_asag.explanation.trace_generator import (
    ExplanationTraceGenerator,
    GradingExplanationTrace,
)
from proposed_asag.relevance.question_relevance import QuestionAwareRelevanceAnalyzer
from proposed_asag.scoring.bounded_scorer import (
    BoundedScoreResult,
    BoundedScorer,
    ScoringStrategy,
)


def robust_prop_to_relation(p: RobustProposition) -> DependencyRelation:
    """Convert a RobustProposition to a DependencyRelation for matching."""
    subj = p.subject.strip() if (p.subject and p.subject.strip()) else "it"
    pred = p.predicate.strip() if (p.predicate and p.predicate.strip()) else "be"
    obj = p.object.strip() if (p.object and p.object.strip()) else None

    subj_lemma = p.subject_lemma.strip() if (p.subject_lemma and p.subject_lemma.strip()) else subj.lower()
    pred_lemma = p.predicate_lemma.strip() if (p.predicate_lemma and p.predicate_lemma.strip()) else pred.lower()
    obj_lemma = p.object_lemma.strip() if (p.object_lemma and p.object_lemma.strip()) else (obj.lower() if obj else None)

    rel_type = "SPO" if obj else "SP"
    s_idx = p.token_indices[0] if len(p.token_indices) > 0 else 0
    p_idx = p.token_indices[1] if len(p.token_indices) > 1 else 0
    o_idx = p.token_indices[2] if len(p.token_indices) > 2 else None
    # Propagate extended argument attributes
    raw_prep_args = p.properties.get("prepositional_arguments", ())
    prep_args = []
    for item in raw_prep_args:
        if isinstance(item, (list, tuple)) and len(item) == 2:
            prep_args.append((str(item[0]), str(item[1])))

    pred_mods = tuple(str(x) for x in p.properties.get("predicate_modifiers", p.properties.get("predicate_modifier_lemmas", ())))
    subj_mods = tuple(str(x) for x in p.properties.get("subject_modifiers", ()))
    obj_mods = tuple(str(x) for x in p.properties.get("object_modifiers", ()))
    iobj = p.properties.get("indirect_object")
    iobj_lemma = p.properties.get("indirect_object_lemma")

    return DependencyRelation(
        subject=subj,
        predicate=pred,
        object=obj,
        subject_lemma=subj_lemma,
        predicate_lemma=pred_lemma,
        object_lemma=obj_lemma,
        relation_type=rel_type,
        source_dependency_relations=p.dependency_evidence,
        subject_index=s_idx,
        predicate_index=p_idx,
        object_index=o_idx,
        indirect_object=iobj,
        indirect_object_lemma=iobj_lemma,
        prepositional_arguments=tuple(prep_args),
        predicate_modifiers=pred_mods,
        subject_modifiers=subj_mods,
        object_modifiers=obj_mods,
    )


def relation_to_robust_prop(rel: DependencyRelation, text: str = "") -> RobustProposition:
    """Convert a DependencyRelation to a RobustProposition."""
    src = text or f"{rel.subject} {rel.predicate} {rel.object or ''}".strip()
    return RobustProposition(
        subject=rel.subject,
        predicate=rel.predicate,
        object=rel.object,
        subject_lemma=rel.subject_lemma,
        predicate_lemma=rel.predicate_lemma,
        object_lemma=rel.object_lemma,
        representation_type=PropositionType.TRIPLE,
        polarity=Polarity.POSITIVE,
        modality=Modality.ASSERTED,
        source_text=src,
        char_start=0,
        char_end=len(src),
        sentence_index=0,
        token_indices=(rel.subject_index, rel.predicate_index, rel.object_index or 0),
        dependency_evidence=rel.source_dependency_relations,
    )


@dataclass(frozen=True)
class OverhauledASAGResult:
    """Complete evaluation result for System 4 / Overhauled Proposed ASAG."""
    question: str
    reference_answer: str
    student_answer: str
    base_score_normalized: float
    base_score_scaled: float
    final_score_normalized: float
    final_score_scaled: float
    positive_adjustment: float
    negative_adjustment: float
    net_adjustment: float
    is_clipped_upper: bool
    is_clipped_lower: bool
    correct_additional_count: int
    irrelevant_count: int
    incorrect_count: int
    uncertain_count: int
    matched_propositions_count: int
    reference_propositions_count: int
    unmatched_student_propositions_count: int
    score_result: BoundedScoreResult
    classification_result: Optional[RobustClassificationResult]
    explanation_trace: GradingExplanationTrace
    config: Dict[str, Any]
    direct_matches_count: int = 0
    cross_slot_matches_count: int = 0
    student_propositions_count: int = 0
    entailment_decisions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "question": self.question,
            "reference_answer": self.reference_answer,
            "student_answer": self.student_answer,
            "base_score_normalized": round(self.base_score_normalized, 4),
            "base_score_scaled": round(self.base_score_scaled, 4),
            "final_score_normalized": round(self.final_score_normalized, 4),
            "final_score_scaled": round(self.final_score_scaled, 4),
            "positive_adjustment": round(self.positive_adjustment, 4),
            "negative_adjustment": round(self.negative_adjustment, 4),
            "net_adjustment": round(self.net_adjustment, 4),
            "is_clipped_upper": self.is_clipped_upper,
            "is_clipped_lower": self.is_clipped_lower,
            "counts": {
                "correct_additional": self.correct_additional_count,
                "irrelevant": self.irrelevant_count,
                "incorrect": self.incorrect_count,
                "uncertain": self.uncertain_count,
                "matched": self.matched_propositions_count,
                "reference_total": self.reference_propositions_count,
                "unmatched_student": self.unmatched_student_propositions_count,
                "direct_matches": self.direct_matches_count,
                "cross_slot_matches": self.cross_slot_matches_count,
                "student_total": self.student_propositions_count,
            },
            "entailment_decisions": list(self.entailment_decisions),
            "score_result": self.score_result.to_dict(),
            "classification_result": self.classification_result.to_dict() if self.classification_result else None,
            "explanation_trace": self.explanation_trace.to_dict(),
            "config": self.config,
        }


class OverhauledASAGPipeline:
    """
    Modular, end-to-end overhauled ASAG grading engine.
    """

    def __init__(
        self,
        use_hybrid_representation: bool = True,
        semantic_matcher_version: str = "v2",
        matching_strategy: str = "global",
        use_question_relevance: bool = True,
        use_property_contradiction: bool = True,
        scoring_strategy: ScoringStrategy = ScoringStrategy.SATURATING,
        enable_proposed_scoring: bool = True,
        use_domain_equivalence: bool = True,
        alignment_threshold: float = 0.50,
        max_positive_bonus: float = 0.30,
        max_negative_penalty: float = 0.40,
        diminishing_rate: float = 0.50,
        scale: float = 5.0,
    ) -> None:
        self.use_hybrid_representation = use_hybrid_representation
        self.semantic_matcher_version = semantic_matcher_version
        self.matching_strategy = matching_strategy
        self.use_question_relevance = use_question_relevance
        self.use_property_contradiction = use_property_contradiction
        self.scoring_strategy = scoring_strategy
        self.enable_proposed_scoring = enable_proposed_scoring
        self.use_domain_equivalence = use_domain_equivalence
        self.alignment_threshold = alignment_threshold
        self.scale = scale

        # Linguistic parser
        self.parser = DependencyParser()

        # Extractors
        self.clausal_extractor = DependencyTripleExtractor()
        self.hybrid_extractor = RobustPropositionExtractor()

        # Semantic comparator
        if semantic_matcher_version == "v2":
            self.comparator = SemanticMatcherV2(use_domain_equivalence=use_domain_equivalence)
        else:
            self.comparator = LexicalSemanticComparator()

        # Matcher
        self.matcher = ConfigurableTripleMatcher(
            comparator=self.comparator,
            threshold=alignment_threshold,
            matching_strategy=matching_strategy,
            enable_cross_slot=True,
        )
        self.direct_matcher = TripleMatcher(
            comparator=self.comparator,
            alignment_threshold=alignment_threshold,
            enable_cross_slot=False,
        )

        # Entailment analyzer
        self.entailment_analyzer = PropositionalEntailmentAnalyzer()

        # Relevance analyzer
        self.relevance_analyzer = QuestionAwareRelevanceAnalyzer(
            relevance_threshold=0.35,
        )

        # Contradiction detector
        self.contradiction_detector = PropertyContradictionDetector()

        # Additional information classifier
        self.classifier = RobustAdditionalInfoClassifier(
            relevance_threshold=0.35,
            sufficiency_threshold=0.40,
            relevance_analyzer=self.relevance_analyzer if use_question_relevance else None,
            contradiction_detector=self.contradiction_detector if use_property_contradiction else None,
        )

        # Bounded scorer
        self.bounded_scorer = BoundedScorer(
            strategy=scoring_strategy,
            max_positive_bonus=max_positive_bonus,
            max_negative_penalty=max_negative_penalty,
            diminishing_rate=diminishing_rate,
        )

        # Explanation generator
        self.trace_generator = ExplanationTraceGenerator(default_scale=scale)

    def evaluate(
        self,
        question: str,
        reference_answer: str,
        student_answer: str,
    ) -> OverhauledASAGResult:
        """
        Execute full end-to-end evaluation with intermediate trace preservation.
        """
        config = {
            "use_hybrid_representation": self.use_hybrid_representation,
            "semantic_matcher_version": self.semantic_matcher_version,
            "matching_strategy": self.matching_strategy,
            "use_question_relevance": self.use_question_relevance,
            "use_property_contradiction": self.use_property_contradiction,
            "scoring_strategy": self.scoring_strategy.value,
            "enable_proposed_scoring": self.enable_proposed_scoring,
            "use_domain_equivalence": self.use_domain_equivalence,
            "alignment_threshold": self.alignment_threshold,
            "scale": self.scale,
        }

        # 1. Parse texts
        ref_parsed = self.parser.parse_document(reference_answer)
        stu_parsed = self.parser.parse_document(student_answer)

        # 2. Extract propositions
        if self.use_hybrid_representation:
            ref_props = self.hybrid_extractor.extract_document(ref_parsed, reference_answer)
            stu_props = self.hybrid_extractor.extract_document(stu_parsed, student_answer)
            ref_relations = [robust_prop_to_relation(p) for p in ref_props]
            stu_relations = [robust_prop_to_relation(p) for p in stu_props]
        else:
            ref_triples = self.clausal_extractor.extract_document(ref_parsed)
            stu_triples = self.clausal_extractor.extract_document(stu_parsed)
            ref_relations = ref_triples.canonical_relations
            stu_relations = stu_triples.canonical_relations
            ref_props = [relation_to_robust_prop(r) for r in ref_relations]
            stu_props = [relation_to_robust_prop(r) for r in stu_relations]

        # 3. Match reference and student relations
        matching_res = self.matcher.match(ref_relations, stu_relations)

        # 4. Entailment & Base Scoring
        n_ref = len(ref_relations)
        matched_items_evidence: List[Dict[str, Any]] = []
        base_coverage = 0.0

        if n_ref > 0:
            entail_res_list = self.entailment_analyzer.evaluate_matching_result(
                matching_res, ref_parsed, stu_parsed
            )
            for matched, entail_res in zip(matching_res.matched_relations, entail_res_list):
                status = entail_res.relation
                weight = 1.0 if status == "ENTAILS" else (0.5 if status == "UNCERTAIN" else 0.0)
                base_coverage += (weight * matched.triple_score) / n_ref

                ref_str = f"{matched.reference_relation.subject} {matched.reference_relation.predicate} {matched.reference_relation.object or ''}".strip()
                stu_str = f"{matched.student_relation.subject} {matched.student_relation.predicate} {matched.student_relation.object or ''}".strip()
                matched_items_evidence.append({
                    "reference_statement": ref_str,
                    "student_statement": stu_str,
                    "match_score": matched.triple_score,
                    "entailment_status": status,
                    "evidence_summary": f"Matched via {self.matching_strategy} ({matched.triple_score:.2f})",
                })
        else:
            # When reference has 0 propositions even after extraction
            base_coverage = 0.0

        # Determine direct vs cross-slot matches
        direct_matches_count = 0
        cross_slot_matches_count = 0
        for matched in matching_res.matched_relations:
            s_d, o_d, p_d, _ = self.direct_matcher.compare_slots(matched.reference_relation, matched.student_relation)
            is_sp = (matched.reference_relation.object is None and matched.student_relation.object is None)
            d_score = self.direct_matcher.compute_triple_score(s_d, p_d, o_d, is_sp)
            if matched.triple_score > d_score + 1e-4:
                cross_slot_matches_count += 1
            else:
                direct_matches_count += 1

        entailment_decisions = [e.relation for e in entail_res_list] if n_ref > 0 else []

        base_score_norm = min(1.0, max(0.0, base_coverage))
        base_score_scaled = base_score_norm * self.scale

        # Identify matched student indices
        matched_stu_indices = {m.student_index for m in matching_res.matched_relations}
        matched_student_props = [
            stu_props[i] for i in range(len(stu_props)) if i in matched_stu_indices
        ]
        unmatched_student_props = [
            stu_props[i] for i in range(len(stu_props)) if i not in matched_stu_indices
        ]

        # 5. Classify unmatched student propositions
        classification_res: Optional[RobustClassificationResult] = None
        if self.enable_proposed_scoring and len(unmatched_student_props) > 0:
            classification_res = self.classifier.classify_propositions(
                question=question,
                reference_answer=reference_answer,
                student_answer=student_answer,
                unmatched_student_props=unmatched_student_props,
                matched_student_props=matched_student_props,
                reference_props=ref_props,
            )

        # 6. Bounded scoring
        if self.enable_proposed_scoring and classification_res is not None:
            score_res = self.bounded_scorer.score(
                base_score=base_score_norm,
                classification_result=classification_res,
            )
        else:
            # Base ASAG score only
            score_res = BoundedScoreResult(
                base_score=base_score_norm,
                net_adjustment=0.0,
                final_score=base_score_norm,
                strategy=self.scoring_strategy,
                positive_adjustment=0.0,
                negative_adjustment=0.0,
                is_clipped_upper=False,
                is_clipped_lower=False,
                correct_additional_count=0,
                irrelevant_count=0,
                incorrect_count=0,
                uncertain_count=0,
                adjustment_records=[],
                explanation="Base ASAG only (no additional-info adjustments applied).",
            )

        final_norm = score_res.final_score
        final_scaled = final_norm * self.scale

        # 7. Generate explanation trace
        trace = self.trace_generator.generate_trace(
            question=question,
            reference_answer=reference_answer,
            student_answer=student_answer,
            score_result=score_res,
            classification_result=classification_res,
            matched_evidence=matched_items_evidence,
            scale=self.scale,
        )

        return OverhauledASAGResult(
            question=question,
            reference_answer=reference_answer,
            student_answer=student_answer,
            base_score_normalized=base_score_norm,
            base_score_scaled=base_score_scaled,
            final_score_normalized=final_norm,
            final_score_scaled=final_scaled,
            positive_adjustment=score_res.positive_adjustment,
            negative_adjustment=score_res.negative_adjustment,
            net_adjustment=score_res.net_adjustment,
            is_clipped_upper=score_res.is_clipped_upper,
            is_clipped_lower=score_res.is_clipped_lower,
            correct_additional_count=score_res.correct_additional_count,
            irrelevant_count=score_res.irrelevant_count,
            incorrect_count=score_res.incorrect_count,
            uncertain_count=score_res.uncertain_count,
            matched_propositions_count=len(matching_res.matched_relations),
            reference_propositions_count=n_ref,
            unmatched_student_propositions_count=len(unmatched_student_props),
            score_result=score_res,
            classification_result=classification_res,
            explanation_trace=trace,
            config=config,
            direct_matches_count=direct_matches_count,
            cross_slot_matches_count=cross_slot_matches_count,
            student_propositions_count=len(stu_props),
            entailment_decisions=entailment_decisions,
        )
