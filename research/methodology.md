# ASAG Research Methodology

## Overview
This project investigates automated short answer grading through an interpretable, multi-stage semantic and dependency parsing framework. Rather than employing black-box deep learning models, the system constructs explicit propositional representations and audits every score adjustment.

## Pipeline Evolution

### 1. V0 — TF-IDF Baseline
- Unigram TF-IDF vectorization with cosine similarity.
- Provides a fast, bag-of-words lexical comparison baseline.

### 2. V1 — Base ASAG (Basak et al. 2019-inspired)
- Preprocessing: spaCy tokenization, lemmatization, POS tagging.
- Dependency extraction: Subject-Predicate-Object triples.
- Lexical-semantic comparison: 4-tier hierarchy (Exact -> Lemma -> POS compatibility -> WordNet path similarity).
- Propositional entailment: Polarity check resulting in ENTAILS (1.0), UNCERTAIN (0.5), CONTRADICTS (0.0).
- Scoring: Strict reference proposition coverage. Discards unmatched student information.

### 3. V2 — Proposition-Level ASAG (Stages 11–14)
- Identifies unmatched student propositions with character span provenance.
- Classifies unmatched information into 4 categories: `CORRECT_ADDITIONAL`, `IRRELEVANT`, `INCORRECT`, `UNCERTAIN`.
- Additive linear modulation: adds bonus (+0.10) for correct additional info and penalty (-0.20) for incorrect info.

### 4. V3 — Enhanced Proposition-Level ASAG (System 4 Overhaul)
- Hybrid proposition extraction handling non-clausal and non-finite constructions.
- Global bipartite matching using the Hungarian algorithm.
- Question-aware relevance filtering and bounded horizontal-asymptote scoring.

### 5. V4 — Severity-Aware Proposition ASAG (Experiment 4)
- Model D scoring: Distinguishes core invalidations from minor inaccuracies.
- Core invalidation applies a multiplicative discount to the base score.
- Gated bonus ensures additional information cannot award credit if core propositions are contradictory.

### 6. V5 — Final Proposition-Level ASAG (Experiment 5)
- Core paraphrase recovery: Recovers student propositions that paraphrase the reference answer despite structural divergence.
- Non-sentential reference canonicalization: Synthesizes virtual propositions for nominal/fragment references.
- Contradiction guards: Prevents false positive contradictions caused by negation scope or lexicon gaps.
- Model D2 scoring: Refined severity and confidence weighting.
