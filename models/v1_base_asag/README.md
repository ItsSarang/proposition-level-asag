# V1 — Base ASAG

## Identity
- **Version:** V1
- **Name:** Base ASAG (Basak et al. 2019-inspired)
- **Role:** Classical semantic/dependency clausal ASAG pipeline

## Methodology Note
This implementation is inspired by the methodology of Basak et al. (2019). We do NOT claim exact reproduction of all parameters or environments from the paper.

## Components
- Linguistic Preprocessing (spaCy lemmatization, tokenization)
- Clausal SPO Dependency Triple Extraction
- WordNet Path Similarity & Exact/Lemma Slot Matching
- Direct Slot Triple Alignment
- Propositional Polarity & Entailment
- Reference-Proportional Rule-Based Scoring

## Research Status
**FROZEN.** Evaluated on Mohler benchmark (Pearson $r = 0.1379$, Spearman $ho = 0.1181$, MAE $= 3.8050$).
