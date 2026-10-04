# Phase 4C: Pipeline Feature & Severity Signal Inventory

**Module:** `evaluation/severity_development/phase4c_feature_inventory.md`  
**Purpose:** Comprehensive inventory of all interpretable signals currently available within the ASAG research pipeline that can potentially inform contradiction severity estimation without relying on black-box neural models or large language models.

---

## 1. Architectural Principle: Separation of Contradiction from Severity

A foundational constraint in interpretable ASAG is that **contradiction detection must strictly precede severity estimation**:
$$\text{Linguistic Evidence} \longrightarrow \text{Contradiction Detection} \longrightarrow \text{Severity Estimation} \longrightarrow \text{Scoring}$$

- **Contradiction Detection:** Determines *epistemic conflict*: Does the student proposition directly contradict or invert verified factual knowledge or reference assertions?
- **Severity Estimation:** Determines *pedagogical magnitude*: Given that a factual contradiction exists, how severely does it undermine the student's mastery of the core concept being assessed?

Under no circumstances may severity signals (such as high lexical overlap with the question) be used to manufacture a contradiction where no factual incompatibility exists.

---

## 2. Inventory of Available Pipeline Signals

The following 10 feature signals are directly extracted or derived from existing components of the ASAG pipeline:

### Signal 1: `core_proposition_link`
- **Source:** Stage 5 (Dependency Triples), Stage 7 (Relational Matching), and `base_asag/representation/hybrid.py`.
- **Meaning:** Indicates whether the student's contradictory proposition directly aligns in syntactic/semantic slots (subject, predicate, or object) with a canonical proposition present in the reference answer.
- **Extraction Mechanism:** Lexical/lemma intersection and semantic similarity between the contradicted student triple $(s_{\text{stu}}, p_{\text{stu}}, o_{\text{stu}})$ and reference triples $(s_{\text{ref}}, p_{\text{ref}}, o_{\text{ref}})$.
- **Interpretability:** Highly interpretable. Directly traceable to reference sentence graph.
- **Potential Usefulness:** Contradictions that directly collide with a core reference proposition (e.g. asserting duplicate records when the reference asserts unique records) indicate a breakdown in the primary concept, rather than peripheral trivia.
- **Known Limitations:** If reference answer phrasing is fragmented or non-clausal (as seen in 40.7% of Mohler reference answers), relational alignment may fail to establish a direct link despite conceptual relevance.

---

### Signal 2: `defining_property_target`
- **Source:** `proposed_asag/contradiction/property_contradiction.py` (`INCOMPATIBLE_VALUE_SETS`).
- **Meaning:** Identifies whether the conflicting property detected by the contradiction engine targets the defining invariant of the domain entity.
  - *Primary Key:* Property `uniqueness` (defining invariant).
  - *Binary Search Tree:* Property `relative_size` / `sort_order` / `ordering` (defining invariant).
  - *Compiler:* Property `translation` / `execution_discipline` (defining invariant).
- **Extraction Mechanism:** Inspects `ContradictionEvidence.conflicting_property` against the curated property domain mapping.
- **Interpretability:** Extremely high. Grounded in explicit domain properties (e.g., student asserting *"duplicate"* vs reference *"unique"* targets `uniqueness`).
- **Potential Usefulness:** Provides the strongest deterministic signal for distinguishing `CORE_CONTRADICTION` from peripheral errors.
- **Known Limitations:** Restricted to properties explicitly modeled in the property contradiction lexicon. Unmodeled properties cannot trigger this signal.

---

### Signal 3: `contradiction_type`
- **Source:** `proposed_asag/contradiction/property_contradiction.py` (`ContradictionType`).
- **Meaning:** The formal linguistic mechanism through which the contradiction was established:
  - `EXPLICIT_NEGATION`: Direct polarity inversion on a shared predicate ($s \text{ does not } p \text{ vs } s \text{ } p$).
  - `VALUE_CONFLICT`: Incompatible property values from mutually exclusive sets (e.g., *unique* vs *duplicate*, *smaller* vs *larger*).
  - `ANTONYM_CONFLICT`: WordNet lexical antonyms operating on an aligned predicate slot.
