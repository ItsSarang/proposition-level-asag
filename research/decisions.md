# Research & Architectural Decisions Log

## Key Methodological Decisions

1. **Interpretability Over Black-Box Neural Models**:
   - *Decision*: Maintain explicit dependency parsing, proposition extraction, and rule-based scoring instead of fine-tuning end-to-end transformers (BERT/RoBERTa/LLMs).
   - *Rationale*: Educational grading systems require complete auditability and justifiable feedback for students and instructors.

2. **Decoupled Verification from Grading Classification**:
   - *Decision*: Separate epistemic fact-checking (is the statement true?) from the pedagogical grading policy (should credit be awarded?).
   - *Rationale*: A student asserting an unverified claim should be treated as `UNCERTAIN` rather than defaulted to `CORRECT_ADDITIONAL`.

3. **Core Paraphrase Recovery Before Unmatched Classification**:
   - *Decision*: Check whether an "unmatched" proposition actually paraphrases a missed reference concept before treating it as bonus additional information.
   - *Rationale*: Prevents verbosity inflation where student answers restating the answer in multiple ways receive artificial bonus points.

4. **Multiplicative Core Invalidation Discount (Model D / D2)**:
   - *Decision*: If a core defining contradiction is detected, multiply the base score by a discount factor (e.g. 0.50) rather than merely subtracting a flat penalty.
   - *Rationale*: A fundamental domain misconception invalidates understanding of the core concept.

5. **Final Proposed Model Designation**:
   - *Decision*: Designate V5 (Experiment 5 Model D2) as the final proposed model. Freeze all further experiments (no Experiment 6).
   - *Rationale*: V5 represents the culmination of all planned research phases, achieving the highest correlation among semantic/dependency systems on the 2,273 benchmark records.
