"""
Tests for Cross-Slot Matching Precision Improvement (Experiment 3 Development).

Validates the general precision gates designed to eliminate false-positive cross-slot
matches (e.g. over-crediting generic verbs, superficial noun overlap, peripheral polysemy)
while preserving genuine syntactic paraphrases and Experiment 2 regressions.

Controlled Metrics Target:
- TP = 5
- FP = 0
- FN = 0
- TN = 5
- Precision = 1.0000
- Recall = 1.0000
- F1 = 1.0000
"""

from typing import Any, Dict, List
import pytest

from base_asag.matching.triple_matcher import TripleMatcher
from evaluation.dataset.mohler_loader import MohlerLoader
from evaluation.runners.overhaul_runner import OverhaulASAGRunner
from proposed_asag.overhauled_pipeline import OverhauledASAGPipeline, robust_prop_to_relation


@pytest.fixture(scope="module")
def overhaul_runner() -> OverhaulASAGRunner:
    return OverhaulASAGRunner()


@pytest.fixture(scope="module")
def overhauled_pipeline() -> OverhauledASAGPipeline:
    return OverhauledASAGPipeline()


@pytest.fixture(scope="module")
def mohler_dataset():
    loader = MohlerLoader()
    return loader.load_raw()


# ============================================================================
# Section 5: 10 Controlled Precision Test Cases
# ============================================================================

CONTROLLED_CASES: List[Dict[str, Any]] = [
    # Genuine Matches (Expected: TP)
    {
        "id": "Case 1 (simulate portions)",
        "expected": "GENUINE",
        "q": "What is a prototype program?",
        "ref": "To simulate the behaviour of portions of the desired software product.",
        "stu": "A prototype program simulates portions of the desired final product.",
        "expected_grade_min": 4.0,
    },
    {
        "id": "Case 2 (active/passive)",
        "expected": "GENUINE",
        "q": "What does a compiler do?",
        "ref": "A compiler converts high-level source code into machine code.",
        "stu": "High-level source code is converted into machine code by a compiler.",
        "expected_grade_min": 4.5,
    },
    {
        "id": "Case 3 (implement algorithm / run algorithm)",
        "expected": "GENUINE",
        "q": "How to measure running time?",
        "ref": "Implement the algorithm and measure the physical running time.",
        "stu": "You create and run the algorithm multiple times, while measuring the amount of time it takes.",
        "expected_grade_min": 3.5,
    },
    {
        "id": "Case 4 (generic pronoun variation)",
        "expected": "GENUINE",
        "q": "What does the function do?",
        "ref": "It finds the maximum element.",
        "stu": "You find the maximum element.",
        "expected_grade_min": 4.5,
    },
    {
        "id": "Case 5 (modifier variation)",
        "expected": "GENUINE",
        "q": "What does the function return?",
        "ref": "The function returns an integer value.",
        "stu": "The function returns an integer.",
        "expected_grade_min": 4.5,
    },
    # False Matches (Expected: TN)
    {
        "id": "Case 6 (find node / see nodes)",
        "expected": "FALSE",
        "q": "How to delete a node from BST?",
        "ref": "Find the node, then replace it with the leftmost node from its right subtree.",
        "stu": "The way you delete a node from a binary search tree is first you have to see the nodes that are coming from the root. And delete the nodes and set the root to NULL.",
        "expected_grade_max": 1.0,
    },
    {
        "id": "Case 7 (use constructors / assign memory)",
        "expected": "FALSE",
        "q": "How are objects initialized?",
        "ref": "By using constructors.",
        "stu": "Objects are assigned a space in memory when they are created.",
        "expected_grade_max": 0.5,
    },
    {
        "id": "Case 8 (delete node / inspect node)",
        "expected": "FALSE",
        "q": "What is the deletion step?",
        "ref": "Delete the target node from the binary tree.",
        "stu": "The algorithm inspects the node in the binary tree.",
        "expected_grade_max": 0.5,
    },
    {
        "id": "Case 9 (unrelated generic verbs with shared noun)",
        "expected": "FALSE",
        "q": "What does the method do?",
        "ref": "The method updates the data structure.",
        "stu": "The algorithm visualizes the data structure.",
        "expected_grade_max": 0.5,
    },
    {
        "id": "Case 10 (unrelated prepositional arguments / opposite actions)",
        "expected": "FALSE",
        "q": "How are records handled?",
        "ref": "The system writes records to disk.",
        "stu": "The system reads records from disk.",
        "expected_grade_max": 0.5,
    },
]


