"""
Comprehensive tests for the ASAG Evaluation Lab UI and Services.

Covers the 10 required testing points:
1. Flask app starts and routes respond.
2. Evaluation request reaches evaluator service.
3. Multiple student answers are evaluated independently.
4. Model outputs are correctly normalized into UI result objects.
5. Missing human grades do not trigger evaluation metrics.
6. Existing engine scores are not modified.
7. Errors from one model do not prevent other models from being displayed.
8. Proposition classifications are preserved exactly.
9. No system predictions appear in future annotator views (protocol integrity).
10. CSV export contains actual model outputs.
"""

import csv
import io
from pathlib import Path
import pytest

from evaluation.runners.baseline_runner import BaselinePrediction
from evaluation_ui.app import EVALUATION_CACHE, EXPERIMENT_CACHE, create_app
from evaluation_ui.services.comparison import ASAGComparisonService
from evaluation_ui.services.evaluator import ASAGEvaluatorService
from proposed_asag.overhauled_pipeline import OverhauledASAGPipeline


@pytest.fixture
def app():
    test_app = create_app({"TESTING": True, "SECRET_KEY": "test-secret"})
    return test_app


@pytest.fixture
def client(app):
    return app.test_client()


# 1. Flask app starts
def test_flask_app_starts(client):
    res = client.get("/")
    assert res.status_code == 200
    assert b"ASAG Evaluation Lab" in res.data
    assert b"Multi-Answer Comparative Evaluation" in res.data

    res_doc = client.get("/documentation")
    assert res_doc.status_code == 200
    assert b"Research Architecture" in res_doc.data

    res_val = client.get("/validation")
    assert res_val.status_code == 200
    assert b"PENDING REAL HUMAN ANNOTATIONS" in res_val.data


# 2. Evaluation request reaches evaluator service
def test_evaluation_request_reaches_evaluator_service(client):
    post_data = {
        "question": "What is the purpose of a primary key?",
        "reference_answer": "A primary key uniquely identifies each record in a table.",
        "student_answers": ["A primary key uniquely identifies every row in a table."],
    }
    res = client.post("/evaluate", data=post_data)
    assert res.status_code == 200
    assert b"Multi-Model Evaluation Overview" in res.data
    assert b"V0: TF-IDF" in res.data
    assert b"V1: Base ASAG" in res.data
    assert b"V3: Current Proposed" in res.data


# 3. Multiple student answers are evaluated independently
def test_multiple_student_answers_evaluated_independently():
    service = ASAGEvaluatorService()
    q = "What is the purpose of a primary key?"
    r = "A primary key uniquely identifies each record in a table."
    answers = [
        "A primary key uniquely identifies every row in a table.",
        "A primary key uniquely identifies each record in a table and cannot contain NULL values.",
        "SQL was developed in the 1970s.",
    ]
    results = service.evaluate_batch(q, r, answers)
    assert len(results) == 3

    # Answer 0 is paraphrase (high base coverage)
    # Answer 1 has correct additional info
    # Answer 2 is purely off-topic
    assert results[0]["answer_index"] == 0
    assert results[1]["answer_index"] == 1
    assert results[2]["answer_index"] == 2

    # Verify scores are independent
    g0 = results[0]["systems"]["v3_current_proposed"]["final_grade"]
    g2 = results[2]["systems"]["v3_current_proposed"]["final_grade"]
    assert g0 > g2  # Answer 0 score must be substantially higher than off-topic answer 2


