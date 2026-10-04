"""
Four-System Comparative Benchmark Runner (Phase 13).

Executes reproducible evaluation comparing:
1. SYSTEM 1: TF-IDF Baseline (Cosine similarity)
2. SYSTEM 2: Base ASAG (Simplified Basak-inspired clausal coverage)
3. SYSTEM 3: Historical Proposed ASAG (Stage 14 linear addition)
4. SYSTEM 4: Overhauled Proposed ASAG (Hybrid + Semantic V2 + Global + Relevance + Contradiction + Saturating Bounded Scorer)

Preserves results in evaluation/results/overhaul_v1/ without overwriting historical results.
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
import pandas as pd

from evaluation.dataset.mohler_loader import MohlerDataset, MohlerLoader, MohlerRecord
from evaluation.error_analysis.overhaul_error_analysis import OverhaulErrorAnalyzer
from evaluation.metrics.asag_metrics import EvaluationMetrics, compute_all_metrics
from evaluation.runners.base_asag_runner import BaseASAGRunner
from evaluation.runners.baseline_runner import BaselineRunner
from evaluation.runners.overhaul_runner import OverhaulASAGRunner
from evaluation.runners.proposed_asag_runner import ProposedASAGRunner

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def format_metric(val: Optional[float], decimals: int = 4) -> str:
    if val is None:
        return "  N/A  "
    return f"{val:7.{decimals}f}"


def print_comparison_table(title: str, metrics_dict: Dict[str, EvaluationMetrics]) -> None:
    print(f"\n### {title}")
    print(
        f"{'System':<38} | {'MAE':^7} | {'RMSE':^7} | {'Pearson r':^9} | {'Spearman rho':^12} | {'QWK':^7} | {'N':^5}"
    )
    print("-" * 96)
    order = ["baseline", "base_asag", "historical_proposed", "overhaul_proposed"]
    for key in order:
        if key not in metrics_dict:
            continue
        m = metrics_dict[key]
        print(
            f"{m.system_name:<38} | {m.mae:7.4f} | {m.rmse:7.4f} | {format_metric(m.pearson_r):^9} | "
            f"{format_metric(m.spearman_rho):^12} | {format_metric(m.qwk):^7} | {m.n_samples:^5}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run 4-system comparative ASAG benchmark.")
    parser.add_argument(
        "--subset",
        choices=["active", "assignments_1_10", "exams", "all"],
        default="active",
        help="Dataset subset: 'active' (2,273 records), 'assignments_1_10' (1,721), 'exams' (552).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional limit on number of records (e.g. 50 for rapid test).",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="evaluation/results/overhaul_v1",
        help="Directory to export benchmark predictions and summaries.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent.parent
    out_dir = repo_root / args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load dataset
    raw_dataset = MohlerLoader.load_processed_csv()
    if args.subset == "active":
        dataset = raw_dataset.filter_active()
    elif args.subset == "assignments_1_10":
        dataset = raw_dataset.filter_assignments_1_10()
    elif args.subset == "exams":
        dataset = raw_dataset.filter_exams()
    else:
        dataset = raw_dataset

    if args.limit is not None and args.limit > 0:
        records_to_evaluate = dataset.records[: args.limit]
    else:
        records_to_evaluate = dataset.records

    total_records = len(records_to_evaluate)
    logger.info("Initializing benchmark on %d records (%s subset)...", total_records, args.subset)

    # 2. Instantiate Runners
    logger.info("Initializing runners for Systems 1, 2, 3, and 4...")
    baseline_runner = BaselineRunner()
    base_runner = BaseASAGRunner()
    historical_runner = ProposedASAGRunner()
    overhaul_runner = OverhaulASAGRunner()
    error_analyzer = OverhaulErrorAnalyzer()

    # 3. Execute Benchmark
    logger.info("Starting execution across all 4 systems...")
    start_time = time.time()

    rows: List[Dict[str, Any]] = []
    y_true: List[float] = []
    y_pred_baseline: List[float] = []
    y_pred_base: List[float] = []
    y_pred_hist: List[float] = []
    y_pred_overhaul: List[float] = []

    diagnoses_list: List[Any] = []

    # Caching parsed reference answers per question to optimize speed
    ref_base_cache: Dict[str, Any] = {}

    for idx, rec in enumerate(records_to_evaluate):
        if (idx + 1) % 100 == 0 or (idx + 1) == total_records:
            elapsed = time.time() - start_time
            rate = (idx + 1) / max(0.01, elapsed)
            logger.info("Progress: %d/%d (%.1f%%) | Rate: %.1f records/s", idx + 1, total_records, (idx + 1) / total_records * 100, rate)

        stu_text = rec.student_answer_cleaned
        human_score = rec.score_ave

        # System 1: Baseline
        b_pred = baseline_runner.evaluate_pair(
            reference_answer=rec.reference_answer,
            student_answer=stu_text,
            max_points=5.0,
        )

        # System 2: Base ASAG
        base_pred = base_runner.evaluate_triplet(
            question=rec.question,
            reference_answer=rec.reference_answer,
            student_answer=stu_text,
            max_points=5.0,
        )

        # System 3: Historical Proposed ASAG (Stage 14)
        if base_pred.pipeline_result is not None:
            hist_pred = historical_runner.evaluate_base_result(
                base_result=base_pred.pipeline_result,
                max_points=5.0,
            )
        else:
            hist_pred = historical_runner.evaluate_base_result(None, max_points=5.0)

        # System 4: Overhauled Proposed ASAG
        overhaul_pred = overhaul_runner.evaluate_triplet(
            question=rec.question,
            reference_answer=rec.reference_answer,
            student_answer=stu_text,
            max_points=5.0,
        )

        # Accumulate metrics
        y_true.append(human_score)
        y_pred_baseline.append(b_pred.grade)
        y_pred_base.append(base_pred.grade)
        y_pred_hist.append(hist_pred.proposed_grade)
        y_pred_overhaul.append(overhaul_pred.grade)

        # Diagnostic error check on Overhauled system
        disagreement = abs(rec.score_me - rec.score_other)
        rec_diagnoses = error_analyzer.diagnose_record(
            question_id=rec.question_id,
            student_index=rec.student_index,
            question=rec.question,
            reference_answer=rec.reference_answer,
            student_answer=stu_text,
            human_score=human_score,
            system_score=overhaul_pred.grade,
            reference_props_count=overhaul_pred.reference_propositions_count,
            student_props_count=(overhaul_pred.matched_propositions_count + overhaul_pred.unmatched_student_propositions_count),
            matched_props_count=overhaul_pred.matched_propositions_count,
            unmatched_props_count=overhaul_pred.unmatched_student_propositions_count,
            positive_adjustment=overhaul_pred.positive_adjustment,
            negative_adjustment=overhaul_pred.negative_adjustment,
            grader_disagreement=disagreement,
        )
        diagnoses_list.extend(rec_diagnoses)

        # Record dict
        row = {
            "question_id": rec.question_id,
            "assignment": rec.assignment,
            "question_index": rec.question_index,
            "student_index": rec.student_index,
            "human_score": round(human_score, 4),
            "score_me": round(rec.score_me, 4),
            "score_other": round(rec.score_other, 4),
            "baseline_grade": round(b_pred.grade, 4),
            "base_asag_grade": round(base_pred.grade, 4),
            "historical_proposed_grade": round(hist_pred.proposed_grade, 4),
            "overhaul_proposed_grade": round(overhaul_pred.grade, 4),
            "overhaul_base_grade": round(overhaul_pred.base_grade, 4),
            "overhaul_pos_adj": round(overhaul_pred.positive_adjustment, 4),
            "overhaul_neg_adj": round(overhaul_pred.negative_adjustment, 4),
            "overhaul_net_adj": round(overhaul_pred.net_adjustment, 4),
            "overhaul_correct_additional": overhaul_pred.correct_additional_count,
            "overhaul_irrelevant": overhaul_pred.irrelevant_count,
            "overhaul_incorrect": overhaul_pred.incorrect_count,
            "overhaul_uncertain": overhaul_pred.uncertain_count,
            "overhaul_matched_count": overhaul_pred.matched_propositions_count,
            "overhaul_ref_props_count": overhaul_pred.reference_propositions_count,
        }
        rows.append(row)

    total_elapsed = time.time() - start_time
    logger.info("Evaluation complete in %.2f seconds.", total_elapsed)

    # 4. Compute Metrics
    metrics_all: Dict[str, EvaluationMetrics] = {
        "baseline": compute_all_metrics("System 1: TF-IDF Baseline", y_true, y_pred_baseline),
        "base_asag": compute_all_metrics("System 2: Base ASAG", y_true, y_pred_base),
        "historical_proposed": compute_all_metrics("System 3: Historical Proposed ASAG", y_true, y_pred_hist),
        "overhaul_proposed": compute_all_metrics("System 4: Overhauled Proposed ASAG", y_true, y_pred_overhaul),
    }

    # 5. Export Predictions CSV
    pred_csv_path = out_dir / "final_comparison_predictions.csv"
    with open(pred_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    # 6. Export Diagnostic Error Summary
    diag_summary = error_analyzer.analyze_diagnoses_summary(diagnoses_list)
    diag_json_path = out_dir / "diagnostic_error_summary.json"
    with open(diag_json_path, "w", encoding="utf-8") as f:
        json.dump(diag_summary, f, indent=2)

    # 7. Export Benchmark Summary JSON
    summary_meta = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dataset_version": "UNT CS Short Answer Dataset v2.0 (Mohler et al., 2011)",
        "total_evaluated": total_records,
        "elapsed_seconds": round(total_elapsed, 2),
        "subset": args.subset,
        "overall_metrics": {k: v.to_dict() for k, v in metrics_all.items()},
        "diagnostic_error_counts": diag_summary["category_counts"],
    }
    summary_json_path = out_dir / "final_comparison_summary.json"
    with open(summary_json_path, "w", encoding="utf-8") as f:
        json.dump(summary_meta, f, indent=2)

    logger.info("Exported predictions to %s", pred_csv_path)
    logger.info("Exported summary to %s", summary_json_path)

    # 8. Print Comparative Table
    print_comparison_table(f"FINAL COMPARISON ON {total_records} RECORDS ({args.subset.upper()})", metrics_all)


if __name__ == "__main__":
    main()
