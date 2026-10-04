# Frozen Experiment: V4 — Severity-Aware Proposition ASAG

- **Model Version**: V4
- **Model Name**: Severity-Aware Proposition ASAG (Experiment 4 / Model D)
- **Status**: FROZEN
- **Dataset**: Mohler ASAG benchmark (2,273 active records across 81 questions)
- **Methodology**: Experiment 4 severity-aware contradiction analysis with Model D multiplicative core invalidation discount and diminishing bonus.
- **Artifacts**: Located in `evaluation/experiments/experiment_4/`
  - Predictions: `experiment_4_results.csv`
  - Summary: `experiment_4_summary.json`
  - Manifest: `experiment_4_manifest.json`
  - Report: `experiment_4_report.md`
- **Configuration**: `experiments/configs/v4.json`
- **Benchmark Metrics** (from `summary.json` on full active benchmark, N=2,273):
  - Pearson r: 0.2055
  - Spearman rho: 0.2033
  - MAE: 3.6288
  - RMSE: 3.9270
