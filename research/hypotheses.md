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
  - On the frozen full active benchmark ($N=2,273$), V5 achieves Pearson r = 0.2428, Spearman rho = 0.2404, MAE = 3.4711, RMSE = 3.7637, consistently outperforming V1 Base ASAG (r = 0.1379, rho = 0.1181, MAE = 3.8050, RMSE = 4.0373).

### Hypothesis 4 (H4 — Superiority Over Lexical Baseline)
- **Statement**: Proposition-level semantic ASAG outperforms a simple TF-IDF cosine baseline on holistic human grade correlation.
- **Empirical Status**: **REFUTED / NOT SUPPORTED**.
  - TF-IDF (V0) remains stronger than the semantic/dependency models on the primary full active benchmark; see the frozen Experiment 5 results for the exact evaluation metrics.
  - While V5 is the strongest semantic/dependency ASAG model, TF-IDF (V0: Pearson r = 0.4184, Spearman rho = 0.4424) achieves higher correlation on holistic human grades due to human grading heuristics favoring exact topical vocabulary overlap over structural entailment.
