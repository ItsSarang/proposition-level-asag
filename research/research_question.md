# Research Question

## Primary Research Question

"Can an interpretable proposition-level extension of a classical semantic/dependency-based ASAG system evaluate unmatched student information as correct additional, irrelevant, or incorrect information, and does incorporating this evaluation improve agreement with human grading?"

## Epistemic Status
- This formulation originated as a formal research hypothesis.
- Across extensive empirical evaluation on the 2,273 active student answers in the Mohler ASAG benchmark (81 active computer science questions across 10 assignments), the answer is nuanced:
  1. Proposition-level extraction, alignment, and classification of unmatched student information is technically feasible and highly interpretable.
  2. Incorporating unmatched-information evaluation improves absolute error metrics over Base ASAG (MAE improved from 3.8050 for V1 to 3.4711 for V5; RMSE improved from 4.0373 to 3.7637).
  3. However, rank correlation against holistic human grades shows that TF-IDF (V0) remains stronger than the semantic/dependency models on the primary full active benchmark; see the frozen Experiment 5 results for the exact evaluation metrics.

## Research Sub-Questions
1. **Extraction & Classification**: Can unmatched student propositions be accurately classified into four categories:
   - `CORRECT_ADDITIONAL`
   - `IRRELEVANT`
   - `INCORRECT`
   - `UNCERTAIN`
2. **Scoring Integration**: Can an interpretable, bounded scoring function integrate these proposition categories without destroying reference answer coverage or inflating grades on non-answers?
3. **Core Recovery**: When reference answers are nominal fragments or students paraphrase core concepts using different syntactic structures, can core proposition alignment be recovered before classifying information as "unmatched"?
