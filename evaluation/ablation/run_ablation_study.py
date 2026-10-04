"""
Controlled Ablation Study Runner (Phase 12).

Executes controlled empirical ablations across the 7 designated conditions:
A. Base ASAG (control)
B. Base + Hybrid Proposition Representation
C. Base + Improved Semantic Matching (SemanticMatcherV2)
D. Base + Global Proposition Matching (Hungarian bipartite)
E. Base + Question-Aware Relevance
F. Base + Property Contradiction
G. Full Proposed Overhaul System

Records:
- Dataset version and active record count
- Exact condition configuration
- Metrics: MAE, RMSE, Pearson r, Spearman rho, QWK
- Strict scientific honesty: never claims an improvement unless demonstrated by data.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import time
from typing import Any, Dict, List, Optional, Sequence

from evaluation.dataset.mohler_loader import MohlerDataset, MohlerLoader, MohlerRecord
from evaluation.metrics.asag_metrics import EvaluationMetrics, compute_all_metrics
from proposed_asag.overhauled_pipeline import OverhauledASAGPipeline
from proposed_asag.scoring.bounded_scorer import ScoringStrategy

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

ABLATION_CONDITIONS: Dict[str, Dict[str, Any]] = {
    "A_BASE_ASAG": {
        "name": "A_BASE_ASAG",
        "description": "Baseline: Simplified Base ASAG (clausal triples, V1 comparator, greedy matching)",
        "use_hybrid_representation": False,
        "semantic_matcher_version": "v1",
        "matching_strategy": "greedy",
        "use_question_relevance": False,
        "use_property_contradiction": False,
        "enable_proposed_scoring": False,
    },
    "B_BASE_PLUS_HYBRID": {
        "name": "B_BASE_PLUS_HYBRID",
        "description": "Base ASAG + Hybrid Proposition Representation (recovers nominal fragments & infinitives)",
        "use_hybrid_representation": True,
        "semantic_matcher_version": "v1",
        "matching_strategy": "greedy",
        "use_question_relevance": False,
        "use_property_contradiction": False,
        "enable_proposed_scoring": False,
    },
    "C_BASE_PLUS_SEMANTIC_V2": {
        "name": "C_BASE_PLUS_SEMANTIC_V2",
        "description": "Base ASAG + Semantic Matcher V2 (multi-tier derivation & domain equivalences)",
        "use_hybrid_representation": False,
        "semantic_matcher_version": "v2",
        "matching_strategy": "greedy",
        "use_question_relevance": False,
        "use_property_contradiction": False,
        "enable_proposed_scoring": False,
    },
    "D_BASE_PLUS_GLOBAL_MATCHING": {
        "name": "D_BASE_PLUS_GLOBAL_MATCHING",
        "description": "Base ASAG + Global Bipartite Matching (Hungarian algorithm)",
        "use_hybrid_representation": False,
        "semantic_matcher_version": "v1",
        "matching_strategy": "global",
        "use_question_relevance": False,
        "use_property_contradiction": False,
        "enable_proposed_scoring": False,
    },
    "E_BASE_PLUS_QUESTION_RELEVANCE": {
        "name": "E_BASE_PLUS_QUESTION_RELEVANCE",
        "description": "Base ASAG + Question-Aware Relevance Filtering",
        "use_hybrid_representation": False,
        "semantic_matcher_version": "v1",
        "matching_strategy": "greedy",
        "use_question_relevance": True,
        "use_property_contradiction": False,
        "enable_proposed_scoring": True,
        "scoring_strategy": ScoringStrategy.SATURATING,
    },
    "F_BASE_PLUS_PROPERTY_CONTRADICTION": {
        "name": "F_BASE_PLUS_PROPERTY_CONTRADICTION",
        "description": "Base ASAG + Property & Antonym Contradiction Detection",
        "use_hybrid_representation": False,
        "semantic_matcher_version": "v1",
        "matching_strategy": "greedy",
        "use_question_relevance": False,
        "use_property_contradiction": True,
        "enable_proposed_scoring": True,
        "scoring_strategy": ScoringStrategy.SATURATING,
    },
    "G_FULL_OVERHAULED_SYSTEM": {
        "name": "G_FULL_OVERHAULED_SYSTEM",
        "description": "Full Overhauled System: Hybrid Rep + Semantic V2 + Global Match + Relevance + Contradiction + Saturating Bounded Scoring",
        "use_hybrid_representation": True,
        "semantic_matcher_version": "v2",
        "matching_strategy": "global",
        "use_question_relevance": True,
        "use_property_contradiction": True,
        "enable_proposed_scoring": True,
        "scoring_strategy": ScoringStrategy.SATURATING,
    },
}


class AblationStudyRunner:
    """
    Executes and reports controlled ablation experiments.
    """

    def __init__(self, records: Sequence[MohlerRecord]) -> None:
        self.records = list(records)

    def run_condition(
        self,
        condition_key: str,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Run evaluation for a specific ablation condition."""
        if condition_key not in ABLATION_CONDITIONS:
            raise ValueError(f"Unknown condition: '{condition_key}'. Choices: {list(ABLATION_CONDITIONS.keys())}")

        cfg = ABLATION_CONDITIONS[condition_key]
        records_to_run = self.records[:limit] if limit is not None else self.records

        logger.info("Initializing pipeline for condition '%s' (%d records)...", condition_key, len(records_to_run))
        pipeline = OverhauledASAGPipeline(
            use_hybrid_representation=cfg.get("use_hybrid_representation", True),
            semantic_matcher_version=cfg.get("semantic_matcher_version", "v2"),
            matching_strategy=cfg.get("matching_strategy", "global"),
            use_question_relevance=cfg.get("use_question_relevance", True),
            use_property_contradiction=cfg.get("use_property_contradiction", True),
            scoring_strategy=cfg.get("scoring_strategy", ScoringStrategy.SATURATING),
            enable_proposed_scoring=cfg.get("enable_proposed_scoring", True),
        )

        y_true: List[float] = []
        y_pred: List[float] = []
        start_time = time.time()

        for idx, rec in enumerate(records_to_run):
            res = pipeline.evaluate(
                question=rec.question,
                reference_answer=rec.reference_answer,
                student_answer=rec.student_answer_cleaned,
            )
            y_true.append(rec.score_ave)
            y_pred.append(res.final_score_scaled)

        elapsed = time.time() - start_time
        metrics = compute_all_metrics(
            system_name=condition_key,
            y_true=y_true,
            y_pred=y_pred,
            min_rating=0,
            max_rating=5,
        )

        return {
            "condition_key": condition_key,
            "description": cfg["description"],
            "config": cfg,
            "sample_count": len(records_to_run),
            "elapsed_seconds": round(elapsed, 2),
            "metrics": metrics.to_dict(),
        }

    def run_all(
        self,
        limit: Optional[int] = None,
        conditions: Optional[Sequence[str]] = None,
    ) -> Dict[str, Any]:
        """Run all designated ablation conditions and compile comparative results."""
        target_keys = list(conditions) if conditions else list(ABLATION_CONDITIONS.keys())
        results: Dict[str, Any] = {}

        for key in target_keys:
            logger.info("=== Running Ablation: %s ===", key)
            res = self.run_condition(key, limit=limit)
            results[key] = res

        return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Run controlled ASAG ablation study.")
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional limit on records (e.g. 50 for quick test, omit for all).",
    )
    parser.add_argument(
        "--conditions",
        type=str,
        default="all",
        help="Comma-separated condition keys, or 'all'.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="evaluation/results/ablations",
        help="Directory to export ablation summary JSON.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent.parent
    out_dir = repo_root / args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    dataset = MohlerLoader.load_processed_csv().filter_active()
    logger.info("Loaded active Mohler dataset: %d records.", len(dataset))

    runner = AblationStudyRunner(dataset.records)
    target_conds = None if args.conditions == "all" else [c.strip() for c in args.conditions.split(",")]

    ablation_results = runner.run_all(limit=args.limit, conditions=target_conds)

    # Save summary JSON
    summary_path = out_dir / "ablation_study_summary.json"
    meta = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dataset_version": "UNT CS Short Answer Dataset v2.0 (Mohler et al., 2011)",
        "active_records_total": len(dataset),
        "evaluated_count": args.limit if args.limit else len(dataset),
        "results": ablation_results,
    }

    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    logger.info("Ablation study completed. Results saved to %s", summary_path)

    # Print table
    print("\n" + "=" * 90)
    print("ABLATION STUDY RESULTS SUMMARY")
    print("=" * 90)
    print(f"{'Condition':<32} | {'MAE':^7} | {'RMSE':^7} | {'Pearson r':^9} | {'Spearman rho':^12} | {'QWK':^7}")
    print("-" * 90)
    for k, v in ablation_results.items():
        m = v["metrics"]
        pr_str = f"{m['pearson_r']:7.4f}" if m.get("pearson_r") is not None else "  N/A  "
        sp_str = f"{m['spearman_rho']:7.4f}" if m.get("spearman_rho") is not None else "  N/A  "
        qwk_str = f"{m['qwk']:7.4f}" if m.get("qwk") is not None else "  N/A  "
        print(f"{k:<32} | {m['mae']:7.4f} | {m['rmse']:7.4f} | {pr_str:^9} | {sp_str:^12} | {qwk_str:^7}")
    print("=" * 90)


if __name__ == "__main__":
    main()
