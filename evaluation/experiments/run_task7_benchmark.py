"""
Task 7: Fresh Benchmark Evaluation Runner for Current V0, V1, and V5.

Executes a fresh, fully reproducible evaluation of:
- V0: TF-IDF + Cosine Baseline
- V1: Base ASAG (Basak et al. 2019-inspired clausal semantic/dependency ASAG)
- V5: Current Proposition-Level ASAG with Core Paraphrase Recovery,
      Canonical Reference Handling, Contradiction Guards, and Model D2 Scoring.

Evaluates on the official UNT CS Short Answer Dataset v2.0 (Mohler et al., 2011).
Evaluates all N=2,273 active records across 81 active questions with ground-truth `score_ave`.

Subsets evaluated:
1. Full Active Dataset (N=2,273)
2. Assignments 1–10 (N=1,721)
3. Exams 11–12 (N=552)
4. Sentential Reference Subset (N=1,341)
5. Non-Sentential Reference Subset (N=932)

Exports dedicated, timestamped artifacts to:
- evaluation/results/fresh_v5_benchmark/task7_benchmark_results.csv
- evaluation/results/fresh_v5_benchmark/task7_benchmark_summary.json
- evaluation/results/fresh_v5_benchmark/task7_benchmark_config.json
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
    parser = argparse.ArgumentParser(description="Run Task 7 fresh benchmark on Mohler dataset.")
    parser.add_argument(
        "--output-dir",
        type=str,
        default="evaluation/results/fresh_v5_benchmark",
        help="Directory to export fresh benchmark results.",
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
    logger.info("Task 7 Fresh Benchmark starting at Git revision: %s", git_rev)

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

    # 2. Load active dataset (N=2,273)
    raw_dataset = MohlerLoader.load_processed_csv()
    dataset = raw_dataset.filter_active()
    logger.info("Loaded active Mohler dataset with %d records.", len(dataset.records))

    records_to_evaluate = dataset.records[: args.limit] if (args.limit and args.limit > 0) else dataset.records
    total_records = len(records_to_evaluate)
    logger.info("Evaluating %d records fresh across V0, V1, and V5...", total_records)

    # 3. Instantiate fresh models
    v0_model = get_model("V0", scale=5.0)
    v1_model = get_model("V1", scale=5.0)
    v5_pipeline = Experiment5Pipeline(variant=Experiment5Variant.V5)

    start_time = time.time()
    failures = 0

    rows: List[Dict[str, Any]] = []
    y_true: List[float] = []
    y_pred_v0: List[float] = []
    y_pred_v1: List[float] = []
    y_pred_v5: List[float] = []

    total_recovered_core = 0
    total_guarded_contra = 0

    for idx, record in enumerate(records_to_evaluate):
        key = f"{record.question_id}_{record.student_index}"
        human_score = float(record.score_ave)
        has_non_sentential = non_sentential_lookup.get(key, False)
        stu_text = record.student_answer_cleaned

        # Fresh V0 Evaluation
        try:
            res_v0 = v0_model.evaluate(record.question, record.reference_answer, stu_text)
            v0_grade = float(res_v0.grade)
        except Exception as e:
            logger.error("V0 failure on record %s: %s", key, e)
            v0_grade = 0.0

        # Fresh V1 Evaluation
        try:
            res_v1 = v1_model.evaluate(record.question, record.reference_answer, stu_text)
            v1_grade = float(res_v1.grade)
        except Exception as e:
            logger.error("V1 failure on record %s: %s", key, e)
            v1_grade = 0.0

        # Fresh V5 Evaluation
        try:
            res_v5 = v5_pipeline.evaluate(
                question=record.question,
                reference_answer=record.reference_answer,
                student_answer=stu_text,
            )
            v5_grade = float(res_v5.final_grade)
            status = "SUCCESS"
            total_recovered_core += res_v5.recovered_core_count
            total_guarded_contra += res_v5.guarded_contradiction_count
        except Exception as e:
            logger.error("V5 failure on record %s: %s", key, e)
            failures += 1
            v5_grade = 0.0
            status = f"ERROR: {str(e)}"
            res_v5 = None

        y_true.append(human_score)
        y_pred_v0.append(v0_grade)
        y_pred_v1.append(v1_grade)
        y_pred_v5.append(v5_grade)

        row = {
            "question_id": record.question_id,
            "assignment": record.assignment,
            "question_index": record.question_index,
            "student_index": record.student_index,
            "question": record.question,
            "reference_answer": record.reference_answer,
            "student_answer": stu_text,
            "human_score": human_score,
            "v0_baseline_grade": round(v0_grade, 4),
            "v1_base_asag_grade": round(v1_grade, 4),
            "v5_grade": round(v5_grade, 4),
            "v5_base_raw": round(res_v5.base_score_raw * 5.0, 4) if res_v5 else 0.0,
            "v5_base_effective": round(res_v5.base_score_effective * 5.0, 4) if res_v5 else 0.0,
            "v5_recovered_core_count": res_v5.recovered_core_count if res_v5 else 0,
            "v5_guarded_contra_count": res_v5.guarded_contradiction_count if res_v5 else 0,
            "v5_matched_count": res_v5.counts.get("matched_by_base", 0) if res_v5 else 0,
            "v5_correct_additional_count": res_v5.counts.get("correct_additional", 0) if res_v5 else 0,
            "v5_irrelevant_count": res_v5.counts.get("irrelevant", 0) if res_v5 else 0,
            "v5_uncertain_count": res_v5.counts.get("uncertain", 0) if res_v5 else 0,
            "v5_incorrect_count": res_v5.counts.get("incorrect", 0) if res_v5 else 0,
            "v5_pos_adj": round(res_v5.score_result.positive_adjustment, 4) if res_v5 else 0.0,
            "v5_neg_adj": round(res_v5.score_result.negative_adjustment, 4) if res_v5 else 0.0,
            "v5_net_adj": round(res_v5.score_result.net_adjustment, 4) if res_v5 else 0.0,
            "has_non_sentential_ref": has_non_sentential,
            "status": status,
        }
        rows.append(row)

        if (idx + 1) % 250 == 0 or (idx + 1) == total_records:
            elapsed = time.time() - start_time
            logger.info("Processed %d/%d records in %.1fs...", idx + 1, total_records, elapsed)

    elapsed_time = time.time() - start_time
    logger.info("Benchmark execution finished in %.2fs with %d failures.", elapsed_time, failures)

    # 4. Export fresh results CSV
    results_csv_path = out_dir / "task7_benchmark_results.csv"
    logger.info("Writing fresh results CSV to %s...", results_csv_path)
    fieldnames = list(rows[0].keys())
    with open(results_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    # 5. Compute metrics across all 5 subsets
    indices_overall = list(range(len(rows)))
    indices_asg1_10 = [i for i, r in enumerate(rows) if int(r["assignment"]) <= 10]
    indices_exams = [i for i, r in enumerate(rows) if int(r["assignment"]) in (11, 12)]
    indices_sentential = [i for i, r in enumerate(rows) if not r["has_non_sentential_ref"]]
    indices_non_sentential = [i for i, r in enumerate(rows) if r["has_non_sentential_ref"]]

    subsets = {
        "overall": ("Full Active Dataset (N=2,273)", indices_overall),
        "assignments_1_10": ("Assignments 1-10 (N=1,721)", indices_asg1_10),
        "exams_11_12": ("Exams 11-12 (N=552)", indices_exams),
        "sentential_reference_subset": ("Sentential Reference Subset (N=1,341)", indices_sentential),
        "non_sentential_reference_subset": ("Non-Sentential Reference Subset (N=932)", indices_non_sentential),
    }

    summary: Dict[str, Any] = {
        "benchmark_name": "Task 7: Fresh Benchmark Evaluation of Current V0, V1, and V5",
        "git_commit": git_rev,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_records": len(rows),
        "execution_time_seconds": round(elapsed_time, 2),
        "failures": failures,
        "interventions_summary": {
            "total_recovered_core_propositions": total_recovered_core,
            "total_guarded_contradictions": total_guarded_contra,
        },
        "subsets": {},
    }

    system_keys = [
        ("v0_baseline", "V0: TF-IDF Baseline", y_pred_v0),
        ("v1_base_asag", "V1: Base ASAG", y_pred_v1),
        ("v5_full", "V5: Current Proposition-Level ASAG", y_pred_v5),
    ]

    print("\n" + "=" * 90)
    print("TASK 7 FRESH BENCHMARK RESULTS")
    print("=" * 90)

    for subset_key, (subset_name, sub_indices) in subsets.items():
        if not sub_indices:
            continue
        sub_y_true = [y_true[i] for i in sub_indices]
        subset_dict: Dict[str, Any] = {
            "subset_name": subset_name,
            "n_samples": len(sub_indices),
            "metrics": {},
            "distributions": {
                "human": {
                    "mean": round(float(np.mean(sub_y_true)), 4),
                    "std": round(float(np.std(sub_y_true, ddof=1)), 4) if len(sub_indices) > 1 else 0.0,
                    "min": round(float(np.min(sub_y_true)), 4),
                    "max": round(float(np.max(sub_y_true)), 4),
                }
            },
        }

        print(f"\n### {subset_name}")
        print(f"{'System':<36} | {'MAE':^7} | {'RMSE':^7} | {'Pearson r':^9} | {'Spearman rho':^12} | {'QWK':^7} | {'Mean Pred':^9} | {'Mean Human':^10} | {'N':^5}")
        print("-" * 122)

        for sys_key, sys_name, y_preds in system_keys:
            sub_y_pred = [y_preds[i] for i in sub_indices]
            m = compute_all_metrics(sys_name, sub_y_true, sub_y_pred)
            r_str = f"{m.pearson_r:7.4f}" if m.pearson_r is not None else "  N/A  "
            rho_str = f"{m.spearman_rho:7.4f}" if m.spearman_rho is not None else "   N/A    "
            qwk_str = f"{m.qwk:7.4f}" if m.qwk is not None else "  N/A  "

            print(
                f"{sys_name:<36} | {m.mae:7.4f} | {m.rmse:7.4f} | {r_str:^9} | {rho_str:^12} | "
                f"{qwk_str:^7} | {m.predicted_mean:9.4f} | {m.ground_truth_mean:10.4f} | {m.n_samples:^5}"
            )

            subset_dict["metrics"][sys_key] = {
                "system_name": sys_name,
                "n_samples": len(sub_indices),
                "mae": m.mae,
                "rmse": m.rmse,
                "pearson_r": m.pearson_r,
                "pearson_p": m.pearson_p,
                "spearman_rho": m.spearman_rho,
                "spearman_p": m.spearman_p,
                "qwk": m.qwk,
                "ground_truth_mean": m.ground_truth_mean,
                "ground_truth_std": m.ground_truth_std,
                "predicted_mean": m.predicted_mean,
                "predicted_std": m.predicted_std,
            }
            subset_dict["distributions"][sys_key] = compute_distribution_stats(sub_y_pred, sub_y_true)

        summary["subsets"][subset_key] = subset_dict

    # 6. Export summary JSON
    summary_path = out_dir / "task7_benchmark_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    logger.info("Wrote fresh summary JSON to %s.", summary_path)

    # 7. Export config JSON
    config_path = out_dir / "task7_benchmark_config.json"
    config = {
        "benchmark": "Task 7: Fresh Benchmark Evaluation",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "git_commit": git_rev,
        "dataset": {
            "name": "University of North Texas Computer Science Short Answer Dataset v2.0",
            "citation": "Mohler, M., Bunescu, R., & Mihalcea, R. (2011). Learning to grade short answer questions. ACL 2011.",
            "total_questions": 87,
            "active_questions": 81,
            "total_records": 2442,
            "active_records_evaluated": 2273,
            "target_variable": "score_ave (0.0 to 5.0 scale)",
        },
        "models_evaluated": {
            "V0": {
                "name": "TF-IDF Baseline",
                "module": "models.v0_tfidf.predictor.V0Predictor",
                "scale": 5.0,
            },
            "V1": {
                "name": "Base ASAG (Basak et al. 2019-inspired)",
                "module": "models.v1_base_asag.pipeline.BaseASAGPipeline",
                "scale": 5.0,
            },
            "V5": {
                "name": "Current Proposition-Level ASAG",
                "module": "proposed_asag.pipeline_v5.Experiment5Pipeline",
                "variant": "V5",
                "scale": 5.0,
                "features": {
                    "core_paraphrase_recovery": True,
                    "canonical_fragments": True,
                    "contradiction_guards": True,
                    "model_d2_scoring": True,
                    "deduplication": True,
                },
            },
        },
        "artifact_paths": {
            "results_csv": str(results_csv_path.relative_to(repo_root)),
            "summary_json": str(summary_path.relative_to(repo_root)),
            "config_json": str(config_path.relative_to(repo_root)),
        },
    }
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    logger.info("Wrote config JSON to %s.", config_path)


if __name__ == "__main__":
    main()
