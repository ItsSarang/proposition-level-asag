"""
Phase 4B Controlled Case Runner & Data Exporter.

Executes all 33 controlled development cases across three domains (Primary Key,
Binary Search Tree, Compiler) plus Mixed Combinations against the 4 candidate
scoring models:
- Model A: Current Additive Saturating Scorer
- Model B: Proportional Penalty Scorer
- Model C: Evidence-Weighted Bounded Severity Penalty Scorer
- Model D: Core / Additional Decomposition with Gated Compensation

Exports:
- phase4b_controlled_cases.csv
- phase4b_model_comparison.csv
- phase4b_score_traces.json
"""

from __future__ import annotations

import csv
import json
import os
from typing import Any, Dict, List, Optional, Tuple

from base_asag.representation.hybrid import RobustProposition
from evaluation.scoring_development.experimental_scoring_models import (
    ModelA_CurrentAdditiveScorer,
    ModelB_ProportionalPenaltyScorer,
    ModelC_EvidenceWeightedSeverityScorer,
    ModelD_CoreAdditionalDecompositionScorer,
)
from proposed_asag.classification.robust_classifier import (
    AdditionalInfoClass,
    ClassifiedProposition,
)
from proposed_asag.contradiction.property_contradiction import (
    ContradictionEvidence,
    ContradictionType,
)
from proposed_asag.overhauled_pipeline import OverhauledASAGPipeline


# ============================================================================
# CASE DEFINITIONS (33 Controlled Development Cases)
# ============================================================================

