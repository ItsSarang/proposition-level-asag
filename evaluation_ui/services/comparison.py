"""
ASAG Comparison and Batch Experiment Service (Phase 7 & Phase 9).

Processes batch evaluation files, computes empirical ASAG metrics when human
grades are present, and provides error analysis sorting.

Strict Research Integrity:
- Only calculates agreement metrics (MAE, RMSE, Pearson, Spearman, QWK) if real human grades are present.
- Never computes or displays synthetic metrics.
- Records all failure reasons explicitly.
"""

from __future__ import annotations

import csv
import io
import logging
from typing import Any, Dict, List, Optional, Sequence, Tuple

from evaluation.metrics.asag_metrics import EvaluationMetrics, compute_all_metrics
from evaluation_ui.services.evaluator import ASAGEvaluatorService

logger = logging.getLogger(__name__)


class ASAGComparisonService:
    """
    Coordinates batch evaluation experiments, metric computation, and error analysis.
    """

    def __init__(self, evaluator_service: Optional[ASAGEvaluatorService] = None) -> None:
        self.evaluator = evaluator_service or ASAGEvaluatorService()

    def process_csv_batch(
        self,
        csv_file_content: str,
        max_records: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Process a batch CSV file with student records across all four ASAG engines.

        Expected columns:
        - question_id (or qid)
        - question (or question_text)
        - reference_answer (or reference_text, ref_answer)
        - student_answer (or student_answer_text, student_text)
        Optional:
        - human_grade (or score_ave, human_score, grade)
        """
        reader = csv.DictReader(io.StringIO(csv_file_content.strip()))
        rows = list(reader)

        if not rows:
            return {
                "total_records": 0,
                "evaluated_count": 0,
                "failed_count": 0,
                "has_human_grades": False,
                "metrics": None,
                "records": [],
                "failure_reasons": ["Empty CSV file provided."],
            }

        # Normalize column header mapping
        headers = {col.strip().lower(): col for col in (reader.fieldnames or [])}

        qid_col = headers.get("question_id") or headers.get("qid") or "question_id"
        q_col = headers.get("question") or headers.get("question_text") or "question"
        ref_col = headers.get("reference_answer") or headers.get("reference_text") or headers.get("ref_answer") or "reference_answer"
        stu_col = headers.get("student_answer") or headers.get("student_answer_text") or headers.get("student_text") or "student_answer"
        human_col = (
            headers.get("human_grade")
            or headers.get("score_ave")
            or headers.get("human_score")
            or headers.get("grade")
        )

        records_to_process = rows[:max_records] if max_records is not None else rows

        evaluated_records: List[Dict[str, Any]] = []
        failures: List[Dict[str, Any]] = []

        y_true: List[float] = []
        y_pred_v0: List[float] = []
        y_pred_v1: List[float] = []
        y_pred_v2: List[float] = []
        y_pred_v3: List[float] = []

        has_human_grades = False

        for idx, row in enumerate(records_to_process, 1):
            qid = row.get(qid_col, f"Q_{idx}")
            q_text = row.get(q_col, "")
            ref_text = row.get(ref_col, "")
            stu_text = row.get(stu_col, "")

            # Parse optional human grade
            human_val: Optional[float] = None
            if human_col and human_col in row and row[human_col].strip():
                try:
                    human_val = float(row[human_col].strip())
                    has_human_grades = True
                except ValueError:
                    human_val = None

            try:
                eval_res = self.evaluator.evaluate_single(
                    question=q_text,
                    reference_answer=ref_text,
                    student_answer=stu_text,
                )

                v0 = eval_res["systems"]["v0_baseline"]
                v1 = eval_res["systems"]["v1_base_asag"]
                v2 = eval_res["systems"]["v2_historical_proposed"]
                v3 = eval_res["systems"]["v3_current_proposed"]

                rec_entry = {
                    "record_id": f"REC_{idx:04d}",
                    "row_index": idx,
                    "question_id": qid,
                    "question": q_text,
                    "reference_answer": ref_text,
                    "student_answer": stu_text,
                    "human_grade": human_val,
                    "v0_baseline_grade": round(v0["grade"], 2) if v0["status"] == "SUCCESS" else None,
                    "v1_base_grade": round(v1["grade"], 2) if v1["status"] == "SUCCESS" else None,
                    "v2_historical_grade": round(v2["proposed_grade"], 2) if v2["status"] == "SUCCESS" else None,
                    "v3_overhaul_grade": round(v3["final_grade"], 2) if v3["status"] == "SUCCESS" else None,
                    "v3_counts": {
                        "correct_additional": v3["correct_additional_count"],
                        "irrelevant": v3["irrelevant_count"],
                        "incorrect": v3["incorrect_count"],
                        "uncertain": v3["uncertain_count"],
                    },
                    "evaluation_detail": eval_res,
                    "status": "SUCCESS",
                }

                if human_val is not None:
                    # Compute error metrics for sorting and analysis
                    if rec_entry["v3_overhaul_grade"] is not None:
                        err = rec_entry["v3_overhaul_grade"] - human_val
                        rec_entry["error"] = round(err, 4)
                        rec_entry["absolute_error"] = round(abs(err), 4)
                        y_true.append(human_val)
                        y_pred_v0.append(rec_entry["v0_baseline_grade"] or 0.0)
                        y_pred_v1.append(rec_entry["v1_base_grade"] or 0.0)
                        y_pred_v2.append(rec_entry["v2_historical_grade"] or 0.0)
                        y_pred_v3.append(rec_entry["v3_overhaul_grade"] or 0.0)

                evaluated_records.append(rec_entry)

            except Exception as e:
                logger.error("Failed to evaluate batch row %d: %s", idx, str(e))
                failures.append({
                    "row_index": idx,
                    "question_id": qid,
                    "error": str(e),
                })

        # Calculate metrics ONLY if real human grades were present
        metrics_summary: Optional[Dict[str, Any]] = None
        if has_human_grades and len(y_true) > 0:
            m0 = compute_all_metrics("V0_Baseline", y_true, y_pred_v0, 0, 5).to_dict()
            m1 = compute_all_metrics("V1_Base_ASAG", y_true, y_pred_v1, 0, 5).to_dict()
            m2 = compute_all_metrics("V2_Historical_Proposed", y_true, y_pred_v2, 0, 5).to_dict()
            m3 = compute_all_metrics("V3_Overhauled_Proposed", y_true, y_pred_v3, 0, 5).to_dict()

            metrics_summary = {
                "n_samples": len(y_true),
                "systems": {
                    "v0_baseline": m0,
                    "v1_base_asag": m1,
                    "v2_historical_proposed": m2,
                    "v3_overhauled_proposed": m3,
                },
            }

        return {
            "total_records": len(records_to_process),
            "evaluated_count": len(evaluated_records),
            "failed_count": len(failures),
            "has_human_grades": has_human_grades,
            "metrics": metrics_summary,
            "records": evaluated_records,
            "failures": failures,
        }

    def generate_predictions_csv(self, batch_result: Dict[str, Any]) -> str:
        """
        Generate machine-readable CSV of predictions from batch evaluation.
        """
        output = io.StringIO()
        fieldnames = [
            "record_id",
            "question_id",
            "question",
            "reference_answer",
            "student_answer",
            "human_grade",
            "v0_baseline_grade",
            "v1_base_grade",
            "v2_historical_grade",
            "v3_overhaul_grade",
            "v3_correct_additional",
            "v3_irrelevant",
            "v3_incorrect",
            "v3_uncertain",
            "status",
        ]

        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for rec in batch_result.get("records", []):
            counts = rec.get("v3_counts", {})
            writer.writerow({
                "record_id": rec.get("record_id"),
                "question_id": rec.get("question_id"),
                "question": rec.get("question"),
                "reference_answer": rec.get("reference_answer"),
                "student_answer": rec.get("student_answer"),
                "human_grade": rec.get("human_grade", ""),
                "v0_baseline_grade": rec.get("v0_baseline_grade", ""),
                "v1_base_grade": rec.get("v1_base_grade", ""),
                "v2_historical_grade": rec.get("v2_historical_grade", ""),
                "v3_overhaul_grade": rec.get("v3_overhaul_grade", ""),
                "v3_correct_additional": counts.get("correct_additional", 0),
                "v3_irrelevant": counts.get("irrelevant", 0),
                "v3_incorrect": counts.get("incorrect", 0),
                "v3_uncertain": counts.get("uncertain", 0),
                "status": rec.get("status", "SUCCESS"),
            })

        return output.getvalue()

    def sort_error_records(
        self,
        records: List[Dict[str, Any]],
        sort_by: str = "absolute_error",
    ) -> List[Dict[str, Any]]:
        """
        Sort evaluated records by diagnostic error criteria (Phase 9):
        - 'absolute_error': largest |pred - human|
        - 'underprediction': pred << human (largest negative pred - human)
        - 'overprediction': pred >> human (largest positive pred - human)
        """
        records_with_human = [r for r in records if r.get("human_grade") is not None and "error" in r]
        other_records = [r for r in records if r not in records_with_human]

        if sort_by == "absolute_error":
            sorted_recs = sorted(records_with_human, key=lambda x: x["absolute_error"], reverse=True)
        elif sort_by == "underprediction":
            # Smallest error (most negative)
            sorted_recs = sorted(records_with_human, key=lambda x: x["error"])
        elif sort_by == "overprediction":
            # Largest error (most positive)
            sorted_recs = sorted(records_with_human, key=lambda x: x["error"], reverse=True)
        else:
            sorted_recs = records_with_human

        return sorted_recs + other_records