# 4. Model outputs are correctly normalized into UI result objects
def test_model_outputs_correctly_normalized_into_ui_objects():
    service = ASAGEvaluatorService()
    q = "What is an algorithm?"
    r = "A step-by-step procedure for solving a problem."
    s = "A finite sequence of steps to solve a specific problem."

    res = service.evaluate_single(q, r, s)
    systems = res["systems"]

    for sys_key in ["v0_baseline", "v1_base_asag", "v2_historical_proposed", "v3_current_proposed"]:
        sys_data = systems[sys_key]
        assert sys_data["status"] == "SUCCESS"
        # Check normalized score in [0.0, 1.0]
        norm = None
        for k in ["normalized_score", "final_normalized", "proposed_normalized"]:
            if k in sys_data and sys_data[k] is not None:
                norm = sys_data[k]
                break
        assert norm is not None
        assert 0.0 <= norm <= 1.0

        # Check grade in [0.0, 5.0]
        grade = None
        for k in ["grade", "final_grade", "proposed_grade"]:
            if k in sys_data and sys_data[k] is not None:
                grade = sys_data[k]
                break
        assert grade is not None
        assert 0.0 <= grade <= 5.0


# 5. Missing human grades do not trigger evaluation metrics
def test_missing_human_grades_do_not_trigger_evaluation_metrics():
    comp_service = ASAGComparisonService()
    csv_content = """question_id,question,reference_answer,student_answer
1.1,What is a primary key?,A unique record identifier.,A unique row identifier.
1.1,What is a primary key?,A unique record identifier.,It identifies records uniquely.
"""
    batch_res = comp_service.process_csv_batch(csv_content)
    assert batch_res["total_records"] == 2
    assert batch_res["evaluated_count"] == 2
    assert batch_res["has_human_grades"] is False
    assert batch_res["metrics"] is None


# 6. Existing engine scores are not modified
def test_existing_engine_scores_are_not_modified():
    q = "What is a binary search tree?"
    r = "A binary tree where left child is less than root and right child is greater."
    s = "A binary tree where left nodes are smaller and right nodes are larger."

    # Direct engine run
    direct_pipeline = OverhauledASAGPipeline()
    direct_res = direct_pipeline.evaluate(q, r, s)

    # Service run
    service = ASAGEvaluatorService()
    service_res = service.evaluate_single(q, r, s)
    v3_service = service_res["systems"]["v3_current_proposed"]

    assert v3_service["final_normalized"] == pytest.approx(direct_res.final_score_normalized, abs=1e-4)
    assert v3_service["final_grade"] == pytest.approx(direct_res.final_score_scaled, abs=1e-4)
    assert v3_service["base_normalized"] == pytest.approx(direct_res.base_score_normalized, abs=1e-4)


# 7. Errors from one model do not prevent other models from being displayed
def test_errors_from_one_model_do_not_prevent_other_models():
    service = ASAGEvaluatorService()

    # Create a faulty baseline runner that raises an exception
    class FaultyBaselineRunner:
        def evaluate_pair(self, *args, **kwargs):
            raise RuntimeError("Simulated baseline engine failure")

    service.baseline_runner = FaultyBaselineRunner()

    res = service.evaluate_single(
        question="What is the purpose of a primary key?",
        reference_answer="A primary key uniquely identifies each record in a table.",
        student_answer="A primary key uniquely identifies each record in a table.",
    )

    # Baseline has error status
    assert res["systems"]["v0_baseline"]["status"] == "ERROR"
    assert "Simulated baseline engine failure" in res["systems"]["v0_baseline"]["error_message"]

    # Other systems evaluated successfully
    assert res["systems"]["v1_base_asag"]["status"] == "SUCCESS"
    assert res["systems"]["v3_current_proposed"]["status"] == "SUCCESS"
    assert res["systems"]["v3_current_proposed"]["final_grade"] > 0.0


# 8. Proposition classifications are preserved exactly
def test_proposition_classifications_are_preserved_exactly():
    service = ASAGEvaluatorService()
    q = "What is the purpose of a primary key?"
    r = "A primary key uniquely identifies each record in a table."
    s = "A primary key uniquely identifies each record in a table and cannot contain NULL values."

    res = service.evaluate_single(q, r, s)
    trace = res["proposition_trace"]

    # Verify proposition classifications exist in trace
    classifications = [p["classification"] for p in trace]
    assert "MATCHED_BY_BASE_ASAG" in classifications
    assert "CORRECT_ADDITIONAL" in classifications

    # Check the correct additional statement
    add_prop = next(p for p in trace if p["classification"] == "CORRECT_ADDITIONAL")
    assert "null" in add_prop["student_statement"].lower()
    assert add_prop["status"] == "UNMATCHED"


