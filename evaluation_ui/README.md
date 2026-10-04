# ASAG Evaluation Lab — Research & Viva Demonstration Interface

## 1. Overview & Research Purpose

The **ASAG Evaluation Lab** is a lightweight, Flask-based research interface designed for the undergraduate NLP research project:
> **"Automatic Short Answer Grading using Semantic and Dependency Analysis"**

This application is **NOT** a production web service or commercial dashboard. It is a dedicated research laboratory and demonstration tool designed to:
1. Interactively evaluate and compare multiple student responses against an instructor reference answer;
2. Observe differences between four ASAG paradigms (V0 TF-IDF, V1 Base ASAG, V2 Historical Proposed, and V3 Current Overhauled Proposed);
3. Inspect fine-grained, interpretable proposition-level evidence traces;
4. Run batch CSV evaluations on benchmark datasets and calculate agreement metrics (MAE, RMSE, Pearson $r$, Spearman $\rho$, QWK);
5. Provide an auditable viva and defense interface for examiners and researchers.

---

## 2. Research Integrity Mandates

- **Zero LLM Prompting:** Graders use deterministic, interpretable NLP components (syntactic dependency parsing, WordNet, Hungarian matching, domain lexicons).
- **Control Condition Preservation:** Base ASAG (V1) is preserved unchanged as the control condition.
- **No Parameter Tuning from Demos:** Scoring parameters are never modified to satisfy interactive test cases.
- **Strict Blinded Validation:** The human validation page displays a formal placeholder acknowledging that real human annotations remain `PENDING_HUMAN_ANNOTATIONS`. Zero synthetic human labels are fabricated.
- **Error Transparency:** If an engine encounters an issue, it explicitly outputs `ERROR` with the exact diagnostic reason rather than silently inventing grades.

---

## 3. Four Systems Under Comparison

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                             STUDENT RESPONSE                                │
└──────────────────────┬────────────────────────────────┬─────────────────────┘
                       │                                │
                       ▼                                ▼
         ┌───────────────────────────┐    ┌───────────────────────────┐
         │       V0: BASELINE        │    │       V1: BASE ASAG       │
         │  TF-IDF + Cosine Sim      │    │  Basak Clausal Coverage   │
         │  (Bag-of-Words Overlap)   │    │  (Unmatched Ignored: +0)  │
         └─────────────┬─────────────┘    └─────────────┬─────────────┘
                       │                                │
                       ▼                                ▼
         ┌───────────────────────────┐    ┌───────────────────────────┐
         │ V2: HISTORICAL PROPOSED   │    │   V3: CURRENT OVERHAULED  │
         │ Stage 14 Additive Linear  │    │  Hybrid + Hungarian +     │
         │ (Base + 0.10*C - 0.20*I)  │    │  Relevance + Bounded Sat  │
         └───────────────────────────┘    └───────────────────────────┘