def get_phase4b_case_definitions() -> List[Dict[str, Any]]:
    return [
        # --------------------------------------------------------------------
        # DOMAIN 1: PRIMARY KEY (10 cases)
        # --------------------------------------------------------------------
        {
            "case_id": "PK-01",
            "domain": "PRIMARY_KEY",
            "case_name": "PK-01 (Correct core only)",
            "question": "What is the purpose of a primary key?",
            "reference_answer": "A primary key uniquely identifies each record in a table.",
            "student_answer": "A primary key uniquely identifies each record in a table.",
            "case_description": "Clean paraphrase of reference definition; baseline control.",
            "expected_qualitative_relation": "Baseline high score (no additions)",
            "severities": {},
            "target_classifications": {},
        },
        {
            "case_id": "PK-02",
            "domain": "PRIMARY_KEY",
            "case_name": "PK-02 (Correct core + correct additional)",
            "question": "What is the purpose of a primary key?",
            "reference_answer": "A primary key uniquely identifies each record in a table.",
            "student_answer": "A primary key uniquely identifies each record in a table and cannot contain NULL values.",
            "case_description": "Correct core plus verified factual addition (PK_NOT_NULL).",
            "expected_qualitative_relation": "R2: Score >= PK-01",
            "severities": {},
            "target_classifications": {},
        },
        {
            "case_id": "PK-03",
            "domain": "PRIMARY_KEY",
            "case_name": "PK-03 (Correct core + irrelevant)",
            "question": "What is the purpose of a primary key?",
            "reference_answer": "A primary key uniquely identifies each record in a table.",
            "student_answer": "A primary key uniquely identifies each record in a table. SQL was developed in the 1970s.",
            "case_description": "Correct core plus off-topic historical fact.",
            "expected_qualitative_relation": "R1, R12: Score == PK-01 within tolerance",
            "severities": {},
            "target_classifications": {},
        },
        {
            "case_id": "PK-04",
            "domain": "PRIMARY_KEY",
            "case_name": "PK-04 (Correct core + unsupported relevant)",
            "question": "What is the purpose of a primary key?",
            "reference_answer": "A primary key uniquely identifies each record in a table.",
            "student_answer": "A primary key uniquely identifies each record in a table and is usually indexed using a B-tree.",
            "case_description": "Relevant implementation detail unsupported by frozen rules; UNCERTAIN.",
            "expected_qualitative_relation": "R8: Score == PK-01 (no unverified bonus)",
            "severities": {},
            "target_classifications": {},
        },
        {
            "case_id": "PK-05",
            "domain": "PRIMARY_KEY",
            "case_name": "PK-05 (Correct core + minor incorrect)",
            "question": "What is the purpose of a primary key?",
            "reference_answer": "A primary key uniquely identifies each record in a table.",
            "student_answer": "A primary key uniquely identifies each record in a table. A primary key is always named ID in database schemas.",
            "case_description": "Peripheral schema convention error; minor severity.",
            "expected_qualitative_relation": "R3, R4, R11: Score < PK-01, but > PK-06",
            "severities": {"key is always named": "MINOR", "A primary key is always named ID in database schemas": "MINOR"},
            "target_classifications": {"key is always named": AdditionalInfoClass.INCORRECT},
        },
        {
            "case_id": "PK-06",
            "domain": "PRIMARY_KEY",
            "case_name": "PK-06 (Correct core + serious contradiction)",
            "question": "What is the purpose of a primary key?",
            "reference_answer": "A primary key uniquely identifies each record in a table.",
            "student_answer": "A primary key uniquely identifies each record in a table and can contain duplicate values.",
            "case_description": "Direct contradiction of core uniqueness property; CORE_CONTRADICTION.",
            "expected_qualitative_relation": "R3, R4: Score strictly lower than PK-01 and PK-05",
            "severities": {"can contain duplicate values": "CORE_CONTRADICTION"},
            "target_classifications": {},
        },
        {
            "case_id": "PK-07",
            "domain": "PRIMARY_KEY",
            "case_name": "PK-07 (Correct core + multiple minor incorrect)",
            "question": "What is the purpose of a primary key?",
            "reference_answer": "A primary key uniquely identifies each record in a table.",
            "student_answer": "A primary key uniquely identifies each record in a table. A primary key is always named ID. The key was invented in 1999.",
            "case_description": "Two peripheral minor factual errors.",
            "expected_qualitative_relation": "R5: Score <= PK-05 <= PK-01",
            "severities": {
                "key is always named": "MINOR",
                "key was invented": "MINOR",
            },
            "target_classifications": {
                "key is always named": AdditionalInfoClass.INCORRECT,
                "key was invented": AdditionalInfoClass.INCORRECT,
            },
        },
        {
            "case_id": "PK-08",
            "domain": "PRIMARY_KEY",
            "case_name": "PK-08 (Correct core + serious contradiction + irrelevant)",
            "question": "What is the purpose of a primary key?",
            "reference_answer": "A primary key uniquely identifies each record in a table.",
            "student_answer": "A primary key uniquely identifies each record in a table and can contain duplicate values. SQL was developed in the 1970s.",
            "case_description": "Core contradiction combined with neutral off-topic statement.",
            "expected_qualitative_relation": "R12: Score == PK-06 within tolerance",
            "severities": {"can contain duplicate values": "CORE_CONTRADICTION"},
            "target_classifications": {},
        },
        {
            "case_id": "PK-09",
            "domain": "PRIMARY_KEY",
            "case_name": "PK-09 (Partial core + serious contradiction)",
            "question": "What is the purpose of a primary key?",
            "reference_answer": "A primary key uniquely identifies each record in a table.",
            "student_answer": "A primary key determines each record in a table. It can contain duplicate values.",
            "case_description": "Incomplete core coverage combined with core contradiction.",
            "expected_qualitative_relation": "R6, R7: Score <= Partial core baseline",
            "severities": {"It can contain duplicate values": "CORE_CONTRADICTION"},
            "target_classifications": {},
        },
        {
            "case_id": "PK-10",
            "domain": "PRIMARY_KEY",
            "case_name": "PK-10 (Partial core + minor incorrect)",
            "question": "What is the purpose of a primary key?",
            "reference_answer": "A primary key uniquely identifies each record in a table.",
            "student_answer": "A primary key determines each record in a table. A primary key is always named ID in database schemas.",
            "case_description": "Incomplete core coverage combined with peripheral minor error.",
            "expected_qualitative_relation": "R6: Score <= Partial core baseline, > PK-09",
            "severities": {"key is always named": "MINOR"},
            "target_classifications": {"key is always named": AdditionalInfoClass.INCORRECT},
        },

        # --------------------------------------------------------------------
        # DOMAIN 2: BINARY SEARCH TREE (8 cases)
        # --------------------------------------------------------------------
        {
            "case_id": "BST-01",
            "domain": "BST",
            "case_name": "BST-01 (Correct core only)",
            "question": "What is a binary search tree?",
            "reference_answer": "A binary search tree stores smaller values in the left subtree.",
            "student_answer": "A binary search tree stores smaller values in the left subtree.",
            "case_description": "Full core coverage for binary search tree.",
            "expected_qualitative_relation": "Baseline high score (BST domain)",
            "severities": {},
            "target_classifications": {},
        },
        {
            "case_id": "BST-02",
            "domain": "BST",
            "case_name": "BST-02 (Correct core + correct additional)",
            "question": "What is a binary search tree?",
            "reference_answer": "A binary search tree stores smaller values in the left subtree.",
            "student_answer": "A binary search tree stores smaller values in the left subtree. BST inorder traversal yields sorted order.",
            "case_description": "Correct core plus verified factual addition (BST_INORDER_SORTED).",
            "expected_qualitative_relation": "R2: Score >= BST-01",
            "severities": {},
            "target_classifications": {},
        },
        {
            "case_id": "BST-03",
            "domain": "BST",
            "case_name": "BST-03 (Correct core + irrelevant)",
            "question": "What is a binary search tree?",
            "reference_answer": "A binary search tree stores smaller values in the left subtree.",
            "student_answer": "A binary search tree stores smaller values in the left subtree. Binary search was published in 1946.",
            "case_description": "Correct core plus off-topic historical remark.",
            "expected_qualitative_relation": "R1, R12: Score == BST-01 within tolerance",
            "severities": {},
            "target_classifications": {},
        },
        {
            "case_id": "BST-04",
            "domain": "BST",
            "case_name": "BST-04 (Correct core + unsupported relevant)",
            "question": "What is a binary search tree?",
            "reference_answer": "A binary search tree stores smaller values in the left subtree.",
            "student_answer": "A binary search tree stores smaller values in the left subtree. AVL trees perform rotations to maintain height balance.",
            "case_description": "Relevant tree concept unsupported by frozen rules; UNCERTAIN.",
            "expected_qualitative_relation": "R8: Score == BST-01 (no unverified bonus)",
            "severities": {},
            "target_classifications": {},
        },
        {
            "case_id": "BST-05",
            "domain": "BST",
            "case_name": "BST-05 (Correct core + minor incorrect)",
            "question": "What is a binary search tree?",
            "reference_answer": "A binary search tree stores smaller values in the left subtree.",
            "student_answer": "A binary search tree stores smaller values in the left subtree. A binary search tree always requires four pointers per node.",
            "case_description": "Peripheral node structure mistake; minor severity.",
            "expected_qualitative_relation": "R3, R4, R11: Score < BST-01, but > BST-06",
            "severities": {"tree always requires": "MINOR"},
            "target_classifications": {"tree always requires": AdditionalInfoClass.INCORRECT},
        },
        {
            "case_id": "BST-06",
            "domain": "BST",
            "case_name": "BST-06 (Correct core + direct contradiction)",
            "question": "What is a binary search tree?",
            "reference_answer": "A binary search tree stores smaller values in the left subtree.",
            "student_answer": "A binary search tree stores smaller values in the left subtree. A binary search tree places larger values in the left subtree.",
            "case_description": "Direct contradiction of ordering property (smaller vs larger); CORE_CONTRADICTION.",
            "expected_qualitative_relation": "R3, R4: Score strictly lower than BST-01 and BST-05",
            "severities": {"tree places larger values": "CORE_CONTRADICTION"},
            "target_classifications": {},
        },
        {
            "case_id": "BST-07",
            "domain": "BST",
            "case_name": "BST-07 (Correct core + multiple contradictions)",
            "question": "What is a binary search tree?",
            "reference_answer": "A binary search tree stores smaller values in the left subtree.",
            "student_answer": "A binary search tree stores smaller values in the left subtree. A binary search tree places larger values in the left subtree. Inorder traversal yields random order.",
            "case_description": "Two serious conceptual contradictions of BST invariants.",
            "expected_qualitative_relation": "R5: Score <= BST-06 <= BST-01",
            "severities": {
                "tree places larger values": "CORE_CONTRADICTION",
                "yields random order": "MODERATE",
            },
            "target_classifications": {
                "yields random order": AdditionalInfoClass.INCORRECT,
            },
        },
        {
            "case_id": "BST-08",
            "domain": "BST",
            "case_name": "BST-08 (Partial core + contradiction)",
            "question": "What is a binary search tree?",
            "reference_answer": "A binary search tree stores smaller values in the left subtree.",
            "student_answer": "A binary search tree keeps values in the left subtree. A binary search tree places larger values in the left subtree.",
            "case_description": "Incomplete core coverage combined with ordering contradiction.",
            "expected_qualitative_relation": "R6, R7: Score <= Partial core baseline",
            "severities": {"tree places larger values": "CORE_CONTRADICTION"},
            "target_classifications": {},
        },

        # --------------------------------------------------------------------
        # DOMAIN 3: COMPILER (8 cases)
        # --------------------------------------------------------------------
        {
            "case_id": "CMP-01",
            "domain": "COMPILER",
            "case_name": "CMP-01 (Correct core only)",
            "question": "What is a compiler?",
            "reference_answer": "A compiler translates source code into machine code.",
            "student_answer": "A compiler translates source code into machine code.",
            "case_description": "Full core coverage for compiler definition.",
            "expected_qualitative_relation": "Baseline high score (Compiler domain)",
            "severities": {},
            "target_classifications": {},
        },
        {
            "case_id": "CMP-02",
            "domain": "COMPILER",
            "case_name": "CMP-02 (Correct core + correct additional)",
            "question": "What is a compiler?",
            "reference_answer": "A compiler translates source code into machine code.",
            "student_answer": "A compiler translates source code into machine code. A compiler generates an intermediate representation.",
            "case_description": "Correct core plus verified factual addition (COMPILER_INTERMEDIATE_REP).",
            "expected_qualitative_relation": "R2: Score >= CMP-01",
            "severities": {},
            "target_classifications": {},
        },
        {
            "case_id": "CMP-03",
            "domain": "COMPILER",
            "case_name": "CMP-03 (Correct core + irrelevant)",
            "question": "What is a compiler?",
            "reference_answer": "A compiler translates source code into machine code.",
            "student_answer": "A compiler translates source code into machine code. Dennis Ritchie created the C programming language.",
            "case_description": "Correct core plus off-topic historical biographical statement.",
            "expected_qualitative_relation": "R1, R12: Score == CMP-01 within tolerance",
            "severities": {},
            "target_classifications": {},
        },
        {
            "case_id": "CMP-04",
            "domain": "COMPILER",
            "case_name": "CMP-04 (Correct core + unsupported relevant)",
            "question": "What is a compiler?",
            "reference_answer": "A compiler translates source code into machine code.",
            "student_answer": "A compiler translates source code into machine code. A compiler uses LLVM optimization passes.",
            "case_description": "Relevant compiler technology unsupported by frozen rules; UNCERTAIN.",
            "expected_qualitative_relation": "R8: Score == CMP-01 (no unverified bonus)",
            "severities": {},
            "target_classifications": {},
        },
        {
            "case_id": "CMP-05",
            "domain": "COMPILER",
            "case_name": "CMP-05 (Correct core + minor incorrect)",
            "question": "What is a compiler?",
            "reference_answer": "A compiler translates source code into machine code.",
            "student_answer": "A compiler translates source code into machine code. A compiler always generates output files with exe extension.",
            "case_description": "Peripheral file extension misconception; minor severity.",
            "expected_qualitative_relation": "R3, R4, R11: Score < CMP-01, but > CMP-06",
            "severities": {"compiler always generates": "MINOR", "generates output files": "MINOR"},
            "target_classifications": {"compiler always generates": AdditionalInfoClass.INCORRECT, "generates output files": AdditionalInfoClass.INCORRECT},
        },
        {
            "case_id": "CMP-06",
            "domain": "COMPILER",
            "case_name": "CMP-06 (Correct core + direct contradiction)",
            "question": "What is a compiler?",
            "reference_answer": "A compiler translates source code into machine code.",
            "student_answer": "A compiler translates source code into machine code. A compiler does not translate source code.",
            "case_description": "Explicit negation contradiction on core translation function; CORE_CONTRADICTION.",
            "expected_qualitative_relation": "R3, R4: Score strictly lower than CMP-01 and CMP-05",
            "severities": {"compiler does not translate source code": "CORE_CONTRADICTION"},
            "target_classifications": {},
        },
        {
            "case_id": "CMP-07",
            "domain": "COMPILER",
            "case_name": "CMP-07 (Correct core + multiple incorrect additions)",
            "question": "What is a compiler?",
            "reference_answer": "A compiler translates source code into machine code.",
            "student_answer": "A compiler translates source code into machine code. A compiler does not translate source code. It executes machine code directly without translation.",
            "case_description": "Direct contradiction plus execution-model confusion.",
            "expected_qualitative_relation": "R5: Score <= CMP-06 <= CMP-01",
            "severities": {
                "compiler does not translate source code": "CORE_CONTRADICTION",
                "It executes machine code": "MODERATE",
            },
            "target_classifications": {
                "It executes machine code": AdditionalInfoClass.INCORRECT,
            },
        },
        {
            "case_id": "CMP-08",
            "domain": "COMPILER",
            "case_name": "CMP-08 (Partial core + incorrect addition)",
            "question": "What is a compiler?",
            "reference_answer": "A compiler translates source code into machine code.",
            "student_answer": "A compiler modifies source code into machine code. A compiler executes code directly at runtime.",
            "case_description": "Approximate core coverage combined with interpreter confusion.",
            "expected_qualitative_relation": "R6, R7: Score <= Partial core baseline",
            "severities": {"compiler executes code": "CORE_CONTRADICTION"},
            "target_classifications": {"compiler executes code": AdditionalInfoClass.INCORRECT},
        },

        # --------------------------------------------------------------------
        # DOMAIN 4: MIXED COMBINATIONS (7 cases)
        # --------------------------------------------------------------------
        {
            "case_id": "MIX-01",
            "domain": "MIXED",
            "case_name": "MIX-01 (Correct additional + irrelevant)",
            "question": "What is the purpose of a primary key?",
            "reference_answer": "A primary key uniquely identifies each record in a table.",
            "student_answer": "A primary key uniquely identifies each record in a table and cannot contain NULL values. SQL was developed in the 1970s.",
            "case_description": "Verified correct addition (PK_NOT_NULL) plus off-topic irrelevant fact.",
            "expected_qualitative_relation": "R1, R2: Score >= PK-01, neutral irrelevant",
            "severities": {},
            "target_classifications": {},
        },
        {
            "case_id": "MIX-02",
            "domain": "MIXED",
            "case_name": "MIX-02 (Correct additional + incorrect)",
            "question": "What is the purpose of a primary key?",
            "reference_answer": "A primary key uniquely identifies each record in a table.",
            "student_answer": "A primary key uniquely identifies each record in a table and cannot contain NULL values. It can contain duplicate values.",
            "case_description": "Verified correct addition plus defining-property contradiction.",
            "expected_qualitative_relation": "R7: Correct bonus cannot override core contradiction",
            "severities": {"It can contain duplicate values": "CORE_CONTRADICTION"},
            "target_classifications": {},
        },
        {
            "case_id": "MIX-03",
            "domain": "MIXED",
            "case_name": "MIX-03 (Correct additional + uncertain)",
            "question": "What is the purpose of a primary key?",
            "reference_answer": "A primary key uniquely identifies each record in a table.",
            "student_answer": "A primary key uniquely identifies each record in a table and cannot contain NULL values. It is usually indexed using a B-tree.",
            "case_description": "Verified correct addition plus unverified relevant statement.",
            "expected_qualitative_relation": "R2, R8: Receives correct bonus, 0 bonus for uncertain",
            "severities": {},
            "target_classifications": {},
        },
        {
            "case_id": "MIX-04",
            "domain": "MIXED",
            "case_name": "MIX-04 (Incorrect + irrelevant)",
            "question": "What is the purpose of a primary key?",
            "reference_answer": "A primary key uniquely identifies each record in a table.",
            "student_answer": "A primary key uniquely identifies each record in a table and can contain duplicate values. SQL was developed in the 1970s.",
            "case_description": "Core contradiction combined with off-topic historical fact.",
            "expected_qualitative_relation": "R12: Irrelevant does not alter contradiction penalty",
            "severities": {"can contain duplicate values": "CORE_CONTRADICTION"},
            "target_classifications": {},
        },
        {
            "case_id": "MIX-05",
            "domain": "MIXED",
            "case_name": "MIX-05 (Minor incorrect + core contradiction)",
            "question": "What is the purpose of a primary key?",
            "reference_answer": "A primary key uniquely identifies each record in a table.",
            "student_answer": "A primary key uniquely identifies each record in a table. A primary key is always named ID in database schemas. It can contain duplicate values.",
            "case_description": "Minor peripheral naming error plus core defining property contradiction.",
            "expected_qualitative_relation": "R5: Compound deficit <= single contradiction",
            "severities": {
                "key is always named": "MINOR",
                "It can contain duplicate values": "CORE_CONTRADICTION",
            },
            "target_classifications": {
                "key is always named": AdditionalInfoClass.INCORRECT,
            },
        },
        {
            "case_id": "MIX-06",
            "domain": "MIXED",
            "case_name": "MIX-06 (Correct additional + minor incorrect + irrelevant)",
            "question": "What is the purpose of a primary key?",
            "reference_answer": "A primary key uniquely identifies each record in a table.",
            "student_answer": "A primary key uniquely identifies each record in a table and cannot contain NULL values. A primary key is always named ID in database schemas. SQL was developed in the 1970s.",
            "case_description": "Three-way mix: verified correct + minor incorrect + neutral irrelevant.",
            "expected_qualitative_relation": "R1, R2, R11: Balanced adjustment with full itemized traceability",
            "severities": {"key is always named": "MINOR"},
            "target_classifications": {"key is always named": AdditionalInfoClass.INCORRECT},
        },
        {
            "case_id": "MIX-07",
            "domain": "MIXED",
            "case_name": "MIX-07 (Correct additional + core contradiction across BST)",
            "question": "What is a binary search tree?",
            "reference_answer": "A binary search tree stores smaller values in the left subtree.",
            "student_answer": "A binary search tree stores smaller values in the left subtree. BST inorder traversal yields sorted order. A binary search tree places larger values in the left subtree.",
            "case_description": "BST correct additional (BST_INORDER_SORTED) plus direct ordering contradiction.",
            "expected_qualitative_relation": "R7: Correct bonus cannot override core ordering contradiction",
            "severities": {"tree places larger values": "CORE_CONTRADICTION"},
            "target_classifications": {},
        },
    ]


