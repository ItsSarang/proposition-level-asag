# Benchmark Results Summary

Benchmark: Mohler ASAG Dataset (N = 2,273 active records across 81 questions)

| Model Version | System Name | Pearson r | Spearman rho | MAE | RMSE | Status |
|---|---|---|---|---|---|---|
| **V0** | TF-IDF Baseline | **0.4485** | **0.4357** | 0.9984 | 1.2584 | FROZEN |
| **V1** | Base ASAG (Basak-inspired) | 0.3013 | 0.3129 | 1.2185 | 1.5457 | FROZEN |
| **V2** | Proposition-Level ASAG | 0.2227 | 0.2442 | 0.9996 | 1.3090 | FROZEN |
| **V3** | Enhanced Proposition ASAG | 0.3145 | 0.3270 | 1.0520 | 1.3810 | FROZEN |
| **V4** | Severity-Aware ASAG (Model D) | 0.3204 | 0.3340 | 0.9234 | 1.2065 | FROZEN |
| **V5** | Final Proposition ASAG (Model D2)| **0.3444** | **0.3541** | **0.9220** | **1.2001** | FROZEN |

*Note: V5 achieves the highest correlation and lowest error among all semantic/dependency ASAG systems. However, lexical TF-IDF remains globally superior on holistic human grade correlation.*
