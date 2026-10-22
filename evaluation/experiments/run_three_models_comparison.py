"""
Execution script for Full Experimental Comparison across the Three ASAG Systems:
- Model 1: TF-IDF + Cosine Baseline (V0)
- Model 2: Base ASAG (Basak et al. 2019-inspired Clausal Dependency ASAG) (V1)
- Model 3a: Proposed ASAG — Pure Symbolic Proposition Level (V5 Symbolic)
- Model 3b: Proposed ASAG — Calibrated Hybrid Proposition-Lexical Engine (V5 Proposed Active)

Evaluates performance across:
1. Full Active Mohler Benchmark (N=2,273)
2. Assignments 1–10 (N=1,721)
3. Exams 11–12 (N=552)
4. Sentential Reference Questions (N=1,341)
5. Non-Sentential Reference Questions (N=932)

Generates:
- evaluation/results/three_models_comparison/three_models_summary.json
- evaluation/results/three_models_comparison/three_models_predictions.csv
"""

from __future__ import annotations

import json
import math
from pathlib import Path
import re
from typing import Any, Dict, List

import numpy as np
import pandas as pd
from scipy import stats

from evaluation.metrics.asag_metrics import compute_all_metrics

_COMMON_STOPS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are",
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by",
    "did", "do", "does", "doing", "down", "during", "each", "few", "for", "from", "further",
    "had", "has", "have", "having", "he", "her", "here", "hers", "herself", "him", "himself",
    "his", "how", "i", "if", "in", "into", "is", "it", "its", "itself", "me", "more", "most",
    "my", "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other",
    "our", "ours", "ourselves", "out", "over", "own", "same", "she", "should", "so", "some",
    "such", "than", "that", "the", "their", "theirs", "them", "themselves", "then", "there",
    "these", "they", "this", "those", "through", "to", "too", "under", "until", "up", "very",
    "was", "we", "were", "what", "when", "where", "which", "while", "who", "whom", "why", "with", "you", "your"
}

def compute_calibrated_grades(df: pd.DataFrame) -> List[float]:
    alpha = 0.25
    k = 15.0
    x0 = 0.05

    def _raw_s(v: float) -> float:
        try:
            return 1.0 / (1.0 + math.exp(-k * (v - x0)))
        except OverflowError:
            return 0.0 if (-k * (v - x0)) > 0 else 1.0

    s_0 = _raw_s(0.0)
    s_1 = _raw_s(1.0)
    denom = s_1 - s_0

    calib_grades = []
    for _, row in df.iterrows():
        stu_tokens = set(re.findall(r"\b[a-zA-Z0-9_]+\b", str(row["student_text"]).lower()))
        ref_tokens = set(re.findall(r"\b[a-zA-Z0-9_]+\b", str(row["reference_text"]).lower()))
        content_overlap = (stu_tokens - _COMMON_STOPS) & (ref_tokens - _COMMON_STOPS)

        score_norm = float(row["v5_full_grade"]) / 5.0
        lex_sim = float(row["v0_grade"]) / 5.0

        if not content_overlap and float(row["base_coverage"]) <= 0.0 and int(row["correct_additional_count"]) == 0:
            raw_hybrid = 0.0
        else:
            raw_hybrid = alpha * score_norm + (1.0 - alpha) * lex_sim

        s_val = _raw_s(raw_hybrid)
        calib = (s_val - s_0) / denom * 5.0 if denom > 0 else raw_hybrid * 5.0

        if bool(row["has_core_invalidation"]):
            calib *= 0.5
        calib = float(max(0.0, min(5.0, calib)))
        calib_grades.append(calib)

    return calib_grades

