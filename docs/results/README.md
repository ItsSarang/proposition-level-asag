# Benchmark Results Summary

Benchmark: Mohler ASAG Dataset (N = 2,273 active records across 81 questions)

| Model Version | System Name | Pearson r | Spearman rho | MAE | RMSE | Status |
|---|---|---|---|---|---|---|
| **V0** | TF-IDF Baseline | **0.4184** | **0.4424** | 2.6571 | 2.9178 | FROZEN |
| **V1** | Base ASAG (Basak-inspired) | 0.1379 | 0.1181 | 3.8050 | 4.0373 | FROZEN |
| **V2** | Proposition-Level ASAG | 0.1342 | 0.0765 | 3.2176 | 3.5179 | FROZEN |
| **V3** | Enhanced Proposition ASAG | 0.2037 | 0.2007 | 3.5955 | 3.8862 | FROZEN |
| **V4** | Severity-Aware ASAG (Model D) | 0.2055 | 0.2033 | 3.6288 | 3.9270 | FROZEN |
| **V5** | Final Proposition ASAG (Model D2)| **0.2428** | **0.2404** | **3.4711** | **3.7637** | FROZEN |

*Note: V5 achieves the highest correlation and lowest error among all semantic/dependency ASAG systems. TF-IDF (V0) remains stronger than the semantic/dependency models on the primary full active benchmark; see the frozen Experiment 5 results for the exact evaluation metrics.*
