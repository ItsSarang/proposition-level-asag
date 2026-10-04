"""
Phase 4C Controlled Severity Evaluation & Ablation Runner.

Executes 51 controlled development cases across Primary Key, Binary Search Tree,
and Compiler domains (including adversarial/entity-confusion cases) against
the Interpretable Severity Estimator and 5 ablation variants.

Exports:
- phase4c_controlled_cases.csv
- phase4c_severity_results.csv
- phase4c_ablation_results.csv
- phase4c_score_traces.json
"""

from __future__ import annotations

import csv
import json
import os
from typing import Any, Dict, List, Optional, Tuple

from base_asag.representation.hybrid import Modality, Polarity, PropositionType, RobustProposition
from evaluation.severity_development.phase4c_severity_estimator import (
    InterpretableSeverityEstimator,
    SeverityLevel,
)
from proposed_asag.contradiction.property_contradiction import (
    ContradictionEvidence,
    ContradictionType,
    PropertyContradictionDetector,
)


def get_phase4c_controlled_dataset() -> List[Dict[str, Any]]:
    """Return 51 systematically designed controlled development cases."""
    cases: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------------
    # 1. PRIMARY KEY DOMAIN (17 cases: 5 Core, 5 Moderate, 5 Minor, 2 Adv)
    # ------------------------------------------------------------------------
    pk_ref = "A primary key uniquely identifies each record in a table."
    pk_q = "What is the purpose of a primary key?"

    # Core Contradictions (5)
    cases.append({
        "case_id": "PK-CORE-01",
        "domain": "PRIMARY_KEY",
        "question": pk_q,
        "reference_answer": pk_ref,
        "student_proposition": "A primary key can contain duplicate values.",
        "controlled_severity": "CORE_CONTRADICTION",
        "contradiction_type": "VALUE_CONFLICT",
        "conflicting_property": "uniqueness",
        "evidence_strength": 0.90,
        "category_rationale": "Direct contradiction of fundamental uniqueness property.",
    })
    cases.append({
        "case_id": "PK-CORE-02",
        "domain": "PRIMARY_KEY",
        "question": pk_q,
        "reference_answer": pk_ref,
        "student_proposition": "A primary key contains redundant rows.",
        "controlled_severity": "CORE_CONTRADICTION",
        "contradiction_type": "VALUE_CONFLICT",
        "conflicting_property": "uniqueness",
        "evidence_strength": 0.90,
        "category_rationale": "Asserts redundant rows, directly violating row uniqueness.",
    })
    cases.append({
        "case_id": "PK-CORE-03",
        "domain": "PRIMARY_KEY",
        "question": pk_q,
        "reference_answer": pk_ref,
        "student_proposition": "A primary key does not uniquely identify records.",
        "controlled_severity": "CORE_CONTRADICTION",
        "contradiction_type": "EXPLICIT_NEGATION",
        "conflicting_property": "uniquely",
        "evidence_strength": 0.85,
        "category_rationale": "Explicit negation of the core defining predicate.",
    })
    cases.append({
        "case_id": "PK-CORE-04",
        "domain": "PRIMARY_KEY",
        "question": pk_q,
        "reference_answer": pk_ref,
        "student_proposition": "A primary key permits identical entries for multiple records.",
        "controlled_severity": "CORE_CONTRADICTION",
        "contradiction_type": "VALUE_CONFLICT",
        "conflicting_property": "uniqueness",
        "evidence_strength": 0.90,
        "category_rationale": "Direct value conflict on uniqueness via identical entries.",
    })
    cases.append({
        "case_id": "PK-CORE-05",
        "domain": "PRIMARY_KEY",
        "question": pk_q,
        "reference_answer": pk_ref,
        "student_proposition": "A primary key can contain NULL values.",
        "controlled_severity": "CORE_CONTRADICTION",
        "contradiction_type": "VALUE_CONFLICT",
        "conflicting_property": "nullability",
        "evidence_strength": 0.90,
        "category_rationale": "Direct violation of the relational entity integrity nullability invariant.",
    })

    # Moderate Errors (5)
    cases.append({
        "case_id": "PK-MOD-01",
        "domain": "PRIMARY_KEY",
        "question": pk_q,
        "reference_answer": pk_ref,
        "student_proposition": "A primary key must always be an integer data type.",
        "controlled_severity": "MODERATE",
        "contradiction_type": "VALUE_CONFLICT",
        "conflicting_property": "data_type_restriction",
        "evidence_strength": 0.70,
        "category_rationale": "Data type restriction misconception; does not negate record uniqueness.",
    })
    cases.append({
        "case_id": "PK-MOD-02",
        "domain": "PRIMARY_KEY",
        "question": pk_q,
        "reference_answer": pk_ref,
        "student_proposition": "A primary key cannot consist of multiple composite columns.",
        "controlled_severity": "MODERATE",
        "contradiction_type": "EXPLICIT_NEGATION",
        "conflicting_property": "composite",
        "evidence_strength": 0.75,
        "category_rationale": "Denies composite primary key capability; notable relational misconception.",
    })
    cases.append({
        "case_id": "PK-MOD-03",
        "domain": "PRIMARY_KEY",
        "question": pk_q,
        "reference_answer": pk_ref,
        "student_proposition": "A primary key must be defined as an auto-increment column.",
        "controlled_severity": "MODERATE",
        "contradiction_type": "VALUE_CONFLICT",
        "conflicting_property": "auto-increment",
        "evidence_strength": 0.70,
        "category_rationale": "Confuses implementation generation mechanism with definition.",
    })
    cases.append({
        "case_id": "PK-MOD-04",
        "domain": "PRIMARY_KEY",
        "question": pk_q,
        "reference_answer": pk_ref,
        "student_proposition": "A table can define multiple primary keys simultaneously.",
        "controlled_severity": "MODERATE",
        "contradiction_type": "VALUE_CONFLICT",
        "conflicting_property": "multiple primary keys",
        "evidence_strength": 0.75,
        "category_rationale": "Relational model misconception regarding single PK per relation.",
    })
    cases.append({
        "case_id": "PK-MOD-05",
        "domain": "PRIMARY_KEY",
        "question": pk_q,
        "reference_answer": pk_ref,
        "student_proposition": "A primary key is destroyed when a table row is updated.",
        "controlled_severity": "MODERATE",
        "contradiction_type": "VALUE_CONFLICT",
        "conflicting_property": "lifecycle",
        "evidence_strength": 0.70,
        "category_rationale": "Row update lifecycle confusion without negating uniqueness.",
    })

    # Minor Errors (5)
    cases.append({
        "case_id": "PK-MIN-01",
        "domain": "PRIMARY_KEY",
        "question": pk_q,
        "reference_answer": pk_ref,
        "student_proposition": "A primary key is always named ID in database schemas.",
        "controlled_severity": "MINOR",
        "contradiction_type": "VALUE_CONFLICT",
        "conflicting_property": "naming",
        "evidence_strength": 0.65,
        "category_rationale": "Peripheral naming convention error.",
    })
    cases.append({
        "case_id": "PK-MIN-02",
        "domain": "PRIMARY_KEY",
        "question": pk_q,
        "reference_answer": pk_ref,
        "student_proposition": "A primary key must be defined as the very first column in a table.",
        "controlled_severity": "MINOR",
        "contradiction_type": "VALUE_CONFLICT",
        "conflicting_property": "first column",
        "evidence_strength": 0.65,
        "category_rationale": "Schema layout styling misconception.",
    })
    cases.append({
        "case_id": "PK-MIN-03",
        "domain": "PRIMARY_KEY",
        "question": pk_q,
        "reference_answer": pk_ref,
        "student_proposition": "A primary key column must be written in uppercase syntax.",
        "controlled_severity": "MINOR",
        "contradiction_type": "VALUE_CONFLICT",
        "conflicting_property": "syntax style",
        "evidence_strength": 0.60,
        "category_rationale": "SQL syntax formatting convention error.",
    })
    cases.append({
        "case_id": "PK-MIN-04",
        "domain": "PRIMARY_KEY",
        "question": pk_q,
        "reference_answer": pk_ref,
        "student_proposition": "A primary key was invented by IBM in the year 1999.",
        "controlled_severity": "MINOR",
        "contradiction_type": "VALUE_CONFLICT",
        "conflicting_property": "date",
        "evidence_strength": 0.60,
        "category_rationale": "Historical trivia error (relational model published in 1970).",
    })
    cases.append({
        "case_id": "PK-MIN-05",
        "domain": "PRIMARY_KEY",
        "question": pk_q,
        "reference_answer": pk_ref,
        "student_proposition": "A primary key requires exactly 8 bytes of storage on disk.",
        "controlled_severity": "MINOR",
        "contradiction_type": "VALUE_CONFLICT",
        "conflicting_property": "bytes",
        "evidence_strength": 0.60,
        "category_rationale": "Low-level implementation storage size trivia error.",
    })

    # Adversarial / Near-Miss Cases (2)
    cases.append({
        "case_id": "PK-ADV-01",
        "domain": "PRIMARY_KEY",
        "question": pk_q,
        "reference_answer": pk_ref,
        "student_proposition": "A foreign key can contain duplicate values.",
        "controlled_severity": "UNRESOLVED",
        "contradiction_type": "VALUE_CONFLICT",
        "conflicting_property": "uniqueness",
        "evidence_strength": 0.90,
        "category_rationale": "Entity confusion: statement about foreign key, not a PK contradiction.",
    })
    cases.append({
        "case_id": "PK-ADV-02",
        "domain": "PRIMARY_KEY",
        "question": pk_q,
        "reference_answer": pk_ref,
        "student_proposition": "A primary key is usually placed early in a table schema.",
        "controlled_severity": "NONE",
        "contradiction_type": "NONE",
        "conflicting_property": None,
        "evidence_strength": 0.0,
        "category_rationale": "Hedged stylistic remark; non-contradictory statement.",
    })

    # ------------------------------------------------------------------------
    # 2. BINARY SEARCH TREE DOMAIN (17 cases: 5 Core, 5 Moderate, 5 Minor, 2 Adv)
    # ------------------------------------------------------------------------
    bst_ref = "A binary search tree stores smaller values in the left subtree."
    bst_q = "What is a binary search tree?"

    # Core Contradictions (5)
    cases.append({
        "case_id": "BST-CORE-01",
        "domain": "BST",
        "question": bst_q,
        "reference_answer": bst_ref,
        "student_proposition": "A binary search tree places larger values in the left subtree.",
        "controlled_severity": "CORE_CONTRADICTION",
        "contradiction_type": "VALUE_CONFLICT",
        "conflicting_property": "relative_size",
        "evidence_strength": 0.90,
        "category_rationale": "Direct value conflict on relative size: smaller vs larger in left subtree.",
    })
    cases.append({
        "case_id": "BST-CORE-02",
        "domain": "BST",
        "question": bst_q,
        "reference_answer": bst_ref,
        "student_proposition": "A binary search tree stores smaller values in the right subtree.",
        "controlled_severity": "CORE_CONTRADICTION",
        "contradiction_type": "VALUE_CONFLICT",
        "conflicting_property": "ordering",
        "evidence_strength": 0.90,
        "category_rationale": "Direct reversal of the defining BST invariant.",
    })
    cases.append({
        "case_id": "BST-CORE-03",
        "domain": "BST",
        "question": bst_q,
        "reference_answer": bst_ref,
        "student_proposition": "A binary search tree does not store smaller values in the left subtree.",
        "controlled_severity": "CORE_CONTRADICTION",
        "contradiction_type": "EXPLICIT_NEGATION",
        "conflicting_property": "store",
        "evidence_strength": 0.85,
        "category_rationale": "Explicit negation of the defining ordering predicate.",
    })
    cases.append({
        "case_id": "BST-CORE-04",
        "domain": "BST",
        "question": bst_q,
        "reference_answer": bst_ref,
        "student_proposition": "In a binary search tree, the left child is always greater than the parent.",
        "controlled_severity": "CORE_CONTRADICTION",
        "contradiction_type": "VALUE_CONFLICT",
        "conflicting_property": "relative_size",
        "evidence_strength": 0.90,
        "category_rationale": "Inversion of parent-child relative ordering invariant.",
    })
    cases.append({
        "case_id": "BST-CORE-05",
        "domain": "BST",
        "question": bst_q,
        "reference_answer": bst_ref,
        "student_proposition": "A binary search tree places keys in random arbitrary child positions.",
        "controlled_severity": "CORE_CONTRADICTION",
        "contradiction_type": "VALUE_CONFLICT",
        "conflicting_property": "ordering",
        "evidence_strength": 0.85,
        "category_rationale": "Direct denial of organized search tree ordering invariant.",
    })

    # Moderate Errors (5)
    cases.append({
        "case_id": "BST-MOD-01",
        "domain": "BST",
        "question": bst_q,
        "reference_answer": bst_ref,
        "student_proposition": "A binary search tree inorder traversal yields random order.",
        "controlled_severity": "MODERATE",
        "contradiction_type": "VALUE_CONFLICT",
        "conflicting_property": "traversal",
        "evidence_strength": 0.75,
        "category_rationale": "Traversal ordering confusion; secondary behavioral error.",
    })
    cases.append({
        "case_id": "BST-MOD-02",
        "domain": "BST",
        "question": bst_q,
        "reference_answer": bst_ref,
        "student_proposition": "A binary search tree guarantees O(1) constant time search in all cases.",
        "controlled_severity": "MODERATE",
        "contradiction_type": "VALUE_CONFLICT",
        "conflicting_property": "constant time",
        "evidence_strength": 0.70,
        "category_rationale": "Time complexity analysis confusion (worst-case O(n) vs O(1)).",
    })
    cases.append({
        "case_id": "BST-MOD-03",
        "domain": "BST",
        "question": bst_q,
        "reference_answer": bst_ref,
        "student_proposition": "A binary search tree is always perfectly balanced after every insertion.",
        "controlled_severity": "MODERATE",
        "contradiction_type": "VALUE_CONFLICT",
        "conflicting_property": "balanced",
        "evidence_strength": 0.75,
        "category_rationale": "Confuses basic BST with self-balancing tree variants.",
    })
    cases.append({
        "case_id": "BST-MOD-04",
        "domain": "BST",
        "question": bst_q,
        "reference_answer": bst_ref,
        "student_proposition": "A binary search tree permits nodes to have up to three children.",
        "controlled_severity": "MODERATE",
        "contradiction_type": "VALUE_CONFLICT",
        "conflicting_property": "three children",
        "evidence_strength": 0.80,
        "category_rationale": "Arity error (binary tree arity <= 2 vs ternary).",
    })
    cases.append({
        "case_id": "BST-MOD-05",
        "domain": "BST",
        "question": bst_q,
        "reference_answer": bst_ref,
        "student_proposition": "A binary search tree cannot store integer values in its nodes.",
        "controlled_severity": "MODERATE",
        "contradiction_type": "EXPLICIT_NEGATION",
        "conflicting_property": "integer data type",
        "evidence_strength": 0.70,
        "category_rationale": "Arbitrary data type restriction misconception.",
    })

    # Minor Errors (5)
    cases.append({
        "case_id": "BST-MIN-01",
        "domain": "BST",
        "question": bst_q,
        "reference_answer": bst_ref,
        "student_proposition": "A binary search tree always requires four pointers per node.",
        "controlled_severity": "MINOR",
        "contradiction_type": "VALUE_CONFLICT",
        "conflicting_property": "pointers",
        "evidence_strength": 0.65,
        "category_rationale": "Peripheral node struct implementation detail error.",
    })
    cases.append({
        "case_id": "BST-MIN-02",
        "domain": "BST",
        "question": bst_q,
        "reference_answer": bst_ref,
        "student_proposition": "A binary search tree must be implemented using recursive functions.",
        "controlled_severity": "MINOR",
        "contradiction_type": "VALUE_CONFLICT",
        "conflicting_property": "recursion",
        "evidence_strength": 0.60,
        "category_rationale": "Implementation paradigm misconception (iterative is valid).",
    })
    cases.append({
        "case_id": "BST-MIN-03",
        "domain": "BST",
        "question": bst_q,
        "reference_answer": bst_ref,
        "student_proposition": "Binary search trees were invented in the year 2010.",
        "controlled_severity": "MINOR",
        "contradiction_type": "VALUE_CONFLICT",
        "conflicting_property": "year",
        "evidence_strength": 0.60,
        "category_rationale": "Historical date trivia error.",
    })
    cases.append({
        "case_id": "BST-MIN-04",
        "domain": "BST",
        "question": bst_q,
        "reference_answer": bst_ref,
        "student_proposition": "A binary search tree requires each node to store a blue color flag.",
        "controlled_severity": "MINOR",
        "contradiction_type": "VALUE_CONFLICT",
        "conflicting_property": "color",
        "evidence_strength": 0.60,
        "category_rationale": "Node attribute trivia confusion from Red-Black tree.",
    })
    cases.append({
        "case_id": "BST-MIN-05",
        "domain": "BST",
        "question": bst_q,
        "reference_answer": bst_ref,
        "student_proposition": "A binary search tree root node must always be painted blue in diagrams.",
        "controlled_severity": "MINOR",
        "contradiction_type": "VALUE_CONFLICT",
        "conflicting_property": "diagram",
        "evidence_strength": 0.55,
        "category_rationale": "Stylistic visual presentation trivia error.",
    })

    # Adversarial / Near-Miss Cases (2)
    cases.append({
        "case_id": "BST-ADV-01",
        "domain": "BST",
        "question": bst_q,
        "reference_answer": bst_ref,
        "student_proposition": "A general binary tree must store smaller values in the left subtree.",
        "controlled_severity": "UNRESOLVED",
        "contradiction_type": "VALUE_CONFLICT",
        "conflicting_property": "ordering",
        "evidence_strength": 0.85,
        "category_rationale": "Entity confusion: general binary tree does not enforce BST ordering.",
    })
    cases.append({
        "case_id": "BST-ADV-02",
        "domain": "BST",
        "question": bst_q,
        "reference_answer": bst_ref,
        "student_proposition": "A binary search tree is often used in computer memory systems.",
        "controlled_severity": "NONE",
        "contradiction_type": "NONE",
        "conflicting_property": None,
        "evidence_strength": 0.0,
        "category_rationale": "General domain application statement; non-contradictory.",
    })

    # ------------------------------------------------------------------------
    # 3. COMPILER DOMAIN (17 cases: 5 Core, 5 Moderate, 5 Minor, 2 Adv)
    # ------------------------------------------------------------------------
    cmp_ref = "A compiler translates source code into machine code."
    cmp_q = "What is a compiler?"

    # Core Contradictions (5)
    cases.append({
        "case_id": "CMP-CORE-01",
        "domain": "COMPILER",
        "question": cmp_q,
        "reference_answer": cmp_ref,
        "student_proposition": "A compiler does not translate source code.",
        "controlled_severity": "CORE_CONTRADICTION",
        "contradiction_type": "EXPLICIT_NEGATION",
        "conflicting_property": "translate",
        "evidence_strength": 0.85,
        "category_rationale": "Explicit negation of the core defining translation function.",
    })
    cases.append({
        "case_id": "CMP-CORE-02",
        "domain": "COMPILER",
        "question": cmp_q,
        "reference_answer": cmp_ref,
        "student_proposition": "A compiler executes source code directly without translation.",
        "controlled_severity": "CORE_CONTRADICTION",
        "contradiction_type": "VALUE_CONFLICT",
        "conflicting_property": "translation",
        "evidence_strength": 0.90,
        "category_rationale": "Direct denial of translation; execution model inversion.",
    })
    cases.append({
        "case_id": "CMP-CORE-03",
        "domain": "COMPILER",
        "question": cmp_q,
        "reference_answer": cmp_ref,
        "student_proposition": "A compiler translates machine code into source code.",
        "controlled_severity": "CORE_CONTRADICTION",
        "contradiction_type": "VALUE_CONFLICT",
        "conflicting_property": "translation",
        "evidence_strength": 0.90,
        "category_rationale": "Inversion of translation direction (describes decompiler).",
    })
    cases.append({
        "case_id": "CMP-CORE-04",
        "domain": "COMPILER",
        "question": cmp_q,
        "reference_answer": cmp_ref,
        "student_proposition": "A compiler converts source code into user input.",
        "controlled_severity": "CORE_CONTRADICTION",
        "contradiction_type": "VALUE_CONFLICT",
        "conflicting_property": "translation",
        "evidence_strength": 0.85,
        "category_rationale": "Direct replacement of target representation with user input.",
    })
    cases.append({
        "case_id": "CMP-CORE-05",
        "domain": "COMPILER",
        "question": cmp_q,
        "reference_answer": cmp_ref,
        "student_proposition": "A compiler deletes source code instead of producing machine code.",
        "controlled_severity": "CORE_CONTRADICTION",
        "contradiction_type": "VALUE_CONFLICT",
        "conflicting_property": "translation",
        "evidence_strength": 0.85,
        "category_rationale": "Denial of artifact generation.",
    })

    # Moderate Errors (5)
    cases.append({
        "case_id": "CMP-MOD-01",
        "domain": "COMPILER",
        "question": cmp_q,
        "reference_answer": cmp_ref,
        "student_proposition": "A compiler interprets code line by line at runtime.",
        "controlled_severity": "MODERATE",
        "contradiction_type": "VALUE_CONFLICT",
        "conflicting_property": "line by line",
        "evidence_strength": 0.75,
        "category_rationale": "Interpreter vs compiler runtime execution timing confusion.",
    })
    cases.append({
        "case_id": "CMP-MOD-02",
        "domain": "COMPILER",
        "question": cmp_q,
        "reference_answer": cmp_ref,
        "student_proposition": "A compiler executes programs faster than the CPU hardware.",
        "controlled_severity": "MODERATE",
        "contradiction_type": "VALUE_CONFLICT",
        "conflicting_property": "cpu",
        "evidence_strength": 0.70,
        "category_rationale": "Execution agent role confusion (compiler translates, CPU executes).",
    })
    cases.append({
        "case_id": "CMP-MOD-03",
        "domain": "COMPILER",
        "question": cmp_q,
        "reference_answer": cmp_ref,
        "student_proposition": "A compiler cannot detect syntax errors during compilation.",
        "controlled_severity": "MODERATE",
        "contradiction_type": "EXPLICIT_NEGATION",
        "conflicting_property": "detect syntax",
        "evidence_strength": 0.75,
        "category_rationale": "Denial of standard semantic/syntactic analysis phase capability.",
    })
    cases.append({
        "case_id": "CMP-MOD-04",
        "domain": "COMPILER",
        "question": cmp_q,
        "reference_answer": cmp_ref,
        "student_proposition": "A compiler only translates programs written in C.",
        "controlled_severity": "MODERATE",
        "contradiction_type": "VALUE_CONFLICT",
        "conflicting_property": "only translates c",
        "evidence_strength": 0.70,
        "category_rationale": "Arbitrary language restriction misconception.",
    })
    cases.append({
        "case_id": "CMP-MOD-05",
        "domain": "COMPILER",
        "question": cmp_q,
        "reference_answer": cmp_ref,
        "student_proposition": "A compiler never performs code optimization passes.",
        "controlled_severity": "MODERATE",
        "contradiction_type": "EXPLICIT_NEGATION",
        "conflicting_property": "optimization",
        "evidence_strength": 0.70,
        "category_rationale": "Denial of standard compiler optimization phase.",
    })

    # Minor Errors (5)
    cases.append({
        "case_id": "CMP-MIN-01",
        "domain": "COMPILER",
        "question": cmp_q,
        "reference_answer": cmp_ref,
        "student_proposition": "A compiler always produces bytecode named class.",
        "controlled_severity": "MINOR",
        "contradiction_type": "VALUE_CONFLICT",
        "conflicting_property": "class",
        "evidence_strength": 0.65,
        "category_rationale": "Java-specific bytecode file naming misconception.",
    })
    cases.append({
        "case_id": "CMP-MIN-02",
        "domain": "COMPILER",
        "question": cmp_q,
        "reference_answer": cmp_ref,
        "student_proposition": "A compiler always generates output files with exe extension.",
        "controlled_severity": "MINOR",
        "contradiction_type": "VALUE_CONFLICT",
        "conflicting_property": "extension",
        "evidence_strength": 0.65,
        "category_rationale": "Platform-specific file extension trivia error.",
    })
    cases.append({
        "case_id": "CMP-MIN-03",
        "domain": "COMPILER",
        "question": cmp_q,
        "reference_answer": cmp_ref,
        "student_proposition": "A compiler was first implemented in Python in the year 2005.",
        "controlled_severity": "MINOR",
        "contradiction_type": "VALUE_CONFLICT",
        "conflicting_property": "year",
        "evidence_strength": 0.60,
        "category_rationale": "Historical implementation date error.",
    })
    cases.append({
        "case_id": "CMP-MIN-04",
        "domain": "COMPILER",
        "question": cmp_q,
        "reference_answer": cmp_ref,
        "student_proposition": "A compiler requires at least 16 gigabytes of RAM to compile code.",
        "controlled_severity": "MINOR",
        "contradiction_type": "VALUE_CONFLICT",
        "conflicting_property": "ram",
        "evidence_strength": 0.60,
        "category_rationale": "System hardware requirement exaggeration.",
    })
    cases.append({
        "case_id": "CMP-MIN-05",
        "domain": "COMPILER",
        "question": cmp_q,
        "reference_answer": cmp_ref,
        "student_proposition": "A compiler executable file must always be stored in the root directory.",
        "controlled_severity": "MINOR",
        "contradiction_type": "VALUE_CONFLICT",
        "conflicting_property": "root directory",
        "evidence_strength": 0.55,
        "category_rationale": "File system placement convention error.",
    })

    # Adversarial / Near-Miss Cases (2)
    cases.append({
        "case_id": "CMP-ADV-01",
        "domain": "COMPILER",
        "question": cmp_q,
        "reference_answer": cmp_ref,
        "student_proposition": "An interpreter compiles source code into machine files.",
        "controlled_severity": "UNRESOLVED",
        "contradiction_type": "VALUE_CONFLICT",
        "conflicting_property": "translation",
        "evidence_strength": 0.85,
        "category_rationale": "Entity confusion: statement predicated of interpreter, not compiler.",
    })
    cases.append({
        "case_id": "CMP-ADV-02",
        "domain": "COMPILER",
        "question": cmp_q,
        "reference_answer": cmp_ref,
        "student_proposition": "A compiler is usually written in C++ or Rust.",
        "controlled_severity": "NONE",
        "contradiction_type": "NONE",
        "conflicting_property": None,
        "evidence_strength": 0.0,
        "category_rationale": "General tooling observation; non-contradictory statement.",
    })

    return cases


