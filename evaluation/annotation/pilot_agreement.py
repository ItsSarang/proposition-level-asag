"""
Phase 6 Human Annotation Pilot: Agreement Analysis Script.

Computes inter-annotator agreement metrics (raw agreement, Cohen's Kappa,
per-class agreement, confusion matrix) once both annotator files are populated.

When annotation fields are blank, reports 'PENDING_HUMAN_ANNOTATIONS' without
fabricating results.
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sklearn.metrics import cohen_kappa_score

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

VALID_LABELS = ["CORRECT_ADDITIONAL", "IRRELEVANT", "INCORRECT", "UNCERTAIN"]


def check_pilot_status(
    a1_path: Path, a2_path: Path
) -> Tuple[str, Dict[str, Any], Optional[List[str]], Optional[List[str]]]:
    """Inspect annotator files and determine whether annotations are complete."""
    if not a1_path.exists() or not a2_path.exists():
        return (
            "FILES_NOT_FOUND",
            {"message": f"Annotator files not found: {a1_path}, {a2_path}"},
            None,
            None,
        )

    with open(a1_path, encoding="utf-8") as f:
        rows1 = list(csv.DictReader(f))
    with open(a2_path, encoding="utf-8") as f:
        rows2 = list(csv.DictReader(f))

    if len(rows1) != len(rows2):
        return (
            "ROW_COUNT_MISMATCH",
            {"message": f"Row count mismatch: {len(rows1)} vs {len(rows2)}"},
            None,
            None,
        )

    total_items = len(rows1)
    labels1 = [r.get("annotator_label", "").strip() for r in rows1]
    labels2 = [r.get("annotator_label", "").strip() for r in rows2]

    completed1 = sum(1 for l in labels1 if l in VALID_LABELS)
    completed2 = sum(1 for l in labels2 if l in VALID_LABELS)

    if completed1 < total_items or completed2 < total_items:
        return (
            "PENDING_HUMAN_ANNOTATIONS",
            {
                "status": "PENDING_HUMAN_ANNOTATIONS",
                "total_items": total_items,
                "annotator_1_completed": completed1,
                "annotator_2_completed": completed2,
                "message": (
                    f"Awaiting human annotations. Progress: Annotator 1 ({completed1}/{total_items}), "
                    f"Annotator 2 ({completed2}/{total_items}). Zero synthetic labels used."
                ),
            },
            None,
            None,
        )

    return (
        "READY_FOR_ANALYSIS",
        {
            "status": "READY_FOR_ANALYSIS",
            "total_items": total_items,
            "annotator_1_completed": completed1,
            "annotator_2_completed": completed2,
        },
        labels1,
        labels2,
    )


def compute_agreement_metrics(
    labels1: List[str], labels2: List[str]
) -> Dict[str, Any]:
    """Compute formal inter-annotator agreement statistics."""
    total = len(labels1)
    agreed = sum(1 for l1, l2 in zip(labels1, labels2) if l1 == l2)
    raw_agreement = agreed / total if total > 0 else 0.0

    kappa = float(cohen_kappa_score(labels1, labels2, labels=VALID_LABELS))

    # Per-class counts and agreement
    per_class: Dict[str, Dict[str, Any]] = {}
    for cat in VALID_LABELS:
        c1 = sum(1 for l in labels1 if l == cat)
        c2 = sum(1 for l in labels2 if l == cat)
        both = sum(1 for l1, l2 in zip(labels1, labels2) if l1 == cat and l2 == cat)
        per_class[cat] = {
            "annotator_1_count": c1,
            "annotator_2_count": c2,
            "joint_agreement_count": both,
            "concordance_rate": (2.0 * both / (c1 + c2)) if (c1 + c2) > 0 else 0.0,
        }

    return {
        "total_items": total,
        "agreed_items": agreed,
        "disagreed_items": total - agreed,
        "raw_agreement": round(raw_agreement, 4),
        "cohens_kappa": round(kappa, 4),
        "per_class_concordance": per_class,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Pilot Inter-Annotator Agreement Calculator.")
    parser.add_argument(
        "--a1",
        type=str,
        default="evaluation/annotation/pilot/pilot_annotator_1.csv",
        help="Path to Annotator 1 CSV file.",
    )
    parser.add_argument(
        "--a2",
        type=str,
        default="evaluation/annotation/pilot/pilot_annotator_2.csv",
        help="Path to Annotator 2 CSV file.",
    )
    parser.add_argument(
        "--output-json",
        type=str,
        default=None,
        help="Optional path to export agreement metrics JSON.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    a1_path = repo_root / args.a1
    a2_path = repo_root / args.a2

    status, info, l1, l2 = check_pilot_status(a1_path, a2_path)

    if status == "PENDING_HUMAN_ANNOTATIONS":
        print("\n" + "=" * 70)
        print("PILOT ANNOTATION STATUS: PENDING_HUMAN_ANNOTATIONS")
        print("=" * 70)
        print(info["message"])
        print("No synthetic or placeholder labels will be computed.")
        print("=" * 70 + "\n")
        return

    if status != "READY_FOR_ANALYSIS" or l1 is None or l2 is None:
        logger.error("Cannot compute agreement: %s", info.get("message", status))
        return

    logger.info("Computing agreement on %d fully annotated items...", len(l1))
    results = compute_agreement_metrics(l1, l2)

    print("\n" + "=" * 70)
    print("PILOT INTER-ANNOTATOR AGREEMENT RESULTS")
    print("=" * 70)
    print(f"Total Items:     {results['total_items']}")
    print(f"Agreed Items:    {results['agreed_items']} ({results['raw_agreement']*100:.1f}%)")
    print(f"Cohen's Kappa:   {results['cohens_kappa']:.4f}")
    print("\nPer-Class Breakdown:")
    for cat, stats in results["per_class_concordance"].items():
        print(
            f"  {cat:<18}: A1={stats['annotator_1_count']:2d}, A2={stats['annotator_2_count']:2d}, "
            f"Agreed={stats['joint_agreement_count']:2d} (Rate={stats['concordance_rate']:.2f})"
        )
    print("=" * 70 + "\n")

    if args.output_json:
        out_p = Path(args.output_json)
        with open(out_p, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        logger.info("Exported results to %s", out_p)


if __name__ == "__main__":
    main()
