"""CLI Experiment Script: Run Mohler ASAG Evaluation (Stage 15.2).

Executes the three ASAG systems (Baseline, Base ASAG, Proposed ASAG) across
the Mohler ASAG dataset and exports machine-readable and human-readable results.

Usage:
    # Full benchmark evaluation across all 2,273 active records:
    PYTHONPATH=. .venv/bin/python3 evaluation/experiments/run_mohler_evaluation.py --subset active

    # Quick sample evaluation (e.g., 25 records):
    PYTHONPATH=. .venv/bin/python3 evaluation/experiments/run_mohler_evaluation.py --limit 25
"""

from __future__ import annotations

import argparse
from pathlib import Path
import time
from typing import Dict, Optional

from evaluation.dataset.mohler_loader import MohlerDataset, MohlerLoader
from evaluation.metrics.asag_metrics import EvaluationMetrics
from evaluation.runners.evaluation_runner import EvaluationRunner


def format_metric(val: Optional[float], decimals: int = 4) -> str:
    """Format an optional metric float for table display."""
    if val is None:
        return "  N/A  "
    return f"{val:7.{decimals}f}"


def print_comparison_table(title: str, metrics_dict: Dict[str, EvaluationMetrics]) -> None:
    """Print a clean Markdown-like table comparing the ASAG systems."""
    print(f"\n### {title}")
    print(
        f"{'System':<30} | {'MAE':^7} | {'RMSE':^7} | {'Pearson r':^9} | {'Spearman rho':^12} | {'QWK':^7} | {'N':^5}"
    )
    print("-" * 88)
    for key in ["baseline", "base_asag", "proposed_asag"]:
        if key not in metrics_dict:
            continue
        m = metrics_dict[key]
        print(
            f"{m.system_name:<30} | {m.mae:7.4f} | {m.rmse:7.4f} | {format_metric(m.pearson_r):^9} | "
            f"{format_metric(m.spearman_rho):^12} | {format_metric(m.qwk):^7} | {m.n_samples:^5}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate ASAG systems on Mohler dataset.")
    parser.add_argument(
        "--subset",
        choices=["active", "assignments_1_10", "exams", "all"],
        default="active",
        help="Dataset subset to evaluate: 'active' (default, 2,273 records), 'assignments_1_10' (1,721 records), 'exams' (552 records), 'all' (2,442 records).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional limit on the number of records to evaluate (for testing/diagnostics).",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="evaluation/results",
        help="Directory to save predictions CSV and summary JSON.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent.parent
    output_dir = repo_root / args.output_dir

    print("=" * 72)
    print("ASAG EVALUATION PIPELINE (STAGE 15.2)")
    print("=" * 72)
    print(f"Dataset subset requested: {args.subset}")
    if args.limit:
        print(f"Record limit applied: {args.limit}")

    # Load dataset
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
        dataset = MohlerDataset(dataset.records[: args.limit])

    print(f"Total records to evaluate: {len(dataset)}")
    print("Starting evaluation across System 1, System 2, and System 3...")

    runner = EvaluationRunner()

    def progress_callback(current: int, total: int) -> None:
        pct = (current / total) * 100
        print(f"Progress: [{current}/{total}] ({pct:.1f}%) evaluated...")

    t0 = time.time()
    run_result = runner.evaluate_dataset(
        dataset,
        progress_callback=progress_callback,
        progress_interval=max(50, len(dataset) // 10),
    )
    duration = time.time() - t0

    print(f"\nEvaluation completed in {duration:.2f} seconds ({duration/len(dataset):.3f}s/record).")
    print(f"Failures recorded: {len(run_result.failures)}")

    # Print tables
    if run_result.metrics_all:
        print_comparison_table(
            f"Overall Results (N = {run_result.summary['active_records_evaluated']})",
            run_result.metrics_all,
        )

    if run_result.metrics_assignments_1_10:
        print_comparison_table(
            f"Assignments 1-10 (Uniform 0-5 scale, N = {run_result.summary['assignments_1_10_records']})",
            run_result.metrics_assignments_1_10,
        )

    if run_result.metrics_exams:
        print_comparison_table(
            f"Exams 11-12 (Normalized scale, N = {run_result.summary['exams_records']})",
            run_result.metrics_exams,
        )

    # Export results
    exported = run_result.export_results(output_dir)
    print("\nResults exported successfully:")
    for k, p in exported.items():
        print(f"  - {k}: {p}")
    print("=" * 72)


if __name__ == "__main__":
    main()
