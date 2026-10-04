"""
Clean Stratified Sampling Script for Proposition-Level Human Annotation.

Generates:
1. evaluation/annotation/mohler_unmatched_master.csv (with system predictions and rationales)
2. evaluation/annotation/annotator_1.csv (strictly blinded: NO system labels, NO rationales)
3. evaluation/annotation/annotator_2.csv (strictly blinded: NO system labels, NO rationales)
4. evaluation/annotation/annotation_manifest.json (researcher metadata for record linkage)

Preserves:
- evaluation/annotation/mohler_unmatched_sample_original.csv (historical inspection artifact)
"""

import csv
import json
import logging
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Set

from evaluation.dataset.mohler_loader import MohlerLoader
from proposed_asag.classification.robust_classifier import AdditionalInfoClass
from proposed_asag.overhauled_pipeline import OverhauledASAGPipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TARGET_QUESTIONS = [
    "1.1",  # C++ prototyping
    "1.3",  # Prototype vs definition
    "1.4",  # Similarities prototype / definition
    "1.7",  # Advantages of prototypes
    "2.2",  # Array vs pointer
    "2.3",  # When to use pointer vs array
    "3.1",  # Algorithms
    "5.1",  # Recursion
    "8.1",  # Binary Search Trees
    "9.1",  # Queue data structure
]

QUESTION_TARGETS = {
    "1.1": 5,
    "1.3": 6,
    "1.4": 4,
    "1.7": 6,
    "2.2": 5,
    "2.3": 6,
    "3.1": 4,
    "5.1": 5,
    "8.1": 5,
    "9.1": 4,
}


def is_clean_candidate(prop, student_text: str) -> bool:
    text = prop.source_text.strip()
    if len(text) < 3:
        return False
    if not re.search(r"[a-zA-Z]{2,}", text):
        return False
    # Validate character spans
    if prop.char_start < 0 or prop.char_end <= prop.char_start or prop.char_end > len(student_text):
        return False
    slice_text = student_text[prop.char_start:prop.char_end].strip()
    if not slice_text:
        return False
    # Exclude isolated punctuation or markdown
    if text in [".", ",", ";", ":", "-", "(", ")", '"', '""', "'"]:
        return False
    # Exclude obvious mid-word or truncation artifacts
    first_word = text.split()[0]
    common_short_words = {
        "a", "an", "the", "to", "in", "on", "at", "for", "with", "by", "of", "and", "or",
        "but", "is", "are", "can", "may", "will", "it", "they", "that", "this", "which",
        "when", "if", "not", "so", "as"
    }
    if first_word.islower() and first_word not in common_short_words:
        if prop.char_start > 0 and student_text[prop.char_start - 1].isalnum():
            return False
    # Check end of slice: should not end mid-word if slice is followed immediately by alphanumerics
    if prop.char_end < len(student_text) and student_text[prop.char_end - 1].isalnum() and student_text[prop.char_end].isalnum():
        return False
    return True


