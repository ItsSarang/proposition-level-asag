"""
Human Annotation Sampling and Extraction Tool (Phase 10).

Extracts unmatched student propositions from real Mohler dataset records and
exports them to a standardized CSV format for double-blind human annotation.

Research Integrity Mandate:
- Does NOT fabricate human annotations.
- Annotator columns are left blank until real human annotators complete them.
- If annotations are not yet completed, reports status as PENDING_HUMAN_ANNOTATIONS.
"""

import csv
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from base_asag.dependency.parser import DependencyParser
from base_asag.representation.hybrid import RobustProposition, RobustPropositionExtractor
from evaluation.annotation.agreement_metrics import (
    VALID_LABELS,
    compute_inter_annotator_agreement,
    evaluate_classification_against_gold,
)
from evaluation.dataset.mohler_loader import MohlerLoader, MohlerRecord

logger = logging.getLogger(__name__)

CSV_HEADERS = [
    "question_id",
    "answer_id",
    "proposition_id",
    "question_text",
    "reference_text",
    "student_answer_text",
    "proposition_text",
    "annotator_1",
    "annotator_2",
    "adjudicated_label",
    "notes",
]


class AnnotationTool:
    """
    Tool for sampling and validating proposition-level human annotation data.
    """

    def __init__(
        self,
        parser: Optional[DependencyParser] = None,
        extractor: Optional[RobustPropositionExtractor] = None,
    ) -> None:
        self.parser = parser or DependencyParser()
        self.extractor = extractor or RobustPropositionExtractor()

    def export_unmatched_propositions_sample(
        self,
        output_csv_path: str,
        sample_size: int = 50,
        target_assignments: Optional[Sequence[int]] = (1, 2, 3),
    ) -> int:
        """
        Sample real Mohler answers, extract unmatched propositions, and export
        a clean template for human annotation.
        """
        try:
            dataset = MohlerLoader.load_processed_csv().filter_active()
        except Exception:
            dataset = MohlerLoader.load_raw().filter_active()

        records = [
            r for r in dataset.records
            if target_assignments is None or r.assignment in target_assignments
        ]

        extracted_rows: List[Dict[str, str]] = []
        prop_counter = 0

        for rec in records:
            if len(extracted_rows) >= sample_size:
                break

            student_parsed = self.parser.parse_document(rec.student_answer_cleaned)
            ref_parsed = self.parser.parse_document(rec.reference_answer)

            student_props = self.extractor.extract_document(student_parsed, rec.student_answer_cleaned)
            ref_props = self.extractor.extract_document(ref_parsed, rec.reference_answer)

            # Determine unmatched propositions: student propositions with no exact or close lemma match
            ref_lemma_tuples = {p.to_lemma_tuple() for p in ref_props}

            for sp in student_props:
                prop_text = sp.source_text.strip()
                if not prop_text:
                    continue
                if sp.to_lemma_tuple() not in ref_lemma_tuples:
                    prop_counter += 1
                    extracted_rows.append({
                        "question_id": rec.question_id,
                        "answer_id": f"{rec.question_id}_{rec.student_index}",
                        "proposition_id": f"prop_{prop_counter:04d}",
                        "question_text": rec.question,
                        "reference_text": rec.reference_answer,
                        "student_answer_text": rec.student_answer_cleaned,
                        "proposition_text": prop_text,
                        "annotator_1": "",
                        "annotator_2": "",
                        "adjudicated_label": "",
                        "notes": "",
                    })
                    if len(extracted_rows) >= sample_size:
                        break

        out_path = Path(output_csv_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        with open(out_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
            writer.writeheader()
            for row in extracted_rows:
                writer.writerow(row)

        logger.info("Exported %d unmatched propositions to %s", len(extracted_rows), output_csv_path)
        return len(extracted_rows)

    def load_and_inspect_annotations(self, csv_path: str) -> Dict[str, Any]:
        """
        Inspect an annotation CSV and report status and completion counts.
        """
        path = Path(csv_path)
        if not path.exists():
            return {
                "status": "FILE_NOT_FOUND",
                "file_path": str(path),
                "total_rows": 0,
                "message": f"Annotation file not found at {path}",
            }

        rows: List[Dict[str, str]] = []
        with open(path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)

        total = len(rows)
        annotated_1 = sum(1 for r in rows if r.get("annotator_1", "").strip())
        annotated_2 = sum(1 for r in rows if r.get("annotator_2", "").strip())
        adjudicated = sum(1 for r in rows if r.get("adjudicated_label", "").strip())

        if adjudicated == 0 and annotated_1 == 0 and annotated_2 == 0:
            return {
                "status": "PENDING_HUMAN_ANNOTATIONS",
                "file_path": str(path),
                "total_rows": total,
                "annotator_1_count": 0,
                "annotator_2_count": 0,
                "adjudicated_count": 0,
                "message": (
                    "Awaiting human annotations. All annotation fields are blank. "
                    "Zero synthetic ground truth fabricated."
                ),
            }

        return {
            "status": "ANNOTATIONS_AVAILABLE" if adjudicated == total else "PARTIALLY_ANNOTATED",
            "file_path": str(path),
            "total_rows": total,
            "annotator_1_count": annotated_1,
            "annotator_2_count": annotated_2,
            "adjudicated_count": adjudicated,
        }

    def evaluate_study_if_available(
        self,
        csv_path: str,
        system_predictions: Optional[Sequence[str]] = None,
    ) -> Dict[str, Any]:
        """
        Evaluate inter-annotator agreement and classifier performance if human labels are provided.
        Otherwise returns PENDING_HUMAN_ANNOTATIONS.
        """
        inspection = self.load_and_inspect_annotations(csv_path)
        if inspection.get("status") == "PENDING_HUMAN_ANNOTATIONS":
            return inspection

        rows: List[Dict[str, str]] = []
        with open(csv_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                rows.append(r)

        a1_labels = [r.get("annotator_1", "").strip().upper() for r in rows if r.get("annotator_1", "").strip()]
        a2_labels = [r.get("annotator_2", "").strip().upper() for r in rows if r.get("annotator_2", "").strip()]
        adj_labels = [r.get("adjudicated_label", "").strip().upper() for r in rows if r.get("adjudicated_label", "").strip()]

        result: Dict[str, Any] = {
            "status": "EVALUATED",
            "inspection": inspection,
        }

        if len(a1_labels) == len(a2_labels) and len(a1_labels) > 0:
            agreement = compute_inter_annotator_agreement(a1_labels, a2_labels)
            result["inter_annotator_agreement"] = agreement.to_dict()

        if system_predictions is not None and len(adj_labels) == len(system_predictions):
            eval_metrics = evaluate_classification_against_gold(
                gold_labels=adj_labels,
                pred_labels=system_predictions,
                target_classes=list(VALID_LABELS),
            )
            result["classification_performance"] = eval_metrics.to_dict()

        return result