- **Extraction Mechanism:** Direct enum value from `ContradictionEvidence.contradiction_type`.
- **Interpretability:** Fully deterministic and rule-governed.
- **Potential Usefulness:** Categorizes whether the contradiction is a direct structural denial (`EXPLICIT_NEGATION`), a semantic value inversion (`VALUE_CONFLICT`), or a lexical opposition (`ANTONYM_CONFLICT`).
- **Known Limitations:** Does not inherently measure severity by itself; an explicit negation of an incidental detail is minor, while explicit negation of the core verb is catastrophic. Must be combined with entity and predicate alignment.

---

### Signal 4: `contradiction_evidence_strength`
- **Source:** `ContradictionEvidence.evidence_strength` ($\in [0.0, 1.0]$).
- **Meaning:** Confidence score of the contradiction detection rule:
  - $0.90$: Direct mutually exclusive property value set match.
  - $0.85$: Strict polarity clash with matching subject and predicate lemmas.
  - $0.75$: Context-validated lexical antonymy.
- **Extraction Mechanism:** Float field from `ContradictionEvidence`.
- **Interpretability:** Transparent rule-assigned confidence.
- **Potential Usefulness:** Distinguishes high-certainty property inversions from softer lexical oppositions.
- **Known Limitations:** **Evidence confidence is NOT conceptual severity.** A detector can be 100% confident that a student made a minor naming error ($0.90$ strength), while being slightly less certain about a convoluted core error. Strength measures detection certainty, not severity of impact.

---

### Signal 5: `entity_concept_grounding`
- **Source:** Stage 3 (Linguistic Preprocessing), Stage 4 (Dependency Parser), and `proposed_asag/evidence/domain_knowledge.py`.
- **Meaning:** Verifies whether the contradictory statement is explicitly predicated of the *target entity under evaluation*, rather than an adjacent, related, or confused entity.
- **Extraction Mechanism:** Checks subject lemma and noun-chunk modifier chains against canonical entity sets (e.g., distinguishing `binary search tree` from `general binary tree`, `primary key` from `foreign key`, and `compiler` from `interpreter`).
- **Interpretability:** High. Based on exact lemma and dependency parse modifier inspection (`amod`, `compound`).
- **Potential Usefulness:** Prevents false severity escalation caused by entity confusion (e.g., asserting that duplicate values are allowed in a *foreign key* is true, and must not be marked as a core contradiction of a *primary key*).
- **Known Limitations:** In pronominal or elided sentences (e.g., *"It can contain duplicate values"*), coreference resolution must trace back to the preceding sentence subject.

---

### Signal 6: `question_topical_centrality`
- **Source:** `proposed_asag/relevance/question_relevance.py` (`QuestionAwareRelevanceAnalyzer`).
- **Meaning:** Measures the semantic and lexical centrality of the contradictory proposition to the interrogative focus of the question.
- **Extraction Mechanism:** Synset depth, question term overlap, and focus noun overlap with the question prompt.
- **Interpretability:** Transparent set overlap and synset matching.
- **Potential Usefulness:** Distinguishes statements addressing the primary question objective from tangential remarks.
- **Known Limitations:** **Relevance is not truth or severity.** A completely wrong statement can have 100% topical relevance to the question. Relevance indicates *topical focus*, which can only modulate severity *after* a contradiction is independently verified.

---

### Signal 7: `reference_coverage_weight`
- **Source:** Stage 9 (Base ASAG Scoring) and `BaseASAGPipelineResult.scoring_result`.
- **Meaning:** Indicates how much weight the target reference proposition carries in the total reference coverage formula:
  $$w_{\text{ref}} = \frac{1}{|P_{\text{ref}}|}$$
- **Extraction Mechanism:** Reciprocal of total reference proposition count.
- **Interpretability:** Fully mathematical and transparent.
- **Potential Usefulness:** In multi-proposition reference answers, contradictions of heavily weighted or solitary defining propositions carry higher diagnostic significance than contradictions of secondary auxiliary clauses.
- **Known Limitations:** Does not distinguish whether a reference proposition is a primary definition or an illustrative example if all reference propositions are uniformly weighted.

---

### Signal 8: `argument_displacement_depth`
- **Source:** Stage 5 (Dependency Triples) and Stage 12 (Proposition Representation).
- **Meaning:** Identifies whether the conflicting element appears in the core predicate/object slot, or inside a secondary prepositional phrase, adverbial clause, or parenthetical modifier.
- **Extraction Mechanism:** Inspects whether the conflict token occurs in `token_indices[:3]` (core triple) or in `prepositional_arguments` / `predicate_modifiers`.
- **Interpretability:** High syntactic transparency.
- **Potential Usefulness:** Peripheral errors frequently occur in subordinate clauses or prepositional attachments, while core contradictions typically invert root predicates or primary direct objects.
- **Known Limitations:** German-style or complex English relative clauses can place defining criteria inside restrictive relative clauses (e.g., *"a key that uniquely identifies"*).