def test_controlled_precision_suite(overhauled_pipeline: OverhauledASAGPipeline) -> None:
    """Verify precision, recall, and F1 on the 10 controlled development test cases."""
    tp, fp, fn, tn = 0, 0, 0, 0

    for c in CONTROLLED_CASES:
        ref_parsed = overhauled_pipeline.parser.parse_document(c["ref"])
        stu_parsed = overhauled_pipeline.parser.parse_document(c["stu"])
        ref_props = overhauled_pipeline.hybrid_extractor.extract_document(ref_parsed, c["ref"])
        stu_props = overhauled_pipeline.hybrid_extractor.extract_document(stu_parsed, c["stu"])
        ref_relations = [robust_prop_to_relation(p) for p in ref_props]
        stu_relations = [robust_prop_to_relation(p) for p in stu_props]

        matching_res = overhauled_pipeline.matcher.match(ref_relations, stu_relations)
        has_match = len(matching_res.matched_relations) > 0

        if c["expected"] == "GENUINE":
            if has_match:
                tp += 1
            else:
                fn += 1
        else:
            if has_match:
                fp += 1
            else:
                tn += 1

    assert tp == 5, f"Expected 5 TP, got {tp}"
    assert fp == 0, f"Expected 0 FP, got {fp}"
    assert fn == 0, f"Expected 0 FN, got {fn}"
    assert tn == 5, f"Expected 5 TN, got {tn}"

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    assert precision == 1.0, f"Expected Precision=1.0, got {precision}"
    assert recall == 1.0, f"Expected Recall=1.0, got {recall}"
    assert f1 == 1.0, f"Expected F1=1.0, got {f1}"


def test_genuine_case_1_simulate_portions(overhaul_runner: OverhaulASAGRunner) -> None:
    c = CONTROLLED_CASES[0]
    pred = overhaul_runner.evaluate_triplet(c["q"], c["ref"], c["stu"])
    assert pred.grade >= c["expected_grade_min"]
    assert pred.cross_slot_matches_count >= 1


def test_genuine_case_2_active_passive(overhaul_runner: OverhaulASAGRunner) -> None:
    c = CONTROLLED_CASES[1]
    pred = overhaul_runner.evaluate_triplet(c["q"], c["ref"], c["stu"])
    assert pred.grade >= c["expected_grade_min"]


def test_genuine_case_3_implement_run_algorithm(overhaul_runner: OverhaulASAGRunner) -> None:
    c = CONTROLLED_CASES[2]
    pred = overhaul_runner.evaluate_triplet(c["q"], c["ref"], c["stu"])
    assert pred.grade >= c["expected_grade_min"]
    assert pred.cross_slot_matches_count >= 1


def test_genuine_case_4_pronoun_variation(overhaul_runner: OverhaulASAGRunner) -> None:
    c = CONTROLLED_CASES[3]
    pred = overhaul_runner.evaluate_triplet(c["q"], c["ref"], c["stu"])
    assert pred.grade >= c["expected_grade_min"]


def test_genuine_case_5_modifier_variation(overhaul_runner: OverhaulASAGRunner) -> None:
    c = CONTROLLED_CASES[4]
    pred = overhaul_runner.evaluate_triplet(c["q"], c["ref"], c["stu"])
    assert pred.grade >= c["expected_grade_min"]
    assert pred.cross_slot_matches_count >= 1


def test_false_case_6_find_node_see_nodes(overhaul_runner: OverhaulASAGRunner) -> None:
    c = CONTROLLED_CASES[5]
    pred = overhaul_runner.evaluate_triplet(c["q"], c["ref"], c["stu"])
    assert pred.grade <= c["expected_grade_max"]
    assert pred.cross_slot_matches_count == 0


