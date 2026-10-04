"""Inspection and Diagnostic Summary for the Mohler ASAG Dataset.

This script performs comprehensive inspection and statistical analysis of the
University of North Texas Computer Science Short Answer Dataset Version 2.0
(Mohler, Bunescu & Mihalcea, 2011).

Usage:
    PYTHONPATH=. .venv/bin/python3 evaluation/dataset/inspect_mohler.py
"""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List
import numpy as np
from scipy.stats import spearmanr

from evaluation.dataset.mohler_loader import MohlerDataset, MohlerLoader


def compute_dataset_stats(dataset: MohlerDataset) -> Dict[str, Any]:
    """Compute detailed dataset statistics across active and all records."""
    total_records = len(dataset)
    active_dataset = dataset.filter_active()
    active_records = len(active_dataset)
    ignored_records = total_records - active_records

    # Questions summary
    q_summary = dataset.get_questions_summary()
    total_questions = len(q_summary)
    active_questions = sum(1 for q in q_summary if q["is_active"])
    ignored_questions = total_questions - active_questions

    # Assignments 1-10 (uniform 0-5 scale)
    assign_1_10_dataset = dataset.filter_assignments_1_10()
    n_assign_1_10 = len(assign_1_10_dataset)

    # Exams 11-12
    exam_dataset = dataset.filter_exams()
    n_exams = len(exam_dataset)

    # Grader scores for assignments 1-10
    me_1_10 = np.array([r.score_me for r in assign_1_10_dataset])
    other_1_10 = np.array([r.score_other for r in assign_1_10_dataset])
    ave_1_10 = np.array([r.score_ave for r in assign_1_10_dataset])

    # Inter-rater metrics (me vs other) on assignments 1-10
    pearson_r = float(np.corrcoef(me_1_10, other_1_10)[0, 1])
    spearman_rho, spearman_p = spearmanr(me_1_10, other_1_10)
    mae = float(np.mean(np.abs(me_1_10 - other_1_10)))
    rmse = float(np.sqrt(np.mean((me_1_10 - other_1_10) ** 2)))

    # Scores for all active questions
    ave_active = np.array([r.score_ave for r in active_dataset])

    # Score distribution for active records (rounded to 1 decimal place)
    score_dist = Counter(round(float(s), 1) for s in ave_active)

    # Text length statistics (word count)
    raw_lengths = [len(r.student_answer_raw.split()) for r in active_dataset]
    clean_lengths = [len(r.student_answer_cleaned.split()) for r in active_dataset]

    # HTML tags count
    html_count = sum(1 for r in dataset if "<br" in r.student_answer_raw.lower())

    # Ignored questions details
    ignored_q_details = [
        {
            "question_id": q["question_id"],
            "question_text": q["question_text"],
            "answers_count": q["total_student_answers"],
        }
        for q in q_summary
        if not q["is_active"]
    ]

    # Per-assignment breakdown
    assignment_breakdown: Dict[int, Dict[str, Any]] = {}
    for a in range(1, 13):
        subset = dataset.filter_by_assignment(a)
        sub_active = subset.filter_active()
        q_count = len({r.question_id for r in subset})
        active_q_count = len({r.question_id for r in sub_active})
        sub_ave = [r.score_ave for r in sub_active]
        assignment_breakdown[a] = {
            "total_questions": q_count,
            "active_questions": active_q_count,
            "total_answers": len(subset),
            "active_answers": len(sub_active),
            "mean_score_ave": float(np.mean(sub_ave)) if sub_ave else 0.0,
            "scale": "0-5" if a <= 10 else "0-10_normalized_to_0-5",
        }

    return {
        "total_records": total_records,
        "active_records": active_records,
        "ignored_records": ignored_records,
        "total_questions": total_questions,
        "active_questions": active_questions,
        "ignored_questions": ignored_questions,
        "ignored_q_details": ignored_q_details,
        "assignments_1_10_count": n_assign_1_10,
        "exams_count": n_exams,
        "inter_rater_assignments_1_10": {
            "pearson_r": pearson_r,
            "spearman_rho": float(spearman_rho),
            "spearman_p": float(spearman_p),
            "mae": mae,
            "rmse": rmse,
            "me_mean": float(np.mean(me_1_10)),
            "me_std": float(np.std(me_1_10)),
            "other_mean": float(np.mean(other_1_10)),
            "other_std": float(np.std(other_1_10)),
            "ave_mean": float(np.mean(ave_1_10)),
            "ave_std": float(np.std(ave_1_10)),
        },
        "active_scores_summary": {
            "mean": float(np.mean(ave_active)),
            "std": float(np.std(ave_active)),
            "median": float(np.median(ave_active)),
            "min": float(np.min(ave_active)),
            "max": float(np.max(ave_active)),
            "score_distribution": dict(sorted(score_dist.items())),
        },
        "length_stats": {
            "raw_word_mean": float(np.mean(raw_lengths)),
            "raw_word_std": float(np.std(raw_lengths)),
            "clean_word_mean": float(np.mean(clean_lengths)),
            "clean_word_std": float(np.std(clean_lengths)),
            "clean_word_min": int(np.min(clean_lengths)),
            "clean_word_max": int(np.max(clean_lengths)),
        },
        "html_artifact_count": html_count,
        "assignment_breakdown": assignment_breakdown,
    }


