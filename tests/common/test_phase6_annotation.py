"""Tests for Phase 6: Human Proposition-Level Annotation Dataset Preparation."""

from pathlib import Path
import csv
import pytest


def test_phase6_files_exist():
    ann_dir = Path("evaluation/annotation")
    assert (ann_dir / "master_annotation_dataset.csv").exists()
    assert (ann_dir / "annotator_1.csv").exists()
    assert (ann_dir / "annotator_2.csv").exists()
    assert (ann_dir / "annotation_guidelines.md").exists()
    assert (ann_dir / "annotation_schema.md").exists()
    assert (ann_dir / "annotation_sampling_report.md").exists()
    assert (ann_dir / "README.md").exists()


def test_master_dataset_structure_and_counts():
    master_path = Path("evaluation/annotation/master_annotation_dataset.csv")
    with open(master_path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    assert len(rows) == 500

    # Verify required master headers
    expected_headers = {
        "item_id", "question_id", "answer_id", "proposition_id",
        "question_text", "reference_text", "student_answer_text",
        "proposition_text", "proposition_context", "system_label",
        "system_severity", "system_rationale", "annotator_1_label",
        "annotator_1_notes", "annotator_2_label", "annotator_2_notes",
        "adjudicated_label", "adjudication_notes"
    }
    assert expected_headers.issubset(set(rows[0].keys()))

    # Verify unique item_ids from ITEM_001 to ITEM_500
    item_ids = [r["item_id"] for r in rows]
    assert len(set(item_ids)) == 500
    assert item_ids[0] == "ITEM_001"
    assert item_ids[-1] == "ITEM_500"

    # Category counts
    cats = [r["system_label"] for r in rows]
    assert cats.count("INCORRECT") == 64
    assert cats.count("UNCERTAIN") == 218
    assert cats.count("IRRELEVANT") == 218
    assert cats.count("CORRECT_ADDITIONAL") == 0

    # Severity counts for INCORRECT
    incorrect_rows = [r for r in rows if r["system_label"] == "INCORRECT"]
    sevs = [r["system_severity"] for r in incorrect_rows]
    assert sevs.count("CORE_CONTRADICTION") == 15
    assert sevs.count("MODERATE") == 42
    assert sevs.count("MINOR") == 2
    assert sevs.count("UNRESOLVED") == 5

    # 100% question coverage
    qids = set(r["question_id"] for r in rows)
    assert len(qids) == 81


def test_blinded_annotator_files_integrity():
    a1_path = Path("evaluation/annotation/annotator_1.csv")
    a2_path = Path("evaluation/annotation/annotator_2.csv")

    with open(a1_path, encoding="utf-8") as f:
        a1_rows = list(csv.DictReader(f))
    with open(a2_path, encoding="utf-8") as f:
        a2_rows = list(csv.DictReader(f))

    assert len(a1_rows) == 500
    assert len(a2_rows) == 500

    forbidden_fields = {
        "system_label", "system_severity", "system_rationale",
        "human_score", "human_grade", "score_ave", "v4_grade"
    }

    for path, rows in [(a1_path, a1_rows), (a2_path, a2_rows)]:
        headers = set(rows[0].keys())
        assert not (headers & forbidden_fields)
        for r in rows:
            assert r["annotator_label"] == ""
            assert r["annotator_notes"] == ""
            assert len(r["question_text"]) > 0
            assert len(r["reference_text"]) > 0
            assert len(r["student_answer_text"]) > 0
            assert len(r["proposition_text"]) > 0
            assert len(r["proposition_context"]) > 0

    # Ensure exact 1-to-1 correspondence between annotator 1 and annotator 2
    for r1, r2 in zip(a1_rows, a2_rows):
        assert r1["item_id"] == r2["item_id"]
        assert r1["question_id"] == r2["question_id"]
        assert r1["proposition_id"] == r2["proposition_id"]
