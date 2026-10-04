# Frozen Experiment: V1 — Base ASAG

- **Model Version**: V1
- **Model Name**: Base ASAG (Basak et al. 2019-inspired)
- **Status**: FROZEN
- **Dataset**: Mohler ASAG benchmark (2,273 active records across 81 questions)
- **Methodology**: Classical dependency triples, 4-tier lexical-semantic similarity, propositional entailment, strict reference coverage.
- **Evaluation Runner**: `evaluation/runners/base_asag_runner.py` / `evaluation/runners/evaluate_v1.py`
- **Configuration**: `experiments/configs/v1.json`
- **Benchmark Metrics**:
  - Pearson r: 0.3013
  - Spearman rho: 0.3129
  - MAE: 1.2185
  - RMSE: 1.5457
