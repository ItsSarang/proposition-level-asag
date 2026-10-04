"""
Phase 4D End-to-End Severity-Aware Evaluation Runner.

Executes controlled development cases (including the 33 Phase 4B cases plus targeted
moderate, multi-core, and entity-confusion cases) through the complete end-to-end
pipeline:
Student Answer -> Base ASAG -> Proposition Extraction ->
Additional Info Classification -> Contradiction Detection ->
Automatic Severity Estimation -> Model D Scoring -> Final Grade.

Outputs:
- evaluation/scoring_development/phase4d_controlled_cases.csv
- evaluation/scoring_development/phase4d_end_to_end_results.csv
- evaluation/scoring_development/phase4d_score_traces.json
- evaluation/scoring_development/phase4d_comparison.csv
"""

from __future__ import annotations

import csv
import json
import os
from typing import Any, Dict, List, Optional, Tuple

from evaluation.scoring_development.run_phase4b_cases import get_phase4b_case_definitions
from proposed_asag.scoring.severity_aware_scorer import SeverityAwarePipeline


def get_phase4d_extended_cases() -> List[Dict[str, Any]]:
    """
    Returns the full suite of Phase 4D controlled cases:
    - 33 Phase 4B cases (for 1-to-1 comparison)
    - 7 Phase 4D targeted extension cases for Categories E, F, K, L
    """
    base_cases = get_phase4b_case_definitions()

    # Tag base cases with category_type
    case_type_map = {
        "PK-01": "A_CORRECT_CORE",
        "PK-02": "B_CORRECT_ADDITIONAL",
        "PK-03": "C_IRRELEVANT",
        "PK-04": "D_UNCERTAIN",
        "PK-05": "E_MINOR_INCORRECT",
        "PK-06": "G_CORE_CONTRADICTION",
        "PK-07": "J_MULTIPLE_MINOR",
        "PK-08": "G_CORE_CONTRADICTION",
        "PK-09": "H_PARTIAL_CORE_CONTRADICTION",
        "PK-10": "E_MINOR_INCORRECT",
        "BST-01": "A_CORRECT_CORE",
        "BST-02": "B_CORRECT_ADDITIONAL",
        "BST-03": "C_IRRELEVANT",
        "BST-04": "D_UNCERTAIN",
        "BST-05": "E_MINOR_INCORRECT",
        "BST-06": "G_CORE_CONTRADICTION",
        "BST-07": "K_MULTIPLE_CONTRADICTIONS",
        "BST-08": "H_PARTIAL_CORE_CONTRADICTION",
        "CMP-01": "A_CORRECT_CORE",
        "CMP-02": "B_CORRECT_ADDITIONAL",
        "CMP-03": "C_IRRELEVANT",
        "CMP-04": "D_UNCERTAIN",
        "CMP-05": "E_MINOR_INCORRECT",
        "CMP-06": "G_CORE_CONTRADICTION",
        "CMP-07": "K_MULTIPLE_CONTRADICTIONS",
        "CMP-08": "H_PARTIAL_CORE_CONTRADICTION",
        "MIX-01": "B_CORRECT_ADDITIONAL",
        "MIX-02": "I_CORRECT_ADD_CORE_CONTRADICTION",
        "MIX-03": "B_CORRECT_ADDITIONAL",
        "MIX-04": "G_CORE_CONTRADICTION",
        "MIX-05": "G_CORE_CONTRADICTION",
        "MIX-06": "B_CORRECT_ADDITIONAL",
        "MIX-07": "I_CORRECT_ADD_CORE_CONTRADICTION",
    }

    all_cases: List[Dict[str, Any]] = []
    for c in base_cases:
        c_copy = dict(c)
        c_copy["category_type"] = case_type_map.get(c["case_id"], "CONTROL")
        all_cases.append(c_copy)

    # Add targeted extensions for F (MODERATE), K (DUAL CORE), L (ENTITY CONFUSION)
    all_cases.extend([
        {
            "case_id": "PK-MOD",
            "domain": "PRIMARY_KEY",
            "category_type": "F_MODERATE_INCORRECT",
            "case_name": "PK-MOD (Correct core + moderate error: integer type)",
            "question": "What is the purpose of a primary key?",
            "reference_answer": "A primary key uniquely identifies each record in a table.",
            "student_answer": "A primary key uniquely identifies each record in a table. A primary key must always be an integer data type.",
            "case_description": "Data type restriction misconception; does not negate record uniqueness.",
            "expected_qualitative_relation": "Score < PK-01, > PK-06 (moderate deduction)",
            "severities": {"primary key must always be an integer": "MODERATE"},
            "target_classifications": {},
        },
        {
            "case_id": "BST-MOD",
            "domain": "BST",
            "category_type": "F_MODERATE_INCORRECT",
            "case_name": "BST-MOD (Correct core + moderate error: random traversal)",
            "question": "What is a binary search tree?",
            "reference_answer": "A binary search tree stores smaller values in the left subtree.",
            "student_answer": "A binary search tree stores smaller values in the left subtree. A binary search tree inorder traversal yields random order.",
            "case_description": "Traversal ordering confusion; secondary behavioral misconception.",
            "expected_qualitative_relation": "Score < BST-01, > BST-06 (moderate deduction)",
            "severities": {"inorder traversal yields random order": "MODERATE"},
            "target_classifications": {},
        },
        {
            "case_id": "CMP-MOD",
            "domain": "COMPILER",
            "category_type": "F_MODERATE_INCORRECT",
            "case_name": "CMP-MOD (Correct core + moderate error: line-by-line interpretation)",
            "question": "What is a compiler?",
            "reference_answer": "A compiler translates source code into machine code.",
            "student_answer": "A compiler translates source code into machine code. A compiler interprets code line by line at runtime.",
            "case_description": "Runtime execution timing confusion without denying translation function.",
            "expected_qualitative_relation": "Score < CMP-01, > CMP-06 (moderate deduction)",
            "severities": {"interprets code line by line": "MODERATE"},
            "target_classifications": {},
        },
        {
            "case_id": "PK-ADV-01",
            "domain": "PRIMARY_KEY",
            "category_type": "L_ENTITY_CONFUSION",
            "case_name": "PK-ADV-01 (Entity confusion: foreign key duplicates)",
            "question": "What is the purpose of a primary key?",
            "reference_answer": "A primary key uniquely identifies each record in a table.",
            "student_answer": "A primary key uniquely identifies each record in a table. A foreign key can contain duplicate values.",
            "case_description": "Adjacent entity discussed; does not contradict primary key properties.",
            "expected_qualitative_relation": "Score == PK-01 (neutral unresolved entity)",
            "severities": {"foreign key can contain duplicate values": "UNRESOLVED"},
            "target_classifications": {},
        },
        {
            "case_id": "BST-ADV-01",
            "domain": "BST",
            "category_type": "L_ENTITY_CONFUSION",
            "case_name": "BST-ADV-01 (Entity confusion: general binary tree)",
            "question": "What is a binary search tree?",
            "reference_answer": "A binary search tree stores smaller values in the left subtree.",
            "student_answer": "A binary search tree stores smaller values in the left subtree. A general binary tree must store smaller values in the left subtree.",
            "case_description": "Adjacent entity discussed; general binary tree does not enforce BST ordering.",
            "expected_qualitative_relation": "Score == BST-01 (neutral unresolved entity)",
            "severities": {"general binary tree must store": "UNRESOLVED"},
            "target_classifications": {},
        },
        {
            "case_id": "CMP-ADV-01",
            "domain": "COMPILER",
            "category_type": "L_ENTITY_CONFUSION",
            "case_name": "CMP-ADV-01 (Entity confusion: interpreter)",
            "question": "What is a compiler?",
            "reference_answer": "A compiler translates source code into machine code.",
            "student_answer": "A compiler translates source code into machine code. An interpreter compiles source code into machine files.",
            "case_description": "Adjacent entity discussed; predicated of interpreter, not compiler.",
            "expected_qualitative_relation": "Score == CMP-01 (neutral unresolved entity)",
            "severities": {"interpreter compiles source code": "UNRESOLVED"},
            "target_classifications": {},
        },
        {
            "case_id": "BST-CORE-MULTI",
            "domain": "BST",
            "category_type": "K_MULTIPLE_CONTRADICTIONS",
            "case_name": "BST-CORE-MULTI (Two direct core contradictions)",
            "question": "What is a binary search tree?",
            "reference_answer": "A binary search tree stores smaller values in the left subtree.",
            "student_answer": "A binary search tree stores smaller values in the left subtree. A binary search tree places larger values in the left subtree. A binary search tree stores smaller values in the right subtree.",
            "case_description": "Dual core contradictions of BST ordering invariants.",
            "expected_qualitative_relation": "Score <= BST-06 (multiple core invalidation)",
            "severities": {
                "places larger values": "CORE_CONTRADICTION",
                "stores smaller values in the right subtree": "CORE_CONTRADICTION",
            },
            "target_classifications": {},
        },
    ])

    return all_cases