def generate_clean_sample() -> None:
    dataset = MohlerLoader.load_processed_csv().filter_active()
    pipeline = OverhauledASAGPipeline()

    logger.info("Loaded %d active Mohler records.", len(dataset.records))

    candidates_by_qid = defaultdict(list)
    seen_combinations: Set[str] = set()

    for qid in TARGET_QUESTIONS:
        recs = [r for r in dataset.records if r.question_id == qid]
        for r in recs:
            res = pipeline.evaluate(r.question, r.reference_answer, r.student_answer_cleaned)
            if not res.classification_result or not res.classification_result.classified_propositions:
                continue
            for cp in res.classification_result.classified_propositions:
                if cp.classification == AdditionalInfoClass.MATCHED_BY_BASE_ASAG:
                    continue
                prop = cp.proposition
                if not is_clean_candidate(prop, r.student_answer_cleaned):
                    continue
                combo_key = f"{qid}::{prop.source_text.strip().lower()}"
                if combo_key in seen_combinations:
                    continue
                seen_combinations.add(combo_key)
                candidates_by_qid[qid].append({
                    "record": r,
                    "classified_prop": cp,
                })

    selected_items: List[Dict[str, Any]] = []

    for qid, target_count in QUESTION_TARGETS.items():
        cands = candidates_by_qid[qid]
        by_class = defaultdict(list)
        for c in cands:
            by_class[c["classified_prop"].classification.value].append(c)

        q_selected = []
        # Prioritize rare classes: INCORRECT, UNCERTAIN
        for rare_cls in ["INCORRECT", "UNCERTAIN"]:
            if rare_cls in by_class:
                for item in by_class[rare_cls][:2]:
                    if len(q_selected) < target_count:
                        q_selected.append(item)

        # Balance CORRECT_ADDITIONAL and IRRELEVANT
        corrects = by_class.get("CORRECT_ADDITIONAL", [])
        irrelevants = by_class.get("IRRELEVANT", [])
        idx_c, idx_irr = 0, 0
        while len(q_selected) < target_count and (idx_c < len(corrects) or idx_irr < len(irrelevants)):
            if idx_c < len(corrects) and len(q_selected) < target_count:
                if corrects[idx_c] not in q_selected:
                    q_selected.append(corrects[idx_c])
                idx_c += 1
            if idx_irr < len(irrelevants) and len(q_selected) < target_count:
                if irrelevants[idx_irr] not in q_selected:
                    q_selected.append(irrelevants[idx_irr])
                idx_irr += 1

        selected_items.extend(q_selected)
        logger.info(
            "Selected %d items for Question %s: %s",
            len(q_selected),
            qid,
            dict(Counter([x["classified_prop"].classification.value for x in q_selected])),
        )

    logger.info("Total propositions selected: %d", len(selected_items))

    # Output paths
    base_dir = Path("evaluation/annotation")
    base_dir.mkdir(parents=True, exist_ok=True)

    master_csv_path = base_dir / "mohler_unmatched_master.csv"
    annotator_1_csv_path = base_dir / "annotator_1.csv"
    annotator_2_csv_path = base_dir / "annotator_2.csv"
    manifest_json_path = base_dir / "annotation_manifest.json"

    # Define headers
    master_headers = [
        "proposition_id",
        "question_id",
        "answer_id",
        "question_text",
        "reference_text",
        "student_answer_text",
        "proposition_text",
        "proposition_type",
        "char_start",
        "char_end",
        "system_predicted_classification",
        "system_rationale",
        "score_effect",
        "annotator_1",
        "annotator_2",
        "adjudicated_label",
        "adjudicated_rationale",
    ]

    annotator_headers = [
        "proposition_id",
        "question_id",
        "question_text",
        "reference_text",
        "student_answer_text",
        "proposition_text",
        "annotator_label",
        "annotator_rationale",
        "confidence",
    ]

    master_rows = []
    annotator_rows = []
    manifest_entries = []

    for idx, item in enumerate(selected_items, 1):
        rec = item["record"]
        cp = item["classified_prop"]
        prop = cp.proposition

        prop_id = f"PROP_{idx:03d}"
        ans_id = f"{rec.question_id}_{rec.student_index}"

        master_row = {
            "proposition_id": prop_id,
            "question_id": rec.question_id,
            "answer_id": ans_id,
            "question_text": rec.question,
            "reference_text": rec.reference_answer,
            "student_answer_text": rec.student_answer_cleaned,
            "proposition_text": prop.source_text.strip(),
            "proposition_type": prop.representation_type.value,
            "char_start": prop.char_start,
            "char_end": prop.char_end,
            "system_predicted_classification": cp.classification.value,
            "system_rationale": cp.rationale,
            "score_effect": cp.score_effect,
            "annotator_1": "",
            "annotator_2": "",
            "adjudicated_label": "",
            "adjudicated_rationale": "",
        }
        master_rows.append(master_row)

        # Blinded annotator row: NO system predictions, NO system rationales, NO scores
        annotator_row = {
            "proposition_id": prop_id,
            "question_id": rec.question_id,
            "question_text": rec.question,
            "reference_text": rec.reference_answer,
            "student_answer_text": rec.student_answer_cleaned,
            "proposition_text": prop.source_text.strip(),
            "annotator_label": "",
            "annotator_rationale": "",
            "confidence": "",
        }
        annotator_rows.append(annotator_row)

        manifest_entries.append({
            "proposition_id": prop_id,
            "question_id": rec.question_id,
            "answer_id": ans_id,
            "assignment": rec.assignment,
            "student_index": rec.student_index,
            "proposition_type": prop.representation_type.value,
            "proposition_text": prop.source_text.strip(),
            "char_span": [prop.char_start, prop.char_end],
            "system_prediction": {
                "classification": cp.classification.value,
                "rationale": cp.rationale,
                "score_effect": cp.score_effect,
            },
        })

    # Write master CSV
    with open(master_csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=master_headers)
        writer.writeheader()
        for r in master_rows:
            writer.writerow(r)
    logger.info("Saved master CSV to %s (%d rows)", master_csv_path, len(master_rows))

    # Write annotator 1 CSV (blinded)
    with open(annotator_1_csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=annotator_headers)
        writer.writeheader()
        for r in annotator_rows:
            writer.writerow(r)
    logger.info("Saved blinded Annotator 1 CSV to %s", annotator_1_csv_path)

    # Write annotator 2 CSV (blinded)
    with open(annotator_2_csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=annotator_headers)
        writer.writeheader()
        for r in annotator_rows:
            writer.writerow(r)
    logger.info("Saved blinded Annotator 2 CSV to %s", annotator_2_csv_path)

    # Write annotation manifest JSON
    manifest_data = {
        "metadata": {
            "dataset": "Mohler CS Short Answer Dataset v2.0",
            "study_type": "Double-Blind Proposition-Level Human Annotation Study",
            "date_generated": datetime.now().isoformat(),
            "total_propositions": len(selected_items),
            "questions_covered": len(QUESTION_TARGETS),
            "stratification": {
                "question_distribution": {qid: len([x for x in selected_items if x["record"].question_id == qid]) for qid in QUESTION_TARGETS},
                "system_classification_distribution": dict(Counter([x["classified_prop"].classification.value for x in selected_items])),
                "proposition_type_distribution": dict(Counter([x["classified_prop"].proposition.representation_type.value for x in selected_items])),
            },
            "status": "PENDING_HUMAN_ANNOTATIONS",
            "blinded_files": [
                str(annotator_1_csv_path),
                str(annotator_2_csv_path),
            ],
            "master_file": str(master_csv_path),
        },
        "items": manifest_entries,
    }

    with open(manifest_json_path, mode="w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)
    logger.info("Saved annotation manifest to %s", manifest_json_path)


if __name__ == "__main__":
    generate_clean_sample()
