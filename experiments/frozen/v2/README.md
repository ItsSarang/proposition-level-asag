# Frozen Experiment: V2 — Proposition-Level ASAG

- **Model Version**: V2
- **Model Name**: Proposition-Level ASAG (Historical System 3, Stages 11-14)
- **Status**: FROZEN
- **Dataset**: Mohler ASAG benchmark (2,273 active records across 81 questions)
- **Methodology**: Base ASAG + unmatched proposition extraction + 4-way classification + additive linear scoring adjustment (+0.10 for correct additional, -0.20 for incorrect).
- **Evaluation Runner**: `evaluation/runners/proposed_asag_runner.py` / `evaluation/runners/evaluate_v2.py`
- **Configuration**: `experiments/configs/v2.json`
- **Benchmark Metrics** (from `summary.json` on full active benchmark, N=2,273):
  - Pearson r: 0.1342
  - Spearman rho: 0.0765
  - MAE: 3.2176
  - RMSE: 3.5179