def print_inspection_report(stats: Dict[str, Any]) -> None:
    """Print formatted inspection report to stdout."""
    print("=" * 72)
    print("MOHLER ASAG DATASET INSPECTION REPORT (UNT CS Short Answer v2.0)")
    print("=" * 72)

    print("\n1. RECORD & QUESTION TOTALS")
    print(f"   Total student answers:    {stats['total_records']}")
    print(f"   Active student answers:   {stats['active_records']} (matches ACL 2011 exactly)")
    print(f"   Ignored student answers:  {stats['ignored_records']}")
    print(f"   Total questions:          {stats['total_questions']}")
    print(f"   Active questions:         {stats['active_questions']}")
    print(f"   Ignored questions:        {stats['ignored_questions']}")

    print("\n2. IGNORED QUESTIONS (Selection / Ordering Questions)")
    for q in stats["ignored_q_details"]:
        print(f"   - #{q['question_id']}: {q['question_text']} ({q['answers_count']} answers)")

    print("\n3. ASSIGNMENT BREAKDOWN")
    print("   Asgn | Questions (Act/Tot) | Answers (Act/Tot) | Mean Ave Score | Scale")
    print("   " + "-" * 66)
    for a, data in stats["assignment_breakdown"].items():
        kind = "Exam" if a > 10 else f"A{a:02d}"
        q_str = f"{data['active_questions']}/{data['total_questions']}"
        ans_str = f"{data['active_answers']}/{data['total_answers']}"
        print(
            f"   {kind:<4} | {q_str:^19} | {ans_str:^17} | {data['mean_score_ave']:^14.3f} | {data['scale']}"
        )

    print("\n4. HUMAN GRADER AGREEMENT (Assignments 1-10, N = 1,721, Scale 0-5)")
    ir = stats["inter_rater_assignments_1_10"]
    print(f"   Grader 2 ('me', Michael Mohler):  mean={ir['me_mean']:.3f}, std={ir['me_std']:.3f}")
    print(f"   Grader 1 ('other', Course TA):    mean={ir['other_mean']:.3f}, std={ir['other_std']:.3f}")
    print(f"   Average ('ave', official ground): mean={ir['ave_mean']:.3f}, std={ir['ave_std']:.3f}")
    print(f"   Pearson correlation (r):          {ir['pearson_r']:.4f}")
    print(f"   Spearman correlation (rho):       {ir['spearman_rho']:.4f}")
    print(f"   Mean Absolute Error (MAE):        {ir['mae']:.4f}")
    print(f"   Root Mean Squared Error (RMSE):   {ir['rmse']:.4f}")

    print("\n5. SCORE DISTRIBUTION (Active Records N = 2,273, Scale 0.0 - 5.0)")
    dist = stats["active_scores_summary"]["score_distribution"]
    for score, count in dist.items():
        pct = (count / stats["active_records"]) * 100
        bar = "#" * int(pct / 2)
        print(f"   {score:4.1f} | {count:4d} ({pct:5.1f}%) | {bar}")

    print("\n6. TEXT CHARACTERISTICS")
    lt = stats["length_stats"]
    print(f"   Cleaned answer length (words): mean={lt['clean_word_mean']:.1f}, "
          f"min={lt['clean_word_min']}, max={lt['clean_word_max']}")
    print(f"   Answers with HTML tags (<br>): {stats['html_artifact_count']}")
    print("=" * 72)


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect Mohler ASAG Dataset.")
    parser.add_argument(
        "--source",
        choices=["raw", "processed"],
        default="raw",
        help="Data source to inspect: 'raw' (default) or 'processed'.",
    )
    args = parser.parse_args()

    if args.source == "processed":
        dataset = MohlerLoader.load_processed_csv()
    else:
        dataset = MohlerLoader.load_raw()

    stats = compute_dataset_stats(dataset)
    print_inspection_report(stats)


if __name__ == "__main__":
    main()
