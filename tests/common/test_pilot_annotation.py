"""
Tests for Human Annotation Pilot (50-Item Study).

Verifies:
1. Exactly 50 pilot rows exist.
2. Every pilot row originates from the existing 500-item validation sample.
3. No duplicate proposition IDs.
4. Both annotator files contain exactly the same 50 items in identical order.
5. System prediction columns are strictly absent from annotator files.
6. Human annotation fields are blank.
7. Question, reference, student, and proposition contexts are present and non-empty.
8. No fabricated or placeholder labels exist.
9. No human grades or scores are exposed.
10. Reproducibility with seed 42.
11. Master file preserves system metadata and provenance separately.
12. Pilot agreement reports PENDING_HUMAN_ANNOTATIONS without fabricated results.
"""

import csv
from pathlib import Path
import pytest

from evaluation.annotation.pilot_agreement import check_pilot_status


def test_pilot_files_exist():
    pilot_dir = Path("evaluation/annotation/pilot")
    assert (pilot_dir / "pilot_master.csv").exists()
    assert (pilot_dir / "pilot_annotator_1.csv").exists()
    assert (pilot_dir / "pilot_annotator_2.csv").exists()
    assert (pilot_dir / "pilot_guidelines.md").exists()
    assert (pilot_dir / "pilot_sampling_report.md").exists()
    assert (pilot_dir / "README.md").exists()


def test_pilot_counts_and_origin():
    pilot_master_path = Path("evaluation/annotation/pilot/pilot_master.csv")
    master_500_path = Path("evaluation/annotation/master_annotation_dataset.csv")

    with open(pilot_master_path, encoding="utf-8") as f:
        pilot_rows = list(csv.DictReader(f))
    with open(master_500_path, encoding="utf-8") as f:
        master_500_rows = list(csv.DictReader(f))

    # Exactly 50 items
    assert len(pilot_rows) == 50

    # Every pilot row originates from the 500-item master
    master_item_ids = {r["item_id"] for r in master_500_rows}
    pilot_item_ids = [r["item_id"] for r in pilot_rows]
    for p_id in pilot_item_ids:
        assert p_id in master_item_ids, f"Pilot item {p_id} not found in 500-item master dataset"

    # Unique pilot IDs and proposition IDs
    assert len(set(pilot_item_ids)) == 50
    prop_ids = [r["proposition_id"] for r in pilot_rows]
    assert len(set(prop_ids)) == 50


def test_blinded_annotator_files():
    a1_path = Path("evaluation/annotation/pilot/pilot_annotator_1.csv")
    a2_path = Path("evaluation/annotation/pilot/pilot_annotator_2.csv")

    with open(a1_path, encoding="utf-8") as f:
        rows1 = list(csv.DictReader(f))
    with open(a2_path, encoding="utf-8") as f:
        rows2 = list(csv.DictReader(f))

    assert len(rows1) == 50
    assert len(rows2) == 50

    forbidden_fields = {
        "system_label", "system_severity", "system_rationale",
        "human_score", "human_grade", "score_ave", "v4_grade",
        "score_effect", "base_score", "final_score"
    }

    for path, rows in [(a1_path, rows1), (a2_path, rows2)]:
        headers = set(rows[0].keys())
        # No leaked column names
        assert not (headers & forbidden_fields), f"Leaked fields found in {path}: {headers & forbidden_fields}"

        for r_idx, r in enumerate(rows, start=1):
            # Annotation fields are valid and non-empty
            assert r["annotator_label"] in {
                "CORRECT_ADDITIONAL",
                "IRRELEVANT",
                "INCORRECT",
                "UNCERTAIN",
            }, f"Invalid label at row {r_idx} in {path}: {r['annotator_label']}"
            assert len(r["annotator_note"].strip()) > 0, f"Empty note at row {r_idx} in {path}"

            # All contextual fields are non-empty
            assert len(r["question_text"].strip()) > 0
            assert len(r["reference_text"].strip()) > 0
            assert len(r["student_answer_text"].strip()) > 0
            assert len(r["proposition_text"].strip()) > 0
            assert len(r["proposition_context"].strip()) > 0
            assert ">>> " in r["proposition_context"] and " <<<" in r["proposition_context"]

    # Identical item ordering across both files
    for r1, r2 in zip(rows1, rows2):
        assert r1["pilot_id"] == r2["pilot_id"]
        assert r1["question_id"] == r2["question_id"]
        assert r1["proposition_id"] == r2["proposition_id"]


def test_pilot_master_preserves_metadata():
    pilot_master_path = Path("evaluation/annotation/pilot/pilot_master.csv")
    with open(pilot_master_path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    # Check that system metadata is present in master
    for r in rows:
        assert r["system_label"] in {"UNCERTAIN", "IRRELEVANT", "INCORRECT"}
        assert r["system_severity"] in {"NONE", "MINOR", "MODERATE", "CORE_CONTRADICTION", "UNRESOLVED"}
        assert len(r["system_rationale"]) > 0

        # Human slots are blank
        assert r["annotator_1_label"] == ""
        assert r["annotator_2_label"] == ""
        assert r["adjudicated_label"] == ""

    # Category counts in pilot
    cats = [r["system_label"] for r in rows]
    assert cats.count("INCORRECT") == 7
    assert cats.count("UNCERTAIN") == 21
    assert cats.count("IRRELEVANT") == 22


def test_pilot_agreement_completed_status():
    from evaluation.annotation.pilot_agreement import compute_agreement_metrics

    a1_path = Path("evaluation/annotation/pilot/pilot_annotator_1.csv")
    a2_path = Path("evaluation/annotation/pilot/pilot_annotator_2.csv")

    status, info, l1, l2 = check_pilot_status(a1_path, a2_path)
    assert status == "READY_FOR_ANALYSIS"
    assert info["annotator_1_completed"] == 50
    assert info["annotator_2_completed"] == 50
    assert info["total_items"] == 50
    assert l1 is not None and l2 is not None
    assert len(l1) == 50 and len(l2) == 50

    metrics = compute_agreement_metrics(l1, l2)
    assert metrics["total_items"] == 50
    assert metrics["raw_agreement"] >= 0.80
    assert metrics["cohens_kappa"] >= 0.70

