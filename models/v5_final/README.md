# V5 — Final Proposition-Level ASAG

## Identity
- **Version:** V5
- **Name:** Final Proposition-Level ASAG (Experiment 5)
- **Role:** Official final proposed ASAG system

## Components
- Core Paraphrase Recovery (`CoreParaphraseRecoverer`)
- Non-Sentential Reference Canonicalization (`CanonicalReferenceExtractor`)
- Contradiction Guard Pipeline (4 structural guards)
- Evidence-Grounded Unmatched Proposition Classification
- Model D2 Soft-Gated Severity-Aware Scorer ($	au_{	ext{gate}} = 0.30$, $\gamma = 0.25$)

## Benchmark Performance ($N=2,273$)
- **Pearson $r$:** $0.2428$ ($+18.2\%$ over V4)
- **Spearman $ho$:** $0.2404$ ($+18.2\%$ over V4)
- **Sentential Subset $ho$:** $0.2590$ ($+34.6\%$ over V4, exceeds Base ASAG $0.1968$)
- **Non-Sentential Subset $r$:** $0.2525$ (Base ASAG failed completely with 100% zeros)
- **MAE:** $3.4711$

## Research Status
**FROZEN.** Official final model of this research project.