def test_false_case_7_use_constructors_assign_memory(overhaul_runner: OverhaulASAGRunner) -> None:
    c = CONTROLLED_CASES[6]
    pred = overhaul_runner.evaluate_triplet(c["q"], c["ref"], c["stu"])
    assert pred.grade <= c["expected_grade_max"]
    assert pred.cross_slot_matches_count == 0


def test_false_case_8_delete_node_inspect_node(overhaul_runner: OverhaulASAGRunner) -> None:
    c = CONTROLLED_CASES[7]
    pred = overhaul_runner.evaluate_triplet(c["q"], c["ref"], c["stu"])
    assert pred.grade <= c["expected_grade_max"]
    assert pred.cross_slot_matches_count == 0


def test_false_case_9_generic_verbs_shared_noun(overhaul_runner: OverhaulASAGRunner) -> None:
    c = CONTROLLED_CASES[8]
    pred = overhaul_runner.evaluate_triplet(c["q"], c["ref"], c["stu"])
    assert pred.grade <= c["expected_grade_max"]
    assert pred.cross_slot_matches_count == 0


def test_false_case_10_unrelated_prepositional_direction(overhaul_runner: OverhaulASAGRunner) -> None:
    c = CONTROLLED_CASES[9]
    pred = overhaul_runner.evaluate_triplet(c["q"], c["ref"], c["stu"])
    assert pred.grade <= c["expected_grade_max"]
    assert pred.cross_slot_matches_count == 0


# ============================================================================
# Section 6: Experiment 2 Regression Tests
# ============================================================================

def _find_mohler_record(dataset, q_id: str, s_idx: int):
    for rec in dataset.filter_active().records:
        if rec.question_id == q_id and rec.student_index == s_idx:
            return rec
    raise ValueError(f"Record {q_id}_{s_idx} not found in Mohler dataset")


def test_regression_q1_1_s1(overhaul_runner: OverhaulASAGRunner, mohler_dataset) -> None:
    rec = _find_mohler_record(mohler_dataset, "1.1", 1)
    pred = overhaul_runner.evaluate_triplet(rec.question, rec.reference_answer, rec.student_answer_cleaned)
    assert abs(pred.grade - 4.7583) < 1e-3, f"Expected 4.7583, got {pred.grade}"


def test_regression_q8_2_s14(overhaul_runner: OverhaulASAGRunner, mohler_dataset) -> None:
    rec = _find_mohler_record(mohler_dataset, "8.2", 14)
    pred = overhaul_runner.evaluate_triplet(rec.question, rec.reference_answer, rec.student_answer_cleaned)
    assert abs(pred.grade - 5.0000) < 1e-3, f"Expected 5.0000, got {pred.grade}"


def test_regression_q12_2_s9(overhaul_runner: OverhaulASAGRunner, mohler_dataset) -> None:
    rec = _find_mohler_record(mohler_dataset, "12.2", 9)
    pred = overhaul_runner.evaluate_triplet(rec.question, rec.reference_answer, rec.student_answer_cleaned)
    assert abs(pred.grade - 4.0000) < 1e-3, f"Expected 4.0000, got {pred.grade}"


def test_regression_q11_8_s19(overhaul_runner: OverhaulASAGRunner, mohler_dataset) -> None:
    rec = _find_mohler_record(mohler_dataset, "11.8", 19)
    pred = overhaul_runner.evaluate_triplet(rec.question, rec.reference_answer, rec.student_answer_cleaned)
    assert abs(pred.grade - 3.8333) < 1e-3, f"Expected 3.8333, got {pred.grade}"


def test_regression_q5_1_s26(overhaul_runner: OverhaulASAGRunner, mohler_dataset) -> None:
    rec = _find_mohler_record(mohler_dataset, "5.1", 26)
    pred = overhaul_runner.evaluate_triplet(rec.question, rec.reference_answer, rec.student_answer_cleaned)
    assert abs(pred.grade - 4.9167) < 1e-3, f"Expected 4.9167, got {pred.grade}"