def build_robust_prop(text: str, domain: str) -> RobustProposition:
    """Helper to construct a mock RobustProposition with lemmas."""
    text_lower = text.lower()
    subj = "entity"
    pred = "act"
    obj = "val"

    if "primary key" in text_lower or "pk" in text_lower:
        subj = "primary key"
    elif "foreign key" in text_lower:
        subj = "foreign key"
    elif "binary search tree" in text_lower or "bst" in text_lower:
        subj = "binary search tree"
    elif "binary tree" in text_lower:
        subj = "binary tree"
    elif "compiler" in text_lower:
        subj = "compiler"
    elif "interpreter" in text_lower:
        subj = "interpreter"

    if "uniquely" in text_lower or "identifies" in text_lower or "identify" in text_lower:
        pred = "identify"
        obj = "record"
    elif "stores" in text_lower or "store" in text_lower:
        pred = "store"
        obj = "value"
    elif "translates" in text_lower or "translate" in text_lower:
        pred = "translate"
        obj = "code"

    return RobustProposition(
        subject=subj,
        predicate=pred,
        object=obj,
        subject_lemma=subj,
        predicate_lemma=pred,
        object_lemma=obj,
        representation_type=PropositionType.TRIPLE,
        polarity=Polarity.NEGATIVE if (" not " in text_lower or "never" in text_lower or "cannot" in text_lower) else Polarity.POSITIVE,
        modality=Modality.ASSERTED,
        source_text=text,
        char_start=0,
        char_end=len(text),
        sentence_index=0,
        token_indices=(0, 1, 2),
        dependency_evidence=("nsubj", "dobj"),
    )


