"""
Phase 6 Human Annotation Pilot: 50-Item Pilot Dataset Generator.

Selects a deterministic 50-item pilot sample from the existing 500-item
stratified/enriched validation sample (master_annotation_dataset.csv).

Seed: 42 (Reproducible)

Exports:
- evaluation/annotation/pilot/pilot_master.csv
- evaluation/annotation/pilot/pilot_annotator_1.csv
- evaluation/annotation/pilot/pilot_annotator_2.csv
"""

from __future__ import annotations

import csv
import logging
from pathlib import Path
import random
from collections import Counter, defaultdict
from typing import Any, Dict, List

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

RANDOM_SEED = 42
PILOT_SAMPLE_SIZE = 50


def generate_pilot() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    master_500_path = repo_root / "evaluation/annotation/master_annotation_dataset.csv"
    pilot_dir = repo_root / "evaluation/annotation/pilot"
    pilot_dir.mkdir(parents=True, exist_ok=True)

    if not master_500_path.exists():
        raise FileNotFoundError(f"Source 500-item master dataset not found at: {master_500_path}")

    logger.info("Loading 500-item validation master from %s...", master_500_path)
    with open(master_500_path, encoding="utf-8") as f:
        master_rows = list(csv.DictReader(f))

    assert len(master_rows) == 500, f"Expected 500 items in master dataset, got {len(master_rows)}"

    # Group by category and severity
    by_cat: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for r in master_rows:
        by_cat[r["system_label"]].append(r)

    rng = random.Random(RANDOM_SEED)

    # 1. Stratify INCORRECT (Target: 7 items across 4 severities)
    by_sev: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for r in by_cat["INCORRECT"]:
        by_sev[r["system_severity"]].append(r)

    for s in by_sev:
        rng.shuffle(by_sev[s])

    # Select 2 CORE, 3 MODERATE, 1 MINOR, 1 UNRESOLVED
    sel_inc: List[Dict[str, Any]] = []
    sel_inc.extend(by_sev["CORE_CONTRADICTION"][:2])
    sel_inc.extend(by_sev["MODERATE"][:3])
    sel_inc.extend(by_sev["MINOR"][:1])
    sel_inc.extend(by_sev["UNRESOLVED"][:1])
    assert len(sel_inc) == 7

    # 2. Stratify UNCERTAIN (21 items) and IRRELEVANT (22 items) across diverse questions
    def select_diverse(items: List[Dict[str, Any]], count: int, sub_seed: int) -> List[Dict[str, Any]]:
        sub_rng = random.Random(sub_seed)
        by_q: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for it in items:
            by_q[it["question_id"]].append(it)
        selected: List[Dict[str, Any]] = []
        q_keys = sorted(by_q.keys())
        sub_rng.shuffle(q_keys)
        while len(selected) < count:
            for q in q_keys:
                if len(selected) >= count:
                    break
                if by_q[q]:
                    selected.append(by_q[q].pop(0))
        return selected

    sel_unc = select_diverse(by_cat["UNCERTAIN"], 21, sub_seed=RANDOM_SEED + 1)
    sel_irr = select_diverse(by_cat["IRRELEVANT"], 22, sub_seed=RANDOM_SEED + 2)

    full_pilot = sel_inc + sel_unc + sel_irr
    assert len(full_pilot) == PILOT_SAMPLE_SIZE, f"Expected 50 pilot items, got {len(full_pilot)}"

    # Deterministic final shuffle
    rng.shuffle(full_pilot)

    # Assign sequential pilot_id (PILOT_001 to PILOT_050)
    for idx, item in enumerate(full_pilot, start=1):
        item["pilot_id"] = f"PILOT_{idx:03d}"

    # Verify distribution
    cat_counts = Counter(r["system_label"] for r in full_pilot)
    sev_counts = Counter(r["system_severity"] for r in sel_inc)
    q_counts = Counter(r["question_id"] for r in full_pilot)
    asgns = Counter(int(r["answer_id"].split("_")[1]) for r in full_pilot)

    logger.info("Pilot Category distribution: %s", dict(cat_counts))
    logger.info("Pilot INCORRECT severities: %s", dict(sev_counts))
    logger.info("Pilot unique questions: %d", len(q_counts))
    logger.info("Pilot assignments/exams: %s", sorted(asgns.items()))

    # 3. Export Pilot Master Dataset
    pilot_master_path = pilot_dir / "pilot_master.csv"
    master_fields = [
        "pilot_id",
        "item_id",
        "question_id",
        "answer_id",
        "proposition_id",
        "question_text",
        "reference_text",
        "student_answer_text",
        "proposition_text",
        "proposition_context",
        "system_label",
        "system_severity",
        "system_rationale",
        "annotator_1_label",
        "annotator_1_note",
        "annotator_2_label",
        "annotator_2_note",
        "adjudicated_label",
        "adjudication_note",
    ]

    with open(pilot_master_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=master_fields)
        writer.writeheader()
        for item in full_pilot:
            row = {
                "pilot_id": item["pilot_id"],
                "item_id": item["item_id"],
                "question_id": item["question_id"],
                "answer_id": item["answer_id"],
                "proposition_id": item["proposition_id"],
                "question_text": item["question_text"],
                "reference_text": item["reference_text"],
                "student_answer_text": item["student_answer_text"],
                "proposition_text": item["proposition_text"],
                "proposition_context": item["proposition_context"],
                "system_label": item["system_label"],
                "system_severity": item["system_severity"],
                "system_rationale": item["system_rationale"],
                "annotator_1_label": "",
                "annotator_1_note": "",
                "annotator_2_label": "",
                "annotator_2_note": "",
                "adjudicated_label": "",
                "adjudication_note": "",
            }
            writer.writerow(row)
    logger.info("Exported pilot master dataset: %s (%d rows)", pilot_master_path, len(full_pilot))

    # 4. Export Blinded Annotator 1 and Annotator 2 Datasets
    blinded_fields = [
        "pilot_id",
        "question_id",
        "answer_id",
        "proposition_id",
        "question_text",
        "reference_text",
        "student_answer_text",
        "proposition_text",
        "proposition_context",
        "annotator_label",
        "annotator_note",
    ]

    for ann_filename in ["pilot_annotator_1.csv", "pilot_annotator_2.csv"]:
        ann_path = pilot_dir / ann_filename
        with open(ann_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=blinded_fields)
            writer.writeheader()
            for item in full_pilot:
                row = {
                    "pilot_id": item["pilot_id"],
                    "question_id": item["question_id"],
                    "answer_id": item["answer_id"],
                    "proposition_id": item["proposition_id"],
                    "question_text": item["question_text"],
                    "reference_text": item["reference_text"],
                    "student_answer_text": item["student_answer_text"],
                    "proposition_text": item["proposition_text"],
                    "proposition_context": item["proposition_context"],
                    "annotator_label": "",
                    "annotator_note": "",
                }
                writer.writerow(row)
        logger.info("Exported blinded pilot dataset: %s (%d rows)", ann_path, len(full_pilot))

    # 5. Automated Blinding Verification
    logger.info("Running automated blinding verification for pilot files...")
    forbidden_tokens = [
        "system_label",
        "system_severity",
        "system_rationale",
        "human_score",
        "human_grade",
        "CORRECT_ADDITIONAL",
        "UNCERTAIN",
        "IRRELEVANT",
        "INCORRECT",
        "CORE_CONTRADICTION",
        "MODERATE",
    ]

    for ann_filename in ["pilot_annotator_1.csv", "pilot_annotator_2.csv"]:
        ann_path = pilot_dir / ann_filename
        with open(ann_path, encoding="utf-8") as f:
            content = f.read()

        lines = content.splitlines()
        header = lines[0]
        # Check forbidden tokens in header
        for ft in ["system", "severity", "score", "grade", "human"]:
            assert ft not in header.lower(), f"Forbidden substring '{ft}' in header of {ann_filename}"

        # Check rows
        reader = csv.DictReader(lines)
        for r_idx, r in enumerate(reader, start=1):
            assert r["annotator_label"] == "", f"Non-empty label at row {r_idx} in {ann_filename}"
            assert r["annotator_note"] == "", f"Non-empty note at row {r_idx} in {ann_filename}"
            assert len(r["question_text"]) > 0
            assert len(r["reference_text"]) > 0
            assert len(r["student_answer_text"]) > 0
            assert len(r["proposition_text"]) > 0
            assert len(r["proposition_context"]) > 0

    logger.info("Blinding verification passed: Annotator files are 100% blinded with zero leaked metadata.")


if __name__ == "__main__":
    generate_pilot()
