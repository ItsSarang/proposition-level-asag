"""
Common data types and result structures for Proposition-Level ASAG.

Defines standardized data transfer objects used across models, evaluation runners,
CLI scripts, and API adapters.
"""
from dataclasses import dataclass, field
import json
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class GradingResult:
    """
    Standardized grading result produced across all model versions (V0 through V5).

    Attributes
    ----------
    model_version : str
        Version identifier ('V0', 'V1', 'V2', 'V3', 'V4', or 'V5').
    question : str
        Prompt question text.
    reference_answer : str
        Instructor ground-truth reference answer.
    student_answer : str
        Student response text.
    normalized_score : float
        Score bounded in [0.0, 1.0].
    grade : float
        Scaled numeric score bounded in [0.0, max_points].
    max_points : float, default=5.0
        Maximum grading scale points.
    explanation : str, default=""
        Human-readable explanation of score and proposition adjustments.
    metadata : Optional[Dict[str, Any]], default=None
        Optional version-specific diagnostic trace and provenance records.
    """

    model_version: str
    question: str
    reference_answer: str
    student_answer: str
    normalized_score: float
    grade: float
    max_points: float = 5.0
    explanation: str = ""
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to a JSON-serializable dictionary."""
        return {
            "model_version": self.model_version,
            "question": self.question,
            "reference_answer": self.reference_answer,
            "student_answer": self.student_answer,
            "normalized_score": round(self.normalized_score, 4),
            "grade": round(self.grade, 4),
            "max_points": self.max_points,
            "explanation": self.explanation,
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize result to a formatted JSON string."""
        return json.dumps(self.to_dict(), indent=indent)