# ============================================================================
# ABLATION VARIANTS
# ============================================================================

def run_ablation_variant(
    variant_name: str,
    ev: ContradictionEvidence,
    stu_prop: RobustProposition,
    ref_props: List[RobustProposition],
    domain: str,
    estimator: InterpretableSeverityEstimator,
) -> str:
    """
    Run an ablation variant:
    A: Contradiction evidence strength only (threshold based)
    B: Contradiction + Core proposition link
    C: Contradiction + Defining property target
    D: Contradiction + Reference role
    E: Full proposed estimator
    """
    if not ev.is_contradicted:
        return "NONE"

    if variant_name == "Variant_A":  # Evidence strength only
        if ev.evidence_strength >= 0.85:
            return "CORE_CONTRADICTION"
        elif ev.evidence_strength >= 0.65:
            return "MODERATE"
        else:
            return "MINOR"

    elif variant_name == "Variant_B":  # Contradiction + Core link
        core_link, _ = estimator._check_core_link(stu_prop, ref_props)
        if core_link and ev.evidence_strength >= 0.85:
            return "CORE_CONTRADICTION"
        elif ev.evidence_strength >= 0.65:
            return "MODERATE"
        else:
            return "MINOR"

    elif variant_name == "Variant_C":  # Contradiction + Defining property
        conf_prop = ev.conflicting_property
        defining_target = conf_prop and conf_prop.lower() in estimator.DEFINING_PROPERTIES.get(domain, set())
        if defining_target:
            return "CORE_CONTRADICTION"
        elif ev.evidence_strength >= 0.65:
            return "MODERATE"
        else:
            return "MINOR"

    elif variant_name == "Variant_D":  # Contradiction + Reference role
        core_link, _ = estimator._check_core_link(stu_prop, ref_props)
        conf_prop = ev.conflicting_property
        defining_target = conf_prop and conf_prop.lower() in estimator.DEFINING_PROPERTIES.get(domain, set())
        if core_link or defining_target:
            return "CORE_CONTRADICTION"
        else:
            return "MODERATE"

    elif variant_name == "Variant_E":  # Full proposed estimator
        res = estimator.estimate(ev, stu_prop, ref_props, domain=domain)
        return res.severity.value

    return "UNRESOLVED"