---

### Signal 9: `domain_knowledge_invalidation`
- **Source:** `proposed_asag/evidence/evidence_verifier.py` (`PropositionEvidenceVerifier`).
- **Meaning:** Indicates whether the student proposition directly refutes an authoritative domain knowledge rule (e.g. `PK_NOT_NULL`, `BST_INORDER_SORTED`, `COMPILER_INTERMEDIATE_REP`).
- **Extraction Mechanism:** Polarity conflict detection against domain rule objects and actions.
- **Interpretability:** Grounded in peer-reviewed textbooks and formal specifications.
- **Potential Usefulness:** When an authoritative domain rule is directly negated, epistemic justification for high severity is ironclad.
- **Known Limitations:** Only applicable when the concept falls within the scope of curated domain rules.

---

### Signal 10: `modality_and_hedging`
- **Source:** `base_asag/representation/hybrid.py` (`RobustProposition.modality`).
- **Meaning:** Captures epistemic hedging: `ASSERTED` (factual certainty), `POSSIBLE` (e.g., *"can"*, *"may"*), `NECESSARY` (e.g., *"must"*, *"always"*), or `UNCERTAIN` (e.g., *"might"*).
- **Extraction Mechanism:** Auxiliary verb analysis (`can`, `could`, `may`, `might`, `must`, `should`, `always`).
- **Interpretability:** High grammatical transparency.
- **Potential Usefulness:** An incorrect universal assertion (*"A primary key is always named ID"*) indicates a misconception, whereas a hedged statement (*"A primary key might sometimes be an integer"*) is softer.
- **Known Limitations:** Many students write colloquially without precise modal qualifiers, making modality noisy if used as a primary severity driver.

---

## 3. Signal Evaluation Summary Matrix

| Signal Name | Source Module | Primary Function | Robustness | Risk of Spurious Severity |
| :--- | :--- | :--- | :---: | :---: |
| **`core_proposition_link`** | Matching & Hybrid Rep | Link conflict to reference | High | Low |
| **`defining_property_target`** | Property Contradiction | Detect defining invariant inversion | Very High | Very Low |
| **`contradiction_type`** | Property Contradiction | Structural contradiction form | High | Low (if paired with link) |
| **`contradiction_evidence_strength`** | Property Contradiction | Detection certainty score | High | **High** (if used alone) |
| **`entity_concept_grounding`** | Parser & Domain Lexicon | Verify target entity ownership | High | Very Low |
| **`question_topical_centrality`** | Question Relevance | Measure topical focus | High | **High** (if used alone) |
| **`reference_coverage_weight`** | Base Scoring | Coverage impact of ref prop | High | Low |
| **`argument_displacement_depth`** | Hybrid Representation | Syntactic core vs modifier | Moderate | Moderate |
| **`domain_knowledge_invalidation`** | Evidence Verifier | Invalidation of curated rules | Very High | Very Low |
| **`modality_and_hedging`** | Hybrid Representation | Epistemic certainty markers | Moderate | High |

---

## 4. Key Architectural Takeaways for Phase 4C

1. **Topical Relevance and Detection Confidence Must Never Drive Severity in Isolation:**  
   High question relevance merely confirms that the student is talking about the question topic; high evidence strength merely confirms that the detector is confident. Neither proves that the error is conceptually catastrophic.
2. **The Backbone of Core Contradiction is Entity Grounding + Defining Property Target:**  
   A `CORE_CONTRADICTION` is justified when:
   $$\text{entity\_grounded} \land (\text{defining\_property\_target} \lor (\text{core\_proposition\_link} \land \text{core\_predicate\_negated}))$$
3. **Minor Errors Typically Target Secondary Properties or Syntactic Periphery:**  
   Misconceptions regarding naming conventions, file formats, or peripheral counts that do not invert the core invariant should map to `MINOR`.
4. **Entity Mismatches Must Abort Severity Escalation:**  
   If the student makes a false claim about an adjacent entity (e.g. *foreign key*), it must not be treated as a core contradiction of the *primary key*.
