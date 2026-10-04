# Proposition-Level Annotation Protocol

## Objective
Validate the proposition-level classification taxonomy (`CORRECT_ADDITIONAL`, `IRRELEVANT`, `INCORRECT`, `UNCERTAIN`) on unmatched student propositions extracted by the ASAG engine.

## Taxonomy Definitions

### 1. Core Paraphrase vs. Additional Information
- **SYSTEM UNMATCHED ≠ HUMAN ADDITIONAL**: A proposition that simply rephrases information already contained in the reference answer is CORE information, not genuinely additional information.
- If the ASAG system fails to align a student proposition because of syntactic divergence, but human readers recognize it as expressing the essential reference concept, it is a **Core Paraphrase**.

### 2. CORRECT_ADDITIONAL
- The proposition provides information that:
  1. Goes beyond the reference answer.
  2. Is technically true and valid within the domain (Computer Science).
  3. Is relevant to the question topic.

### 3. IRRELEVANT
- The proposition is off-topic, conversational filler, or discusses unrelated facts (e.g., historical trivia about SQL creation date when asked about primary keys).

### 4. INCORRECT
- The proposition contains a factual error, domain misconception, or directly contradicts established computer science principles (e.g., asserting that primary keys can contain duplicate values).

### 5. UNCERTAIN
- The proposition cannot be conclusively verified as true or false within the provided domain context, or is ambiguous.

## Annotation Pilot Results
- Evaluated on a 50-item stratified sample.
- Raw agreement: 88.0%
- Cohen's kappa: 0.8054
- Core paraphrases identified: 22/50 items (motivating the Phase 9 / Experiment 5 Core Recovery component).
