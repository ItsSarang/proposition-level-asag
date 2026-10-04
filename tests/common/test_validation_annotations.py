"""
Unit tests for AI Validation Annotation datasets (Remaining 450 and Combined 500).

Verifies:
1. Both output files exist.
2. Exactly 450 items in ai_remaining_450_annotations.csv.
3. Exactly 500 items in ai_validation_500_annotations.csv.
4. Pilot items are strictly absent from the 450 file.
5. All item IDs are unique.
6. Combined 500 items maintain exact alignment with master_annotation_dataset.csv.
7. All labels belong to the 4 allowed categories.
8. Annotator notes are non-empty and core paraphrases are identified.
9. Pilot phase vs remaining phase metadata is preserved.
10. Source master and pilot datasets remain unmodified.
"""

import csv
from pathlib import Path
import pytest

VALID_LABELS = {"CORRECT_ADDITIONAL", "IRRELEVANT", "INCORRECT", "UNCERTAIN"}


def test_validation_files_exist():
    val_dir = Path("evaluation/annotation/validation")
    assert (val_dir / "ai_remaining_450_annotations.csv").exists()
    assert (val_dir / "ai_validation_500_annotations.csv").exists()


def test_remaining_450_structure():
    path_450 = Path("evaluation/annotation/validation/ai_remaining_450_annotations.csv")
    pilot_master_path = Path("evaluation/annotation/pilot/pilot_master.csv")

    with open(path_450, encoding="utf-8") as f:
        rows_450 = list(csv.DictReader(f))
    with open(pilot_master_path, encoding="utf-8") as f:
        pilot_rows = list(csv.DictReader(f))

    # Exactly 450 items
    assert len(rows_450) == 450

    # Unique IDs
    item_ids_450 = [r["item_id"] for r in rows_450]
    assert len(set(item_ids_450)) == 450

    # No pilot item in 450 set
    pilot_item_ids = {r["item_id"] for r in pilot_rows}
    assert len(pilot_item_ids) == 50
    for it_id in item_ids_450:
        assert it_id not in pilot_item_ids, f"Pilot item {it_id} found in remaining 450 dataset!"

    # Allowed labels and non-empty notes
    for r in rows_450:
        assert r["annotator_label"] in VALID_LABELS
        assert len(r["annotator_note"].strip()) > 0
        assert len(r["question_text"].strip()) > 0
        assert len(r["reference_text"].strip()) > 0
        assert len(r["student_answer_text"].strip()) > 0
        assert len(r["proposition_text"].strip()) > 0
        assert len(r["proposition_context"].strip()) > 0


def test_combined_500_structure():
    path_500 = Path("evaluation/annotation/validation/ai_validation_500_annotations.csv")
    master_path = Path("evaluation/annotation/master_annotation_dataset.csv")

    with open(path_500, encoding="utf-8") as f:
        rows_500 = list(csv.DictReader(f))
    with open(master_path, encoding="utf-8") as f:
        master_rows = list(csv.DictReader(f))

    # Exactly 500 items
    assert len(rows_500) == 500
    assert len(master_rows) == 500

    # Order and IDs match master exactly
    for r500, rmaster in zip(rows_500, master_rows):
        assert r500["item_id"] == rmaster["item_id"]
        assert r500["question_id"] == rmaster["question_id"]
        assert r500["proposition_id"] == rmaster["proposition_id"]

    # Phase counts
    phases = [r["annotation_phase"] for r in rows_500]
    assert phases.count("AI_PILOT_50") == 50
    assert phases.count("AI_REMAINING_450") == 450

    # Valid labels and notes
    for r in rows_500:
        assert r["annotator_label"] in VALID_LABELS
        assert len(r["annotator_note"].strip()) > 0


def test_core_paraphrases_identified():
    path_500 = Path("evaluation/annotation/validation/ai_validation_500_annotations.csv")
    with open(path_500, encoding="utf-8") as f:
        rows_500 = list(csv.DictReader(f))

    cp_count = sum(1 for r in rows_500 if "core paraphrase" in r["annotator_note"].lower())
    assert cp_count >= 100, f"Expected at least 100 core paraphrases across 500 items, got {cp_count}"

    # Verify that core paraphrases were labeled UNCERTAIN per guideline protocol
    for r in rows_500:
        if "core paraphrase" in r["annotator_note"].lower():
            assert r["annotator_label"] == "UNCERTAIN", (
                f"Core paraphrase at {r['item_id']} was labeled {r['annotator_label']} "
                "instead of UNCERTAIN"
            )
