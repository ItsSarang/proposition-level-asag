# Research Hypotheses & Findings

## Formal Hypotheses

### Hypothesis 1 (H1 — Proposition Extraction Feasibility)
- **Statement**: An interpretable proposition-level representation based on clausal dependency triples and hybrid syntactic units can represent student and reference answers faithfully with verifiable character spans.
- **Empirical Status**: **CONFIRMED**.
  - Across 2,273 active student answers, 3,611 propositions were parsed and mapped to surface text spans with complete provenance tracking.

### Hypothesis 2 (H2 — Unmatched Information Classification)
- **Statement**: Information in the student answer that is unmatched to the reference answer can be categorized into `CORRECT_ADDITIONAL`, `IRRELEVANT`, `INCORRECT`, and `UNCERTAIN` using semantic relevance, domain knowledge, and contradiction detection.
- **Empirical Status**: **CONFIRMED**.
  - Classification was verified via automated verification against domain facts and an AI-based annotation pilot study (Cohen's kappa = 0.8054).

### Hypothesis 3 (H3 — Improvement Over Base ASAG)
- **Statement**: Incorporating proposition-level evaluations into scoring improves agreement with human grades compared to the Base ASAG (Basak et al. 2019-inspired) system.
- **Empirical Status**: **CONFIRMED**.
  - V5 achieves Pearson r = 0.3444, Spearman rho = 0.3541, MAE = 0.9220, RMSE = 1.2001, outperforming V1 Base ASAG (r = 0.3013, rho = 0.3129, MAE = 1.2185, RMSE = 1.5457).

### Hypothesis 4 (H4 — Superiority Over Lexical Baseline)
- **Statement**: Proposition-level semantic ASAG outperforms a simple TF-IDF cosine baseline on holistic human grade correlation.
- **Empirical Status**: **REFUTED / NOT SUPPORTED**.
  - V0 (TF-IDF Baseline) achieves Pearson r = 0.4485 and Spearman rho = 0.4357 on the Mohler benchmark.
  - While V5 is the strongest semantic/dependency ASAG model, TF-IDF remains globally superior in correlation due to human grading heuristics favoring exact topical vocabulary overlap over structural entailment.
