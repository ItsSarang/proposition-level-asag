"""
Results models, observation deriver, and tabular formatters for ASAG Lab.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from base_asag.pipeline import BaseASAGPipelineResult


def derive_system_observation(p_res: BaseASAGPipelineResult) -> str:
    """
    Derive an objective system observation strictly from Base ASAG diagnostic metrics.

    IMPORTANT RESEARCH INTEGRITY RULE:
    Do NOT claim qualitative categories such as 'Correct', 'Incorrect', 'Paraphrase',
    or 'Irrelevant' which are reserved for the proposed extension (Stages 11–14).
    Only report observable structural facts computed by Base ASAG.
    """
    total_ref = p_res.total_reference_propositions
    missing = p_res.missing_count
    entailed = p_res.entailed_count
    uncertain = p_res.uncertain_count
    contradicted = p_res.contradicted_count
    unmatched_stu = p_res.unmatched_student_count

    if contradicted > 0:
        if unmatched_stu > 0:
            return "Contradiction detected; additional student information detected (not evaluated)"
        return "Contradiction detected (negation/incompatible relation)"

    if total_ref > 0 and missing == total_ref:
        if unmatched_stu > 0:
            return "Missing reference information; unaligned student content detected"
        return "Missing reference information (no alignment with reference)"

    if missing > 0:
        if unmatched_stu > 0:
            return "Reference partially covered; additional student information detected (not classified)"
        return "Reference information partially covered"

    if uncertain > 0:
        if unmatched_stu > 0:
            return "Reference covered with uncertain semantics; additional student information detected"
        return "Reference covered with uncertain semantic alignment"

    # Fully covered (missing == 0, contradicted == 0, uncertain == 0, entailed == total_ref)
    if unmatched_stu > 0:
        return "Core reference covered; additional student information detected (not classified by Base ASAG)"
    return "Core reference information covered"


@dataclass(frozen=True)
class SingleEvaluationRecord:
    """Structured evaluation record for a single student answer."""
    answer_id: str
    student_answer: str
    tfidf_score: float
    base_asag_score: float
    matched_count: int
    missing_reference_count: int
    unmatched_student_count: int
    entails_count: int
    uncertain_count: int
    contradicts_count: int
    system_observation: str
    pipeline_result: BaseASAGPipelineResult

    @property
    def student_answer_preview(self) -> str:
        """Compact preview of student answer text."""
        cleaned = " ".join(self.student_answer.split())
        return cleaned if len(cleaned) <= 65 else cleaned[:62] + "..."


@dataclass
class BatchEvaluationResult:
    """Structured collection of evaluation outcomes across a batch of student answers."""
    experiment_name: str
    question: str
    reference_answer: str
    timestamp: str
    records: List[SingleEvaluationRecord]

    def to_summary_dataframe(self) -> pd.DataFrame:
        """
        Generate the user-facing summary comparison DataFrame.
        """
        rows = []
        for r in self.records:
            rows.append({
                "Answer": r.answer_id,
                "Student Answer Preview": r.student_answer_preview,
                "TF-IDF Score": f"{r.tfidf_score:.4f}",
                "Base ASAG Score": f"{r.base_asag_score:.4f}",
                "Matched": r.matched_count,
                "Missing Reference": r.missing_reference_count,
                "Unmatched Student": r.unmatched_student_count,
                "Entails": r.entails_count,
                "Uncertain": r.uncertain_count,
                "Contradicts": r.contradicts_count,
                "System Observation": r.system_observation,
            })
        return pd.DataFrame(rows)

    def to_export_dataframe(self) -> pd.DataFrame:
        """
        Generate structured DataFrame for CSV export without internal Python objects.
        """
        rows = []
        for r in self.records:
            rows.append({
                "experiment_name": self.experiment_name,
                "question": self.question,
                "reference_answer": self.reference_answer,
                "answer_id": r.answer_id,
                "student_answer": r.student_answer,
                "tfidf_score": round(r.tfidf_score, 4),
                "base_asag_score": round(r.base_asag_score, 4),
                "matched_count": r.matched_count,
                "missing_reference_count": r.missing_reference_count,
                "unmatched_student_count": r.unmatched_student_count,
                "entails_count": r.entails_count,
                "uncertain_count": r.uncertain_count,
                "contradicts_count": r.contradicts_count,
                "system_observation": r.system_observation,
            })
        return pd.DataFrame(rows)

    def export_csv(self, target_path: Path) -> Path:
        """Export results to CSV file."""
        target_path.parent.mkdir(parents=True, exist_ok=True)
        df = self.to_export_dataframe()
        df.to_csv(target_path, index=False)
        return target_path


def format_preprocessing_tables(p_res: BaseASAGPipelineResult) -> Dict[str, pd.DataFrame]:
    """Format token/lemma/POS DataFrames for reference and student answers."""
    ref_rows = [
        {
            "Idx": t.index,
            "Token": t.text,
            "Lemma": t.lemma,
            "POS": t.pos,
            "Tag": t.tag,
            "Head": f"{t.head_text} ({t.head_index})",
            "Dep": t.dep,
            "Stop": t.is_stop,
            "Punct": t.is_punct,
        }
        for t in p_res.reference_parsed.tokens
    ]
    stu_rows = [
        {
            "Idx": t.index,
            "Token": t.text,
            "Lemma": t.lemma,
            "POS": t.pos,
            "Tag": t.tag,
            "Head": f"{t.head_text} ({t.head_index})",
            "Dep": t.dep,
            "Stop": t.is_stop,
            "Punct": t.is_punct,
        }
        for t in p_res.student_parsed.tokens
    ]
    return {
        "reference_tokens": pd.DataFrame(ref_rows),
        "student_tokens": pd.DataFrame(stu_rows),
    }


def format_dependency_relations_tables(p_res: BaseASAGPipelineResult) -> Dict[str, pd.DataFrame]:
    """Format canonical relations (SPO/SP) for reference and student answers."""
    ref_rows = [
        {
            "Index": i,
            "Subject": r.subject,
            "Predicate": r.predicate,
            "Object": r.object or "(None - SP)",
            "Type": r.relation_type,
            "Source Arcs": " + ".join(r.source_dependency_relations),
        }
        for i, r in enumerate(p_res.reference_triples.canonical_relations)
    ]
    stu_rows = [
        {
            "Index": i,
            "Subject": s.subject,
            "Predicate": s.predicate,
            "Object": s.object or "(None - SP)",
            "Type": s.relation_type,
            "Source Arcs": " + ".join(s.source_dependency_relations),
        }
        for i, s in enumerate(p_res.student_triples.canonical_relations)
    ]
    return {
        "reference_relations": pd.DataFrame(ref_rows),
        "student_relations": pd.DataFrame(stu_rows),
    }


def format_semantic_matching_table(p_res: BaseASAGPipelineResult) -> pd.DataFrame:
    """Format matched relation pairs and slot evidence."""
    rows = []
    for m in p_res.matched_relations:
        ref_str = f"({m.reference_relation.subject}, {m.reference_relation.predicate}, {m.reference_relation.object or 'None'})"
        stu_str = f"({m.student_relation.subject}, {m.student_relation.predicate}, {m.student_relation.object or 'None'})"
        s_ev = m.slot_evidence.get("subject")
        p_ev = m.slot_evidence.get("predicate")
        o_ev = m.slot_evidence.get("object")
        rows.append({
            "Reference Proposition": ref_str,
            "Student Proposition": stu_str,
            "Triple Score": f"{m.triple_score:.4f}",
            "Threshold": f"{m.threshold:.2f}",
            "Match Method": m.match_method,
            "Subj Sim (Method)": f"{m.subject_similarity:.2f} ({s_ev.semantic_relation if s_ev else 'N/A'})",
            "Pred Sim (Method)": f"{m.predicate_similarity:.2f} ({p_ev.semantic_relation if p_ev else 'N/A'})",
            "Obj Sim (Method)": f"{m.object_similarity:.2f} ({o_ev.semantic_relation if o_ev else 'N/A'})" if m.object_similarity is not None else "N/A (SP)",
        })
    return pd.DataFrame(rows)


def format_entailment_table(p_res: BaseASAGPipelineResult) -> pd.DataFrame:
    """Format proposition-level entailment decisions."""
    rows = []
    for e in p_res.entailment_results:
        ref_str = f"({e.reference_relation.subject}, {e.reference_relation.predicate}, {e.reference_relation.object or 'None'})"
        stu_str = f"({e.student_relation.subject}, {e.student_relation.predicate}, {e.student_relation.object or 'None'})"
        rows.append({
            "Reference Proposition": ref_str,
            "Student Proposition": stu_str,
            "Decision": e.relation,
            "Evidence Score": f"{e.confidence:.4f}",
            "Ref Polarity": e.reference_polarity,
            "Stu Polarity": e.student_polarity,
            "Diagnostic Reasons": "; ".join(e.reasons),
        })
    return pd.DataFrame(rows)


def format_unmatched_reference_table(p_res: BaseASAGPipelineResult) -> pd.DataFrame:
    """Format missing reference propositions."""
    rows = [
        {
            "Missing Reference Proposition": f"({r.subject}, {r.predicate}, {r.object or 'None'})",
            "Type": r.relation_type,
            "Status": "MISSING FROM STUDENT ANSWER",
            "Score Contribution": "0.00 (Zero Credit)",
        }
        for r in p_res.unmatched_reference_relations
    ]
    return pd.DataFrame(rows)


def format_unmatched_student_table(p_res: BaseASAGPipelineResult) -> pd.DataFrame:
    """Format unmatched student propositions with research boundary labels."""
    rows = [
        {
            "Extra Student Proposition": f"({s.subject}, {s.predicate}, {s.object or 'None'})",
            "Subject": s.subject,
            "Predicate": s.predicate,
            "Object": s.object or "(None)",
            "Type": s.relation_type,
            "Classification": "NOT EVALUATED BY BASE ASAG",
            "Score Effect": "0.00 (Strictly Neutral)",
        }
        for s in p_res.unmatched_student_relations
    ]
    return pd.DataFrame(rows)


def format_score_contributions_table(p_res: BaseASAGPipelineResult) -> pd.DataFrame:
    """Format itemized reference proposition score contributions."""
    rows = [
        {
            "Reference Proposition": f"({rec.reference_relation.subject}, {rec.reference_relation.predicate}, {rec.reference_relation.object or 'None'})",
            "Status": rec.status,
            "Proposition Weight": f"{rec.weight:.2f}",
            "Score Awarded": f"{rec.contribution:.2f}",
            "Weighted Score": f"{rec.weighted_contribution:.2f}",
            "Diagnostic Reasons": "; ".join(rec.diagnostic_reasons),
        }
        for rec in p_res.scoring_result.proposition_results
    ]
    return pd.DataFrame(rows)
