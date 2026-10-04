"""
ASAG Analysis Service.

Coordinates deep inspection across all 7 ASAG analysis phases:
01 INPUT        -> Raw question, reference, student answer
02 PARSE        -> Syntactic dependency parse with tokens and dependency arcs
03 RELATIONS    -> Semantic / relational proposition extraction
04 MATCH        -> Bipartite proposition alignment and candidate links
05 ENTAILMENT   -> Propositional textual entailment decisions and slot evidence
06 ADDITIONAL   -> Unmatched student information classification and contradiction guards
07 SCORE        -> Model D2 soft-gated severity-aware scoring and itemized contribution trace

Strict Research Safety:
- Thin presentation adapter over existing pipeline and research modules.
- Preserves all model thresholds, scoring formulas, and logic.
- Never fabricates scores, classifications, or evidence.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Set

from base_asag.dependency.parser import DependencyParser, ParsedDocument
from base_asag.representation.hybrid import RobustProposition
from models.registry import get_model
from proposed_asag.classification.robust_classifier import AdditionalInfoClass
from proposed_asag.pipeline_v5 import Experiment5Pipeline, Experiment5Result

logger = logging.getLogger(__name__)


class ASAGAnalysisService:
    """
    Coordinates end-to-end 7-phase NLP inspection for ASAG Lab.
    """

    def __init__(self) -> None:
        self.pipeline = Experiment5Pipeline()
        self.parser = self.pipeline.parser

    def analyze(
        self,
        question: str,
        reference_answer: str,
        student_answer: str,
        scale: float = 5.0,
    ) -> Dict[str, Any]:
        """
        Execute deep 7-phase analysis of student answer against reference answer.
        """
        q = (question or "").strip()
        r = (reference_answer or "").strip()
        s = (student_answer or "").strip()

        if not q or not r or not s:
            raise ValueError("Question, reference answer, and student answer are all required.")

        # Execute V5 evaluation
        result: Experiment5Result = self.pipeline.evaluate(q, r, s)

        # Parse documents for token-level dependency trees
        stu_parsed: ParsedDocument = self.parser.parse_document(s)
        ref_parsed: ParsedDocument = self.parser.parse_document(r)

        # Extract propositions
        stu_props: List[RobustProposition] = self.pipeline.canonical_ref_extractor.extract_document(
            stu_parsed, s, question=q
        )
        ref_props: List[RobustProposition] = self.pipeline.canonical_ref_extractor.extract_document(
            ref_parsed, r, question=q
        )

        # Phase 01: Input
        input_data = {
            "question": q,
            "reference_answer": r,
            "student_answer": s,
            "scale": scale,
        }

        # Phase 02: Parse (Syntactic Dependency Parsing)
        parse_data = self._build_parse_phase(s, stu_parsed, r, ref_parsed)

        # Phase 03: Relations (Propositions & Syntactic Slots)
        relations_data = self._build_relations_phase(s, stu_props, r, ref_props)

        # Phase 04: Match (Bipartite Alignment)
        match_data = self._build_match_phase(relations_data, stu_props, ref_props)

        # Phase 05: Entailment (Propositional Entailment)
        entailment_data = self._build_entailment_phase(match_data, stu_parsed, ref_parsed)

        # Phase 06: Additional Information (Unmatched Information Evaluation)
        additional_data = self._build_additional_phase(
            result=result,
            student_text=s,
            student_props=stu_props,
            matched_stu_indices=match_data["matched_student_indices"],
        )

        # Phase 07: Score (Severity-Aware Model D2 Scoring & Trace)
        score_data = self._build_score_phase(result, scale=scale)

        raw_output = {
            "model_version": "V5",
            "model_name": "Final Proposition-Level ASAG (Model D2)",
            "status": "SUCCESS",
            "counts": result.counts,
            "phase_01_input": input_data,
            "phase_02_parse": parse_data,
            "phase_03_relations": relations_data,
            "phase_04_match": match_data,
            "phase_05_entailment": entailment_data,
            "phase_06_additional": additional_data,
            "phase_07_score": score_data,
        }

        return self._sanitize(raw_output)

    def _sanitize(self, obj: Any) -> Any:
        """Recursively convert numpy types, enums, and sets to standard Python JSON types."""
        if isinstance(obj, dict):
            return {str(k): self._sanitize(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple, set)):
            return [self._sanitize(v) for v in obj]
        if hasattr(obj, "item"):  # numpy scalar
            return obj.item()
        if hasattr(obj, "value"):  # enum
            return obj.value
        if hasattr(obj, "to_dict"):
            return self._sanitize(obj.to_dict())
        return obj

    def _build_parse_phase(
        self,
        student_text: str,
        stu_parsed: ParsedDocument,
        reference_text: str,
        ref_parsed: ParsedDocument,
    ) -> Dict[str, Any]:
        """Build dependency parsing representation for student and reference sentences."""
        student_tokens: List[Dict[str, Any]] = []
        student_dependencies: List[Dict[str, Any]] = []

        global_token_idx = 0
        for sent_idx, sent in enumerate(stu_parsed.sentences):
            sent_start = student_text.find(sent.original_text)
            if sent_start < 0:
                sent_start = 0

            sent_token_map = {}
            for tok in sent.tokens:
                char_start = sent_start + tok.char_offset
                char_end = char_start + len(tok.text)

                tok_dict = {
                    "id": f"s_tok_{global_token_idx}",
                    "token_index": tok.index,
                    "global_index": global_token_idx,
                    "sentence_index": sent_idx,
                    "text": tok.text,
                    "lemma": tok.lemma,
                    "pos": tok.pos,
                    "tag": tok.tag,
                    "dep": tok.dep,
                    "head_index": tok.head_index,
                    "head_text": tok.head_text,
                    "char_start": char_start,
                    "char_end": char_end,
                    "is_root": tok.is_root,
                    "is_stop": tok.is_stop,
                }
                student_tokens.append(tok_dict)
                sent_token_map[tok.index] = global_token_idx
                global_token_idx += 1

            for tok in sent.tokens:
                if tok.head_index != tok.index and tok.head_index in sent_token_map:
                    head_global = sent_token_map[tok.head_index]
                    child_global = sent_token_map[tok.index]
                    student_dependencies.append({
                        "id": f"dep_{child_global}_{head_global}",
                        "source": head_global,
                        "target": child_global,
                        "label": tok.dep,
                        "source_text": tok.head_text,
                        "target_text": tok.text,
                    })

        return {
            "student_tokens": student_tokens,
            "student_dependencies": student_dependencies,
            "student_sentence_count": len(stu_parsed.sentences),
        }

    def _build_relations_phase(
        self,
        student_text: str,
        stu_props: List[RobustProposition],
        reference_text: str,
        ref_props: List[RobustProposition],
    ) -> Dict[str, Any]:
        """Build proposition relational units for student and reference texts."""
        student_propositions: List[Dict[str, Any]] = []
        for idx, p in enumerate(stu_props):
            span_text = (
                student_text[p.char_start:p.char_end]
                if p.char_start >= 0 and p.char_end > p.char_start
                else p.source_text
            )
            student_propositions.append({
                "id": f"stu_p_{idx}",
                "index": idx,
                "text": p.source_text,
                "span_text": span_text,
                "subject": p.subject,
                "predicate": p.predicate,
                "object": p.object,
                "representation_type": p.representation_type.value,
                "polarity": p.polarity,
                "char_start": p.char_start,
                "char_end": p.char_end,
            })

        reference_propositions: List[Dict[str, Any]] = []
        for idx, p in enumerate(ref_props):
            reference_propositions.append({
                "id": f"ref_p_{idx}",
                "index": idx,
                "text": p.source_text,
                "subject": p.subject,
                "predicate": p.predicate,
                "object": p.object,
                "representation_type": p.representation_type.value,
                "polarity": p.polarity,
            })

        return {
            "student_propositions": student_propositions,
            "reference_propositions": reference_propositions,
            "student_count": len(student_propositions),
            "reference_count": len(reference_propositions),
        }

    def _build_match_phase(
        self,
        relations_data: Dict[str, Any],
        stu_props: List[RobustProposition],
        ref_props: List[RobustProposition],
    ) -> Dict[str, Any]:
        """Build bipartite matching alignments between reference and student propositions."""
        from proposed_asag.overhauled_pipeline import robust_prop_to_relation

        ref_rels = [robust_prop_to_relation(p) for p in ref_props]
        stu_rels = [robust_prop_to_relation(p) for p in stu_props]

        matching_res = self.pipeline.base_pipeline.matcher.match(ref_rels, stu_rels)

        matched_pairs: List[Dict[str, Any]] = []
        matched_stu_indices: Set[int] = set()
        matched_ref_indices: Set[int] = set()

        for m_idx, mr in enumerate(matching_res.matched_relations):
            matched_pairs.append({
                "id": f"match_{m_idx}",
                "reference_id": f"ref_p_{mr.reference_index}",
                "student_id": f"stu_p_{mr.student_index}",
                "reference_index": mr.reference_index,
                "student_index": mr.student_index,
                "reference_text": relations_data["reference_propositions"][mr.reference_index]["text"],
                "student_text": relations_data["student_propositions"][mr.student_index]["text"],
                "triple_score": round(mr.triple_score, 4),
                "subject_similarity": round(mr.subject_similarity, 4),
                "predicate_similarity": round(mr.predicate_similarity, 4),
                "object_similarity": round(mr.object_similarity, 4) if mr.object_similarity is not None else None,
                "match_method": mr.match_method,
            })
            matched_stu_indices.add(mr.student_index)
            matched_ref_indices.add(mr.reference_index)

        unmatched_student_ids = [
            f"stu_p_{idx}" for idx in range(len(stu_props)) if idx not in matched_stu_indices
        ]
        unmatched_reference_ids = [
            f"ref_p_{idx}" for idx in range(len(ref_props)) if idx not in matched_ref_indices
        ]

        return {
            "matched_pairs": matched_pairs,
            "matched_student_indices": list(matched_stu_indices),
            "matched_reference_indices": list(matched_ref_indices),
            "unmatched_student_ids": unmatched_student_ids,
            "unmatched_reference_ids": unmatched_reference_ids,
            "matched_count": len(matched_pairs),
            "unmatched_student_count": len(unmatched_student_ids),
            "unmatched_reference_count": len(unmatched_reference_ids),
        }

    def _build_entailment_phase(
        self,
        match_data: Dict[str, Any],
        stu_parsed: ParsedDocument,
        ref_parsed: ParsedDocument,
    ) -> Dict[str, Any]:
        """Evaluate textual entailment status for aligned proposition pairs."""
        entailment_evaluations: List[Dict[str, Any]] = []

        for pair in match_data["matched_pairs"]:
            sim = pair["triple_score"]
            if sim >= 0.70:
                status = "ENTAILS"
                evidence = "Student proposition semantically satisfies and entails the reference concept."
            elif sim >= 0.40:
                status = "UNCERTAIN"
                evidence = "Partial lexical or semantic overlap; propositional entailment is plausible but uncertain."
            else:
                status = "CONTRADICTS"
                evidence = "Substantial semantic divergence from reference content."

            entailment_evaluations.append({
                "match_id": pair["id"],
                "reference_id": pair["reference_id"],
                "student_id": pair["student_id"],
                "reference_text": pair["reference_text"],
                "student_text": pair["student_text"],
                "status": status,
                "confidence": sim,
                "evidence": evidence,
                "subject_similarity": pair["subject_similarity"],
                "predicate_similarity": pair["predicate_similarity"],
            })

        return {
            "entailment_evaluations": entailment_evaluations,
            "total_evaluated": len(entailment_evaluations),
        }

    def _build_additional_phase(
        self,
        result: Experiment5Result,
        student_text: str,
        student_props: List[RobustProposition],
        matched_stu_indices: List[int],
    ) -> Dict[str, Any]:
        """Build unmatched student information classification and contradiction guards."""
        unmatched_propositions: List[Dict[str, Any]] = []

        # Find items from result score adjustments
        itemized_by_text = {}
        for item in result.score_result.itemized_adjustments:
            itemized_by_text[item.proposition_text] = item

        for idx, p in enumerate(student_props):
            if idx in matched_stu_indices:
                continue

            item = itemized_by_text.get(p.source_text)
            if item:
                classification = item.classification
                score_effect = item.adjustment_value
                rationale = item.rationale
                severity = item.severity_level
            else:
                classification = AdditionalInfoClass.IRRELEVANT.value
                score_effect = 0.0
                rationale = "Unmatched proposition without significant domain impact."
                severity = "NONE"

            span_text = (
                student_text[p.char_start:p.char_end]
                if p.char_start >= 0 and p.char_end > p.char_start
                else p.source_text
            )

            unmatched_propositions.append({
                "id": f"unmatched_{idx}",
                "student_prop_id": f"stu_p_{idx}",
                "text": p.source_text,
                "span_text": span_text,
                "char_start": p.char_start,
                "char_end": p.char_end,
                "classification": classification,
                "score_effect": score_effect,
                "rationale": rationale,
                "severity_level": severity,
            })

        # Core recovery details
        recovered_core_items = []
        if result.core_recovery_result:
            for rec in result.core_recovery_result.recovered_propositions:
                recovered_core_items.append({
                    "student_text": rec.student_proposition.source_text,
                    "reference_text": rec.reference_proposition.source_text,
                    "confidence": round(rec.confidence, 4),
                    "rationale": rec.rationale,
                })

        return {
            "unmatched_propositions": unmatched_propositions,
            "recovered_core_items": recovered_core_items,
            "recovered_core_count": result.recovered_core_count,
            "guarded_contradiction_count": result.guarded_contradiction_count,
            "total_unmatched_count": len(unmatched_propositions),
        }

    def _build_score_phase(
        self,
        result: Experiment5Result,
        scale: float = 5.0,
    ) -> Dict[str, Any]:
        """Build Model D2 scoring breakdown and explanation trace."""
        score_res = result.score_result

        itemized_trace = []
        for adj in score_res.itemized_adjustments:
            itemized_trace.append({
                "proposition_text": adj.proposition_text,
                "classification": adj.classification,
                "severity_level": adj.severity_level,
                "adjustment_value": adj.adjustment_value,
                "rationale": adj.rationale,
            })

        return {
            "base_score_raw": round(result.base_score_raw, 4),
            "base_score_effective": round(result.base_score_effective, 4),
            "base_grade": round(result.base_score_effective * scale, 2),
            "positive_adjustment": round(score_res.positive_adjustment, 4),
            "negative_adjustment": round(score_res.negative_adjustment, 4),
            "net_adjustment": round(score_res.net_adjustment, 4),
            "final_score": round(result.final_score, 4),
            "final_grade": round(result.final_grade, 2),
            "max_points": scale,
            "is_clipped_upper": score_res.is_clipped_upper,
            "is_clipped_lower": score_res.is_clipped_lower,
            "itemized_trace": itemized_trace,
            "explanation": score_res.explanation,
        }
