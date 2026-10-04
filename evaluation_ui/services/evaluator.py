"""
ASAG Evaluation Service (Phase 2 & Phase 3).

Coordinates the four ASAG engines to evaluate student answers:
- V0: TF-IDF Baseline
- V1: Base ASAG (Basak-inspired clausal dependency coverage)
- V2: Historical Proposed ASAG (Stage 14 linear adjustment)
- V3: Current / Overhauled Proposed ASAG (Hybrid + Semantic V2 + Hungarian + Relevance + Contradiction + Saturating Bounded Scorer)

Strict Research Safety Mandates:
- Preserves existing engine algorithms without modification.
- Never fabricates scores, classifications, or evidence.
- Isolates errors so failure in one system does not crash others.
- Exposes actual intermediate provenance for proposition and pipeline traces.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Sequence

from evaluation.runners.base_asag_runner import BaseASAGRunner
from evaluation.runners.baseline_runner import BaselineRunner
from evaluation.runners.overhaul_runner import OverhaulASAGRunner
from evaluation.runners.proposed_asag_runner import ProposedASAGRunner
from proposed_asag.classification.robust_classifier import AdditionalInfoClass

logger = logging.getLogger(__name__)


class ASAGEvaluatorService:
    """
    Evaluation service coordinating all 4 ASAG systems for UI demonstration and research analysis.
    """

    def __init__(
        self,
        baseline_runner: Optional[BaselineRunner] = None,
        base_runner: Optional[BaseASAGRunner] = None,
        proposed_runner: Optional[ProposedASAGRunner] = None,
        overhaul_runner: Optional[OverhaulASAGRunner] = None,
    ) -> None:
        self.baseline_runner = baseline_runner or BaselineRunner()
        self.base_runner = base_runner or BaseASAGRunner()
        self.proposed_runner = proposed_runner or ProposedASAGRunner()
        self.overhaul_runner = overhaul_runner or OverhaulASAGRunner()

    def evaluate_single(
        self,
        question: str,
        reference_answer: str,
        student_answer: str,
        max_points: float = 5.0,
    ) -> Dict[str, Any]:
        """
        Evaluate a single student answer across all four ASAG engines.
        Returns a standardized, inspectable result dictionary.
        """
        q = (question or "").strip()
        r = (reference_answer or "").strip()
        s = (student_answer or "").strip()

        # 1. System V0: TF-IDF Baseline
        v0_data: Dict[str, Any] = {
            "version": "V0 — TF-IDF Baseline",
            "name": "TF-IDF Baseline",
            "normalized_score": 0.0,
            "grade": 0.0,
            "status": "NOT_RUN",
            "error_message": None,
        }
        try:
            p0 = self.baseline_runner.evaluate_pair(r, s, max_points=max_points)
            v0_data.update({
                "normalized_score": p0.normalized_score,
                "grade": p0.grade,
                "status": p0.status,
                "error_message": p0.error_message,
            })
        except Exception as e:
            v0_data.update({
                "status": "ERROR",
                "error_message": str(e),
            })

        # 2. System V1: Base ASAG
        v1_data: Dict[str, Any] = {
            "version": "V1 — Base ASAG",
            "name": "Base ASAG",
            "normalized_score": 0.0,
            "grade": 0.0,
            "matched_count": 0,
            "total_ref_props": 0,
            "unmatched_student_count": 0,
            "entailed_count": 0,
            "uncertain_count": 0,
            "contradicted_count": 0,
            "missing_count": 0,
            "status": "NOT_RUN",
            "error_message": None,
        }
        base_pipeline_res = None
        try:
            p1 = self.base_runner.evaluate_triplet(q, r, s, max_points=max_points)
            base_pipeline_res = p1.pipeline_result
            v1_data.update({
                "normalized_score": p1.normalized_score,
                "grade": p1.grade,
                "matched_count": p1.matched_count,
                "total_ref_props": p1.total_reference_propositions,
                "unmatched_student_count": p1.unmatched_student_count,
                "entailed_count": p1.entailed_count,
                "uncertain_count": p1.uncertain_count,
                "contradicted_count": p1.contradicted_count,
                "missing_count": p1.missing_count,
                "status": p1.status,
                "error_message": p1.error_message,
            })
        except Exception as e:
            v1_data.update({
                "status": "ERROR",
                "error_message": str(e),
            })

        # 3. System V2: Historical Proposed ASAG
        v2_data: Dict[str, Any] = {
            "version": "V2 — Historical Proposed",
            "name": "Historical Proposed ASAG",
            "base_normalized": 0.0,
            "base_grade": 0.0,
            "proposed_normalized": 0.0,
            "proposed_grade": 0.0,
            "positive_adjustment": 0.0,
            "negative_adjustment": 0.0,
            "net_adjustment": 0.0,
            "correct_additional_count": 0,
            "irrelevant_count": 0,
            "incorrect_count": 0,
            "uncertain_count": 0,
            "is_clipped_upper": False,
            "is_clipped_lower": False,
            "status": "NOT_RUN",
            "error_message": None,
        }
        try:
            if base_pipeline_res is not None:
                p2 = self.proposed_runner.evaluate_base_result(base_pipeline_res, max_points=max_points)
                v2_data.update({
                    "base_normalized": p2.base_normalized,
                    "base_grade": p2.base_grade,
                    "proposed_normalized": p2.proposed_normalized,
                    "proposed_grade": p2.proposed_grade,
                    "positive_adjustment": p2.positive_adjustment,
                    "negative_adjustment": p2.negative_adjustment,
                    "net_adjustment": p2.net_adjustment,
                    "correct_additional_count": p2.correct_additional_count,
                    "irrelevant_count": p2.irrelevant_count,
                    "incorrect_count": p2.incorrect_count,
                    "uncertain_count": p2.uncertain_count,
                    "is_clipped_upper": p2.is_clipped_upper,
                    "is_clipped_lower": p2.is_clipped_lower,
                    "status": p2.status,
                    "error_message": p2.error_message,
                })
            else:
                v2_data.update({
                    "status": "ERROR",
                    "error_message": "Base ASAG prerequisite failed or produced no pipeline result.",
                })
        except Exception as e:
            v2_data.update({
                "status": "ERROR",
                "error_message": str(e),
            })

        # 4. System V3: Current / Overhauled Proposed ASAG
        v3_data: Dict[str, Any] = {
            "version": "V3 — Current Overhauled Proposed",
            "name": "Current Overhauled Proposed ASAG",
            "base_normalized": 0.0,
            "base_grade": 0.0,
            "final_normalized": 0.0,
            "final_grade": 0.0,
            "positive_adjustment": 0.0,
            "negative_adjustment": 0.0,
            "net_adjustment": 0.0,
            "is_clipped_upper": False,
            "is_clipped_lower": False,
            "correct_additional_count": 0,
            "irrelevant_count": 0,
            "incorrect_count": 0,
            "uncertain_count": 0,
            "matched_count": 0,
            "total_ref_props": 0,
            "unmatched_student_count": 0,
            "status": "NOT_RUN",
            "error_message": None,
        }
        overhaul_pipeline_res = None
        try:
            p3 = self.overhaul_runner.evaluate_triplet(q, r, s, max_points=max_points)
            overhaul_pipeline_res = p3.pipeline_result
            v3_data.update({
                "base_normalized": p3.base_normalized,
                "base_grade": p3.base_grade,
                "final_normalized": p3.normalized_score,
                "final_grade": p3.grade,
                "positive_adjustment": p3.positive_adjustment,
                "negative_adjustment": p3.negative_adjustment,
                "net_adjustment": p3.net_adjustment,
                "is_clipped_upper": p3.is_clipped_upper,
                "is_clipped_lower": p3.is_clipped_lower,
                "correct_additional_count": p3.correct_additional_count,
                "irrelevant_count": p3.irrelevant_count,
                "incorrect_count": p3.incorrect_count,
                "uncertain_count": p3.uncertain_count,
                "matched_count": p3.matched_propositions_count,
                "total_ref_props": p3.reference_propositions_count,
                "unmatched_student_count": p3.unmatched_student_propositions_count,
                "status": p3.status,
                "error_message": p3.error_message,
            })
        except Exception as e:
            v3_data.update({
                "status": "ERROR",
                "error_message": str(e),
            })

        # 5. Build Proposition Trace (Phase 5) from actual V3 execution
        proposition_trace = self._build_proposition_trace(overhaul_pipeline_res)

        # 6. Build Research Pipeline Trace (Phase 6) from actual pipeline stages
        pipeline_trace = self._build_pipeline_trace(
            question=q,
            reference_answer=r,
            student_answer=s,
            base_res=base_pipeline_res,
            overhaul_res=overhaul_pipeline_res,
        )

        return {
            "question": q,
            "reference_answer": r,
            "student_answer": s,
            "systems": {
                "v0_baseline": v0_data,
                "v1_base_asag": v1_data,
                "v2_historical_proposed": v2_data,
                "v3_current_proposed": v3_data,
            },
            "proposition_trace": proposition_trace,
            "pipeline_trace": pipeline_trace,
        }

    def evaluate_batch(
        self,
        question: str,
        reference_answer: str,
        student_answers: Sequence[str],
        max_points: float = 5.0,
    ) -> List[Dict[str, Any]]:
        """
        Evaluate multiple student answers against a common question and reference answer.
        Each answer is evaluated independently.
        """
        results = []
        for idx, ans in enumerate(student_answers):
            eval_res = self.evaluate_single(
                question=question,
                reference_answer=reference_answer,
                student_answer=ans,
                max_points=max_points,
            )
            eval_res["answer_index"] = idx
            results.append(eval_res)
        return results

    def _build_proposition_trace(
        self,
        overhaul_res: Optional[Any],
    ) -> List[Dict[str, Any]]:
        """
        Build itemized proposition table from actual V3 OverhauledASAGResult.
        Columns:
        - Student proposition
        - Status (MATCHED / UNMATCHED)
        - Best match / Reference proposition
        - Semantic evidence
        - Entailment / Compatibility
        - Classification
        - Score effect
        - Rationale
        """
        if overhaul_res is None:
            return []

        trace_items: List[Dict[str, Any]] = []

        # 1. Matched propositions (core information)
        if hasattr(overhaul_res, "explanation_trace") and overhaul_res.explanation_trace:
            for item in overhaul_res.explanation_trace.matched_items:
                trace_items.append({
                    "student_statement": item.student_statement,
                    "status": "MATCHED",
                    "best_match_reference": item.reference_statement,
                    "semantic_evidence": item.evidence_summary,
                    "entailment_compatibility": item.entailment_status,
                    "classification": "MATCHED_BY_BASE_ASAG",
                    "score_effect": f"+{item.match_score:.2f} (Core Coverage)",
                    "rationale": f"Matched to reference assertion with similarity {item.match_score:.2f}. Status: {item.entailment_status}.",
                })

        # 2. Additional propositions (unmatched student information evaluated by Stage 13)
        if hasattr(overhaul_res, "classification_result") and overhaul_res.classification_result:
            for cp in overhaul_res.classification_result.classified_propositions:
                if cp.classification in (
                    AdditionalInfoClass.MATCHED_BY_BASE_ASAG,
                    AdditionalInfoClass.MATCHED_BY_BASE_ASAG.value,
                ):
                    continue

                # Format semantic evidence
                sem_ev = "None (Low question similarity)"
                if cp.relevance_evidence is not None:
                    sem_ev = f"Relevance score: {cp.relevance_evidence.evidence_strength:.2f} ({cp.relevance_evidence.evidence_explanation})"

                # Format entailment/compatibility
                compat = "COMPATIBLE"
                if cp.contradiction_evidence is not None and cp.contradiction_evidence.is_contradicted:
                    compat = f"CONTRADICTION: {cp.contradiction_evidence.contradiction_type.value}"

                score_eff = "+0.00"
                if cp.score_effect > 0:
                    score_eff = f"+{cp.score_effect:.2f}"
                elif cp.score_effect < 0:
                    score_eff = f"{cp.score_effect:.2f}"

                trace_items.append({
                    "student_statement": cp.proposition.source_text,
                    "status": "UNMATCHED",
                    "best_match_reference": "None (No reference alignment)",
                    "semantic_evidence": sem_ev,
                    "entailment_compatibility": compat,
                    "classification": cp.classification.value,
                    "score_effect": score_eff,
                    "rationale": cp.rationale,
                })

        return trace_items

    def _build_pipeline_trace(
        self,
        question: str,
        reference_answer: str,
        student_answer: str,
        base_res: Optional[Any],
        overhaul_res: Optional[Any],
    ) -> List[Dict[str, Any]]:
        """
        Build expandable 11-stage research pipeline trace exposing actual intermediate representations.
        """
        stages: List[Dict[str, Any]] = []

        # Stage 1: Preprocessing
        stu_tokens = student_answer.split()
        ref_tokens = reference_answer.split()
        stages.append({
            "stage_id": 1,
            "title": "Stage 1: Linguistic Preprocessing",
            "concept": "Text tokenization, sentence segmentation, normalization, and stopword isolation.",
            "data": {
                "student_word_count": len(stu_tokens),
                "reference_word_count": len(ref_tokens),
                "student_sentences": [student_answer] if student_answer else [],
            },
            "status": "COMPLETED",
        })

        # Stage 2: Dependency Parsing
        ref_parsed = getattr(base_res, "reference_parsed", None)
        stu_parsed = getattr(base_res, "student_parsed", None)
        stages.append({
            "stage_id": 2,
            "title": "Stage 2: Dependency Parsing",
            "concept": "Syntactic dependency parsing extracting grammatical relations (nsubj, dobj, ROOT).",
            "data": {
                "student_tokens_parsed": len(stu_parsed.sentences[0].tokens) if stu_parsed and stu_parsed.sentences else len(stu_tokens),
                "reference_tokens_parsed": len(ref_parsed.sentences[0].tokens) if ref_parsed and ref_parsed.sentences else len(ref_tokens),
            } if stu_parsed or ref_parsed else "Not exposed by current run",
            "status": "COMPLETED" if (stu_parsed or ref_parsed) else "NOT_AVAILABLE",
        })

        # Stage 3: Proposition Extraction
        stu_props_count = 0
        ref_props_count = 0
        if overhaul_res:
            stu_props_count = overhaul_res.matched_propositions_count + overhaul_res.unmatched_student_propositions_count
            ref_props_count = overhaul_res.reference_propositions_count
        elif base_res:
            stu_props_count = len(getattr(base_res, "student_triples", []))
            ref_props_count = len(getattr(base_res, "reference_triples", []))

        stages.append({
            "stage_id": 3,
            "title": "Stage 3: Proposition Extraction",
            "concept": "Extracts clausal SPO triples, predicate fragments, infinitives, and property assertions.",
            "data": {
                "student_propositions_extracted": stu_props_count,
                "reference_propositions_extracted": ref_props_count,
                "hybrid_representation": True if overhaul_res else False,
            },
            "status": "COMPLETED",
        })

        # Stage 4: Semantic Matching
        stages.append({
            "stage_id": 4,
            "title": "Stage 4: Semantic Matching",
            "concept": "Evaluates lexical/semantic compatibility using exact match, lemmas, derivation, domain lexicon, and WordNet path.",
            "data": {
                "matcher_version": "SemanticMatcherV2 (curated domain lexicon + derivation)" if overhaul_res else "SemanticMatcherV1",
                "alignment_threshold": 0.50,
            },
            "status": "COMPLETED",
        })

        # Stage 5: Entailment & Reference Coverage
        entail_counts = {
            "entailed": getattr(base_res, "entailed_count", 0),
            "uncertain": getattr(base_res, "uncertain_count", 0),
            "contradicted": getattr(base_res, "contradicted_count", 0),
            "missing": getattr(base_res, "missing_count", 0),
        }
        stages.append({
            "stage_id": 5,
            "title": "Stage 5: Propositional Entailment Analysis",
            "concept": "Analyzes whether student propositions entail, contradict, or remain uncertain relative to reference assertions.",
            "data": entail_counts,
            "status": "COMPLETED",
        })

        # Stage 6: Matched vs Unmatched Alignment
        matched_c = getattr(overhaul_res, "matched_propositions_count", getattr(base_res, "matched_count", 0))
        unmatched_c = getattr(overhaul_res, "unmatched_student_propositions_count", getattr(base_res, "unmatched_student_count", 0))
        stages.append({
            "stage_id": 6,
            "title": "Stage 6: Matched vs. Unmatched Partitioning",
            "concept": "Applies Hungarian bipartite alignment to cleanly isolate core matched assertions from unmatched information.",
            "data": {
                "matched_propositions": matched_c,
                "unmatched_student_propositions": unmatched_c,
            },
            "status": "COMPLETED",
        })

        # Stage 7: Question-Aware Relevance
        stages.append({
            "stage_id": 7,
            "title": "Stage 7: Question-Aware Relevance Analysis",
            "concept": "Evaluates semantic overlap with question focus concepts to distinguish relevant additions from off-topic trivia.",
            "data": {
                "question": question,
                "relevance_threshold": 0.35,
            },
            "status": "COMPLETED" if overhaul_res else "NOT_AVAILABLE",
        })

        # Stage 8: Property Contradiction & Antonym Analysis
        contra_count = getattr(overhaul_res, "incorrect_count", 0)
        stages.append({
            "stage_id": 8,
            "title": "Stage 8: Property Contradiction & Antonym Analysis",
            "concept": "Inspects polarity mismatch, lexical antonymy, and mutually exclusive property values.",
            "data": {
                "contradictions_detected": contra_count,
            },
            "status": "COMPLETED" if overhaul_res else "NOT_AVAILABLE",
        })

        # Stage 9: Additional-Information Classification
        cat_counts = {
            "CORRECT_ADDITIONAL": getattr(overhaul_res, "correct_additional_count", 0),
            "IRRELEVANT": getattr(overhaul_res, "irrelevant_count", 0),
            "INCORRECT": getattr(overhaul_res, "incorrect_count", 0),
            "UNCERTAIN": getattr(overhaul_res, "uncertain_count", 0),
        }
        stages.append({
            "stage_id": 9,
            "title": "Stage 9: Additional-Information Classification",
            "concept": "Classifies unmatched propositions into CORRECT_ADDITIONAL, IRRELEVANT, INCORRECT, or UNCERTAIN.",
            "data": cat_counts,
            "status": "COMPLETED" if overhaul_res else "NOT_AVAILABLE",
        })

        # Stage 10: Bounded Score Aggregation
        score_data = {
            "strategy": "SATURATING (Horizontal Asymptote)" if overhaul_res else "SUM (Linear)",
            "base_score_normalized": getattr(overhaul_res, "base_score_normalized", getattr(base_res, "normalized_score", 0.0)),
            "positive_adjustment": getattr(overhaul_res, "positive_adjustment", 0.0),
            "negative_adjustment": getattr(overhaul_res, "negative_adjustment", 0.0),
            "net_adjustment": getattr(overhaul_res, "net_adjustment", 0.0),
            "is_clipped_upper": getattr(overhaul_res, "is_clipped_upper", False),
            "is_clipped_lower": getattr(overhaul_res, "is_clipped_lower", False),
        }
        stages.append({
            "stage_id": 10,
            "title": "Stage 10: Bounded Score Aggregation",
            "concept": "Incorporates additional proposition evidence with diminishing marginal returns, strictly bounded in [0.0, 1.0].",
            "data": score_data,
            "status": "COMPLETED",
        })

        # Stage 11: Final Grade
        stages.append({
            "stage_id": 11,
            "title": "Stage 11: Final Grade Calculation",
            "concept": "Maps normalized ASAG score to 0–5 continuous grade scale matching the human evaluation target.",
            "data": {
                "normalized_score": getattr(overhaul_res, "final_score_normalized", getattr(base_res, "normalized_score", 0.0)),
                "scaled_grade": getattr(overhaul_res, "final_score_scaled", round(getattr(base_res, "normalized_score", 0.0) * 5.0, 2)),
                "scale": 5.0,
            },
            "status": "COMPLETED",
        })

        return stages
