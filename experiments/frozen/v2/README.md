# Frozen Experiment: V2 — Proposition-Level ASAG

- **Model Version**: V2
- **Model Name**: Proposition-Level ASAG (Historical System 3, Stages 11-14)
- **Status**: FROZEN
- **Dataset**: Mohler ASAG benchmark (2,273 active records across 81 questions)
- **Methodology**: Base ASAG + unmatched proposition extraction + 4-way classification + additive linear scoring adjustment (+0.10 for correct additional, -0.20 for incorrect).
- **Evaluation Runner**: `evaluation/runners/proposed_asag_runner.py` / `evaluation/runners/evaluate_v2.py`
- **Configuration**: `experiments/configs/v2.json`
- **Benchmark Metrics**:
  - Pearson r: 0.2227
  - Spearman rho: 0.2442
  - MAE: 0.9996
  - RMSE: 1.3090
