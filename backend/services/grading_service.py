"""
Grading Service coordinating model execution and response serialization.

Decouples API route handlers from model registry and evaluation logic.
Pure Python service without external web framework coupling.
"""
from typing import Any, Dict, Optional
from backend.services.model_registry import BackendModelRegistry
from common.types import GradingResult


class GradingService:
    """
    Application service that executes grading requests via the model registry.
    """

    def __init__(self, registry: Optional[BackendModelRegistry] = None) -> None:
        """
        Initialize GradingService with an optional model registry instance.

        Parameters
        ----------
        registry : Optional[BackendModelRegistry], default=None
            Registry instance used for model discovery.
        """
        self.registry = registry or BackendModelRegistry()

    def grade(
        self,
        question: str,
        reference_answer: str,
        student_answer: str,
        model_id: str = "V5",
        scale: float = 5.0,
    ) -> Dict[str, Any]:
        """
        Grade a student answer using the model version specified.

        Parameters
        ----------
        question : str
            The prompt or query.
        reference_answer : str
            Instructor benchmark reference.
        student_answer : str
            Student candidate answer.
        model_id : str, default="V5"
            Model key (V0, V1, V2, V3, V4, V5).
        scale : float, default=5.0
            Maximum score scale.

        Returns
        -------
        Dict[str, Any]
            Serialized evaluation result.
        """
        model = self.registry.get_model(model_id, scale=scale)
        res: GradingResult = model.evaluate(
            question=question,
            reference_answer=reference_answer,
            student_answer=student_answer,
        )
        return {
            "model_version": res.model_version,
            "question": res.question,
            "reference_answer": res.reference_answer,
            "student_answer": res.student_answer,
            "normalized_score": res.normalized_score,
            "grade": res.grade,
            "max_points": res.max_points,
            "explanation": res.explanation,
        }