def run_phase4d_evaluation() -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any], List[Dict[str, Any]]]:
    """
    Execute full Phase 4D evaluation across all controlled cases.
    """
    # Load Phase 4B score traces for baseline comparison
    phase4b_path = "evaluation/scoring_development/phase4b_score_traces.json"
    phase4b_traces: Dict[str, Any] = {}
    if os.path.exists(phase4b_path):
        with open(phase4b_path, "r", encoding="utf-8") as f:
            phase4b_traces = json.load(f)

    pipeline = SeverityAwarePipeline()
    cases = get_phase4d_extended_cases()

    controlled_cases_rows: List[Dict[str, Any]] = []
    end_to_end_rows: List[Dict[str, Any]] = []
    comparison_rows: List[Dict[str, Any]] = []
    score_traces: Dict[str, Any] = {}

    for c in cases:
        cid = c["case_id"]
        domain = c["domain"]
        cat_type = c["category_type"]
        cname = c["case_name"]
        q = c["question"]
        ref = c["reference_answer"]
        stu = c["student_answer"]
        cdesc = c["case_description"]
        expected_rel = c["expected_qualitative_relation"]
        sev_map = c.get("severities", {})

        # Expected severity from development label
        exp_sev = "NONE"
        if sev_map:
            # Pick highest severity label
            sev_values = list(sev_map.values())
            if "CORE_CONTRADICTION" in sev_values:
                exp_sev = "CORE_CONTRADICTION"
            elif "MODERATE" in sev_values:
                exp_sev = "MODERATE"
            elif "MINOR" in sev_values:
                exp_sev = "MINOR"
            elif "UNRESOLVED" in sev_values:
                exp_sev = "UNRESOLVED"
            else:
                exp_sev = sev_values[0]

        # 1. Row for phase4d_controlled_cases.csv
        controlled_cases_rows.append({
            "case_id": cid,
            "domain": domain,
            "category_type": cat_type,
            "case_name": cname,
            "question": q,
            "reference_answer": ref,
            "student_answer": stu,
            "case_description": cdesc,
            "expected_qualitative_relation": expected_rel,
            "expected_severity": exp_sev,
        })

        # 2. Run end-to-end evaluation (let pipeline infer domain automatically if domain is MIXED)
        active_domain = domain if domain in ("PRIMARY_KEY", "BST", "COMPILER") else None
        eval_res = pipeline.evaluate(
            question=q,
            reference_answer=ref,
            student_answer=stu,
            domain=active_domain,
        )
        score_res = eval_res.score_result

        # Identify predicted severity from itemized adjustments
        pred_sev = "NONE"
        pred_sev_score = 0.0
        for it in score_res.itemized_adjustments:
            if it.severity_level != "NONE":
                pred_sev = it.severity_level
                pred_sev_score = it.severity_score
                if pred_sev == "CORE_CONTRADICTION":
                    break

        # 3. Row for phase4d_end_to_end_results.csv
        end_to_end_rows.append({
            "case_id": cid,
            "domain": domain,
            "category_type": cat_type,
            "case_name": cname,
            "student_answer": stu,
            "base_score": round(score_res.base_score, 4),
            "core_effective": round(score_res.core_effective_score, 4),
            "pos_adj": round(score_res.positive_adjustment, 4),
            "neg_adj": round(score_res.negative_adjustment, 4),
            "final_score": round(score_res.final_score, 4),
            "final_grade": round(score_res.final_grade, 4),
            "has_core_invalidation": score_res.has_core_invalidation,
            "core_count": score_res.core_contradiction_count,
            "predicted_severity": pred_sev,
            "severity_score": round(pred_sev_score, 4),
            "matched_count": score_res.counts.get("matched", 0),
            "correct_additional_count": score_res.counts.get("correct_additional", 0),
            "irrelevant_count": score_res.counts.get("irrelevant", 0),
            "incorrect_count": score_res.counts.get("incorrect", 0),
            "uncertain_count": score_res.counts.get("uncertain", 0),
            "explanation": score_res.explanation,
        })

        # 4. Phase 4B comparison
        p4b_record = phase4b_traces.get(cid, {})
        p4b_model_d_grade = p4b_record.get("models", {}).get("Model_D", {}).get("scaled_score", None)
        diff = (round(score_res.final_grade - p4b_model_d_grade, 4)) if p4b_model_d_grade is not None else 0.0

        sev_agreement = (pred_sev == exp_sev) if exp_sev != "NONE" else (pred_sev in ("NONE", "UNRESOLVED"))

        # Explanation of difference / agreement
        comp_explanation = ""
        if p4b_model_d_grade is None:
            comp_explanation = "Phase 4D dedicated extension case; no direct Phase 4B antecedent."
        elif abs(diff) < 1e-4:
            if sev_agreement:
                comp_explanation = f"Exact score agreement ({score_res.final_grade:.2f}/5.00); automatic severity matches expected label ({pred_sev})."
            else:
                comp_explanation = f"Exact score agreement ({score_res.final_grade:.2f}/5.00); severity difference had neutral score impact."
        else:
            if exp_sev in ("MINOR", "MODERATE") and pred_sev == "NONE":
                comp_explanation = (
                    f"Epistemic divergence (+{diff:.2f}): unstated peripheral fact classified as UNCERTAIN "
                    f"by reference-grounded pipeline (producing 0.0 penalty), whereas Phase 4B applied manual override deduction."
                )
            else:
                comp_explanation = f"Score divergence ({diff:+.2f}): Phase 4B Model D ({p4b_model_d_grade:.2f}) vs Phase 4D ({score_res.final_grade:.2f})."

        comparison_rows.append({
            "case_id": cid,
            "base_score": round(score_res.base_score, 4),
            "phase4b_model_d": round(p4b_model_d_grade, 4) if p4b_model_d_grade is not None else "N/A",
            "phase4d_auto_model_d": round(score_res.final_grade, 4),
            "predicted_severity": pred_sev,
            "expected_dev_severity": exp_sev,
            "score_difference": diff,
            "severity_agreement": sev_agreement,
            "explanation": comp_explanation,
        })

        # 5. Score Trace for phase4d_score_traces.json
        score_traces[cid] = {
            "case_id": cid,
            "domain": domain,
            "category_type": cat_type,
            "case_name": cname,
            "question": q,
            "reference_answer": ref,
            "student_answer": stu,
            "base_score_normalized": round(score_res.base_score, 4),
            "base_score_scaled": round(score_res.base_score * 5.0, 4),
            "final_score_normalized": round(score_res.final_score, 4),
            "final_score_scaled": round(score_res.final_grade, 4),
            "has_core_invalidation": score_res.has_core_invalidation,
            "core_contradiction_count": score_res.core_contradiction_count,
            "positive_adjustment": round(score_res.positive_adjustment, 4),
            "negative_adjustment": round(score_res.negative_adjustment, 4),
            "net_adjustment": round(score_res.net_adjustment, 4),
            "counts": score_res.counts,
            "itemized_adjustments": [it.to_dict() for it in score_res.itemized_adjustments],
            "explanation": score_res.explanation,
            "phase4b_comparison": {
                "phase4b_model_d_scaled": p4b_model_d_grade,
                "score_difference": diff,
                "expected_severity": exp_sev,
                "predicted_severity": pred_sev,
                "severity_agreement": sev_agreement,
                "explanation": comp_explanation,
            },
        }

    return controlled_cases_rows, end_to_end_rows, score_traces, comparison_rows


