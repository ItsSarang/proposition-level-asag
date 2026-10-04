"""
Scoring Stability and Verbosity Stress Experiments.

Evaluates four scoring mechanisms under controlled verbosity stress tests and
across the Mohler ASAG benchmark:

Mechanisms:
A. Base Only (Control: reference coverage only; additions contribute 0.0)
B. Base + Unbounded Linear Bonus (Linear +w per addition, clipped only at boundaries)
C. Base + Bounded Saturating Bonus (Diminishing marginal returns, horizontal asymptote)
D. Decomposed Core + Bounded Additional - Bounded Contradiction (Explicit decomposed architecture)

Stress Tests:
1. Irrelevant Proposition Injection (k = 0, 1, 2, 5, 10, 20 off-topic propositions)
2. Correct Additional Accumulation (k = 0, 1, 2, 5, 10, 20 correct propositions)
3. Contradiction Accumulation (k = 0, 1, 2, 5, 10, 20 incorrect propositions)
4. Mixed Verbosity Stress (k irrelevant + k correct + 1 incorrect)
5. Empirical Length Correlation and Benchmark Evaluation on Mohler Dataset

Exports results to: evaluation/results/scoring_stability_experiments.json
"""

import argparse
from collections import defaultdict
from datetime import datetime, timezone
import json
import logging
import math
from pathlib import Path
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from evaluation.dataset.mohler_loader import MohlerLoader
from evaluation.metrics.asag_metrics import compute_all_metrics
from proposed_asag.classification.robust_classifier import (
    AdditionalInfoClass,
    ClassifiedProposition,
)
from proposed_asag.overhauled_pipeline import OverhauledASAGPipeline
from base_asag.representation.hybrid import (
    Modality,
    Polarity,
    PropositionType,
    RobustProposition,
)
from proposed_asag.scoring.bounded_scorer import (
    BoundedScoreResult,
    BoundedScorer,
    ScoringStrategy,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


# --- Helper to create synthetic ClassifiedPropositions for stress testing ---
def make_mock_proposition(
    text: str,
    classification: AdditionalInfoClass,
    prop_type: PropositionType = PropositionType.TRIPLE,
) -> ClassifiedProposition:
    prop = RobustProposition(
        subject="term",
        predicate="is",
        object="defined",
        subject_lemma="term",
        predicate_lemma="be",
        object_lemma="define",
        representation_type=prop_type,
        polarity=Polarity.POSITIVE,
        modality=Modality.ASSERTED,
        source_text=text,
        char_start=0,
        char_end=len(text),
        sentence_index=0,
        token_indices=(0, 1, 2),
        dependency_evidence=(),
    )
    score_effect = 0.0
    if classification == AdditionalInfoClass.CORRECT_ADDITIONAL:
        score_effect = 0.10
    elif classification == AdditionalInfoClass.INCORRECT:
        score_effect = -0.20
    return ClassifiedProposition(
        proposition=prop,
        classification=classification,
        relevance_evidence=None,
        contradiction_evidence=None,
        score_effect=score_effect,
        rationale=f"Simulated {classification.value} proposition",
    )


# --- Four Scoring Architectures ---

def score_model_a_base_only(base_score: float, classified_props: List[ClassifiedProposition]) -> Dict[str, Any]:
    """Model A: Base Only (Control). Additions have zero effect."""
    return {
        "model": "A_BASE_ONLY",
        "base_score": base_score,
        "bonus": 0.0,
        "penalty": 0.0,
        "final_score": max(0.0, min(1.0, base_score)),
    }


def score_model_b_unbounded_linear(
    base_score: float,
    classified_props: List[ClassifiedProposition],
    linear_bonus: float = 0.10,
    linear_penalty: float = 0.20,
) -> Dict[str, Any]:
    """Model B: Base + Unbounded Linear Bonus."""
    n_correct = sum(1 for p in classified_props if p.classification == AdditionalInfoClass.CORRECT_ADDITIONAL)
    n_incorrect = sum(1 for p in classified_props if p.classification == AdditionalInfoClass.INCORRECT)
    bonus = n_correct * linear_bonus
    penalty = n_incorrect * linear_penalty
    raw = base_score + bonus - penalty
    clipped = max(0.0, min(1.0, raw))
    return {
        "model": "B_UNBOUNDED_LINEAR",
        "base_score": base_score,
        "bonus": bonus,
        "penalty": penalty,
        "final_score": clipped,
    }


def score_model_c_bounded_saturating(
    base_score: float,
    classified_props: List[ClassifiedProposition],
    max_bonus: float = 0.30,
    max_penalty: float = 0.40,
    diminishing_rate: float = 0.50,
) -> Dict[str, Any]:
    """Model C: Base + Bounded Saturating Bonus."""
    n_correct = sum(1 for p in classified_props if p.classification == AdditionalInfoClass.CORRECT_ADDITIONAL)
    n_incorrect = sum(1 for p in classified_props if p.classification == AdditionalInfoClass.INCORRECT)

    bonus = 0.0
    if n_correct > 0:
        scaled = diminishing_rate * n_correct
        bonus = max_bonus * (scaled / (1.0 + scaled))

    penalty = 0.0
    if n_incorrect > 0:
        scaled_neg = 0.50 * n_incorrect
        penalty = max_penalty * (scaled_neg / (1.0 + scaled_neg))

    raw = base_score + bonus - penalty
    clipped = max(0.0, min(1.0, raw))
    return {
        "model": "C_BOUNDED_SATURATING",
        "base_score": base_score,
        "bonus": bonus,
        "penalty": penalty,
        "final_score": clipped,
    }


def score_model_d_decomposed_core(
    base_score: float,
    classified_props: List[ClassifiedProposition],
    max_bonus: float = 0.30,
    max_penalty: float = 0.40,
    diminishing_rate: float = 0.50,
) -> Dict[str, Any]:
    """
    Model D: Decomposed Core + Bounded Additional - Bounded Contradiction.
    Explicitly tracks Core coverage, Bounded Additional benefit, and Bounded Contradiction penalty.
    """
    core_score = max(0.0, min(1.0, base_score))
    n_correct = sum(1 for p in classified_props if p.classification == AdditionalInfoClass.CORRECT_ADDITIONAL)
    n_incorrect = sum(1 for p in classified_props if p.classification == AdditionalInfoClass.INCORRECT)
    n_irrelevant = sum(1 for p in classified_props if p.classification == AdditionalInfoClass.IRRELEVANT)

    # Saturating additional credit
    bounded_additional = 0.0
    if n_correct > 0:
        s = diminishing_rate * n_correct
        bounded_additional = max_bonus * (s / (1.0 + s))

    # Saturating contradiction penalty
    bounded_contradiction = 0.0
    if n_incorrect > 0:
        s_neg = 0.50 * n_incorrect
        bounded_contradiction = max_penalty * (s_neg / (1.0 + s_neg))

    # Irrelevant information is strictly neutral (+0.0)
    irrelevant_effect = 0.0

    final_score = max(0.0, min(1.0, core_score + bounded_additional - bounded_contradiction + irrelevant_effect))
    return {
        "model": "D_DECOMPOSED_CORE",
        "core_score": core_score,
        "bounded_additional": bounded_additional,
        "bounded_contradiction": bounded_contradiction,
        "irrelevant_effect": irrelevant_effect,
        "final_score": final_score,
    }


def run_controlled_stress_tests() -> Dict[str, Any]:
    """Execute synthetic verbosity injection tests across k in [0, 1, 2, 5, 10, 20]."""
    k_values = [0, 1, 2, 5, 10, 20]
    base_levels = [0.0, 0.20, 0.50, 0.80, 1.0]

    stress_results: Dict[str, Any] = {
        "irrelevant_bombardment": {},
        "correct_addition_accumulation": {},
        "contradiction_accumulation": {},
        "mixed_stress": {},
    }

    # 1. Irrelevant Bombardment (injecting k irrelevant propositions)
    # Testing whether irrelevant information alters grades
    irr_tests = {}
    for base in base_levels:
        base_runs = []
        for k in k_values:
            props = [
                make_mock_proposition(f"irrelevant_{i}", AdditionalInfoClass.IRRELEVANT)
                for i in range(k)
            ]
            res_a = score_model_a_base_only(base, props)["final_score"]
            res_b = score_model_b_unbounded_linear(base, props)["final_score"]
            res_c = score_model_c_bounded_saturating(base, props)["final_score"]
            res_d = score_model_d_decomposed_core(base, props)["final_score"]
            base_runs.append({
                "k_irrelevant": k,
                "model_a_base_only": round(res_a, 4),
                "model_b_linear": round(res_b, 4),
                "model_c_saturating": round(res_c, 4),
                "model_d_decomposed": round(res_d, 4),
            })
        irr_tests[f"base_{base:.2f}"] = base_runs
    stress_results["irrelevant_bombardment"] = irr_tests

    # 2. Correct Addition Accumulation (injecting k correct additional propositions)
    corr_tests = {}
    for base in base_levels:
        base_runs = []
        for k in k_values:
            props = [
                make_mock_proposition(f"correct_{i}", AdditionalInfoClass.CORRECT_ADDITIONAL)
                for i in range(k)
            ]
            res_a = score_model_a_base_only(base, props)["final_score"]
            res_b = score_model_b_unbounded_linear(base, props)["final_score"]
            res_c = score_model_c_bounded_saturating(base, props)["final_score"]
            res_d = score_model_d_decomposed_core(base, props)["final_score"]
            base_runs.append({
                "k_correct": k,
                "model_a_base_only": round(res_a, 4),
                "model_b_linear": round(res_b, 4),
                "model_c_saturating": round(res_c, 4),
                "model_d_decomposed": round(res_d, 4),
            })
        corr_tests[f"base_{base:.2f}"] = base_runs
    stress_results["correct_addition_accumulation"] = corr_tests

    # 3. Contradiction Accumulation (injecting k incorrect propositions)
    contra_tests = {}
    for base in base_levels:
        base_runs = []
        for k in k_values:
            props = [
                make_mock_proposition(f"contradiction_{i}", AdditionalInfoClass.INCORRECT)
                for i in range(k)
            ]
            res_a = score_model_a_base_only(base, props)["final_score"]
            res_b = score_model_b_unbounded_linear(base, props)["final_score"]
            res_c = score_model_c_bounded_saturating(base, props)["final_score"]
            res_d = score_model_d_decomposed_core(base, props)["final_score"]
            base_runs.append({
                "k_contradictions": k,
                "model_a_base_only": round(res_a, 4),
                "model_b_linear": round(res_b, 4),
                "model_c_saturating": round(res_c, 4),
                "model_d_decomposed": round(res_d, 4),
            })
        contra_tests[f"base_{base:.2f}"] = base_runs
    stress_results["contradiction_accumulation"] = contra_tests

    # 4. Mixed Verbosity Stress: k irrelevant + k correct + 1 incorrect
    mixed_tests = {}
    for base in [0.20, 0.50, 0.80]:
        base_runs = []
        for k in k_values:
            props = []
            props.extend([make_mock_proposition(f"irr_{i}", AdditionalInfoClass.IRRELEVANT) for i in range(k)])
            props.extend([make_mock_proposition(f"cor_{i}", AdditionalInfoClass.CORRECT_ADDITIONAL) for i in range(k)])
            props.append(make_mock_proposition("inc_0", AdditionalInfoClass.INCORRECT))
            res_a = score_model_a_base_only(base, props)["final_score"]
            res_b = score_model_b_unbounded_linear(base, props)["final_score"]
            res_c = score_model_c_bounded_saturating(base, props)["final_score"]
            res_d = score_model_d_decomposed_core(base, props)["final_score"]
            base_runs.append({
                "k_each": k,
                "total_props": 2 * k + 1,
                "model_a_base_only": round(res_a, 4),
                "model_b_linear": round(res_b, 4),
                "model_c_saturating": round(res_c, 4),
                "model_d_decomposed": round(res_d, 4),
            })
        mixed_tests[f"base_{base:.2f}"] = base_runs
    stress_results["mixed_stress"] = mixed_tests

    return stress_results


def run_empirical_benchmark_verbosity(limit: Optional[int] = None) -> Dict[str, Any]:
    """
    Run empirical verbosity correlation on real Mohler dataset records.
    Computes length correlation with scores across the 4 models.
    """
    dataset = MohlerLoader.load_processed_csv().filter_active()
    records = dataset.records[:limit] if limit is not None else dataset.records

    logger.info("Running Empirical Verbosity Benchmark across %d records...", len(records))
    pipeline = OverhauledASAGPipeline()

    y_true: List[float] = []
    y_pred_a: List[float] = []
    y_pred_b: List[float] = []
    y_pred_c: List[float] = []
    y_pred_d: List[float] = []
    word_lengths: List[int] = []
    prop_counts: List[int] = []

    for r in records:
        res = pipeline.evaluate(r.question, r.reference_answer, r.student_answer_cleaned)
        classified_props = (
            res.classification_result.classified_propositions
            if res.classification_result is not None
            else []
        )
        base_norm = res.base_score_normalized

        score_a = score_model_a_base_only(base_norm, classified_props)["final_score"] * 5.0
        score_b = score_model_b_unbounded_linear(base_norm, classified_props)["final_score"] * 5.0
        score_c = score_model_c_bounded_saturating(base_norm, classified_props)["final_score"] * 5.0
        score_d = score_model_d_decomposed_core(base_norm, classified_props)["final_score"] * 5.0

        w_len = len(r.student_answer_cleaned.split())
        p_count = len(classified_props) + res.matched_propositions_count

        y_true.append(r.score_ave)
        y_pred_a.append(score_a)
        y_pred_b.append(score_b)
        y_pred_c.append(score_c)
        y_pred_d.append(score_d)
        word_lengths.append(w_len)
        prop_counts.append(p_count)

    # Compute ASAG evaluation metrics
    metrics_a = compute_all_metrics("Model_A_Base_Only", y_true, y_pred_a, 0, 5).to_dict()
    metrics_b = compute_all_metrics("Model_B_Linear", y_true, y_pred_b, 0, 5).to_dict()
    metrics_c = compute_all_metrics("Model_C_Saturating", y_true, y_pred_c, 0, 5).to_dict()
    metrics_d = compute_all_metrics("Model_D_Decomposed", y_true, y_pred_d, 0, 5).to_dict()

    # Compute correlation with answer length (word length and proposition count)
    def compute_corr(x_arr: List[float], y_arr: List[float]) -> float:
        if len(x_arr) < 2 or np.std(x_arr) == 0 or np.std(y_arr) == 0:
            return 0.0
        return float(np.corrcoef(x_arr, y_arr)[0, 1])

    human_length_corr = compute_corr(word_lengths, y_true)

    length_correlations = {
        "human_score_vs_word_length": round(human_length_corr, 4),
        "model_a_vs_word_length": round(compute_corr(word_lengths, y_pred_a), 4),
        "model_b_vs_word_length": round(compute_corr(word_lengths, y_pred_b), 4),
        "model_c_vs_word_length": round(compute_corr(word_lengths, y_pred_c), 4),
        "model_d_vs_word_length": round(compute_corr(word_lengths, y_pred_d), 4),
        "human_score_vs_prop_count": round(compute_corr(prop_counts, y_true), 4),
        "model_a_vs_prop_count": round(compute_corr(prop_counts, y_pred_a), 4),
        "model_b_vs_prop_count": round(compute_corr(prop_counts, y_pred_b), 4),
        "model_c_vs_prop_count": round(compute_corr(prop_counts, y_pred_c), 4),
        "model_d_vs_prop_count": round(compute_corr(prop_counts, y_pred_d), 4),
    }

    # Verbosity inflation analysis: compare top 10% longest answers vs bottom 10%
    sorted_by_len = sorted(
        zip(word_lengths, y_true, y_pred_a, y_pred_b, y_pred_c, y_pred_d),
        key=lambda x: x[0]
    )
    n_ten = max(1, len(sorted_by_len) // 10)
    shortest = sorted_by_len[:n_ten]
    longest = sorted_by_len[-n_ten:]

    verbosity_gap = {
        "shortest_decile_avg_words": round(float(np.mean([x[0] for x in shortest])), 1),
        "longest_decile_avg_words": round(float(np.mean([x[0] for x in longest])), 1),
        "human_score_gap": round(float(np.mean([x[1] for x in longest]) - np.mean([x[1] for x in shortest])), 4),
        "model_a_score_gap": round(float(np.mean([x[2] for x in longest]) - np.mean([x[2] for x in shortest])), 4),
        "model_b_score_gap": round(float(np.mean([x[3] for x in longest]) - np.mean([x[3] for x in shortest])), 4),
        "model_c_score_gap": round(float(np.mean([x[4] for x in longest]) - np.mean([x[4] for x in shortest])), 4),
        "model_d_score_gap": round(float(np.mean([x[5] for x in longest]) - np.mean([x[5] for x in shortest])), 4),
    }

    return {
        "sample_count": len(records),
        "evaluation_metrics": {
            "model_a_base_only": metrics_a,
            "model_b_linear": metrics_b,
            "model_c_saturating": metrics_c,
            "model_d_decomposed": metrics_d,
        },
        "length_correlations": length_correlations,
        "verbosity_gap": verbosity_gap,
    }


def main():
    parser = argparse.ArgumentParser(description="Run scoring stability and verbosity experiments.")
    parser.add_argument("--limit", type=int, default=None, help="Record limit for empirical test.")
    parser.add_argument("--output", type=str, default="evaluation/results/scoring_stability_experiments.json")
    args = parser.parse_args()

    logger.info("Executing controlled synthetic stress tests...")
    synthetic_stress = run_controlled_stress_tests()

    logger.info("Executing empirical Mohler benchmark verbosity experiments...")
    empirical_benchmark = run_empirical_benchmark_verbosity(limit=args.limit)

    full_report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "description": "Scoring Stability and High-Verbosity Stress Analysis",
        "models_evaluated": {
            "A_BASE_ONLY": "Strict reference proposition coverage. Zero effect from unmatched statements.",
            "B_UNBOUNDED_LINEAR": "Linear addition per proposition (+0.10 / -0.20), hard boundary clip only.",
            "C_BOUNDED_SATURATING": "Horizontal asymptote at +0.30 via non-linear diminishing returns.",
            "D_DECOMPOSED_CORE": "Decomposed Core + Bounded Additional - Bounded Contradiction.",
        },
        "controlled_synthetic_stress_tests": synthetic_stress,
        "empirical_benchmark_verbosity": empirical_benchmark,
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, mode="w", encoding="utf-8") as f:
        json.dump(full_report, f, indent=2)

    logger.info("Saved scoring stability experiments to %s", args.output)


if __name__ == "__main__":
    main()
