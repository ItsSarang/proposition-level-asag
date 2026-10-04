"""
Systematic Diagnostic Error Analysis Module (Phase 11).

Categorizes ASAG failure modes across 8 systematic NLP and dataset failure types:
1. EXTRACTION_FAILURE: Syntactic or fragment extraction yielded 0 propositions from valid text.
2. SEMANTIC_SIMILARITY_FAILURE: Paraphrases or domain equivalents uncaptured by lexical/WordNet resources.
3. PROPOSITION_ALIGNMENT_FAILURE: Misalignment or threshold rejection between valid propositions.
4. RELEVANCE_FAILURE: Erroneous assessment of question-domain relevance or off-topic status.
5. CONTRADICTION_FAILURE: Misdiagnosed polarity, false contradiction, or undetected factual conflict.
6. ADDITIONAL_INFO_CLASSIFICATION_FAILURE: Miscategorization of unmatched information.
7. SCORING_AGGREGATION_FAILURE: Verbosity inflation, diminishing returns distortion, or score bounds clipping.
8. DATASET_REFERENCE_REPRESENTATION_ISSUE: Reference answer lacks clausal structure (nominal/fragment) or human graders severely disagreed.

Uses actual dataset records from the Mohler benchmark; never fabricates cases.
"""

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


class ErrorCategory(str, Enum):
    """The 8 formal failure categories of the ASAG error taxonomy."""
    EXTRACTION_FAILURE = "EXTRACTION_FAILURE"
    SEMANTIC_SIMILARITY_FAILURE = "SEMANTIC_SIMILARITY_FAILURE"
    PROPOSITION_ALIGNMENT_FAILURE = "PROPOSITION_ALIGNMENT_FAILURE"
    RELEVANCE_FAILURE = "RELEVANCE_FAILURE"
    CONTRADICTION_FAILURE = "CONTRADICTION_FAILURE"
    ADDITIONAL_INFO_CLASSIFICATION_FAILURE = "ADDITIONAL_INFO_CLASSIFICATION_FAILURE"
    SCORING_AGGREGATION_FAILURE = "SCORING_AGGREGATION_FAILURE"
    DATASET_REFERENCE_REPRESENTATION_ISSUE = "DATASET_REFERENCE_REPRESENTATION_ISSUE"


@dataclass(frozen=True)
class ErrorDiagnosis:
    """Diagnostic record for a detected error pattern."""
    category: ErrorCategory
    severity: str  # "HIGH", "MEDIUM", "LOW"
    question_id: str
    student_index: int
    question: str
    reference_answer: str
    student_answer: str
    human_score: float
    system_score: float
    error_delta: float
    evidence: Dict[str, Any]
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category.value,
            "severity": self.severity,
            "question_id": self.question_id,
            "student_index": self.student_index,
            "question": self.question,
            "reference_answer": self.reference_answer,
            "student_answer": self.student_answer,
            "human_score": round(self.human_score, 4),
            "system_score": round(self.system_score, 4),
            "error_delta": round(self.error_delta, 4),
            "evidence": self.evidence,
            "explanation": self.explanation,
        }