def export_phase4d_artifacts(
    controlled_cases: List[Dict[str, Any]],
    end_to_end_results: List[Dict[str, Any]],
    score_traces: Dict[str, Any],
    comparisons: List[Dict[str, Any]],
    output_dir: str = "evaluation/scoring_development",
) -> None:
    os.makedirs(output_dir, exist_ok=True)

    # 1. phase4d_controlled_cases.csv
    cases_path = os.path.join(output_dir, "phase4d_controlled_cases.csv")
    with open(cases_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(controlled_cases[0].keys()))
        writer.writeheader()
        writer.writerows(controlled_cases)

    # 2. phase4d_end_to_end_results.csv
    e2e_path = os.path.join(output_dir, "phase4d_end_to_end_results.csv")
    with open(e2e_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(end_to_end_results[0].keys()))
        writer.writeheader()
        writer.writerows(end_to_end_results)

    # 3. phase4d_score_traces.json
    traces_path = os.path.join(output_dir, "phase4d_score_traces.json")
    with open(traces_path, "w", encoding="utf-8") as f:
        json.dump(score_traces, f, indent=2)

    # 4. phase4d_comparison.csv
    comp_path = os.path.join(output_dir, "phase4d_comparison.csv")
    with open(comp_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(comparisons[0].keys()))
        writer.writeheader()
        writer.writerows(comparisons)

    print(f"Phase 4D Artifacts exported successfully to {output_dir}/")
    print(f"  - Controlled Cases: {len(controlled_cases)} rows -> {cases_path}")
    print(f"  - End-to-End Results: {len(end_to_end_results)} rows -> {e2e_path}")
    print(f"  - Score Traces: {len(score_traces)} traces -> {traces_path}")
    print(f"  - Comparisons: {len(comparisons)} rows -> {comp_path}")


if __name__ == "__main__":
    c_cases, e2e_res, traces, comps = run_phase4d_evaluation()
    export_phase4d_artifacts(c_cases, e2e_res, traces, comps)