def run_comparison():
    input_csv = Path("evaluation/results/task8_benchmark/mohler_task8_evaluation_predictions.csv")
    if not input_csv.exists():
        raise FileNotFoundError(f"Input predictions file not found: {input_csv}")

    df = pd.read_csv(input_csv)
    print(f"Loaded {len(df)} records from {input_csv}")

    # Compute Calibrated Hybrid predictions
    df["v5_calibrated_grade"] = compute_calibrated_grades(df)

    out_dir = Path("evaluation/results/three_models_comparison")
    out_dir.mkdir(parents=True, exist_ok=True)

    out_csv = out_dir / "three_models_predictions.csv"
    df.to_csv(out_csv, index=False)
    print(f"Saved predictions with calibrated V5 to {out_csv}")

    subsets = {
        "full_active": {
            "name": "Full Active Benchmark",
            "df": df,
            "description": "Entire active evaluation benchmark without omitted ordering/selection tasks",
        },
        "assignments_1_10": {
            "name": "Assignments 1–10",
            "df": df[df["assignment"] <= 10],
            "description": "Regular homework assignments covering fundamental C++ programming",
        },
        "exams_11_12": {
            "name": "Exams 11–12",
            "df": df[df["assignment"] > 10],
            "description": "Midterm and final exam questions requiring synthetic explanations",
        },
        "sentential_ref": {
            "name": "Sentential Reference Questions",
            "df": df[~df["has_non_sentential_ref"]],
            "description": "Questions where the reference answer forms a complete grammatical clause",
        },
        "non_sentential_ref": {
            "name": "Non-Sentential Reference Questions",
            "df": df[df["has_non_sentential_ref"]],
            "description": "Questions where reference answer is a non-finite clause or nominal fragment",
        },
    }

    model_cols = [
        ("V0", "Model 1: TF-IDF Baseline", "v0_grade"),
        ("V1", "Model 2: Base ASAG (Basak et al.)", "v1_grade"),
        ("V5_Symbolic", "Model 3a: Proposed ASAG (Symbolic)", "v5_full_grade"),
        ("V5_Calibrated", "Model 3b: Proposed ASAG (Calibrated Hybrid)", "v5_calibrated_grade"),
    ]

    summary_results: Dict[str, Any] = {
        "benchmark_metadata": {
            "total_records": len(df),
            "scale_max": 5.0,
            "models_evaluated": [
                {"id": "V0", "name": "Model 1: TF-IDF Baseline (Cosine Sim)", "paradigm": "Lexical Vector Overlap"},
                {"id": "V1", "name": "Model 2: Base ASAG (Basak-inspired)", "paradigm": "Clausal Dependency Triples"},
                {"id": "V5_Symbolic", "name": "Model 3a: Proposed ASAG (Symbolic)", "paradigm": "Proposition-Level Symbolic + Rules"},
                {"id": "V5_Calibrated", "name": "Model 3b: Proposed ASAG (Calibrated)", "paradigm": "Calibrated Hybrid Proposition-Lexical"},
            ],
        },
        "subsets": {},
    }

    for skey, sinfo in subsets.items():
        sdf = sinfo["df"]
        y_true = sdf["human_score"].values
        n_samples = len(sdf)
        gt_mean = float(np.mean(y_true))
        gt_std = float(np.std(y_true))

        subset_record: Dict[str, Any] = {
            "name": sinfo["name"],
            "n_samples": n_samples,
            "pct_of_dataset": round(n_samples / len(df) * 100.0, 2),
            "description": sinfo["description"],
            "ground_truth": {
                "mean": round(gt_mean, 4),
                "std": round(gt_std, 4),
            },
            "models": {},
        }

        print(f"\n=======================================================")
        print(f" SUBSET: {sinfo['name']} (N={n_samples})")
        print(f" Human Ground Truth: Mean={gt_mean:.4f}, Std={gt_std:.4f}")
        print(f"=======================================================")

        for mid, mname, mcol in model_cols:
            y_pred = sdf[mcol].values
            m = compute_all_metrics(mname, y_true, y_pred, min_rating=0, max_rating=5)

            pr, pp = stats.pearsonr(y_pred, y_true) if np.std(y_pred) > 1e-9 else (None, None)
            sr, sp = stats.spearmanr(y_pred, y_true) if np.std(y_pred) > 1e-9 else (None, None)

            pred_mean = float(np.mean(y_pred))
            pred_std = float(np.std(y_pred))
            bias = pred_mean - gt_mean

            pct_exact_zero = float(np.mean(y_pred == 0.0) * 100.0)
            pct_near_zero = float(np.mean(y_pred <= 0.5) * 100.0)
            pct_middle = float(np.mean((y_pred > 0.5) & (y_pred < 4.0)) * 100.0)
            pct_high = float(np.mean(y_pred >= 4.0) * 100.0)

            model_data = {
                "system_id": mid,
                "name": mname,
                "metrics": {
                    "mae": round(m.mae, 4),
                    "rmse": round(m.rmse, 4),
                    "pearson_r": round(float(pr), 4) if pr is not None else None,
                    "pearson_p": float(pp) if pp is not None else None,
                    "spearman_rho": round(float(sr), 4) if sr is not None else None,
                    "spearman_p": float(sp) if sp is not None else None,
                    "qwk": round(m.qwk, 4),
                },
                "distribution": {
                    "mean": round(pred_mean, 4),
                    "std": round(pred_std, 4),
                    "descriptive_bias": round(bias, 4),
                    "pct_exactly_zero": round(pct_exact_zero, 2),
                    "pct_near_zero": round(pct_near_zero, 2),
                    "pct_middle": round(pct_middle, 2),
                    "pct_high_grade": round(pct_high, 2),
                },
            }
            subset_record["models"][mid] = model_data

            r_str = f"{pr:.4f}" if pr is not None else "N/A"
            rho_str = f"{sr:.4f}" if sr is not None else "N/A"
            print(f"{mid:14s} | MAE: {m.mae:.4f} | RMSE: {m.rmse:.4f} | r: {r_str:6s} | rho: {rho_str:6s} | QWK: {m.qwk:.4f} | Mean: {pred_mean:.2f} (Bias: {bias:+.2f})")

        summary_results["subsets"][skey] = subset_record

    out_json = out_dir / "three_models_summary.json"
    with open(out_json, "w") as f:
        json.dump(summary_results, f, indent=2)
    print(f"\nSaved full comparative summary to {out_json}")

if __name__ == "__main__":
    run_comparison()
