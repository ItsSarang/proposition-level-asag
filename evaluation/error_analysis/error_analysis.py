"""Diagnostic Error Analysis Module (Stage 16).

This module performs systematic diagnostic error analysis on the ASAG evaluation
results from Stage 15.2 (2,273 active records from the Mohler ASAG dataset).

Research Boundaries:
--------------------
- Strictly diagnostic: does NOT tune model parameters or modify scoring logic.
- Evaluates four quadrants for Base ASAG (FN, FP, TP, TN).
- Computes aggregate proposition-level statistics for Proposed ASAG.
- Identifies representative targeted cases for Proposed ASAG (improves MAE, worsens MAE,
  neutral adjustment, correct additional, irrelevant, incorrect).
- Analyzes why TF-IDF outperforms Base ASAG on specific questions.
- Does NOT calculate classifier accuracy for Stage 13 since no human clause-level
  ground truth exists.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from base_asag.pipeline import BaseASAGPipeline, BaseASAGPipelineResult
from proposed_asag.scoring.proposed_scorer import ProposedScoreResult, ProposedScorer


def compute_aggregate_proposition_stats(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate aggregate proposition counts and adjustment distributions across the benchmark.

    Parameters
    ----------
    df : pd.DataFrame
        Evaluation results DataFrame from Stage 15.2.

    Returns
    -------
    Dict[str, Any]
        Aggregated counts, proportions, and adjustment distribution metrics.
    """
    total_records = len(df)

    c_add = int(df["correct_additional_count"].sum())
    irrel = int(df["irrelevant_count"].sum())
    incorr = int(df["incorrect_count"].sum())
    uncert = int(df["uncertain_count"].sum())
    total_unmatched = c_add + irrel + incorr + uncert

    pos_adj_count = int((df["net_adjustment"] > 0).sum())
    neg_adj_count = int((df["net_adjustment"] < 0).sum())
    zero_adj_count = int((df["net_adjustment"] == 0).sum())

    raw_prop = df["base_normalized"] + df["net_adjustment"]
    clipped_upper = int((raw_prop > 1.0).sum())
    clipped_lower = int((raw_prop < 0.0).sum())

    net_norm = df["net_adjustment"]
    net_grade = net_norm * 5.0

    percentiles = [0, 25, 50, 75, 90, 95, 99, 100]
    pct_norm = {f"p{p}": float(np.percentile(net_norm, p)) for p in percentiles}
    pct_grade = {f"p{p}": float(np.percentile(net_grade, p)) for p in percentiles}

    return {
        "total_records": total_records,
        "total_unmatched_propositions": total_unmatched,
        "classification_counts": {
            "CORRECT_ADDITIONAL": c_add,
            "CORRECT_ADDITIONAL_pct": float(round(c_add / max(1, total_unmatched) * 100, 2)),
            "IRRELEVANT": irrel,
            "IRRELEVANT_pct": float(round(irrel / max(1, total_unmatched) * 100, 2)),
            "INCORRECT": incorr,
            "INCORRECT_pct": float(round(incorr / max(1, total_unmatched) * 100, 2)),
            "UNCERTAIN": uncert,
            "UNCERTAIN_pct": float(round(uncert / max(1, total_unmatched) * 100, 2)),
        },
        "answer_adjustment_counts": {
            "positive_adjustment_answers": pos_adj_count,
            "positive_adjustment_pct": float(round(pos_adj_count / total_records * 100, 2)),
            "negative_adjustment_answers": neg_adj_count,
            "negative_adjustment_pct": float(round(neg_adj_count / total_records * 100, 2)),
            "zero_adjustment_answers": zero_adj_count,
            "zero_adjustment_pct": float(round(zero_adj_count / total_records * 100, 2)),
            "clipped_upper_count": clipped_upper,
            "clipped_lower_count": clipped_lower,
        },
        "net_adjustment_normalized": {
            "mean": float(round(float(net_norm.mean()), 4)),
            "std": float(round(float(net_norm.std()), 4)),
            "min": float(round(float(net_norm.min()), 4)),
            "max": float(round(float(net_norm.max()), 4)),
            "percentiles": pct_norm,
        },
        "net_adjustment_grade_scale_0_5": {
            "mean": float(round(float(net_grade.mean()), 4)),
            "std": float(round(float(net_grade.std()), 4)),
            "min": float(round(float(net_grade.min()), 4)),
            "max": float(round(float(net_grade.max()), 4)),
            "percentiles": pct_grade,
        },
    }


