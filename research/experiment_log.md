# Experiment Log

| Experiment | Model Evaluated | Records | Pearson r | Spearman rho | MAE | RMSE | Key Milestone / Findings |
|---|---|---|---|---|---|---|---|
| **Stage 1** | V0 (TF-IDF) | Demo | N/A | N/A | N/A | N/A | Baseline lexical implementation verified. |
| **Stage 10** | V1 (Base ASAG) | Demo | N/A | N/A | N/A | N/A | Full dependency triple pipeline integrated. |
| **Stage 15.2** | V0, V1, V2 | 2,273 | 0.4184 (V0)<br>0.1379 (V1)<br>0.1342 (V2) | 0.4424 (V0)<br>0.1181 (V1)<br>0.0765 (V2) | 2.6571 (V0)<br>3.8050 (V1)<br>3.2176 (V2) | 2.9178 (V0)<br>4.0373 (V1)<br>3.5179 (V2) | First full benchmark. Unmatched info analysis reduced MAE but degraded rank correlation due to verbosity bias. |
| **Stage 16** | Qualitative Error Analysis | 2,273 | - | - | - | - | Diagnosed 33/81 reference answers as non-sentential fragments; identified over-crediting of conversational filler. |
| **Experiment 3** | V3 (Current Proposed) | 2,273 | 0.2037 | 0.2007 | 3.5955 | 3.8862 | Hungarian matching and bounded scoring stabilized adjustments. |
| **Experiment 4** | V4 (Severity-Aware) | 2,273 | 0.2055 | 0.2033 | 3.6288 | 3.9270 | Model D introduced core invalidation discount and domain knowledge verification. |
| **Phase 6 Pilot** | Annotation Pilot | 50 items | - | - | - | - | AI annotation pilot achieved Cohen's kappa = 0.8054. Confirmed core paraphrase vs additional distinction. |
| **Experiment 5** | V5 (Final ASAG) | 2,273 | 0.2428 | 0.2404 | 3.4711 | 3.7637 | Final Proposed Model. Added core recovery, non-sentential canonicalization, and contradiction guards. Highest correlation among semantic ASAG systems. |

*Note: TF-IDF (V0) remains stronger than the semantic/dependency models on the primary full active benchmark; see the frozen Experiment 5 results for the exact evaluation metrics.*
