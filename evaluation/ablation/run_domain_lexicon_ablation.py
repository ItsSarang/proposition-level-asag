"""
Domain Lexicon Ablation Study.

Compares ASAG evaluation metrics with and without the curated 13 Computer Science
domain lexical equivalences on the Mohler ASAG dataset.

Conditions evaluated:
1. Proposed_Overhaul_WITH_Domain_Lexicon (use_domain_equivalence=True)
2. Proposed_Overhaul_WITHOUT_Domain_Lexicon (use_domain_equivalence=False)
3. Base_ASAG_V2_WITH_Domain_Lexicon (use_domain_equivalence=True, scoring disabled)
4. Base_ASAG_V2_WITHOUT_Domain_Lexicon (use_domain_equivalence=False, scoring disabled)

Saves summary to: evaluation/results/ablations/domain_lexicon_ablation.json
"""

import argparse
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import time
from typing import Any, Dict, List, Optional

from base_asag.semantic.domain_lexicon import DOMAIN_LEXICAL_EQUIVALENCES
from evaluation.dataset.mohler_loader import MohlerLoader
from evaluation.metrics.asag_metrics import compute_all_metrics
from proposed_asag.overhauled_pipeline import OverhauledASAGPipeline
from proposed_asag.scoring.bounded_scorer import ScoringStrategy

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def run_domain_lexicon_ablation(
    limit: Optional[int] = None,
    output_path: str = "evaluation/results/ablations/domain_lexicon_ablation.json",
) -> Dict[str, Any]:
    dataset = MohlerLoader.load_processed_csv().filter_active()
    records = dataset.records[:limit] if limit is not None else dataset.records

    logger.info("Running Domain Lexicon Ablation across %d records...", len(records))

    conditions = [
        {
            "key": "Proposed_Overhaul_WITH_Domain_Lexicon",
            "description": "Full Proposed Overhaul (V2 matcher WITH 13 CS domain equivalences)",
            "use_hybrid_representation": True,
            "semantic_matcher_version": "v2",
            "matching_strategy": "global",
            "use_question_relevance": True,
            "use_property_contradiction": True,
            "scoring_strategy": ScoringStrategy.SATURATING,
            "enable_proposed_scoring": True,
            "use_domain_equivalence": True,
        },
        {
            "key": "Proposed_Overhaul_WITHOUT_Domain_Lexicon",
            "description": "Full Proposed Overhaul (V2 matcher WITHOUT CS domain equivalences)",
            "use_hybrid_representation": True,
            "semantic_matcher_version": "v2",
            "matching_strategy": "global",
            "use_question_relevance": True,
            "use_property_contradiction": True,
            "scoring_strategy": ScoringStrategy.SATURATING,
            "enable_proposed_scoring": True,
            "use_domain_equivalence": False,
        },
        {
            "key": "Base_ASAG_V2_WITH_Domain_Lexicon",
            "description": "Base ASAG with V2 matcher WITH CS domain equivalences",
            "use_hybrid_representation": False,
            "semantic_matcher_version": "v2",
            "matching_strategy": "greedy",
            "use_question_relevance": False,
            "use_property_contradiction": False,
            "scoring_strategy": ScoringStrategy.SATURATING,
            "enable_proposed_scoring": False,
            "use_domain_equivalence": True,
        },
        {
            "key": "Base_ASAG_V2_WITHOUT_Domain_Lexicon",
            "description": "Base ASAG with V2 matcher WITHOUT CS domain equivalences",
            "use_hybrid_representation": False,
            "semantic_matcher_version": "v2",
            "matching_strategy": "greedy",
            "use_question_relevance": False,
            "use_property_contradiction": False,
            "scoring_strategy": ScoringStrategy.SATURATING,
            "enable_proposed_scoring": False,
            "use_domain_equivalence": False,
        },
    ]

    results: Dict[str, Any] = {}

    for cond in conditions:
        key = cond["key"]
        logger.info("Evaluating condition: %s...", key)
        pipeline = OverhauledASAGPipeline(
            use_hybrid_representation=cond["use_hybrid_representation"],
            semantic_matcher_version=cond["semantic_matcher_version"],
            matching_strategy=cond["matching_strategy"],
            use_question_relevance=cond["use_question_relevance"],
            use_property_contradiction=cond["use_property_contradiction"],
            scoring_strategy=cond["scoring_strategy"],
            enable_proposed_scoring=cond["enable_proposed_scoring"],
            use_domain_equivalence=cond["use_domain_equivalence"],
        )

        y_true: List[float] = []
        y_pred: List[float] = []
        start_time = time.time()

        for rec in records:
            res = pipeline.evaluate(
                question=rec.question,
                reference_answer=rec.reference_answer,
                student_answer=rec.student_answer_cleaned,
            )
            y_true.append(rec.score_ave)
            y_pred.append(res.final_score_scaled)

        elapsed = time.time() - start_time
        metrics = compute_all_metrics(
            system_name=key,
            y_true=y_true,
            y_pred=y_pred,
            min_rating=0,
            max_rating=5,
        )

        results[key] = {
            "condition_key": key,
            "description": cond["description"],
            "use_domain_equivalence": cond["use_domain_equivalence"],
            "sample_count": len(records),
            "elapsed_seconds": round(elapsed, 2),
            "metrics": metrics.to_dict(),
        }

    # Compute delta for Proposed Overhaul
    with_metrics = results["Proposed_Overhaul_WITH_Domain_Lexicon"]["metrics"]
    without_metrics = results["Proposed_Overhaul_WITHOUT_Domain_Lexicon"]["metrics"]

    comparison_summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_records_evaluated": len(records),
        "domain_lexicon_terms_count": len(DOMAIN_LEXICAL_EQUIVALENCES),
        "results": results,
        "proposed_overhaul_deltas": {
            "mae_delta": round(with_metrics["mae"] - without_metrics["mae"], 4),
            "rmse_delta": round(with_metrics["rmse"] - without_metrics["rmse"], 4),
            "pearson_delta": round(with_metrics["pearson_r"] - without_metrics["pearson_r"], 4),
            "spearman_delta": round(with_metrics["spearman_rho"] - without_metrics["spearman_rho"], 4),
            "qwk_delta": round(with_metrics["qwk"] - without_metrics["qwk"], 4),
        },
    }

    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, mode="w", encoding="utf-8") as f:
        json.dump(comparison_summary, f, indent=2)

    logger.info("Domain lexicon ablation results saved to %s", output_path)
    return comparison_summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run domain lexicon ablation study.")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of records to evaluate.")
    parser.add_argument("--output", type=str, default="evaluation/results/ablations/domain_lexicon_ablation.json")
    args = parser.parse_args()

    run_domain_lexicon_ablation(limit=args.limit, output_path=args.output)
