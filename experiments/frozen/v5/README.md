# Frozen Experiment: V5 — Final Proposition-Level ASAG

- **Model Version**: V5
- **Model Name**: Final Proposition-Level ASAG (Experiment 5 / Model D2)
- **Status**: FROZEN (Final Proposed Model)
- **Dataset**: Mohler ASAG benchmark (2,273 active records across 81 questions)
- **Methodology**: Core paraphrase recovery, non-sentential reference canonicalization, contradiction guards, and Model D2 scoring.
- **Artifacts**: Located in `evaluation/experiments/experiment_5/`
  - Predictions: `experiment_5_results.csv`
  - Summary: `experiment_5_summary.json`
  - Config: `experiment_5_config.json`
  - Report: `experiment_5_report.md`
- **Configuration**: `experiments/configs/v5.json`
- **Benchmark Metrics** (from `summary.json` on full active benchmark, N=2,273):
  - Pearson r: 0.2428 (Highest among semantic/dependency ASAG systems)
  - Spearman rho: 0.2404
  - MAE: 3.4711
  - RMSE: 3.7637

TF-IDF (V0) remains stronger than the semantic/dependency models on the primary full active benchmark; see the frozen Experiment 5 results for the exact evaluation metrics.