# 9. No system predictions appear in future annotator views
def test_no_system_predictions_appear_in_future_annotator_views(client):
    res = client.get("/validation")
    assert res.status_code == 200
    # Must explicitly state PENDING REAL HUMAN ANNOTATIONS
    assert b"PENDING REAL HUMAN ANNOTATIONS" in res.data
    assert b"Human validation will be enabled after independent annotation is completed" in res.data

    # Check blinded annotator files directly
    for path in ["evaluation/annotation/annotator_1.csv", "evaluation/annotation/annotator_2.csv"]:
        with open(path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fieldnames = set(reader.fieldnames or [])
            assert "system_predicted_classification" not in fieldnames
            assert "system_rationale" not in fieldnames
            assert "score_effect" not in fieldnames


# 10. CSV export contains actual model outputs
def test_csv_export_contains_actual_model_outputs(client):
    csv_content = """question_id,question,reference_answer,student_answer,human_grade
1.1,What is a primary key?,A unique identifier.,A unique record key.,4.5
"""
    data = {
        "csv_file": (io.BytesIO(csv_content.encode("utf-8")), "test.csv"),
    }
    post_res = client.post("/experiment/upload", data=data, follow_redirects=True)
    assert post_res.status_code == 200

    # Get the experiment ID from the cache
    assert len(EXPERIMENT_CACHE) > 0
    exp_id = list(EXPERIMENT_CACHE.keys())[-1]

    # Download CSV
    dl_res = client.get(f"/experiment/download/{exp_id}")
    assert dl_res.status_code == 200
    assert dl_res.mimetype == "text/csv"

    exported_text = dl_res.data.decode("utf-8")
    reader = csv.DictReader(io.StringIO(exported_text))
    rows = list(reader)
    assert len(rows) == 1
    r = rows[0]
    assert r["question_id"] == "1.1"
    assert float(r["human_grade"]) == 4.5
    assert float(r["v3_overhaul_grade"]) > 0.0
    assert r["status"] == "SUCCESS"


# 11. Regression Test: No duplicate matched proposition rendered in unmatched section
def test_proposition_trace_no_duplicate_matched_in_unmatched():
    """
    Regression test for Issue 1:
    Ensure MATCHED_BY_BASE_ASAG propositions appear only once (under the matched section)
    and are never rendered with status='UNMATCHED'.
    """
    service = ASAGEvaluatorService()
    q = "What is the purpose of a primary key?"
    r = "A primary key uniquely identifies each record in a table."
    s = "A primary key uniquely identifies each record in a table and can contain duplicate values."

    res = service.evaluate_single(q, r, s)
    trace = res["proposition_trace"]

    # 1. Matched section check
    matched_items = [p for p in trace if p["status"] == "MATCHED"]
    assert len(matched_items) == 1
    assert matched_items[0]["classification"] == "MATCHED_BY_BASE_ASAG"

    # 2. Unmatched section check - MUST NOT contain MATCHED_BY_BASE_ASAG
    unmatched_items = [p for p in trace if p["status"] == "UNMATCHED"]
    for item in unmatched_items:
        assert item["classification"] != "MATCHED_BY_BASE_ASAG", (
            f"Found matched proposition duplicated in unmatched trace: {item}"
        )

    # 3. Exactly one unmatched proposition classified as INCORRECT
    assert len(unmatched_items) == 1
    assert unmatched_items[0]["classification"] == "INCORRECT"
    assert unmatched_items[0]["student_statement"] == "can contain duplicate values"

