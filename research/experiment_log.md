# Experiment Log

| Experiment | Model Evaluated | Records | Pearson r | Spearman rho | MAE | RMSE | Key Milestone / Findings |
|---|---|---|---|---|---|---|---|
| **Stage 1** | V0 (TF-IDF) | Demo | N/A | N/A | N/A | N/A | Baseline lexical implementation verified. |
| **Stage 10** | V1 (Base ASAG) | Demo | N/A | N/A | N/A | N/A | Full dependency triple pipeline integrated. |
| **Stage 15.2** | V0, V1, V2 | 2,273 | 0.4485 (V0)<br>0.3013 (V1)<br>0.2227 (V2) | 0.4357 (V0)<br>0.3129 (V1)<br>0.2442 (V2) | 0.9984 (V0)<br>1.2185 (V1)<br>0.9996 (V2) | 1.2584 (V0)<br>1.5457 (V1)<br>1.3090 (V2) | First full benchmark. Unmatched info analysis reduced MAE but degraded rank correlation due to verbosity bias. |
| **Stage 16** | Qualitative Error Analysis | 2,273 | - | - | - | - | Diagnosed 33/81 reference answers as non-sentential fragments; identified over-crediting of conversational filler. |
| **Experiment 2** | Robust Representation | 2,273 | 0.3082 | 0.3195 | 1.1850 | 1.5120 | Extended clausal triples to hybrid propositions. |
| **Experiment 3** | System 4 Overhaul | 2,273 | 0.3145 | 0.3270 | 1.0520 | 1.3810 | Hungarian matching and bounded scoring stabilized adjustments. |
| **Experiment 4** | V4 (Severity-Aware) | 2,273 | 0.3204 | 0.3340 | 0.9234 | 1.2065 | Model D introduced core invalidation discount and domain knowledge verification. |
| **Phase 6 Pilot** | Annotation Pilot | 50 items | - | - | - | - | AI annotation pilot achieved Cohen's kappa = 0.8054. Confirmed core paraphrase vs additional distinction. |
| **Experiment 5** | V5 (Final ASAG) | 2,273 | 0.3444 | 0.3541 | 0.9220 | 1.2001 | Final Proposed Model. Added core recovery, non-sentential canonicalization, and contradiction guards. Highest correlation among semantic ASAG systems. |