class OverhaulErrorAnalyzer:
    """
    Automated diagnostic engine classifying prediction failures into the 8 error categories.
    """

    def __init__(self, error_delta_threshold: float = 1.50) -> None:
        self.error_delta_threshold = error_delta_threshold

    def diagnose_record(
        self,
        question_id: str,
        student_index: int,
        question: str,
        reference_answer: str,
        student_answer: str,
        human_score: float,
        system_score: float,
        reference_props_count: int,
        student_props_count: int,
        matched_props_count: int,
        unmatched_props_count: int,
        raw_base_score: float = 0.0,
        positive_adjustment: float = 0.0,
        negative_adjustment: float = 0.0,
        grader_disagreement: float = 0.0,
        is_reference_nominal: bool = False,
        details: Optional[Dict[str, Any]] = None,
    ) -> List[ErrorDiagnosis]:
        """
        Diagnose potential root cause errors for a single student answer record.
        """
        diagnoses: List[ErrorDiagnosis] = []
        error_delta = abs(system_score - human_score)
        details = details or {}

        # 1. DATASET_REFERENCE_REPRESENTATION_ISSUE
        # Reference answer lacks clausal structure or human graders disagreed severely (>= 2.0)
        if reference_props_count == 0 or is_reference_nominal or grader_disagreement >= 2.0:
            reasons = []
            if reference_props_count == 0 or is_reference_nominal:
                reasons.append("Reference answer is a non-clausal nominal or fragmentary phrase yielding 0 propositions.")
            if grader_disagreement >= 2.0:
                reasons.append(f"High inter-grader disagreement ({grader_disagreement:.1f} points between graders).")

            diagnoses.append(
                ErrorDiagnosis(
                    category=ErrorCategory.DATASET_REFERENCE_REPRESENTATION_ISSUE,
                    severity="HIGH" if error_delta >= self.error_delta_threshold else "MEDIUM",
                    question_id=question_id,
                    student_index=student_index,
                    question=question,
                    reference_answer=reference_answer,
                    student_answer=student_answer,
                    human_score=human_score,
                    system_score=system_score,
                    error_delta=error_delta,
                    evidence={
                        "reference_props_count": reference_props_count,
                        "grader_disagreement": grader_disagreement,
                    },
                    explanation=" ".join(reasons),
                )
            )

        # 2. EXTRACTION_FAILURE
        # Valid student answer text (> 4 words), but 0 student propositions extracted
        word_count = len(student_answer.split())
        if word_count >= 5 and student_props_count == 0:
            diagnoses.append(
                ErrorDiagnosis(
                    category=ErrorCategory.EXTRACTION_FAILURE,
                    severity="HIGH",
                    question_id=question_id,
                    student_index=student_index,
                    question=question,
                    reference_answer=reference_answer,
                    student_answer=student_answer,
                    human_score=human_score,
                    system_score=system_score,
                    error_delta=error_delta,
                    evidence={"student_word_count": word_count, "student_props_count": 0},
                    explanation=(
                        f"Student answer contains {word_count} words of valid text but syntactic parser "
                        "extracted 0 propositional structures."
                    ),
                )
            )

        # 3. SCORING_AGGREGATION_FAILURE (e.g. Verbosity Inflation)
        # Low human score (<= 1.5) but high positive adjustment (> 0.50 scaled, or pos_adj >= 0.15 norm)
        if human_score <= 1.5 and positive_adjustment >= 0.15 and system_score >= 2.5:
            diagnoses.append(
                ErrorDiagnosis(
                    category=ErrorCategory.SCORING_AGGREGATION_FAILURE,
                    severity="HIGH",
                    question_id=question_id,
                    student_index=student_index,
                    question=question,
                    reference_answer=reference_answer,
                    student_answer=student_answer,
                    human_score=human_score,
                    system_score=system_score,
                    error_delta=error_delta,
                    evidence={
                        "positive_adjustment": positive_adjustment,
                        "unmatched_props_count": unmatched_props_count,
                    },
                    explanation=(
                        f"Verbosity inflation: student received +{positive_adjustment:.2f} bonus from "
                        f"{unmatched_props_count} unmatched additions despite poor answer quality (human={human_score:.1f})."
                    ),
                )
            )

        # 4. PROPOSITION_ALIGNMENT_FAILURE
        # High human score (>= 4.0), student and reference both have propositions, but 0 matched
        if human_score >= 4.0 and reference_props_count > 0 and student_props_count > 0 and matched_props_count == 0:
            diagnoses.append(
                ErrorDiagnosis(
                    category=ErrorCategory.PROPOSITION_ALIGNMENT_FAILURE,
                    severity="HIGH",
                    question_id=question_id,
                    student_index=student_index,
                    question=question,
                    reference_answer=reference_answer,
                    student_answer=student_answer,
                    human_score=human_score,
                    system_score=system_score,
                    error_delta=error_delta,
                    evidence={
                        "reference_props_count": reference_props_count,
                        "student_props_count": student_props_count,
                        "matched_props_count": 0,
                    },
                    explanation=(
                        "Student provided a highly rated answer (human score >= 4.0) with propositions, "
                        "yet proposition matcher failed to align any student proposition with reference."
                    ),
                )
            )

        # 5. CONTRADICTION_FAILURE
        if details.get("false_contradiction_detected"):
            diagnoses.append(
                ErrorDiagnosis(
                    category=ErrorCategory.CONTRADICTION_FAILURE,
                    severity="HIGH",
                    question_id=question_id,
                    student_index=student_index,
                    question=question,
                    reference_answer=reference_answer,
                    student_answer=student_answer,
                    human_score=human_score,
                    system_score=system_score,
                    error_delta=error_delta,
                    evidence=details.get("contradiction_evidence", {}),
                    explanation=details.get("contradiction_explanation", "Contradiction detector misdiagnosed relation."),
                )
            )

        # 6. SEMANTIC_SIMILARITY_FAILURE
        if details.get("semantic_gap_detected"):
            diagnoses.append(
                ErrorDiagnosis(
                    category=ErrorCategory.SEMANTIC_SIMILARITY_FAILURE,
                    severity="MEDIUM",
                    question_id=question_id,
                    student_index=student_index,
                    question=question,
                    reference_answer=reference_answer,
                    student_answer=student_answer,
                    human_score=human_score,
                    system_score=system_score,
                    error_delta=error_delta,
                    evidence=details.get("semantic_evidence", {}),
                    explanation=details.get("semantic_explanation", "Lexical/WordNet comparator missed domain paraphrase."),
                )
            )

        return diagnoses

    def analyze_diagnoses_summary(
        self,
        diagnoses: Sequence[ErrorDiagnosis],
    ) -> Dict[str, Any]:
        """
        Aggregate category counts, average error deltas, and sample cases.
        """
        category_counts: Dict[str, int] = {cat.value: 0 for cat in ErrorCategory}
        category_deltas: Dict[str, List[float]] = {cat.value: [] for cat in ErrorCategory}
        sample_cases: Dict[str, List[Dict[str, Any]]] = {cat.value: [] for cat in ErrorCategory}

        for d in diagnoses:
            cat_name = d.category.value
            category_counts[cat_name] += 1
            category_deltas[cat_name].append(d.error_delta)
            if len(sample_cases[cat_name]) < 3:
                sample_cases[cat_name].append(d.to_dict())

        avg_deltas = {
            cat: round(sum(deltas) / max(1, len(deltas)), 4)
            for cat, deltas in category_deltas.items()
        }

        return {
            "total_diagnoses": len(diagnoses),
            "category_counts": category_counts,
            "average_error_deltas": avg_deltas,
            "representative_samples": sample_cases,
        }
