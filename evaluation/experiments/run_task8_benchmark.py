"""
Task 8: Benchmark Evaluation Runner & Additional-Information Layer Ablation.

Executes a fresh evaluation across all N=2,273 active records from the Mohler dataset for:
1. V0: TF-IDF + Cosine Baseline
2. V1: Base ASAG (Clausal semantic/dependency ASAG)
3. V5 Core-Only: Ablation mode (enable_additional_info=False)
4. V5 Full: Post-fix system with preposition epistemic fixes (enable_additional_info=True)

Computes:
- Benchmark metrics (MAE, RMSE, Pearson r, Spearman rho, QWK) on 5 subsets:
  - Full Active (N=2,273)
  - Assignments 1-10 (N=1,721)
  - Exams 11-12 (N=552)
  - Sentential Reference (N=1,341)
  - Non-Sentential Reference (N=932)
- Comparative ablation between V5 Core-Only and V5 Full.
- Exact per-record deltas against Task 7 baseline (identifying resolved false contradictions).
- Targeted inspection of Q6.1 (pointer) and Q11.10 (merge sort).

Exports dedicated artifacts to:
- evaluation/results/task8_benchmark/mohler_task8_evaluation_predictions.csv
- evaluation/results/task8_benchmark/mohler_task8_evaluation_summary.json
- evaluation/results/task8_benchmark/mohler_task8_evaluation_config.json
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import subprocess
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from evaluation.dataset.mohler_loader import MohlerDataset, MohlerLoader, MohlerRecord
from evaluation.metrics.asag_metrics import EvaluationMetrics, compute_all_metrics
from models.registry import get_model
from proposed_asag.pipeline_v5 import Experiment5Pipeline, Experiment5Variant

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def compute_distribution_stats(grades: List[float], human_grades: List[float]) -> Dict[str, Any]:
    """Compute descriptive distribution statistics and bias relative to human grades."""
    arr = np.array(grades, dtype=float)
    h_arr = np.array(human_grades, dtype=float)

    mean_val = float(np.mean(arr))
    std_val = float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.0
    min_val = float(np.min(arr))
    max_val = float(np.max(arr))
    bias = float(mean_val - np.mean(h_arr))

    pct_near_zero = float(np.mean(arr <= 0.5) * 100.0)
    pct_exactly_zero = float(np.mean(arr == 0.0) * 100.0)
    pct_near_five = float(np.mean(arr >= 4.0) * 100.0)

    return {
        "mean": round(mean_val, 4),
        "std": round(std_val, 4),
        "min": round(min_val, 4),
        "max": round(max_val, 4),
        "descriptive_bias": round(bias, 4),
        "pct_near_zero": round(pct_near_zero, 2),
        "pct_exactly_zero": round(pct_exactly_zero, 2),
        "pct_high_grade": round(pct_near_five, 2),
    }


def get_git_revision() -> str:
    """Retrieve current git revision hash."""
    try:
        rev = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
        return rev
    except Exception:
        return "UNKNOWN_REVISION"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Task 8 benchmark and ablation on Mohler dataset.")
    parser.add_argument(
        "--output-dir",
        type=str,
        default="evaluation/results/task8_benchmark",
        help="Directory to export Task 8 benchmark results.",
    )
    parser.add_argument(
        "--task7-csv",
        type=str,
        default="evaluation/results/fresh_v5_benchmark/task7_benchmark_results.csv",
        help="Path to Task 7 results CSV for delta comparisons.",
    )
    parser.add_argument(
        "--exp4-csv",
        type=str,
        default="evaluation/experiments/experiment_4/experiment_4_results.csv",
        help="Path to historical results CSV for sentential/non-sentential reference flags.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional limit on records for quick diagnostics.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent.parent
    out_dir = repo_root / args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    git_rev = get_git_revision()
    logger.info("Task 8 Benchmark starting at Git revision: %s", git_rev)

    # 1. Load historical metadata for reference structure labels
    exp4_csv_path = repo_root / args.exp4_csv
    non_sentential_lookup: Dict[str, bool] = {}
    if exp4_csv_path.exists():
        logger.info("Loading reference structure flags from %s...", exp4_csv_path)
        with open(exp4_csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = f"{row['question_id']}_{row['student_index']}"
                non_sentential_lookup[key] = (
                    row.get("has_non_sentential_ref", "False").lower() in ("true", "1")
                )
        logger.info("Loaded reference structure metadata for %d records.", len(non_sentential_lookup))
    else:
        logger.warning("Historical CSV not found; non-sentential flags will be defaulted to False.")

    # 2. Load Task 7 results for per-record delta comparison
    task7_csv_path = repo_root / args.task7_csv
    task7_lookup: Dict[str, float] = {}
    if task7_csv_path.exists():
        logger.info("Loading Task 7 baseline predictions from %s...", task7_csv_path)
        with open(task7_csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = f"{row['question_id']}_{row['student_index']}"
                task7_lookup[key] = float(row.get("v5_grade", 0.0))
        logger.info("Loaded Task 7 predictions for %d records.", len(task7_lookup))
    else:
        logger.warning("Task 7 CSV not found at %s; delta columns will be defaulted to 0.0.", task7_csv_path)

    # 3. Load active dataset (N=2,273)
    raw_dataset = MohlerLoader.load_processed_csv()
    dataset = raw_dataset.filter_active()
    logger.info("Loaded active Mohler dataset with %d records.", len(dataset.records))

    records_to_evaluate = dataset.records[: args.limit] if (args.limit and args.limit > 0) else dataset.records
    total_records = len(records_to_evaluate)
    logger.info("Evaluating %d records fresh across V0, V1, V5 Core-Only, and V5 Full...", total_records)

    # 4. Instantiate fresh models
    v0_model = get_model("V0", scale=5.0)
    v1_model = get_model("V1", scale=5.0)
    v5_core_pipeline = Experiment5Pipeline(variant=Experiment5Variant.V5, enable_additional_info=False)
    v5_full_pipeline = Experiment5Pipeline(variant=Experiment5Variant.V5, enable_additional_info=True)

    start_time = time.time()
    failures_core = 0
    failures_full = 0

    rows: List[Dict[str, Any]] = []
    y_true: List[float] = []
    y_pred_v0: List[float] = []
    y_pred_v1: List[float] = []
    y_pred_v5_core: List[float] = []
    y_pred_v5_full: List[float] = []
    y_pred_task7: List[float] = []

    total_recovered_core = 0
    total_guarded_contra = 0

    for idx, record in enumerate(records_to_evaluate):
        key = f"{record.question_id}_{record.student_index}"
        human_score = float(record.score_ave)
        has_non_sentential = non_sentential_lookup.get(key, False)
        stu_text = record.student_answer_cleaned
        t7_grade = task7_lookup.get(key, float("nan"))

        # V0 Evaluation
        try:
            res_v0 = v0_model.evaluate(record.question, record.reference_answer, stu_text)
            v0_grade = float(res_v0.grade)
        except Exception as e:
            logger.error("V0 failure on record %s: %s", key, e)
            v0_grade = 0.0

        # V1 Evaluation
        try:
            res_v1 = v1_model.evaluate(record.question, record.reference_answer, stu_text)
            v1_grade = float(res_v1.grade)
        except Exception as e:
            logger.error("V1 failure on record %s: %s", key, e)
            v1_grade = 0.0

        # V5 Core-Only Evaluation (Ablation)
        try:
            res_v5_core = v5_core_pipeline.evaluate(
                question=record.question,
                reference_answer=record.reference_answer,
                student_answer=stu_text,
            )
            v5_core_grade = float(res_v5_core.final_grade)
        except Exception as e:
            logger.error("V5 Core failure on record %s: %s", key, e)
            failures_core += 1
            v5_core_grade = 0.0

        # V5 Full Evaluation (Post-Fix)
        try:
            res_v5_full = v5_full_pipeline.evaluate(
                question=record.question,
                reference_answer=record.reference_answer,
                student_answer=stu_text,
            )
            v5_full_grade = float(res_v5_full.final_grade)
            status = "SUCCESS"
            total_recovered_core += res_v5_full.recovered_core_count
            total_guarded_contra += res_v5_full.guarded_contradiction_count
        except Exception as e:
            logger.error("V5 Full failure on record %s: %s", key, e)
            failures_full += 1
            v5_full_grade = 0.0
            status = f"ERROR: {str(e)}"
            res_v5_full = None

        y_true.append(human_score)
        y_pred_v0.append(v0_grade)
        y_pred_v1.append(v1_grade)
        y_pred_v5_core.append(v5_core_grade)
        y_pred_v5_full.append(v5_full_grade)
        if not np.isnan(t7_grade):
            y_pred_task7.append(t7_grade)

        delta_t8_vs_t7 = (v5_full_grade - t7_grade) if not np.isnan(t7_grade) else 0.0
        delta_full_vs_core = v5_full_grade - v5_core_grade

        # Row dictionary
        row = {
            "question_id": record.question_id,
            "assignment": record.assignment,
            "student_index": record.student_index,
            "question_text": record.question,
            "reference_text": record.reference_answer,
            "student_text": stu_text,
            "human_score": round(human_score, 4),
            "v0_grade": round(v0_grade, 4),
            "v1_grade": round(v1_grade, 4),
            "task7_v5_grade": round(t7_grade, 4) if not np.isnan(t7_grade) else "",
            "v5_core_grade": round(v5_core_grade, 4),
            "v5_full_grade": round(v5_full_grade, 4),
            "delta_t8_vs_t7": round(delta_t8_vs_t7, 4),
            "delta_full_vs_core": round(delta_full_vs_core, 4),
            "has_non_sentential_ref": has_non_sentential,
            "status": status,
        }

        if res_v5_full:
            row.update({
                "base_coverage": round(res_v5_full.base_score_effective, 4),
                "recovered_core_count": res_v5_full.recovered_core_count,
                "guarded_contra_count": res_v5_full.guarded_contradiction_count,
                "has_core_invalidation": res_v5_full.score_result.has_core_invalidation,
                "matched_count": res_v5_full.counts.get("matched", 0),
                "correct_additional_count": res_v5_full.counts.get("correct_additional", 0),
                "incorrect_count": res_v5_full.counts.get("incorrect", 0),
                "irrelevant_count": res_v5_full.counts.get("irrelevant", 0),
                "uncertain_count": res_v5_full.counts.get("uncertain", 0),
            })
        rows.append(row)

        if (idx + 1) % 200 == 0 or (idx + 1) == total_records:
            elapsed = time.time() - start_time
            logger.info("Processed %d / %d records (%.1fs elapsed)...", idx + 1, total_records, elapsed)

    elapsed_total = time.time() - start_time
    logger.info("Finished evaluation in %.2fs. Full Failures: %d, Core Failures: %d", elapsed_total, failures_full, failures_core)

    # 5. Export Predictions CSV
    csv_path = out_dir / "mohler_task8_evaluation_predictions.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    logger.info("Exported predictions CSV to %s", csv_path)

    # 6. Compute Metrics across Subsets
    def get_subset_indices(predicate) -> List[int]:
        return [i for i, r in enumerate(records_to_evaluate) if predicate(r, rows[i])]

    all_indices = list(range(len(records_to_evaluate)))
    assign_indices = get_subset_indices(lambda r, row: str(r.assignment) in [str(i) for i in range(1, 11)])
    exam_indices = get_subset_indices(lambda r, row: str(r.assignment) in ["11", "12"])
    sentential_indices = get_subset_indices(lambda r, row: not row["has_non_sentential_ref"])
    non_sentential_indices = get_subset_indices(lambda r, row: row["has_non_sentential_ref"])

    subsets = {
        "full_active": (all_indices, "Full Active Dataset (N=2,273)"),
        "assignments_1_10": (assign_indices, "Assignments 1-10 (N=1,721)"),
        "exams_11_12": (exam_indices, "Exams 11-12 (N=552)"),
        "sentential_ref": (sentential_indices, "Sentential Reference Subset (N=1,341)"),
        "non_sentential_ref": (non_sentential_indices, "Non-Sentential Reference Subset (N=932)"),
    }

    models_to_eval = {
        "V0": y_pred_v0,
        "V1": y_pred_v1,
        "V5_Core_Only": y_pred_v5_core,
        "V5_Full": y_pred_v5_full,
    }
    if len(y_pred_task7) == len(y_true):
        models_to_eval["Task7_V5"] = y_pred_task7

    summary_metrics: Dict[str, Any] = {}

    for subset_key, (indices, subset_desc) in subsets.items():
        if not indices:
            continue
        sub_y_true = [y_true[i] for i in indices]
        summary_metrics[subset_key] = {
            "description": subset_desc,
            "n_records": len(indices),
            "models": {},
        }
        for m_name, preds in models_to_eval.items():
            sub_y_pred = [preds[i] for i in indices]
            m_metrics = compute_all_metrics(m_name, sub_y_true, sub_y_pred)
            dist_stats = compute_distribution_stats(sub_y_pred, sub_y_true)
            summary_metrics[subset_key]["models"][m_name] = {
                "metrics": m_metrics.to_dict(),
                "distribution": dist_stats,
            }

    # 7. Delta Analysis & Key Targets Inspection
    deltas = [r["delta_t8_vs_t7"] for r in rows if r["task7_v5_grade"] != ""]
    positive_deltas = [d for d in deltas if d > 0.05]
    negative_deltas = [d for d in deltas if d < -0.05]
    zero_deltas = [d for d in deltas if abs(d) <= 0.05]

    previously_zero_now_positive = [
        r for r in rows
        if r["task7_v5_grade"] != "" and float(r["task7_v5_grade"]) == 0.0 and float(r["v5_full_grade"]) > 0.5
    ]

    # Specific Target Case Inspections:
    # 1. Pointer (Q6.1)
    pointer_cases = [
        r for r in rows
        if r["question_id"] == "6.1"
    ]
    # 2. Merge Sort (Q11.10)
    merge_sort_cases = [
        r for r in rows
        if r["question_id"] == "11.10"
    ]

    delta_analysis = {
        "n_evaluated_with_task7": len(deltas),
        "n_improved_score": len(positive_deltas),
        "n_reduced_score": len(negative_deltas),
        "n_unchanged_score": len(zero_deltas),
        "n_previously_zero_now_positive": len(previously_zero_now_positive),
        "target_case_pointer_q6_1": [
            {
                "student_index": r["student_index"],
                "student_text": r["student_text"],
                "human_score": r["human_score"],
                "task7_grade": r["task7_v5_grade"],
                "v5_full_grade": r["v5_full_grade"],
                "delta": r["delta_t8_vs_t7"],
            }
            for r in pointer_cases[:5]
        ],
        "target_case_merge_sort_q11_10": [
            {
                "student_index": r["student_index"],
                "student_text": r["student_text"],
                "human_score": r["human_score"],
                "task7_grade": r["task7_v5_grade"],
                "v5_full_grade": r["v5_full_grade"],
                "delta": r["delta_t8_vs_t7"],
            }
            for r in merge_sort_cases[:5]
        ],
    }

    # 8. Export Summary JSON
    summary_data = {
        "benchmark_run_timestamp": datetime.now(timezone.utc).isoformat(),
        "git_revision": git_rev,
        "elapsed_seconds": round(elapsed_total, 2),
        "total_active_records": total_records,
        "full_failures": failures_full,
        "core_failures": failures_core,
        "total_recovered_core_propositions": total_recovered_core,
        "total_guarded_contradictions": total_guarded_contra,
        "delta_analysis": delta_analysis,
        "subsets": summary_metrics,
    }

    summary_json_path = out_dir / "mohler_task8_evaluation_summary.json"
    with open(summary_json_path, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2)
    logger.info("Exported summary JSON to %s", summary_json_path)

    # 9. Export Config JSON
    config_data = {
        "output_dir": str(out_dir),
        "task7_csv": str(task7_csv_path),
        "exp4_csv": str(exp4_csv_path),
        "dataset_active_count": len(dataset.records),
        "git_revision": git_rev,
        "models_evaluated": list(models_to_eval.keys()),
    }
    config_json_path = out_dir / "mohler_task8_evaluation_config.json"
    with open(config_json_path, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=2)
    logger.info("Exported config JSON to %s", config_json_path)

    # 10. Print Console Summary Table
    print("\n" + "=" * 90)
    print(f"TASK 8 BENCHMARK & ABLATION SUMMARY — FULL ACTIVE DATASET (N={len(y_true)})")
    print("=" * 90)
    print(f"{'Model':<16} | {'MAE':<7} | {'RMSE':<7} | {'Pearson r':<9} | {'Spearman rho':<12} | {'QWK':<7}")
    print("-" * 90)
    full_models = summary_metrics["full_active"]["models"]
    for m_name in ["V0", "V1", "Task7_V5", "V5_Core_Only", "V5_Full"]:
        if m_name in full_models:
            mets = full_models[m_name]["metrics"]
            p_r = mets["pearson_r"]
            s_rho = mets["spearman_rho"]
            qwk_v = mets["qwk"]
            p_r_str = f"{p_r:.4f}" if p_r is not None else "N/A"
            s_rho_str = f"{s_rho:.4f}" if s_rho is not None else "N/A"
            qwk_str = f"{qwk_v:.4f}" if qwk_v is not None else "N/A"
            print(f"{m_name:<16} | {mets['mae']:<7.4f} | {mets['rmse']:<7.4f} | {p_r_str:<9} | {s_rho_str:<12} | {qwk_str:<7}")
    print("=" * 90)


if __name__ == "__main__":
    main()