# ============================================================================
# EVALUATION & METRICS COMPUTATION
# ============================================================================

def compute_classification_metrics(y_true: List[str], y_pred: List[str], labels: List[str]) -> Dict[str, Any]:
    """Compute confusion matrix, per-class precision/recall/F1, and macro F1."""
    # Build confusion matrix: rows = true, cols = pred
    matrix: Dict[str, Dict[str, int]] = {t: {p: 0 for p in labels} for t in labels}
    for t, p in zip(y_true, y_pred):
        if t in matrix and p in matrix[t]:
            matrix[t][p] += 1

    per_class: Dict[str, Dict[str, float]] = {}
    f1_list: List[float] = []
    p_list: List[float] = []
    r_list: List[float] = []

    for label in labels:
        tp = matrix[label][label]
        fp = sum(matrix[t][label] for t in labels if t != label)
        fn = sum(matrix[label][p] for p in labels if p != label)

        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0

        per_class[label] = {
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1": round(f1, 4),
            "support": sum(matrix[label].values()),
        }
        f1_list.append(f1)
        p_list.append(prec)
        r_list.append(rec)

    macro_f1 = sum(f1_list) / len(f1_list) if f1_list else 0.0
    macro_prec = sum(p_list) / len(p_list) if p_list else 0.0
    macro_rec = sum(r_list) / len(r_list) if r_list else 0.0

    return {
        "confusion_matrix": matrix,
        "per_class": per_class,
        "macro_precision": round(macro_prec, 4),
        "macro_recall": round(macro_rec, 4),
        "macro_f1": round(macro_f1, 4),
    }


