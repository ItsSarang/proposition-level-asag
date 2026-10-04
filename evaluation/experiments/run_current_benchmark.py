"""
Controlled Mohler Benchmark Evaluation Runner.

Executes reproducible evaluation comparing:
- V0: TF-IDF Baseline (Cosine similarity)
- V1: Base ASAG (Simplified Basak-inspired clausal coverage)
- V2: Historical Proposed ASAG (Stage 14 linear addition)
- V3: Current Proposed ASAG with the repaired evidence layer (Phases 1-9)

Evaluates on the complete active Mohler dataset (2,273 records) and reports
subsets for Full Active, Assignments 1-10 (N=1,721), and Exams 11-12 (N=552).
Captures full proposition-level provenance and score effects.
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
from evaluation.runners.base_asag_runner import BaseASAGRunner
from evaluation.runners.baseline_runner import BaselineRunner
from evaluation.runners.overhaul_runner import OverhaulASAGRunner
from evaluation.runners.proposed_asag_runner import ProposedASAGRunner
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
        f"{'System':<38} | {'MAE':^7} | {'RMSE':^7} | {'Pearson r':^9} | {'Spearman rho':^12} | {'QWK':^7} | {'Mean Pred':^9} | {'Mean Human':^10} | {'N':^5}"
    )
    print("-" * 122)
    order = ["v0_baseline", "v1_base_asag", "v2_historical_proposed", "v3_current_proposed"]
    for key in order:
        if key not in metrics_dict:
            continue
        m = metrics_dict[key]
        print(
            f"{m.system_name:<38} | {m.mae:7.4f} | {m.rmse:7.4f} | {format_metric(m.pearson_r):^9} | "
            f"{format_metric(m.spearman_rho):^12} | {format_metric(m.qwk):^7} | {m.predicted_mean:9.4f} | {m.ground_truth_mean:10.4f} | {m.n_samples:^5}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run controlled Mohler ASAG benchmark.")
    parser.add_argument(
        "--output-dir",
        type=str,
        default="evaluation/results",
        help="Directory to export benchmark predictions and summaries.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional limit on number of records (for testing).",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent.parent
    out_dir = repo_root / args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load active dataset
    raw_dataset = MohlerLoader.load_processed_csv()
    dataset = raw_dataset.filter_active()

    if args.limit is not None and args.limit > 0:
        records_to_evaluate = dataset.records[: args.limit]
    else:
        records_to_evaluate = dataset.records

    total_records = len(records_to_evaluate)
    logger.info("Initializing controlled benchmark on %d active records...", total_records)

    # 2. Instantiate Runners
    baseline_runner = BaselineRunner()
    base_runner = BaseASAGRunner()
    historical_runner = ProposedASAGRunner()
    current_proposed_runner = OverhaulASAGRunner()

    # 3. Execution Data Containers
    start_time = time.time()
    failures = 0

    rows: List[Dict[str, Any]] = []
    y_true: List[float] = []
    y_pred_baseline: List[float] = []
    y_pred_base: List[float] = []
    y_pred_hist: List[float] = []
    y_pred_current: List[float] = []

    # Proposition provenance diagnostics
    detailed_propositions: List[Dict[str, Any]] = []

    # Cumulative counts for evidence layer
    answers_with_unmatched = 0
    total_unmatched_props = 0
    classified_counts = {
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

    # Score adjustments tracking
    pos_adjustments = 0
    neg_adjustments = 0
    zero_adjustments = 0
    base_grades_list: List[float] = []
    net_adjs_list: List[float] = []
    final_grades_list: List[float] = []

    # Non-sentential reference tracking
    non_sentential_questions: set = set()
    non_sentential_records_count = 0

    for idx, rec in enumerate(records_to_evaluate):
        if (idx + 1) % 100 == 0 or (idx + 1) == total_records:
            elapsed = time.time() - start_time
            rate = (idx + 1) / max(0.01, elapsed)
            logger.info("Progress: %d/%d (%.1f%%) | Rate: %.1f records/s", idx + 1, total_records, (idx + 1) / total_records * 100, rate)

        stu_text = rec.student_answer_cleaned
        human_score = rec.score_ave

        try:
            # System 0: Baseline (TF-IDF)
            b_pred = baseline_runner.evaluate_pair(
                reference_answer=rec.reference_answer,
                student_answer=stu_text,
                max_points=5.0,
            )

            # System 1: Base ASAG
            base_pred = base_runner.evaluate_triplet(
                question=rec.question,
                reference_answer=rec.reference_answer,
                student_answer=stu_text,
                max_points=5.0,
            )

            # System 2: Historical Proposed ASAG (Stage 14)
            if base_pred.pipeline_result is not None:
                hist_pred = historical_runner.evaluate_base_result(
                    base_result=base_pred.pipeline_result,
                    max_points=5.0,
                )
            else:
                hist_pred = historical_runner.evaluate_base_result(None, max_points=5.0)

            # System 3: Current Proposed ASAG (with repaired evidence layer)
            current_pred = current_proposed_runner.evaluate_triplet(
                question=rec.question,
                reference_answer=rec.reference_answer,
                student_answer=stu_text,
                max_points=5.0,
            )
        except Exception as e:
            logger.error("Error evaluating record %s_%s: %s", rec.question_id, rec.student_index, e)
            failures += 1
            continue

        # Accumulate metrics
        y_true.append(human_score)
        y_pred_baseline.append(b_pred.grade)
        y_pred_base.append(base_pred.grade)
        y_pred_hist.append(hist_pred.proposed_grade)
        y_pred_current.append(current_pred.grade)

        # Check non-sentential reference issue in Base ASAG
        is_non_sentential = (base_pred.total_reference_propositions == 0)
        if is_non_sentential:
            non_sentential_questions.add(rec.question_id)
            non_sentential_records_count += 1

        # Track score adjustments
        base_grades_list.append(current_pred.base_grade)
        net_adjs_list.append(current_pred.net_adjustment)
        final_grades_list.append(current_pred.grade)

        if current_pred.net_adjustment > 0.0001:
            pos_adjustments += 1
        elif current_pred.net_adjustment < -0.0001:
            neg_adjustments += 1
        else:
            zero_adjustments += 1

        # Track proposition statistics
        unmatched_count = current_pred.unmatched_student_propositions_count
        if unmatched_count > 0:
            answers_with_unmatched += 1
            total_unmatched_props += unmatched_count

        classified_counts["CORRECT_ADDITIONAL"] += current_pred.correct_additional_count
        classified_counts["INCORRECT"] += current_pred.incorrect_count
        classified_counts["IRRELEVANT"] += current_pred.irrelevant_count
        classified_counts["UNCERTAIN"] += current_pred.uncertain_count

        # Extract proposition provenance from pipeline_result if available
        domain_supported_in_rec = 0
        if current_pred.pipeline_result and current_pred.pipeline_result.classification_result:
            for cp in current_pred.pipeline_result.classification_result.classified_propositions:
                # Only inspect unmatched propositions (skip MATCHED_BY_BASE_ASAG)
                if cp.classification.value == "MATCHED_BY_BASE_ASAG":
                    continue

                v_ev = cp.verification_evidence
                is_supp = (v_ev is not None and v_ev.status == EvidenceStatus.SUPPORTED)
                if is_supp:
                    domain_supported_in_rec += 1
                    domain_evidence_supported += 1
                    if v_ev.rule_id in rule_counts:
                        rule_counts[v_ev.rule_id] += 1

                # Save detailed provenance record
                prop_record = {
                    "question_id": rec.question_id,
                    "student_index": rec.student_index,
                    "proposition_text": cp.proposition.source_text,
                    "matched_rule_id": v_ev.rule_id if v_ev else None,
                    "evidence_status": v_ev.status.value if v_ev else None,
                    "final_classification": cp.classification.value,
                    "evidence_rationale": cp.rationale,
                    "scoring_adjustment": cp.score_effect,
                    "answer_final_grade": round(current_pred.grade, 4),
                    "human_score": round(human_score, 4),
                }
                detailed_propositions.append(prop_record)

        # CSV row
        row = {
            "question_id": rec.question_id,
            "assignment": rec.assignment,
            "question_index": rec.question_index,
            "student_index": rec.student_index,
            "human_score": round(human_score, 4),
            "score_me": round(rec.score_me, 4),
            "score_other": round(rec.score_other, 4),
            "v0_baseline_grade": round(b_pred.grade, 4),
            "v1_base_asag_grade": round(base_pred.grade, 4),
            "v2_historical_proposed_grade": round(hist_pred.proposed_grade, 4),
            "v3_current_proposed_grade": round(current_pred.grade, 4),
            "v3_base_grade": round(current_pred.base_grade, 4),
            "v3_pos_adj": round(current_pred.positive_adjustment, 4),
            "v3_neg_adj": round(current_pred.negative_adjustment, 4),
            "v3_net_adj": round(current_pred.net_adjustment, 4),
            "v3_is_clipped_upper": current_pred.is_clipped_upper,
            "v3_is_clipped_lower": current_pred.is_clipped_lower,
            "v3_matched_count": current_pred.matched_propositions_count,
            "v3_unmatched_count": current_pred.unmatched_student_propositions_count,
            "v3_correct_additional_count": current_pred.correct_additional_count,
            "v3_incorrect_count": current_pred.incorrect_count,
            "v3_irrelevant_count": current_pred.irrelevant_count,
            "v3_uncertain_count": current_pred.uncertain_count,
            "v3_domain_supported_count": domain_supported_in_rec,
            "v3_ref_props_count": current_pred.reference_propositions_count,
            "has_non_sentential_ref": is_non_sentential,
        }
        rows.append(row)

    total_elapsed = time.time() - start_time
    logger.info("Benchmark complete in %.2f seconds. Failures: %d", total_elapsed, failures)

    # 4. Compute Metrics for Subsets
    # Helper to compute metrics dict
    def compute_system_metrics(sub_y_true, sub_v0, sub_v1, sub_v2, sub_v3) -> Dict[str, EvaluationMetrics]:
        return {
            "v0_baseline": compute_all_metrics("V0: TF-IDF Baseline", sub_y_true, sub_v0),
            "v1_base_asag": compute_all_metrics("V1: Base ASAG", sub_y_true, sub_v1),
            "v2_historical_proposed": compute_all_metrics("V2: Historical Proposed ASAG", sub_y_true, sub_v2),
            "v3_current_proposed": compute_all_metrics("V3: Current Proposed ASAG", sub_y_true, sub_v3),
        }

    # Full Active
    metrics_full = compute_system_metrics(y_true, y_pred_baseline, y_pred_base, y_pred_hist, y_pred_current)

    # Assignments 1-10 vs Exams 11-12
    assign_indices = [i for i, r in enumerate(rows) if int(r["assignment"]) <= 10]
    exam_indices = [i for i, r in enumerate(rows) if int(r["assignment"]) > 10]

    def filter_by_indices(arr, indices):
        return [arr[i] for i in indices]

    metrics_assignments = (
        compute_system_metrics(
            filter_by_indices(y_true, assign_indices),
            filter_by_indices(y_pred_baseline, assign_indices),
            filter_by_indices(y_pred_base, assign_indices),
            filter_by_indices(y_pred_hist, assign_indices),
            filter_by_indices(y_pred_current, assign_indices),
        )
        if assign_indices
        else {}
    )

    metrics_exams = (
        compute_system_metrics(
            filter_by_indices(y_true, exam_indices),
            filter_by_indices(y_pred_baseline, exam_indices),
            filter_by_indices(y_pred_base, exam_indices),
            filter_by_indices(y_pred_hist, exam_indices),
            filter_by_indices(y_pred_current, exam_indices),
        )
        if exam_indices
        else {}
    )

    # Sentential vs Non-sentential subsets
    sentential_indices = [i for i, r in enumerate(rows) if not r["has_non_sentential_ref"]]
    non_sentential_indices = [i for i, r in enumerate(rows) if r["has_non_sentential_ref"]]

    metrics_sentential = (
        compute_system_metrics(
            filter_by_indices(y_true, sentential_indices),
            filter_by_indices(y_pred_baseline, sentential_indices),
            filter_by_indices(y_pred_base, sentential_indices),
            filter_by_indices(y_pred_hist, sentential_indices),
            filter_by_indices(y_pred_current, sentential_indices),
        )
        if sentential_indices
        else {}
    )

    metrics_non_sentential = (
        compute_system_metrics(
            filter_by_indices(y_true, non_sentential_indices),
            filter_by_indices(y_pred_baseline, non_sentential_indices),
            filter_by_indices(y_pred_base, non_sentential_indices),
            filter_by_indices(y_pred_hist, non_sentential_indices),
            filter_by_indices(y_pred_current, non_sentential_indices),
        )
        if non_sentential_indices
        else {}
    )

    # 5. Export Predictions CSV
    csv_path = out_dir / "current_mohler_results.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    # 6. Export Summary JSON
    summary_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
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
        "proposition_counts": {
            "total_answers_evaluated": total_records,
            "answers_with_unmatched_propositions": answers_with_unmatched,
            "total_unmatched_propositions": total_unmatched_props,
            "classified_correct_additional": classified_counts["CORRECT_ADDITIONAL"],
            "classified_incorrect": classified_counts["INCORRECT"],
            "classified_irrelevant": classified_counts["IRRELEVANT"],
            "classified_uncertain": classified_counts["UNCERTAIN"],
            "domain_evidence_supported": domain_evidence_supported,
            "rule_breakdown": rule_counts,
        },
        "score_effects": {
            "mean_base_grade": round(float(np.mean(base_grades_list)), 4),
            "mean_net_adj": round(float(np.mean(net_adjs_list)), 4),
            "mean_final_grade": round(float(np.mean(final_grades_list)), 4),
            "count_positive_adj": pos_adjustments,
            "count_negative_adj": neg_adjustments,
            "count_zero_adj": zero_adjustments,
        },
        "non_sentential_reference_diagnostic": {
            "affected_questions_count": len(non_sentential_questions),
            "affected_questions": sorted(list(non_sentential_questions)),
            "affected_answers_count": non_sentential_records_count,
            "percentage_affected_records": round(non_sentential_records_count / total_records * 100, 2),
        },
    }

    summary_json_path = out_dir / "current_mohler_summary.json"
    with open(summary_json_path, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2)

    # Export detailed provenance
    prov_json_path = out_dir / "current_mohler_propositions.json"
    with open(prov_json_path, "w", encoding="utf-8") as f:
        json.dump(detailed_propositions, f, indent=2)

    logger.info("Exported results to %s", csv_path)
    logger.info("Exported summary to %s", summary_json_path)
    logger.info("Exported proposition provenance to %s", prov_json_path)

    # 7. Print Comparative Tables
    print_comparison_table("A. FULL ACTIVE DATASET (N=2,273)", metrics_full)
    print_comparison_table("B. ASSIGNMENTS 1-10 (N=1,721)", metrics_assignments)
    print_comparison_table("C. EXAMS 11-12 (N=552)", metrics_exams)


if __name__ == "__main__":
    main()
