# Frozen Experiment: V0 — TF-IDF Baseline

- **Model Version**: V0
- **Model Name**: TF-IDF Cosine Baseline
- **Status**: FROZEN
- **Dataset**: Mohler ASAG benchmark (2,273 active records across 81 questions)
- **Evaluation Runner**: `evaluation/runners/baseline_runner.py` / `evaluation/runners/evaluate_v0.py`
- **Configuration**: `experiments/configs/v0.json`
- **Benchmark Metrics** (from `summary.json` on full active benchmark, N=2,273):
  - Pearson r: 0.4184
  - Spearman rho: 0.4424
  - MAE: 2.6571
  - RMSE: 2.9178

TF-IDF (V0) remains stronger than the semantic/dependency models on the primary full active benchmark; see the frozen Experiment 5 results for the exact evaluation metrics.