# ============================================================================
# EXECUTION & LOGGING
# ============================================================================

def run_phase4b_evaluation() -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    pipe = OverhauledASAGPipeline()
    model_a = ModelA_CurrentAdditiveScorer()
    model_b = ModelB_ProportionalPenaltyScorer()
    model_c = ModelC_EvidenceWeightedSeverityScorer()
    model_d = ModelD_CoreAdditionalDecompositionScorer()

    case_defs = get_phase4b_case_definitions()

    controlled_cases_rows: List[Dict[str, Any]] = []
    model_comp_rows: List[Dict[str, Any]] = []
    score_traces: Dict[str, Any] = {}

    for cdef in case_defs:
        cid = cdef["case_id"]
        q = cdef["question"]
        ref = cdef["reference_answer"]
        stu = cdef["student_answer"]
        sev_map = cdef["severities"]
        override_class = cdef["target_classifications"]

        # Run pipeline
        res = pipe.evaluate(q, ref, stu)
        base_norm = res.base_score_normalized
        base_scaled = res.base_score_scaled

        # Collect raw classified props
        raw_props = list(res.classification_result.classified_propositions) if res.classification_result else []

        # Construct adapted propositions with experimental overrides if specified
        adapted_props: List[ClassifiedProposition] = []
        for p in raw_props:
            matched_override = None
            p_text = p.proposition.source_text
            for target_substr, cls_target in override_class.items():
                if target_substr.lower() in p_text.lower():
                    matched_override = cls_target
                    break

            if matched_override is not None:
                # If overriding to INCORRECT and proposition lacked contradiction evidence, provide standard experimental evidence
                if matched_override == AdditionalInfoClass.INCORRECT and (p.contradiction_evidence is None or not p.contradiction_evidence.is_contradicted):
                    ev = ContradictionEvidence(
                        is_contradicted=True,
                        contradiction_type=ContradictionType.VALUE_CONFLICT,
                        conflicting_entity=p.proposition.subject,
                        conflicting_property=p.proposition.predicate,
                        conflicting_value="experimental_override",
                        evidence_strength=0.80,
                        explanation=f"Experimental controlled override to {matched_override.value}",
                    )
                else:
                    ev = p.contradiction_evidence

                adapted_p = ClassifiedProposition(
                    proposition=p.proposition,
                    classification=matched_override,
                    relevance_evidence=p.relevance_evidence,
                    contradiction_evidence=ev,
                    score_effect=0.0,
                    rationale=f"Controlled experimental override to {matched_override.value}",
                    verification_evidence=p.verification_evidence,
                )
                adapted_props.append(adapted_p)
            else:
                adapted_props.append(p)

        # Count pipeline classifications
        pip_correct = sum(1 for p in raw_props if p.classification == AdditionalInfoClass.CORRECT_ADDITIONAL)
        pip_irr = sum(1 for p in raw_props if p.classification == AdditionalInfoClass.IRRELEVANT)
        pip_inc = sum(1 for p in raw_props if p.classification == AdditionalInfoClass.INCORRECT)
        pip_unc = sum(1 for p in raw_props if p.classification == AdditionalInfoClass.UNCERTAIN)
        matched_cnt = sum(1 for p in raw_props if p.classification == AdditionalInfoClass.MATCHED_BY_BASE_ASAG)
        unmatched_cnt = len(raw_props) - matched_cnt

        # Evaluate the 4 candidate models
        score_a = model_a.score(base_norm, adapted_props, severities=sev_map)
        score_b = model_b.score(base_norm, adapted_props, severities=sev_map)
        score_c = model_c.score(base_norm, adapted_props, severities=sev_map)
        score_d = model_d.score(base_norm, adapted_props, severities=sev_map)

        # Record controlled case metadata
        controlled_cases_rows.append({
            "case_id": cid,
            "domain": cdef["domain"],
            "case_name": cdef["case_name"],
            "question": q,
            "reference_answer": ref,
            "student_answer": stu,
            "case_description": cdef["case_description"],
            "expected_qualitative_relation": cdef["expected_qualitative_relation"],
            "base_score_normalized": round(base_norm, 4),
            "base_score_scaled": round(base_scaled, 4),
            "matched_count": matched_cnt,
            "unmatched_student_count": unmatched_cnt,
            "pipeline_correct_additional": pip_correct,
            "pipeline_irrelevant": pip_irr,
            "pipeline_incorrect": pip_inc,
            "pipeline_uncertain": pip_unc,
            "experimental_severities": json.dumps(sev_map),
            "experimental_overrides": json.dumps({k: v.value for k, v in override_class.items()}),
        })

        # Record model comparison row
        model_comp_rows.append({
            "case_id": cid,
            "domain": cdef["domain"],
            "case_name": cdef["case_name"],
            "base_score_normalized": round(base_norm, 4),
            "base_score_scaled": round(base_scaled, 4),
            "model_a_final_norm": round(score_a.clipped_score, 4),
            "model_a_final_scaled": round(score_a.scaled_score, 4),
            "model_a_delta": round(score_a.scaled_score - base_scaled, 4),
            "model_b_final_norm": round(score_b.clipped_score, 4),
            "model_b_final_scaled": round(score_b.scaled_score, 4),
            "model_b_delta": round(score_b.scaled_score - base_scaled, 4),
            "model_c_final_norm": round(score_c.clipped_score, 4),
            "model_c_final_scaled": round(score_c.scaled_score, 4),
            "model_c_delta": round(score_c.scaled_score - base_scaled, 4),
            "model_d_final_norm": round(score_d.clipped_score, 4),
            "model_d_final_scaled": round(score_d.scaled_score, 4),
            "model_d_delta": round(score_d.scaled_score - base_scaled, 4),
        })

        # Record itemized score trace
        score_traces[cid] = {
            "case_id": cid,
            "domain": cdef["domain"],
            "case_name": cdef["case_name"],
            "question": q,
            "reference_answer": ref,
            "student_answer": stu,
            "base_score_normalized": round(base_norm, 4),
            "base_score_scaled": round(base_scaled, 4),
            "adapted_propositions": [
                {
                    "source_text": p.proposition.source_text,
                    "classification": p.classification.value,
                    "evidence_type": p.contradiction_evidence.contradiction_type.value if p.contradiction_evidence else ("SUPPORTED" if p.verification_evidence else "NONE"),
                    "evidence_strength": round(p.contradiction_evidence.evidence_strength if p.contradiction_evidence else (1.0 if p.verification_evidence else 0.0), 4),
                }
                for p in adapted_props
            ],
            "models": {
                "Model_A": score_a.to_dict(),
                "Model_B": score_b.to_dict(),
                "Model_C": score_c.to_dict(),
                "Model_D": score_d.to_dict(),
            },
        }

    return controlled_cases_rows, model_comp_rows, score_traces


def main() -> None:
    output_dir = "evaluation/scoring_development"
    os.makedirs(output_dir, exist_ok=True)

    print("Running Phase 4B controlled evaluation across 33 cases...")
    controlled_rows, comp_rows, traces = run_phase4b_evaluation()

    # 1. Export controlled cases CSV
    cases_path = os.path.join(output_dir, "phase4b_controlled_cases.csv")
    with open(cases_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(controlled_rows[0].keys()))
        writer.writeheader()
        writer.writerows(controlled_rows)
    print(f"Exported {len(controlled_rows)} cases to {cases_path}")

    # 2. Export model comparison CSV
    comp_path = os.path.join(output_dir, "phase4b_model_comparison.csv")
    with open(comp_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(comp_rows[0].keys()))
        writer.writeheader()
        writer.writerows(comp_rows)
    print(f"Exported model comparisons to {comp_path}")

    # 3. Export score traces JSON
    traces_path = os.path.join(output_dir, "phase4b_score_traces.json")
    with open(traces_path, "w", encoding="utf-8") as f:
        json.dump(traces, f, indent=2)
    print(f"Exported itemized score traces to {traces_path}")


if __name__ == "__main__":
    main()
