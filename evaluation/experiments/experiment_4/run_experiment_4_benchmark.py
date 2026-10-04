"""
Experiment 4: Severity-Aware Proposed ASAG Benchmark Runner.

Executes the formal frozen benchmark evaluation of System 5 (Severity-Aware Proposed ASAG)
on the official UNT CS Short Answer Dataset v2.0 (Mohler et al., 2011).

Evaluates N=2,273 active records across all 81 active questions.
Compares:
- System 1 (V0): TF-IDF + Cosine Baseline
- System 2 (V1): Base ASAG
- System 3 (V2): Historical Proposed ASAG (Stage 15.2 / Stage 17)
- System 4 (V3): Current Proposed ASAG (Frozen Experiment 1)
- System 5 (V4): Experiment 4 — Severity-Aware Proposed ASAG

Exports:
- evaluation/experiments/experiment_4/experiment_4_results.csv
- evaluation/experiments/experiment_4/experiment_4_summary.json
- evaluation/experiments/experiment_4/experiment_4_propositions.json
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
from proposed_asag.scoring.severity_aware_scorer import SeverityAwarePipeline

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

    # Proportions near boundaries (within 0.5 of 0.0 or 5.0)
    pct_near_zero = float(np.mean(arr <= 0.5) * 100.0)
    pct_near_five = float(np.mean(arr >= 4.5) * 100.0)

    return {
        "mean": round(mean_val, 4),
        "std": round(std_val, 4),
        "min": round(min_val, 4),
        "max": round(max_val, 4),
        "descriptive_bias": round(bias, 4),
        "pct_near_zero": round(pct_near_zero, 2),
        "pct_near_five": round(pct_near_five, 2),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Experiment 4 Mohler ASAG benchmark.")
    parser.add_argument(
        "--output-dir",
        type=str,
        default="evaluation/experiments/experiment_4",
        help="Directory to export Experiment 4 results.",
    )
    parser.add_argument(
        "--historical-csv",
        type=str,
        default="evaluation/results/experiment_2_representation/experiment_2_results.csv",
        help="Path to frozen historical benchmark results CSV.",
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

    hist_csv_path = repo_root / args.historical_csv
    if not hist_csv_path.exists():
        raise FileNotFoundError(f"Historical results CSV not found at: {hist_csv_path}")

    # 1. Load historical predictions
    logger.info("Loading historical predictions from %s...", hist_csv_path)
    hist_lookup: Dict[str, Dict[str, Any]] = {}
    with open(hist_csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            key = f"{r['question_id']}_{r['student_index']}"
            hist_lookup[key] = r

    # 2. Load active dataset
    raw_dataset = MohlerLoader.load_processed_csv()
    dataset = raw_dataset.filter_active()

    if args.limit is not None and args.limit > 0:
        records_to_evaluate = dataset.records[: args.limit]
    else:
        records_to_evaluate = dataset.records

    total_records = len(records_to_evaluate)
    logger.info("Starting Experiment 4 benchmark on %d active records...", total_records)

    # 3. Instantiate pipeline
    pipeline = SeverityAwarePipeline()

    start_time = time.time()
    failures = 0

    rows: List[Dict[str, Any]] = []
    y_true: List[float] = []
    y_pred_v0: List[float] = []
    y_pred_v1: List[float] = []
    y_pred_v2: List[float] = []
    y_pred_v3: List[float] = []
    y_pred_v4: List[float] = []

    detailed_propositions: List[Dict[str, Any]] = []

    # Aggregator counters for additional information analysis
    answers_with_unmatched = 0
    total_unmatched_propositions = 0
    cat_counts = {
        "CORRECT_ADDITIONAL": 0,
        "IRRELEVANT": 0,
        "UNCERTAIN": 0,
        "INCORRECT": 0,
    }
    sev_counts = {
        "CORE_CONTRADICTION": 0,
        "MODERATE": 0,
        "MINOR": 0,
        "UNRESOLVED": 0,
        "NONE": 0,
    }
    adj_direction_counts = {
        "positive": 0,
        "negative": 0,
        "zero": 0,
    }
    positive_adjustments: List[float] = []
    negative_adjustments: List[float] = []
    net_adjustments: List[float] = []

    for idx, record in enumerate(records_to_evaluate):
        key = f"{record.question_id}_{record.student_index}"
        hist_row = hist_lookup.get(key)
        if hist_row is None:
            raise KeyError(f"Missing historical record for key: {key}")

        v0_grade = float(hist_row["v0_baseline_grade"])
        v1_grade = float(hist_row["v1_base_asag_grade"])
        v2_grade = float(hist_row["v2_historical_proposed_grade"])
        v3_grade = float(hist_row["v3_current_proposed_grade"])
        human_score = float(record.score_ave)
        has_non_sentential = hist_row.get("has_non_sentential_ref", "False").lower() in ("true", "1")

        try:
            eval_res = pipeline.evaluate(
                question=record.question,
                reference_answer=record.reference_answer,
                student_answer=record.student_answer_cleaned,
            )
            score_res = eval_res.score_result
            v4_grade = score_res.final_grade
            status = "SUCCESS"
        except Exception as e:
            logger.error("Failure on record %s: %s", key, e)
            failures += 1
            v4_grade = 0.0
            status = f"ERROR: {str(e)}"
            score_res = None

        y_true.append(human_score)
        y_pred_v0.append(v0_grade)
        y_pred_v1.append(v1_grade)
        y_pred_v2.append(v2_grade)
        y_pred_v3.append(v3_grade)
        y_pred_v4.append(v4_grade)

        # Additional information stats
        if score_res:
            unmatched_cnt = score_res.counts.get("correct_additional", 0) + \
                            score_res.counts.get("irrelevant", 0) + \
                            score_res.counts.get("uncertain", 0) + \
                            score_res.counts.get("incorrect", 0)
            if unmatched_cnt > 0:
                answers_with_unmatched += 1
                total_unmatched_propositions += unmatched_cnt

            cat_counts["CORRECT_ADDITIONAL"] += score_res.counts.get("correct_additional", 0)
            cat_counts["IRRELEVANT"] += score_res.counts.get("irrelevant", 0)
            cat_counts["UNCERTAIN"] += score_res.counts.get("uncertain", 0)
            cat_counts["INCORRECT"] += score_res.counts.get("incorrect", 0)

            # Adjustment direction
            net_adj = score_res.net_adjustment
            net_adjustments.append(net_adj)
            if score_res.positive_adjustment > 0:
                positive_adjustments.append(score_res.positive_adjustment)
            if score_res.negative_adjustment > 0:
                negative_adjustments.append(score_res.negative_adjustment)

            if net_adj > 1e-4:
                adj_direction_counts["positive"] += 1
            elif net_adj < -1e-4:
                adj_direction_counts["negative"] += 1
            else:
                adj_direction_counts["zero"] += 1

            # Count severities from itemized adjustments
            rec_minor = 0
            rec_moderate = 0
            rec_core = 0
            rec_unresolved = 0

            for it in score_res.itemized_adjustments:
                if it.classification != "MATCHED_BY_BASE_ASAG":
                    sev_level = it.severity_level
                    if sev_level in sev_counts:
                        sev_counts[sev_level] += 1
                    if sev_level == "MINOR":
                        rec_minor += 1
                    elif sev_level == "MODERATE":
                        rec_moderate += 1
                    elif sev_level == "CORE_CONTRADICTION":
                        rec_core += 1
                    elif sev_level == "UNRESOLVED":
                        rec_unresolved += 1

                    detailed_propositions.append({
                        "question_id": record.question_id,
                        "student_index": record.student_index,
                        "human_score": human_score,
                        "v4_grade": round(v4_grade, 4),
                        "proposition_text": it.proposition_text,
                        "classification": it.classification,
                        "severity_level": it.severity_level,
                        "severity_score": it.severity_score,
                        "contradiction_type": it.contradiction_type,
                        "evidence_strength": it.evidence_strength,
                        "adjustment_value": it.adjustment_value,
                        "rationale": it.rationale,
                    })

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
                "v4_experiment_4_grade": round(v4_grade, 4),
                "v4_base_normalized": round(score_res.base_score, 4),
                "v4_base_grade": round(score_res.base_score * 5.0, 4),
                "v4_core_effective_score": round(score_res.core_effective_score, 4),
                "v4_has_core_invalidation": score_res.has_core_invalidation,
                "v4_core_contradiction_count": score_res.core_contradiction_count,
                "v4_pos_adj": round(score_res.positive_adjustment, 4),
                "v4_neg_adj": round(score_res.negative_adjustment, 4),
                "v4_net_adj": round(score_res.net_adjustment, 4),
                "v4_is_clipped_upper": score_res.is_clipped_upper,
                "v4_is_clipped_lower": score_res.is_clipped_lower,
                "v4_matched_count": score_res.counts.get("matched", 0),
                "v4_unmatched_count": unmatched_cnt,
                "v4_correct_additional_count": score_res.counts.get("correct_additional", 0),
                "v4_incorrect_count": score_res.counts.get("incorrect", 0),
                "v4_irrelevant_count": score_res.counts.get("irrelevant", 0),
                "v4_uncertain_count": score_res.counts.get("uncertain", 0),
                "v4_minor_count": rec_minor,
                "v4_moderate_count": rec_moderate,
                "v4_core_count": rec_core,
                "v4_unresolved_count": rec_unresolved,
                "has_non_sentential_ref": has_non_sentential,
                "status": status,
                "explanation": score_res.explanation,
            }
        else:
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
                "v4_experiment_4_grade": 0.0,
                "v4_base_normalized": 0.0,
                "v4_base_grade": 0.0,
                "v4_core_effective_score": 0.0,
                "v4_has_core_invalidation": False,
                "v4_core_contradiction_count": 0,
                "v4_pos_adj": 0.0,
                "v4_neg_adj": 0.0,
                "v4_net_adj": 0.0,
                "v4_is_clipped_upper": False,
                "v4_is_clipped_lower": False,
                "v4_matched_count": 0,
                "v4_unmatched_count": 0,
                "v4_correct_additional_count": 0,
                "v4_incorrect_count": 0,
                "v4_irrelevant_count": 0,
                "v4_uncertain_count": 0,
                "v4_minor_count": 0,
                "v4_moderate_count": 0,
                "v4_core_count": 0,
                "v4_unresolved_count": 0,
                "has_non_sentential_ref": has_non_sentential,
                "status": status,
                "explanation": "Execution failure",
            }

        rows.append(row)

        if (idx + 1) % 250 == 0 or (idx + 1) == total_records:
            elapsed = time.time() - start_time
            rate = (idx + 1) / elapsed
            logger.info("Processed %d / %d records (%.1f rec/s)...", idx + 1, total_records, rate)

    total_time = time.time() - start_time
    logger.info("Completed evaluation in %.1f seconds (failures: %d)", total_time, failures)

    # 4. Compute Metrics across Subsets
    def get_metrics_for_indices(indices: List[int], subset_name: str) -> Dict[str, Any]:
        if not indices:
            return {
                "subset_name": subset_name,
                "n_samples": 0,
                "metrics": {},
                "distributions": {},
            }
        sub_true = [y_true[i] for i in indices]
        sub_v0 = [y_pred_v0[i] for i in indices]
        sub_v1 = [y_pred_v1[i] for i in indices]
        sub_v2 = [y_pred_v2[i] for i in indices]
        sub_v3 = [y_pred_v3[i] for i in indices]
        sub_v4 = [y_pred_v4[i] for i in indices]

        m_v0 = compute_all_metrics("V0: TF-IDF Baseline", sub_true, sub_v0).to_dict()
        m_v1 = compute_all_metrics("V1: Base ASAG", sub_true, sub_v1).to_dict()
        m_v2 = compute_all_metrics("V2: Historical Proposed ASAG", sub_true, sub_v2).to_dict()
        m_v3 = compute_all_metrics("V3: Current Proposed ASAG", sub_true, sub_v3).to_dict()
        m_v4 = compute_all_metrics("V4: Experiment 4 (Severity-Aware Proposed)", sub_true, sub_v4).to_dict()

        dist_human = {
            "mean": round(float(np.mean(sub_true)), 4),
            "std": round(float(np.std(sub_true, ddof=1)), 4),
            "min": round(float(np.min(sub_true)), 4),
            "max": round(float(np.max(sub_true)), 4),
        }
        dist_v0 = compute_distribution_stats(sub_v0, sub_true)
        dist_v1 = compute_distribution_stats(sub_v1, sub_true)
        dist_v2 = compute_distribution_stats(sub_v2, sub_true)
        dist_v3 = compute_distribution_stats(sub_v3, sub_true)
        dist_v4 = compute_distribution_stats(sub_v4, sub_true)

        return {
            "subset_name": subset_name,
            "n_samples": len(indices),
            "metrics": {
                "v0_baseline": m_v0,
                "v1_base_asag": m_v1,
                "v2_historical_proposed": m_v2,
                "v3_current_proposed": m_v3,
                "v4_experiment_4": m_v4,
            },
            "distributions": {
                "human": dist_human,
                "v0_baseline": dist_v0,
                "v1_base_asag": dist_v1,
                "v2_historical_proposed": dist_v2,
                "v3_current_proposed": dist_v3,
                "v4_experiment_4": dist_v4,
            }
        }

    all_indices = list(range(total_records))
    asgn_indices = [i for i, r in enumerate(rows) if r["assignment"] <= 10]
    exam_indices = [i for i, r in enumerate(rows) if r["assignment"] >= 11]
    sent_indices = [i for i, r in enumerate(rows) if not r["has_non_sentential_ref"]]
    non_sent_indices = [i for i, r in enumerate(rows) if r["has_non_sentential_ref"]]

    subset_results = {
        "overall": get_metrics_for_indices(all_indices, "Full Active Dataset (N=2,273)"),
        "assignments_1_10": get_metrics_for_indices(asgn_indices, "Assignments 1-10 (N=1,721)"),
        "exams_11_12": get_metrics_for_indices(exam_indices, "Exams 11-12 (N=552)"),
        "sentential_reference_subset": get_metrics_for_indices(sent_indices, "Sentential Reference Subset (N=1,341)"),
        "non_sentential_reference_subset": get_metrics_for_indices(non_sent_indices, "Non-Sentential Reference Subset (N=932)"),
    }

    # 5. Additional Information Summary
    additional_info_summary = {
        "answers_with_unmatched_propositions": answers_with_unmatched,
        "answers_with_unmatched_pct": round(answers_with_unmatched / max(1, total_records) * 100.0, 2),
        "total_unmatched_propositions": total_unmatched_propositions,
        "category_counts": cat_counts,
        "category_proportions": {
            k: round(v / max(1, total_unmatched_propositions) * 100.0, 2)
            for k, v in cat_counts.items()
        },
        "severity_counts": sev_counts,
        "adjustment_direction_counts": adj_direction_counts,
        "adjustment_direction_proportions": {
            k: round(v / max(1, total_records) * 100.0, 2)
            for k, v in adj_direction_counts.items()
        },
        "mean_positive_adjustment": round(float(np.mean(positive_adjustments)), 4) if positive_adjustments else 0.0,
        "mean_negative_adjustment": round(float(np.mean(negative_adjustments)), 4) if negative_adjustments else 0.0,
        "mean_net_adjustment": round(float(np.mean(net_adjustments)), 4) if net_adjustments else 0.0,
    }

    # 6. Export Results
    results_csv_path = out_dir / "experiment_4_results.csv"
    with open(results_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    logger.info("Exported results CSV: %s", results_csv_path)

    props_json_path = out_dir / "experiment_4_propositions.json"
    with open(props_json_path, "w", encoding="utf-8") as f:
        json.dump(detailed_propositions, f, indent=2)
    logger.info("Exported propositions JSON (%d items): %s", len(detailed_propositions), props_json_path)

    summary_json_path = out_dir / "experiment_4_summary.json"
    full_summary = {
        "experiment_name": "Experiment 4: Severity-Aware Proposed ASAG",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_records": total_records,
        "execution_time_seconds": round(total_time, 2),
        "failures": failures,
        "subsets": subset_results,
        "additional_information_summary": additional_info_summary,
    }
    with open(summary_json_path, "w", encoding="utf-8") as f:
        json.dump(full_summary, f, indent=2)
    logger.info("Exported summary JSON: %s", summary_json_path)

    # 7. Print Console Summary
    print("\n" + "=" * 80)
    print("EXPERIMENT 4 BENCHMARK EXECUTION COMPLETED")
    print("=" * 80)
    print(f"Total active records: {total_records}")
    print(f"Execution time:       {total_time:.1f}s ({total_records/total_time:.1f} rec/s)")
    print(f"Failures:             {failures}")
    print("\nPRIMARY OVERALL COMPARISON (N=2,273):")
    ov_m = subset_results["overall"]["metrics"]
    print(f"{'System':<40} | {'MAE':^7} | {'RMSE':^7} | {'Pearson':^8} | {'Spearman':^8} | {'QWK':^7}")
    print("-" * 88)
    for skey, sname in [
        ("v0_baseline", "V0: TF-IDF Baseline"),
        ("v1_base_asag", "V1: Base ASAG"),
        ("v2_historical_proposed", "V2: Historical Proposed ASAG"),
        ("v3_current_proposed", "V3: Current Proposed ASAG"),
        ("v4_experiment_4", "V4: Experiment 4 (Severity-Aware)"),
    ]:
        m = ov_m[skey]
        p_val = f"{m['pearson_r']:.4f}" if m['pearson_r'] is not None else "  N/A  "
        s_val = f"{m['spearman_rho']:.4f}" if m['spearman_rho'] is not None else "  N/A  "
        q_val = f"{m['qwk']:.4f}" if m['qwk'] is not None else "  N/A  "
        print(f"{sname:<40} | {m['mae']:7.4f} | {m['rmse']:7.4f} | {p_val:^8} | {s_val:^8} | {q_val:^7}")


if __name__ == "__main__":
    main()
