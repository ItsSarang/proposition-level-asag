"""
Experiment 5 Formal Mohler Benchmark Evaluation Runner.

Executes the formal benchmark evaluation of Experiment 5 and its 4 ablation variants
on the official UNT CS Short Answer Dataset v2.0 (Mohler et al., 2011).

Evaluates N=2,273 active records across all 81 active questions.
Compares:
- V0: TF-IDF + Cosine Baseline
- V1: Base ASAG (Pure Clausal)
- V2: Historical Proposed ASAG (Stage 15.2 / Stage 17)
- V3: Current Proposed ASAG (Frozen Experiment 1)
- V4: Experiment 4 Severity-Aware Proposed ASAG (Frozen Baseline)
- V5-A: Core Paraphrase Recovery + Non-sentential Fragments + Model D
- V5-B: V5-A + Contradiction Guards + Model D
- V5-C: Frozen Exp 4 Upstream + Model D2
- V5: Full Experiment 5 (V5-A + V5-B + Model D2)

Evaluates 5 subsets:
1. Full active dataset (N=2,273)
2. Assignments 1–10 (N=1,721)
3. Exams 11–12 (N=552)
4. Sentential reference subset (N=1,341)
5. Non-sentential reference subset (N=932)

Exports:
- evaluation/experiments/experiment_5/experiment_5_results.csv
- evaluation/experiments/experiment_5/experiment_5_summary.json
- evaluation/experiments/experiment_5/experiment_5_config.json
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import time
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np

from evaluation.dataset.mohler_loader import MohlerDataset, MohlerLoader, MohlerRecord
from evaluation.metrics.asag_metrics import EvaluationMetrics, compute_all_metrics
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Experiment 5 Mohler ASAG benchmark.")
    parser.add_argument(
        "--output-dir",
        type=str,
        default="evaluation/experiments/experiment_5",
        help="Directory to export Experiment 5 results.",
    )
    parser.add_argument(
        "--exp4-csv",
        type=str,
        default="evaluation/experiments/experiment_4/experiment_4_results.csv",
        help="Path to frozen Experiment 4 results CSV.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional limit on records for quick testing.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[3]
    out_dir = repo_root / args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    exp4_csv_path = repo_root / args.exp4_csv
    if not exp4_csv_path.exists():
        raise FileNotFoundError(f"Experiment 4 results CSV not found at: {exp4_csv_path}")

    # 1. Load Experiment 4 baseline records
    logger.info("Loading frozen Experiment 4 records from %s...", exp4_csv_path)
    exp4_lookup: Dict[str, Dict[str, Any]] = {}
    with open(exp4_csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = f"{row['question_id']}_{row['student_index']}"
            exp4_lookup[key] = row

    logger.info("Loaded %d frozen baseline records.", len(exp4_lookup))

    # 2. Load active dataset (N=2,273)
    raw_dataset = MohlerLoader.load_processed_csv()
    dataset = raw_dataset.filter_active()
    logger.info("Loaded active Mohler dataset with %d active records.", len(dataset.records))

    records_to_evaluate = dataset.records[: args.limit] if (args.limit and args.limit > 0) else dataset.records
    total_records = len(records_to_evaluate)
    logger.info("Starting Experiment 5 benchmark on %d active records...", total_records)

    # 3. Instantiate pipeline variants
    pipeline_v5a = Experiment5Pipeline(variant=Experiment5Variant.V5_A)
    pipeline_v5b = Experiment5Pipeline(variant=Experiment5Variant.V5_B)
    pipeline_v5c = Experiment5Pipeline(variant=Experiment5Variant.V5_C)
    pipeline_v5 = Experiment5Pipeline(variant=Experiment5Variant.V5)

    start_time = time.time()
    failures = 0

    rows: List[Dict[str, Any]] = []
    y_true: List[float] = []
    y_pred_v0: List[float] = []
    y_pred_v1: List[float] = []
    y_pred_v2: List[float] = []
    y_pred_v3: List[float] = []
    y_pred_v4: List[float] = []
    y_pred_v5a: List[float] = []
    y_pred_v5b: List[float] = []
    y_pred_v5c: List[float] = []
    y_pred_v5: List[float] = []

    total_recovered_core = 0
    total_guarded_contra = 0

    for idx, record in enumerate(records_to_evaluate):
        key = f"{record.question_id}_{record.student_index}"
        hist_row = exp4_lookup.get(key)
        if hist_row is None:
            raise KeyError(f"Missing historical record for key: {key}")

        v0_grade = float(hist_row["v0_baseline_grade"])
        v1_grade = float(hist_row["v1_base_asag_grade"])
        v2_grade = float(hist_row["v2_historical_proposed_grade"])
        v3_grade = float(hist_row["v3_current_proposed_grade"])
        v4_grade = float(hist_row["v4_experiment_4_grade"])
        human_score = float(record.score_ave)
        has_non_sentential = hist_row.get("has_non_sentential_ref", "False").lower() in ("true", "1")

        try:
            # Evaluate all 4 new variants
            res_v5 = pipeline_v5.evaluate(
                question=record.question,
                reference_answer=record.reference_answer,
                student_answer=record.student_answer_cleaned,
            )
            res_v5a = pipeline_v5a.evaluate(
                question=record.question,
                reference_answer=record.reference_answer,
                student_answer=record.student_answer_cleaned,
            )
            res_v5b = pipeline_v5b.evaluate(
                question=record.question,
                reference_answer=record.reference_answer,
                student_answer=record.student_answer_cleaned,
            )
            res_v5c = pipeline_v5c.evaluate(
                question=record.question,
                reference_answer=record.reference_answer,
                student_answer=record.student_answer_cleaned,
            )

            v5_grade = res_v5.final_grade
            v5a_grade = res_v5a.final_grade
            v5b_grade = res_v5b.final_grade
            v5c_grade = res_v5c.final_grade
            status = "SUCCESS"

            total_recovered_core += res_v5.recovered_core_count
            total_guarded_contra += res_v5.guarded_contradiction_count

        except Exception as e:
            logger.error("Failure on record %s: %s", key, e)
            failures += 1
            v5_grade = 0.0
            v5a_grade = 0.0
            v5b_grade = 0.0
            v5c_grade = 0.0
            status = f"ERROR: {str(e)}"
            res_v5 = None

        y_true.append(human_score)
        y_pred_v0.append(v0_grade)
        y_pred_v1.append(v1_grade)
        y_pred_v2.append(v2_grade)
        y_pred_v3.append(v3_grade)
        y_pred_v4.append(v4_grade)
        y_pred_v5a.append(v5a_grade)
        y_pred_v5b.append(v5b_grade)
        y_pred_v5c.append(v5c_grade)
        y_pred_v5.append(v5_grade)

        row = {
            "question_id": record.question_id,
            "assignment": record.assignment,
            "question_index": record.question_index,
            "student_index": record.student_index,
            "human_score": human_score,
            "v0_baseline_grade": v0_grade,
            "v1_base_asag_grade": v1_grade,
            "v2_historical_proposed_grade": v2_grade,
            "v3_current_proposed_grade": v3_grade,
            "v4_experiment_4_grade": v4_grade,
            "v5_a_grade": round(v5a_grade, 4),
            "v5_b_grade": round(v5b_grade, 4),
            "v5_c_grade": round(v5c_grade, 4),
            "v5_grade": round(v5_grade, 4),
            "v5_base_raw": round(res_v5.base_score_raw * 5.0, 4) if res_v5 else 0.0,
            "v5_base_effective": round(res_v5.base_score_effective * 5.0, 4) if res_v5 else 0.0,
            "v5_recovered_core_count": res_v5.recovered_core_count if res_v5 else 0,
            "v5_guarded_contra_count": res_v5.guarded_contradiction_count if res_v5 else 0,
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
    logger.info("Benchmark execution completed in %.2fs with %d failures.", elapsed_time, failures)

    # 4. Export results CSV
    results_csv_path = out_dir / "experiment_5_results.csv"
    logger.info("Writing results CSV to %s...", results_csv_path)
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
        "experiment_name": "Experiment 5: Core Paraphrase Recovery, Contradiction Guards, and Model D2",
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
        ("v2_historical_proposed", "V2: Historical Proposed ASAG", y_pred_v2),
        ("v3_current_proposed", "V3: Current Proposed ASAG", y_pred_v3),
        ("v4_experiment_4", "V4: Experiment 4 (Severity-Aware Proposed)", y_pred_v4),
        ("v5_a", "V5-A: Core Recovery + Fragments (Model D)", y_pred_v5a),
        ("v5_b", "V5-B: V5-A + Contradiction Guards (Model D)", y_pred_v5b),
        ("v5_c", "V5-C: Exp 4 Upstream + Model D2 Scorer", y_pred_v5c),
        ("v5_full", "V5: Full Experiment 5 (All Interventions)", y_pred_v5),
    ]

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

        for sys_key, sys_name, y_preds in system_keys:
            sub_y_pred = [y_preds[i] for i in sub_indices]
            # Compute evaluation metrics
            m = compute_all_metrics(sys_name, sub_y_true, sub_y_pred)
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
    summary_path = out_dir / "experiment_5_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    logger.info("Wrote summary JSON to %s.", summary_path)

    # 7. Export config JSON
    config_path = out_dir / "experiment_5_config.json"
    config = {
        "experiment": "Experiment 5",
        "description": "Core Paraphrase Recovery, Canonical Fragments, Contradiction Guards, and Model D2 Scorer",
        "variants": {
            "V4": {"core_recovery": False, "canonical_fragments": False, "contradiction_guards": False, "scorer": "Model D"},
            "V5-A": {"core_recovery": True, "canonical_fragments": True, "contradiction_guards": False, "scorer": "Model D"},
            "V5-B": {"core_recovery": True, "canonical_fragments": True, "contradiction_guards": True, "scorer": "Model D"},
            "V5-C": {"core_recovery": False, "canonical_fragments": False, "contradiction_guards": False, "scorer": "Model D2"},
            "V5": {"core_recovery": True, "canonical_fragments": True, "contradiction_guards": True, "scorer": "Model D2"},
        },
        "model_d2_parameters": {
            "tau_gate": 0.30,
            "gamma": 0.25,
            "max_positive_bonus": 0.25,
            "diminishing_rate": 0.50,
            "core_invalidation_discount": 0.50,
            "minor_penalty_weight": 0.20,
            "max_points": 5.0,
            "sigma_core_threshold": 0.90,
        },
    }
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    logger.info("Wrote config JSON to %s.", config_path)


if __name__ == "__main__":
    main()