```

1. **V0 — TF-IDF Baseline:**
   - Vectorizes texts using TF-IDF and computes cosine similarity.
   - Ignores grammatical structure, negation, and proposition boundaries.
2. **V1 — Base ASAG:**
   - Simplified Basak-inspired pipeline extracting clausal Subject-Predicate-Object triples.
   - Evaluates reference proposition coverage using WordNet path similarity and greedy alignment.
   - Ignores all unmatched student information ($+0.00$).
3. **V2 — Historical Proposed ASAG:**
   - Stage 14 additive scoring extension over Base ASAG.
   - Evaluates unmatched student propositions and applies linear bonuses/penalties: $\text{Base} + (0.10 \times N_{\text{correct}}) - (0.20 \times N_{\text{incorrect}})$.
4. **V3 — Current Overhauled Proposed ASAG:**
   - Hybrid proposition representation (clausal + nominal fragments + infinitives).
   - Multi-tier Semantic Matcher V2 (morphological derivation + 13 curated CS domain equivalences).
   - Global Hungarian bipartite alignment.
   - Question-aware relevance filtering and property contradiction detection.
   - Bounded horizontal-asymptote scoring ($B_{\max} = 0.30$, diminishing rate $r = 0.50$), cutting verbosity bias by 50%.

---

## 4. How to Launch the Evaluation Lab

### Prerequisites
Activate the virtual environment with dependencies installed:
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### Running the Application
From the repository root:
```bash
PYTHONPATH=. .venv/bin/python3 evaluation_ui/app.py
```
Or specify a custom port:
```bash
PORT=5000 PYTHONPATH=. .venv/bin/python3 evaluation_ui/app.py
```

Open your browser to:
**http://127.0.0.1:5000**

---

## 5. Demonstration Walkthrough & Examples

### Example A: The Canonical Primary Key Demonstration
Click the preset button **"Primary Key Purpose (GEMINI.md Motivation)"** on the main page:
- **Question:** `What is the purpose of a primary key?`
- **Reference Answer:** `A primary key uniquely identifies each record in a table.`
- **Student 1 (Paraphrase):** `A primary key uniquely identifies every row in a table.`
  - *Observation:* V1 matches via domain equivalence (`record` $\leftrightarrow$ `row`). Awarded full mark (5.0).
- **Student 2 (Correct Additional):** `A primary key uniquely identifies each record in a table and cannot contain NULL values.`
  - *Observation:* V1 awards core coverage (5.0). V3 isolates `"cannot contain NULL values"`, classifies as `CORRECT_ADDITIONAL`, and demonstrates bounded adjustment.
- **Student 3 (Incorrect Additional):** `A primary key uniquely identifies each record in a table and can contain duplicate values.`
  - *Observation:* V1 awards 5.0 (blind to the contradiction). V3 detects `INCORRECT` property conflict and applies penalization.
- **Student 4 (Irrelevant Tangent):** `A primary key uniquely identifies each record in a table. SQL was developed in the 1970s.`
  - *Observation:* V3 identifies `"SQL was developed in the 1970s"` as `IRRELEVANT` (relevance strength $< 0.35$) and assigns strictly $+0.00$.

---

## 6. Batch Experiment Mode (`/experiment`)

1. Navigate to `http://127.0.0.1:5000/experiment`.
2. Upload any benchmark CSV containing:
   - `question_id`, `question`, `reference_answer`, `student_answer`
   - *(Optional)* `human_grade`
3. If `human_grade` is provided, the lab computes:
   - Mean Absolute Error (MAE)
   - Root Mean Squared Error (RMSE)
   - Pearson correlation ($r$)
   - Spearman rank correlation ($\rho$)
   - Quadratic Weighted Kappa (QWK)
4. Use **Diagnostic Error Sorting** to sort answers by largest absolute error, largest underprediction, or largest overprediction.
5. Export full predictions via **Download Predictions CSV**.

---

## 7. Architecture & Service Boundaries

```
evaluation_ui/
├── app.py                     # Flask route handlers & application factory
├── services/
│   ├── evaluator.py           # Multi-engine coordinator & trace extractor
│   └── comparison.py          # Batch CSV processor, metric runner, error sorter
├── templates/
│   ├── base.html              # Dark research theme layout
│   ├── index.html             # Multi-answer quick comparison input
│   ├── results.html           # Comparative overview table
│   ├── detail.html            # Proposition & 11-stage pipeline traces
│   ├── experiment.html        # Batch experiment & diagnostic error view
│   ├── validation.html        # Double-blind human annotation protocol
│   └── documentation.html     # Mathematical formulas & research boundaries
├── static/
│   ├── style.css              # Custom research laboratory stylesheet
│   └── app.js                 # Dynamic answer manipulation scripts
└── README.md                  # This file
```

All research logic remains strictly within `baseline/`, `base_asag/`, `proposed_asag/`, and `evaluation/`. The UI contains zero grading heuristics.