def main() -> None:
    output_dir = "evaluation/severity_development"
    os.makedirs(output_dir, exist_ok=True)

    print("Loading 51 controlled development cases for Phase 4C...")
    cases = get_phase4c_controlled_dataset()
    estimator = InterpretableSeverityEstimator()

    controlled_cases_rows: List[Dict[str, Any]] = []
    severity_results_rows: List[Dict[str, Any]] = []
    traces: Dict[str, Any] = {}

    y_true: List[str] = []
    y_pred_full: List[str] = []

    ablation_preds: Dict[str, List[str]] = {
        "Variant_A": [],
        "Variant_B": [],
        "Variant_C": [],
        "Variant_D": [],
        "Variant_E": [],
    }

    for c in cases:
        cid = c["case_id"]
        dom = c["domain"]
        q = c["question"]
        ref_text = c["reference_answer"]
        stu_text = c["student_proposition"]
        true_sev = c["controlled_severity"]

        ref_prop = build_robust_prop(ref_text, dom)
        stu_prop = build_robust_prop(stu_text, dom)

        # Build contradiction evidence structure
        is_cont = (true_sev != "NONE")
        c_type = ContradictionType(c["contradiction_type"])
        ev = ContradictionEvidence(
            is_contradicted=is_cont,
            contradiction_type=c_type,
            conflicting_entity=stu_prop.subject,
            conflicting_property=c["conflicting_property"],
            conflicting_value="conflicting_val",
            evidence_strength=c["evidence_strength"],
            explanation=c["category_rationale"],
        )

        # Run Full Estimator
        res = estimator.estimate(ev, stu_prop, [ref_prop], question=q, domain=dom)
        pred_sev = res.severity.value

        y_true.append(true_sev)
        y_pred_full.append(pred_sev)

        # Run Ablations
        for vname in ablation_preds.keys():
            ab_pred = run_ablation_variant(vname, ev, stu_prop, [ref_prop], dom, estimator)
            ablation_preds[vname].append(ab_pred)

        # Save metadata
        controlled_cases_rows.append({
            "case_id": cid,
            "domain": dom,
            "question": q,
            "reference_answer": ref_text,
            "student_proposition": stu_text,
            "controlled_severity": true_sev,
            "contradiction_type": c["contradiction_type"],
            "conflicting_property": c["conflicting_property"] or "NONE",
            "evidence_strength": c["evidence_strength"],
            "category_rationale": c["category_rationale"],
        })

        severity_results_rows.append({
            "case_id": cid,
            "domain": dom,
            "student_proposition": stu_text,
            "controlled_severity": true_sev,
            "estimated_severity": pred_sev,
            "is_correct": (pred_sev == true_sev),
            "severity_score": res.severity_score,
            "core_link": res.evidence.core_link,
            "defining_property": res.evidence.defining_property_target,
            "is_peripheral": res.evidence.is_peripheral,
            "is_relational": res.evidence.is_relational_confusion,
            "entity_grounded": res.evidence.entity_grounded,
            "explanation": res.explanation,
        })

        traces[cid] = {
            "case_id": cid,
            "domain": dom,
            "controlled_severity": true_sev,
            "estimated_result": res.to_dict(),
        }

    # 1. Export phase4c_controlled_cases.csv
    cases_path = os.path.join(output_dir, "phase4c_controlled_cases.csv")
    with open(cases_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(controlled_cases_rows[0].keys()))
        writer.writeheader()
        writer.writerows(controlled_cases_rows)
    print(f"Exported {len(controlled_cases_rows)} controlled cases to {cases_path}")

    # 2. Export phase4c_severity_results.csv
    results_path = os.path.join(output_dir, "phase4c_severity_results.csv")
    with open(results_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(severity_results_rows[0].keys()))
        writer.writeheader()
        writer.writerows(severity_results_rows)
    print(f"Exported severity estimation results to {results_path}")

    # 3. Export phase4c_score_traces.json
    traces_path = os.path.join(output_dir, "phase4c_score_traces.json")
    with open(traces_path, "w", encoding="utf-8") as f:
        json.dump(traces, f, indent=2)
    print(f"Exported severity traces to {traces_path}")

    # 4. Compute Metrics & Ablations
    eval_labels = ["CORE_CONTRADICTION", "MODERATE", "MINOR", "UNRESOLVED", "NONE"]
    metrics_full = compute_classification_metrics(y_true, y_pred_full, eval_labels)

    ablation_rows: List[Dict[str, Any]] = []
    for vname, vpreds in ablation_preds.items():
        vmetrics = compute_classification_metrics(y_true, vpreds, eval_labels)
        correct_cnt = sum(1 for yt, yp in zip(y_true, vpreds) if yt == yp)
        acc = correct_cnt / len(y_true)
        ablation_rows.append({
            "ablation_variant": vname,
            "accuracy": round(acc, 4),
            "macro_precision": vmetrics["macro_precision"],
            "macro_recall": vmetrics["macro_recall"],
            "macro_f1": vmetrics["macro_f1"],
            "core_contradiction_f1": vmetrics["per_class"]["CORE_CONTRADICTION"]["f1"],
            "moderate_f1": vmetrics["per_class"]["MODERATE"]["f1"],
            "minor_f1": vmetrics["per_class"]["MINOR"]["f1"],
            "unresolved_f1": vmetrics["per_class"]["UNRESOLVED"]["f1"],
        })

    ablation_path = os.path.join(output_dir, "phase4c_ablation_results.csv")
    with open(ablation_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(ablation_rows[0].keys()))
        writer.writeheader()
        writer.writerows(ablation_rows)
    print(f"Exported ablation results to {ablation_path}")

    print("\n=======================================================")
    print("PHASE 4C CONTROLLED EVALUATION SUMMARY")
    print("=======================================================")
    print(f"Total Cases: {len(y_true)}")
    print(f"Full Model Macro F1: {metrics_full['macro_f1']:.4f}")
    print(f"Full Model Macro Precision: {metrics_full['macro_precision']:.4f}")
    print(f"Full Model Macro Recall: {metrics_full['macro_recall']:.4f}")
    print("\nPer-Class Performance:")
    for lbl, stats in metrics_full["per_class"].items():
        print(f"  {lbl:20s}: P={stats['precision']:.4f}, R={stats['recall']:.4f}, F1={stats['f1']:.4f} (n={stats['support']})")

    print("\nConfusion Matrix (Rows=True, Cols=Pred):")
    print(f"{'':20s} " + " ".join(f"{lbl[:5]:>7s}" for lbl in eval_labels))
    for t in eval_labels:
        row_str = " ".join(f"{metrics_full['confusion_matrix'][t][p]:>7d}" for p in eval_labels)
        print(f"{t:20s} {row_str}")

    print("\nAblation Comparison:")
    for arow in ablation_rows:
        print(f"  {arow['ablation_variant']:12s}: Acc={arow['accuracy']:.4f}, Macro-F1={arow['macro_f1']:.4f}, Core-F1={arow['core_contradiction_f1']:.4f}")


if __name__ == "__main__":
    main()