def trace_pipeline_case(
    question: str,
    reference: str,
    student: str,
    pipeline: BaseASAGPipeline,
    scorer: ProposedScorer,
    human_score: float,
    baseline_grade: float,
    case_metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Execute full Base ASAG and Proposed ASAG pipeline and capture transparent linguistic trace."""
    base_res = pipeline.grade(question, reference, student)
    prop_res = scorer.score_document(base_res)

    ref_props = [
        {
            "tuple": r.to_tuple(),
            "relation_type": r.relation_type,
            "dep": getattr(r, "dep", None),
        }
        for sent in base_res.reference_triples.sentences
        for r in sent.canonical_relations
    ]

    stu_props = [
        {
            "tuple": s.to_tuple(),
            "relation_type": s.relation_type,
            "dep": getattr(s, "dep", None),
        }
        for sent in base_res.student_triples.sentences
        for s in sent.canonical_relations
    ]

    matched_details = [
        {
            "reference": m.reference_relation.to_tuple(),
            "student": m.student_relation.to_tuple(),
            "score": float(round(m.triple_score, 4)),
            "method": m.match_method,
            "slot_evidence": {
                k: v.to_dict() if hasattr(v, "to_dict") else str(v)
                for k, v in m.slot_evidence.items()
            },
        }
        for m in base_res.matched_relations
    ]

    unmatched_ref = [r.to_tuple() for r in base_res.unmatched_reference_relations]
    unmatched_stu = [s.to_tuple() for s in base_res.unmatched_student_relations]

    entailment_details = [e.to_dict() for e in base_res.entailment_results]

    adjustments = [
        {
            "classification": a.classification,
            "text": a.text,
            "confidence": a.confidence,
            "applied_adjustment": a.applied_adjustment,
            "reason": a.reason,
        }
        for a in prop_res.adjustment_details
    ]

    return {
        "metadata": case_metadata or {},
        "question": question,
        "reference_answer": reference,
        "student_answer": student,
        "human_score": human_score,
        "baseline_grade": baseline_grade,
        "base_grade": float(round(base_res.normalized_score * 5.0, 4)),
        "proposed_grade": float(round(prop_res.proposed_score * 5.0, 4)),
        "base_normalized": float(round(base_res.normalized_score, 4)),
        "proposed_normalized": float(round(prop_res.proposed_score, 4)),
        "net_adjustment": prop_res.net_adjustment,
        "extracted_reference_propositions": ref_props,
        "extracted_student_propositions": stu_props,
        "matched_propositions": matched_details,
        "unmatched_reference_propositions": unmatched_ref,
        "unmatched_student_propositions": unmatched_stu,
        "entailment_results": entailment_details,
        "proposed_adjustments": adjustments,
    }


def find_representative_cases(
    df: pd.DataFrame,
    pipeline: BaseASAGPipeline,
    scorer: ProposedScorer,
) -> Dict[str, Any]:
    """Identify and trace representative cases across Base ASAG, Proposed ASAG, and TF-IDF comparisons."""
    cases: Dict[str, Any] = {}

    df = df.copy()
    df["err_base"] = (df["base_grade"] - df["human_score"]).abs()
    df["err_prop"] = (df["proposed_grade"] - df["human_score"]).abs()
    df["err_tfidf"] = (df["baseline_grade"] - df["human_score"]).abs()
    df["mae_diff"] = df["err_base"] - df["err_prop"]

    # Helper to trace row
    def trace_row(row: pd.Series, category_name: str) -> Dict[str, Any]:
        meta = {
            "category": category_name,
            "question_id": str(row["question_id"]),
            "student_index": int(row["student_index"]),
            "assignment": int(row["assignment"]),
        }
        return trace_pipeline_case(
            question=row["question"],
            reference=row["reference_answer"],
            student=row["student_answer"],
            pipeline=pipeline,
            scorer=scorer,
            human_score=float(row["human_score"]),
            baseline_grade=float(row["baseline_grade"]),
            case_metadata=meta,
        )

    # -----------------------------------------------------------------------
    # Section 1: Base ASAG Four Quadrants
    # -----------------------------------------------------------------------
    # Quad A: High Human (>= 4.5), Zero Base (== 0.0) [False Negative]
    # We choose two contrasting cases:
    # 1. Zero reference proposition case (e.g. Q 1.1)
    # 2. Non-zero reference proposition but syntactic/semantic mismatch
    quad_a_zero_ref = df[(df["question_id"] == "1.1") & (df["student_index"] == 9)].iloc[0]
    # Find a Quad A where reference DOES have propositions
    quad_a_cand = df[(df["human_score"] >= 4.5) & (df["base_grade"] == 0.0)]
    quad_a_non_zero = None
    for _, r in quad_a_cand.iterrows():
        p = pipeline.parser.parse(pipeline.preprocessor.process(r["reference_answer"]))
        if len(pipeline.extractor.extract_document(p).canonical_relations) > 0:
            quad_a_non_zero = r
            break

    cases["base_asag_quadrant_A_zero_ref_prop"] = trace_row(
        quad_a_zero_ref, "Base ASAG FN (Zero Reference Propositions)"
    )
    if quad_a_non_zero is not None:
        cases["base_asag_quadrant_A_matching_gap"] = trace_row(
            quad_a_non_zero, "Base ASAG FN (Relational Matching Gap)"
        )

    # Quad B: Low Human (<= 2.5), Moderate/High Base (>= 2.5) [False Positive / Over-prediction]
    quad_b_row = df[(df["question_id"] == "1.6") & (df["student_index"] == 5)].iloc[0]
    cases["base_asag_quadrant_B_overprediction"] = trace_row(
        quad_b_row, "Base ASAG FP (Over-prediction on Partial/Incorrect Content)"
    )

    # Quad C: Concordant High: High Human (== 5.0), High Base (== 5.0) [True Positive]
    quad_c_row = df[(df["question_id"] == "1.7") & (df["student_index"] == 1)].iloc[0]
    cases["base_asag_quadrant_C_concordant_high"] = trace_row(
        quad_c_row, "Base ASAG TP (Concordant High Score 5.0/5.0)"
    )

    # Quad D: Concordant Low: Low Human (<= 1.0), Low Base (== 0.0) [True Negative]
    quad_d_row = df[(df["question_id"] == "1.4") & (df["student_index"] == 7)].iloc[0]
    cases["base_asag_quadrant_D_concordant_low"] = trace_row(
        quad_d_row, "Base ASAG TN (Concordant Low Score 0.0/0.0)"
    )

    # -----------------------------------------------------------------------
    # Section 3: Targeted Proposed ASAG Cases
    # -----------------------------------------------------------------------
    # Case A: Proposed improves MAE significantly
    case_a_row = df[(df["question_id"] == "3.7") & (df["student_index"] == 3)].iloc[0]
    cases["proposed_asag_case_A_improves_mae"] = trace_row(
        case_a_row, "Proposed ASAG Case A (Substantial Error Reduction)"
    )

    # Case B: Proposed worsens MAE (verbosity / credit inflation)
    case_b_row = df[(df["question_id"] == "2.6") & (df["student_index"] == 1)].iloc[0]
    cases["proposed_asag_case_B_worsens_mae"] = trace_row(
        case_b_row, "Proposed ASAG Case B (Verbosity Inflation / Worsened MAE)"
    )

    # Case C: Proposed changes score but human grade is unchanged / low
    case_c_row = df[(df["question_id"] == "11.8") & (df["student_index"] == 1)].iloc[0]
    cases["proposed_asag_case_C_divergence"] = trace_row(
        case_c_row, "Proposed ASAG Case C (Score Shift on Low Human Grade)"
    )

    # Case D: Proposed does not change score despite unmatched information (neutral adjustment)
    case_d_row = df[(df["net_adjustment"] == 0.0) & (df["irrelevant_count"] >= 3)].iloc[0]
    cases["proposed_asag_case_D_neutral_unmatched"] = trace_row(
        case_d_row, "Proposed ASAG Case D (Neutral Adjustment on Irrelevant Propositions)"
    )

    # Case E: High-quality CORRECT_ADDITIONAL classification
    case_e_row = df[(df["question_id"] == "12.9") & (df["student_index"] == 13)].iloc[0]
    cases["proposed_asag_case_E_correct_additional"] = trace_row(
        case_e_row, "Proposed ASAG Case E (Valid Domain Content as CORRECT_ADDITIONAL)"
    )

    # Case F: High-quality IRRELEVANT classification
    case_f_row = df[(df["question_id"] == "1.3") & (df["student_index"] == 0)].iloc[0]
    cases["proposed_asag_case_F_irrelevant"] = trace_row(
        case_f_row, "Proposed ASAG Case F (Off-Topic Digression as IRRELEVANT)"
    )

    # Case G: INCORRECT classification (Antonymous / Polarity Inversion Analysis)
    case_g_row = df[(df["question_id"] == "7.2") & (df["student_index"] == 9)].iloc[0]
    cases["proposed_asag_case_G_incorrect_polarity"] = trace_row(
        case_g_row, "Proposed ASAG Case G (Antonymy Polarity Inversion / False INCORRECT)"
    )

    # -----------------------------------------------------------------------
    # Section 4: TF-IDF vs Base ASAG
    # -----------------------------------------------------------------------
    # Case where TF-IDF significantly outperforms Base ASAG
    # Q 1.3: "What are the main advantages associated with object-oriented programming?"
    # Ref: "Abstraction and reusability."
    # Stu 4: "Some advantages are existing classes can be reused..."
    tfidf_better_row = df[(df["question_id"] == "1.3") & (df["student_index"] == 4)].iloc[0]
    cases["tfidf_vs_base_lexical_superiority"] = trace_row(
        tfidf_better_row, "TF-IDF Outperformance (Noun-Phrase Fragment / Lexical Match)"
    )

    return cases


def run_diagnostic_analysis(
    predictions_csv_path: Optional[Path] = None,
    output_json_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Execute complete Stage 16 diagnostic analysis and export structured results."""
    repo_root = Path(__file__).resolve().parent.parent.parent
    if predictions_csv_path is None:
        predictions_csv_path = repo_root / "evaluation" / "results" / "mohler_evaluation_predictions.csv"
    if output_json_path is None:
        output_json_path = repo_root / "evaluation" / "error_analysis" / "representative_cases.json"
    output_json_path.parent.mkdir(parents=True, exist_ok=True)

    if not predictions_csv_path.exists():
        raise FileNotFoundError(f"Predictions CSV not found at: {predictions_csv_path}")

    # Explicitly specify string dtype for question_id to preserve formats like '1.10' vs '1.1'
    df = pd.read_csv(predictions_csv_path, dtype={"question_id": str})

    # 1. Compute aggregate statistics
    agg_stats = compute_aggregate_proposition_stats(df)

    # 2. Extract and trace representative cases
    pipeline = BaseASAGPipeline()
    scorer = ProposedScorer()
    cases = find_representative_cases(df, pipeline, scorer)

    output_payload = {
        "aggregate_proposition_statistics": agg_stats,
        "representative_cases": cases,
    }

    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(output_payload, f, indent=2)

    return output_payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Stage 16 Diagnostic Error Analysis.")
    parser.add_argument(
        "--predictions-csv",
        type=str,
        default="evaluation/results/mohler_evaluation_predictions.csv",
        help="Path to evaluation predictions CSV.",
    )
    parser.add_argument(
        "--output-json",
        type=str,
        default="evaluation/error_analysis/representative_cases.json",
        help="Path to export representative cases JSON.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent.parent
    pred_path = repo_root / args.predictions_csv
    out_path = repo_root / args.output_json

    print("=" * 72)
    print("STAGE 16: DIAGNOSTIC ERROR ANALYSIS")
    print("=" * 72)
    print(f"Reading predictions from: {pred_path}")

    results = run_diagnostic_analysis(pred_path, out_path)
    agg = results["aggregate_proposition_statistics"]

    print("\n1. AGGREGATE PROPOSITION COUNTS (N = 2,273 records)")
    print(f"   Total Unmatched Propositions: {agg['total_unmatched_propositions']}")
    for cat, count in agg["classification_counts"].items():
        if not cat.endswith("_pct"):
            pct = agg["classification_counts"][f"{cat}_pct"]
            print(f"   - {cat:<20}: {count:5d} ({pct:5.1f}%)")

    print("\n2. ANSWER-LEVEL ADJUSTMENTS")
    adj = agg["answer_adjustment_counts"]
    print(f"   Positive adjustments: {adj['positive_adjustment_answers']:5d} ({adj['positive_adjustment_pct']:5.1f}%)")
    print(f"   Negative adjustments: {adj['negative_adjustment_answers']:5d} ({adj['negative_adjustment_pct']:5.1f}%)")
    print(f"   Zero adjustments:     {adj['zero_adjustment_answers']:5d} ({adj['zero_adjustment_pct']:5.1f}%)")
    print(f"   Clipped upper (>1.0): {adj['clipped_upper_count']}")
    print(f"   Clipped lower (<0.0): {adj['clipped_lower_count']}")

    print("\n3. REPRESENTATIVE CASES TRACED")
    cases = results["representative_cases"]
    for case_id, c in cases.items():
        m = c["metadata"]
        print(f"   [{case_id}] Q {m['question_id']} (stu {m['student_index']}): "
              f"Human={c['human_score']} | Base={c['base_grade']} | Proposed={c['proposed_grade']}")

    print(f"\nDiagnostic results exported to: {out_path}")
    print("=" * 72)


if __name__ == "__main__":
    main()
