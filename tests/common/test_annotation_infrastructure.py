"""
Tests for Phase 10: Human Annotation Infrastructure and Agreement Metrics.
"""

import math
import pytest
from pathlib import Path

from evaluation.annotation.agreement_metrics import (
    VALID_LABELS,
    compute_inter_annotator_agreement,
    evaluate_classification_against_gold,
)
from evaluation.annotation.annotation_tool import AnnotationTool


def test_inter_annotator_agreement_perfect():
    # Both annotators agree on all 10 items
    a1 = ["CORRECT_ADDITIONAL", "IRRELEVANT", "INCORRECT", "CORRECT_ADDITIONAL"] * 2
    a2 = ["CORRECT_ADDITIONAL", "IRRELEVANT", "INCORRECT", "CORRECT_ADDITIONAL"] * 2

    res = compute_inter_annotator_agreement(a1, a2)
    assert res.total_items == 8
    assert res.agreed_items == 8
    assert res.raw_agreement == 1.0
    assert res.cohens_kappa == 1.0


def test_inter_annotator_agreement_partial():
    # 6 agree, 4 disagree
    a1 = ["CORRECT_ADDITIONAL", "CORRECT_ADDITIONAL", "IRRELEVANT", "INCORRECT", "UNCERTAIN"] * 2
    a2 = ["CORRECT_ADDITIONAL", "UNCERTAIN",          "IRRELEVANT", "INCORRECT", "INCORRECT"] * 2

    res = compute_inter_annotator_agreement(a1, a2)
    assert res.total_items == 10
    assert res.agreed_items == 6
    assert res.raw_agreement == 0.60
    assert 0.0 < res.cohens_kappa < 1.0


def test_classification_against_gold_metrics():
    gold = ["CORRECT_ADDITIONAL", "CORRECT_ADDITIONAL", "IRRELEVANT", "INCORRECT"]
    pred = ["CORRECT_ADDITIONAL", "IRRELEVANT",         "IRRELEVANT", "INCORRECT"]

    res = evaluate_classification_against_gold(
        gold_labels=gold,
        pred_labels=pred,
        target_classes=list(VALID_LABELS),
    )

    assert res.total_evaluated == 4
    assert res.accuracy == 0.75  # 3 of 4 correct
    # CORRECT_ADDITIONAL: TP=1, FP=0, FN=1 -> Prec=1.0, Rec=0.5, F1=0.6667
    assert res.per_class_metrics["CORRECT_ADDITIONAL"]["precision"] == 1.0
    assert res.per_class_metrics["CORRECT_ADDITIONAL"]["recall"] == 0.5
    # IRRELEVANT: TP=1, FP=1, FN=0 -> Prec=0.5, Rec=1.0
    assert res.per_class_metrics["IRRELEVANT"]["precision"] == 0.5
    assert res.per_class_metrics["IRRELEVANT"]["recall"] == 1.0
    # INCORRECT: TP=1, FP=0, FN=0 -> Prec=1.0, Rec=1.0
    assert res.per_class_metrics["INCORRECT"]["precision"] == 1.0
    assert res.per_class_metrics["INCORRECT"]["recall"] == 1.0
    # UNCERTAIN: support = 0
    assert res.per_class_metrics["UNCERTAIN"]["support"] == 0.0


def test_annotation_tool_pending_status():
    tool = AnnotationTool()
    sample_csv = "evaluation/annotation/mohler_unmatched_sample.csv"
    assert Path(sample_csv).exists()

    inspection = tool.load_and_inspect_annotations(sample_csv)
    assert inspection["status"] == "PENDING_HUMAN_ANNOTATIONS"
    assert inspection["total_rows"] == 50
    assert inspection["adjudicated_count"] == 0
    assert "Awaiting human annotations" in inspection["message"]

    eval_result = tool.evaluate_study_if_available(sample_csv)
    assert eval_result["status"] == "PENDING_HUMAN_ANNOTATIONS"


def test_historical_original_sample_preserved():
    orig_path = Path("evaluation/annotation/mohler_unmatched_sample_original.csv")
    assert orig_path.exists()
    assert orig_path.stat().st_size > 0


def test_master_and_blinded_annotation_files_integrity():
    master_path = Path("evaluation/annotation/mohler_unmatched_master.csv")
    a1_path = Path("evaluation/annotation/annotator_1.csv")
    a2_path = Path("evaluation/annotation/annotator_2.csv")
    manifest_path = Path("evaluation/annotation/annotation_manifest.json")

    assert master_path.exists()
    assert a1_path.exists()
    assert a2_path.exists()
    assert manifest_path.exists()

    import csv
    import json

    # Master inspection
    with open(master_path, mode="r", encoding="utf-8") as f:
        master_rows = list(csv.DictReader(f))
    assert len(master_rows) == 50

    # Ensure spans are valid and non-corrupt
    for r in master_rows:
        assert int(r["char_start"]) >= 0
        assert int(r["char_end"]) > int(r["char_start"])
        assert len(r["system_predicted_classification"]) > 0
        assert len(r["system_rationale"]) > 0
        # Human columns must be blank
        assert r["annotator_1"] == ""
        assert r["annotator_2"] == ""
        assert r["adjudicated_label"] == ""

    # Blinded inspection: NO system predictions or scores leaked
    for path in [a1_path, a2_path]:
        with open(path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fieldnames = set(reader.fieldnames or [])
            # Assert forbidden leaked columns do NOT exist
            assert "system_predicted_classification" not in fieldnames
            assert "system_rationale" not in fieldnames
            assert "score_effect" not in fieldnames
            assert "base_score" not in fieldnames
            assert "final_score" not in fieldnames
            rows = list(reader)
            assert len(rows) in (50, 500)
            for r in rows:
                assert r["annotator_label"] == ""
                if "annotator_rationale" in r:
                    assert r["annotator_rationale"] == ""
                if "annotator_notes" in r:
                    assert r["annotator_notes"] == ""

    # Manifest inspection
    with open(manifest_path, mode="r", encoding="utf-8") as f:
        manifest = json.load(f)
    assert manifest["metadata"]["status"] == "PENDING_HUMAN_ANNOTATIONS"
    assert manifest["metadata"]["total_propositions"] == 50
    assert manifest["metadata"]["questions_covered"] == 10
    assert len(manifest["items"]) == 50
