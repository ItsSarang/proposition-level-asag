"""
Experiment 2: Base ASAG Representation and Matching Improvement Evaluation Runner.

Evaluates the repaired pipeline with extended dependency representation,
matrix non-finite root handling, and predicate-gated cross-slot argument matching
on the official UNT CS Short Answer Dataset v2.0 (Mohler et al., 2011).

Compares all five systems:
- System A (V0): TF-IDF Baseline
- System B (V1): Base ASAG
- System C (V2): Historical Proposed ASAG (Stage 15.2)
- System D (V3): Current Proposed ASAG (Frozen Experiment 1)
- System E (V4): Representation-Improved Proposed ASAG (Experiment 2)

Preserves frozen Experiment 1 outputs untouched and exports all outputs to:
evaluation/results/experiment_2_representation/
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import time
from typing import Any, Dict, List, Optional

import numpy as np

from evaluation.dataset.mohler_loader import MohlerDataset, MohlerLoader, MohlerRecord
from evaluation.metrics.asag_metrics import EvaluationMetrics, compute_all_metrics
from evaluation.runners.overhaul_runner import OverhaulASAGRunner
from proposed_asag.evidence.models import EvidenceStatus

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def format_metric(val: Optional[float], decimals: int = 4) -> str:
    if val is None:
        return "  N/A  "
    return f"{val:7.{decimals}f}"


def print_comparison_table(title: str, metrics_dict: Dict[str, EvaluationMetrics]) -> None:
    print(f"\n### {title}")
    print(
        f"{'System':<42} | {'MAE':^7} | {'RMSE':^7} | {'Pearson r':^9} | {'Spearman rho':^12} | {'QWK':^7} | {'Mean Pred':^9} | {'Mean Human':^10} | {'N':^5}"
    )
    print("-" * 126)
    order = [
        "v0_baseline",
        "v1_base_asag",
        "v2_historical_proposed",
        "v3_current_proposed",
        "v4_representation_improved",
    ]
    for key in order:
        if key not in metrics_dict:
            continue
        m = metrics_dict[key]
        print(
            f"{m.system_name:<42} | {m.mae:7.4f} | {m.rmse:7.4f} | {format_metric(m.pearson_r):^9} | "
            f"{format_metric(m.spearman_rho):^12} | {format_metric(m.qwk):^7} | {m.predicted_mean:9.4f} | {m.ground_truth_mean:10.4f} | {m.n_samples:^5}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Experiment 2 Mohler ASAG benchmark.")
    parser.add_argument(
        "--output-dir",
        type=str,
        default="evaluation/results/experiment_2_representation",
        help="Directory to export Experiment 2 results.",
    )
    parser.add_argument(
        "--frozen-results",
        type=str,
        default="evaluation/results/current_mohler_results.csv",
        help="Path to frozen Experiment 1 results CSV.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional limit on number of records (for quick testing).",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent.parent
    out_dir = repo_root / args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    frozen_csv_path = repo_root / args.frozen_results
    if not frozen_csv_path.exists():
        raise FileNotFoundError(f"Frozen Experiment 1 CSV not found at: {frozen_csv_path}")

    # 1. Load frozen Experiment 1 lookup
    logger.info("Loading frozen historical results from %s...", frozen_csv_path)
    frozen_lookup: Dict[str, Dict[str, Any]] = {}
    with open(frozen_csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            key = f"{r['question_id']}_{r['student_index']}"
            frozen_lookup[key] = r

    # 2. Load active dataset
    raw_dataset = MohlerLoader.load_processed_csv()
    dataset = raw_dataset.filter_active()

    if args.limit is not None and args.limit > 0:
        records_to_evaluate = dataset.records[: args.limit]
    else:
        records_to_evaluate = dataset.records

    total_records = len(records_to_evaluate)
    logger.info("Starting Experiment 2 benchmark on %d active records...", total_records)

    # 3. Instantiate Runner (with improved representation & cross-slot matching enabled)
    runner = OverhaulASAGRunner()

    start_time = time.time()
    failures = 0

    rows: List[Dict[str, Any]] = []
    y_true: List[float] = []
    y_pred_v0: List[float] = []
    y_pred_v1: List[float] = []
    y_pred_v2: List[float] = []
    y_pred_v3: List[float] = []
    y_pred_v4: List[float] = []

    # Detailed proposition provenance
    detailed_propositions: List[Dict[str, Any]] = []

    # Diagnostics aggregators
    total_stu_props = 0
    total_ref_props = 0
    total_matches = 0
    total_direct_matches = 0
    total_cross_slot_matches = 0
    total_unmatched_stu_props = 0

    entailment_counts = {
        "ENTAILS": 0,
        "CONTRADICTS": 0,
        "UNCERTAIN": 0,
    }

    classification_counts = {
        "CORRECT_ADDITIONAL": 0,
        "INCORRECT": 0,
        "IRRELEVANT": 0,
        "UNCERTAIN": 0,
    }

    domain_evidence_supported = 0
    rule_counts = {
        "PK_NOT_NULL": 0,
        "BST_INORDER_SORTED": 0,
        "COMPILER_INTERMEDIATE_REP": 0,
    }

    for idx, rec in enumerate(records_to_evaluate):
        if (idx + 1) % 100 == 0 or (idx + 1) == total_records:
            elapsed = time.time() - start_time
            rate = (idx + 1) / max(0.01, elapsed)
            logger.info(
                "Progress: %d/%d (%.1f%%) | Rate: %.1f records/s",
                idx + 1,
                total_records,
                (idx + 1) / total_records * 100,
                rate,
            )

        key = f"{rec.question_id}_{rec.student_index}"
        frozen_row = frozen_lookup.get(key)
        if frozen_row is None:
            logger.warning("Missing frozen row for key: %s", key)
            continue

        human_score = rec.score_ave
        v0_grade = float(frozen_row["v0_baseline_grade"])
        v1_grade = float(frozen_row["v1_base_asag_grade"])
        v2_grade = float(frozen_row["v2_historical_proposed_grade"])
        v3_grade = float(frozen_row["v3_current_proposed_grade"])
        has_non_sentential = frozen_row["has_non_sentential_ref"] == "True"

        try:
            pred = runner.evaluate_triplet(
                question=rec.question,
                reference_answer=rec.reference_answer,
                student_answer=rec.student_answer_cleaned,
                max_points=5.0,
            )
        except Exception as e:
            logger.error("Error evaluating record %s: %s", key, e)
            failures += 1
            continue

        # Accumulate metrics vectors
        y_true.append(human_score)
        y_pred_v0.append(v0_grade)
        y_pred_v1.append(v1_grade)
        y_pred_v2.append(v2_grade)
        y_pred_v3.append(v3_grade)
        y_pred_v4.append(pred.grade)

        # Aggregate diagnostics
        total_stu_props += pred.student_propositions_count
        total_ref_props += pred.reference_propositions_count
        total_matches += pred.matched_propositions_count
        total_direct_matches += pred.direct_matches_count
        total_cross_slot_matches += pred.cross_slot_matches_count
        total_unmatched_stu_props += pred.unmatched_student_propositions_count

        classification_counts["CORRECT_ADDITIONAL"] += pred.correct_additional_count
        classification_counts["INCORRECT"] += pred.incorrect_count
        classification_counts["IRRELEVANT"] += pred.irrelevant_count
        classification_counts["UNCERTAIN"] += pred.uncertain_count

        for decision in pred.entailment_decisions:
            if decision in entailment_counts:
                entailment_counts[decision] += 1

        # Track domain evidence support
        domain_supported_in_rec = 0
        if pred.pipeline_result and pred.pipeline_result.classification_result:
            for cp in pred.pipeline_result.classification_result.classified_propositions:
                if cp.classification.value == "MATCHED_BY_BASE_ASAG":
                    continue
                v_ev = cp.verification_evidence
                is_supp = v_ev is not None and v_ev.status == EvidenceStatus.SUPPORTED
                if is_supp:
                    domain_supported_in_rec += 1
                    domain_evidence_supported += 1
                    if v_ev.rule_id in rule_counts:
                        rule_counts[v_ev.rule_id] += 1

                detailed_propositions.append({
                    "question_id": rec.question_id,
                    "student_index": rec.student_index,
                    "proposition_text": cp.proposition.source_text,
                    "matched_rule_id": v_ev.rule_id if v_ev else None,
                    "evidence_status": v_ev.status.value if v_ev else None,
                    "final_classification": cp.classification.value,
                    "evidence_rationale": cp.rationale,
                    "scoring_adjustment": cp.score_effect,
                    "answer_final_grade": round(pred.grade, 4),
                    "human_score": round(human_score, 4),
                })

        # Build CSV row
        row = {
            "question_id": rec.question_id,
            "assignment": rec.assignment,
            "question_index": rec.question_index,
            "student_index": rec.student_index,
            "human_score": round(human_score, 4),
            "v0_baseline_grade": v0_grade,
            "v1_base_asag_grade": v1_grade,
            "v2_historical_proposed_grade": v2_grade,
            "v3_current_proposed_grade": v3_grade,
            "v4_representation_improved_grade": round(pred.grade, 4),
            "v4_base_grade": round(pred.base_grade, 4),
            "v4_pos_adj": round(pred.positive_adjustment, 4),
            "v4_neg_adj": round(pred.negative_adjustment, 4),
            "v4_net_adj": round(pred.net_adjustment, 4),
            "v4_is_clipped_upper": pred.is_clipped_upper,
            "v4_is_clipped_lower": pred.is_clipped_lower,
            "v4_matched_count": pred.matched_propositions_count,
            "v4_unmatched_count": pred.unmatched_student_propositions_count,
            "v4_correct_additional_count": pred.correct_additional_count,
            "v4_incorrect_count": pred.incorrect_count,
            "v4_irrelevant_count": pred.irrelevant_count,
            "v4_uncertain_count": pred.uncertain_count,
            "v4_domain_supported_count": domain_supported_in_rec,
            "v4_ref_props_count": pred.reference_propositions_count,
            "v4_cross_slot_matches_count": pred.cross_slot_matches_count,
            "v4_direct_matches_count": pred.direct_matches_count,
            "has_non_sentential_ref": has_non_sentential,
        }
        rows.append(row)

    total_elapsed = time.time() - start_time
    logger.info("Evaluation complete in %.2f seconds. Failures: %d", total_elapsed, failures)

    # 4. Compute Metrics Across Subsets
    def compute_all_five_systems(sub_y_true, sub_v0, sub_v1, sub_v2, sub_v3, sub_v4) -> Dict[str, EvaluationMetrics]:
        return {
            "v0_baseline": compute_all_metrics("System A (V0): TF-IDF Baseline", sub_y_true, sub_v0),
            "v1_base_asag": compute_all_metrics("System B (V1): Base ASAG", sub_y_true, sub_v1),
            "v2_historical_proposed": compute_all_metrics("System C (V2): Historical Proposed ASAG", sub_y_true, sub_v2),
            "v3_current_proposed": compute_all_metrics("System D (V3): Current Proposed (Exp 1)", sub_y_true, sub_v3),
            "v4_representation_improved": compute_all_metrics("System E (V4): Representation-Improved (Exp 2)", sub_y_true, sub_v4),
        }

    def filter_by_indices(arr: List[float], indices: List[int]) -> List[float]:
        return [arr[i] for i in indices]

    # Full Active
    metrics_full = compute_all_five_systems(y_true, y_pred_v0, y_pred_v1, y_pred_v2, y_pred_v3, y_pred_v4)

    # Assignments 1-10 vs Exams 11-12
    assign_indices = [i for i, r in enumerate(rows) if int(r["assignment"]) <= 10]
    exam_indices = [i for i, r in enumerate(rows) if int(r["assignment"]) > 10]

    metrics_assignments = compute_all_five_systems(
        filter_by_indices(y_true, assign_indices),
        filter_by_indices(y_pred_v0, assign_indices),
        filter_by_indices(y_pred_v1, assign_indices),
        filter_by_indices(y_pred_v2, assign_indices),
        filter_by_indices(y_pred_v3, assign_indices),
        filter_by_indices(y_pred_v4, assign_indices),
    ) if assign_indices else {}

    metrics_exams = compute_all_five_systems(
        filter_by_indices(y_true, exam_indices),
        filter_by_indices(y_pred_v0, exam_indices),
        filter_by_indices(y_pred_v1, exam_indices),
        filter_by_indices(y_pred_v2, exam_indices),
        filter_by_indices(y_pred_v3, exam_indices),
        filter_by_indices(y_pred_v4, exam_indices),
    ) if exam_indices else {}

    # Sentential vs Non-sentential subsets
    sentential_indices = [i for i, r in enumerate(rows) if not r["has_non_sentential_ref"]]
    non_sentential_indices = [i for i, r in enumerate(rows) if r["has_non_sentential_ref"]]

    metrics_sentential = compute_all_five_systems(
        filter_by_indices(y_true, sentential_indices),
        filter_by_indices(y_pred_v0, sentential_indices),
        filter_by_indices(y_pred_v1, sentential_indices),
        filter_by_indices(y_pred_v2, sentential_indices),
        filter_by_indices(y_pred_v3, sentential_indices),
        filter_by_indices(y_pred_v4, sentential_indices),
    ) if sentential_indices else {}

    metrics_non_sentential = compute_all_five_systems(
        filter_by_indices(y_true, non_sentential_indices),
        filter_by_indices(y_pred_v0, non_sentential_indices),
        filter_by_indices(y_pred_v1, non_sentential_indices),
        filter_by_indices(y_pred_v2, non_sentential_indices),
        filter_by_indices(y_pred_v3, non_sentential_indices),
        filter_by_indices(y_pred_v4, non_sentential_indices),
    ) if non_sentential_indices else {}

    # 5. Export Predictions CSV
    csv_path = out_dir / "experiment_2_results.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    # 6. Export Summary JSON
    pct_cross_slot = (total_cross_slot_matches / max(1, total_matches)) * 100.0
    summary_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "experiment_name": "Experiment 2 — Base ASAG Representation and Matching Improvement",
        "dataset_version": "UNT CS Short Answer Dataset v2.0 (Mohler et al., 2011)",
        "total_active_records": total_records,
        "elapsed_seconds": round(total_elapsed, 2),
        "failures": failures,
        "metrics": {
            "full_active": {k: v.to_dict() for k, v in metrics_full.items()},
            "assignments_1_10": {k: v.to_dict() for k, v in metrics_assignments.items()},
            "exams_11_12": {k: v.to_dict() for k, v in metrics_exams.items()},
            "sentential_reference_subset": {k: v.to_dict() for k, v in metrics_sentential.items()},
            "non_sentential_reference_subset": {k: v.to_dict() for k, v in metrics_non_sentential.items()},
        },
        "representation_diagnostics": {
            "total_student_propositions_extracted": total_stu_props,
            "total_reference_propositions_extracted": total_ref_props,
            "total_matches_made": total_matches,
            "total_direct_matches": total_direct_matches,
            "total_cross_slot_matches": total_cross_slot_matches,
            "percentage_matches_cross_slot": round(pct_cross_slot, 2),
            "total_unmatched_student_propositions": total_unmatched_stu_props,
            "additional_info_distribution": classification_counts,
            "entailment_decisions_distribution": entailment_counts,
            "domain_evidence_supported": domain_evidence_supported,
            "domain_rule_breakdown": rule_counts,
        },
    }

    summary_json_path = out_dir / "experiment_2_summary.json"
    with open(summary_json_path, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2)

    prov_json_path = out_dir / "experiment_2_propositions.json"
    with open(prov_json_path, "w", encoding="utf-8") as f:
        json.dump(detailed_propositions, f, indent=2)

    logger.info("Exported results CSV to %s", csv_path)
    logger.info("Exported summary JSON to %s", summary_json_path)
    logger.info("Exported proposition details to %s", prov_json_path)

    # 7. Print Comparative Tables
    print_comparison_table("A. FULL ACTIVE DATASET (N=2,273)", metrics_full)
    print_comparison_table("B. ASSIGNMENTS 1-10 (N=1,721)", metrics_assignments)
    print_comparison_table("C. EXAMS 11-12 (N=552)", metrics_exams)


if __name__ == "__main__":
    main()
