# Research Question

## Primary Research Question

"Can an interpretable proposition-level extension of a classical semantic/dependency-based ASAG system evaluate unmatched student information as correct additional, irrelevant, or incorrect information, and does incorporating this evaluation improve agreement with human grading?"

## Epistemic Status
- This formulation originated as a formal research hypothesis.
- Across extensive empirical evaluation on the 2,273 active student answers in the Mohler ASAG benchmark (81 active computer science questions across 10 assignments), the answer is nuanced:
  1. Proposition-level extraction, alignment, and classification of unmatched student information is technically feasible and highly interpretable.
  2. Incorporating unmatched-information evaluation improves absolute error metrics (MAE improved from 1.2185 to 0.9220; RMSE improved from 1.5457 to 1.2001).
  3. However, rank correlation against holistic human grades slightly degrades or remains bounded (Pearson r = 0.3444 for V5 vs 0.4485 for TF-IDF baseline) due to human grading penalizing verbosity/fluff while semantic models reward correct domain details.

## Research Sub-Questions
1. **Extraction & Classification**: Can unmatched student propositions be accurately classified into four categories:
   - `CORRECT_ADDITIONAL`
   - `IRRELEVANT`
   - `INCORRECT`
   - `UNCERTAIN`
2. **Scoring Integration**: Can an interpretable, bounded scoring function integrate these proposition categories without destroying reference answer coverage or inflating grades on non-answers?
3. **Core Recovery**: When reference answers are nominal fragments or students paraphrase core concepts using different syntactic structures, can core proposition alignment be recovered before classifying information as "unmatched"?
